import os
import sys
import socket
import asyncio
import json
import threading
import time
from typing import List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
from medication_labels import LABELS_HTML, get_labels_html
from medication_manager import load_medications, add_or_update_medication, delete_medication, reset_to_defaults
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

app = FastAPI(title="ICU & CPR Imtihon Xonasi - Aqlli Vital Monitor & Dori Skaneri")

try:
    from fastapi.staticfiles import StaticFiles
    os.makedirs("static", exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception:
    pass

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
    "barcode": "",
    "med_id": "",
    "timestamp": 0
}

HTML_CONTENT = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>ICU Imtihon Xonasi: Vital Monitor & Dori Skaneri Simulyatori</title>
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

        @keyframes injFlashSuccess {
            0% { background-color: rgba(34, 197, 94, 0.45); }
            100% { background-color: transparent; }
        }
        .inj-success {
            animation: injFlashSuccess 1.2s ease-out;
        }

        @keyframes injFlashDanger {
            0% { background-color: rgba(239, 68, 68, 0.55); }
            100% { background-color: transparent; }
        }
        .inj-danger {
            animation: injFlashDanger 1.5s ease-out;
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
                <span class="font-black text-sm tracking-wider text-slate-900">ICU IMTIHON XONASI & CPR MONITOR</span>
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

            <!-- DORI SKANERI / JAVONI TUGMASI -->
            <button id="btn-med-cabinet" onclick="openMedCabinetModal()" class="px-2.5 py-1 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-black text-xs flex items-center gap-1.5 shadow-xs cursor-pointer transition">
                <i class="fa-solid fa-barcode text-xs"></i>
                <span>📷 Dori Skaneri</span>
                <span id="active-med-badge-top" class="px-1.5 py-0.2 rounded bg-purple-900 text-[10px] text-purple-100 font-mono">ADR-01</span>
            </button>

            <!-- A4 CHOP ETISH (STIKERLAR) TUGMASI -->
            <a href="/vital/labels" target="_blank" title="Barcha 10 ta dori shtrix va QR kodlarini 1 ta A4 varaqda chop etish" class="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-black text-xs flex items-center gap-1 shadow-xs cursor-pointer transition active:scale-95">
                <i class="fa-solid fa-print text-xs"></i>
                <span>🖨️ A4 Stikerlar</span>
            </a>

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
        <span id="inj-banner-text">💉 UKOL QILINDI! FARMAKOLOGIK TA'SIR KUZATILMOQDA...</span>
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

    <!-- 3. BOTTOM 50% SECTION: CPR 30:2 EXERCISE DASHBOARD & SCANNER HUD -->
    <div class="bg-white border border-slate-200 rounded-xl p-2 my-0.5 shadow-xs flex-1 min-h-0 flex flex-col justify-between overflow-hidden">
        
        <!-- Header Strip with Stage Badge and Prepared Drug Banner -->
        <div class="flex flex-wrap items-center justify-between gap-2 pb-1 border-b border-slate-100 shrink-0">
            <div class="flex items-center gap-2">
                <span class="w-6 h-6 rounded-lg bg-rose-600 text-white flex items-center justify-center text-xs font-black">
                    <i class="fa-solid fa-heart-pulse"></i>
                </span>
                <div>
                    <span class="text-xs font-black text-slate-900 uppercase tracking-wide">YURAK-O'PKA REANIMATSIYASI (CPR 30:2) VA FARMAKOTERAPIYA</span>
                    <span class="text-[10px] text-slate-500 font-semibold ml-2">Standart: 30 zarba + 2 nafas</span>
                </div>
            </div>

            <!-- Prepared Medication Status Chip -->
            <div id="active-med-chip" class="px-2.5 py-0.5 rounded-lg text-xs font-bold bg-purple-50 text-purple-900 border border-purple-300 flex items-center gap-1.5 shadow-xs cursor-pointer hover:bg-purple-100 transition" onclick="openMedCabinetModal()">
                <i class="fa-solid fa-syringe text-purple-600"></i>
                <span>TAYYOR DORI:</span>
                <span id="active-med-name" class="font-black text-purple-700">Adrenalin 1mg/ml (ADR-01)</span>
            </div>

            <div id="cpr-stage-badge" class="px-2.5 py-0.5 rounded-lg text-xs font-black bg-slate-100 text-slate-700 border border-slate-300 flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-slate-400"></span>
                <span>0-BOSQICH: ASISTOLIYA (CPR KUTILMOQDA)</span>
            </div>
        </div>

        <!-- 3 Columns: A. Force Meter | B. 30:2 Cycle Hub | C. Airway & Smart Injection -->
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

            <!-- COLUMN C (3 cols): AIRWAY & SMART INJECTION HUB -->
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

                <!-- SMART INJECTION BUTTON -->
                <button type="button" onclick="triggerManualInjection()" id="inj-badge-small" class="mt-1 w-full py-2 px-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-black text-xs shadow-md flex items-center justify-center gap-1.5 transition cursor-pointer active:scale-95 shrink-0">
                    <i class="fa-solid fa-syringe text-xs"></i> <span id="inj-btn-label">💉 UKOL: ADRENALIN</span>
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
                <i class="fa-solid fa-bolt-lightning text-amber-600"></i> ⚡ Taxikardiya (185)
            </button>

            <button onclick="setScenario('hypoxia')" class="px-2 py-0.5 rounded-lg bg-sky-50 hover:bg-sky-100 text-sky-800 border border-sky-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-lungs text-sky-600"></i> 🫁 Gipoksiya (74%)
            </button>

            <button onclick="setScenario('shock')" class="px-2 py-0.5 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-800 border border-purple-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-droplet-slash text-purple-600"></i> 🩸 Shok (65/35)
            </button>

            <button onclick="openMedCabinetModal()" class="px-2 py-0.5 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-800 border border-purple-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-pills text-purple-600"></i> 💊 Dorilar
            </button>

            <button onclick="defibrillateShock()" class="px-2 py-0.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-800 border border-blue-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-wand-magic-sparkles text-blue-600"></i> ⚡ Defibrilyator
            </button>
        </div>
    </footer>

    <!-- ==================== DORI JAVONI, TAHRIRLASH & SHTRIX-KODLAR MODALI ==================== -->
    <div id="med-modal" class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs hidden z-50 flex items-center justify-center p-3 select-none">
        <div class="bg-white border border-slate-200 rounded-2xl w-full max-w-2xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <!-- Modal Header with Navigation Tabs -->
            <div class="bg-slate-50 border-b border-slate-200 px-4 py-2.5 flex flex-wrap items-center justify-between gap-2">
                <div class="flex items-center gap-2">
                    <span class="w-8 h-8 rounded-xl bg-purple-600 text-white flex items-center justify-center font-bold">
                        <i class="fa-solid fa-barcode text-sm"></i>
                    </span>
                    <div>
                        <h3 class="font-black text-slate-900 text-sm">IMTIHON DORILARI BOSHQARUVI & SKANER</h3>
                        <p class="text-[10px] text-slate-500 font-medium">Dorilarni tahrirlang, yangi qo'shing yoki o'chiring</p>
                    </div>
                </div>

                <div class="flex items-center gap-1.5">
                    <button id="tab-btn-list" onclick="switchMedModalTab('list')" class="px-3 py-1 rounded-lg text-xs font-black bg-purple-600 text-white transition flex items-center gap-1 cursor-pointer">
                        <i class="fa-solid fa-list-check"></i> Ro'yxat (<span id="med-count-badge">10</span>)
                    </button>
                    <button id="tab-btn-form" onclick="switchMedModalTab('form')" class="px-3 py-1 rounded-lg text-xs font-black bg-slate-200 hover:bg-slate-300 text-slate-700 transition flex items-center gap-1 cursor-pointer">
                        <i class="fa-solid fa-plus"></i> Yangi Qo'shish
                    </button>
                    <button onclick="resetMedicationsUI()" title="Standart 10 ta doriga qaytarish" class="px-2 py-1 rounded-lg text-xs font-bold bg-slate-100 hover:bg-rose-100 text-slate-600 hover:text-rose-700 border border-slate-300 transition cursor-pointer">
                        <i class="fa-solid fa-rotate-left"></i>
                    </button>
                    <button onclick="closeMedCabinetModal()" class="w-8 h-8 rounded-lg bg-slate-200 hover:bg-slate-300 text-slate-700 flex items-center justify-center cursor-pointer ml-1">
                        <i class="fa-solid fa-xmark"></i>
                    </button>
                </div>
            </div>

            <!-- TAB 1: MEDICATION LIST VIEW -->
            <div id="med-tab-list" class="flex-1 flex flex-col min-h-0 overflow-hidden">
                <!-- Barcode Scanner Search Bar -->
                <div class="p-2.5 bg-purple-50/70 border-b border-purple-100 flex items-center gap-2 shrink-0">
                    <i class="fa-solid fa-barcode text-purple-600 text-lg"></i>
                    <input type="text" id="manual-barcode-input" placeholder="Shtrix-kodni skanerlang yoki qidiring (masalan: ADR-01, AMI-02)..." onkeydown="if(event.key==='Enter') scanManualBarcode()" class="flex-1 px-3 py-1.5 bg-white border border-purple-300 rounded-lg text-xs font-mono font-bold focus:outline-none focus:ring-2 focus:ring-purple-500">
                    <button onclick="scanManualBarcode()" class="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs rounded-lg cursor-pointer">
                        Skanerlash
                    </button>
                </div>

                <!-- Cards Container -->
                <div id="med-list-container" class="p-3 overflow-y-auto flex-1 grid grid-cols-1 md:grid-cols-2 gap-2">
                    <!-- Dynamic medication cards rendered by JS -->
                </div>
            </div>

            <!-- TAB 2: ADD / EDIT MEDICATION FORM -->
            <div id="med-tab-form" class="hidden flex-1 p-4 overflow-y-auto">
                <div class="border border-slate-200 rounded-xl p-4 bg-slate-50/50 shadow-xs space-y-3">
                    <div class="flex items-center justify-between pb-2 border-b border-slate-200">
                        <h4 id="form-title" class="font-black text-sm text-slate-900 flex items-center gap-2">
                            <i class="fa-solid fa-pen-to-square text-purple-600"></i> Yangi Dori Qo'shish
                        </h4>
                        <span id="form-mode-badge" class="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-800">YANGI</span>
                    </div>

                    <input type="hidden" id="form-med-id" value="">

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                            <label class="block text-[11px] font-bold text-slate-700 mb-1">Dori nomi va dozasi *</label>
                            <input type="text" id="form-med-name" placeholder="Masalan: Magniy Sulfat 25% 10ml" class="w-full px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-bold focus:ring-2 focus:ring-purple-500 focus:outline-none">
                        </div>

                        <div>
                            <label class="block text-[11px] font-bold text-slate-700 mb-1">Dori Kodi (Shtrix-kod matni) *</label>
                            <input type="text" id="form-med-code" placeholder="Masalan: MAG-11" class="w-full px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-mono font-bold uppercase focus:ring-2 focus:ring-purple-500 focus:outline-none">
                        </div>
                    </div>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div>
                            <label class="block text-[11px] font-bold text-slate-700 mb-1">Farmakologik guruhi</label>
                            <input type="text" id="form-med-group" placeholder="Masalan: Antiaritmik / Sedativ" class="w-full px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-bold focus:ring-2 focus:ring-purple-500 focus:outline-none">
                        </div>

                        <div>
                            <label class="block text-[11px] font-bold text-slate-700 mb-1">Qo'shimcha barkodlar (vergul bilan)</label>
                            <input type="text" id="form-med-barcodes" placeholder="Masalan: 4780001011, MAG11" class="w-full px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-mono focus:ring-2 focus:ring-purple-500 focus:outline-none">
                        </div>
                    </div>

                    <div>
                        <label class="block text-[11px] font-bold text-slate-700 mb-1">Klinik tavsifi / Ko'rsatma</label>
                        <input type="text" id="form-med-desc" placeholder="Masalan: Pirouette taxikardiyasi va gipertonik krizda qo'llaniladi." class="w-full px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-purple-500 focus:outline-none">
                    </div>

                    <!-- Clinical Scenarios Matching -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-slate-200">
                        <div class="bg-emerald-50/80 border border-emerald-200 rounded-xl p-2.5">
                            <label class="block text-[11px] font-black text-emerald-900 mb-1.5">
                                <i class="fa-solid fa-circle-check text-emerald-600 mr-1"></i> Qaysi holatda TO'G'RI (yaxshilaydi)?
                            </label>
                            <div class="grid grid-cols-2 gap-1.5 text-xs text-emerald-950 font-bold">
                                <label class="flex items-center gap-1.5 cursor-pointer"><input type="checkbox" id="appr-asystole" class="accent-emerald-600"> 0 Asistoliya (CPR)</label>
                                <label class="flex items-center gap-1.5 cursor-pointer"><input type="checkbox" id="appr-tachycardia" class="accent-emerald-600"> ⚡ Taxikardiya</label>
                                <label class="flex items-center gap-1.5 cursor-pointer"><input type="checkbox" id="appr-bradycardia" class="accent-emerald-600"> 🟡 Bradikardiya</label>
                                <label class="flex items-center gap-1.5 cursor-pointer"><input type="checkbox" id="appr-hypoxia" class="accent-emerald-600"> 🫁 Gipoksiya</label>
                                <label class="flex items-center gap-1.5 cursor-pointer"><input type="checkbox" id="appr-shock" class="accent-emerald-600"> 🩸 Shok (Kollaps)</label>
                            </div>
                        </div>

                        <div class="bg-rose-50/80 border border-rose-200 rounded-xl p-2.5">
                            <label class="block text-[11px] font-black text-rose-900 mb-1.5">
                                <i class="fa-solid fa-triangle-exclamation text-rose-600 mr-1"></i> Qaysi holatda XAVFLI (yomonlashtiradi)?
                            </label>
                            <div class="grid grid-cols-2 gap-1.5 text-xs text-rose-950 font-bold">
                                <label class="flex items-center gap-1.5 cursor-pointer"><input type="checkbox" id="dang-asystole" class="accent-rose-600"> 0 Asistoliya</label>
                                <label class="flex items-center gap-1.5 cursor-pointer"><input type="checkbox" id="dang-tachycardia" class="accent-rose-600"> ⚡ Taxikardiya</label>
                                <label class="flex items-center gap-1.5 cursor-pointer"><input type="checkbox" id="dang-bradycardia" class="accent-rose-600"> 🟡 Bradikardiya</label>
                                <label class="flex items-center gap-1.5 cursor-pointer"><input type="checkbox" id="dang-hypoxia" class="accent-rose-600"> 🫁 Gipoksiya</label>
                                <label class="flex items-center gap-1.5 cursor-pointer"><input type="checkbox" id="dang-shock" class="accent-rose-600"> 🩸 Shok (Kollaps)</label>
                                <label class="flex items-center gap-1.5 cursor-pointer"><input type="checkbox" id="dang-normal" class="accent-rose-600"> 🟢 Normal (Sog'lom)</label>
                            </div>
                        </div>
                    </div>

                    <!-- Form Buttons -->
                    <div class="flex items-center justify-end gap-2 pt-2">
                        <button type="button" onclick="switchMedModalTab('list')" class="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-700 font-bold text-xs rounded-xl cursor-pointer">
                            Bekor qilish
                        </button>
                        <button type="button" onclick="saveMedicationFromForm()" class="px-5 py-2 bg-purple-600 hover:bg-purple-700 text-white font-black text-xs rounded-xl shadow-md cursor-pointer transition active:scale-95">
                            <i class="fa-solid fa-floppy-disk mr-1"></i> Saqlash
                        </button>
                    </div>
                </div>
            </div>

            <!-- Modal Footer -->
            <div class="bg-slate-50 border-t border-slate-200 px-4 py-2.5 flex items-center justify-between text-xs gap-2 shrink-0">
                <a href="/vital/labels" target="_blank" class="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-black rounded-lg flex items-center gap-1.5 shadow-sm transition active:scale-95 cursor-pointer">
                    <i class="fa-solid fa-print"></i> 🖨️ A4 Chop Etish (Barcha Stikerlar)
                </a>
                <button onclick="closeMedCabinetModal()" class="px-4 py-1.5 bg-slate-200 hover:bg-slate-300 font-bold rounded-lg cursor-pointer">
                    Yopish
                </button>
            </div>
        </div>
    </div>

    <!-- JAVASCRIPT ENGINE -->
    <script>
        // ==================== DORI-DARMONLAR BAZASI VA CRUD BOSHQARUVI ====================
        let MEDICATION_DB = [
            {
                id: "adrenalin",
                code: "ADR-01",
                name: "Adrenalin (Epinefrin) 1 mg/ml",
                barcodes: ["ADR01", "ADR-01", "ADRENALIN", "EPINEPHRINE", "4780001001"],
                group: "Adrenomimetik (Vazopressor)",
                desc: "Yurak to'xtashi, asistoliya va anafilaktik shokda asosiy vosita.",
                badgeBg: "#7e22ce",
                btnColor: "bg-purple-600 hover:bg-purple-700",
                appropriate_for: ["asystole", "bradycardia", "shock", "hypoxia"],
                dangerous_for: ["tachycardia"]
            },
            {
                id: "amiodaron",
                code: "AMI-02",
                name: "Amiodaron (Kordaron) 150 mg",
                barcodes: ["AMI02", "AMI-02", "AMIODARON", "CORDARONE", "4780001002"],
                group: "Antiaritmik (III-sinf)",
                desc: "Qorincha taxikardiyasi (VTach) va aritmiyalarni to'xtatuvchi.",
                badgeBg: "#0284c7",
                btnColor: "bg-sky-600 hover:bg-sky-700",
                appropriate_for: ["tachycardia"],
                dangerous_for: ["bradycardia", "asystole"]
            },
            {
                id: "atropin",
                code: "ATR-03",
                name: "Atropin sulfat 1 mg/ml",
                barcodes: ["ATR03", "ATR-03", "ATROPIN", "ATROPINE", "4780001003"],
                group: "M-Xolinoblokator",
                desc: "Sust puls (bradikardiya) va AV-blokadalarda ritmni oshiradi.",
                badgeBg: "#d97706",
                btnColor: "bg-amber-600 hover:bg-amber-700",
                appropriate_for: ["bradycardia"],
                dangerous_for: ["tachycardia"]
            },
            {
                id: "nitro",
                code: "NIT-04",
                name: "Nitroglitserin 0.5 mg",
                barcodes: ["NIT04", "NIT-04", "NITRO", "NITROGLYCERIN", "4780001004"],
                group: "Periferik vazodilatator",
                desc: "O'tkir gipertonik kriz va stenokardiyada bosimni tushiradi.",
                badgeBg: "#e11d48",
                btnColor: "bg-rose-600 hover:bg-rose-700",
                appropriate_for: ["attack"],
                dangerous_for: ["shock", "asystole"]
            },
            {
                id: "metoprolol",
                code: "MET-05",
                name: "Metoprolol (Beta-blokator) 5 mg",
                barcodes: ["MET05", "MET-05", "METOPROLOL", "BETALOC", "4780001005"],
                group: "Beta-1 adrenoblokator",
                desc: "Taxikardiyada puls va miokard kislorod talabini pasaytiradi.",
                badgeBg: "#4f46e5",
                btnColor: "bg-indigo-600 hover:bg-indigo-700",
                appropriate_for: ["tachycardia"],
                dangerous_for: ["bradycardia", "asystole", "hypoxia"]
            },
            {
                id: "saline",
                code: "SAL-06",
                name: "Fizrastvor (0.9% NaCl) 500 ml",
                barcodes: ["SAL06", "SAL-06", "NACL", "FIZRASTVOR", "SALINE", "4780001006"],
                group: "Kristalloid plazma o'rnini bosuvchi",
                desc: "Gipovolemik va qon yo'qotish shokida qon bosimini tiklaydi.",
                badgeBg: "#2563eb",
                btnColor: "bg-blue-600 hover:bg-blue-700",
                appropriate_for: ["shock", "hypoxia"],
                dangerous_for: []
            },
            {
                id: "dexa",
                code: "DEX-07",
                name: "Deksametazon 8 mg/2ml",
                barcodes: ["DEX07", "DEX-07", "DEXA", "DEXAMETHASONE", "4780001007"],
                group: "Glikokortikosteroid (Gormon)",
                desc: "Bronxospazm, anafilaksiya va o'tkir gipoksiyani bartaraf etadi.",
                badgeBg: "#059669",
                btnColor: "bg-emerald-600 hover:bg-emerald-700",
                appropriate_for: ["hypoxia"],
                dangerous_for: []
            },
            {
                id: "naloxone",
                code: "NAL-08",
                name: "Nalokson 0.4 mg/ml",
                barcodes: ["NAL08", "NAL-08", "NALOXON", "NALOXONE", "4780001008"],
                group: "Opioid retseptorlari antagonisti",
                desc: "Narkotik intoksikatsiyasi va nafas tormozlanishiga qarshi vosita.",
                badgeBg: "#0d9488",
                btnColor: "bg-teal-600 hover:bg-teal-700",
                appropriate_for: ["hypoxia"],
                dangerous_for: []
            },
            {
                id: "kcl",
                code: "KCL-09",
                name: "Kaliy xlorid (KCl 4%) 20 ml",
                barcodes: ["KCL09", "KCL-09", "KCL", "POTASSIUM", "4780001009"],
                group: "Elektrolit (Toksik konsentrat)",
                desc: "DIQQAT: Sof holda vena ichiga yuborish kardioplegiya chaqiradi!",
                badgeBg: "#dc2626",
                btnColor: "bg-red-600 hover:bg-red-700",
                appropriate_for: [],
                dangerous_for: ["asystole", "normal", "shock", "bradycardia", "tachycardia"]
            },
            {
                id: "furosemide",
                code: "FUR-10",
                name: "Furosemid (Laziks) 20 mg",
                barcodes: ["FUR10", "FUR-10", "FUROSEMID", "LASIX", "4780001010"],
                group: "Halqa diuretigi",
                desc: "O'pka shishi va gipertoniyada tezkor suyuqlik haydovchi vosita.",
                badgeBg: "#0891b2",
                btnColor: "bg-cyan-600 hover:bg-cyan-700",
                appropriate_for: ["attack"],
                dangerous_for: ["shock", "asystole"]
            }
        ];

        let selectedMedication = MEDICATION_DB[0];

        async function fetchMedicationsFromServer() {
            try {
                const res = await fetch("/api/medications");
                if (res.ok) {
                    const data = await res.json();
                    if (Array.isArray(data) && data.length > 0) {
                        MEDICATION_DB = data;
                        if (!selectedMedication || !MEDICATION_DB.some(m => m.id === selectedMedication.id)) {
                            selectedMedication = MEDICATION_DB[0];
                        }
                        updateSelectedMedicationUI();
                        renderMedList();
                    }
                }
            } catch(e) {
                console.warn("Dori bazasi yuklanmadi:", e);
            }
        }

        function switchMedModalTab(tab) {
            const listTab = document.getElementById("med-tab-list");
            const formTab = document.getElementById("med-tab-form");
            const listBtn = document.getElementById("tab-btn-list");
            const formBtn = document.getElementById("tab-btn-form");

            if (tab === 'form') {
                if (listTab) listTab.classList.add("hidden");
                if (formTab) formTab.classList.remove("hidden");
                if (listBtn) listBtn.className = "px-3 py-1 rounded-lg text-xs font-bold bg-slate-200 hover:bg-slate-300 text-slate-700 transition flex items-center gap-1 cursor-pointer";
                if (formBtn) formBtn.className = "px-3 py-1 rounded-lg text-xs font-black bg-purple-600 text-white transition flex items-center gap-1 cursor-pointer";
            } else {
                if (formTab) formTab.classList.add("hidden");
                if (listTab) listTab.classList.remove("hidden");
                if (formBtn) formBtn.className = "px-3 py-1 rounded-lg text-xs font-bold bg-slate-200 hover:bg-slate-300 text-slate-700 transition flex items-center gap-1 cursor-pointer";
                if (listBtn) listBtn.className = "px-3 py-1 rounded-lg text-xs font-black bg-purple-600 text-white transition flex items-center gap-1 cursor-pointer";
                renderMedList();
            }
        }

        function openAddMedicationForm() {
            document.getElementById("form-title").innerHTML = `<i class="fa-solid fa-plus text-purple-600"></i> Yangi Dori Qo'shish`;
            document.getElementById("form-mode-badge").innerText = "YANGI";
            document.getElementById("form-mode-badge").className = "px-2 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-800";
            
            document.getElementById("form-med-id").value = "";
            document.getElementById("form-med-name").value = "";
            document.getElementById("form-med-code").value = "";
            document.getElementById("form-med-group").value = "";
            document.getElementById("form-med-barcodes").value = "";
            document.getElementById("form-med-desc").value = "";

            ["asystole", "tachycardia", "bradycardia", "hypoxia", "shock"].forEach(c => {
                const el = document.getElementById("appr-" + c);
                if (el) el.checked = false;
            });
            ["asystole", "tachycardia", "bradycardia", "hypoxia", "shock", "normal"].forEach(c => {
                const el = document.getElementById("dang-" + c);
                if (el) el.checked = false;
            });

            switchMedModalTab('form');
        }

        function editMedication(medId) {
            const m = MEDICATION_DB.find(item => item.id === medId || item.code === medId);
            if (!m) return;

            document.getElementById("form-title").innerHTML = `<i class="fa-solid fa-pen-to-square text-purple-600"></i> Dorini Tahrirlash: ${m.code}`;
            document.getElementById("form-mode-badge").innerText = "TAHRIRLASH";
            document.getElementById("form-mode-badge").className = "px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800";

            document.getElementById("form-med-id").value = m.id || m.code;
            document.getElementById("form-med-name").value = m.name || "";
            document.getElementById("form-med-code").value = m.code || "";
            document.getElementById("form-med-group").value = m.group || "";
            document.getElementById("form-med-barcodes").value = (m.barcodes || []).join(", ");
            document.getElementById("form-med-desc").value = m.desc || "";

            const appr = m.appropriate_for || [];
            ["asystole", "tachycardia", "bradycardia", "hypoxia", "shock"].forEach(c => {
                const el = document.getElementById("appr-" + c);
                if (el) el.checked = appr.includes(c);
            });

            const dang = m.dangerous_for || [];
            ["asystole", "tachycardia", "bradycardia", "hypoxia", "shock", "normal"].forEach(c => {
                const el = document.getElementById("dang-" + c);
                if (el) el.checked = dang.includes(c);
            });

            switchMedModalTab('form');
        }

        async function saveMedicationFromForm() {
            const name = document.getElementById("form-med-name").value.trim();
            const code = document.getElementById("form-med-code").value.trim().toUpperCase();
            if (!name || !code) {
                alert("Iltimos dori nomi va kodini to'ldiring!");
                return;
            }

            const medId = document.getElementById("form-med-id").value.trim() || code.toLowerCase().replace("-", "_");
            const group = document.getElementById("form-med-group").value.trim();
            const barcodesStr = document.getElementById("form-med-barcodes").value.trim();
            const desc = document.getElementById("form-med-desc").value.trim();

            let barcodes = barcodesStr.split(",").map(s => s.trim().toUpperCase()).filter(Boolean);
            if (!barcodes.includes(code)) barcodes.unshift(code);

            const appr = [];
            ["asystole", "tachycardia", "bradycardia", "hypoxia", "shock"].forEach(c => {
                const el = document.getElementById("appr-" + c);
                if (el && el.checked) appr.push(c);
            });

            const dang = [];
            ["asystole", "tachycardia", "bradycardia", "hypoxia", "shock", "normal"].forEach(c => {
                const el = document.getElementById("dang-" + c);
                if (el && el.checked) dang.push(c);
            });

            const payload = {
                id: medId,
                code: code,
                name: name,
                group: group || "Klinik dori",
                desc: desc || "Shoshilinch dori vositasi",
                barcodes: barcodes,
                appropriate_for: appr,
                dangerous_for: dang,
                badgeBg: "#6366f1",
                btnColor: "bg-indigo-600 hover:bg-indigo-700"
            };

            try {
                const res = await fetch("/api/medications", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    await fetchMedicationsFromServer();
                    switchMedModalTab('list');
                    updateBanner(`✅ DORI SAQLANDI: ${name} [${code}]`, "bg-emerald-100 text-emerald-900 border-emerald-400 font-black");
                } else {
                    alert("Saqlashda server xatosi yuz berdi.");
                }
            } catch(err) {
                alert("Saqlashda xatolik: " + err.message);
            }
        }

        async function deleteMedicationUI(medId) {
            const med = MEDICATION_DB.find(m => m.id === medId || m.code === medId);
            const name = med ? med.name : medId;
            if (!confirm(`Haqiqatdan ham "${name}" dorisini o'chirmoqchimisiz?`)) {
                return;
            }

            try {
                const res = await fetch(`/api/medications/${medId}`, { method: "DELETE" });
                if (res.ok) {
                    await fetchMedicationsFromServer();
                    updateBanner(`🗑️ DORI O'CHIRILDI: ${name}`, "bg-slate-200 text-slate-800 border-slate-400 font-bold");
                }
            } catch(err) {
                alert("O'chirishda xatolik: " + err.message);
            }
        }

        async function resetMedicationsUI() {
            if (!confirm("Barcha dorilarni standart 10 ta dori ro'yxatiga qaytarishni xohlaysizmi?")) {
                return;
            }

            try {
                const res = await fetch("/api/medications/reset", { method: "POST" });
                if (res.ok) {
                    await fetchMedicationsFromServer();
                    updateBanner(`🔄 DORILAR STANDART HOLATGA QAYTARILDI`, "bg-purple-100 text-purple-900 border-purple-400 font-bold");
                }
            } catch(err) {
                alert("Qaytarishda xatolik: " + err.message);
            }
        }

        function renderMedList() {
            const countEl = document.getElementById("med-count-badge");
            if (countEl) countEl.innerText = MEDICATION_DB.length;

            const container = document.getElementById("med-list-container");
            if (!container) return;

            container.innerHTML = MEDICATION_DB.map(m => `
                <div class="border border-slate-200 rounded-xl p-2.5 bg-slate-50/70 hover:bg-white flex flex-col justify-between transition shadow-xs ${selectedMedication && selectedMedication.id === m.id ? 'ring-2 ring-purple-600 bg-purple-50/50' : ''}">
                    <div class="flex justify-between items-start gap-1">
                        <div>
                            <div class="font-black text-xs text-slate-900">${m.name}</div>
                            <div class="text-[10px] font-bold text-slate-500">${m.group || "Klinik dori"}</div>
                        </div>
                        <span class="mono px-1.5 py-0.5 rounded text-[10px] font-black bg-white border border-slate-300 text-slate-700 shadow-xs">${m.code}</span>
                    </div>
                    <p class="text-[9px] text-slate-600 my-1 leading-tight">${m.desc || ""}</p>
                    <div class="flex items-center justify-between mt-1 pt-1.5 border-t border-slate-200 gap-1">
                        <span class="mono text-[9px] text-slate-400 truncate max-w-[90px]"><i class="fa-solid fa-barcode mr-1"></i>${m.barcodes && m.barcodes[0] ? m.barcodes[0] : m.code}</span>
                        <div class="flex items-center gap-1 shrink-0">
                            <button type="button" onclick="selectMedicationDirect('${m.id}')" class="px-2 py-0.5 rounded text-white text-[10px] font-black ${m.btnColor || 'bg-purple-600 hover:bg-purple-700'} cursor-pointer active:scale-95 transition shadow-xs">
                                <i class="fa-solid fa-check mr-0.5"></i> ${selectedMedication && selectedMedication.id === m.id ? 'Tayyor' : 'Tanlash'}
                            </button>
                            <button type="button" onclick="editMedication('${m.id}')" title="Tahrirlash" class="px-1.5 py-0.5 rounded bg-white hover:bg-amber-100 text-amber-700 border border-slate-300 text-[10px] font-bold cursor-pointer transition">
                                <i class="fa-solid fa-pen"></i>
                            </button>
                            <button type="button" onclick="deleteMedicationUI('${m.id}')" title="O'chirish" class="px-1.5 py-0.5 rounded bg-white hover:bg-rose-100 text-rose-700 border border-slate-300 text-[10px] font-bold cursor-pointer transition">
                                <i class="fa-solid fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `).join("");
        }

        function openMedCabinetModal() {
            const modal = document.getElementById("med-modal");
            if (!modal) return;
            switchMedModalTab('list');
            modal.classList.remove("hidden");
            setTimeout(() => {
                const input = document.getElementById("manual-barcode-input");
                if (input) input.focus();
            }, 100);
        }

        function closeMedCabinetModal() {
            const modal = document.getElementById("med-modal");
            if (modal) modal.classList.add("hidden");
        }

        function updateSelectedMedicationUI() {
            if (!selectedMedication) return;
            const topBadge = document.getElementById("active-med-badge-top");
            if (topBadge) topBadge.innerText = selectedMedication.code;

            const nameEl = document.getElementById("active-med-name");
            if (nameEl) nameEl.innerText = `${selectedMedication.name} (${selectedMedication.code})`;

            const btnLabel = document.getElementById("inj-btn-label");
            if (btnLabel) btnLabel.innerText = `💉 UKOL: ${selectedMedication.name.split(' ')[0].toUpperCase()}`;
        }

        function selectMedicationDirect(medId) {
            const med = MEDICATION_DB.find(m => m.id === medId || m.code === medId);
            if (med) {
                selectedMedication = med;
                playScannerBeep();
                updateSelectedMedicationUI();
                renderMedList();
                updateBanner(`💊 TANLANDI: ${med.name} [${med.code}] — Manikenga ukol qilish kutilmoqda...`, "bg-purple-100 text-purple-900 border-purple-400 font-black");
                closeMedCabinetModal();
            }
        }

        function processScannedMedication(rawCode) {
            const clean = rawCode.trim().toUpperCase();
            const matched = MEDICATION_DB.find(m => 
                m.code.toUpperCase() === clean ||
                (m.barcodes && m.barcodes.some(b => b.toUpperCase() === clean)) ||
                m.id.toUpperCase() === clean ||
                m.name.toUpperCase().includes(clean)
            );

            if (matched) {
                selectedMedication = matched;
                playScannerBeep();
                updateSelectedMedicationUI();
                renderMedList();

                const bannerMsg = `💊 DORI SKANERLANDI: ${matched.name} [${matched.code}] — Manikenga ukol qilish kutilmoqda...`;
                updateBanner(bannerMsg, "bg-purple-100 text-purple-900 border-purple-400 font-black");

                const injText = document.getElementById("inj-banner-text");
                if (injText) injText.innerText = `💉 DORI TAYYORLANDI: ${matched.name}`;

                closeMedCabinetModal();
            } else {
                playAlarmErrorTone();
                updateBanner(`⚠️ NOMA'LUM BARKOD: "${rawCode}" — Dori topilmadi!`, "bg-amber-100 text-amber-900 border-amber-400 font-bold");
            }
        }

        function scanManualBarcode() {
            const input = document.getElementById("manual-barcode-input");
            if (input && input.value.trim()) {
                processScannedMedication(input.value.trim());
                input.value = "";
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
            if (data.barcode || data.med_code || data.med_id) {
                processScannedMedication(data.barcode || data.med_code || data.med_id);
            }

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

            // --- 30:2 SIKL: NAFASNI HISOBGA OLISH VA 5s SEKIN JONLANISH (22 BPM) ---
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
                        cprRevivalStage = 1;
                        target.hr = 22;
                        target.spo2 = 62;
                        target.sys = 65;
                        target.dia = 40;
                        target.rr = 6;
                        current.rhythm = "brady";
                        
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
                processSmartMedicationAdministration();
            } else if (!injectionInProgress) {
                const injBanner = document.getElementById("inj-banner");
                const injBtnEl = document.getElementById("inj-badge-small");
                if (injBanner) injBanner.classList.add("hidden");
                if (injBtnEl) {
                    injBtnEl.className = "mt-1 w-full py-2 px-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-black text-xs shadow-md flex items-center justify-center gap-1.5 transition cursor-pointer active:scale-95 shrink-0";
                }
            }
        }

        // ==================== AQLLI FARMAKOLOGIK REAKSIYA DVIGATELI ====================
        function processSmartMedicationAdministration() {
            if (injectionInProgress) return;

            const med = selectedMedication;
            const medId = med.id;
            const medName = med.name;

            const injBanner = document.getElementById("inj-banner");
            const injText = document.getElementById("inj-banner-text");
            const injBtnEl = document.getElementById("inj-badge-small");
            if (injBanner) injBanner.classList.remove("hidden");
            if (injBtnEl) {
                injBtnEl.className = "mt-1 w-full py-2 px-2 rounded-lg bg-purple-700 text-white font-black text-xs shadow-md flex items-center justify-center gap-1.5 alarm-blink";
            }

            const flash = document.getElementById("flash-overlay");

            // Baholash: joriy holat nima?
            const isAsystoleOrCPR = (current.hr <= 5 || current.mode === "dying" || cprRevivalStage === 1);
            const isTachycardia = (current.mode === "attack" || current.hr >= 160);
            const isBradycardia = (current.hr <= 35 && current.hr > 5);
            const isHypoxia = (current.mode === "hypoxia" || current.spo2 <= 80);
            const isShock = (current.mode === "shock" || current.sys <= 75);
            const isNormal = (current.mode === "normal" && current.hr > 50 && current.hr < 110);

            const appr = Array.isArray(med.appropriate_for) ? med.appropriate_for : [];
            const dang = Array.isArray(med.dangerous_for) ? med.dangerous_for : [];

            // --- 1. ASISTOLIYA / CPR JARAYONI ---
            if (isAsystoleOrCPR) {
                if (appr.includes("asystole") || medId === "adrenalin") {
                    // TO'G'RI DORI!
                    flash.classList.add("inj-success");
                    setTimeout(() => flash.classList.remove("inj-success"), 1200);

                    injectionInProgress = true;
                    cprRevivalStage = 2;

                    let delaySec = 5;
                    const stageBadge = document.getElementById("cpr-stage-badge");
                    if (stageBadge) {
                        stageBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-purple-500 alarm-blink"></span><span>2-BOSQICH: ${med.code} YURAKKA YETIB BORMOQDA (${delaySec}s)...</span>`;
                        stageBadge.className = "px-2.5 py-0.5 rounded-lg text-xs font-black bg-purple-100 text-purple-900 border border-purple-400 flex items-center gap-1.5 shadow-sm";
                    }
                    const msg = `✅ TO'G'RI DORI: ${medName} yuborildi! Qon orqali yurakka yetib bormoqda (${delaySec}s)...`;
                    if (injText) injText.innerText = msg;
                    updateBanner(msg, "bg-purple-100 text-purple-900 border-purple-400 font-black");

                    if (injectionCountdownTimer) clearInterval(injectionCountdownTimer);
                    injectionCountdownTimer = setInterval(() => {
                        delaySec--;
                        if (delaySec > 0) {
                            if (stageBadge) {
                                stageBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-purple-500 alarm-blink"></span><span>2-BOSQICH: ${med.code} YURAKKA YETIB BORMOQDA (${delaySec}s)...</span>`;
                            }
                            const curMsg = `✅ TO'G'RI DORI: ${medName} yuborildi! Dori yetib bormoqda (${delaySec}s)...`;
                            if (injText) injText.innerText = curMsg;
                            updateBanner(curMsg, "bg-purple-100 text-purple-900 border-purple-400 font-black");
                        } else {
                            clearInterval(injectionCountdownTimer);
                            injectionCountdownTimer = null;

                            // 10 soniya davomida 75 BPM ga tiklanish
                            target = { hr: 75, spo2: 98, sys: 120, dia: 80, rr: 16, temp: 36.6, mode: "normal", rhythm: "sinus" };
                            totalSteps = 100;
                            transitionSteps = 100;
                            stopAsystoleTone();

                            if (stageBadge) {
                                stageBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-500 alarm-blink"></span><span>2-BOSQICH: YURAK RITMI SEKIN TIKLANMOQDA (10s -> 75 BPM)</span>`;
                                stageBadge.className = "px-2.5 py-0.5 rounded-lg text-xs font-black bg-emerald-100 text-emerald-900 border border-emerald-400 flex items-center gap-1.5 shadow-sm";
                            }
                            const recMsg = `🟢 2-BOSQICH: ${medName.toUpperCase()} TA'SIR QILDI! YURAK RITMI TIKLANMOQDA (10s davomida 75 BPM ga)...`;
                            if (injText) injText.innerText = recMsg;
                            updateBanner(recMsg, "bg-emerald-100 text-emerald-900 border-emerald-400 font-black");
                        }
                    }, 1000);
                } else if (dang.includes("asystole") || medId === "kcl") {
                    // KATASTROFIK XATO!
                    flash.classList.add("inj-danger");
                    setTimeout(() => flash.classList.remove("inj-danger"), 1500);
                    playAlarmErrorTone();
                    stopAsystoleTone();
                    startAsystoleTone();

                    target = { hr: 0, spo2: 0, sys: 0, dia: 0, rr: 0, temp: 35.5, mode: "dying", rhythm: "asystole" };
                    current = { ...target };
                    transitionSteps = 0;
                    cprRevivalStage = 0;

                    const err = `🚨 O'LIMGA OLIB KELUVCHI XATO: Asistoliyada ${medName} qilindi! Toksik kardioplegiya, miokard butunlay falajlandi!`;
                    if (injText) injText.innerText = err;
                    updateBanner(err, "bg-rose-600 text-white border-rose-800 font-black alarm-blink");

                    const stageBadge = document.getElementById("cpr-stage-badge");
                    if (stageBadge) {
                        stageBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-rose-600 alarm-blink"></span><span>KATASTROFA: TOKSIK ASISTOLIYA (${med.code})</span>`;
                        stageBadge.className = "px-2.5 py-0.5 rounded-lg text-xs font-black bg-rose-200 text-rose-950 border border-rose-400 flex items-center gap-1.5 shadow-sm";
                    }
                } else {
                    // Boshqa nomutanosib dori
                    flash.classList.add("inj-danger");
                    setTimeout(() => flash.classList.remove("inj-danger"), 1200);
                    playAlarmErrorTone();

                    const warn = `❌ MOS EMAS: Asistoliyada ${medName} foydasiz! Ko'rsatilgan dori (masalan, Adrenalin) talab qilinadi!`;
                    if (injText) injText.innerText = warn;
                    updateBanner(warn, "bg-rose-100 text-rose-900 border-rose-400 font-black");
                }
            }

            // --- 2. O'TKIR TAXIKARDIYA (VTach / SVT 185 BPM) ---
            else if (isTachycardia) {
                if (appr.includes("tachycardia") || medId === "amiodaron" || medId === "metoprolol") {
                    // TO'G'RI DORI!
                    flash.classList.add("inj-success");
                    setTimeout(() => flash.classList.remove("inj-success"), 1200);
                    injectionInProgress = true;

                    let delaySec = 5;
                    const msg = `✅ TO'G'RI DORI: ${medName} yuborildi! Antiaritmik ta'sir boshlanmoqda (${delaySec}s)...`;
                    if (injText) injText.innerText = msg;
                    updateBanner(msg, "bg-sky-100 text-sky-900 border-sky-400 font-black");

                    if (injectionCountdownTimer) clearInterval(injectionCountdownTimer);
                    injectionCountdownTimer = setInterval(() => {
                        delaySec--;
                        if (delaySec > 0) {
                            const curMsg = `✅ Antiaritmik ta'sir yetib bormoqda (${delaySec}s)...`;
                            if (injText) injText.innerText = curMsg;
                            updateBanner(curMsg, "bg-sky-100 text-sky-900 border-sky-400 font-black");
                        } else {
                            clearInterval(injectionCountdownTimer);
                            injectionCountdownTimer = null;

                            target = { hr: 78, spo2: 98, sys: 125, dia: 80, rr: 16, temp: 36.6, mode: "normal", rhythm: "sinus" };
                            totalSteps = 100;
                            transitionSteps = 100;

                            const okMsg = `🟢 A'LO DAVO: ${medName} ta'sirida taxikardiya to'xtatildi, sinus ritmi tiklandi (78 BPM)!`;
                            if (injText) injText.innerText = okMsg;
                            updateBanner(okMsg, "bg-emerald-100 text-emerald-900 border-emerald-400 font-black");
                        }
                    }, 1000);
                } else if (dang.includes("tachycardia") || medId === "adrenalin" || medId === "atropin") {
                    // KATASTROFIK XATO!
                    flash.classList.add("inj-danger");
                    setTimeout(() => flash.classList.remove("inj-danger"), 1500);
                    playAlarmErrorTone();

                    target = { hr: 0, spo2: 0, sys: 0, dia: 0, rr: 0, temp: 36.5, mode: "dying", rhythm: "asystole" };
                    current.hr = 220;
                    current.rhythm = "vtach";
                    transitionSteps = 30;

                    const errMsg = `🚨 OG'IR XATO: Taxikardiyada ${medName} berildi! Qorinchalar titrashi (VFib) va yurak to'xtashi yuz berdi!`;
                    if (injText) injText.innerText = errMsg;
                    updateBanner(errMsg, "bg-rose-600 text-white border-rose-800 font-black alarm-blink");
                    startAsystoleTone();
                } else {
                    playAlarmErrorTone();
                    const warn = `⚠️ NOMUTANOSIB: Taxikardiyada ${medName} yetarli samara bermaydi. Antiaritmik dori zarur!`;
                    if (injText) injText.innerText = warn;
                    updateBanner(warn, "bg-amber-100 text-amber-900 border-amber-400 font-bold");
                }
            }

            // --- 3. BRADIKARDIYA (22 - 35 BPM) ---
            else if (isBradycardia) {
                if (appr.includes("bradycardia") || medId === "atropin" || medId === "adrenalin") {
                    flash.classList.add("inj-success");
                    setTimeout(() => flash.classList.remove("inj-success"), 1200);

                    target = { hr: 75, spo2: 98, sys: 120, dia: 80, rr: 16, temp: 36.6, mode: "normal", rhythm: "sinus" };
                    totalSteps = 80;
                    transitionSteps = 80;

                    const okMsg = `✅ TO'G'RI DAVO: ${medName} ta'sirida bradikardiya bartaraf etildi, puls 75 BPM ga chiqdi!`;
                    if (injText) injText.innerText = okMsg;
                    updateBanner(okMsg, "bg-emerald-100 text-emerald-900 border-emerald-400 font-black");
                } else if (dang.includes("bradycardia") || medId === "metoprolol") {
                    flash.classList.add("inj-danger");
                    setTimeout(() => flash.classList.remove("inj-danger"), 1500);
                    playAlarmErrorTone();

                    target = { hr: 0, spo2: 0, sys: 0, dia: 0, rr: 0, temp: 36.0, mode: "dying", rhythm: "asystole" };
                    current = { ...target };
                    transitionSteps = 0;
                    startAsystoleTone();

                    const errMsg = `🚨 QO'POL XATO: Bradikardiyada ${medName} berildi! To'liq AV-blokada va yurak to'xtadi!`;
                    if (injText) injText.innerText = errMsg;
                    updateBanner(errMsg, "bg-rose-600 text-white border-rose-800 font-black alarm-blink");
                } else {
                    playAlarmErrorTone();
                    const warn = `⚠️ MOS EMAS: Bradikardiyada ${medName} ritmni oshirmaydi. Atropin yoki ritm ko'taruvchi dori tanlang!`;
                    if (injText) injText.innerText = warn;
                    updateBanner(warn, "bg-amber-100 text-amber-900 border-amber-400 font-bold");
                }
            }

            // --- 4. GIPOKSIYA (SpO2 74%, RR 38) ---
            else if (isHypoxia) {
                if (appr.includes("hypoxia") || medId === "dexa" || medId === "adrenalin" || medId === "saline") {
                    flash.classList.add("inj-success");
                    setTimeout(() => flash.classList.remove("inj-success"), 1200);

                    target = { hr: 75, spo2: 98, sys: 120, dia: 80, rr: 16, temp: 36.6, mode: "normal", rhythm: "sinus" };
                    totalSteps = 80;
                    transitionSteps = 80;

                    const okMsg = `✅ TO'G'RI DAVO: ${medName} ta'sirida gipoksiya bartaraf etildi, kislorod 98% ga tiklandi!`;
                    if (injText) injText.innerText = okMsg;
                    updateBanner(okMsg, "bg-emerald-100 text-emerald-900 border-emerald-400 font-black");
                } else if (dang.includes("hypoxia") || medId === "metoprolol") {
                    flash.classList.add("inj-danger");
                    setTimeout(() => flash.classList.remove("inj-danger"), 1500);
                    playAlarmErrorTone();

                    current.spo2 = 55;
                    current.rr = 45;
                    updateNumericsUI();

                    const errMsg = `🚨 OG'IR ASORAT: Gipoksiyada ${medName} berildi! Bronxospazm keskin kuchaydi (SpO2 55%)!`;
                    if (injText) injText.innerText = errMsg;
                    updateBanner(errMsg, "bg-rose-600 text-white border-rose-800 font-black alarm-blink");
                } else {
                    playAlarmErrorTone();
                    const warn = `⚠️ MOS EMAS: Gipoksiyada ${medName} bronxlarni kengaytirmaydi. Deksametazon yoki kislorod talab qilinadi!`;
                    if (injText) injText.innerText = warn;
                    updateBanner(warn, "bg-amber-100 text-amber-900 border-amber-400 font-bold");
                }
            }

            // --- 5. SHOK / KOLLAPS (BP 65/35, HR 145) ---
            else if (isShock) {
                if (appr.includes("shock") || medId === "saline" || medId === "adrenalin") {
                    flash.classList.add("inj-success");
                    setTimeout(() => flash.classList.remove("inj-success"), 1200);

                    target = { hr: 78, spo2: 98, sys: 120, dia: 80, rr: 16, temp: 36.6, mode: "normal", rhythm: "sinus" };
                    totalSteps = 80;
                    transitionSteps = 80;

                    const okMsg = `✅ TO'G'RI DAVO: ${medName} infuziyasi gemodinamika va qon bosimini tikladi (120/80 mmHg)!`;
                    if (injText) injText.innerText = okMsg;
                    updateBanner(okMsg, "bg-emerald-100 text-emerald-900 border-emerald-400 font-black");
                } else if (dang.includes("shock") || medId === "nitro" || medId === "furosemide") {
                    flash.classList.add("inj-danger");
                    setTimeout(() => flash.classList.remove("inj-danger"), 1500);
                    playAlarmErrorTone();

                    target = { hr: 0, spo2: 0, sys: 20, dia: 10, rr: 4, temp: 35.5, mode: "dying", rhythm: "asystole" };
                    current = { ...target };
                    transitionSteps = 0;
                    startAsystoleTone();

                    const errMsg = `🚨 GIPOVOLEMIK KOLLAPS: Shokda ${medName} berildi! Bosim 20 mmHg ga quladi va yurak to'xtadi!`;
                    if (injText) injText.innerText = errMsg;
                    updateBanner(errMsg, "bg-rose-600 text-white border-rose-800 font-black alarm-blink");
                } else {
                    playAlarmErrorTone();
                    const warn = `⚠️ MOS EMAS: Shokda infuzion hajm (Fizrastvor) yoki vazopressor talab qilinadi!`;
                    if (injText) injText.innerText = warn;
                    updateBanner(warn, "bg-amber-100 text-amber-900 border-amber-400 font-bold");
                }
            }

            // --- 6. NORMAL / SOG'LOM BEMOR (HR 75, BP 120/80) ---
            else {
                if (dang.includes("normal") || medId === "kcl") {
                    flash.classList.add("inj-danger");
                    setTimeout(() => flash.classList.remove("inj-danger"), 1500);
                    playAlarmErrorTone();
                    target = { hr: 0, spo2: 0, sys: 0, dia: 0, rr: 0, temp: 36.0, mode: "dying", rhythm: "asystole" };
                    current = { ...target };
                    transitionSteps = 0;
                    startAsystoleTone();
                    const msg = `🚨 TOKSIK O'LIM: Sog'lom bemorga noo'rin dori (${medName}) qilindi! Kardioplegiya va asistoliya!`;
                    if (injText) injText.innerText = msg;
                    updateBanner(msg, "bg-rose-600 text-white border-rose-800 font-black alarm-blink");
                } else if (medId === "adrenalin") {
                    target = { hr: 160, spo2: 96, sys: 180, dia: 110, rr: 28, temp: 37.0, mode: "attack", rhythm: "vtach" };
                    totalSteps = 60;
                    transitionSteps = 60;
                    const msg = `⚠️ SOG'LOMGA ADRENALIN BERILDI: Doza ortishi oqibatida taxikardiya (160 BPM) va gipertoniya boshlandi!`;
                    if (injText) injText.innerText = msg;
                    updateBanner(msg, "bg-amber-100 text-amber-900 border-amber-400 font-black");
                } else {
                    updateBanner(`ℹ️ ${medName} yuborildi. Parametrlarda jiddiy o'zgarish yo'q.`, "bg-slate-100 text-slate-800 border-slate-300 font-bold");
                }
            }

            setTimeout(() => {
                if (!injectionInProgress && injBanner) {
                    injBanner.classList.add("hidden");
                }
                if (injBtnEl) {
                    injBtnEl.className = "mt-1 w-full py-2 px-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-black text-xs shadow-md flex items-center justify-center gap-1.5 transition cursor-pointer active:scale-95 shrink-0";
                }
            }, 3000);
        }

        function triggerManualInjection() {
            processSmartMedicationAdministration();
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
                current.mode = "dying";
                transitionSteps = 0;
                totalSteps = 0;
                updateNumericsUI();
                updateBanner("🚨 ASISTOLIYA: YURAK TO'XTADI (0 BPM)! CPR (30:2) VA ADRENALIN TALAB QILINADI!", "bg-rose-100 text-rose-900 border-rose-400 alarm-blink font-black");
                if (stageBadge) {
                    stageBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-rose-500 alarm-blink"></span><span>0-BOSQICH: ASISTOLIYA (CPR TALAB QILINADI)</span>`;
                    stageBadge.className = "px-2.5 py-0.5 rounded-lg text-xs font-black bg-rose-100 text-rose-900 border border-rose-400 flex items-center gap-1.5 shadow-sm";
                }
                startAsystoleTone();
                return;
            }

            if (type === "normal") {
                target = { hr: 75, spo2: 98, sys: 120, dia: 80, rr: 16, temp: 36.6, mode: "normal", rhythm: "sinus" };
                current.mode = "normal";
                updateBanner("🟢 STATUS: BARQAROR (NORMAL)", "bg-emerald-100 text-emerald-900 border-emerald-300 font-bold");
                if (stageBadge) {
                    stageBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-500"></span><span>STATUS: BARQAROR NORMAL (75 BPM)</span>`;
                    stageBadge.className = "px-2.5 py-0.5 rounded-lg text-xs font-black bg-emerald-100 text-emerald-900 border border-emerald-400 flex items-center gap-1.5 shadow-sm";
                }
                stopAsystoleTone();
            } else if (type === "attack") {
                target = { hr: 185, spo2: 88, sys: 210, dia: 125, rr: 34, temp: 37.4, mode: "attack", rhythm: "vtach" };
                current.mode = "attack";
                updateBanner("⚡ XURUJ: O'TKIR TAXIKARDIYA (185 BPM)! AMIODARON YOKI METOPROLOL KERAK!", "bg-amber-100 text-amber-900 border-amber-400 alarm-blink font-black");
                stopAsystoleTone();
            } else if (type === "hypoxia") {
                target = { hr: 135, spo2: 74, sys: 135, dia: 90, rr: 38, temp: 36.8, mode: "hypoxia", rhythm: "sinus" };
                current.mode = "hypoxia";
                updateBanner("🫁 GIPOKSIYA: BO'G'ILISH VA KISLOROD YETISHMOVCHILIGI (74%)! DEKSAMETAZON KERAK!", "bg-sky-100 text-sky-900 border-sky-400 alarm-blink font-black");
                stopAsystoleTone();
            } else if (type === "shock") {
                target = { hr: 145, spo2: 89, sys: 65, dia: 35, rr: 28, temp: 35.8, mode: "shock", rhythm: "sinus" };
                current.mode = "shock";
                updateBanner("🩸 SHOK: QON BOSIMINING KESKIN TUSHISHI (65/35)! FIZRASTVOR INFUSIYASI KERAK!", "bg-purple-100 text-purple-900 border-purple-400 alarm-blink font-black");
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
            fetchMedicationsFromServer();
            updateSelectedMedicationUI();
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

class ScanMedicationRequest(BaseModel):
    barcode: Optional[str] = None
    med_id: Optional[str] = None

@app.get("/vital/labels", response_class=HTMLResponse)
@app.get("/labels", response_class=HTMLResponse)
@app.get("/print_labels", response_class=HTMLResponse)
async def get_print_labels():
    return HTMLResponse(content=get_labels_html())

@app.get("/", response_class=HTMLResponse)
@app.get("/vital", response_class=HTMLResponse)
async def get_monitor():
    return HTMLResponse(content=HTML_CONTENT)

@app.post("/api/compressor")
async def api_compressor(req: CompressorRequest):
    return JSONResponse(content={"status": "ok", "cmd": req.cmd})

@app.get("/api/medications")
async def api_get_medications():
    return JSONResponse(content=load_medications())

@app.post("/api/medications")
async def api_save_medication(request: Request):
    try:
        data = await request.json()
        saved = add_or_update_medication(data)
        for ws in active_websockets:
            try: await ws.send_text(json.dumps({"type": "meds_updated"}))
            except: pass
        return JSONResponse(content={"status": "ok", "medication": saved})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

@app.delete("/api/medications/{med_id}")
async def api_delete_medication(med_id: str):
    ok = delete_medication(med_id)
    for ws in active_websockets:
        try: await ws.send_text(json.dumps({"type": "meds_updated"}))
        except: pass
    return JSONResponse(content={"status": "ok" if ok else "not_found"})

@app.post("/api/medications/reset")
async def api_reset_medications():
    meds = reset_to_defaults()
    for ws in active_websockets:
        try: await ws.send_text(json.dumps({"type": "meds_updated"}))
        except: pass
    return JSONResponse(content={"status": "ok", "medications": meds})

@app.post("/api/scan_medication")
async def api_scan_medication(req: ScanMedicationRequest):
    data = {"barcode": req.barcode or req.med_id, "med_id": req.med_id}
    for ws in active_websockets:
        try:
            await ws.send_text(json.dumps(data))
        except:
            pass
    return JSONResponse(content={"status": "ok", "scanned": data})

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
    print("  🏥 ICU IMTIHON XONASI & DORI SKANERI MONITORI")
    print("=" * 65)
    print(f"  Monitor ekrani:       http://localhost:{port}")
    print(f"  Dori skanerlash:      POST http://localhost:{port}/api/scan_medication")
    print(f"  JSON qabul qilish:    POST http://localhost:{port}/api/telemetry")
    print("=" * 65 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
