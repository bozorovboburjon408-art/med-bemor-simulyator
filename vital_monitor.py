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
    <title>ICU Bemor Hayotiy Ko'rsatkichlari Monitori (ESP32)</title>
    <meta name="theme-color" content="#ffffff">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Vital Monitor">
    <link rel="manifest" href="/manifest_vital.json">
    <link rel="icon" href="/static/icons/vital_192.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@500;600;700;800&display=swap');
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
            50% { opacity: 0.3; }
        }
        .alarm-blink {
            animation: alarmBlink 0.8s infinite;
        }
    </style>
</head>
<body class="h-screen w-screen bg-slate-100 text-slate-800 flex flex-col justify-between p-2 overflow-hidden select-none">

    <div id="flash-overlay" class="fixed inset-0 pointer-events-none z-50"></div>

    <!-- 1. TOP MEDICAL HEADER -->
    <header class="bg-white border border-slate-200 rounded-xl px-3 py-1.5 flex flex-wrap items-center justify-between gap-2 shadow-xs shrink-0">
        <div class="flex items-center space-x-3">
            <div class="flex items-center space-x-2">
                <span class="w-3 h-3 rounded-full bg-emerald-500 alarm-blink"></span>
                <span class="font-extrabold text-base tracking-wider text-slate-900">ICU PATIENT MONITOR</span>
            </div>
            <div class="text-xs text-slate-500 border-l border-slate-300 pl-3">
                KOYKA: <span class="text-slate-900 font-bold">#04 (Reanimatsiya)</span>
            </div>
            <div class="text-xs text-slate-500 border-l border-slate-300 pl-3">
                BEMOR: <span class="text-emerald-700 font-bold">Anvar Karimov (40 yosh)</span>
            </div>
        </div>

        <div id="alarm-banner" class="px-3 py-0.5 rounded-lg text-xs font-bold uppercase tracking-wider bg-emerald-100 text-emerald-800 border border-emerald-300 transition-all duration-300">
            <i class="fa-solid fa-heart-pulse mr-1"></i> STATUS: BARQAROR (NORMAL)
        </div>

        <div class="flex flex-wrap items-center gap-1.5 text-xs">
            <a href="/hub" class="px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300 flex items-center gap-1 transition font-bold shadow-xs">
                <i class="fa-solid fa-hospital text-cyan-600"></i>
                <span>Hub</span>
            </a>

            <button id="pwa-vital-btn" onclick="installVitalPWA()" class="hidden px-2 py-1 rounded-lg bg-amber-400 hover:bg-amber-300 text-slate-950 flex items-center gap-1 font-black shadow-xs cursor-pointer transition">
                <i class="fa-solid fa-download"></i>
                <span>O'rnatish</span>
            </button>

            <a href="/" target="_blank" class="px-2 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 flex items-center gap-1 transition font-bold shadow-xs">
                <i class="fa-solid fa-hospital-user text-indigo-600"></i>
                <span>AI Bemor</span>
            </a>

            <a href="/console" target="_blank" class="px-2 py-1 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 flex items-center gap-1 transition font-bold shadow-xs">
                <i class="fa-solid fa-hand-holding-heart text-purple-600"></i>
                <span>Pult & CPR</span>
            </a>

            <div id="hw-badge" class="px-2 py-1 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 flex items-center gap-1.5 font-bold">
                <span id="hw-dot" class="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span id="hw-text">ESP32 UART: Jonli</span>
            </div>

            <!-- VOLUME CONTROL (100% MAKSIMAL) -->
            <div class="flex items-center gap-1.5 bg-slate-100 border border-slate-300 px-2 py-1 rounded-lg">
                <button id="btn-audio" onclick="toggleAudio()" class="text-slate-700 hover:text-slate-900 flex items-center gap-1 cursor-pointer transition">
                    <i id="audio-icon" class="fa-solid fa-volume-high text-emerald-600 text-xs"></i>
                    <span id="audio-text" class="text-xs font-bold">100%</span>
                </button>
                <input type="range" id="monitor-volume-slider" min="0" max="1" step="0.05" value="1.0" oninput="changeMonitorVolume(this.value)" class="w-14 accent-emerald-600 h-1.5 bg-slate-300 rounded cursor-pointer" title="Yurak urish ovoz balandligi (100% Maksimal)">
            </div>

            <button onclick="toggleFullScreen()" class="px-2 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300 cursor-pointer">
                <i class="fa-solid fa-expand"></i>
            </button>
            <span id="clock" class="mono text-xs font-bold text-slate-700">00:00:00</span>
        </div>
    </header>

    <!-- INJECTION NOTIFICATION POPUP -->
    <div id="inj-banner" class="hidden my-1 bg-purple-100 border border-purple-400 rounded-xl p-2 shadow-sm text-center text-purple-900 text-xs font-bold alarm-blink">
        <i class="fa-solid fa-syringe text-purple-600 text-sm mr-1"></i> 
        <span>💉 UKOL QILINDI (ADRENALIN 1mg)! FARMAKOLOGIK TA'SIR KUZATILMOQDA...</span>
    </div>

    <!-- 2. LIVE MANIKEN SENSOR TELEMETRY & CPR 30:2 HUD -->
    <div id="cpr-hud" class="bg-white border border-slate-200 rounded-xl p-2 my-1 shadow-xs grid grid-cols-2 md:grid-cols-5 gap-2 items-center text-xs shrink-0">
        
        <!-- 1. CPR Compression Force -->
        <div class="flex flex-col border-r border-slate-200 pr-2">
            <div class="flex justify-between items-center text-xs font-bold text-slate-700 mb-0.5">
                <span><i class="fa-solid fa-hand-fist mr-1 text-rose-600"></i> KUCH:</span>
                <div class="flex items-center gap-1">
                    <span id="cpr-force-val" class="mono text-rose-600 font-extrabold text-sm">0.0 kg</span>
                    <button type="button" onclick="tareCprForce()" title="Boshlang'ich vaznni 0 qilish (Tare)" class="px-1.5 py-0.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded border border-slate-300 text-[9px] font-bold cursor-pointer active:scale-95 transition flex items-center gap-0.5">
                        <i class="fa-solid fa-scale-balanced text-[8px]"></i> 0 qilish
                    </button>
                </div>
            </div>
            <div class="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden relative">
                <div id="cpr-force-bar" class="bg-rose-500 h-full rounded-full transition-all duration-75" style="width: 0%;"></div>
                <div class="absolute inset-y-0 left-[63%] w-[28%] bg-emerald-500/20 border-x border-emerald-500/50 pointer-events-none"></div>
            </div>
            <div class="flex justify-between text-[9px] text-slate-500 mt-0.5">
                <span>0 kg</span>
                <span class="text-emerald-700 font-bold">Me'yor (38-55 kg)</span>
                <span>60 kg</span>
            </div>
        </div>

        <!-- 2. CPR 30:2 Cycle Tracker & Quality -->
        <div class="flex flex-col border-r border-slate-200 pr-2 justify-between">
            <div class="text-[11px] font-bold text-slate-700 mb-0.5 flex items-center justify-between">
                <span><i class="fa-solid fa-clipboard-check text-indigo-600"></i> SIKL (30:2):</span>
                <span id="cpr-cycle-badge" class="text-xs mono font-black text-indigo-700">0/30 zarba | 0/2 nafas</span>
            </div>
            <div class="grid grid-cols-2 gap-1 text-[9px]">
                <span id="badge-d" class="px-1 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600 text-center font-bold">Chuqurlik: -</span>
                <span id="badge-r" class="px-1 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600 text-center font-bold">Bo'shatish: -</span>
                <span id="badge-bpm" class="px-1 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600 text-center font-bold">Tezlik: -</span>
                <span id="badge-pos" class="px-1 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-600 text-center font-bold">Joyi: -</span>
            </div>
        </div>

        <!-- 3. CPR BPM Speed -->
        <div class="flex flex-col border-r border-slate-200 pr-2 justify-center">
            <div class="flex justify-between items-center text-xs font-bold text-slate-700 mb-0.5">
                <span><i class="fa-solid fa-gauge text-slate-600"></i> CPR TEZLIK:</span>
                <span id="cpr-bpm-val" class="mono text-emerald-700 font-bold text-sm">0 /min</span>
            </div>
            <div id="cpr-rate-badge" class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-200 text-center">
                Standart: 100 - 120 /min
            </div>
        </div>

        <!-- 4. Lung Pressure -->
        <div class="flex flex-col border-r border-slate-200 pr-2">
            <div class="flex justify-between items-center text-xs font-bold text-sky-800 mb-0.5">
                <span><i class="fa-solid fa-lungs mr-1 text-sky-600"></i> O'PKA (lung_p):</span>
                <span id="lung-p-val" class="mono text-sky-700 font-extrabold text-sm">0.0 kPa</span>
            </div>
            <div class="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
                <div id="lung-p-bar" class="bg-sky-500 h-full rounded-full transition-all duration-75" style="width: 0%;"></div>
            </div>
            <div id="lung-status-text" class="text-[9px] text-sky-700 mt-0.5 font-bold">Me'yor: 0.8 - 2.2 kPa</div>
        </div>

        <!-- 5. Stomach Alert & Injection Action -->
        <div class="flex flex-col justify-between">
            <div class="flex justify-between items-center text-xs font-bold text-slate-700 mb-0.5">
                <span><i class="fa-solid fa-circle-exclamation text-amber-500"></i> OSHQOZON:</span>
                <span id="stomach-p-val" class="mono text-slate-700 font-bold text-xs">0.0</span>
            </div>
            <div id="stomach-alert" class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-slate-100 text-slate-600 border border-slate-200 text-center">
                Oshqozon toza
            </div>
            <button type="button" onclick="triggerManualInjection()" id="inj-badge-small" class="mt-1 w-full py-0.5 px-1.5 rounded bg-purple-100 hover:bg-purple-200 text-purple-800 border border-purple-300 font-bold text-[10px] flex items-center justify-center gap-1 transition cursor-pointer active:scale-95 shadow-xs">
                <i class="fa-solid fa-syringe text-purple-600"></i> 💉 Ukol Qilish (Adrenalin)
            </button>
        </div>

    </div>

    <!-- 3. MAIN MONITOR DISPLAY (WAVEFORMS + VITAL NUMERICS - ZERO SCROLL FIT) -->
    <div class="grid grid-cols-1 lg:grid-cols-4 gap-2 my-0.5 flex-1 min-h-0 overflow-hidden">
        
        <!-- LEFT 3 COLUMNS: LIVE MEDICAL OSCILLOSCOPE (WHITE CLINICAL BACKGROUND) -->
        <div class="lg:col-span-3 bg-white border border-slate-200 rounded-xl p-2 flex flex-col justify-between shadow-xs overflow-hidden">
            
            <!-- 1. ECG WAVEFORM (Deep Medical Green) -->
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

            <!-- 2. SpO2 PLETHYSMOGRAM WAVEFORM (Deep Medical Cyan/Blue) -->
            <div class="flex-1 flex flex-col min-h-0 py-1 border-b border-slate-100">
                <div class="flex justify-between items-center text-xs font-bold text-sky-800 mb-0.5 shrink-0">
                    <span class="flex items-center gap-1.5">
                        <i class="fa-solid fa-wave-square text-sky-600"></i> SpO2 Pleth
                        <span class="text-[10px] text-slate-400 font-normal">Puls to'lqini</span>
                    </span>
                    <span id="pleth-status" class="font-extrabold text-sky-700">Normal perfuziya</span>
                </div>
                <div class="flex-1 relative min-h-0 rounded-lg bg-white border border-slate-200 overflow-hidden">
                    <canvas id="plethCanvas" class="w-full h-full block"></canvas>
                </div>
            </div>

            <!-- 3. RESPIRATION WAVEFORM (Deep Medical Amber) -->
            <div class="flex-1 flex flex-col min-h-0 pt-1">
                <div class="flex justify-between items-center text-xs font-bold text-amber-800 mb-0.5 shrink-0">
                    <span class="flex items-center gap-1.5">
                        <i class="fa-solid fa-lungs text-amber-600"></i> RESP (Nafas olish)
                        <span class="text-[10px] text-slate-400 font-normal">Pneumography</span>
                    </span>
                    <span id="resp-status" class="font-extrabold text-amber-700">Ritmli nafas</span>
                </div>
                <div class="flex-1 relative min-h-0 rounded-lg bg-white border border-slate-200 overflow-hidden">
                    <canvas id="respCanvas" class="w-full h-full block"></canvas>
                </div>
            </div>

        </div>

        <!-- RIGHT 1 COLUMN: VITAL NUMERIC BOXES (COMPACT CLINICAL WHITE CARDS) -->
        <div class="flex flex-col justify-between gap-1.5 min-h-0 overflow-hidden">
            
            <!-- HR / PULSE (Green Card) -->
            <div class="bg-white border border-emerald-300 rounded-xl p-2 shadow-xs flex-1 flex flex-col justify-between">
                <div class="flex justify-between items-center text-emerald-800 font-bold text-xs">
                    <span><i class="fa-solid fa-heart-pulse mr-1 text-emerald-600"></i> HR / PULS</span>
                    <span class="text-[10px] text-slate-400">bpm</span>
                </div>
                <div class="flex items-baseline justify-between my-0.5">
                    <span id="num-hr" class="mono text-4xl lg:text-5xl font-black text-emerald-600 leading-none">75</span>
                    <div class="text-right text-[10px] text-slate-500 font-semibold leading-tight">
                        <div>YUQ: 120</div>
                        <div>PAS: 50</div>
                    </div>
                </div>
                <div class="flex justify-between text-[10px] text-slate-500 border-t border-slate-100 pt-0.5">
                    <span>Kompressiyalar: <span id="num-count" class="font-bold text-emerald-700">0</span></span>
                    <span>Puls: Normal</span>
                </div>
            </div>

            <!-- SpO2 (Blue Card) -->
            <div class="bg-white border border-sky-300 rounded-xl p-2 shadow-xs flex-1 flex flex-col justify-between">
                <div class="flex justify-between items-center text-sky-800 font-bold text-xs">
                    <span><i class="fa-solid fa-droplet mr-1 text-sky-600"></i> SpO2 (Kislorod)</span>
                    <span class="text-[10px] text-slate-400">%</span>
                </div>
                <div class="flex items-baseline justify-between my-0.5">
                    <span id="num-spo2" class="mono text-4xl lg:text-5xl font-black text-sky-600 leading-none">98</span>
                    <div class="text-right text-[10px] text-slate-500 font-semibold leading-tight">
                        <div>PI: 4.2%</div>
                        <div>PAS: 90%</div>
                    </div>
                </div>
                <div class="flex justify-between text-[10px] text-slate-500 border-t border-slate-100 pt-0.5">
                    <span>Puls: <span id="num-pr" class="font-bold text-sky-700">75</span></span>
                    <span>Signal: Kuchli</span>
                </div>
            </div>

            <!-- NIBP (Blood Pressure Card) -->
            <div class="bg-white border border-slate-300 rounded-xl p-2 shadow-xs flex-1 flex flex-col justify-between">
                <div class="flex justify-between items-center text-slate-800 font-bold text-xs">
                    <span><i class="fa-solid fa-gauge-high mr-1 text-indigo-600"></i> NIBP (Davleniya)</span>
                    <span class="text-[10px] text-slate-400">mmHg</span>
                </div>
                <div class="flex items-baseline justify-between my-0.5">
                    <div class="text-slate-800 font-black leading-none">
                        <span id="num-sys" class="mono text-2xl lg:text-3xl font-black">120</span>
                        <span class="text-slate-400 text-lg">/</span>
                        <span id="num-dia" class="mono text-2xl lg:text-3xl font-black">80</span>
                    </div>
                    <div class="text-right text-[11px] text-slate-600 font-bold">
                        MAP: <span id="num-map" class="text-emerald-700">93</span>
                    </div>
                </div>
                <div class="flex justify-between text-[10px] text-slate-500 border-t border-slate-100 pt-0.5">
                    <span>Avto: 15min</span>
                    <span>Holat: Barqaror</span>
                </div>
            </div>

            <!-- RR & TEMP (Mini Split Card) -->
            <div class="grid grid-cols-2 gap-1.5">
                <div class="bg-white border border-amber-300 rounded-xl p-1.5 text-center shadow-xs flex flex-col justify-between">
                    <div class="text-[10px] font-bold text-amber-800 flex items-center justify-between">
                        <span><i class="fa-solid fa-lungs mr-0.5 text-amber-600"></i> RR</span>
                        <span class="text-slate-400">rpm</span>
                    </div>
                    <span id="num-rr" class="mono text-2xl font-black text-amber-600 my-0.5">16</span>
                    <div class="text-[9px] text-slate-400">Ritmli nafas</div>
                </div>

                <div class="bg-white border border-purple-300 rounded-xl p-1.5 text-center shadow-xs flex flex-col justify-between">
                    <div class="text-[10px] font-bold text-purple-800 flex items-center justify-between">
                        <span><i class="fa-solid fa-temperature-three-quarters mr-0.5 text-purple-600"></i> TEMP</span>
                        <span class="text-slate-400">°C</span>
                    </div>
                    <span id="num-temp" class="mono text-2xl font-black text-purple-600 my-0.5">36.6</span>
                    <div class="text-[9px] text-slate-400">T1 Teri</div>
                </div>
            </div>

        </div>
    </div>

    <!-- 4. BOTTOM CLINICAL SCENARIOS BAR (NO COMPRESSOR / PURE SIMULATOR) -->
    <footer class="bg-white border border-slate-200 rounded-xl p-1.5 shadow-xs shrink-0 flex flex-wrap items-center justify-between gap-1.5 text-xs">
        <div class="flex items-center gap-1.5 text-slate-700 font-bold">
            <i class="fa-solid fa-stethoscope text-indigo-600"></i>
            <span>Klinik Ssenariylar:</span>
        </div>

        <div class="flex flex-wrap items-center gap-1.5">
            <button onclick="setScenario('normal')" class="px-2.5 py-1 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-heart text-emerald-600"></i> 🟢 Normal (75)
            </button>

            <button onclick="setScenario('dying')" class="px-2.5 py-1 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-skull-crossbones text-rose-600"></i> 🚨 0 Asistoliya
            </button>

            <button onclick="setScenario('attack')" class="px-2.5 py-1 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-bolt-lightning text-amber-600"></i> ⚡ Taxikardiya
            </button>

            <button onclick="setScenario('hypoxia')" class="px-2.5 py-1 rounded-lg bg-sky-50 hover:bg-sky-100 text-sky-800 border border-sky-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-lungs text-sky-600"></i> 🫁 Gipoksiya
            </button>

            <button onclick="setScenario('shock')" class="px-2.5 py-1 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-800 border border-purple-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-droplet-slash text-purple-600"></i> 🩸 Shok
            </button>

            <button onclick="triggerManualInjection()" class="px-2.5 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-800 border border-indigo-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-syringe text-indigo-600"></i> 💉 Ukol (Adrenalin)
            </button>

            <button onclick="defibrillateShock()" class="px-2.5 py-1 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-800 border border-blue-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
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
        let monitorVolume = 1.0; // 100% MAKSIMAL BALAND OVOZ
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

                // 1. Asosiy ton (Fundamental Sine)
                const osc1 = audioCtx.createOscillator();
                const gain1 = audioCtx.createGain();
                osc1.type = "sine";
                osc1.frequency.setValueAtTime(freq, now);
                gain1.gain.setValueAtTime(1.0, now);
                gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.095);

                // 2. Tibbiy Garmonika (Triangle)
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

        // 30:2 Sikl hisoblagichlari:
        let cprCycleComps = 0;
        let cprCycleCorrectComps = 0;
        let cprCycleVents = 0;
        let cprCycleCorrectVents = 0;
        let cprRevivalStage = 0; // 0: Asistoliya/To'xtash, 1: Ozroq jonlanish (20+ BPM), 2: To'liq o'ziga kelish (ROSC)

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

                    // 30:2 Sikl kompressiyalarini hisoblash
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
            if (!badge) return;

            if (cprCycleComps >= 30 && cprCycleVents < 2) {
                badge.innerText = `30 ZARBA TUGADI! 🫁 2 TA NAFAS BERING!`;
                badge.className = "text-xs mono font-black text-amber-600 alarm-blink";
            } else {
                badge.innerText = `${cprCycleComps}/30 zarba | ${cprCycleVents}/2 nafas`;
                badge.className = "text-xs mono font-black text-indigo-700";
            }
        }

        // ==================== CPR FORCE TARE & ZEROING (BOSHLANG'ICH MASSANI 0 QILISH) ====================
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
        }

        // ==================== PROCESS INCOMING ESP32 JSON ====================
        function handleHardwareData(data) {
            const rawF = parseFloat(data.force !== undefined ? data.force : (data.f_curr !== undefined ? data.f_curr : (data.force_kg || 0)));
            lastRawMonitorForce = rawF;

            // Boshlang'ich vaznni 0 deb olish (Boshida tinch turganda avtomatik nolga sozlaydi)
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

            // CPR zarbasini tahlil qilish
            processCPRStroke(fCurr);

            const bpm = data.bpm !== undefined ? parseInt(data.bpm) : currentBpm;
            const count = data.count !== undefined ? parseInt(data.count) : cprCount;
            const dOk = data.d_ok !== undefined ? Boolean(data.d_ok) : lastDepthOk;
            const rOk = data.r_ok !== undefined ? Boolean(data.r_ok) : lastRecoilOk;
            const bpmOk = data.bpm_ok !== undefined ? Boolean(data.bpm_ok) : lastRateOk;
            const posOk = posBtn;

            // 1. Force Bar yangilash
            document.getElementById("cpr-force-val").innerText = `${fCurr.toFixed(1)} kg`;
            const forcePct = Math.min(100, (fCurr / 60.0) * 100);
            const forceBar = document.getElementById("cpr-force-bar");
            forceBar.style.width = `${forcePct}%`;

            if (fCurr >= 38.0 && fCurr <= 55.0) {
                forceBar.className = "bg-emerald-500 h-full rounded-full transition-all duration-75";
                document.getElementById("cpr-force-val").className = "mono text-emerald-600 font-extrabold text-sm";
            } else if (fCurr > 55.0) {
                forceBar.className = "bg-rose-500 h-full rounded-full transition-all duration-75";
                document.getElementById("cpr-force-val").className = "mono text-rose-600 font-extrabold text-sm";
            } else if (fCurr > 8.0) {
                forceBar.className = "bg-amber-500 h-full rounded-full transition-all duration-75";
                document.getElementById("cpr-force-val").className = "mono text-amber-600 font-extrabold text-sm";
            } else {
                forceBar.className = "bg-slate-300 h-full rounded-full transition-all duration-75";
                document.getElementById("cpr-force-val").className = "mono text-slate-500 font-bold text-sm";
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
                rateBadge.className = "px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 text-center";
                rateBadge.innerText = "✅ A'lo tezlik (100-120)";
            } else if (bpm > 120) {
                rateBadge.className = "px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300 text-center";
                rateBadge.innerText = "⚠️ Juda tez (>120)";
            } else if (bpm > 0) {
                rateBadge.className = "px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300 text-center";
                rateBadge.innerText = "⚠️ Sekin (<100)";
            } else {
                rateBadge.className = "px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-600 border border-slate-200 text-center";
                rateBadge.innerText = "Standart: 100 - 120 /min";
            }

            // 4. O'pka bosimi (Optimal me'yor: 0.8 - 2.2 kPa)
            document.getElementById("lung-p-val").innerText = `${lungP.toFixed(1)} kPa`;
            const lungPct = Math.min(100, (lungP / 2.5) * 100);
            document.getElementById("lung-p-bar").style.width = `${lungPct}%`;
            
            const lungStatus = document.getElementById("lung-status-text");
            if (lungP >= 0.8 && lungP <= 2.2) {
                lungStatus.innerText = "✅ TO'G'RI NAFAS (0.8 - 2.2 kPa)";
                lungStatus.className = "text-[9px] text-emerald-700 mt-0.5 font-bold";
                if (current.spo2 < 99 && current.hr > 0) {
                    current.spo2 = Math.min(100, current.spo2 + 1);
                    updateNumericsUI();
                }
            } else if (lungP > 2.2) {
                lungStatus.innerText = "🚨 JUDA KUCHLI! (>2.2 kPa)";
                lungStatus.className = "text-[9px] text-rose-600 mt-0.5 font-bold";
            } else if (lungP >= 0.4) {
                lungStatus.innerText = "⚠️ Qattiqroq siqing (<0.8 kPa)";
                lungStatus.className = "text-[9px] text-amber-700 mt-0.5 font-bold";
            } else {
                lungStatus.innerText = "Me'yor: 0.8 - 2.2 kPa";
                lungStatus.className = "text-[9px] text-slate-500 mt-0.5 font-semibold";
            }

            // --- 30:2 SIKL: NAFASNI HISOBGA OLISH VA BOSQICHLI JONLANISH ---
            if (lungP >= 0.5 && !window._monitorVentTriggered) {
                window._monitorVentTriggered = true;
                cprCycleVents++;
                if (lungP >= 0.8 && lungP <= 2.2) {
                    cprCycleCorrectVents++;
                }
                updateCycleHUD();

                // Agar 30 ta bosish (yoki kamida 25 ta) va 2 ta nafas to'liq bajarilsa:
                if (cprCycleComps >= 25 && cprCycleVents >= 2) {
                    const totalActs = cprCycleComps + cprCycleVents;
                    const totalCorrect = cprCycleCorrectComps + cprCycleCorrectVents;
                    const accuracyPct = Math.round((totalCorrect / totalActs) * 100);

                    // Agar aniqlik 80% dan yuqori bo'lsa -> 1-BOSQICH: OZROQ JONLANSIN (20+ BPM)!
                    if (accuracyPct >= 80) {
                        cprRevivalStage = 1;
                        target.hr = 22;
                        current.hr = 22;
                        target.spo2 = 62;
                        current.spo2 = 62;
                        target.sys = 65;
                        target.dia = 40;
                        current.sys = 65;
                        current.dia = 40;
                        target.rr = 6;
                        current.rr = 6;
                        current.rhythm = "brady";
                        transitionSteps = 0;
                        stopAsystoleTone();
                        updateNumericsUI();
                        updateBanner(`🟡 1-BOSQICH (Aniqlik: ${accuracyPct}%): YURAK 22 BPM URISHNI BOSHLADI! ENDI UKOL (ADRENALIN) QILISH KERAK!`, "bg-amber-100 text-amber-900 border-amber-400 font-black");
                    } else {
                        updateBanner(`⚠️ SIKL YETARLI EMAS (Aniqlik: ${accuracyPct}% < 80%). Qayta 30:2 bajaring!`, "bg-rose-100 text-rose-900 border-rose-400 font-bold");
                    }

                    // Keyingi sikl uchun hisoblagichlarni yangilash
                    cprCycleComps = 0;
                    cprCycleCorrectComps = 0;
                    cprCycleVents = 0;
                    cprCycleCorrectVents = 0;
                }
            } else if (lungP < 0.3) {
                window._monitorVentTriggered = false;
            }

            // 5. Oshqozon xavfi
            document.getElementById("stomach-p-val").innerText = `${stomachP.toFixed(1)} kPa`;
            const stomachAlert = document.getElementById("stomach-alert");
            if (stomachP > 0.8) {
                stomachAlert.className = "px-1.5 py-0.5 rounded text-[9px] font-bold bg-rose-100 text-rose-800 border border-rose-400 alarm-blink";
                stomachAlert.innerHTML = "⚠️ HAVO OSHQOZONDA!";
            } else {
                stomachAlert.className = "px-1.5 py-0.5 rounded text-[9px] font-bold bg-slate-100 text-slate-600 border border-slate-200 text-center";
                stomachAlert.innerHTML = "Oshqozon toza";
            }

            // 6. Ukol / Inyeksiya (Touch Pin 4) -> 2-BOSQICH: TO'LIQ O'ZIGA KELISH
            const injBanner = document.getElementById("inj-banner");
            const injBtnEl = document.getElementById("inj-badge-small");
            if (injBtn) {
                injBanner.classList.remove("hidden");
                if (injBtnEl) {
                    injBtnEl.className = "mt-1 w-full py-0.5 px-1.5 rounded bg-purple-600 text-white font-black text-[10px] flex items-center justify-center gap-1 shadow-sm alarm-blink";
                }
                
                const flash = document.getElementById("flash-overlay");
                flash.classList.add("inj-active");
                setTimeout(() => flash.classList.remove("inj-active"), 1200);

                // Agar 1-bosqichda bo'lsa (yoki reanimatsiya qilinayotgan bo'lsa) -> TO'LIQ O'ZIGA KELISH (ROSC)!
                if (cprRevivalStage === 1 || (current.hr <= 30 && cprCount >= 10)) {
                    cprRevivalStage = 2;
                    target = { hr: 75, spo2: 98, sys: 120, dia: 80, rr: 16, temp: 36.6, mode: "normal", rhythm: "sinus" };
                    transitionSteps = 45;
                    stopAsystoleTone();
                    updateBanner("🟢 2-BOSQICH: UKOL QILINDI VA BEMOR TO'LIQ O'ZIGA KELDI (ROSC - 75 BPM)!", "bg-emerald-100 text-emerald-900 border-emerald-400 font-black");
                }
            } else {
                injBanner.classList.add("hidden");
                if (injBtnEl) {
                    injBtnEl.className = "mt-1 w-full py-0.5 px-1.5 rounded bg-purple-100 hover:bg-purple-200 text-purple-800 border border-purple-300 font-bold text-[10px] flex items-center justify-center gap-1 transition cursor-pointer active:scale-95 shadow-xs";
                }
            }
        }

        function triggerManualInjection() {
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
            if (!isActive) {
                el.className = "px-1 py-0.5 rounded bg-slate-100 border border-slate-200 text-slate-500 text-center font-bold";
                el.innerText = `${label}: -`;
            } else if (isOk) {
                el.className = "px-1 py-0.5 rounded bg-emerald-100 border border-emerald-300 text-emerald-800 text-center font-bold";
                el.innerText = `${label}: ✅`;
            } else {
                el.className = "px-1 py-0.5 rounded bg-rose-100 border border-rose-300 text-rose-800 text-center font-bold";
                el.innerText = `${label}: ❌`;
            }
        }

        function connectTelemetryWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;
            const ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                document.getElementById("hw-dot").className = "w-2 h-2 rounded-full bg-emerald-500";
                document.getElementById("hw-text").innerText = "ESP32 UART: Jonli";
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleHardwareData(data);
                } catch(e) {}
            };

            ws.onclose = () => {
                document.getElementById("hw-dot").className = "w-2 h-2 rounded-full bg-amber-500";
                document.getElementById("hw-text").innerText = "ESP32: Qayta ulanmoqda";
                setTimeout(connectTelemetryWebSocket, 1500);
            };
        }

        // ==================== KLINIK SSENARIYLAR ====================
        function setScenario(type) {
            initAudio();
            cprRevivalStage = 0;
            totalSteps = 120;
            transitionSteps = totalSteps;

            if (type === "dying") {
                target.hr = 0; target.spo2 = 0; target.sys = 0; target.dia = 0; target.rr = 0;
                current.hr = 0; current.spo2 = 0; current.sys = 0; current.dia = 0; current.rr = 0;
                current.rhythm = "asystole";
                transitionSteps = 0;
                totalSteps = 0;
                updateNumericsUI();
                updateBanner("🚨 ASISTOLIYA: YURAK TO'XTADI (0 BPM)! CPR (30:2) TALAB QILINADI!", "bg-rose-100 text-rose-900 border-rose-400 alarm-blink font-black");
                startAsystoleTone();
                return;
            }

            if (type === "normal") {
                target = { hr: 75, spo2: 98, sys: 120, dia: 80, rr: 16, temp: 36.6, mode: "normal", rhythm: "sinus" };
                updateBanner("🟢 STATUS: BARQAROR (NORMAL)", "bg-emerald-100 text-emerald-900 border-emerald-300 font-bold");
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
                rhythmLabel.innerText = "ASYSTOLIYA (Yurak to'xtadi)";
                rhythmLabel.className = "text-rose-600 font-extrabold alarm-blink";
            } else if (hrVal <= 35) {
                rhythmLabel.innerText = "Sekin Bradikardiya (Tiklanmoqda)";
                rhythmLabel.className = "text-amber-600 font-bold";
            } else if (hrVal > 150) {
                rhythmLabel.innerText = "Ventrikulyar Taxikardiya";
                rhythmLabel.className = "text-amber-600 font-bold";
            } else {
                rhythmLabel.innerText = "Sinus Ritmi";
                rhythmLabel.className = "text-emerald-700 font-bold";
            }
        }

        // ==================== CANVAS OSCILLOSCOPES (WHITE MEDICAL DAY-MODE) ====================
        const ecgCanvas = document.getElementById("ecgCanvas");
        const plethCanvas = document.getElementById("plethCanvas");
        const respCanvas = document.getElementById("respCanvas");

        const ecgCtx = ecgCanvas.getContext("2d");
        const plethCtx = plethCanvas.getContext("2d");
        const respCtx = respCanvas.getContext("2d");

        function resizeCanvases() {
            [ecgCanvas, plethCanvas, respCanvas].forEach(c => {
                c.width = c.clientWidth * (window.devicePixelRatio || 1) || c.clientWidth;
                c.height = c.clientHeight * (window.devicePixelRatio || 1) || c.clientHeight;
            });
        }
        window.addEventListener("resize", resizeCanvases);
        setTimeout(resizeCanvases, 100);

        let ecgX = 0;
        let plethX = 0;
        let respX = 0;

        let ecgPhase = 0;
        let plethPhase = 0;
        let respPhase = 0;

        let lastEcgY = null;
        let lastPlethY = null;
        let lastRespY = null;

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

        function getRespY(phase, rr) {
            if (rr <= 0) return 0;
            return Math.sin(phase * Math.PI * 2) * 0.75;
        }

        function animate() {
            const hr = current.hr;
            const spo2 = current.spo2;
            const rr = current.rr;

            const w = ecgCanvas.width;
            const hEcg = ecgCanvas.height;
            const hPleth = plethCanvas.height;
            const hResp = respCanvas.height;

            const sweepSpeed = 2.2 * (window.devicePixelRatio || 1);
            const eraseWidth = 24 * (window.devicePixelRatio || 1);

            const bps = hr / 60;
            ecgPhase += (bps / 60);
            plethPhase += (bps / 60);
            respPhase += ((rr / 60) / 60);

            const currentP = ecgPhase % 1.0;
            if (currentP >= 0.33 && currentP < 0.38) {
                const now = Date.now();
                if (now - lastBeatTime > (60000 / Math.max(20, hr)) * 0.8) {
                    playQRSBeep();
                    lastBeatTime = now;
                }
            }

            // 1. ECG (White background, Crisp Medical Green #16a34a)
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

            // 2. SpO2 Pleth (White background, Deep Medical Cyan #0284c7)
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

            // 3. RESP (White background, Deep Medical Amber #d97706)
            const nextRespX = (respX + sweepSpeed) % w;
            respCtx.fillStyle = "#ffffff";
            respCtx.fillRect(nextRespX, 0, eraseWidth, hResp);

            const respVal = getRespY(respPhase, rr);
            const midResp = hResp / 2;
            const curRespY = midResp - (respVal * (hResp * 0.38));

            if (lastRespY !== null && nextRespX > respX) {
                respCtx.strokeStyle = "#d97706";
                respCtx.lineWidth = 2.2 * (window.devicePixelRatio || 1);
                respCtx.beginPath();
                respCtx.moveTo(respX, lastRespY);
                respCtx.lineTo(nextRespX, curRespY);
                respCtx.stroke();
            }
            respX = nextRespX;
            lastRespY = curRespY;

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

        // ==================== PWA INSTALL (SENSORLI KIOSK) ====================
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
