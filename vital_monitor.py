import os
import sys
import socket
import asyncio
import json
import threading
import time
from typing import List
from pydantic import BaseModel
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None

# UTF-8 encoding Windows console
try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

app = FastAPI(title="Reanimatsiya va Bemor Hayotiy Ko'rsatkichlari Monitori (ESP32 Live)")

active_websockets: List[WebSocket] = []

latest_telemetry = {
    "f_curr": 0.0,
    "bpm": 0,
    "count": 0,
    "d_ok": False,
    "r_ok": True,
    "bpm_ok": False,
    "pos_ok": True,
    "lung_p": 0.0,
    "stomach_p": 0.0,
    "inj_ok": False,
    "timestamp": 0
}

HTML_CONTENT = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>ICU Bemor Hayotiy Ko'rsatkichlari & CPR Simulyatori</title>
    <meta name="theme-color" content="#ffffff">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Vital Monitor">
    <link rel="manifest" href="/manifest_vital.json">
    <link rel="icon" href="/static/icons/vital_192.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@500;600;700;800;900&display=swap');
        * { -webkit-touch-callout: none; touch-action: manipulation; box-sizing: border-box; }
        html, body {
            margin: 0;
            padding: 0;
            width: 100vw;
            height: 100vh;
            overflow: hidden;
            background-color: #f1f5f9;
            color: #0f172a;
            font-family: 'Rajdhani', sans-serif;
            user-select: none;
        }

        .mono {
            font-family: 'Share Tech Mono', monospace;
        }

        @keyframes shockFlash {
            0% { background-color: rgba(59, 130, 246, 0.5); }
            100% { background-color: transparent; }
        }
        .shock-active {
            animation: shockFlash 0.6s ease-out;
        }

        @keyframes injFlash {
            0% { background-color: rgba(168, 85, 247, 0.45); }
            100% { background-color: transparent; }
        }
        .inj-active {
            animation: injFlash 1.2s ease-out;
        }

        @keyframes alarmBlink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.25; }
        }
        .alarm-blink {
            animation: alarmBlink 0.8s infinite;
        }
    </style>
</head>
<body class="h-screen w-screen bg-slate-100 text-slate-800 flex flex-col justify-between p-2 overflow-hidden select-none">

    <div id="flash-overlay" class="fixed inset-0 pointer-events-none z-50"></div>

    <!-- 1. TOP HEADER (COMPACT ~38px) -->
    <header class="bg-white border border-slate-200 rounded-xl px-3 py-1.5 flex flex-wrap items-center justify-between gap-2 shadow-xs shrink-0">
        <div class="flex items-center space-x-3">
            <div class="flex items-center space-x-1.5">
                <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 alarm-blink"></span>
                <span class="font-black text-sm tracking-wider text-slate-900">ICU PATIENT & CPR MONITOR</span>
            </div>
            <div class="text-xs text-slate-500 border-l border-slate-200 pl-2.5">
                KOYKA: <span class="text-slate-900 font-bold">#04</span>
            </div>
            <div class="text-xs text-slate-500 border-l border-slate-200 pl-2.5">
                BEMOR: <span class="text-emerald-700 font-bold">Anvar Karimov (40 yosh)</span>
            </div>
        </div>

        <div id="alarm-banner" class="px-3 py-0.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 border border-emerald-300 transition-all duration-300">
            <i class="fa-solid fa-heart-pulse mr-1"></i> STATUS: BARQAROR (NORMAL)
        </div>

        <div class="flex flex-wrap items-center gap-1.5 text-xs">
            <!-- REAL HARDWARE WEB SERIAL USB CONNECT BUTTON -->
            <button id="btn-web-serial" onclick="toggleDirectWebSerial()" class="px-2.5 py-1 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-black text-xs flex items-center gap-1 shadow-xs cursor-pointer transition animate-pulse">
                <i class="fa-brands fa-usb text-xs"></i>
                <span id="btn-web-serial-text">🔌 USB Ulanish</span>
            </button>

            <div id="hw-badge" class="px-2 py-1 rounded-lg bg-slate-100 border border-slate-200 text-slate-600 flex items-center gap-1 font-bold">
                <span id="hw-dot" class="w-2 h-2 rounded-full bg-slate-400"></span>
                <span id="hw-text">USB: Kutilmoqda</span>
            </div>

            <a href="/hub" class="px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300 flex items-center gap-1 font-bold shadow-xs">
                <i class="fa-solid fa-hospital text-cyan-600"></i> Hub
            </a>

            <button id="pwa-vital-btn" onclick="installVitalPWA()" class="hidden px-2 py-1 rounded-lg bg-amber-400 hover:bg-amber-300 text-slate-950 flex items-center gap-1 font-black shadow-xs cursor-pointer">
                <i class="fa-solid fa-download"></i> O'rnatish
            </button>

            <a href="/" target="_blank" class="px-2 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 flex items-center gap-1 font-bold shadow-xs">
                <i class="fa-solid fa-hospital-user text-indigo-600"></i> AI Bemor
            </a>

            <a href="/console" target="_blank" class="px-2 py-1 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 flex items-center gap-1 font-bold shadow-xs">
                <i class="fa-solid fa-hand-holding-heart text-purple-600"></i> Pult
            </a>

            <!-- Volume Slider -->
            <div class="flex items-center gap-1 bg-slate-100 border border-slate-300 px-2 py-1 rounded-lg">
                <button id="btn-audio" onclick="toggleAudio()" class="text-slate-700 hover:text-slate-900 flex items-center gap-1 cursor-pointer">
                    <i id="audio-icon" class="fa-solid fa-volume-high text-emerald-600 text-xs"></i>
                    <span id="audio-text" class="text-xs font-bold">100%</span>
                </button>
                <input type="range" id="monitor-volume-slider" min="0" max="1" step="0.05" value="1.0" oninput="changeMonitorVolume(this.value)" class="w-12 accent-emerald-600 h-1.5 bg-slate-300 rounded cursor-pointer" title="Ovoz balandligi (100% Maksimal)">
            </div>

            <button onclick="toggleFullScreen()" class="px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300 cursor-pointer">
                <i class="fa-solid fa-expand"></i>
            </button>
            <span id="clock" class="mono text-xs font-bold text-slate-700">00:00:00</span>
        </div>
    </header>

    <!-- INJECTION NOTIFICATION POPUP -->
    <div id="inj-banner" class="hidden my-0.5 bg-purple-100 border border-purple-400 rounded-xl p-1.5 shadow-sm text-center text-purple-900 text-xs font-bold alarm-blink">
        <i class="fa-solid fa-syringe text-purple-600 text-sm mr-1"></i> 
        <span id="inj-banner-text">💉 UKOL QILINDI (ADRENALIN 1mg)! FARMAKOLOGIK TA'SIR KUZATILMOQDA...</span>
    </div>

    <!-- 2. TOP 50% SECTION: VITAL SIGNS & OSCILLOSCOPE MONITOR -->
    <div class="bg-white border border-slate-200 rounded-xl p-2 my-0.5 shadow-xs grid grid-cols-1 lg:grid-cols-4 gap-2 flex-1 min-h-0 overflow-hidden">
        
        <!-- LEFT 3 COLS: LIVE OSCILLOSCOPES (ECG & SpO2) -->
        <div class="lg:col-span-3 flex flex-col justify-between gap-1 border-r border-slate-100 pr-2 min-h-0 overflow-hidden">
            
            <!-- 1. ECG Lead II Waveform -->
            <div class="flex-1 flex flex-col min-h-0 pb-1 border-b border-slate-100">
                <div class="flex justify-between items-center text-xs font-bold text-emerald-800 mb-0.5 shrink-0">
                    <span class="flex items-center gap-1.5">
                        <i class="fa-solid fa-bolt text-emerald-600"></i> EKG Lead II (mV)
                        <span class="text-[10px] text-slate-400 font-normal">25mm/s 10mm/mV</span>
                    </span>
                    <span id="ecg-rhythm-name" class="font-extrabold text-emerald-700">Sinus Ritmi</span>
                </div>
                <div class="flex-1 relative min-h-0 rounded-lg bg-white border border-slate-200 overflow-hidden">
                    <canvas id="ecgCanvas" class="w-full h-full block"></canvas>
                </div>
            </div>

            <!-- 2. SpO2 Pleth Waveform -->
            <div class="flex-1 flex flex-col min-h-0 pt-0.5">
                <div class="flex justify-between items-center text-xs font-bold text-sky-800 mb-0.5 shrink-0">
                    <span class="flex items-center gap-1.5">
                        <i class="fa-solid fa-wave-square text-sky-600"></i> SpO2 Pleth (Puls to'lqini)
                    </span>
                    <span id="pleth-status" class="font-extrabold text-sky-700">Normal perfuziya</span>
                </div>
                <div class="flex-1 relative min-h-0 rounded-lg bg-white border border-slate-200 overflow-hidden">
                    <canvas id="plethCanvas" class="w-full h-full block"></canvas>
                </div>
            </div>

            <canvas id="respCanvas" class="hidden" width="10" height="10"></canvas>
        </div>

        <!-- RIGHT 1 COL: 4 VITAL NUMERIC CARDS -->
        <div class="flex flex-col justify-between gap-1 min-h-0 overflow-hidden">
            
            <!-- HR / PULS -->
            <div class="bg-emerald-50/70 border border-emerald-300 rounded-xl p-1.5 shadow-xs flex-1 flex flex-col justify-between">
                <div class="flex justify-between items-center text-emerald-800 font-bold text-xs">
                    <span><i class="fa-solid fa-heart-pulse mr-1 text-emerald-600"></i> HR / PULS</span>
                    <span class="text-[10px] text-slate-400">bpm</span>
                </div>
                <div class="flex items-baseline justify-between my-auto">
                    <span id="num-hr" class="mono text-4xl lg:text-5xl font-black text-emerald-600 leading-none">75</span>
                    <div class="text-right text-[10px] text-slate-500 font-semibold leading-tight">
                        <div>YUQ: 120</div>
                        <div>PAS: 50</div>
                    </div>
                </div>
                <div class="flex justify-between text-[10px] text-slate-500 border-t border-slate-200 pt-0.5">
                    <span>Zarbalar: <span id="num-count" class="font-bold text-emerald-700">0</span></span>
                    <span>Puls: Normal</span>
                </div>
            </div>

            <!-- SpO2 -->
            <div class="bg-sky-50/70 border border-sky-300 rounded-xl p-1.5 shadow-xs flex-1 flex flex-col justify-between">
                <div class="flex justify-between items-center text-sky-800 font-bold text-xs">
                    <span><i class="fa-solid fa-droplet mr-1 text-sky-600"></i> SpO2</span>
                    <span class="text-[10px] text-slate-400">%</span>
                </div>
                <div class="flex items-baseline justify-between my-auto">
                    <span id="num-spo2" class="mono text-4xl lg:text-5xl font-black text-sky-600 leading-none">98</span>
                    <div class="text-right text-[10px] text-slate-500 font-semibold leading-tight">
                        <div>PI: 4.2%</div>
                        <div>PAS: 90%</div>
                    </div>
                </div>
                <div class="flex justify-between text-[10px] text-slate-500 border-t border-slate-200 pt-0.5">
                    <span>Puls: <span id="num-pr" class="font-bold text-sky-700">75</span></span>
                    <span>Signal: Kuchli</span>
                </div>
            </div>

            <!-- NIBP & RR/Temp Split -->
            <div class="grid grid-cols-2 gap-1 shrink-0">
                <div class="bg-slate-50 border border-slate-300 rounded-xl p-1.5 text-center shadow-xs flex flex-col justify-between">
                    <div class="text-[10px] font-bold text-slate-800 flex items-center justify-between">
                        <span>NIBP</span>
                        <span class="text-slate-400">mmHg</span>
                    </div>
                    <div class="mono font-black text-slate-800 leading-none my-0.5">
                        <span id="num-sys" class="text-lg">120</span>/<span id="num-dia" class="text-sm">80</span>
                    </div>
                    <div class="text-[9px] text-slate-600 font-bold">MAP: <span id="num-map" class="text-emerald-700">93</span></div>
                </div>

                <div class="bg-amber-50/60 border border-amber-300 rounded-xl p-1.5 text-center shadow-xs flex flex-col justify-between">
                    <div class="text-[10px] font-bold text-amber-800 flex items-center justify-between">
                        <span>RESP</span>
                        <span class="text-slate-400">rpm</span>
                    </div>
                    <span id="num-rr" class="mono text-xl font-black text-amber-600 leading-none my-0.5">16</span>
                    <div class="text-[9px] text-purple-700 font-bold"><span id="num-temp">36.6</span>°C</div>
                </div>
            </div>

        </div>

    </div>

    <!-- 3. BOTTOM 50% SECTION: CPR 30:2 EXERCISE DASHBOARD -->
    <div class="bg-white border border-slate-200 rounded-xl p-2 my-0.5 shadow-xs flex-1 min-h-0 flex flex-col justify-between overflow-hidden">
        
        <!-- Header Strip with Stage Badge -->
        <div class="flex flex-wrap items-center justify-between gap-2 pb-1 border-b border-slate-100 shrink-0">
            <div class="flex items-center gap-2">
                <span class="w-6 h-6 rounded-lg bg-rose-600 text-white flex items-center justify-center text-xs font-black">
                    <i class="fa-solid fa-heart-pulse"></i>
                </span>
                <div>
                    <span class="text-xs font-black text-slate-900 uppercase tracking-wide">YURAK-O'PKA REANIMATSIYASI (CPR 30:2) BOSHQARUVI</span>
                    <span class="text-[10px] text-slate-500 font-semibold ml-2">Standart: 30 zarba + 2 nafas</span>
                </div>
            </div>

            <div id="cpr-stage-badge" class="px-2.5 py-0.5 rounded-lg text-xs font-black bg-slate-100 text-slate-700 border border-slate-300 flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-slate-400"></span>
                <span>0-BOSQICH: ASISTOLIYA (CPR KUTILMOQDA)</span>
            </div>
        </div>

        <!-- 3 Columns: A. Force Meter | B. 30:2 Cycle Hub | C. Airway & Adrenalin -->
        <div class="grid grid-cols-1 md:grid-cols-12 gap-2 my-1 flex-1 min-h-0 items-stretch">
            
            <!-- COLUMN A (4 cols): COMPRESSION FORCE -->
            <div class="md:col-span-4 bg-slate-50/90 border border-slate-200 rounded-xl p-2.5 flex flex-col justify-between shadow-xs h-full overflow-hidden">
                <div class="flex justify-between items-center text-xs font-black text-slate-700 shrink-0">
                    <span class="flex items-center gap-1">
                        <i class="fa-solid fa-hand-fist text-rose-600"></i> BOSISH KUCHI:
                    </span>
                    <button type="button" onclick="tareCprForce()" title="Boshlang'ich vaznni 0 qilish" class="py-0.5 px-2 bg-white hover:bg-slate-100 text-slate-700 rounded border border-slate-300 text-[10px] font-bold cursor-pointer active:scale-95 transition flex items-center gap-1 shadow-xs">
                        <i class="fa-solid fa-scale-balanced text-rose-600"></i> ⚖️ 0 Qilish (Tare)
                    </button>
                </div>

                <div class="flex items-baseline justify-between my-auto">
                    <div id="cpr-force-val" class="mono text-4xl lg:text-5xl font-black text-rose-600 tracking-tight">0.0 kg</div>
                    <div id="cpr-eval-verdict" class="px-2.5 py-1 rounded-lg text-xs font-black bg-slate-200 text-slate-700 shadow-xs">
                        BOSISHGA TAYYOR
                    </div>
                </div>

                <div class="shrink-0">
                    <div class="w-full bg-slate-200 rounded-lg h-5 overflow-hidden relative shadow-inner p-0.5 border border-slate-300">
                        <div id="cpr-force-bar" class="bg-rose-500 h-full rounded transition-all duration-75" style="width: 0%;"></div>
                        <div class="absolute inset-y-0 left-[63%] w-[28%] bg-emerald-500/25 border-x-2 border-emerald-500 pointer-events-none flex items-center justify-center">
                            <span class="text-[8px] font-black text-emerald-900 tracking-wider">ME'YOR (38-55 kg)</span>
                        </div>
                    </div>
                    <div class="flex justify-between text-[9px] font-bold text-slate-500 mt-0.5">
                        <span>0 kg</span>
                        <span class="text-emerald-700 font-bold">5 - 6 sm chuqurlik</span>
                        <span>60 kg</span>
                    </div>
                </div>
            </div>

            <!-- COLUMN B (5 cols): 30:2 CYCLE COUNTERS & REAL-TIME QUALITY -->
            <div class="md:col-span-5 bg-indigo-50/50 border border-indigo-200 rounded-xl p-2.5 flex flex-col justify-between shadow-xs h-full overflow-hidden">
                <div class="flex justify-between items-center text-xs font-black text-indigo-900 shrink-0">
                    <span class="flex items-center gap-1">
                        <i class="fa-solid fa-rotate text-indigo-600"></i> 30:2 SIKL HISOBI:
                    </span>
                    <span id="cpr-rate-badge" class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-white text-indigo-800 border border-indigo-200">
                        100 - 120 /min me'yor
                    </span>
                </div>

                <div class="grid grid-cols-2 gap-2 my-auto">
                    <div class="bg-white border border-indigo-200 rounded-lg p-2 text-center shadow-xs">
                        <div class="text-[10px] font-bold text-slate-500 uppercase">Ko'krak Massaji</div>
                        <div class="flex items-baseline justify-center gap-1">
                            <span id="cpr-cycle-comps" class="mono text-3xl lg:text-4xl font-black text-indigo-600">0</span>
                            <span class="text-xs font-bold text-slate-400">/ 30</span>
                        </div>
                    </div>

                    <div class="bg-white border border-sky-200 rounded-lg p-2 text-center shadow-xs">
                        <div class="text-[10px] font-bold text-slate-500 uppercase">Sun'iy Nafas</div>
                        <div class="flex items-baseline justify-center gap-1">
                            <span id="cpr-cycle-vents" class="mono text-3xl lg:text-4xl font-black text-sky-600">0</span>
                            <span class="text-xs font-bold text-slate-400">/ 2</span>
                        </div>
                    </div>
                </div>

                <div id="cpr-cycle-badge" class="py-1 px-2 rounded-lg text-center text-xs font-black bg-indigo-100 text-indigo-900 border border-indigo-300 shrink-0">
                    SIKL: 0/30 ZARBA | 0/2 NAFAS
                </div>

                <!-- 4 Real-time Quality Chips -->
                <div class="grid grid-cols-4 gap-1 mt-1 text-[9px] font-bold shrink-0">
                    <div id="badge-d" class="p-0.5 rounded bg-white border border-slate-200 text-slate-600 text-center shadow-xs">Chuqurlik: -</div>
                    <div id="badge-r" class="p-0.5 rounded bg-white border border-slate-200 text-slate-600 text-center shadow-xs">Bo'shatish: -</div>
                    <div id="badge-bpm" class="p-0.5 rounded bg-white border border-slate-200 text-slate-600 text-center shadow-xs">Tezlik: -</div>
                    <div id="badge-pos" class="p-0.5 rounded bg-white border border-slate-200 text-slate-600 text-center shadow-xs">Joyi: -</div>
                </div>
            </div>

            <!-- COLUMN C (3 cols): AIRWAY & ADRENALIN INJECTION -->
            <div class="md:col-span-3 bg-sky-50/50 border border-sky-200 rounded-xl p-2.5 flex flex-col justify-between shadow-xs h-full overflow-hidden">
                <div class="flex justify-between items-center text-xs font-black text-sky-900 shrink-0">
                    <span class="flex items-center gap-1">
                        <i class="fa-solid fa-lungs text-sky-600"></i> O'PKA BOSIMI:
                    </span>
                    <span id="cpr-bpm-val" class="mono font-black text-emerald-700 text-xs">0 /min</span>
                </div>

                <div class="flex items-baseline justify-between my-auto">
                    <div id="lung-p-val" class="mono text-3xl lg:text-4xl font-black text-sky-600">0.0 kPa</div>
                    <div id="stomach-alert" class="px-2 py-0.5 rounded text-[10px] font-bold bg-white text-slate-600 border border-slate-200">
                        Oshqozon toza
                    </div>
                </div>

                <div class="shrink-0">
                    <div class="w-full bg-slate-200 rounded-lg h-4 overflow-hidden relative shadow-inner p-0.5 border border-slate-300">
                        <div id="lung-p-bar" class="bg-sky-500 h-full rounded transition-all duration-75" style="width: 0%;"></div>
                        <div class="absolute inset-y-0 left-[32%] w-[56%] bg-sky-400/25 border-x border-sky-500 pointer-events-none flex items-center justify-center">
                            <span class="text-[7px] font-black text-sky-900">0.8-2.2 kPa</span>
                        </div>
                    </div>
                    <div id="lung-status-text" class="text-[9px] text-sky-700 font-bold mt-0.5 text-center">
                        Me'yor: 0.8 - 2.2 kPa
                    </div>
                </div>

                <div class="hidden"><span id="stomach-p-val">0.0</span></div>

                <button type="button" onclick="triggerManualInjection()" id="inj-badge-small" class="mt-1 w-full py-2 px-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-black text-xs shadow-md flex items-center justify-center gap-1.5 transition cursor-pointer active:scale-95 shrink-0">
                    <i class="fa-solid fa-syringe text-xs"></i> 💉 ADRENALIN (UKOL)
                </button>
            </div>

        </div>

    </div>

    <!-- 4. BOTTOM CLINICAL SCENARIOS BAR (~36px) -->
    <footer class="bg-white border border-slate-200 rounded-xl p-1.5 shadow-xs shrink-0 flex flex-wrap items-center justify-between gap-1 text-xs">
        <div class="flex items-center gap-1 text-slate-700 font-bold">
            <i class="fa-solid fa-stethoscope text-indigo-600"></i>
            <span>Ssenariylar:</span>
        </div>

        <div class="flex flex-wrap items-center gap-1">
            <button onclick="setScenario('normal')" class="px-2 py-0.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-heart text-emerald-600"></i> 🟢 Normal (75)
            </button>

            <button onclick="setScenario('dying')" class="px-2 py-0.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-skull-crossbones text-rose-600"></i> 🚨 0 Asistoliya
            </button>

            <button onclick="setScenario('attack')" class="px-2 py-0.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-bolt-lightning text-amber-600"></i> ⚡ Taxikardiya
            </button>

            <button onclick="setScenario('hypoxia')" class="px-2 py-0.5 rounded-lg bg-sky-50 hover:bg-sky-100 text-sky-800 border border-sky-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-lungs text-sky-600"></i> 🫁 Gipoksiya
            </button>

            <button onclick="setScenario('shock')" class="px-2 py-0.5 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-800 border border-purple-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-droplet-slash text-purple-600"></i> 🩸 Shok
            </button>

            <button onclick="triggerManualInjection()" class="px-2 py-0.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-800 border border-indigo-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-syringe text-indigo-600"></i> 💉 Ukol (Adrenalin)
            </button>

            <button onclick="defibrillateShock()" class="px-2 py-0.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-800 border border-blue-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-wand-magic-sparkles text-blue-600"></i> ⚡ Defibrilyator
            </button>
        </div>
    </footer>

    <!-- JAVASCRIPT ENGINE -->
    <script>
        let current = {
            hr: 75,
            spo2: 98,
            sys: 120,
            dia: 80,
            rr: 16,
            temp: 36.6,
            mode: "normal",
            rhythm: "sinus"
        };

        let target = { ...current };
        let transitionSteps = 0;
        let totalSteps = 0;

        let audioCtx = null;
        let masterGain = null;
        let masterCompressor = null;
        let soundEnabled = true;
        let monitorVolume = 1.0;
        let asystoleOsc = null;
        let lastBeatTime = 0;

        function initAudio() {
            if (!audioCtx) {
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                
                masterCompressor = audioCtx.createDynamicsCompressor();
                masterCompressor.threshold.setValueAtTime(-14, audioCtx.currentTime);
                masterCompressor.knee.setValueAtTime(30, audioCtx.currentTime);
                masterCompressor.ratio.setValueAtTime(12, audioCtx.currentTime);
                masterCompressor.attack.setValueAtTime(0.002, audioCtx.currentTime);
                masterCompressor.release.setValueAtTime(0.25, audioCtx.currentTime);

                masterGain = audioCtx.createGain();
                masterGain.gain.setValueAtTime(soundEnabled ? monitorVolume : 0, audioCtx.currentTime);

                masterCompressor.connect(masterGain);
                masterGain.connect(audioCtx.destination);
            }
            if (audioCtx.state === 'suspended') {
                audioCtx.resume();
            }
        }

        function changeMonitorVolume(val) {
            initAudio();
            monitorVolume = parseFloat(val);
            soundEnabled = monitorVolume > 0;
            if (masterGain && audioCtx) {
                masterGain.gain.setValueAtTime(soundEnabled ? monitorVolume : 0, audioCtx.currentTime);
            }
            const icon = document.getElementById("audio-icon");
            const text = document.getElementById("audio-text");
            if (icon) {
                if (!soundEnabled || monitorVolume === 0) {
                    icon.className = "fa-solid fa-volume-xmark text-red-500 text-xs";
                } else if (monitorVolume < 0.5) {
                    icon.className = "fa-solid fa-volume-low text-amber-500 text-xs";
                } else {
                    icon.className = "fa-solid fa-volume-high text-emerald-600 text-xs";
                }
            }
            if (text) {
                text.innerText = soundEnabled ? `${Math.round(monitorVolume * 100)}%` : "O'chiq";
            }
        }

        function toggleAudio() {
            initAudio();
            soundEnabled = !soundEnabled;
            if (soundEnabled && monitorVolume === 0) {
                monitorVolume = 1.0;
            }
            const slider = document.getElementById("monitor-volume-slider");
            if (slider) slider.value = soundEnabled ? monitorVolume : 0;
            changeMonitorVolume(soundEnabled ? monitorVolume : 0);
            if (!soundEnabled) {
                stopAsystoleTone();
            }
        }

        function playQRSBeep() {
            if (!soundEnabled || current.hr <= 0 || monitorVolume <= 0) return;
            initAudio();
            try {
                const now = audioCtx.currentTime;
                const minFreq = 480;
                const maxFreq = 960;
                const freq = minFreq + ((Math.max(50, current.spo2) - 50) / 50) * (maxFreq - minFreq);

                const osc1 = audioCtx.createOscillator();
                const gain1 = audioCtx.createGain();
                osc1.type = "sine";
                osc1.frequency.setValueAtTime(freq, now);
                gain1.gain.setValueAtTime(1.0, now);
                gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.095);

                const osc2 = audioCtx.createOscillator();
                const gain2 = audioCtx.createGain();
                osc2.type = "triangle";
                osc2.frequency.setValueAtTime(freq * 1.5, now);
                gain2.gain.setValueAtTime(0.45, now);
                gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.085);

                osc1.connect(gain1);
                osc2.connect(gain2);

                const dest = masterCompressor || audioCtx.destination;
                gain1.connect(dest);
                gain2.connect(dest);

                osc1.start(now);
                osc2.start(now);
                osc1.stop(now + 0.095);
                osc2.stop(now + 0.095);
            } catch (e) {}
        }

        function startAsystoleTone() {
            if (!soundEnabled || asystoleOsc || monitorVolume <= 0) return;
            initAudio();
            try {
                const now = audioCtx.currentTime;
                asystoleOsc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                asystoleOsc.type = "triangle";
                asystoleOsc.frequency.setValueAtTime(850, now);
                gain.gain.setValueAtTime(0.85, now);
                asystoleOsc.connect(gain);
                gain.connect(masterCompressor || audioCtx.destination);
                asystoleOsc.start(now);
            } catch (e) {}
        }

        function stopAsystoleTone() {
            if (asystoleOsc) {
                try {
                    asystoleOsc.stop();
                    asystoleOsc.disconnect();
                } catch(e) {}
                asystoleOsc = null;
            }
        }

        // ==================== CPR 30:2 SIKLI VA BOSQICHLI JONLANISH MANTIQI ====================
        let cprState = "idle";
        let peakForce = 0;
        let lastStrokeTime = 0;
        let cprCount = 0;
        let currentBpm = 0;
        let lastDepthOk = false;
        let lastRecoilOk = true;
        let lastRateOk = false;

        let cprCycleComps = 0;
        let cprCycleCorrectComps = 0;
        let cprCycleVents = 0;
        let cprCycleCorrectVents = 0;
        let cprRevivalStage = 0; // 0: Asistoliya, 1: Ozroq jonlanish (22 BPM), 2: To'liq o'ziga kelish (ROSC)

        let injectionInProgress = false;
        let injectionCountdownTimer = null;

        function processCPRStroke(forceKg) {
            const now = Date.now();
            if (cprState === "idle") {
                if (forceKg > 4.0) {
                    cprState = "compressing";
                    peakForce = forceKg;
                }
            } else if (cprState === "compressing") {
                if (forceKg > peakForce) {
                    peakForce = forceKg;
                }
                if (forceKg < peakForce - 3.0) {
                    cprState = "recoiling";
                    if (lastStrokeTime > 0) {
                        const delta = now - lastStrokeTime;
                        if (delta > 200 && delta < 2000) {
                            currentBpm = Math.round(60000 / delta);
                        }
                    }
                    lastStrokeTime = now;
                    cprCount++;
                    lastDepthOk = (peakForce >= 38.0 && peakForce <= 55.0);
                    lastRateOk = (currentBpm >= 100 && currentBpm <= 120);

                    if (cprCycleComps < 30) {
                        cprCycleComps++;
                        if (lastDepthOk) {
                            cprCycleCorrectComps++;
                        }
                    }

                    updateCycleHUD();
                }
            } else if (cprState === "recoiling") {
                if (forceKg <= 5.0) {
                    lastRecoilOk = true;
                    cprState = "idle";
                } else if (forceKg > peakForce - 1.0 && forceKg > 4.0) {
                    lastRecoilOk = false;
                    cprState = "compressing";
                    peakForce = forceKg;
                }
            }

            if (now - lastStrokeTime > 2500) {
                currentBpm = 0;
            }
        }

        function updateCycleHUD() {
            const badge = document.getElementById("cpr-cycle-badge");
            const compsEl = document.getElementById("cpr-cycle-comps");
            const ventsEl = document.getElementById("cpr-cycle-vents");

            if (compsEl) compsEl.innerText = cprCycleComps;
            if (ventsEl) ventsEl.innerText = cprCycleVents;

            if (!badge) return;

            if (cprCycleComps >= 30 && cprCycleVents < 2) {
                badge.innerText = `🫁 30 ZARBA BO'LDI! ENDI 2 TA NAFAS BERING!`;
                badge.className = "py-1 px-2 rounded-lg text-center text-xs font-black bg-amber-500 text-white alarm-blink shadow-md";
            } else if (cprCycleVents >= 2) {
                badge.innerText = `✅ SIKL YAKUNLANDI (Baholanmoqda...)`;
                badge.className = "py-1 px-2 rounded-lg text-center text-xs font-black bg-emerald-600 text-white shadow-md";
            } else {
                badge.innerText = `SIKL: ${cprCycleComps}/30 ZARBA | ${cprCycleVents}/2 NAFAS`;
                badge.className = "py-1 px-2 rounded-lg text-center text-xs font-black bg-indigo-100 text-indigo-900 border border-indigo-300";
            }
        }

        // ==================== CPR FORCE TARE & ZEROING ====================
        let monitorForceTare = 0.0;
        let lastRawMonitorForce = 0.0;
        let monitorTareCaptured = false;
        let monitorTareSamples = [];

        try {
            const saved = localStorage.getItem("manikin_force_tare");
            if (saved !== null) {
                monitorForceTare = parseFloat(saved) || 0.0;
                monitorTareCaptured = true;
            }
        } catch(e) {}

        function tareCprForce() {
            monitorForceTare = lastRawMonitorForce;
            try {
                localStorage.setItem("manikin_force_tare", monitorForceTare.toFixed(2));
            } catch(e) {}
            const valEl = document.getElementById("cpr-force-val");
            if (valEl) valEl.innerText = "0.0 kg";
            const bar = document.getElementById("cpr-force-bar");
            if (bar) bar.style.width = "0%";
            const verd = document.getElementById("cpr-eval-verdict");
            if (verd) {
                verd.innerText = "NOLGA SOZLANDI";
                verd.className = "px-2.5 py-1 rounded-lg text-xs font-black bg-emerald-100 text-emerald-800 shadow-xs";
            }
        }

        // ==================== RESTORED WEB SERIAL API (REAL HARDWARE USB) ====================
        let isSerialConnected = false;
        let webSerialPort = null;
        let webSerialReader = null;
        let webSerialBuffer = "";

        async function toggleDirectWebSerial() {
            if (isSerialConnected && webSerialPort) {
                await disconnectWebSerial();
                return;
            }
            await connectDirectWebSerial();
        }

        async function connectDirectWebSerial() {
            if (!("serial" in navigator)) {
                alert("Brauzeringiz Web Serial API-ni qo'llab-quvvatlamaydi. Iltimos Google Chrome yoki Microsoft Edge brauzeridan foydalaning!");
                return;
            }
            try {
                webSerialPort = await navigator.serial.requestPort();
                await webSerialPort.open({ baudRate: 115200 });
                isSerialConnected = true;
                updateWebSerialUI(true);
                readWebSerialStream();
            } catch(err) {
                console.error("Web Serial Ulanish xatosi:", err);
                if (err.name !== "NotFoundError") {
                    alert("USB portga ulanishda xatolik: " + err.message);
                }
                updateWebSerialUI(false);
            }
        }

        async function disconnectWebSerial() {
            try {
                if (webSerialReader) {
                    await webSerialReader.cancel();
                    webSerialReader = null;
                }
                if (webSerialPort) {
                    await webSerialPort.close();
                    webSerialPort = null;
                }
            } catch(e) {
                console.warn("Serial yopish xatosi:", e);
            }
            isSerialConnected = false;
            updateWebSerialUI(false);
        }

        function updateWebSerialUI(connected) {
            const btn = document.getElementById("btn-web-serial");
            const btnText = document.getElementById("btn-web-serial-text");
            const dot = document.getElementById("hw-dot");
            const text = document.getElementById("hw-text");

            if (connected) {
                if (btn) {
                    btn.className = "px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-black text-xs flex items-center gap-1 shadow-xs cursor-pointer transition";
                }
                if (btnText) btnText.innerText = "🔌 USB: Ulandi (Uzish)";
                if (dot) dot.className = "w-2 h-2 rounded-full bg-emerald-500";
                if (text) text.innerText = "USB: Jonli datchiklar";
            } else {
                if (btn) {
                    btn.className = "px-2.5 py-1 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-black text-xs flex items-center gap-1 shadow-xs cursor-pointer transition animate-pulse";
                }
                if (btnText) btnText.innerText = "🔌 USB Ulanish";
                if (dot) dot.className = "w-2 h-2 rounded-full bg-slate-400";
                if (text) text.innerText = "USB: Ulanmagan";
            }
        }

        async function readWebSerialStream() {
            while (webSerialPort && webSerialPort.readable && isSerialConnected) {
                try {
                    webSerialReader = webSerialPort.readable.getReader();
                    const decoder = new TextDecoder();
                    while (true) {
                        const { value, done } = await webSerialReader.read();
                        if (done) break;
                        if (value) {
                            webSerialBuffer += decoder.decode(value, { stream: true });
                            let lines = webSerialBuffer.split(String.fromCharCode(10));
                            webSerialBuffer = lines.pop();
                            for (let line of lines) {
                                line = line.trim();
                                if (line.startsWith("{") && line.endsWith("}")) {
                                    try {
                                        const data = JSON.parse(line);
                                        handleHardwareData(data);
                                    } catch(e) {}
                                }
                            }
                        }
                    }
                } catch(err) {
                    console.warn("Serial o'qish xatosi:", err);
                    break;
                } finally {
                    if (webSerialReader) {
                        try { webSerialReader.releaseLock(); } catch(e) {}
                        webSerialReader = null;
                    }
                }
            }
        }

        if ("serial" in navigator) {
            navigator.serial.addEventListener("disconnect", () => {
                isSerialConnected = false;
                updateWebSerialUI(false);
            });
        }

        // ==================== PROCESS INCOMING HARDWARE JSON ====================
        function handleHardwareData(data) {
            const rawF = parseFloat(data.force !== undefined ? data.force : (data.f_curr !== undefined ? data.f_curr : (data.force_kg || 0)));
            lastRawMonitorForce = rawF;

            if (!monitorTareCaptured) {
                if (rawF < 15.0) {
                    monitorTareSamples.push(rawF);
                    if (monitorTareSamples.length >= 4) {
                        const avg = monitorTareSamples.reduce((a, b) => a + b, 0) / monitorTareSamples.length;
                        if (avg > 0.15) {
                            monitorForceTare = avg;
                            try { localStorage.setItem("manikin_force_tare", monitorForceTare.toFixed(2)); } catch(e) {}
                        }
                        monitorTareCaptured = true;
                    }
                } else {
                    monitorTareCaptured = true;
                }
            }

            let fCurr = Math.max(0, rawF - monitorForceTare);
            if (fCurr < 0.2) fCurr = 0.0;

            const posBtn = (data.pos_btn === 1 || data.pos_btn === true || data.pos_ok === true || data.pos_valid === true);
            const injBtn = (data.inj_btn === 1 || data.inj_btn === true || data.inj_ok === true);
            const lungP = parseFloat(data.lung_p || 0);
            const stomachP = parseFloat(data.stomach_p || 0);

            processCPRStroke(fCurr);

            const bpm = data.bpm !== undefined ? parseInt(data.bpm) : currentBpm;
            const count = data.count !== undefined ? parseInt(data.count) : cprCount;
            const dOk = data.d_ok !== undefined ? Boolean(data.d_ok) : lastDepthOk;
            const rOk = data.r_ok !== undefined ? Boolean(data.r_ok) : lastRecoilOk;
            const bpmOk = data.bpm_ok !== undefined ? Boolean(data.bpm_ok) : lastRateOk;
            const posOk = posBtn;

            // 1. Force Bar va Verdict
            document.getElementById("cpr-force-val").innerText = `${fCurr.toFixed(1)} kg`;
            const forcePct = Math.min(100, (fCurr / 60.0) * 100);
            const forceBar = document.getElementById("cpr-force-bar");
            forceBar.style.width = `${forcePct}%`;

            const verd = document.getElementById("cpr-eval-verdict");
            if (fCurr >= 38.0 && fCurr <= 55.0) {
                forceBar.className = "bg-emerald-500 h-full rounded transition-all duration-75 shadow-[0_0_12px_#22c55e]";
                document.getElementById("cpr-force-val").className = "mono text-4xl lg:text-5xl font-black text-emerald-600 tracking-tight";
                if (verd) {
                    verd.innerText = "✅ A'LO ZARBA (38-55 kg)";
                    verd.className = "px-2.5 py-1 rounded-lg text-xs font-black bg-emerald-600 text-white shadow-sm";
                }
            } else if (fCurr > 55.0) {
                forceBar.className = "bg-rose-500 h-full rounded transition-all duration-75 shadow-[0_0_12px_#ef4444]";
                document.getElementById("cpr-force-val").className = "mono text-4xl lg:text-5xl font-black text-rose-600 tracking-tight";
                if (verd) {
                    verd.innerText = "🚨 JUDA QATTIQ (>55 kg)";
                    verd.className = "px-2.5 py-1 rounded-lg text-xs font-black bg-rose-600 text-white shadow-sm";
                }
            } else if (fCurr > 8.0) {
                forceBar.className = "bg-amber-500 h-full rounded transition-all duration-75";
                document.getElementById("cpr-force-val").className = "mono text-4xl lg:text-5xl font-black text-amber-600 tracking-tight";
                if (verd) {
                    verd.innerText = "⚠️ SAYOZ: QATTIQROQ";
                    verd.className = "px-2.5 py-1 rounded-lg text-xs font-black bg-amber-500 text-white shadow-sm";
                }
            } else {
                forceBar.className = "bg-slate-300 h-full rounded transition-all duration-75";
                document.getElementById("cpr-force-val").className = "mono text-4xl lg:text-5xl font-black text-slate-500 tracking-tight";
                if (verd) {
                    verd.innerText = "BOSISHGA TAYYOR";
                    verd.className = "px-2.5 py-1 rounded-lg text-xs font-black bg-slate-200 text-slate-700 shadow-xs";
                }
            }

            // 2. Sifat nishonlari
            updateQualityBadge("badge-d", "Chuqurlik", dOk, fCurr > 10.0);
            updateQualityBadge("badge-r", "Bo'shatish", rOk, fCurr > 10.0);
            updateQualityBadge("badge-bpm", "Tezlik", bpmOk, bpm > 20);
            updateQualityBadge("badge-pos", "Joyi", posOk, fCurr > 5.0);

            // 3. CPR Tezlik BPM
            document.getElementById("cpr-bpm-val").innerText = `${bpm} /min`;
            const rateBadge = document.getElementById("cpr-rate-badge");
            if (bpm >= 100 && bpm <= 120) {
                rateBadge.className = "px-1.5 py-0.5 rounded text-[10px] font-black bg-emerald-100 text-emerald-800 border border-emerald-300";
                rateBadge.innerText = "✅ A'lo tezlik (100-120 /min)";
            } else if (bpm > 120) {
                rateBadge.className = "px-1.5 py-0.5 rounded text-[10px] font-black bg-amber-100 text-amber-800 border border-amber-300";
                rateBadge.innerText = "⚠️ Juda tez (>120 /min)";
            } else if (bpm > 0) {
                rateBadge.className = "px-1.5 py-0.5 rounded text-[10px] font-black bg-amber-100 text-amber-800 border border-amber-300";
                rateBadge.innerText = "⚠️ Sekin (<100 /min)";
            } else {
                rateBadge.className = "px-1.5 py-0.5 rounded text-[10px] font-bold bg-white text-indigo-800 border border-indigo-200";
                rateBadge.innerText = "100 - 120 /min me'yor";
            }

            // 4. O'pka bosimi (0.8 - 2.2 kPa)
            document.getElementById("lung-p-val").innerText = `${lungP.toFixed(1)} kPa`;
            const lungPct = Math.min(100, (lungP / 2.5) * 100);
            document.getElementById("lung-p-bar").style.width = `${lungPct}%`;
            
            const lungStatus = document.getElementById("lung-status-text");
            if (lungP >= 0.8 && lungP <= 2.2) {
                lungStatus.innerText = "✅ TO'G'RI HAJM (0.8 - 2.2 kPa)";
                lungStatus.className = "text-[9px] text-emerald-700 font-black mt-0.5 text-center";
                if (current.spo2 < 99 && current.hr > 0) {
                    current.spo2 = Math.min(100, current.spo2 + 1);
                    updateNumericsUI();
                }
            } else if (lungP > 2.2) {
                lungStatus.innerText = "🚨 JUDA KUCHLI! BAROTRAVMA (>2.2 kPa)";
                lungStatus.className = "text-[9px] text-rose-600 font-black mt-0.5 text-center";
            } else if (lungP >= 0.4) {
                lungStatus.innerText = "⚠️ Kam havo (<0.8 kPa)";
                lungStatus.className = "text-[9px] text-amber-700 font-bold mt-0.5 text-center";
            } else {
                lungStatus.innerText = "Me'yor: 0.8 - 2.2 kPa";
                lungStatus.className = "text-[9px] text-slate-500 font-semibold mt-0.5 text-center";
            }

            // --- 30:2 SIKL: NAFASNI HISOBGA OLISH VA 5 SEKUNDDA SEKIN JONLANISH (22 BPM) ---
            if (lungP >= 0.5 && !window._monitorVentTriggered) {
                window._monitorVentTriggered = true;
                cprCycleVents++;
                if (lungP >= 0.8 && lungP <= 2.2) {
                    cprCycleCorrectVents++;
                }
                updateCycleHUD();

                if (cprCycleComps >= 25 && cprCycleVents >= 2) {
                    const totalActs = cprCycleComps + cprCycleVents;
                    const totalCorrect = cprCycleCorrectComps + cprCycleCorrectVents;
                    const accuracyPct = Math.round((totalCorrect / totalActs) * 100);

                    if (accuracyPct >= 80) {
                        // 1-BOSQICH: 5 SEKUND DAVOMIDA 22 BPM GA SEKIN TIKLANSIN!
                        cprRevivalStage = 1;
                        target.hr = 22;
                        target.spo2 = 62;
                        target.sys = 65;
                        target.dia = 40;
                        target.rr = 6;
                        current.rhythm = "brady";
                        
                        // 50 qadam * 100ms = 5000ms = 5 soniya
                        totalSteps = 50;
                        transitionSteps = 50;
                        stopAsystoleTone();
                        
                        updateBanner(`🟡 1-BOSQICH (Aniqlik: ${accuracyPct}%): YURAK TIKLANMOQDA (~5 soniya -> 22 BPM)...`, "bg-amber-100 text-amber-900 border-amber-400 font-black");

                        const stageBadge = document.getElementById("cpr-stage-badge");
                        if (stageBadge) {
                            stageBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-amber-500 alarm-blink"></span><span>1-BOSQICH: YURAK TIKLANMOQDA (5s -> 22 BPM)</span>`;
                            stageBadge.className = "px-2.5 py-0.5 rounded-lg text-xs font-black bg-amber-100 text-amber-900 border border-amber-400 flex items-center gap-1.5 shadow-sm";
                        }
                    } else {
                        updateBanner(`⚠️ SIKL YETARLI EMAS (Aniqlik: ${accuracyPct}% < 80%). Qayta 30:2 bajaring!`, "bg-rose-100 text-rose-900 border-rose-400 font-bold");
                    }

                    cprCycleComps = 0;
                    cprCycleCorrectComps = 0;
                    cprCycleVents = 0;
                    cprCycleCorrectVents = 0;
                }
            } else if (lungP < 0.3) {
                window._monitorVentTriggered = false;
            }

            // 5. Oshqozon xavfi
            const stomachAlert = document.getElementById("stomach-alert");
            if (stomachP > 0.8) {
                stomachAlert.className = "px-1.5 py-0.5 rounded text-[9px] font-black bg-rose-100 text-rose-800 border border-rose-400 alarm-blink";
                stomachAlert.innerHTML = "⚠️ HAVO OSHQOZONDA!";
            } else {
                stomachAlert.className = "px-1.5 py-0.5 rounded text-[9px] font-bold bg-white text-slate-600 border border-slate-200";
                stomachAlert.innerHTML = "Oshqozon toza";
            }

            // 6. Ukol / Inyeksiya (Touch Pin 4)
            if (injBtn) {
                processInjectionAction();
            } else if (!injectionInProgress) {
                const injBanner = document.getElementById("inj-banner");
                const injBtnEl = document.getElementById("inj-badge-small");
                if (injBanner) injBanner.classList.add("hidden");
                if (injBtnEl) {
                    injBtnEl.className = "mt-1 w-full py-2 px-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-black text-xs shadow-md flex items-center justify-center gap-1.5 transition cursor-pointer active:scale-95 shrink-0";
                }
            }
        }

        // ==================== INJECTION: 5s DELAY + 10s SMOOTH RECOVERY ====================
        function processInjectionAction() {
            if (injectionInProgress) return;

            const injBanner = document.getElementById("inj-banner");
            const injText = document.getElementById("inj-banner-text");
            const injBtnEl = document.getElementById("inj-badge-small");
            if (injBanner) injBanner.classList.remove("hidden");
            if (injBtnEl) {
                injBtnEl.className = "mt-1 w-full py-2 px-2 rounded-lg bg-purple-700 text-white font-black text-xs shadow-md flex items-center justify-center gap-1.5 alarm-blink";
            }

            const flash = document.getElementById("flash-overlay");
            if (flash) {
                flash.classList.add("inj-active");
                setTimeout(() => flash.classList.remove("inj-active"), 1200);
            }

            if (cprRevivalStage === 1 || (current.hr <= 35 && cprCount >= 10)) {
                injectionInProgress = true;
                cprRevivalStage = 2;

                let delaySec = 5;
                const stageBadge = document.getElementById("cpr-stage-badge");
                if (stageBadge) {
                    stageBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-purple-500 alarm-blink"></span><span>2-BOSQICH: ADRENALIN YURAKKA YETIB BORMOQDA (${delaySec}s)...</span>`;
                    stageBadge.className = "px-2.5 py-0.5 rounded-lg text-xs font-black bg-purple-100 text-purple-900 border border-purple-400 flex items-center gap-1.5 shadow-sm";
                }
                const msg = `💉 2-BOSQICH: ADRENALIN 1mg YUBORILDI! DORI QON ORQALI YURAKKA YETIB BORMOQDA (${delaySec} soniya)...`;
                if (injText) injText.innerText = msg;
                updateBanner(msg, "bg-purple-100 text-purple-900 border-purple-400 font-black");

                if (injectionCountdownTimer) clearInterval(injectionCountdownTimer);
                injectionCountdownTimer = setInterval(() => {
                    delaySec--;
                    if (delaySec > 0) {
                        if (stageBadge) {
                            stageBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-purple-500 alarm-blink"></span><span>2-BOSQICH: ADRENALIN YURAKKA YETIB BORMOQDA (${delaySec}s)...</span>`;
                        }
                        const curMsg = `💉 2-BOSQICH: ADRENALIN 1mg YUBORILDI! DORI QON ORQALI YURAKKA YETIB BORMOQDA (${delaySec} soniya)...`;
                        if (injText) injText.innerText = curMsg;
                        updateBanner(curMsg, "bg-purple-100 text-purple-900 border-purple-400 font-black");
                    } else {
                        clearInterval(injectionCountdownTimer);
                        injectionCountdownTimer = null;

                        // 5 sekund kutgandan so'ng -> keyingi 10 sekund davomida sekin-sekin tiklanish (100 * 100ms = 10000ms = 10 soniya)
                        target = { hr: 75, spo2: 98, sys: 120, dia: 80, rr: 16, temp: 36.6, mode: "normal", rhythm: "sinus" };
                        totalSteps = 100;
                        transitionSteps = 100;
                        stopAsystoleTone();

                        if (stageBadge) {
                            stageBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-500 alarm-blink"></span><span>2-BOSQICH: YURAK RITMI SEKIN TIKLANMOQDA (10s -> 75 BPM)</span>`;
                            stageBadge.className = "px-2.5 py-0.5 rounded-lg text-xs font-black bg-emerald-100 text-emerald-900 border border-emerald-400 flex items-center gap-1.5 shadow-sm";
                        }
                        const recMsg = `🟢 2-BOSQICH: ADRENALIN TA'SIR QILDI! YURAK RITMI SEKIN TIKLANMOQDA (10 soniya davomida 75 BPM ga)...`;
                        if (injText) injText.innerText = recMsg;
                        updateBanner(recMsg, "bg-emerald-100 text-emerald-900 border-emerald-400 font-black");
                    }
                }, 1000);
            } else {
                updateBanner("💉 ADRENALIN 1mg YUBORILDI!", "bg-purple-100 text-purple-900 border-purple-400 font-bold");
                setTimeout(() => {
                    if (injBanner) injBanner.classList.add("hidden");
                    if (injBtnEl) {
                        injBtnEl.className = "mt-1 w-full py-2 px-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-black text-xs shadow-md flex items-center justify-center gap-1.5 transition cursor-pointer active:scale-95 shrink-0";
                    }
                }, 1500);
            }
        }

        function triggerManualInjection() {
            processInjectionAction();
            handleHardwareData({
                force: lastRawMonitorForce,
                pos_btn: 1,
                inj_btn: 1,
                lung_p: 0,
                stomach_p: 0
            });
            setTimeout(() => {
                handleHardwareData({
                    force: lastRawMonitorForce,
                    pos_btn: 0,
                    inj_btn: 0,
                    lung_p: 0,
                    stomach_p: 0
                });
            }, 1500);
        }

        function updateQualityBadge(id, label, isOk, isActive) {
            const el = document.getElementById(id);
            if (!el) return;
            if (!isActive) {
                el.className = "p-0.5 rounded bg-white border border-slate-200 text-slate-500 text-center font-bold shadow-xs";
                el.innerText = `${label}: -`;
            } else if (isOk) {
                el.className = "p-0.5 rounded bg-emerald-100 border border-emerald-300 text-emerald-800 text-center font-black shadow-xs";
                el.innerText = `${label}: ✅`;
            } else {
                el.className = "p-0.5 rounded bg-rose-100 border border-rose-300 text-rose-800 text-center font-black shadow-xs";
                el.innerText = `${label}: ❌`;
            }
        }

        function connectTelemetryWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;
            const ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                if (!isSerialConnected) {
                    document.getElementById("hw-dot").className = "w-2 h-2 rounded-full bg-emerald-500";
                    document.getElementById("hw-text").innerText = "ESP32 UART: Jonli";
                }
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleHardwareData(data);
                } catch(e) {}
            };

            ws.onclose = () => {
                if (!isSerialConnected) {
                    document.getElementById("hw-dot").className = "w-2 h-2 rounded-full bg-amber-500";
                    document.getElementById("hw-text").innerText = "ESP32: Qayta ulanmoqda";
                }
                setTimeout(connectTelemetryWebSocket, 1500);
            };
        }

        // ==================== KLINIK SSENARIYLAR ====================
        function setScenario(type) {
            initAudio();
            cprRevivalStage = 0;
            totalSteps = 120;
            transitionSteps = totalSteps;

            if (injectionCountdownTimer) {
                clearInterval(injectionCountdownTimer);
                injectionCountdownTimer = null;
            }
            injectionInProgress = false;

            const stageBadge = document.getElementById("cpr-stage-badge");
            const injBanner = document.getElementById("inj-banner");
            if (injBanner) injBanner.classList.add("hidden");

            if (type === "dying") {
                target.hr = 0; target.spo2 = 0; target.sys = 0; target.dia = 0; target.rr = 0;
                current.hr = 0; current.spo2 = 0; current.sys = 0; current.dia = 0; current.rr = 0;
                current.rhythm = "asystole";
                transitionSteps = 0;
                totalSteps = 0;
                updateNumericsUI();
                updateBanner("🚨 ASISTOLIYA: YURAK TO'XTADI (0 BPM)! CPR (30:2) TALAB QILINADI!", "bg-rose-100 text-rose-900 border-rose-400 alarm-blink font-black");
                if (stageBadge) {
                    stageBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-rose-500 alarm-blink"></span><span>0-BOSQICH: ASISTOLIYA (CPR TALAB QILINADI)</span>`;
                    stageBadge.className = "px-2.5 py-0.5 rounded-lg text-xs font-black bg-rose-100 text-rose-900 border border-rose-400 flex items-center gap-1.5 shadow-sm";
                }
                startAsystoleTone();
                return;
            }

            if (type === "normal") {
                target = { hr: 75, spo2: 98, sys: 120, dia: 80, rr: 16, temp: 36.6, mode: "normal", rhythm: "sinus" };
                updateBanner("🟢 STATUS: BARQAROR (NORMAL)", "bg-emerald-100 text-emerald-900 border-emerald-300 font-bold");
                if (stageBadge) {
                    stageBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-500"></span><span>STATUS: BARQAROR NORMAL (75 BPM)</span>`;
                    stageBadge.className = "px-2.5 py-0.5 rounded-lg text-xs font-black bg-emerald-100 text-emerald-900 border border-emerald-400 flex items-center gap-1.5 shadow-sm";
                }
                stopAsystoleTone();
            } else if (type === "attack") {
                target = { hr: 185, spo2: 88, sys: 210, dia: 125, rr: 34, temp: 37.4, mode: "attack", rhythm: "vtach" };
                updateBanner("⚡ XURUJ: O'TKIR TAXIKARDIYA VA GIPERTONIK KRIZ!", "bg-amber-100 text-amber-900 border-amber-400 alarm-blink font-black");
                stopAsystoleTone();
            } else if (type === "hypoxia") {
                target = { hr: 135, spo2: 74, sys: 135, dia: 90, rr: 38, temp: 36.8, mode: "hypoxia", rhythm: "sinus" };
                updateBanner("🫁 GIPOKSIYA: BO'G'ILISH VA KISLOROD YETISHMOVCHILIGI!", "bg-sky-100 text-sky-900 border-sky-400 alarm-blink font-black");
                stopAsystoleTone();
            } else if (type === "shock") {
                target = { hr: 145, spo2: 89, sys: 65, dia: 35, rr: 28, temp: 35.8, mode: "shock", rhythm: "sinus" };
                updateBanner("🩸 SHOK: QON BOSIMINING KESKIN TUSHISHI!", "bg-purple-100 text-purple-900 border-purple-400 alarm-blink font-black");
                stopAsystoleTone();
            }
        }

        function defibrillateShock() {
            initAudio();
            const flash = document.getElementById("flash-overlay");
            flash.classList.add("shock-active");
            setTimeout(() => flash.classList.remove("shock-active"), 600);

            try {
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = "sawtooth";
                osc.frequency.setValueAtTime(160, audioCtx.currentTime);
                osc.frequency.exponentialRampToValueAtTime(45, audioCtx.currentTime + 0.3);
                gain.gain.setValueAtTime(0.4, audioCtx.currentTime);
                gain.gain.linearRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
                osc.connect(gain);
                gain.connect(masterCompressor || audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + 0.3);
            } catch(e) {}

            setTimeout(() => {
                setScenario("normal");
            }, 700);
        }

        function updateBanner(text, classes) {
            const b = document.getElementById("alarm-banner");
            b.className = `px-3 py-0.5 rounded-lg text-xs uppercase tracking-wider border ${classes}`;
            b.innerHTML = text;
        }

        setInterval(() => {
            if (transitionSteps > 0) {
                const factor = 1 / transitionSteps;
                current.hr += (target.hr - current.hr) * factor;
                current.spo2 += (target.spo2 - current.spo2) * factor;
                current.sys += (target.sys - current.sys) * factor;
                current.dia += (target.dia - current.dia) * factor;
                current.rr += (target.rr - current.rr) * factor;
                current.temp += (target.temp - current.temp) * factor;
                
                transitionSteps--;
                if (transitionSteps === 0) {
                    current = { ...target };
                    if (current.hr <= 0) {
                        current.rhythm = "asystole";
                        startAsystoleTone();
                    } else if (cprRevivalStage === 1 && Math.round(current.hr) >= 20) {
                        updateBanner("🟡 1-BOSQICH: YURAK 22 BPM URMOQDA! ENDI UKOL (ADRENALIN) QILISH KERAK!", "bg-amber-100 text-amber-900 border-amber-400 font-black");
                        const stageBadge = document.getElementById("cpr-stage-badge");
                        if (stageBadge) {
                            stageBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-amber-500 alarm-blink"></span><span>1-BOSQICH: YURAK 22 BPM URMOQDA (ADRENALIN KUTILMOQDA)</span>`;
                            stageBadge.className = "px-2.5 py-0.5 rounded-lg text-xs font-black bg-amber-100 text-amber-900 border border-amber-400 flex items-center gap-1.5 shadow-sm";
                        }
                    } else if (cprRevivalStage === 2 && Math.round(current.hr) >= 70) {
                        updateBanner("🟢 2-BOSQICH MUVAFFAQIYAT: BEMOR TO'LIQ O'ZIGA KELDI (BARQAROR 75 BPM, ROSC)!", "bg-emerald-100 text-emerald-900 border-emerald-400 font-black");
                        const stageBadge = document.getElementById("cpr-stage-badge");
                        if (stageBadge) {
                            stageBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-500"></span><span>2-BOSQICH: BEMOR TO'LIQ O'ZIGA KELDI (BARQAROR 75 BPM)</span>`;
                            stageBadge.className = "px-2.5 py-0.5 rounded-lg text-xs font-black bg-emerald-100 text-emerald-900 border border-emerald-400 flex items-center gap-1.5 shadow-sm";
                        }
                        const injBanner = document.getElementById("inj-banner");
                        if (injBanner) injBanner.classList.add("hidden");
                        injectionInProgress = false;
                    }
                }
                updateNumericsUI();
            }
        }, 100);

        function updateNumericsUI() {
            const hrVal = Math.round(current.hr);
            const spo2Val = Math.round(current.spo2);
            const sysVal = Math.round(current.sys);
            const diaVal = Math.round(current.dia);
            const mapVal = Math.round((sysVal + 2 * diaVal) / 3);
            const rrVal = Math.round(current.rr);

            document.getElementById("num-hr").innerText = hrVal;
            document.getElementById("num-pr").innerText = hrVal;
            document.getElementById("num-spo2").innerText = spo2Val;
            document.getElementById("num-sys").innerText = sysVal;
            document.getElementById("num-dia").innerText = diaVal;
            document.getElementById("num-map").innerText = mapVal;
            document.getElementById("num-rr").innerText = rrVal;
            document.getElementById("num-temp").innerText = current.temp.toFixed(1);

            const rhythmLabel = document.getElementById("ecg-rhythm-name");
            if (hrVal <= 0) {
                rhythmLabel.innerText = "ASYSTOLIYA (0 BPM)";
                rhythmLabel.className = "text-xs font-black text-rose-600 alarm-blink";
            } else if (hrVal <= 35) {
                rhythmLabel.innerText = `Bradikardiya (${hrVal} BPM)`;
                rhythmLabel.className = "text-xs font-black text-amber-600";
            } else if (hrVal > 150) {
                rhythmLabel.innerText = "Ventrikulyar Taxikardiya";
                rhythmLabel.className = "text-xs font-black text-amber-600";
            } else {
                rhythmLabel.innerText = "Sinus Ritmi";
                rhythmLabel.className = "text-xs font-bold text-emerald-700";
            }
        }

        // ==================== CANVAS OSCILLOSCOPES (BALANCED WHITE MEDICAL) ====================
        const ecgCanvas = document.getElementById("ecgCanvas");
        const plethCanvas = document.getElementById("plethCanvas");

        const ecgCtx = ecgCanvas.getContext("2d");
        const plethCtx = plethCanvas.getContext("2d");

        function resizeCanvases() {
            [ecgCanvas, plethCanvas].forEach(c => {
                if (!c) return;
                c.width = c.clientWidth * (window.devicePixelRatio || 1) || c.clientWidth;
                c.height = c.clientHeight * (window.devicePixelRatio || 1) || c.clientHeight;
            });
        }
        window.addEventListener("resize", resizeCanvases);
        setTimeout(resizeCanvases, 100);

        let ecgX = 0;
        let plethX = 0;

        let ecgPhase = 0;
        let plethPhase = 0;

        let lastEcgY = null;
        let lastPlethY = null;

        function getECGY(phase, hr) {
            if (hr <= 0) return 0;
            if (hr > 160) return Math.sin(phase * Math.PI * 2) * 0.8;
            const p = phase % 1.0;
            if (p < 0.15) return 0;
            if (p >= 0.15 && p < 0.25) return Math.sin(((p - 0.15) / 0.10) * Math.PI) * 0.18;
            if (p >= 0.25 && p < 0.30) return 0;
            if (p >= 0.30 && p < 0.33) return -Math.sin(((p - 0.30) / 0.03) * Math.PI) * 0.15;
            if (p >= 0.33 && p < 0.38) {
                const sub = (p - 0.33) / 0.05;
                return sub < 0.5 ? (sub / 0.5) : (1.0 - (sub - 0.5) / 0.5);
            }
            if (p >= 0.38 && p < 0.42) return -Math.sin(((p - 0.38) / 0.04) * Math.PI) * 0.30;
            if (p >= 0.42 && p < 0.50) return 0;
            if (p >= 0.50 && p < 0.70) return Math.sin(((p - 0.50) / 0.20) * Math.PI) * 0.28;
            return 0;
        }

        function getPlethY(phase, hr, spo2) {
            if (hr <= 0 || spo2 <= 0) return 0;
            const p = phase % 1.0;
            const amp = (spo2 / 100);
            if (p < 0.35) return Math.sin(p / 0.35 * (Math.PI / 2)) * amp;
            if (p < 0.55) return (Math.cos(((p - 0.35) / 0.20) * Math.PI) * 0.25 + 0.65) * amp;
            return (Math.cos(((p - 0.55) / 0.45) * (Math.PI / 2)) * 0.4) * amp;
        }

        function animate() {
            const hr = current.hr;
            const spo2 = current.spo2;

            const w = ecgCanvas.width;
            const hEcg = ecgCanvas.height;
            const hPleth = plethCanvas.height;

            const sweepSpeed = 2.2 * (window.devicePixelRatio || 1);
            const eraseWidth = 24 * (window.devicePixelRatio || 1);

            const bps = hr / 60;
            ecgPhase += (bps / 60);
            plethPhase += (bps / 60);

            const currentP = ecgPhase % 1.0;
            if (currentP >= 0.33 && currentP < 0.38) {
                const now = Date.now();
                if (now - lastBeatTime > (60000 / Math.max(20, hr)) * 0.8) {
                    playQRSBeep();
                    lastBeatTime = now;
                }
            }

            // 1. ECG (Crisp Medical Green #16a34a)
            const nextEcgX = (ecgX + sweepSpeed) % w;
            ecgCtx.fillStyle = "#ffffff";
            ecgCtx.fillRect(nextEcgX, 0, eraseWidth, hEcg);

            const ecgVal = getECGY(ecgPhase, hr);
            const midEcg = hEcg / 2;
            const curEcgY = midEcg - (ecgVal * (hEcg * 0.42));

            if (lastEcgY !== null && nextEcgX > ecgX) {
                ecgCtx.strokeStyle = "#16a34a";
                ecgCtx.lineWidth = 2.4 * (window.devicePixelRatio || 1);
                ecgCtx.beginPath();
                ecgCtx.moveTo(ecgX, lastEcgY);
                ecgCtx.lineTo(nextEcgX, curEcgY);
                ecgCtx.stroke();
            }
            ecgX = nextEcgX;
            lastEcgY = curEcgY;

            // 2. SpO2 Pleth (Deep Medical Cyan #0284c7)
            const nextPlethX = (plethX + sweepSpeed) % w;
            plethCtx.fillStyle = "#ffffff";
            plethCtx.fillRect(nextPlethX, 0, eraseWidth, hPleth);

            const plethVal = getPlethY(plethPhase, hr, spo2);
            const curPlethY = hPleth - 8 - (plethVal * (hPleth * 0.8));

            if (lastPlethY !== null && nextPlethX > plethX) {
                plethCtx.strokeStyle = "#0284c7";
                plethCtx.lineWidth = 2.2 * (window.devicePixelRatio || 1);
                plethCtx.beginPath();
                plethCtx.moveTo(plethX, lastPlethY);
                plethCtx.lineTo(nextPlethX, curPlethY);
                plethCtx.stroke();
            }
            plethX = nextPlethX;
            lastPlethY = curPlethY;

            requestAnimationFrame(animate);
        }

        setInterval(() => {
            const d = new Date();
            document.getElementById("clock").innerText = d.toTimeString().split(' ')[0];
        }, 1000);

        function toggleFullScreen() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen();
            } else {
                if (document.exitFullscreen) document.exitFullscreen();
            }
        }

        let deferredPromptVital = null;
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js').catch(() => {});
            });
        }
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPromptVital = e;
            const btn = document.getElementById('pwa-vital-btn');
            if (btn) btn.classList.remove('hidden');
        });
        async function installVitalPWA() {
            if (deferredPromptVital) {
                deferredPromptVital.prompt();
                const { outcome } = await deferredPromptVital.userChoice;
                if (outcome === 'accepted') {
                    const btn = document.getElementById('pwa-vital-btn');
                    if (btn) btn.classList.add('hidden');
                }
                deferredPromptVital = null;
            } else {
                alert("Ilovani o'rnatish uchun brauzer menyusidagi 'O'rnatish' (Install App) tugmasini bosing.");
            }
        }

        window.onload = () => {
            updateNumericsUI();
            connectTelemetryWebSocket();
            requestAnimationFrame(animate);
        };
    </script>
</body>
</html>
"""

# ==================== PYTHON BACKEND SERIAL COM PORT BRIDGE ====================
active_serial_port = None
serial_lock = threading.Lock()

def send_serial_hw_command(cmd: str):
    global active_serial_port
    if not serial:
        return False
    with serial_lock:
        if active_serial_port and active_serial_port.is_open:
            try:
                active_serial_port.write((cmd + "\r\n").encode("utf-8"))
                active_serial_port.flush()
                return True
            except Exception as e:
                print(f"Serial port yozish xatosi: {e}")
                try: active_serial_port.close()
                except: pass
                active_serial_port = None
    return False

def auto_detect_arduino_port():
    global active_serial_port
    if not serial:
        return
    while True:
        if not active_serial_port or not active_serial_port.is_open:
            try:
                ports = list(serial.tools.list_ports.comports())
                for p in ports:
                    desc = (p.description or "").lower()
                    hwid = (p.hwid or "").lower()
                    if any(k in desc or k in hwid for k in ["ch340", "cp210", "usb-serial", "arduino", "uart", "ftdi", "silicon"]):
                        try:
                            s = serial.Serial(p.device, 115200, timeout=0.1)
                            time.sleep(1.6)
                            active_serial_port = s
                            print(f"✅ Backend Arduino/ESP32 USB porti ulandi: {p.device}")
                            break
                        except Exception:
                            pass
            except Exception:
                pass
        time.sleep(3.0)

threading.Thread(target=auto_detect_arduino_port, daemon=True).start()

class CompressorRequest(BaseModel):
    cmd: str

@app.get("/", response_class=HTMLResponse)
@app.get("/vital", response_class=HTMLResponse)
async def get_monitor():
    return HTMLResponse(content=HTML_CONTENT)

@app.post("/api/compressor")
async def api_compressor(req: CompressorRequest):
    return JSONResponse(content={"status": "ok", "cmd": req.cmd})

@app.post("/api/telemetry")
async def post_telemetry(request: Request):
    global latest_telemetry
    try:
        data = await request.json()
        latest_telemetry = data
        for ws in active_websockets:
            try:
                await ws.send_text(json.dumps(data))
            except:
                pass
        return JSONResponse(content={"status": "ok", "received": data})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            try:
                data = json.loads(msg)
                for ws in active_websockets:
                    if ws != websocket:
                        await ws.send_text(json.dumps(data))
            except:
                pass
    except WebSocketDisconnect:
        if websocket in active_websockets:
            active_websockets.remove(websocket)

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == "__main__":
    local_ip = get_local_ip()
    port = int(os.environ.get("PORT", 8500))
    print("=" * 65)
    print("  🏥 ICU BEMOR MONITORI - ESP32 TELEMETRIYASI")
    print("=" * 65)
    print(f"  Monitor ekrani:       http://localhost:{port}")
    print(f"  JSON qabul qilish:    POST http://localhost:{port}/api/telemetry")
    print("=" * 65 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
