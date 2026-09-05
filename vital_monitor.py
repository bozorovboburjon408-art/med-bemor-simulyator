import os
import sys
import re
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
from medication_manager import load_medications
from medication_labels import LABELS_HTML, get_labels_html
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
                <i class="fa-solid fa-hospital-user text-indigo-600"></i> AI Bemor (Veb)
            </a>

            <button onclick="openPatientVoiceIntercomModal()" class="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-black text-xs flex items-center gap-1 shadow-md cursor-pointer transition active:scale-95 animate-pulse">
                <i class="fa-solid fa-microphone"></i> 🎙️ AI Bemor Muloqot
            </button>

            <a href="/console" target="_blank" class="px-2 py-1 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 flex items-center gap-1 font-bold shadow-xs">
                <i class="fa-solid fa-hand-holding-heart text-purple-600"></i> Pult
            </a>

            <!-- Volume Slider -->
            <div class="flex items-center gap-1 bg-slate-100 border border-slate-300 px-2 py-1 rounded-lg">
                <button id="btn-audio" onclick="toggleAudio()" class="text-slate-700 hover:text-slate-900 flex items-center gap-1 cursor-pointer">
                    <i id="audio-icon" class="fa-solid fa-volume-low text-emerald-600 text-xs"></i>
                    <span id="audio-text" class="text-xs font-bold">20%</span>
                </button>
                <input type="range" id="monitor-volume-slider" min="0" max="1" step="0.05" value="0.20" oninput="changeMonitorVolume(this.value)" class="w-12 accent-emerald-600 h-1.5 bg-slate-300 rounded cursor-pointer" title="Ovoz balandligi (20% Me'yoriy)">
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

    <!-- BARCODE SCANNER TOAST NOTIFICATION -->
    <div id="barcode-scan-toast" class="hidden my-0.5 bg-purple-600 text-white border-2 border-purple-300 rounded-xl p-2 shadow-lg flex items-center justify-between animate-in fade-in slide-in-from-top-2 duration-200">
        <div class="flex items-center gap-2.5">
            <span class="w-7 h-7 rounded-lg bg-white/20 flex items-center justify-center text-sm font-bold shrink-0">
                <i class="fa-solid fa-barcode"></i>
            </span>
            <div>
                <div id="scan-toast-title" class="text-[10px] font-black uppercase text-purple-200 tracking-wide">📷 SHTRIX-KOD QABUL QILINDI</div>
                <div id="scan-toast-msg" class="text-xs font-black text-white">Adrenalin 1 mg/ml (ADR-01) — Manikenga ukol qilishga tayyor!</div>
            </div>
        </div>
        <span class="mono px-2 py-0.5 rounded bg-white/20 text-xs font-black" id="scan-toast-badge">ADR-01</span>
    </div>

    <!-- PATIENT VOICE & REVIVAL POPUP -->
    <div id="patient-revived-toast" class="hidden my-0.5 bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 text-white border-2 border-emerald-300 rounded-xl p-2 shadow-lg flex items-center justify-between animate-in fade-in slide-in-from-top-2 duration-300">
        <div class="flex items-center gap-3">
            <span class="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-base shrink-0 animate-bounce">
                <i class="fa-solid fa-heart-pulse text-rose-300"></i>
            </span>
            <div>
                <div class="text-[10px] uppercase tracking-wider font-black text-emerald-200 flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full bg-emerald-300 animate-ping"></span>
                    <span>Bemor Jonlandi (Anvar Karimov, 40 yosh)</span>
                </div>
                <div id="patient-revived-speech" class="text-xs md:text-sm font-black text-white italic">
                    "Uh... Rahmat sizga, doktor! Nafasim qaytdi... Meni hayotga qaytardingiz!"
                </div>
            </div>
        </div>
        <div class="flex items-center gap-2 shrink-0">
            <span class="px-2.5 py-1 rounded-lg bg-white/25 text-[11px] font-black tracking-wide border border-white/30">
                🎉 ROSC: 75 BPM
            </span>
            <button onclick="dismissRevivedToast()" class="text-white/80 hover:text-white p-1 rounded cursor-pointer">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>
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
    <footer class="bg-white border border-slate-200 rounded-xl p-1 shadow-xs shrink-0 flex flex-wrap items-center justify-between gap-1 text-[11px]">
        <div class="flex items-center gap-1 text-slate-700 font-bold shrink-0">
            <i class="fa-solid fa-stethoscope text-indigo-600"></i>
            <span class="hidden sm:inline">Ssenariylar:</span>
        </div>

        <div class="flex flex-wrap items-center gap-1">
            <button onclick="setScenario('normal')" class="px-2 py-0.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                🟢 Normal (75)
            </button>

            <button onclick="setScenario('dying')" class="px-2 py-0.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                🚨 Asistoliya (0)
            </button>

            <button onclick="setScenario('vfib')" class="px-2 py-0.5 rounded-lg bg-red-100 hover:bg-red-200 text-red-950 border border-red-400 font-black transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer alarm-blink">
                ⚡ VFib (230)
            </button>

            <button onclick="setScenario('attack')" class="px-2 py-0.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                ⚡ Taxikardiya (185)
            </button>

            <button onclick="setScenario('brady')" class="px-2 py-0.5 rounded-lg bg-orange-50 hover:bg-orange-100 text-orange-800 border border-orange-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                🫀 Bradikardiya (28)
            </button>

            <button onclick="setScenario('hyper')" class="px-2 py-0.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-800 border border-rose-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                🔴 Gipertoniya (220)
            </button>

            <button onclick="setScenario('hypoxia')" class="px-2 py-0.5 rounded-lg bg-sky-50 hover:bg-sky-100 text-sky-800 border border-sky-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                🫁 Gipoksiya (74%)
            </button>

            <button onclick="setScenario('opioid')" class="px-2 py-0.5 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                💉 Opioid Koma (RR 4)
            </button>

            <button onclick="setScenario('shock')" class="px-2 py-0.5 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-800 border border-purple-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                🩸 Shok (65/35)
            </button>

            <button onclick="setScenario('anaphylaxis')" class="px-2 py-0.5 rounded-lg bg-pink-50 hover:bg-pink-100 text-pink-800 border border-pink-300 font-bold transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                🐝 Anafilaksiya (70/40)
            </button>

            <button onclick="openMedCabinetModal()" class="px-2 py-0.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-black transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-pills"></i> 💊 Dorilar
            </button>

            <button onclick="defibrillateShock()" class="px-2 py-0.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-black transition active:scale-95 shadow-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-wand-magic-sparkles"></i> ⚡ Defibrilyator
            </button>
        </div>
    </footer>

    <!-- ==================== AI BEMOR VOICEMAIL / INTERCOM MODAL ==================== -->
    <div id="ai-patient-voice-modal" class="hidden fixed inset-0 bg-slate-900/60 backdrop-blur-xs z-50 flex items-center justify-center p-3 select-none">
        <div class="bg-white border border-slate-200 rounded-2xl w-full max-w-lg shadow-2xl flex flex-col overflow-hidden max-h-[90vh] animate-in fade-in zoom-in-95 duration-150">
            
            <!-- Modal Header -->
            <div class="bg-gradient-to-r from-emerald-700 via-teal-700 to-cyan-700 px-4 py-3 text-white flex items-center justify-between shrink-0">
                <div class="flex items-center gap-2.5">
                    <div class="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center text-xl shadow-inner shrink-0">
                        🗣️
                    </div>
                    <div>
                        <h3 class="font-black text-sm tracking-wide">ICU AI BEMOR BILAN OVOZLI MULOQOT</h3>
                        <p class="text-[11px] text-emerald-100 font-bold" id="ai-patient-status-subtitle">Bemor: Anvar Karimov (40 yosh) • Ssenariy: Normal</p>
                    </div>
                </div>
                <button onclick="closePatientVoiceIntercomModal()" class="w-7 h-7 rounded-lg bg-white/10 hover:bg-white/20 text-white flex items-center justify-center text-base font-bold cursor-pointer transition">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>

            <!-- Conversation Dialogue Area -->
            <div id="ai-patient-chat-box" class="p-3 overflow-y-auto flex-1 space-y-3 bg-slate-50 min-h-[220px] max-h-[360px] text-xs">
                <div class="flex items-start gap-2">
                    <div class="w-7 h-7 rounded-full bg-emerald-600 text-white font-bold flex items-center justify-center text-xs shrink-0 shadow-xs">AI</div>
                    <div class="bg-white border border-slate-200 p-2.5 rounded-2xl rounded-tl-none shadow-xs text-slate-800 font-bold max-w-[85%]">
                        Assalomu alaykum, doktor. Men Anvar Karimovman. Menga biror savolingiz bormi? Ovozli tugmani bosib gapirishingiz yoki tezkor savollarni tanlashingiz mumkin.
                    </div>
                </div>
            </div>

            <!-- Quick Preset Question Chips -->
            <div class="px-3 py-2 bg-slate-100 border-t border-slate-200 flex flex-wrap gap-1 text-[11px] shrink-0">
                <span class="text-slate-500 font-bold text-[10px] w-full mb-0.5"><i class="fa-solid fa-bolt text-amber-500 mr-1"></i>Tezkor klinik savollar (Bosing va so'rang):</span>
                <button type="button" onclick="sendQuickPatientQuestion(this.dataset.q)" data-q="Ahvolingiz qanday?" class="px-2.5 py-1 rounded-lg bg-white border border-slate-300 hover:bg-emerald-50 hover:border-emerald-400 text-slate-700 font-bold cursor-pointer transition active:scale-95 shadow-2xs">
                    💬 "Ahvolingiz qanday?"
                </button>
                <button type="button" onclick="sendQuickPatientQuestion(this.dataset.q)" data-q="Qayeringiz og'riyapti?" class="px-2.5 py-1 rounded-lg bg-white border border-slate-300 hover:bg-emerald-50 hover:border-emerald-400 text-slate-700 font-bold cursor-pointer transition active:scale-95 shadow-2xs">
                    💬 "Qayeringiz og'riyapti?"
                </button>
                <button type="button" onclick="sendQuickPatientQuestion(this.dataset.q)" data-q="Nafas olishingiz qanday?" class="px-2.5 py-1 rounded-lg bg-white border border-slate-300 hover:bg-emerald-50 hover:border-emerald-400 text-slate-700 font-bold cursor-pointer transition active:scale-95 shadow-2xs">
                    💬 "Nafasingiz qanday?"
                </button>
                <button type="button" onclick="sendQuickPatientQuestion(this.dataset.q)" data-q="Boshingiz aylanyaptimi?" class="px-2.5 py-1 rounded-lg bg-white border border-slate-300 hover:bg-emerald-50 hover:border-emerald-400 text-slate-700 font-bold cursor-pointer transition active:scale-95 shadow-2xs">
                    💬 "Boshingiz aylanyaptimi?"
                </button>
                <button type="button" onclick="sendQuickPatientQuestion(this.dataset.q)" data-q="Dori ichganmidingiz?" class="px-2.5 py-1 rounded-lg bg-white border border-slate-300 hover:bg-emerald-50 hover:border-emerald-400 text-slate-700 font-bold cursor-pointer transition active:scale-95 shadow-2xs">
                    💬 "Dori ichganmisiz?"
                </button>
                <button type="button" onclick="sendQuickPatientQuestion(this.dataset.q)" data-q="Yuragingiz qanday uryapti?" class="px-2.5 py-1 rounded-lg bg-white border border-slate-300 hover:bg-emerald-50 hover:border-emerald-400 text-slate-700 font-bold cursor-pointer transition active:scale-95 shadow-2xs">
                    💬 "Yurak urishi qanday?"
                </button>
                <button type="button" onclick="sendQuickPatientQuestion(this.dataset.q)" data-q="Qachondan beri og'riyapti?" class="px-2.5 py-1 rounded-lg bg-white border border-slate-300 hover:bg-emerald-50 hover:border-emerald-400 text-slate-700 font-bold cursor-pointer transition active:scale-95 shadow-2xs">
                    💬 "Qachon boshlandi?"
                </button>
            </div>

            <!-- Recording and Controls Footer -->
            <div class="p-3 bg-white border-t border-slate-200 flex flex-col gap-2 shrink-0">
                
                <!-- Hands-Free VAD Toggle Card -->
                <div class="flex items-center justify-between p-2 rounded-xl bg-emerald-50/80 border border-emerald-200 shadow-2xs">
                    <div class="flex items-center gap-2">
                        <span id="vad-status-dot" class="w-3 h-3 rounded-full bg-slate-400"></span>
                        <div>
                            <div class="font-black text-slate-800 text-[11px] flex items-center gap-1.5">
                                <span>🎙️ Hands-Free Avto-Eshitish (VAD)</span>
                                <span class="px-1.5 py-0.2 text-[9px] font-extrabold bg-emerald-100 text-emerald-800 rounded">OSCE 0-TOUCH</span>
                            </div>
                            <div id="vad-status-text" class="text-[10px] text-slate-500 font-semibold">Uzluksiz mikrofon (Imtihonda ekranga tegmasdan gapiring)</div>
                        </div>
                    </div>
                    <label class="relative inline-flex items-center cursor-pointer shrink-0 ml-2">
                        <input type="checkbox" id="chk-auto-listen" onchange="toggleAutoListening(this.checked)" class="sr-only peer">
                        <div class="w-9 h-5 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-600"></div>
                    </label>
                </div>

                <!-- Mic Live Audio Visualizer Bar -->
                <div id="mic-audio-level-container" class="hidden flex items-center gap-2 px-3 py-1.5 bg-slate-900 rounded-xl text-white text-[11px] font-bold">
                    <span class="text-rose-400 animate-pulse">🔴 OVOZ YOZILMOQDA:</span>
                    <div class="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden flex items-center">
                        <div id="mic-level-bar" class="h-full bg-emerald-400 rounded-full transition-all duration-75" style="width: 10%;"></div>
                    </div>
                    <span id="mic-timer-text" class="text-xs font-mono text-emerald-300">0:00</span>
                </div>

                <div class="flex items-center gap-2">
                    <button id="btn-ai-mic-record" onclick="togglePatientVoiceRecord()" class="flex-1 py-2.5 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-black text-xs shadow-md flex items-center justify-center gap-2 cursor-pointer transition active:scale-95">
                        <i class="fa-solid fa-microphone text-sm"></i>
                        <span id="btn-ai-mic-text">🎙️ BIR MARTALIK GAPIRISH (Bosing va gapiring)</span>
                    </button>
                    <div class="text-[10px] font-bold text-slate-500 bg-slate-100 border border-slate-200 px-2.5 py-2 rounded-xl text-center shrink-0 cursor-help" title="Masofaviy pult (Bluetooth presenter) yoki Spacebar bosilsa mikrofon yoqiladi">
                        ⌨️ <span class="text-slate-800 font-black">Space</span>
                    </div>
                </div>
                
                <div class="flex items-center gap-2">
                    <input type="text" id="input-ai-patient-text" placeholder="Yoki savolingizni matn ko'rinishida yozing..." onkeydown="if(event.key==='Enter') sendTextPatientQuestion()" class="flex-1 px-3 py-1.5 rounded-lg border border-slate-300 text-xs focus:outline-none focus:border-emerald-500">
                    <button onclick="sendTextPatientQuestion()" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-900 text-white font-bold text-xs cursor-pointer active:scale-95">
                        <i class="fa-solid fa-paper-plane"></i>
                    </button>
                </div>
            </div>

        </div>
    </div>

    <!-- ==================== DORI JAVONI VA SHTRIX-KODLAR MODALI ==================== -->
    <div id="med-modal" class="fixed inset-0 bg-slate-900/60 backdrop-blur-xs hidden z-50 flex items-center justify-center p-3 select-none">
        <div class="bg-white border border-slate-200 rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <!-- Modal Header -->
            <div class="bg-slate-50 border-b border-slate-200 px-4 py-3 flex items-center justify-between">
                <div class="flex items-center gap-2">
                    <span class="w-8 h-8 rounded-xl bg-purple-600 text-white flex items-center justify-center font-bold">
                        <i class="fa-solid fa-barcode text-sm"></i>
                    </span>
                    <div>
                        <h3 class="font-black text-slate-900 text-sm">IMTIHON DORILAR JAVONI & QR/SHTRIX-KOD SKANERI</h3>
                        <p class="text-[11px] text-slate-500 font-medium">Skaner orqali o'tkazing yoki quyidagi ampulalardan tanlang</p>
                    </div>
                </div>
                <button onclick="closeMedCabinetModal()" class="w-8 h-8 rounded-lg bg-slate-200 hover:bg-slate-300 text-slate-700 flex items-center justify-center cursor-pointer">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>

            <!-- Manual Barcode Scanner Input -->
            <div class="p-3 bg-purple-50/70 border-b border-purple-100 flex items-center gap-2">
                <i class="fa-solid fa-barcode text-purple-600 text-lg"></i>
                <input type="text" id="manual-barcode-input" placeholder="Shtrix-kodni skanerlang yoki yozing (masalan: ADR-01, AMI-02)..." onkeydown="if(event.key==='Enter'||event.key==='Tab'){event.preventDefault();scanManualBarcode();}" oninput="onManualBarcodeInput(this.value)" class="flex-1 px-3 py-1.5 bg-white border border-purple-300 rounded-lg text-xs font-mono font-bold focus:outline-none focus:ring-2 focus:ring-purple-500 uppercase">
                <button onclick="scanManualBarcode()" class="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs rounded-lg cursor-pointer">
                    Skanerlash
                </button>
            </div>

            <!-- Medication List Grid -->
            <div id="med-list-container" class="p-3 overflow-y-auto max-h-[60vh] grid grid-cols-1 md:grid-cols-2 gap-2">
                <!-- Javascript will populate medications here -->
            </div>

            <!-- Modal Footer -->
            <div class="bg-slate-50 border-t border-slate-200 px-4 py-2.5 flex items-center justify-between text-xs gap-2">
                <a href="/vital/labels" target="_blank" class="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-black rounded-lg flex items-center gap-1.5 shadow-sm transition active:scale-95 cursor-pointer">
                    <i class="fa-solid fa-print"></i> 🖨️ A4 Chop Etish (10 ta Shtrix & QR Kod)
                </a>
                <button onclick="closeMedCabinetModal()" class="px-4 py-1.5 bg-slate-200 hover:bg-slate-300 font-bold rounded-lg cursor-pointer">
                    Yopish
                </button>
            </div>
        </div>
    </div>

    <!-- JAVASCRIPT ENGINE -->
    <script>
        // ==================== DORI-DARMONLAR BAZASI (MEDICATION DATABASE) ====================
        const MEDICATION_DB = [
        {
                "id": "adrenalin",
                "code": "ADR-01",
                "name": "Adrenalin (Epinefrin) 1 mg/ml",
                "barcodes": [
                        "ADR01",
                        "ADR-01",
                        "ADRENALIN",
                        "EPINEPHRINE",
                        "4780001001"
                ],
                "group": "Adrenomimetik (Vazopressor)",
                "desc": "Yurak to'xtashi, asistoliya va anafilaktik shokda asosiy vosita.",
                "badgeBg": "#7e22ce",
                "btnColor": "bg-purple-600 hover:bg-purple-700",
                "appropriate_for": [
                        "asystole",
                        "bradycardia",
                        "shock",
                        "hypoxia"
                ],
                "dangerous_for": [
                        "tachycardia"
                ]
        },
        {
                "id": "amiodaron",
                "code": "AMI-02",
                "name": "Amiodaron (Kordaron) 150 mg",
                "barcodes": [
                        "AMI02",
                        "AMI-02",
                        "AMIODARON",
                        "CORDARONE",
                        "4780001002"
                ],
                "group": "Antiaritmik (III-sinf)",
                "desc": "Qorincha taxikardiyasi (VTach) va aritmiyalarni to'xtatuvchi.",
                "badgeBg": "#0284c7",
                "btnColor": "bg-sky-600 hover:bg-sky-700",
                "appropriate_for": [
                        "tachycardia"
                ],
                "dangerous_for": [
                        "bradycardia",
                        "asystole"
                ]
        },
        {
                "id": "atropin",
                "code": "ATR-03",
                "name": "Atropin sulfat 1 mg/ml",
                "barcodes": [
                        "ATR03",
                        "ATR-03",
                        "ATROPIN",
                        "ATROPINE",
                        "4780001003"
                ],
                "group": "M-Xolinoblokator",
                "desc": "Sust puls (bradikardiya) va AV-blokadalarda ritmni oshiradi.",
                "badgeBg": "#d97706",
                "btnColor": "bg-amber-600 hover:bg-amber-700",
                "appropriate_for": [
                        "bradycardia"
                ],
                "dangerous_for": [
                        "tachycardia"
                ]
        },
        {
                "id": "nitro",
                "code": "NIT-04",
                "name": "Nitroglitserin 0.5 mg",
                "barcodes": [
                        "NIT04",
                        "NIT-04",
                        "NITRO",
                        "NITROGLYCERIN",
                        "4780001004"
                ],
                "group": "Periferik vazodilatator",
                "desc": "O'tkir gipertonik kriz va stenokardiyada bosimni tushiradi.",
                "badgeBg": "#e11d48",
                "btnColor": "bg-rose-600 hover:bg-rose-700",
                "appropriate_for": [
                        "attack"
                ],
                "dangerous_for": [
                        "shock",
                        "asystole"
                ]
        },
        {
                "id": "metoprolol",
                "code": "MET-05",
                "name": "Metoprolol (Beta-blokator) 5 mg",
                "barcodes": [
                        "MET05",
                        "MET-05",
                        "METOPROLOL",
                        "BETALOC",
                        "4780001005"
                ],
                "group": "Beta-1 adrenoblokator",
                "desc": "Taxikardiyada puls va miokard kislorod talabini pasaytiradi.",
                "badgeBg": "#4f46e5",
                "btnColor": "bg-indigo-600 hover:bg-indigo-700",
                "appropriate_for": [
                        "tachycardia"
                ],
                "dangerous_for": [
                        "bradycardia",
                        "asystole",
                        "hypoxia"
                ]
        },
        {
                "id": "saline",
                "code": "SAL-06",
                "name": "Fizrastvor (0.9% NaCl) 500 ml",
                "barcodes": [
                        "SAL06",
                        "SAL-06",
                        "NACL",
                        "FIZRASTVOR",
                        "SALINE",
                        "4780001006"
                ],
                "group": "Kristalloid plazma o'rnini bosuvchi",
                "desc": "Gipovolemik va qon yo'qotish shokida qon bosimini tiklaydi.",
                "badgeBg": "#2563eb",
                "btnColor": "bg-blue-600 hover:bg-blue-700",
                "appropriate_for": [
                        "shock",
                        "hypoxia"
                ],
                "dangerous_for": []
        },
        {
                "id": "dexa",
                "code": "DEX-07",
                "name": "Deksametazon 8 mg/2ml",
                "barcodes": [
                        "DEX07",
                        "DEX-07",
                        "DEXA",
                        "DEXAMETHASONE",
                        "4780001007"
                ],
                "group": "Glikokortikosteroid (Gormon)",
                "desc": "Bronxospazm, anafilaksiya va o'tkir gipoksiyani bartaraf etadi.",
                "badgeBg": "#059669",
                "btnColor": "bg-emerald-600 hover:bg-emerald-700",
                "appropriate_for": [
                        "hypoxia"
                ],
                "dangerous_for": []
        },
        {
                "id": "naloxone",
                "code": "NAL-08",
                "name": "Nalokson 0.4 mg/ml",
                "barcodes": [
                        "NAL08",
                        "NAL-08",
                        "NALOXON",
                        "NALOXONE",
                        "4780001008"
                ],
                "group": "Opioid retseptorlari antagonisti",
                "desc": "Narkotik intoksikatsiyasi va nafas tormozlanishiga qarshi vosita.",
                "badgeBg": "#0d9488",
                "btnColor": "bg-teal-600 hover:bg-teal-700",
                "appropriate_for": [
                        "hypoxia"
                ],
                "dangerous_for": []
        },
        {
                "id": "kcl",
                "code": "KCL-09",
                "name": "Kaliy xlorid (KCl 4%) 20 ml",
                "barcodes": [
                        "KCL09",
                        "KCL-09",
                        "KCL",
                        "POTASSIUM",
                        "4780001009"
                ],
                "group": "Elektrolit (Toksik konsentrat)",
                "desc": "DIQQAT: Sof holda vena ichiga yuborish kardioplegiya chaqiradi!",
                "badgeBg": "#dc2626",
                "btnColor": "bg-red-600 hover:bg-red-700",
                "appropriate_for": [],
                "dangerous_for": [
                        "asystole",
                        "normal",
                        "shock",
                        "bradycardia",
                        "tachycardia"
                ]
        },
        {
                "id": "furosemide",
                "code": "FUR-10",
                "name": "Furosemid (Laziks) 20 mg",
                "barcodes": [
                        "FUR10",
                        "FUR-10",
                        "FUROSEMID",
                        "LASIX",
                        "4780001010"
                ],
                "group": "Halqa diuretigi",
                "desc": "O'pka shishi va gipertoniyada tezkor suyuqlik haydovchi vosita.",
                "badgeBg": "#0891b2",
                "btnColor": "bg-cyan-600 hover:bg-cyan-700",
                "appropriate_for": [
                        "attack"
                ],
                "dangerous_for": [
                        "shock",
                        "asystole"
                ]
        }
];

        let selectedMedication = MEDICATION_DB[0]; // Default Adrenalin
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
        let monitorVolume = 0.20;
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

        function playScannerBeep() {
            initAudio();
            try {
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = "sine";
                osc.frequency.setValueAtTime(1200, audioCtx.currentTime);
                osc.frequency.setValueAtTime(1800, audioCtx.currentTime + 0.05);
                gain.gain.setValueAtTime(0.10, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.12);
                osc.connect(gain);
                gain.connect(masterCompressor || audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + 0.12);
            } catch(e) {}
        }

        function playAlarmErrorTone() {
            initAudio();
            try {
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = "sawtooth";
                osc.frequency.setValueAtTime(320, audioCtx.currentTime);
                osc.frequency.setValueAtTime(240, audioCtx.currentTime + 0.2);
                gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.45);
                osc.connect(gain);
                gain.connect(masterCompressor || audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + 0.45);
            } catch(e) {}
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
                monitorVolume = 0.20;
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
                gain1.gain.setValueAtTime(0.10, now);
                gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.095);

                const osc2 = audioCtx.createOscillator();
                const gain2 = audioCtx.createGain();
                osc2.type = "triangle";
                osc2.frequency.setValueAtTime(freq * 1.5, now);
                gain2.gain.setValueAtTime(0.03, now);
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
                gain.gain.setValueAtTime(0.12, now);
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

        // ==================== BEMOR OVOZI VA JONLANISH EFFEKTLARI ====================
        let activeVoiceAudio = null;
        let activeVoiceSource = null;

        function playVoiceAudio(src, fallbackText) {
            if (!soundEnabled) return;
            initAudio();
            onPatientSpeechStart();
            try {
                if (activeVoiceAudio) {
                    try { activeVoiceAudio.pause(); } catch(e) {}
                    activeVoiceAudio = null;
                }
                if (activeVoiceSource) {
                    try { activeVoiceSource.stop(); } catch(e) {}
                    activeVoiceSource = null;
                }

                if (audioCtx && audioCtx.state !== 'closed') {
                    fetch(src)
                        .then(res => res.arrayBuffer())
                        .then(buffer => audioCtx.decodeAudioData(buffer))
                        .then(decodedData => {
                            activeVoiceSource = audioCtx.createBufferSource();
                            activeVoiceSource.buffer = decodedData;

                            const gainNode = audioCtx.createGain();
                            gainNode.gain.setValueAtTime(2.2, audioCtx.currentTime); // 220% Musiqiy tiniq kuchaytiruvchi ovoz (Baland, ammo shovqinsiz va tiniq)

                            activeVoiceSource.connect(gainNode);
                            gainNode.connect(audioCtx.destination);
                            activeVoiceSource.onended = () => { onPatientSpeechEnd(); };
                            activeVoiceSource.start(0);
                        })
                        .catch(err => {
                            activeVoiceAudio = new Audio(src);
                            activeVoiceAudio.volume = 1.0;
                            activeVoiceAudio.onended = () => { onPatientSpeechEnd(); };
                            activeVoiceAudio.onerror = () => { onPatientSpeechEnd(); };
                            activeVoiceAudio.play().catch(() => speakWithFallback(fallbackText));
                        });
                } else {
                    activeVoiceAudio = new Audio(src);
                    activeVoiceAudio.volume = 1.0;
                    activeVoiceAudio.onended = () => { onPatientSpeechEnd(); };
                    activeVoiceAudio.onerror = () => { onPatientSpeechEnd(); };
                    activeVoiceAudio.play().catch(() => speakWithFallback(fallbackText));
                }
            } catch(e) {
                speakWithFallback(fallbackText);
            }
        }

        function speakWithFallback(text) {
            if (!text) {
                onPatientSpeechEnd();
                return;
            }
            const cleanText = text.replace(/\(.*?\)/g, "").replace(/🚨|🟢|⚡|🫀|🔴|🫁|💉|🩸|🐝|💬/g, "").trim();
            if (!cleanText) {
                onPatientSpeechEnd();
                return;
            }

            // Serverdagi Edge-TTS uz-UZ-SardorNeural o'zbek erkak ovozi orqali ijro etish
            fetch("/api/tts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: cleanText, voice: "uz-UZ-SardorNeural" })
            })
            .then(res => res.json())
            .then(data => {
                if (data && data.audio) {
                    playPatientMP3Base64(data.audio);
                } else {
                    speakBrowserSynthesis(cleanText);
                }
            })
            .catch(() => {
                speakBrowserSynthesis(cleanText);
            });
        }

        function speakBrowserSynthesis(cleanText) {
            if (!('speechSynthesis' in window)) {
                onPatientSpeechEnd();
                return;
            }
            try {
                window.speechSynthesis.cancel();
                onPatientSpeechStart();

                const utter = new SpeechSynthesisUtterance(cleanText);
                utter.lang = "uz-UZ";
                utter.rate = 0.88; // Doniqiy va sekinroq me'yordagi talaffuz
                utter.pitch = 0.82; // Erkak kishi (Anvar Karimov, 40 yosh) ovozi uchun past va salmoqli ton (Male pitch)
                utter.volume = 1.0;

                const voices = window.speechSynthesis.getVoices();
                if (voices && voices.length > 0) {
                    const maleUzVoice = voices.find(v => (v.lang.includes("uz") || v.lang.includes("tr")) && (v.name.includes("Sardor") || v.name.includes("Male") || v.name.includes("Ahmet")));
                    const uzVoice = voices.find(v => v.lang.includes("uz") || v.lang.includes("tr"));
                    if (maleUzVoice) {
                        utter.voice = maleUzVoice;
                    } else if (uzVoice) {
                        utter.voice = uzVoice;
                    }
                }

                utter.onend = () => { onPatientSpeechEnd(); };
                utter.onerror = () => { onPatientSpeechEnd(); };
                window.speechSynthesis.speak(utter);
            } catch(e) {
                onPatientSpeechEnd();
            }
        }

        function playRevivalChime() {
            if (!soundEnabled || monitorVolume <= 0) return;
            initAudio();
            if (!audioCtx) return;
            try {
                const now = audioCtx.currentTime;
                const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6 garmonik akkord
                notes.forEach((freq, idx) => {
                    const osc = audioCtx.createOscillator();
                    const gain = audioCtx.createGain();
                    osc.type = "sine";
                    osc.frequency.setValueAtTime(freq, now + idx * 0.12);
                    gain.gain.setValueAtTime(0.0001, now + idx * 0.12);
                    gain.gain.exponentialRampToValueAtTime(0.25 * monitorVolume, now + idx * 0.12 + 0.04);
                    gain.gain.exponentialRampToValueAtTime(0.0001, now + idx * 0.12 + 1.2);
                    osc.connect(gain);
                    gain.connect(masterCompressor || audioCtx.destination);
                    osc.start(now + idx * 0.12);
                    osc.stop(now + idx * 0.12 + 1.25);
                });
            } catch(e) {}
        }

        function playDeepBreathSound() {
            if (!soundEnabled || monitorVolume <= 0) return;
            initAudio();
            if (!audioCtx) return;
            try {
                const now = audioCtx.currentTime;
                const bufferSize = Math.floor(audioCtx.sampleRate * 1.2);
                const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
                const data = buffer.getChannelData(0);
                for (let i = 0; i < bufferSize; i++) {
                    data[i] = (Math.random() * 2 - 1) * 0.5;
                }
                const noise = audioCtx.createBufferSource();
                noise.buffer = buffer;

                const filter = audioCtx.createBiquadFilter();
                filter.type = "bandpass";
                filter.frequency.setValueAtTime(350, now);
                filter.frequency.exponentialRampToValueAtTime(1300, now + 0.6);
                filter.frequency.exponentialRampToValueAtTime(250, now + 1.2);
                filter.Q.setValueAtTime(3.0, now);

                const gain = audioCtx.createGain();
                gain.gain.setValueAtTime(0.001, now);
                gain.gain.exponentialRampToValueAtTime(0.35 * monitorVolume, now + 0.5);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 1.2);

                noise.connect(filter);
                filter.connect(gain);
                gain.connect(masterCompressor || audioCtx.destination);

                noise.start(now);
                noise.stop(now + 1.2);
            } catch(e) {}
        }

        function dismissRevivedToast() {
            const toast = document.getElementById("patient-revived-toast");
            if (toast) toast.classList.add("hidden");
        }

        const REVIVED_VOICES = [
            { src: '/static/audio/patient_revived_1.mp3', text: "Uh... Rahmat sizga, doktor! Nafasim qaytdi... Meni hayotga qaytardingiz!" },
            { src: '/static/audio/patient_revived_2.mp3', text: "Xudoga shukur... Doktor, rahmat sizga! O'zimga keldim, nafas olishim yengillashdi!" },
            { src: '/static/audio/patient_revived_3.mp3', text: "Doktor, katta rahmat! Og'riq qoldi, yuragim me'yorida ura boshladi!" }
        ];

        function triggerPatientRevivedExperience(customSpeech) {
            const toast = document.getElementById("patient-revived-toast");
            const speechEl = document.getElementById("patient-revived-speech");
            
            const choice = REVIVED_VOICES[Math.floor(Math.random() * REVIVED_VOICES.length)];
            const voiceSrc = choice.src;
            const speechText = customSpeech || choice.text;
            
            if (speechEl) speechEl.innerText = `"${speechText}"`;
            if (toast) {
                toast.classList.remove("hidden");
                setTimeout(() => {
                    dismissRevivedToast();
                }, 9000);
            }

            // 1. Chuqur nafas olish tovushi
            playDeepBreathSound();

            // 2. Musiqiy garmonik qo'ng'iroq (Chime)
            setTimeout(() => {
                playRevivalChime();
            }, 450);

            // 3. Bemorning o'zbekcha minnatdorchilik ovozi (3 xil variatsiya)
            setTimeout(() => {
                playVoiceAudio(voiceSrc, speechText);
            }, 950);

            // Yashil bayram chaqnashi
            const flash = document.getElementById("flash-overlay");
            if (flash) {
                flash.classList.add("inj-success");
                setTimeout(() => flash.classList.remove("inj-success"), 1200);
            }
        }

        // ==================== ICU AI BEMOR OVOZLI INTERCOM DVIGATELI & VAD ====================
        let isVoiceRecording = false;
        let isAutoListeningEnabled = false;
        let isAISpeaking = false;
        let speechRecognitionInstance = null;
        let autoListenRecognition = null;
        let mediaRecorderInstance = null;
        let audioChunks = [];
        let micStream = null;
        let micAudioCtx = null;
        let micAnalyser = null;
        let micAnimFrame = null;
        let recordStartTime = 0;
        let recordTimerInterval = null;
        let activePatientAudio = null;
        let sttInProgress = false;

        function openPatientVoiceIntercomModal() {
            const modal = document.getElementById("ai-patient-voice-modal");
            if (modal) modal.classList.remove("hidden");
            updateAIPatientSubtitle();
        }

        function closePatientVoiceIntercomModal() {
            const modal = document.getElementById("ai-patient-voice-modal");
            if (modal) modal.classList.add("hidden");
            if (isVoiceRecording) {
                togglePatientVoiceRecord();
            }
            if (speechRecognitionInstance) {
                try { speechRecognitionInstance.stop(); } catch(e) {}
            }
            if (activePatientAudio) {
                try { activePatientAudio.pause(); } catch(e) {}
                activePatientAudio = null;
            }
        }

        function updateAIPatientSubtitle() {
            const el = document.getElementById("ai-patient-status-subtitle");
            if (!el) return;
            const scMap = {
                "normal": "🟢 Barqaror Normal (75 BPM)",
                "dying": "🚨 Asistoliya (Yurak To'xtagan)",
                "vfib": "⚡ Qorinchalar Fibrillyatsiyasi (VFib)",
                "attack": "⚡ O'tkir Taxikardiya (185 BPM)",
                "brady": "🫀 Bradikardiya & AV-Blokada (28 BPM)",
                "hyper": "🔴 Gipertonik Kriz (220/130 mmHg)",
                "hypoxia": "🫁 Gipoksiya & Bronxospazm (SpO2 74%)",
                "opioid": "💉 Opioid Koma (RR 4/min)",
                "shock": "🩸 Gipovolemik Shok (65/35 mmHg)",
                "anaphylaxis": "🐝 Anafilaktik Shok (70/40 mmHg)"
            };
            const scName = scMap[current.mode] || current.mode;
            el.innerText = "Bemor: Anvar Karimov (40 yosh) • Ssenariy: " + scName;
        }

        function updateVADStatusUI(state) {
            const dot = document.getElementById("vad-status-dot");
            const text = document.getElementById("vad-status-text");
            if (!dot || !text) return;

            if (state === "off") {
                dot.className = "w-3 h-3 rounded-full bg-slate-400";
                text.innerText = "Hands-Free VAD o'chirilgan (Manual tugma rejimi)";
            } else if (state === "listening") {
                dot.className = "w-3 h-3 rounded-full bg-emerald-500 alarm-blink shadow-xs";
                text.innerText = "🟢 Uzluksiz tinglanmoqda... (Mikrofon faol, gapiravering)";
            } else if (state === "speaking") {
                dot.className = "w-3 h-3 rounded-full bg-amber-500 shadow-xs";
                text.innerText = "🗣️ Bemor javob bermoqda... (Mikrofon vaqtincha pauzada)";
            } else if (state === "processing") {
                dot.className = "w-3 h-3 rounded-full bg-sky-500 animate-pulse";
                text.innerText = "⏳ Savol tahlil qilinmoqda (AI Bemor o'ylamoqda)...";
            }
        }

        function playPatientMP3Base64(base64Data) {
            if (!base64Data || !soundEnabled) return;
            initAudio();
            try {
                if (activePatientAudio) {
                    try { activePatientAudio.pause(); } catch(e) {}
                    activePatientAudio = null;
                }
                onPatientSpeechStart();
                activePatientAudio = new Audio("data:audio/mp3;base64," + base64Data);
                activePatientAudio.volume = 1.0;
                activePatientAudio.onended = () => { onPatientSpeechEnd(); activePatientAudio = null; };
                activePatientAudio.onerror = () => { onPatientSpeechEnd(); activePatientAudio = null; };
                activePatientAudio.play().catch(e => {
                    console.warn("Audio play error:", e);
                    onPatientSpeechEnd();
                });
            } catch(e) {
                console.error("playPatientMP3Base64 error:", e);
                onPatientSpeechEnd();
            }
        }

        function speakAIPatientResponse(text, base64Audio) {
            if (!soundEnabled) return;
            initAudio();

            // 1. Agar serverdan to'g'ridan-to'g'ri Edge-TTS (Sardor erkak ovozi) MP3 audio kelgan bo'lsa, uni ijro etamiz
            if (base64Audio && base64Audio.length > 50) {
                playPatientMP3Base64(base64Audio);
                return;
            }

            // 2. Agar audio bo'lmasa, /api/tts orqali o'zbek erkak ovozini olamiz
            fetch("/api/tts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: text, voice: "uz-UZ-SardorNeural" })
            })
            .then(res => res.json())
            .then(data => {
                if (data && data.audio) {
                    playPatientMP3Base64(data.audio);
                } else {
                    speakWithFallback(text);
                }
            })
            .catch(() => {
                speakWithFallback(text);
            });
        }

        async function startMicrophoneCapture() {
            const levelContainer = document.getElementById("mic-audio-level-container");
            const levelBar = document.getElementById("mic-level-bar");
            if (levelContainer) levelContainer.classList.remove("hidden");
            if (levelBar) levelBar.style.width = "20%";

            try {
                audioChunks = [];
                micStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });

                // Audio level visualizer
                try {
                    micAudioCtx = new (window.AudioContext || window.webkitAudioContext)();
                    const source = micAudioCtx.createMediaStreamSource(micStream);
                    micAnalyser = micAudioCtx.createAnalyser();
                    micAnalyser.fftSize = 64;
                    source.connect(micAnalyser);

                    const dataArray = new Uint8Array(micAnalyser.frequencyBinCount);
                    const updateMeter = () => {
                        if (!isVoiceRecording && !isAutoListeningEnabled) return;
                        if (micAnalyser) {
                            micAnalyser.getByteFrequencyData(dataArray);
                            let sum = 0;
                            for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
                            const avg = sum / dataArray.length;
                            const pct = Math.min(100, Math.max(5, Math.round((avg / 128) * 100)));
                            if (levelBar) levelBar.style.width = pct + "%";
                        }
                        micAnimFrame = requestAnimationFrame(updateMeter);
                    };
                    updateMeter();
                } catch(e) {}

                // MediaRecorder initialization
                let mimeType = 'audio/webm';
                if (window.MediaRecorder) {
                    if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) mimeType = 'audio/webm;codecs=opus';
                    else if (MediaRecorder.isTypeSupported('audio/mp4')) mimeType = 'audio/mp4';
                    else if (MediaRecorder.isTypeSupported('audio/webm')) mimeType = 'audio/webm';
                    
                    mediaRecorderInstance = new MediaRecorder(micStream, { mimeType: mimeType });
                    mediaRecorderInstance.ondataavailable = (e) => {
                        if (e.data && e.data.size > 0) audioChunks.push(e.data);
                    };
                    mediaRecorderInstance.start(250);
                }

                // Recording timer
                recordStartTime = Date.now();
                const timerText = document.getElementById("mic-timer-text");
                if (timerText) timerText.innerText = "0:00";
                if (recordTimerInterval) clearInterval(recordTimerInterval);
                recordTimerInterval = setInterval(() => {
                    const elapsed = Math.floor((Date.now() - recordStartTime) / 1000);
                    const m = Math.floor(elapsed / 60);
                    const s = elapsed % 60;
                    if (timerText) timerText.innerText = m + ":" + (s < 10 ? "0" : "") + s;
                }, 500);

            } catch(err) {
                console.warn("Microphone access error:", err);
            }
        }

        async function stopMicrophoneCapture() {
            if (recordTimerInterval) {
                clearInterval(recordTimerInterval);
                recordTimerInterval = null;
            }
            if (micAnimFrame) {
                cancelAnimationFrame(micAnimFrame);
                micAnimFrame = null;
            }
            const levelContainer = document.getElementById("mic-audio-level-container");
            if (levelContainer) levelContainer.classList.add("hidden");

            if (micAudioCtx) {
                try { micAudioCtx.close(); } catch(e) {}
                micAudioCtx = null;
            }

            if (mediaRecorderInstance && mediaRecorderInstance.state !== 'inactive') {
                return new Promise((resolve) => {
                    mediaRecorderInstance.onstop = async () => {
                        if (micStream) {
                            micStream.getTracks().forEach(t => t.stop());
                            micStream = null;
                        }
                        const blob = new Blob(audioChunks, { type: mediaRecorderInstance.mimeType || 'audio/webm' });
                        audioChunks = [];
                        
                        // Faqatgina SpeechRecognition matn qaytarmagan bo'lsa STT ga yuboramiz
                        if (blob.size > 800 && !sttInProgress) {
                            sttInProgress = true;
                            updateVADStatusUI("processing");
                            const reader = new FileReader();
                            reader.onloadend = async () => {
                                const base64data = reader.result.split(',')[1];
                                if (base64data) {
                                    try {
                                        const res = await fetch("/api/stt", {
                                            method: "POST",
                                            headers: { "Content-Type": "application/json" },
                                            body: JSON.stringify({ audio_base64: base64data, mime_type: blob.type })
                                        });
                                        const data = await res.json();
                                        if (data && data.text && data.text.trim().length >= 2) {
                                            processAIPatientVoiceQuestion(data.text.trim());
                                        }
                                    } catch(e) {
                                        console.warn("STT error:", e);
                                    }
                                }
                                sttInProgress = false;
                                resolve();
                            };
                            reader.readAsDataURL(blob);
                        } else {
                            resolve();
                        }
                    };
                    try { mediaRecorderInstance.stop(); } catch(e) { resolve(); }
                });
            } else {
                if (micStream) {
                    micStream.getTracks().forEach(t => t.stop());
                    micStream = null;
                }
            }
        }

        function toggleAutoListening(enabled) {
            isAutoListeningEnabled = enabled;
            const chk = document.getElementById("chk-auto-listen");
            if (chk) chk.checked = enabled;

            if (enabled) {
                startAutoListeningVAD();
            } else {
                stopAutoListeningVAD();
                updateVADStatusUI("off");
            }
        }

        function startAutoListeningVAD() {
            if (!isAutoListeningEnabled || isAISpeaking) return;

            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                // Agar Web Speech API bo'lmasa, manual ovoz yozish rejimiga o'tamiz
                updateVADStatusUI("off");
                return;
            }

            if (autoListenRecognition) {
                try { autoListenRecognition.stop(); } catch(e) {}
            }

            autoListenRecognition = new SpeechRecognition();
            autoListenRecognition.lang = "uz-UZ";
            autoListenRecognition.interimResults = false;
            autoListenRecognition.maxAlternatives = 1;
            autoListenRecognition.continuous = true;

            autoListenRecognition.onstart = () => {
                updateVADStatusUI("listening");
            };

            autoListenRecognition.onresult = (event) => {
                if (isAISpeaking) return;
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    if (event.results[i].isFinal) {
                        const recognizedText = event.results[i][0].transcript.trim();
                        if (recognizedText.length >= 2) {
                            updateVADStatusUI("processing");
                            processAIPatientVoiceQuestion(recognizedText);
                        }
                    }
                }
            };

            autoListenRecognition.onerror = (err) => {
                console.warn("Auto VAD speech error:", err);
            };

            autoListenRecognition.onend = () => {
                if (isAutoListeningEnabled && !isAISpeaking) {
                    setTimeout(() => {
                        if (isAutoListeningEnabled && !isAISpeaking) {
                            try { autoListenRecognition.start(); } catch(e) {}
                        }
                    }, 300);
                }
            };

            try {
                autoListenRecognition.start();
            } catch(e) {
                console.warn("Could not start autoListenRecognition:", e);
            }
        }

        function stopAutoListeningVAD() {
            if (autoListenRecognition) {
                try { autoListenRecognition.stop(); } catch(e) {}
                autoListenRecognition = null;
            }
        }

        function onPatientSpeechStart() {
            isAISpeaking = true;
            if (autoListenRecognition) {
                try { autoListenRecognition.stop(); } catch(e) {}
            }
            updateVADStatusUI("speaking");
        }

        function onPatientSpeechEnd() {
            isAISpeaking = false;
            if (isAutoListeningEnabled) {
                updateVADStatusUI("listening");
                setTimeout(() => {
                    if (isAutoListeningEnabled && !isAISpeaking) {
                        startAutoListeningVAD();
                    }
                }, 400);
            } else {
                updateVADStatusUI("off");
            }
        }

        async function togglePatientVoiceRecord() {
            const btn = document.getElementById("btn-ai-mic-record");
            const textEl = document.getElementById("btn-ai-mic-text");

            if (isVoiceRecording) {
                isVoiceRecording = false;
                if (btn) btn.className = "flex-1 py-2.5 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-black text-xs shadow-md flex items-center justify-center gap-2 cursor-pointer transition active:scale-95";
                if (textEl) textEl.innerText = "🎙️ BIR MARTALIK GAPIRISH (Bosing va gapiring)";

                if (speechRecognitionInstance) {
                    try { speechRecognitionInstance.stop(); } catch(e) {}
                }
                await stopMicrophoneCapture();
                return;
            }

            isVoiceRecording = true;
            sttInProgress = false;
            if (btn) btn.className = "flex-1 py-2.5 px-3 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-black text-xs shadow-md flex items-center justify-center gap-2 cursor-pointer transition active:scale-95 alarm-blink";
            if (textEl) textEl.innerText = "🔴 ESHITILMOQDA... GAPIRING (Tugatish uchun bosing)";

            await startMicrophoneCapture();

            // Web Speech API parallel tanib olish
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (SpeechRecognition) {
                try {
                    speechRecognitionInstance = new SpeechRecognition();
                    speechRecognitionInstance.lang = "uz-UZ";
                    speechRecognitionInstance.interimResults = false;
                    speechRecognitionInstance.maxAlternatives = 1;

                    speechRecognitionInstance.onstart = () => {};

                    speechRecognitionInstance.onresult = (event) => {
                        if (event.results && event.results[0] && event.results[0][0]) {
                            const text = event.results[0][0].transcript.trim();
                            if (text.length >= 2) {
                                sttInProgress = true;
                                processAIPatientVoiceQuestion(text);
                            }
                        }
                    };

                    speechRecognitionInstance.onerror = (err) => {
                        console.warn("Speech recognition error:", err);
                    };

                    speechRecognitionInstance.onend = () => {};

                    speechRecognitionInstance.start();
                } catch(e) {
                    console.warn("SpeechRecognition start error:", e);
                }
            }
        }

        // Global hotkey listener for Bluetooth presenter clicker and Spacebar key
        document.addEventListener('keydown', (e) => {
            const activeTag = document.activeElement ? document.activeElement.tagName : '';
            if (activeTag === 'INPUT' || activeTag === 'TEXTAREA') return;

            if (e.code === 'Space' || e.key === ' ' || e.key === 'PageDown' || e.key === 'PageUp') {
                if (e.code === 'Space' || e.key === ' ') e.preventDefault();

                const modal = document.getElementById("ai-patient-voice-modal");
                if (modal && modal.classList.contains("hidden")) {
                    openPatientVoiceIntercomModal();
                }
                togglePatientVoiceRecord();
            }
        });

        function sendQuickPatientQuestion(text) {
            if (!text || !text.trim()) return;
            processAIPatientVoiceQuestion(text.trim());
        }

        function sendTextPatientQuestion() {
            const input = document.getElementById("input-ai-patient-text");
            if (!input || !input.value.trim()) return;
            const text = input.value.trim();
            input.value = "";
            processAIPatientVoiceQuestion(text);
        }

        function processAIPatientVoiceQuestion(docQuestion) {
            appendChatBubble("doc", docQuestion);
            updateAIPatientSubtitle();

            const qLower = docQuestion.toLowerCase().trim();
            const mode = current.mode || "normal";
            const hr = Math.round(current.hr);
            const sys = Math.round(current.sys);
            const dia = Math.round(current.dia || 80);
            const spo2 = Math.round(current.spo2);
            const rr = Math.round(current.rr);

            const respond = (text, audioBase64 = null) => {
                setTimeout(() => {
                    appendChatBubble("patient", text);
                    // Ovozli ijro uchun qavs ichidagi sahna izohlarini (masalan: "(Zaif va sekin ovozda)", "(shoshmasdan gapirib)") olib tashlaymiz
                    const spokenText = text.replace(/\(.*?\)/g, "").replace(/🚨|🟢|⚡|🫀|🔴|🫁|💉|🩸|🐝|💬/g, "").trim();
                    if (spokenText) {
                        speakAIPatientResponse(spokenText, audioBase64);
                    }
                }, 200);
            };

            // 1. BARCODE VA DORI KODLARI TEKSHIRUVI (Shtrixkodlar, ADR-01, ATR-03, AMI-02...)
            const isBarcodeNum = /^\d{6,16}$/.test(qLower);
            const isDrugCode = /^(adr|atr|ami|fur|met|nit|nal|dex|sal|kcl)[-_\d]/.test(qLower);
            if (isBarcodeNum || isDrugCode) {
                processSmartMedicationAdministration(docQuestion);
                return;
            }

            // 2. CHUQUR KOMA YOKI HUSHSIZLIK (ASYSTOLE, VFIB, OPIOID KOMA)
            if (mode === "dying" || mode === "asystole" || mode === "vfib") {
                respond("🚨 BEMOR HUSHSIZ! Yurak to'xtagan (Asistoliya / VFib). Bemor savollarga javob bera olmaydi, darhol CPR massaji va Defibrillyator qo'llang!");
                return;
            }
            if (mode === "opioid") {
                respond("(Bemor chuqur komada, javob bermaydi)... Qorachiqlar toraygan, nafas daqiqasiga 4 marta. Og'riqli ta'sirga zaif javob bor. Nalokson (0.4mg) va sun'iy nafas talab qilinadi!");
                return;
            }

            // 3. TELEMETRIYA / TASHXIS SAVOLLARI ("puls", "bosim", "saturatsiya", "spo2", "harorat", "ritm")
            if (qLower.includes("puls") || qLower.includes("yurak urishi") || qLower.includes("bosim") || qLower.includes("saturatsiya") || qLower.includes("spo2")) {
                if (qLower.includes("puls") || qLower.includes("urishi")) {
                    respond("Doktor, hozir yurak urishim daqiqasiga " + hr + " marta. " + (hr > 120 ? "Juda tez urib ketyapti!" : hr < 50 ? "Sekin urib holsizlantiryapti..." : "Me'yorida urmoqda."));
                } else if (qLower.includes("bosim")) {
                    respond("Doktor, qon bosimim " + sys + "/" + dia + " mm simob ustuniga teng. " + (sys > 160 ? "Juda baland, ensam qattiq og'riyapti!" : sys < 90 ? "Juda tushib ketgan, boshim aylanmoqda..." : "Barqaror."));
                } else {
                    respond("Kislorod saturatsiyam " + spo2 + "%. " + (spo2 < 90 ? "Nafasim qisib bo'g'ilyapman!" : "Nafas olishim me'yorida."));
                }
                return;
            }

            // 4. CHUQUR MULOQOT UCHUN REAL GEMINI LLM API
            fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ 
                    kasallik_id: mode, 
                    text: docQuestion,
                    vital_info: "Puls: " + hr + " bpm, Bosim: " + sys + "/" + dia + " mmHg, SpO2: " + spo2 + "%, Nafas: " + rr + "/min"
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data && data.text) {
                    respond(data.text, data.audio || null);
                } else {
                    fallbackLocalNLP(qLower, mode, respond);
                }
            })
            .catch(err => {
                console.warn("API chat error, using local fallback:", err);
                fallbackLocalNLP(qLower, mode, respond);
            });
        }

        function fallbackLocalNLP(qLower, mode, respond) {
            let patientResponse = "";
            const isGreeting = qLower.includes("salom") || qLower.includes("alaykum") || qLower.includes("xayrli") || qLower.includes("qalaysiz") || qLower.includes("yaxshimisiz") || qLower.includes("ahvol") || qLower.includes("tuzuk");
            const isName = qLower.includes("ism") || qLower.includes("kimsiz") || qLower.includes("yosh") || qLower.includes("familiya");
            const isPain = qLower.includes("og'ri") || qLower.includes("ogri") || qLower.includes("qayer") || qLower.includes("joyingiz") || qLower.includes("sanchiq");
            const isBreath = qLower.includes("nafas") || qLower.includes("bog'il") || qLower.includes("bogil") || qLower.includes("hansir") || qLower.includes("havo");
            const isHead = qLower.includes("bosh") || qLower.includes("aylan") || qLower.includes("ko'z") || qLower.includes("koz") || qLower.includes("holsiz");
            const isDrug = qLower.includes("dori") || qLower.includes("tabletka") || qLower.includes("ichgan") || qLower.includes("ichdingiz");
            const isHeart = qLower.includes("yurak") || qLower.includes("puls") || qLower.includes("urish") || qLower.includes("gupill");

            if (isName) {
                patientResponse = "Ismim Anvar Karimov, yoshim 40 da, doktor.";
            } else if (mode === "hyper") {
                if (isPain || isHead) patientResponse = "Ensam va peshonam tars yorilib ketay deyapti, doktor! Ko'zlarim oldida qora dog'lar uchmoqda...";
                else if (isDrug) patientResponse = "Aslida Lozartan ichardim, bugun asabiylashib ertalab ichishni unutibman, doktor...";
                else if (isGreeting) patientResponse = "Vaalaykum assalom, doktor! Boshim juda o'tkir og'riyapti, ensam qattiq lo'qqillayapti... Yordam bering!";
                else patientResponse = "Boshim qattiq og'riyapti, ensamda kuchli lo'qqillash bor, doktor.";
            } else if (mode === "attack") {
                if (isHeart || isGreeting) patientResponse = "Assalomu alaykum, doktor... Yuragim ko'kragimdan chiqib ketayotganday o'ta tez urib ketdi, qattiq gupillayapti!";
                else if (isBreath) patientResponse = "Nafasim yetmayapti, to'liq nafas ololmayapman, ichimda kuchli xavotir bor...";
                else if (isDrug) patientResponse = "Doimiy dori ichmayman, lekin bugun ishda 4 finjon achchiq kofe ichgan edim...";
                else patientResponse = "Yuragim juda tez urib, ko'kragim gupillab to'xtamayapti, doktor!";
            } else if (mode === "brady") {
                if (isGreeting || isHead) patientResponse = "(Zaif ovozda)... Vaalaykum assalom, doktor... Boshim aylanib, ko'zim qorong'ulashyapti, butun tanamda mador yo'q...";
                else if (isDrug) patientResponse = "Bosimimga Atenolol ichardim, bugun adashib 2 ta ichib qo'ygan edim...";
                else if (isPain) patientResponse = "O'tkir og'riq yo'q, lekin juda holsizman, oyoq-qo'llarim muzdek bo'lib boryapti...";
                else patientResponse = "Doktor... Boshim qorong'ulashib ketdi, juda sekin urib holsizlantiryapti...";
            } else if (mode === "hypoxia") {
                if (isBreath || isGreeting) patientResponse = "(Hansiqlab)... Dok-tor... Havoo... yetmayapti... Bo'g'ilyapman... Kislorod bering...";
                else patientResponse = "(Hansiqlab)... Nafas... qisyapti... gapirishga holim yo'q...";
            } else if (mode === "shock") {
                if (isGreeting || isHead) patientResponse = "Bosimim tushib, hushimdan ketyapman, doktor... Ko'zim oldi qorong'i...";
                else patientResponse = "Badanimni sovuq ter bosdi, holsizman, doktor...";
            } else if (mode === "anaphylaxis") {
                if (isBreath || isGreeting) patientResponse = "Doktor, badanim toshma va shish, tomog'im qisilib bo'g'ilyapman!";
                else patientResponse = "Lab-yuzim shishib ketdi, nafasim qisyapti, yordam bering!";
            } else {
                if (isGreeting) patientResponse = "Vaalaykum assalom, doktor! O'zimni juda yaxshi his qilyapman, profilaktik ko'rikka kelgandim.";
                else if (isPain) patientResponse = "Yo'q, doktor, hech qayerim og'rimayapti, o'zimni sog'lom his qilyapman.";
                else if (isBreath) patientResponse = "Nafas olishim bir maromda va erkin, hech qanday qiyinchilik yo'q.";
                else if (isDrug) patientResponse = "Doimiy hech qanday dori ichmayman, sog'lig'im joyida.";
                else patientResponse = "O'zimni juda yaxshi his qilyapman, rahmat doktor.";
            }
            respond(patientResponse);
        }

        function appendChatBubble(sender, text) {
            const box = document.getElementById("ai-patient-chat-box");
            if (!box) return;

            const div = document.createElement("div");
            if (sender === "doc") {
                div.className = "flex items-start gap-2 justify-end animate-in fade-in slide-in-from-bottom-2 duration-150";
                div.innerHTML = `
                    <div class="bg-emerald-600 text-white p-2.5 rounded-2xl rounded-tr-none shadow-xs font-bold max-w-[85%]">
                        🩺 <span class="opacity-90">Doktor:</span> "${text}"
                    </div>
                    <div class="w-7 h-7 rounded-full bg-slate-800 text-white font-bold flex items-center justify-center text-xs shrink-0 shadow-xs">Dr</div>
                `;
            } else {
                div.className = "flex items-start gap-2 animate-in fade-in slide-in-from-bottom-2 duration-150";
                div.innerHTML = `
                    <div class="w-7 h-7 rounded-full bg-emerald-600 text-white font-bold flex items-center justify-center text-xs shrink-0 shadow-xs">AI</div>
                    <div class="bg-white border border-slate-200 p-2.5 rounded-2xl rounded-tl-none shadow-xs text-slate-800 font-bold max-w-[85%]">
                        🗣️ <span class="text-emerald-700">Anvar Karimov:</span> "${text}"
                    </div>
                `;
            }

            box.appendChild(div);
            box.scrollTop = box.scrollHeight;
        }

        function speakAIPatientResponse(text) {
            if (!soundEnabled) return;
            initAudio();
            speakWithFallback(text);
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
        let cprRevivalStage = 0; // 0: Asistoliya, 1: 22 BPM jonlanish, 2: To'liq tiklanish (ROSC)

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

        // ==================== BARCODE & QR SCANNER LOGIC (HARDWARE HID, CYRILLIC FIX & AUTO-DEBOUNCE) ====================
        const CYRILLIC_TO_LATIN_MAP = {
            "й": "q",
            "Й": "Q",
            "ц": "w",
            "Ц": "W",
            "у": "e",
            "У": "E",
            "к": "r",
            "К": "R",
            "е": "t",
            "Е": "T",
            "н": "y",
            "Н": "Y",
            "г": "u",
            "Г": "U",
            "ш": "i",
            "Ш": "I",
            "щ": "o",
            "Щ": "O",
            "з": "p",
            "З": "P",
            "х": "[",
            "Х": "[",
            "ъ": "]",
            "Ъ": "]",
            "ф": "a",
            "Ф": "A",
            "ы": "s",
            "Ы": "S",
            "в": "d",
            "В": "D",
            "а": "f",
            "А": "F",
            "п": "g",
            "П": "G",
            "р": "h",
            "Р": "H",
            "о": "j",
            "О": "J",
            "л": "k",
            "Л": "K",
            "д": "l",
            "Д": "L",
            "ж": ";",
            "Ж": ";",
            "э": "'",
            "Э": "'",
            "я": "z",
            "Я": "Z",
            "ч": "x",
            "Ч": "X",
            "с": "c",
            "С": "C",
            "м": "v",
            "М": "V",
            "и": "b",
            "И": "B",
            "т": "n",
            "Т": "N",
            "ь": "m",
            "Ь": "M",
            "б": ",",
            "Б": ",",
            "ю": ".",
            "Ю": "."
};

        function convertCyrillicToLatin(str) {
            if (!str) return "";
            return String(str).split('').map(ch => CYRILLIC_TO_LATIN_MAP[ch] || ch).join('');
        }

        function matchMedication(raw) {
            if (!raw) return null;
            let s = String(raw).trim();
            if (!s) return null;

            // QR kod orqali URL kelgan bo'lsa (masalan https://...?code=ADR-01)
            try {
                if (s.includes("://") || s.startsWith("/")) {
                    const u = new URL(s, window.location.origin);
                    const q = u.searchParams.get("code") || u.searchParams.get("barcode") || u.searchParams.get("id");
                    if (q) s = q.trim();
                    else {
                        const parts = u.pathname.split("/").filter(Boolean);
                        if (parts.length > 0) s = parts[parts.length - 1];
                    }
                }
            } catch(e) {}

            const latin = convertCyrillicToLatin(s).toUpperCase().trim();
            const rawUpper = s.toUpperCase().trim();
            const cleanAlphaNum = latin.replace(/[^A-Z0-9]/g, "");

            for (const med of MEDICATION_DB) {
                const medCodeUpper = (med.code || "").toUpperCase();
                const medCodeClean = medCodeUpper.replace(/[^A-Z0-9]/g, "");
                const medIdUpper = (med.id || "").toUpperCase();

                // 1. To'g'ridan-to'g'ri kod bo'yicha moslik (ADR-01, ADR01, adr-01, ФВК-01)
                if (latin === medCodeUpper || rawUpper === medCodeUpper) return med;
                if (cleanAlphaNum && cleanAlphaNum === medCodeClean) return med;
                if (latin === medIdUpper || rawUpper === medIdUpper) return med;

                // 2. Barcodes massivi bo'yicha
                if (Array.isArray(med.barcodes)) {
                    for (const b of med.barcodes) {
                        const bUpper = b.toUpperCase();
                        const bClean = bUpper.replace(/[^A-Z0-9]/g, "");
                        if (latin === bUpper || rawUpper === bUpper) return med;
                        if (cleanAlphaNum && cleanAlphaNum === bClean) return med;
                    }
                }

                // 3. Dori nomi yoki ID qismi bo'yicha moslik
                if (cleanAlphaNum.length >= 3) {
                    const medNameUpper = (med.name || "").toUpperCase();
                    if (medNameUpper.includes(latin) || medNameUpper.includes(cleanAlphaNum) || latin.includes(medIdUpper)) {
                        return med;
                    }
                }
            }
            return null;
        }

        let barcodeBuffer = "";
        let lastBarcodeKeyTime = 0;
        let barcodeDebounceTimer = null;
        let scanToastTimeout = null;

        function showBarcodeScanToast(title, msg, badge, isError = false) {
            const toast = document.getElementById("barcode-scan-toast");
            const titleEl = document.getElementById("scan-toast-title");
            const msgEl = document.getElementById("scan-toast-msg");
            const badgeEl = document.getElementById("scan-toast-badge");
            if (!toast) return;

            if (titleEl) titleEl.innerText = title;
            if (msgEl) msgEl.innerText = msg;
            if (badgeEl) badgeEl.innerText = badge;

            if (isError) {
                toast.className = "my-0.5 bg-rose-600 text-white border-2 border-rose-300 rounded-xl p-2 shadow-lg flex items-center justify-between animate-in fade-in slide-in-from-top-2 duration-200";
            } else {
                toast.className = "my-0.5 bg-purple-600 text-white border-2 border-purple-300 rounded-xl p-2 shadow-lg flex items-center justify-between animate-in fade-in slide-in-from-top-2 duration-200";
            }
            toast.classList.remove("hidden");

            if (scanToastTimeout) clearTimeout(scanToastTimeout);
            scanToastTimeout = setTimeout(() => {
                toast.classList.add("hidden");
            }, 4500);
        }

        function syncBarcodeToInputs(val) {
            const manualInput = document.getElementById("manual-barcode-input");
            if (manualInput && document.activeElement !== manualInput) {
                manualInput.value = val;
            }
        }

        window.addEventListener("keydown", (e) => {
            const activeEl = document.activeElement;
            const activeTag = activeEl ? activeEl.tagName : '';
            
            // Agar foydalanuvchi matnli inputda (masalan, AI bemor savoli #input-ai-patient-text) yozayotgan bo'lsa, skanerni o'tkazib yuboramiz
            if (activeEl && (activeTag === 'INPUT' || activeTag === 'TEXTAREA') && activeEl.id !== 'manual-barcode-input') {
                return;
            }

            const now = Date.now();

            // Skaner terminator kalitlari: Enter yoki Tab
            if (e.key === "Enter" || e.key === "Tab") {
                if (barcodeBuffer.trim().length >= 2) {
                    e.preventDefault();
                    if (barcodeDebounceTimer) clearTimeout(barcodeDebounceTimer);
                    const codeToProcess = barcodeBuffer.trim();
                    barcodeBuffer = "";
                    processScannedMedication(codeToProcess);
                    return;
                }
                const manualInput = document.getElementById("manual-barcode-input");
                if (manualInput && manualInput.value.trim().length >= 2 && document.activeElement === manualInput) {
                    e.preventDefault();
                    scanManualBarcode();
                    return;
                }
            }

            // Oddiy harf/raqam tugmalari (USB HID skaner o'qiyotganda)
            if (e.key && e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey) {
                // Agar belgilar orasidagi vaqt 350ms dan ortiq bo'lsa, yangi o'qish deb hisoblanadi
                if (now - lastBarcodeKeyTime > 350) {
                    barcodeBuffer = "";
                }
                lastBarcodeKeyTime = now;

                const convertedChar = CYRILLIC_TO_LATIN_MAP[e.key] || e.key;
                barcodeBuffer += convertedChar;

                // Ekranda skaner natijasini jonli ko'rsatib borish
                syncBarcodeToInputs(barcodeBuffer);

                // Debounce auto-detect: Agar skaner Enter yubormasa ham, 140ms sukutdan keyin dori qabul qilinadi
                if (barcodeDebounceTimer) clearTimeout(barcodeDebounceTimer);
                barcodeDebounceTimer = setTimeout(() => {
                    if (barcodeBuffer.trim().length >= 2) {
                        const candidate = barcodeBuffer.trim();
                        const m = matchMedication(candidate);
                        if (m || candidate.length >= 5) {
                            barcodeBuffer = "";
                            processScannedMedication(candidate);
                        }
                    }
                }, 140);
            }
        });

        function processScannedMedication(rawCode) {
            if (!rawCode || !rawCode.trim()) return;
            const clean = rawCode.trim();
            const matched = matchMedication(clean);
            if (matched) {
                selectedMedication = matched;
                playScannerBeep();
                updateSelectedMedicationUI();

                const bannerMsg = `💊 DORI SKANERLANDI: ${matched.name} [${matched.code}] — Manikenga ukol qilish kutilmoqda...`;
                updateBanner(bannerMsg, "bg-purple-100 text-purple-900 border-purple-400 font-black");

                const injText = document.getElementById("inj-banner-text");
                if (injText) injText.innerText = `💉 DORI TAYYORLANDI: ${matched.name}`;

                showBarcodeScanToast(
                    "📷 DORI SHTRIX-KODI QABUL QILINDI",
                    `${matched.name} [${matched.code}] — Manikenga ukol qilishga tayyorlandi!`,
                    matched.code,
                    false
                );

                closeMedCabinetModal();
            } else {
                playAlarmErrorTone();
                const displayCode = convertCyrillicToLatin(clean).toUpperCase();
                updateBanner(`⚠️ NOMA'LUM BARKOD: "${displayCode}" — Dori topilmadi!`, "bg-amber-100 text-amber-900 border-amber-400 font-bold");
                showBarcodeScanToast(
                    "⚠️ NOMA'LUM BARKOD / QR KOD",
                    `"${displayCode}" kodi bo'yicha bazadan dori topilmadi. Qayta urinib ko'ring yoki /vital/labels sahifasidan stikerni o'qing.`,
                    displayCode,
                    true
                );
            }
        }

        function scanManualBarcode() {
            const input = document.getElementById("manual-barcode-input");
            if (input && input.value.trim()) {
                processScannedMedication(input.value.trim());
                input.value = "";
            }
        }

        let manualInputTimeout = null;
        function onManualBarcodeInput(val) {
            if (!val) return;
            const converted = convertCyrillicToLatin(val).toUpperCase();
            if (converted !== val) {
                const input = document.getElementById("manual-barcode-input");
                if (input) input.value = converted;
            }
            if (manualInputTimeout) clearTimeout(manualInputTimeout);
            manualInputTimeout = setTimeout(() => {
                if (val.trim().length >= 3) {
                    const m = matchMedication(val);
                    if (m) {
                        processScannedMedication(val);
                        const input = document.getElementById("manual-barcode-input");
                        if (input) input.value = "";
                    }
                }
            }, 200);
        }

        function selectMedicationDirect(medId) {
            const med = MEDICATION_DB.find(m => m.id === medId);
            if (med) {
                selectedMedication = med;
                playScannerBeep();
                updateSelectedMedicationUI();
                updateBanner(`💊 TANLANDI: ${med.name} [${med.code}] — Manikenga ukol qilish kutilmoqda...`, "bg-purple-100 text-purple-900 border-purple-400 font-black");
                showBarcodeScanToast(
                    "💊 DORI TANLANDI",
                    `${med.name} [${med.code}] — Manikenga ukol qilishga tayyor!`,
                    med.code,
                    false
                );
                closeMedCabinetModal();
            }
        }

        function updateSelectedMedicationUI() {
            const topBadge = document.getElementById("active-med-badge-top");
            if (topBadge) topBadge.innerText = selectedMedication.code;

            const nameEl = document.getElementById("active-med-name");
            if (nameEl) nameEl.innerText = `${selectedMedication.name} (${selectedMedication.code})`;

            const btnLabel = document.getElementById("inj-btn-label");
            if (btnLabel) btnLabel.innerText = `💉 UKOL: ${selectedMedication.name.split(' ')[0].toUpperCase()}`;
        }

        function openMedCabinetModal() {
            const modal = document.getElementById("med-modal");
            const container = document.getElementById("med-list-container");
            if (!modal || !container) return;

            container.innerHTML = MEDICATION_DB.map(m => `
                <div class="border border-slate-200 rounded-xl p-2.5 bg-slate-50/70 hover:bg-white flex flex-col justify-between transition shadow-xs ${selectedMedication.id === m.id ? 'ring-2 ring-purple-600 bg-purple-50/50' : ''}">
                    <div class="flex justify-between items-start gap-1">
                        <div>
                            <div class="font-black text-xs text-slate-900">${m.name}</div>
                            <div class="text-[10px] font-bold text-slate-500">${m.group}</div>
                        </div>
                        <span class="mono px-1.5 py-0.5 rounded text-[10px] font-black bg-white border border-slate-300 text-slate-700 shadow-xs">${m.code}</span>
                    </div>
                    <p class="text-[9px] text-slate-600 my-1 leading-tight">${m.desc}</p>
                    <div class="flex justify-between items-center mt-1 pt-1 border-t border-slate-200">
                        <span class="mono text-[9px] text-slate-400"><i class="fa-solid fa-barcode mr-1"></i>${m.barcodes[0]}</span>
                        <button onclick="selectMedicationDirect('${m.id}')" class="px-2.5 py-1 rounded text-white text-[10px] font-black ${m.btnColor} cursor-pointer active:scale-95 transition shadow-xs">
                            <i class="fa-solid fa-check mr-1"></i> ${selectedMedication.id === m.id ? 'Tayyor' : 'Skanerlash'}
                        </button>
                    </div>
                </div>
            `).join("");

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
                                } else if (line.length >= 2) {
                                    // USB Serial orqali kelgan to'g'ridan-to'g'ri barkod
                                    processScannedMedication(line);
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

                        // Ovozli bildirish: 1-bosqich zaif puls paydo bo'ldi
                        playRevivalChime();
                        setTimeout(() => {
                            playVoiceAudio('/static/audio/cpr_stage1_pulse.mp3', "Reanimatsiya muvaffaqiyatli! Zaif puls paydo bo'ldi. Tezlik bilan Adrenalin yuboring!");
                        }, 500);
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

            const MED_VOICES = {
                "adrenalin": "/static/audio/adrenalin_injected.mp3",
                "amiodaron": "/static/audio/amiodaron_injected.mp3",
                "atropin": "/static/audio/atropin_injected.mp3",
                "nitro": "/static/audio/nitro_injected.mp3",
                "metoprolol": "/static/audio/metoprolol_injected.mp3",
                "saline": "/static/audio/saline_injected.mp3",
                "dexa": "/static/audio/dexa_injected.mp3",
                "naloxone": "/static/audio/naloxone_injected.mp3",
                "furosemide": "/static/audio/furosemide_injected.mp3",
                "kcl": "/static/audio/kcl_danger.mp3"
            };

            if (MED_VOICES[medId] && medId !== "adrenalin") {
                playVoiceAudio(MED_VOICES[medId], `${medName} yuborildi.`);
            }

            // Baholash: joriy holat nima?
            const isAsystoleOrCPR = (current.hr <= 5 || current.mode === "dying" || cprRevivalStage === 1);
            const isTachycardia = (current.mode === "attack" || current.hr >= 160);
            const isBradycardia = (current.hr <= 35 && current.hr > 5);
            const isHypoxia = (current.mode === "hypoxia" || current.spo2 <= 80);
            const isShock = (current.mode === "shock" || (current.sys <= 75 && current.mode !== "anaphylaxis"));
            const isAnaphylaxis = (current.mode === "anaphylaxis");
            const isNormal = (current.mode === "normal" && current.hr > 50 && current.hr < 110);

            // --- 1. ASISTOLIYA / CPR JARAYONI ---
            if (isAsystoleOrCPR) {
                if (medId === "adrenalin") {
                    // TO'G'RI DORI!
                    flash.classList.add("inj-success");
                    setTimeout(() => flash.classList.remove("inj-success"), 1200);

                    injectionInProgress = true;
                    cprRevivalStage = 2;

                    let delaySec = 5;
                    const stageBadge = document.getElementById("cpr-stage-badge");
                    if (stageBadge) {
                        stageBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-purple-500 alarm-blink"></span><span>2-BOSQICH: ADRENALIN YURAKKA YETIB BORMOQDA (${delaySec}s)...</span>`;
                        stageBadge.className = "px-2.5 py-0.5 rounded-lg text-xs font-black bg-purple-100 text-purple-900 border border-purple-400 flex items-center gap-1.5 shadow-sm";
                    }
                    const msg = `✅ TO'G'RI DORI: ${medName} yuborildi! Qon orqali yurakka yetib bormoqda (${delaySec}s)...`;
                    if (injText) injText.innerText = msg;
                    updateBanner(msg, "bg-purple-100 text-purple-900 border-purple-400 font-black");

                    // Ovozli bildirish: Adrenalin yuborildi
                    playVoiceAudio('/static/audio/adrenalin_injected.mp3', "Adrenalin yuborildi. Dori qon orqali yurakka yetib bormoqda.");

                    if (injectionCountdownTimer) clearInterval(injectionCountdownTimer);
                    injectionCountdownTimer = setInterval(() => {
                        delaySec--;
                        if (delaySec > 0) {
                            if (stageBadge) {
                                stageBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-purple-500 alarm-blink"></span><span>2-BOSQICH: ADRENALIN YURAKKA YETIB BORMOQDA (${delaySec}s)...</span>`;
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
                            const recMsg = `🟢 2-BOSQICH: ADRENALIN TA'SIR QILDI! YURAK RITMI TIKLANMOQDA (10s davomida 75 BPM ga)...`;
                            if (injText) injText.innerText = recMsg;
                            updateBanner(recMsg, "bg-emerald-100 text-emerald-900 border-emerald-400 font-black");
                        }
                    }, 1000);
                } else if (medId === "kcl") {
                    // KATASTROFIK XATO! Kaliy xlorid asistoliyada o'lim
                    flash.classList.add("inj-danger");
                    setTimeout(() => flash.classList.remove("inj-danger"), 1500);
                    playAlarmErrorTone();
                    stopAsystoleTone();
                    startAsystoleTone();

                    target = { hr: 0, spo2: 0, sys: 0, dia: 0, rr: 0, temp: 35.5, mode: "dying", rhythm: "asystole" };
                    current = { ...target };
                    transitionSteps = 0;
                    cprRevivalStage = 0;
                    updateNumericsUI();

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

                    const warn = `❌ MOS EMAS: Asistoliyada ${medName} samarasiz! ACLS bo'yicha Adrenalin 1mg (va Ko'krak massaji) talab qilinadi!`;
                    if (injText) injText.innerText = warn;
                    updateBanner(warn, "bg-rose-100 text-rose-900 border-rose-400 font-black");
                }
            }

            // --- 2. O'TKIR TAXIKARDIYA (VTach / SVT 185 BPM) ---
            else if (isTachycardia) {
                if (medId === "amiodaron" || medId === "metoprolol") {
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
                } else if (medId === "adrenalin" || medId === "atropin") {
                    // KATASTROFIK XATO! Taxikardiyada Adrenalin berilsa -> Fibrillyatsiya va Asistoliya
                    flash.classList.add("inj-danger");
                    setTimeout(() => flash.classList.remove("inj-danger"), 1500);
                    playAlarmErrorTone();

                    target = { hr: 0, spo2: 0, sys: 0, dia: 0, rr: 0, temp: 36.5, mode: "dying", rhythm: "asystole" };
                    current.hr = 220; // avval qorincha titrashi
                    current.rhythm = "vtach";
                    transitionSteps = 30; // 3 soniyada 0 ga qulash

                    const errMsg = `🚨 OG'IR XATO: Taxikardiyada ${medName} berildi! Qorinchalar titrashi (VFib) va yurak to'xtashi yuz berdi!`;
                    if (injText) injText.innerText = errMsg;
                    updateBanner(errMsg, "bg-rose-600 text-white border-rose-800 font-black alarm-blink");
                    startAsystoleTone();
                } else if (medId === "kcl") {
                    flash.classList.add("inj-danger");
                    setTimeout(() => flash.classList.remove("inj-danger"), 1500);
                    playAlarmErrorTone();
                    target = { hr: 0, spo2: 0, sys: 0, dia: 0, rr: 0, temp: 36.0, mode: "dying", rhythm: "asystole" };
                    current = { ...target };
                    transitionSteps = 0;
                    updateNumericsUI();
                    startAsystoleTone();
                    const errMsg = `🚨 TOKSIK O'LIM: ${medName} ta'sirida miokard kardioplegiyasi va asistoliya!`;
                    if (injText) injText.innerText = errMsg;
                    updateBanner(errMsg, "bg-rose-600 text-white border-rose-800 font-black alarm-blink");
                } else if (medId === "nitro" || medId === "furosemide") {
                    // Vazodilatator yoki diuretik bosimni pasaytiradi
                    target.sys = 100; target.dia = 60; target.hr = 150;
                    totalSteps = 60; transitionSteps = 60;
                    const warn = `⚠️ DINAMIK TA'SIR: ${medName} arterial bosimni pasaytirib (100/60 mmHg), pulsni 150 ga sekinlashtirdi. Lekin asosiy antiaritmik berilmadi!`;
                    if (injText) injText.innerText = warn;
                    updateBanner(warn, "bg-amber-100 text-amber-900 border-amber-400 font-bold");
                } else {
                    playAlarmErrorTone();
                    const warn = `⚠️ NOMUTANOSIB: Taxikardiyada ${medName} yetarli samara bermaydi. Amiodaron yoki Metoprolol zarur!`;
                    if (injText) injText.innerText = warn;
                    updateBanner(warn, "bg-amber-100 text-amber-900 border-amber-400 font-bold");
                }
            }

            // --- 3. BRADIKARDIYA (22 - 35 BPM) ---
            else if (isBradycardia) {
                if (medId === "atropin" || medId === "adrenalin") {
                    // TO'G'RI DORI!
                    flash.classList.add("inj-success");
                    setTimeout(() => flash.classList.remove("inj-success"), 1200);

                    target = { hr: 75, spo2: 98, sys: 120, dia: 80, rr: 16, temp: 36.6, mode: "normal", rhythm: "sinus" };
                    totalSteps = 80;
                    transitionSteps = 80;

                    const okMsg = `✅ TO'G'RI DAVO: ${medName} ta'sirida bradikardiya bartaraf etildi, puls 75 BPM ga chiqdi!`;
                    if (injText) injText.innerText = okMsg;
                    updateBanner(okMsg, "bg-emerald-100 text-emerald-900 border-emerald-400 font-black");
                } else if (medId === "metoprolol" || medId === "amiodaron") {
                    // XATO! Bradikardiyada beta-blokator/antiaritmik berilsa yurak to'xtaydi
                    flash.classList.add("inj-danger");
                    setTimeout(() => flash.classList.remove("inj-danger"), 1500);
                    playAlarmErrorTone();

                    target = { hr: 0, spo2: 0, sys: 0, dia: 0, rr: 0, temp: 36.0, mode: "dying", rhythm: "asystole" };
                    current = { ...target };
                    transitionSteps = 0;
                    updateNumericsUI();
                    startAsystoleTone();

                    const errMsg = `🚨 QO'POL XATO: Bradikardiyada ${medName} berildi! To'liq AV-blokada va yurak to'xtadi!`;
                    if (injText) injText.innerText = errMsg;
                    updateBanner(errMsg, "bg-rose-600 text-white border-rose-800 font-black alarm-blink");
                } else if (medId === "kcl") {
                    flash.classList.add("inj-danger");
                    setTimeout(() => flash.classList.remove("inj-danger"), 1500);
                    playAlarmErrorTone();
                    target = { hr: 0, spo2: 0, sys: 0, dia: 0, rr: 0, temp: 36.0, mode: "dying", rhythm: "asystole" };
                    current = { ...target };
                    transitionSteps = 0;
                    updateNumericsUI();
                    startAsystoleTone();
                    const errMsg = `🚨 TOKSIK O'LIM: ${medName} ta'sirida asistoliya!`;
                    if (injText) injText.innerText = errMsg;
                    updateBanner(errMsg, "bg-rose-600 text-white border-rose-800 font-black alarm-blink");
                } else {
                    playAlarmErrorTone();
                    const warn = `⚠️ MOS EMAS: Bradikardiyada ${medName} ritmni oshirmaydi. Atropin yoki Adrenalin tanlang!`;
                    if (injText) injText.innerText = warn;
                    updateBanner(warn, "bg-amber-100 text-amber-900 border-amber-400 font-bold");
                }
            }

            // --- 4. GIPOKSIYA (SpO2 74%, RR 38) ---
            else if (isHypoxia) {
                if (medId === "dexa" || medId === "adrenalin" || medId === "saline" || medId === "naloxone") {
                    // TO'G'RI DORI!
                    flash.classList.add("inj-success");
                    setTimeout(() => flash.classList.remove("inj-success"), 1200);

                    target = { hr: 75, spo2: 98, sys: 120, dia: 80, rr: 16, temp: 36.6, mode: "normal", rhythm: "sinus" };
                    totalSteps = 80;
                    transitionSteps = 80;

                    const okMsg = `✅ TO'G'RI DAVO: ${medName} ta'sirida bronxospazm/nafas tormozlanishi ochildi, kislorod 98% ga tiklandi!`;
                    if (injText) injText.innerText = okMsg;
                    updateBanner(okMsg, "bg-emerald-100 text-emerald-900 border-emerald-400 font-black");
                } else if (medId === "metoprolol") {
                    // XATO! Beta-blokator bronxospazmni kuchaytiradi
                    flash.classList.add("inj-danger");
                    setTimeout(() => flash.classList.remove("inj-danger"), 1500);
                    playAlarmErrorTone();

                    current.spo2 = 55;
                    current.rr = 45;
                    updateNumericsUI();

                    const errMsg = `🚨 OG'IR ASORAT: Gipoksiyada Beta-blokator berildi! Bronxospazm keskin kuchaydi (SpO2 55%)!`;
                    if (injText) injText.innerText = errMsg;
                    updateBanner(errMsg, "bg-rose-600 text-white border-rose-800 font-black alarm-blink");
                } else if (medId === "kcl") {
                    flash.classList.add("inj-danger");
                    setTimeout(() => flash.classList.remove("inj-danger"), 1500);
                    playAlarmErrorTone();
                    target = { hr: 0, spo2: 0, sys: 0, dia: 0, rr: 0, temp: 36.0, mode: "dying", rhythm: "asystole" };
                    current = { ...target };
                    transitionSteps = 0;
                    updateNumericsUI();
                    startAsystoleTone();
                    const errMsg = `🚨 TOKSIK O'LIM: ${medName} ta'sirida asistoliya!`;
                    if (injText) injText.innerText = errMsg;
                    updateBanner(errMsg, "bg-rose-600 text-white border-rose-800 font-black alarm-blink");
                } else {
                    playAlarmErrorTone();
                    const warn = `⚠️ MOS EMAS: Gipoksiyada ${medName} bronxlarni kengaytirmaydi. Deksametazon yoki Nalokson talab qilinadi!`;
                    if (injText) injText.innerText = warn;
                    updateBanner(warn, "bg-amber-100 text-amber-900 border-amber-400 font-bold");
                }
            }

            // --- 5. SHOK / KOLLAPS (BP 65/35, HR 145) ---
            else if (isShock) {
                if (medId === "saline" || medId === "adrenalin") {
                    // TO'G'RI DORI!
                    flash.classList.add("inj-success");
                    setTimeout(() => flash.classList.remove("inj-success"), 1200);

                    target = { hr: 78, spo2: 98, sys: 120, dia: 80, rr: 16, temp: 36.6, mode: "normal", rhythm: "sinus" };
                    totalSteps = 80;
                    transitionSteps = 80;

                    const okMsg = `✅ TO'G'RI DAVO: ${medName} infuziyasi gemodinamika va qon bosimini tikladi (120/80 mmHg)!`;
                    if (injText) injText.innerText = okMsg;
                    updateBanner(okMsg, "bg-emerald-100 text-emerald-900 border-emerald-400 font-black");
                } else if (medId === "nitro" || medId === "furosemide") {
                    // KATASTROFA! Shokda vazodilatator yoki diuretik qon bosimini 0 ga tushiradi
                    flash.classList.add("inj-danger");
                    setTimeout(() => flash.classList.remove("inj-danger"), 1500);
                    playAlarmErrorTone();

                    target = { hr: 0, spo2: 0, sys: 20, dia: 10, rr: 4, temp: 35.5, mode: "dying", rhythm: "asystole" };
                    current = { ...target };
                    transitionSteps = 0;
                    updateNumericsUI();
                    startAsystoleTone();

                    const errMsg = `🚨 GIPOVOLEMIK KOLLAPS: Shokda vazodilatator (${medName}) berildi! Bosim 20 mmHg ga quladi va yurak to'xtadi!`;
                    if (injText) injText.innerText = errMsg;
                    updateBanner(errMsg, "bg-rose-600 text-white border-rose-800 font-black alarm-blink");
                } else if (medId === "kcl") {
                    flash.classList.add("inj-danger");
                    setTimeout(() => flash.classList.remove("inj-danger"), 1500);
                    playAlarmErrorTone();
                    target = { hr: 0, spo2: 0, sys: 0, dia: 0, rr: 0, temp: 36.0, mode: "dying", rhythm: "asystole" };
                    current = { ...target };
                    transitionSteps = 0;
                    updateNumericsUI();
                    startAsystoleTone();
                    const errMsg = `🚨 TOKSIK O'LIM: ${medName} ta'sirida asistoliya!`;
                    if (injText) injText.innerText = errMsg;
                    updateBanner(errMsg, "bg-rose-600 text-white border-rose-800 font-black alarm-blink");
                } else {
                    playAlarmErrorTone();
                    const warn = `⚠️ MOS EMAS: Shokda infuzion hajm (Fizrastvor) yoki vazopressor talab qilinadi!`;
                    if (injText) injText.innerText = warn;
                    updateBanner(warn, "bg-amber-100 text-amber-900 border-amber-400 font-bold");
                }
            }

            // --- 5.5 ANAFILAKTIK SHOK (OSCE STANDART: IM ADRENALIN 0.5mg 1:1000) ---
            else if (isAnaphylaxis) {
                if (medId === "adrenalin") {
                    flash.classList.add("inj-success");
                    setTimeout(() => flash.classList.remove("inj-success"), 1200);

                    target = { hr: 75, spo2: 98, sys: 120, dia: 80, rr: 16, temp: 36.6, mode: "normal", rhythm: "sinus" };
                    totalSteps = 80;
                    transitionSteps = 80;

                    const okMsg = `✅ BIRINCHI TANLOV DAVO: IM Adrenalin (0.5mg) ta'sirida stridor va angioedema qaytdi, gemodinamika tiklandi (120/80 mmHg, SpO2 98%)!`;
                    if (injText) injText.innerText = okMsg;
                    updateBanner(okMsg, "bg-emerald-100 text-emerald-900 border-emerald-400 font-black");
                    playVoiceAudio('/static/audio/adrenalin_injected.mp3', "Adrenalin yuborildi. Anafilaktik shok bartaraf etildi.");
                } else if (medId === "dexa" || medId === "saline" || medId === "naloxone") {
                    target.sys = 95; target.spo2 = 88;
                    totalSteps = 60; transitionSteps = 60;
                    const warn = `⚠️ QO'SHIMCHA DAVO: ${medName} yallig'lanish va shishni kamaytirdi, lekin anafilaksiyada birinchi tanlov preparati IM ADRENALIN shart!`;
                    if (injText) injText.innerText = warn;
                    updateBanner(warn, "bg-amber-100 text-amber-900 border-amber-400 font-bold");
                } else if (medId === "metoprolol") {
                    flash.classList.add("inj-danger");
                    setTimeout(() => flash.classList.remove("inj-danger"), 1500);
                    playAlarmErrorTone();
                    target = { hr: 0, spo2: 0, sys: 0, dia: 0, rr: 0, temp: 36.0, mode: "dying", rhythm: "asystole" };
                    current = { ...target };
                    transitionSteps = 0;
                    updateNumericsUI();
                    startAsystoleTone();
                    const errMsg = `🚨 KATASTROFIK XATO: Anafilaksiyada Beta-blokator (Metoprolol) berildi! Kompensatsiyalangan taxikardiya qulab asistoliya yuz berdi!`;
                    if (injText) injText.innerText = errMsg;
                    updateBanner(errMsg, "bg-rose-600 text-white border-rose-800 font-black alarm-blink");
                } else {
                    playAlarmErrorTone();
                    const warn = `⚠️ MOS EMAS: Anafilaktik shokda birinchi navbatda son mushagiga IM Adrenalin 0.5mg yuborilishi shart!`;
                    if (injText) injText.innerText = warn;
                    updateBanner(warn, "bg-amber-100 text-amber-900 border-amber-400 font-bold");
                }
            }

            // --- 6. NORMAL / SOG'LOM BEMOR (HR 75, BP 120/80) ---
            else {
                if (medId === "adrenalin") {
                    target = { hr: 160, spo2: 96, sys: 180, dia: 110, rr: 28, temp: 37.0, mode: "attack", rhythm: "vtach" };
                    totalSteps = 60;
                    transitionSteps = 60;
                    const msg = `⚠️ SOG'LOMGA ADRENALIN BERILDI: Taxikardiya (160 BPM) va gipertoniya boshlandi!`;
                    if (injText) injText.innerText = msg;
                    updateBanner(msg, "bg-amber-100 text-amber-900 border-amber-400 font-black");
                } else if (medId === "atropin") {
                    target = { hr: 105, spo2: 98, sys: 130, dia: 85, rr: 20, temp: 36.6, mode: "normal", rhythm: "sinus" };
                    totalSteps = 60;
                    transitionSteps = 60;
                    const msg = `⚠️ ATROPIN TA'SIRI: Puls 105 BPM ga oshdi (M-Xolinoblokada).`;
                    if (injText) injText.innerText = msg;
                    updateBanner(msg, "bg-amber-100 text-amber-900 border-amber-400 font-bold");
                } else if (medId === "metoprolol") {
                    target = { hr: 52, spo2: 97, sys: 105, dia: 65, rr: 14, temp: 36.5, mode: "normal", rhythm: "sinus" };
                    totalSteps = 60;
                    transitionSteps = 60;
                    const msg = `⚠️ METOPROLOL TA'SIRI: Puls 52 BPM ga va bosim 105/65 mmHg ga pasaytirildi (Beta-blokada).`;
                    if (injText) injText.innerText = msg;
                    updateBanner(msg, "bg-sky-100 text-sky-900 border-sky-400 font-bold");
                } else if (medId === "amiodaron") {
                    target = { hr: 60, spo2: 98, sys: 110, dia: 70, rr: 15, temp: 36.6, mode: "normal", rhythm: "sinus" };
                    totalSteps = 60;
                    transitionSteps = 60;
                    const msg = `⚠️ AMIODARON TA'SIRI: Puls 60 BPM ga va bosim 110/70 mmHg ga pasaytirildi.`;
                    if (injText) injText.innerText = msg;
                    updateBanner(msg, "bg-sky-100 text-sky-900 border-sky-400 font-bold");
                } else if (medId === "nitro") {
                    target = { hr: 82, spo2: 98, sys: 95, dia: 60, rr: 18, temp: 36.6, mode: "normal", rhythm: "sinus" };
                    totalSteps = 60;
                    transitionSteps = 60;
                    const msg = `⚠️ NITROGLITSERIN TA'SIRI: Arterial bosim 95/60 mmHg ga tushdi (Vazodilatatsiya).`;
                    if (injText) injText.innerText = msg;
                    updateBanner(msg, "bg-amber-100 text-amber-900 border-amber-400 font-bold");
                } else if (medId === "furosemide") {
                    target = { hr: 76, spo2: 98, sys: 105, dia: 70, rr: 16, temp: 36.6, mode: "normal", rhythm: "sinus" };
                    totalSteps = 60;
                    transitionSteps = 60;
                    const msg = `⚠️ FUROSEMID TA'SIRI: Diurez faollashdi, arterial bosim 105/70 mmHg ga tushdi.`;
                    if (injText) injText.innerText = msg;
                    updateBanner(msg, "bg-cyan-100 text-cyan-900 border-cyan-400 font-bold");
                } else if (medId === "saline") {
                    target = { hr: 75, spo2: 99, sys: 125, dia: 82, rr: 16, temp: 36.6, mode: "normal", rhythm: "sinus" };
                    totalSteps = 60;
                    transitionSteps = 60;
                    const msg = `💧 FIZRASTVOR INFUZIYASI: Tomir ichi hajmi to'ldirildi (125/82 mmHg).`;
                    if (injText) injText.innerText = msg;
                    updateBanner(msg, "bg-blue-100 text-blue-900 border-blue-400 font-bold");
                } else if (medId === "kcl") {
                    flash.classList.add("inj-danger");
                    setTimeout(() => flash.classList.remove("inj-danger"), 1500);
                    playAlarmErrorTone();
                    target = { hr: 0, spo2: 0, sys: 0, dia: 0, rr: 0, temp: 36.0, mode: "dying", rhythm: "asystole" };
                    current = { ...target };
                    transitionSteps = 0;
                    updateNumericsUI();
                    startAsystoleTone();
                    const msg = `🚨 TOKSIK O'LIM: Sog'lom bemorga konsentrlangan Kaliy Xlorid qilindi! Kardioplegiya va asistoliya!`;
                    if (injText) injText.innerText = msg;
                    updateBanner(msg, "bg-rose-600 text-white border-rose-800 font-black alarm-blink");
                } else {
                    target = { hr: 75, spo2: 99, sys: 120, dia: 80, rr: 16, temp: 36.6, mode: "normal", rhythm: "sinus" };
                    totalSteps = 40;
                    transitionSteps = 40;
                    const msg = `ℹ️ ${medName} yuborildi. Parametrlar barqaror saqlandi.`;
                    if (injText) injText.innerText = msg;
                    updateBanner(msg, "bg-slate-100 text-slate-800 border-slate-300 font-bold");
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

            if (type === "dying" || type === "asystole") {
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
                playVoiceAudio('/static/audio/scenario_asystole.mp3', "Diqqat! Asistoliya! Yurak to'xtadi!");
                return;
            }

            if (type === "vfib") {
                target.hr = 230; target.spo2 = 0; target.sys = 0; target.dia = 0; target.rr = 0;
                current.hr = 230; current.spo2 = 0; current.sys = 0; current.dia = 0; current.rr = 0;
                current.rhythm = "vfib";
                current.mode = "vfib";
                transitionSteps = 0;
                totalSteps = 0;
                updateNumericsUI();
                updateBanner("⚡ QORINCHALAR FIBRILLYATSIYASI (VFIB - 230 BPM)! TEZDA DEFIBRILLYATOR (SHOK) URIB JONLANTIRING!", "bg-red-600 text-white border-red-800 alarm-blink font-black");
                if (stageBadge) {
                    stageBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-red-600 alarm-blink"></span><span>KATASTROFA: VFIB (DEFIBRILLYATOR TALAB QILINADI)</span>`;
                    stageBadge.className = "px-2.5 py-0.5 rounded-lg text-xs font-black bg-red-200 text-red-950 border border-red-400 flex items-center gap-1.5 shadow-sm";
                }
                startAsystoleTone();
                playVoiceAudio('/static/audio/scenario_vfib.mp3', "Kritik holat! Qorinchalar fibrillyatsiyasi!");
                return;
            }

            if (type === "normal") {
                target = { hr: 75, spo2: 98, sys: 120, dia: 80, rr: 16, temp: 36.6, mode: "normal", rhythm: "sinus" };
                current.mode = "normal";
                transitionSteps = 120; totalSteps = 120;
                updateBanner("🟢 STATUS: BARQAROR (NORMAL)", "bg-emerald-100 text-emerald-900 border-emerald-300 font-bold");
                if (stageBadge) {
                    stageBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-500"></span><span>STATUS: BARQAROR NORMAL (75 BPM)</span>`;
                    stageBadge.className = "px-2.5 py-0.5 rounded-lg text-xs font-black bg-emerald-100 text-emerald-900 border border-emerald-400 flex items-center gap-1.5 shadow-sm";
                }
                stopAsystoleTone();
            } else if (type === "attack" || type === "tachycardia" || type === "taxikardiya") {
                target = { hr: 185, spo2: 88, sys: 210, dia: 125, rr: 34, temp: 37.4, mode: "attack", rhythm: "vtach" };
                current.mode = "attack";
                transitionSteps = 120; totalSteps = 120;
                updateBanner("⚡ XURUJ: O'TKIR TAXIKARDIYA (185 BPM)! AMIODARON YOKI METOPROLOL KERAK!", "bg-amber-100 text-amber-900 border-amber-400 alarm-blink font-black");
                stopAsystoleTone();
            } else if (type === "brady" || type === "bradicardia" || type === "bradikardiya") {
                target = { hr: 28, spo2: 91, sys: 85, dia: 50, rr: 12, temp: 36.1, mode: "brady", rhythm: "brady" };
                current.mode = "brady";
                transitionSteps = 120; totalSteps = 120;
                updateBanner("🫀 BRADIKARDIYA & AV-BLOKADA (28 BPM)! ATROPIN YOKI ADRENALIN TALAB QILINADI!", "bg-orange-100 text-orange-900 border-orange-400 alarm-blink font-black");
                stopAsystoleTone();
                playVoiceAudio('/static/audio/scenario_brady.mp3', "Diqqat! Og'ir bradikardiya va AV-blokada!");
            } else if (type === "hyper" || type === "gipertoniya") {
                target = { hr: 115, spo2: 95, sys: 220, dia: 130, rr: 24, temp: 36.8, mode: "hyper", rhythm: "sinus" };
                current.mode = "hyper";
                transitionSteps = 120; totalSteps = 120;
                updateBanner("🔴 GIPERTONIK KRIZ: AYoTB KESKIN OSHDI (220/130 mmHg)! NITROGLITSERIN YOKI FUROSEMID KERAK!", "bg-rose-100 text-rose-900 border-rose-400 alarm-blink font-black");
                stopAsystoleTone();
                playVoiceAudio('/static/audio/scenario_hyper.mp3', "Xavfli gipertonik kriz!");
            } else if (type === "hypoxia" || type === "gipoksiya") {
                target = { hr: 135, spo2: 74, sys: 135, dia: 90, rr: 38, temp: 36.8, mode: "hypoxia", rhythm: "sinus" };
                current.mode = "hypoxia";
                transitionSteps = 120; totalSteps = 120;
                updateBanner("🫁 GIPOKSIYA: BO'G'ILISH VA KISLOROD YETISHMOVCHILIGI (74%)! DEKSAMETAZON KERAK!", "bg-sky-100 text-sky-900 border-sky-400 alarm-blink font-black");
                stopAsystoleTone();
                playVoiceAudio('/static/audio/scenario_hypoxia.mp3', "Diqqat! Gipoksiya va kislorod yetishmovchiligi!");
            } else if (type === "opioid") {
                target = { hr: 42, spo2: 62, sys: 80, dia: 50, rr: 4, temp: 35.2, mode: "opioid", rhythm: "sinus" };
                current.mode = "opioid";
                transitionSteps = 120; totalSteps = 120;
                updateBanner("💉 OPIOID KOMA: NAFAS TORMOZLANISHI (RR 4/min, SpO2 62%)! NALOKSON (0.4mg) VA SUN'IY NAFAS KERAK!", "bg-teal-100 text-teal-900 border-teal-400 alarm-blink font-black");
                stopAsystoleTone();
                playVoiceAudio('/static/audio/scenario_opioid.mp3', "Favqulodda holat! Opioid komasi!");
            } else if (type === "shock" || type === "shok") {
                target = { hr: 145, spo2: 89, sys: 65, dia: 35, rr: 28, temp: 35.8, mode: "shock", rhythm: "sinus" };
                current.mode = "shock";
                transitionSteps = 120; totalSteps = 120;
                updateBanner("🩸 SHOK: QON BOSIMINING KESKIN TUSHISHI (65/35)! FIZRASTVOR INFUSIYASI KERAK!", "bg-purple-100 text-purple-900 border-purple-400 alarm-blink font-black");
                stopAsystoleTone();
                playVoiceAudio('/static/audio/scenario_shock.mp3', "Xavfli shok holati! Qon bosimi keskin tushib ketdi!");
            } else if (type === "anaphylaxis" || type === "anafilaksiya") {
                target = { hr: 140, spo2: 78, sys: 70, dia: 40, rr: 32, temp: 37.8, mode: "anaphylaxis", rhythm: "sinus" };
                current.mode = "anaphylaxis";
                transitionSteps = 120; totalSteps = 120;
                updateBanner("🐝 ANAFILAKTIK SHOK: STRIDOR, ANGIOEDEMA VA GIPOTENZIYA (70/40 mmHg)! BIRINCHI TANLOV: IM ADRENALIN 0.5mg (1:1000)!", "bg-pink-100 text-pink-950 border-pink-400 alarm-blink font-black");
                stopAsystoleTone();
                playVoiceAudio('/static/audio/scenario_anaphylaxis.mp3', "Kritik holat! Anafilaktik shok!");
            }
            updateAIPatientSubtitle();
        }

        function defibrillateShock() {
            initAudio();
            playVoiceAudio('/static/audio/defibrillator_shocked.mp3', "Defibrillyatsiya shoki berildi!");
            const flash = document.getElementById("flash-overlay");
            flash.classList.add("shock-active");
            setTimeout(() => flash.classList.remove("shock-active"), 600);

            try {
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = "sawtooth";
                osc.frequency.setValueAtTime(160, audioCtx.currentTime);
                osc.frequency.exponentialRampToValueAtTime(45, audioCtx.currentTime + 0.3);
                gain.gain.setValueAtTime(0.25, audioCtx.currentTime);
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
                        cprRevivalStage = 0;
                        triggerPatientRevivedExperience("Uh... Rahmat sizga, doktor! Nafasim qaytdi... Meni hayotga qaytardingiz!");
                    }
                }
            }
            updateNumericsUI();
        }, 100);

        function updateNumericsUI() {
            const hrVal = Math.round(current.hr);
            const spo2Val = Math.round(current.spo2);
            const sysVal = Math.round(current.sys);
            const diaVal = Math.round(current.dia);
            const mapVal = Math.round((sysVal + 2 * diaVal) / 3);
            const rrVal = Math.round(current.rr);

            // Bemor holati tiklanganda yoki o'lim/vfib dan boshqa ssenariyga o'tilganda uzoq tiiiiit ovozini o'chiramiz
            if (current.mode !== "dying" && current.mode !== "vfib") {
                stopAsystoleTone();
            }

            document.getElementById("num-hr").innerText = hrVal;
            document.getElementById("num-pr").innerText = hrVal;
            document.getElementById("num-spo2").innerText = spo2Val;
            document.getElementById("num-sys").innerText = sysVal;
            document.getElementById("num-dia").innerText = diaVal;
            document.getElementById("num-map").innerText = mapVal;
            document.getElementById("num-rr").innerText = rrVal;
            document.getElementById("num-temp").innerText = current.temp.toFixed(1);

            const rhythmLabel = document.getElementById("ecg-rhythm-name");
            if (current.rhythm === "vfib" || (current.mode === "vfib" && hrVal > 0)) {
                rhythmLabel.innerText = "Qorinchalar Fibrillyatsiyasi (VFib)";
                rhythmLabel.className = "text-xs font-black text-rose-600 alarm-blink";
            } else if (hrVal <= 0) {
                rhythmLabel.innerText = "ASYSTOLIYA (0 BPM)";
                rhythmLabel.className = "text-xs font-black text-rose-600 alarm-blink";
            } else if (hrVal <= 35 || current.mode === "brady") {
                rhythmLabel.innerText = `Bradikardiya & AV-Blokada (${hrVal} BPM)`;
                rhythmLabel.className = "text-xs font-black text-orange-600";
            } else if (current.mode === "hyper") {
                rhythmLabel.innerText = "Gipertonik Kriz (Sinus Ritmi)";
                rhythmLabel.className = "text-xs font-black text-rose-600";
            } else if (current.mode === "opioid") {
                rhythmLabel.innerText = "Opioid Bradipnoe (Sinus Ritmi)";
                rhythmLabel.className = "text-xs font-black text-teal-600";
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
            if (current.rhythm === "vfib" || current.mode === "vfib") {
                return Math.sin(phase * 45) * 0.55 + Math.cos(phase * 22) * 0.35 + (Math.sin(phase * 75) * 0.15);
            }
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

def get_monitor_html() -> str:
    meds = load_medications()
    meds_json = json.dumps(meds, ensure_ascii=False)
    return re.sub(r'const MEDICATION_DB = \[[\s\S]*?\];', f'const MEDICATION_DB = {meds_json};', HTML_CONTENT)

MONITOR_HTML = get_monitor_html()

@app.get("/", response_class=HTMLResponse)
@app.get("/vital", response_class=HTMLResponse)
async def get_monitor():
    return HTMLResponse(content=get_monitor_html())

@app.post("/api/compressor")
async def api_compressor(req: CompressorRequest):
    return JSONResponse(content={"status": "ok", "cmd": req.cmd})

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
