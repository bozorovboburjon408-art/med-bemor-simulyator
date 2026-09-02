import os
import sys
import socket
import asyncio
import json
import threading
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

# UTF-8 encoding Windows console
try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

app = FastAPI(title="Reanimatsiya va Bemor Hayotiy Ko'rsatkichlari Simulyatori (ESP32 Live)")

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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ICU Bemor Hayotiy Ko'rsatkichlari Monitori (ESP32)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@500;600;700&display=swap');
        
        body {
            background-color: #05070d;
            color: #f1f5f9;
            font-family: 'Rajdhani', sans-serif;
            user-select: none;
            overflow-x: hidden;
        }

        .mono {
            font-family: 'Share Tech Mono', monospace;
        }

        .glow-green { text-shadow: 0 0 12px rgba(34, 197, 94, 0.6); }
        .glow-cyan { text-shadow: 0 0 12px rgba(6, 182, 212, 0.6); }
        .glow-yellow { text-shadow: 0 0 12px rgba(234, 179, 8, 0.6); }
        .glow-red { text-shadow: 0 0 15px rgba(239, 68, 68, 0.8); }
        .glow-white { text-shadow: 0 0 12px rgba(255, 255, 255, 0.6); }

        .border-green { border-color: rgba(34, 197, 94, 0.3); }
        .border-cyan { border-color: rgba(6, 182, 212, 0.3); }
        .border-yellow { border-color: rgba(234, 179, 8, 0.3); }
        .border-red { border-color: rgba(239, 68, 68, 0.5); }

        @keyframes shockFlash {
            0% { background-color: rgba(255, 255, 255, 0.9); }
            100% { background-color: transparent; }
        }
        .shock-active {
            animation: shockFlash 0.6s ease-out;
        }

        @keyframes injFlash {
            0% { background-color: rgba(147, 51, 234, 0.7); }
            100% { background-color: transparent; }
        }
        .inj-active {
            animation: injFlash 1.2s ease-out;
        }

        @keyframes alarmBlink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.2; }
        }
        .alarm-blink {
            animation: alarmBlink 0.8s infinite;
        }
    </style>
</head>
<body class="min-h-screen flex flex-col justify-between p-2 lg:p-4">

    <div id="flash-overlay" class="fixed inset-0 pointer-events-none z-50"></div>

    <!-- TOP HEADER -->
    <header class="bg-[#0c101c] border border-slate-800 rounded-xl px-4 py-2 flex flex-wrap items-center justify-between gap-3 shadow-lg">
        <div class="flex items-center space-x-4">
            <div class="flex items-center space-x-2">
                <span class="w-3 h-3 rounded-full bg-emerald-500 alarm-blink"></span>
                <span class="font-bold text-lg tracking-wider text-slate-100">ICU PATIENT MONITOR</span>
            </div>
            <div class="text-xs text-slate-400 border-l border-slate-700 pl-3">
                KOYKA: <span class="text-white font-bold">#04 (Reanimatsiya)</span>
            </div>
            <div class="text-xs text-slate-400 border-l border-slate-700 pl-3">
                BEMOR: <span class="text-emerald-400 font-bold">Anvar Karimov (40 yosh, Erkak)</span>
            </div>
        </div>

        <div id="alarm-banner" class="px-4 py-1 rounded-md text-xs font-bold uppercase tracking-widest bg-emerald-950/80 text-emerald-400 border border-emerald-700">
            <i class="fa-solid fa-heart-pulse mr-1"></i> STATUS: BARQAROR (NORMAL)
        </div>

        <div class="flex items-center space-x-2 text-xs">
            <a href="/console" target="_blank" class="px-2.5 py-1 rounded bg-purple-900/80 hover:bg-purple-800 text-purple-200 border border-purple-600 flex items-center gap-1.5 transition font-bold shadow">
                <i class="fa-solid fa-graduation-cap text-purple-400"></i>
                <span>🎓 CPR Imtihon & Pult</span>
            </a>

            <button id="btn-web-serial" onclick="connectDirectWebSerial()" class="px-2.5 py-1 rounded bg-blue-900/80 hover:bg-blue-800 text-blue-200 border border-blue-500 flex items-center gap-1.5 transition font-bold shadow cursor-pointer">
                <i class="fa-brands fa-usb text-blue-400"></i>
                <span id="web-serial-text">🔌 Maniken (USB) ga Ulanish</span>
            </button>

            <div id="hw-badge" class="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-slate-400 flex items-center gap-1.5">
                <span id="hw-dot" class="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span id="hw-text">ESP32 UART: Jonli oqim</span>
            </div>

            <button id="btn-audio" onclick="toggleAudio()" class="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 flex items-center gap-1.5 transition">
                <i id="audio-icon" class="fa-solid fa-volume-high text-emerald-400"></i>
                <span id="audio-text">Ovoz: Yoniq</span>
            </button>
            <button onclick="toggleFullScreen()" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-600">
                <i class="fa-solid fa-expand"></i>
            </button>
            <span id="clock" class="mono text-sm text-slate-300">00:00:00</span>
        </div>
    </header>

    <!-- INJECTION / UKOL ALERT BANNER (TOP POPUP) -->
    <div id="inj-banner" class="hidden my-1 bg-purple-950/90 border border-purple-500 rounded-xl p-2.5 shadow-lg text-center text-purple-200 text-sm font-bold alarm-blink">
        <i class="fa-solid fa-syringe text-purple-400 text-lg mr-2"></i> 
        <span>💉 UKOL QILINDI (TOUCH SENSOR)! DORI YUBORILMOQDA...</span>
    </div>

    <!-- LIVE MANIKEN SENSOR TELEMETRY HUD (CPR & AIRWAY) -->
    <div id="cpr-hud" class="my-2 bg-[#090d1a] border border-indigo-900/60 rounded-xl p-3 shadow-md grid grid-cols-2 md:grid-cols-5 gap-3 items-center">
        
        <!-- 1. CPR Compression Force -->
        <div class="flex flex-col border-r border-slate-800 pr-2">
            <div class="flex justify-between items-center text-xs font-bold text-indigo-300 mb-1">
                <span><i class="fa-solid fa-hand-fist mr-1 text-indigo-400"></i> KUCH (f_curr):</span>
                <span id="cpr-force-val" class="mono text-emerald-400 font-bold text-sm">0.0 kg</span>
            </div>
            <div class="w-full bg-slate-800 rounded-full h-3 overflow-hidden relative">
                <div id="cpr-force-bar" class="bg-emerald-500 h-full rounded-full transition-all duration-75" style="width: 0%;"></div>
                <div class="absolute inset-y-0 left-[66%] w-[25%] bg-emerald-500/20 border-x border-emerald-400/50 pointer-events-none"></div>
            </div>
            <div class="flex justify-between text-[10px] text-slate-500 mt-0.5">
                <span>0 kg</span>
                <span class="text-emerald-400">Target (40-55 kg)</span>
                <span>60 kg</span>
            </div>
        </div>

        <!-- 2. CPR Quality Checks (Depth, Recoil, BPM, Position) -->
        <div class="flex flex-col border-r border-slate-800 pr-2 justify-between">
            <div class="text-[11px] font-bold text-slate-300 mb-1 flex items-center justify-between">
                <span><i class="fa-solid fa-clipboard-check text-indigo-400"></i> CPR SIFATI:</span>
                <span id="cpr-count-badge" class="text-xs mono text-indigo-400 font-bold">0 marta</span>
            </div>
            <div class="grid grid-cols-2 gap-1 text-[10px]">
                <span id="badge-d" class="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400 text-center font-bold">Chuqurlik: -</span>
                <span id="badge-r" class="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400 text-center font-bold">Bo'shatish: -</span>
                <span id="badge-bpm" class="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400 text-center font-bold">Tezlik: -</span>
                <span id="badge-pos" class="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400 text-center font-bold">Joyi: -</span>
            </div>
        </div>

        <!-- 3. CPR BPM Speed -->
        <div class="flex flex-col border-r border-slate-800 pr-2 justify-center">
            <div class="flex justify-between items-center text-xs font-bold text-slate-300 mb-1">
                <span><i class="fa-solid fa-gauge text-indigo-400"></i> CPR TEZLIK (bpm):</span>
                <span id="cpr-bpm-val" class="mono text-emerald-400 font-bold text-sm">0 /min</span>
            </div>
            <div id="cpr-rate-badge" class="px-2 py-1 rounded text-xs font-bold bg-slate-900 text-slate-400 border border-slate-800 text-center">
                Standart: 100 - 120 /min
            </div>
        </div>

        <!-- 4. Lung Pressure -->
        <div class="flex flex-col border-r border-slate-800 pr-2">
            <div class="flex justify-between items-center text-xs font-bold text-cyan-300 mb-1">
                <span><i class="fa-solid fa-lungs mr-1 text-cyan-400"></i> O'PKA (lung_p):</span>
                <span id="lung-p-val" class="mono text-cyan-400 font-bold text-sm">0.0 cmH2O</span>
            </div>
            <div class="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
                <div id="lung-p-bar" class="bg-cyan-500 h-full rounded-full transition-all duration-75" style="width: 0%;"></div>
            </div>
            <div id="lung-status-text" class="text-[10px] text-cyan-400 mt-0.5">O'pka: Normal</div>
        </div>

        <!-- 5. Stomach Pressure & Injection Status -->
        <div class="flex flex-col justify-between">
            <div class="flex justify-between items-center text-xs font-bold text-slate-300 mb-1">
                <span><i class="fa-solid fa-circle-exclamation text-yellow-400"></i> OSHQOZON:</span>
                <span id="stomach-p-val" class="mono text-slate-300 font-bold text-xs">0.0</span>
            </div>
            <div id="stomach-alert" class="px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-900 text-slate-400 border border-slate-800 text-center">
                Oshqozon toza
            </div>
            <div id="inj-badge-small" class="text-[10px] text-purple-400 font-semibold mt-0.5 text-center">
                Ukol: Kutilmoqda (Touch 4)
            </div>
        </div>

    </div>

    <!-- MAIN MONITOR DISPLAY (WAVEFORMS + VITAL NUMERICS) -->
    <div class="grid grid-cols-1 lg:grid-cols-4 gap-3 my-1 flex-1">
        
        <!-- LEFT 3 COLUMNS: LIVE CANVAS WAVEFORMS -->
        <div class="lg:col-span-3 bg-[#080b14] border border-slate-800 rounded-xl p-3 flex flex-col justify-between shadow-2xl relative">
            
            <!-- 1. ECG WAVEFORM (Green) -->
            <div class="relative flex-1 flex flex-col min-h-[140px] border-b border-slate-800/80 pb-2">
                <div class="flex justify-between items-center text-xs font-bold text-emerald-400 mb-1">
                    <span class="flex items-center gap-2">
                        <i class="fa-solid fa-bolt"></i> EKG Lead II (mV)
                        <span class="text-[10px] text-slate-500 font-normal">25mm/s 10mm/mV</span>
                    </span>
                    <span id="ecg-rhythm-name" class="text-emerald-400">Sinus Ritmi</span>
                </div>
                <canvas id="ecgCanvas" class="w-full flex-1 rounded bg-black/40"></canvas>
            </div>

            <!-- 2. SpO2 PLETHYSMOGRAM WAVEFORM (Cyan) -->
            <div class="relative flex-1 flex flex-col min-h-[120px] border-b border-slate-800/80 py-2">
                <div class="flex justify-between items-center text-xs font-bold text-cyan-400 mb-1">
                    <span class="flex items-center gap-2">
                        <i class="fa-solid fa-wave-square"></i> SpO2 Pleth
                        <span class="text-[10px] text-slate-500 font-normal">Puls to'lqini</span>
                    </span>
                    <span id="pleth-status" class="text-cyan-400">Normal perfuziya</span>
                </div>
                <canvas id="plethCanvas" class="w-full flex-1 rounded bg-black/40"></canvas>
            </div>

            <!-- 3. RESPIRATION WAVEFORM (Yellow) -->
            <div class="relative flex-1 flex flex-col min-h-[110px] pt-2">
                <div class="flex justify-between items-center text-xs font-bold text-yellow-400 mb-1">
                    <span class="flex items-center gap-2">
                        <i class="fa-solid fa-lungs"></i> RESP (Nafas olish)
                        <span class="text-[10px] text-slate-500 font-normal">Impedance Pneumography</span>
                    </span>
                    <span id="resp-status" class="text-yellow-400">Ritmli nafas</span>
                </div>
                <canvas id="respCanvas" class="w-full flex-1 rounded bg-black/40"></canvas>
            </div>

            <div class="absolute inset-0 pointer-events-none opacity-5 bg-[radial-gradient(#22c55e_1px,transparent_1px)] [background-size:16px_16px]"></div>
        </div>

        <!-- RIGHT 1 COLUMN: LARGE VITAL NUMERIC BOXES -->
        <div class="grid grid-cols-2 lg:grid-cols-1 gap-2.5">
            
            <!-- HR / PULSE (Green) -->
            <div class="bg-[#080b14] border border-green rounded-xl p-3 flex flex-col justify-between shadow-md relative overflow-hidden">
                <div class="flex justify-between items-center text-emerald-400 font-bold text-sm">
                    <span><i class="fa-solid fa-heart-pulse mr-1"></i> HR / PULS</span>
                    <span class="text-xs text-slate-500">bpm</span>
                </div>
                <div class="flex items-baseline justify-between my-1">
                    <span id="num-hr" class="mono text-5xl lg:text-6xl font-bold text-emerald-400 glow-green">75</span>
                    <div class="text-right text-[11px] text-emerald-600/80 leading-tight">
                        <div>YUQ: 120</div>
                        <div>PAS: 50</div>
                    </div>
                </div>
                <div class="flex justify-between text-[10px] text-slate-400 border-t border-slate-800 pt-1">
                    <span>Kompressiyalar: <span id="num-count" class="text-emerald-400 font-bold">0</span></span>
                    <span>Puls: Normal</span>
                </div>
            </div>

            <!-- SpO2 (Cyan) -->
            <div class="bg-[#080b14] border border-cyan rounded-xl p-3 flex flex-col justify-between shadow-md relative overflow-hidden">
                <div class="flex justify-between items-center text-cyan-400 font-bold text-sm">
                    <span><i class="fa-solid fa-droplet mr-1"></i> SpO2 (Kislorod)</span>
                    <span class="text-xs text-slate-500">%</span>
                </div>
                <div class="flex items-baseline justify-between my-1">
                    <span id="num-spo2" class="mono text-5xl lg:text-6xl font-bold text-cyan-400 glow-cyan">98</span>
                    <div class="text-right text-[11px] text-cyan-600/80 leading-tight">
                        <div>PI: 4.2%</div>
                        <div>PAS: 90%</div>
                    </div>
                </div>
                <div class="flex justify-between text-[10px] text-slate-400 border-t border-slate-800 pt-1">
                    <span>Puls: <span id="num-pr">75</span></span>
                    <span>Signal: Kuchli</span>
                </div>
            </div>

            <!-- NIBP (Blood Pressure - White) -->
            <div class="bg-[#080b14] border border-slate-700 rounded-xl p-3 flex flex-col justify-between shadow-md relative overflow-hidden">
                <div class="flex justify-between items-center text-slate-200 font-bold text-sm">
                    <span><i class="fa-solid fa-gauge-high mr-1"></i> NIBP (Davleniya)</span>
                    <span class="text-xs text-slate-500">mmHg</span>
                </div>
                <div class="flex items-baseline justify-between my-1">
                    <div>
                        <span id="num-sys" class="mono text-3xl lg:text-4xl font-bold text-white glow-white">120</span>
                        <span class="text-xl text-slate-400">/</span>
                        <span id="num-dia" class="mono text-3xl lg:text-4xl font-bold text-white glow-white">80</span>
                    </div>
                    <div class="text-right text-xs text-slate-400">
                        (<span id="num-map" class="text-emerald-400 font-bold">93</span>)
                    </div>
                </div>
                <div class="flex justify-between text-[10px] text-slate-400 border-t border-slate-800 pt-1">
                    <span>Avto: 15min</span>
                    <span>Oxirgi: 2 min oldin</span>
                </div>
            </div>

            <!-- RR & TEMP (Yellow & Purple) -->
            <div class="grid grid-cols-2 gap-2">
                <div class="bg-[#080b14] border border-yellow rounded-xl p-2.5 flex flex-col justify-between">
                    <div class="flex justify-between items-center text-yellow-400 font-bold text-xs">
                        <span><i class="fa-solid fa-lungs mr-1"></i> RR</span>
                        <span class="text-[10px] text-slate-500">rpm</span>
                    </div>
                    <span id="num-rr" class="mono text-3xl lg:text-4xl font-bold text-yellow-400 glow-yellow my-1">16</span>
                    <div class="text-[10px] text-slate-400 border-t border-slate-800 pt-0.5">Apnoe: 20s</div>
                </div>

                <div class="bg-[#080b14] border border-purple-500/30 rounded-xl p-2.5 flex flex-col justify-between">
                    <div class="flex justify-between items-center text-purple-400 font-bold text-xs">
                        <span><i class="fa-solid fa-temperature-three-quarters mr-1"></i> TEMP</span>
                        <span class="text-[10px] text-slate-500">°C</span>
                    </div>
                    <span id="num-temp" class="mono text-3xl lg:text-4xl font-bold text-purple-400 my-1">36.6</span>
                    <div class="text-[10px] text-slate-400 border-t border-slate-800 pt-0.5">T1 Teri</div>
                </div>
            </div>

        </div>
    </div>

    <!-- INSTRUCTOR SIMULATION CONTROL PANEL -->
    <footer class="bg-[#0c101c] border border-slate-800 rounded-xl p-3 shadow-xl">
        <div class="flex items-center justify-between mb-2">
            <h3 class="text-sm font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                <i class="fa-solid fa-sliders text-indigo-400"></i> O'qituvchi Boshqaruv Paneli va Ssenariylar
            </h3>
            <span class="text-xs text-slate-500">ESP32 UART yoki dastur orqali simulyatsiyani boshqaring</span>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
            <button onclick="setScenario('normal')" class="px-3 py-2 rounded-lg bg-emerald-950 hover:bg-emerald-900 border border-emerald-600 text-emerald-300 font-bold text-xs flex flex-col items-center justify-center gap-1 transition active:scale-95 shadow">
                <i class="fa-solid fa-heart text-base text-emerald-400"></i>
                <span>🟢 Normal (Barqaror)</span>
            </button>

            <button onclick="setScenario('dying')" class="px-3 py-2 rounded-lg bg-red-950 hover:bg-red-900 border border-red-500 text-red-300 font-bold text-xs flex flex-col items-center justify-center gap-1 transition active:scale-95 shadow alarm-blink">
                <i class="fa-solid fa-skull-crossbones text-base text-red-500"></i>
                <span>🚨 Bemorni yo'qotyapmiz!</span>
            </button>

            <button onclick="setScenario('attack')" class="px-3 py-2 rounded-lg bg-orange-950 hover:bg-orange-900 border border-orange-500 text-orange-300 font-bold text-xs flex flex-col items-center justify-center gap-1 transition active:scale-95 shadow">
                <i class="fa-solid fa-bolt-lightning text-base text-orange-400"></i>
                <span>⚡ Xuruj boshlanyapti!</span>
            </button>

            <button onclick="setScenario('hypoxia')" class="px-3 py-2 rounded-lg bg-cyan-950 hover:bg-cyan-900 border border-cyan-500 text-cyan-300 font-bold text-xs flex flex-col items-center justify-center gap-1 transition active:scale-95 shadow">
                <i class="fa-solid fa-lungs text-base text-cyan-400"></i>
                <span>🫁 Gipoksiya / Bo'g'ilish</span>
            </button>

            <button onclick="setScenario('shock')" class="px-3 py-2 rounded-lg bg-rose-950 hover:bg-rose-900 border border-rose-500 text-rose-300 font-bold text-xs flex flex-col items-center justify-center gap-1 transition active:scale-95 shadow">
                <i class="fa-solid fa-droplet-slash text-base text-rose-400"></i>
                <span>🩸 Shok (Qon ketishi)</span>
            </button>

            <button onclick="defibrillateShock()" class="px-3 py-2 rounded-lg bg-indigo-950 hover:bg-indigo-900 border border-indigo-500 text-indigo-300 font-bold text-xs flex flex-col items-center justify-center gap-1 transition active:scale-95 shadow">
                <i class="fa-solid fa-wand-magic-sparkles text-base text-indigo-400"></i>
                <span>💉 Defibrilyator / CPR</span>
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
        let soundEnabled = true;
        let asystoleOsc = null;
        let lastBeatTime = 0;

        function initAudio() {
            if (!audioCtx) {
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (audioCtx.state === 'suspended') {
                audioCtx.resume();
            }
        }

        function toggleAudio() {
            initAudio();
            soundEnabled = !soundEnabled;
            const icon = document.getElementById("audio-icon");
            const text = document.getElementById("audio-text");
            if (soundEnabled) {
                icon.className = "fa-solid fa-volume-high text-emerald-400";
                text.innerText = "Ovoz: Yoniq";
            } else {
                icon.className = "fa-solid fa-volume-xmark text-red-400";
                text.innerText = "Ovoz: O'chiq";
                stopAsystoleTone();
            }
        }

        function playQRSBeep() {
            if (!soundEnabled || current.hr <= 0) return;
            initAudio();
            try {
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                const minFreq = 400;
                const maxFreq = 950;
                const freq = minFreq + ((Math.max(50, current.spo2) - 50) / 50) * (maxFreq - minFreq);
                osc.type = "sine";
                osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
                gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 0.08);
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + 0.08);
            } catch (e) {}
        }

        function startAsystoleTone() {
            if (!soundEnabled || asystoleOsc) return;
            initAudio();
            try {
                asystoleOsc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                asystoleOsc.type = "sine";
                asystoleOsc.frequency.setValueAtTime(800, audioCtx.currentTime);
                gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
                asystoleOsc.connect(gain);
                gain.connect(audioCtx.destination);
                asystoleOsc.start();
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

        // Dynamic CPR Stroke analysis in frontend
        let cprState = "idle";
        let peakForce = 0;
        let lastStrokeTime = 0;
        let cprCount = 0;
        let currentBpm = 0;
        let lastDepthOk = false;
        let lastRecoilOk = true;
        let lastRateOk = false;

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

        // ==================== PROCESS INCOMING ESP32 JSON ====================
        function handleHardwareData(data) {
            // Support all JSON variations: force / f_curr / force_kg
            const fCurr = parseFloat(data.force !== undefined ? data.force : (data.f_curr !== undefined ? data.f_curr : (data.force_kg || 0)));
            const posBtn = (data.pos_btn === 1 || data.pos_btn === true || data.pos_ok === true || data.pos_valid === true);
            const injBtn = (data.inj_btn === 1 || data.inj_btn === true || data.inj_ok === true);
            const lungP = parseFloat(data.lung_p || 0);
            const stomachP = parseFloat(data.stomach_p || 0);

            // Compute CPR in real time
            processCPRStroke(fCurr);

            const bpm = data.bpm !== undefined ? parseInt(data.bpm) : currentBpm;
            const count = data.count !== undefined ? parseInt(data.count) : cprCount;
            const dOk = data.d_ok !== undefined ? Boolean(data.d_ok) : lastDepthOk;
            const rOk = data.r_ok !== undefined ? Boolean(data.r_ok) : lastRecoilOk;
            const bpmOk = data.bpm_ok !== undefined ? Boolean(data.bpm_ok) : lastRateOk;
            const posOk = posBtn;
            const injOk = injBtn;

            // 1. Update Force Bar
            document.getElementById("cpr-force-val").innerText = `${fCurr.toFixed(1)} kg`;
            const forcePct = Math.min(100, (fCurr / 60.0) * 100);
            const forceBar = document.getElementById("cpr-force-bar");
            forceBar.style.width = `${forcePct}%`;

            if (fCurr >= 38.0 && fCurr <= 55.0) {
                forceBar.className = "bg-emerald-500 h-full rounded-full transition-all duration-75";
                document.getElementById("cpr-force-val").className = "mono text-emerald-400 font-bold text-sm";
            } else if (fCurr > 55.0) {
                forceBar.className = "bg-rose-500 h-full rounded-full transition-all duration-75";
                document.getElementById("cpr-force-val").className = "mono text-rose-400 font-bold text-sm";
            } else if (fCurr > 8.0) {
                forceBar.className = "bg-yellow-500 h-full rounded-full transition-all duration-75";
                document.getElementById("cpr-force-val").className = "mono text-yellow-400 font-bold text-sm";
            } else {
                forceBar.className = "bg-slate-700 h-full rounded-full transition-all duration-75";
                document.getElementById("cpr-force-val").className = "mono text-slate-400 font-bold text-sm";
            }

            // 2. Update Quality Badges
            document.getElementById("cpr-count-badge").innerText = `${count} marta`;
            document.getElementById("num-count").innerText = count;

            updateQualityBadge("badge-d", "Chuqurlik", dOk, fCurr > 5);
            updateQualityBadge("badge-r", "Bo'shatish", rOk, fCurr > 5);
            updateQualityBadge("badge-bpm", "Tezlik", bpmOk, bpm > 0);
            updateQualityBadge("badge-pos", "Joyi", posOk, true);

            // 3. CPR BPM
            document.getElementById("cpr-bpm-val").innerText = `${bpm} /min`;
            const rateBadge = document.getElementById("cpr-rate-badge");
            if (bpm > 0) {
                if (bpm >= 100 && bpm <= 120) {
                    rateBadge.className = "px-2 py-1 rounded text-xs font-bold bg-emerald-950 text-emerald-300 border border-emerald-600 text-center";
                    rateBadge.innerText = "✅ Tezlik: A'LO (100-120)";
                } else if (bpm < 100) {
                    rateBadge.className = "px-2 py-1 rounded text-xs font-bold bg-yellow-950 text-yellow-300 border border-yellow-600 text-center";
                    rateBadge.innerText = "⚠️ Tezroq bosing (<100)";
                } else {
                    rateBadge.className = "px-2 py-1 rounded text-xs font-bold bg-orange-950 text-orange-300 border border-orange-600 text-center";
                    rateBadge.innerText = "⚠️ Juda tez (>120)";
                }
            } else {
                rateBadge.className = "px-2 py-1 rounded text-xs font-bold bg-slate-900 text-slate-400 border border-slate-800 text-center";
                rateBadge.innerText = "Standart: 100 - 120 /min";
            }

            // 4. Lung Pressure (Max: 3.5 kPa)
            document.getElementById("lung-p-val").innerText = `${lungP.toFixed(1)} kPa`;
            const lungPct = Math.min(100, (lungP / 3.5) * 100);
            document.getElementById("lung-p-bar").style.width = `${lungPct}%`;
            if (lungP >= 2.0 && lungP <= 3.0) {
                document.getElementById("lung-status-text").innerText = "✅ TO'G'RI VA YETARLI NAFAS (20-30 cmH2O)";
                document.getElementById("lung-status-text").className = "text-[10px] text-emerald-400 mt-0.5 font-bold glow-green";
                if (current.spo2 < 99) {
                    current.spo2 = Math.min(100, current.spo2 + 1);
                    updateNumericsUI();
                }
            } else if (lungP > 3.0) {
                document.getElementById("lung-status-text").innerText = "🚨 JUDA KUCHLI! BAROTRAVMA XAVFI (>3.0 kPa)";
                document.getElementById("lung-status-text").className = "text-[10px] text-rose-400 mt-0.5 font-bold glow-red";
            } else if (lungP > 0.6) {
                document.getElementById("lung-status-text").innerText = "⚠️ Qattiqroq siqing (<20 cmH2O)";
                document.getElementById("lung-status-text").className = "text-[10px] text-yellow-400 mt-0.5 font-bold";
            } else {
                document.getElementById("lung-status-text").innerText = "O'pka: Normal";
                document.getElementById("lung-status-text").className = "text-[10px] text-cyan-400 mt-0.5";
            }

            // 5. Stomach Pressure
            document.getElementById("stomach-p-val").innerText = `${stomachP.toFixed(1)} kPa`;
            const stomachAlert = document.getElementById("stomach-alert");
            if (stomachP > 0.8) {
                stomachAlert.className = "px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-950 text-rose-300 border border-rose-500 alarm-blink";
                stomachAlert.innerHTML = "⚠️ HAVO OSHQOZONDA!";
            } else {
                stomachAlert.className = "px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-900 text-slate-400 border border-slate-800 text-center";
                stomachAlert.innerHTML = "Oshqozon toza";
            }

            // 6. Injection (Touch Sensor Ukol)
            const injBanner = document.getElementById("inj-banner");
            const injBadge = document.getElementById("inj-badge-small");
            if (injOk) {
                injBanner.classList.remove("hidden");
                injBadge.innerText = "💉 UKOL QILINDI!";
                injBadge.className = "text-[10px] text-purple-300 font-bold mt-0.5 text-center alarm-blink";
                
                // Flash overlay
                const flash = document.getElementById("flash-overlay");
                flash.classList.add("inj-active");
                setTimeout(() => flash.classList.remove("inj-active"), 1200);

                // If patient was dying, injection helps rescue patient!
                if (current.hr <= 30) {
                    setTimeout(() => {
                        setScenario("normal");
                    }, 1500);
                }
            } else {
                injBanner.classList.add("hidden");
                injBadge.innerText = "Ukol: Kutilmoqda (Touch 4)";
                injBadge.className = "text-[10px] text-purple-400 font-semibold mt-0.5 text-center";
            }

            // Auto-recovery after 10 high-quality compressions
            if (current.hr <= 20 && count >= 10 && dOk && posOk && bpmOk) {
                setScenario("normal");
            }
        }

        function updateQualityBadge(id, label, isOk, isActive) {
            const el = document.getElementById(id);
            if (!isActive) {
                el.className = "px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400 text-center font-bold";
                el.innerText = `${label}: -`;
            } else if (isOk) {
                el.className = "px-1.5 py-0.5 rounded bg-emerald-950 border border-emerald-700 text-emerald-300 text-center font-bold";
                el.innerText = `${label}: ✅`;
            } else {
                el.className = "px-1.5 py-0.5 rounded bg-rose-950 border border-rose-700 text-rose-300 text-center font-bold";
                el.innerText = `${label}: ❌`;
            }
        }

        function connectTelemetryWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;
            const ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                document.getElementById("hw-dot").className = "w-2 h-2 rounded-full bg-emerald-500";
                document.getElementById("hw-text").innerText = "ESP32 UART: Jonli oqim";
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleHardwareData(data);
                } catch(e) {}
            };

            ws.onclose = () => {
                document.getElementById("hw-dot").className = "w-2 h-2 rounded-full bg-amber-500";
                document.getElementById("hw-text").innerText = "ESP32 UART: Qayta ulanmoqda";
                setTimeout(connectTelemetryWebSocket, 1500);
            };
        }

        // ==================== DIRECT WEB SERIAL API (ONE-CLICK USB SYNC) ====================
        let webSerialPort = null;
        let webSerialWriter = null;

        async function connectDirectWebSerial() {
            if (!("serial" in navigator)) {
                alert("Brauzeringiz Web Serial API-ni qo'llab-quvvatlamaydi. Iltimos Google Chrome yoki Microsoft Edge brauzeridan foydalaning!");
                return;
            }
            try {
                webSerialPort = await navigator.serial.requestPort();
                await webSerialPort.open({ baudRate: 115200 });
                const textEncoder = new TextEncoderStream();
                const writableStreamClosed = textEncoder.readable.pipeTo(webSerialPort.writable);
                webSerialWriter = textEncoder.writable.getWriter();

                document.getElementById("web-serial-text").innerText = "✅ Maniken Ulandi (USB)";
                document.getElementById("btn-web-serial").className = "px-2.5 py-1 rounded bg-emerald-900 text-emerald-200 border border-emerald-500 flex items-center gap-1.5 font-bold shadow";

                sendWebSerialCommand("BPM:75\n");
            } catch(err) {
                console.error("Web Serial Ulanish xatosi:", err);
            }
        }

        async function sendWebSerialCommand(cmd) {
            if (webSerialWriter) {
                try {
                    await webSerialWriter.write(cmd);
                } catch(e) {}
            }
        }

        function setScenario(type) {
            initAudio();
            totalSteps = 150;
            transitionSteps = totalSteps;

            if (type === "normal") {
                target = { hr: 75, spo2: 98, sys: 120, dia: 80, rr: 16, temp: 36.6, mode: "normal", rhythm: "sinus" };
                updateBanner("🟢 STATUS: BARQAROR (NORMAL)", "bg-emerald-950/80 text-emerald-400 border-emerald-700");
                stopAsystoleTone();
                sendWebSerialCommand("NORMAL\n");
            } else if (type === "dying") {
                target = { hr: 0, spo2: 0, sys: 0, dia: 0, rr: 0, temp: 35.1, mode: "dying", rhythm: "asystole" };
                updateBanner("🚨 DIQQAT: BEMORNI YO'QOTYAPMIZ! (KOLLAPS / ASISTOLIYA)", "bg-red-950 text-red-400 border-red-500 alarm-blink");
                sendWebSerialCommand("DYING\n");
            } else if (type === "attack") {
                target = { hr: 185, spo2: 88, sys: 210, dia: 125, rr: 34, temp: 37.4, mode: "attack", rhythm: "vtach" };
                updateBanner("⚡ XURUJ: O'TKIR TAXIKARDIYA VA GIPERTONIK KRIZ!", "bg-orange-950 text-orange-400 border-orange-500 alarm-blink");
                stopAsystoleTone();
                sendWebSerialCommand("ATTACK\n");
            } else if (type === "hypoxia") {
                target = { hr: 135, spo2: 74, sys: 135, dia: 90, rr: 38, temp: 36.8, mode: "hypoxia", rhythm: "sinus" };
                updateBanner("🫁 GIPOKSIYA: BO'G'ILISH VA KISLOROD YETISHMOVCHILIGI!", "bg-cyan-950 text-cyan-400 border-cyan-500 alarm-blink");
                stopAsystoleTone();
                sendWebSerialCommand("BPM:135\n");
            } else if (type === "shock") {
                target = { hr: 145, spo2: 89, sys: 65, dia: 35, rr: 28, temp: 35.8, mode: "shock", rhythm: "sinus" };
                updateBanner("🩸 SHOK: QON BOSIMINING KESKIN TUSHISHI!", "bg-rose-950 text-rose-400 border-rose-500 alarm-blink");
                stopAsystoleTone();
                sendWebSerialCommand("BPM:145\n");
            }
        }

        function defibrillateShock() {
            initAudio();
            sendWebSerialCommand("SHOCK\n");
            const flash = document.getElementById("flash-overlay");
            flash.classList.add("shock-active");
            setTimeout(() => flash.classList.remove("shock-active"), 600);

            try {
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = "sawtooth";
                osc.frequency.setValueAtTime(150, audioCtx.currentTime);
                osc.frequency.exponentialRampToValueAtTime(40, audioCtx.currentTime + 0.3);
                gain.gain.setValueAtTime(0.4, audioCtx.currentTime);
                gain.gain.linearRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + 0.3);
            } catch(e) {}

            setTimeout(() => {
                setScenario("normal");
            }, 700);
        }

        function updateBanner(text, classes) {
            const b = document.getElementById("alarm-banner");
            b.className = `px-4 py-1 rounded-md text-xs font-bold uppercase tracking-widest border ${classes}`;
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

            if (hrVal <= 0) {
                document.getElementById("ecg-rhythm-name").innerText = "ASYSTOLIYA (Yurak to'xtadi)";
                document.getElementById("ecg-rhythm-name").className = "text-red-500 font-bold alarm-blink";
            } else if (hrVal > 150) {
                document.getElementById("ecg-rhythm-name").innerText = "Ventrikulyar Taxikardiya";
                document.getElementById("ecg-rhythm-name").className = "text-orange-400 font-bold";
            } else {
                document.getElementById("ecg-rhythm-name").innerText = "Sinus Ritmi";
                document.getElementById("ecg-rhythm-name").className = "text-emerald-400";
            }
        }

        // Canvas Oscilloscopes
        const ecgCanvas = document.getElementById("ecgCanvas");
        const plethCanvas = document.getElementById("plethCanvas");
        const respCanvas = document.getElementById("respCanvas");

        const ecgCtx = ecgCanvas.getContext("2d");
        const plethCtx = plethCanvas.getContext("2d");
        const respCtx = respCanvas.getContext("2d");

        function resizeCanvases() {
            [ecgCanvas, plethCanvas, respCanvas].forEach(c => {
                c.width = c.clientWidth * window.devicePixelRatio || c.clientWidth;
                c.height = c.clientHeight * window.devicePixelRatio || c.clientHeight;
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

            const sweepSpeed = 2.5 * (window.devicePixelRatio || 1);
            const eraseWidth = 25 * (window.devicePixelRatio || 1);

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

            // 1. ECG
            const nextEcgX = (ecgX + sweepSpeed) % w;
            ecgCtx.fillStyle = "#000000";
            ecgCtx.fillRect(nextEcgX, 0, eraseWidth, hEcg);

            const ecgVal = getECGY(ecgPhase, hr);
            const midEcg = hEcg / 2;
            const curEcgY = midEcg - (ecgVal * (hEcg * 0.42));

            if (lastEcgY !== null && nextEcgX > ecgX) {
                ecgCtx.strokeStyle = "#22c55e";
                ecgCtx.lineWidth = 2.5 * (window.devicePixelRatio || 1);
                ecgCtx.shadowColor = "#22c55e";
                ecgCtx.shadowBlur = 6;
                ecgCtx.beginPath();
                ecgCtx.moveTo(ecgX, lastEcgY);
                ecgCtx.lineTo(nextEcgX, curEcgY);
                ecgCtx.stroke();
            }
            ecgX = nextEcgX;
            lastEcgY = curEcgY;

            // 2. SpO2
            const nextPlethX = (plethX + sweepSpeed) % w;
            plethCtx.fillStyle = "#000000";
            plethCtx.fillRect(nextPlethX, 0, eraseWidth, hPleth);

            const plethVal = getPlethY(plethPhase, hr, spo2);
            const curPlethY = hPleth - 10 - (plethVal * (hPleth * 0.8));

            if (lastPlethY !== null && nextPlethX > plethX) {
                plethCtx.strokeStyle = "#06b6d4";
                plethCtx.lineWidth = 2.2 * (window.devicePixelRatio || 1);
                plethCtx.shadowColor = "#06b6d4";
                plethCtx.shadowBlur = 5;
                plethCtx.beginPath();
                plethCtx.moveTo(plethX, lastPlethY);
                plethCtx.lineTo(nextPlethX, curPlethY);
                plethCtx.stroke();
            }
            plethX = nextPlethX;
            lastPlethY = curPlethY;

            // 3. RESP
            const nextRespX = (respX + sweepSpeed) % w;
            respCtx.fillStyle = "#000000";
            respCtx.fillRect(nextRespX, 0, eraseWidth, hResp);

            const respVal = getRespY(respPhase, rr);
            const midResp = hResp / 2;
            const curRespY = midResp - (respVal * (hResp * 0.38));

            if (lastRespY !== null && nextRespX > respX) {
                respCtx.strokeStyle = "#eab308";
                respCtx.lineWidth = 2.2 * (window.devicePixelRatio || 1);
                respCtx.shadowColor = "#eab308";
                respCtx.shadowBlur = 5;
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

        window.onload = () => {
            updateNumericsUI();
            connectTelemetryWebSocket();
            requestAnimationFrame(animate);
        };
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_monitor():
    return HTMLResponse(content=HTML_CONTENT)

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
