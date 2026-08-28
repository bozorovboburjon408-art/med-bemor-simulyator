import os
import sys
import json
import socket
import asyncio
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

app = FastAPI(title="General Doctor GD/H126 Manikin Tester Console")

active_websockets: List[WebSocket] = []

latest_data = {
    "force": 0.0,
    "lung_p": 0.0,
    "stomach_p": 0.0,
    "pos_btn": 0,
    "inj_btn": 0,
    "count": 0,
    "bpm": 0
}

HTML_CONTENT = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GD/H126 Manikin Pult Simulyatori (General Doctor)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@400;600;800&display=swap');

        body {
            background-color: #1a1e29;
            font-family: 'Inter', sans-serif;
            user-select: none;
        }

        .mono {
            font-family: 'Share Tech Mono', monospace;
        }

        /* Medical Device Plastic Casing Texture */
        .casing {
            background: linear-gradient(145deg, #e4e1d8, #d0ccbf);
            box-shadow: 0 20px 40px rgba(0,0,0,0.6), inset 0 2px 4px rgba(255,255,255,0.8), inset 0 -2px 4px rgba(0,0,0,0.2);
            border: 4px solid #b8b3a5;
        }

        .panel-inset {
            background: #e9e6dd;
            box-shadow: inset 0 2px 6px rgba(0,0,0,0.15), 0 1px 0 rgba(255,255,255,0.9);
            border: 1.5px solid #bab4a3;
        }

        /* Segmented LED Bar Styles */
        .led-segment {
            transition: all 0.05s ease-out;
            border-radius: 1.5px;
            margin-bottom: 2px;
            height: 7px;
            background-color: #3b1b1b;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.8);
        }

        .led-yellow-on {
            background-color: #facc15 !important;
            box-shadow: 0 0 10px #facc15, inset 0 0 4px #ffffff !important;
        }

        .led-green-on {
            background-color: #22c55e !important;
            box-shadow: 0 0 10px #22c55e, inset 0 0 4px #ffffff !important;
        }

        .led-red-on {
            background-color: #ef4444 !important;
            box-shadow: 0 0 10px #ef4444, inset 0 0 4px #ffffff !important;
        }

        /* Anatomical LED Indicator Lights */
        .led-indicator {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: #451a1a;
            border: 1.5px solid #2b1111;
            transition: all 0.08s ease;
        }

        .led-pos-active {
            background: #22c55e !important;
            box-shadow: 0 0 16px #22c55e, 0 0 30px #22c55e, inset 0 0 6px #ffffff !important;
            border-color: #15803d !important;
            animation: pulseLed 0.4s infinite alternate;
        }

        .led-stomach-active {
            background: #ef4444 !important;
            box-shadow: 0 0 16px #ef4444, 0 0 30px #ef4444, inset 0 0 6px #ffffff !important;
            border-color: #b91c1c !important;
            animation: blinkFast 0.25s infinite;
        }

        .led-pulse-active {
            background: #38bdf8 !important;
            box-shadow: 0 0 14px #38bdf8, inset 0 0 4px #ffffff !important;
            border-color: #0284c7 !important;
        }

        @keyframes pulseLed {
            0% { transform: scale(1); filter: brightness(1); }
            100% { transform: scale(1.15); filter: brightness(1.3); }
        }

        @keyframes blinkFast {
            0%, 100% { opacity: 1; filter: brightness(1.4); }
            50% { opacity: 0.2; filter: brightness(0.6); }
        }

        /* Power Rocker Switch */
        .rocker-switch {
            width: 44px;
            height: 64px;
            background: #222;
            border-radius: 4px;
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.8), 0 1px 2px rgba(255,255,255,0.5);
            padding: 3px;
            cursor: pointer;
        }

        .rocker-knob {
            width: 100%;
            height: 50%;
            background: linear-gradient(to bottom, #eeeeee, #cccccc);
            border-radius: 2px;
            box-shadow: 0 3px 6px rgba(0,0,0,0.4);
            transition: all 0.15s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: bold;
            color: #333;
        }

        .rocker-on .rocker-knob {
            transform: translateY(100%);
            background: linear-gradient(to top, #ffffff, #e0e0e0);
            box-shadow: 0 -3px 6px rgba(0,0,0,0.3);
        }

        /* Beveled buttons */
        .btn-beveled {
            background: linear-gradient(145deg, #d8d4c7, #c2bdae);
            border: 2px solid #a8a293;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2), inset 0 1px 2px rgba(255,255,255,0.8);
        }
        .btn-beveled:active {
            box-shadow: inset 0 3px 5px rgba(0,0,0,0.4);
            transform: translateY(1px);
        }

        /* Pointer Dashed Lines */
        .pointer-line {
            stroke: #222222;
            stroke-width: 1.8;
            stroke-dasharray: 4, 3;
        }
    </style>
</head>
<body class="min-h-screen flex flex-col items-center justify-center p-3 sm:p-6">

    <!-- Top Connection & Navigation Bar -->
    <div class="w-full max-w-2xl flex items-center justify-between mb-3 text-slate-300 text-xs">
        <div class="flex items-center gap-2">
            <span id="conn-dot" class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
            <span id="conn-status" class="font-semibold">ESP32 UART: Kutish holatida</span>
        </div>
        <div class="flex items-center gap-3">
            <a href="/monitor" target="_blank" class="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-lg transition shadow">
                <i class="fa-solid fa-heart-pulse mr-1"></i> ICU Monitor
            </a>
            <a href="/" target="_blank" class="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg transition shadow">
                <i class="fa-solid fa-user-doctor mr-1"></i> AI Bemor
            </a>
        </div>
    </div>

    <!-- MAIN CONSOLE DEVICE (GD/H126 GENERAL DOCTOR) -->
    <div class="w-full max-w-[500px] casing rounded-3xl p-4 sm:p-5 flex flex-col">
        
        <!-- TOP PANEL (Anatomical Diagram & Dual LED Bars) -->
        <div class="panel-inset rounded-2xl p-4 relative overflow-hidden flex flex-col border">
            
            <!-- Header Labels -->
            <div class="flex items-start justify-between mb-2">
                <div class="leading-tight">
                    <div class="font-bold text-[13px] text-slate-800 tracking-tight">GD/H126 High Intelligent</div>
                    <div class="text-[11px] text-slate-600 font-semibold">Comprehensive Nursing</div>
                    <div class="text-[11px] text-slate-600 font-semibold">Manikin</div>
                </div>
                <div class="text-right">
                    <div class="text-base font-black italic tracking-wide text-slate-800">
                        General <span class="text-red-600 font-black not-italic"><i class="fa-solid fa-plus text-xs align-middle"></i> Doctor</span><span class="text-[10px] align-super">®</span>
                    </div>
                </div>
            </div>

            <!-- MAIN DISPLAY AREA (LEFT BAR | SVG MANIKIN | RIGHT BAR) -->
            <div class="flex items-stretch justify-between relative mt-2 mb-2 h-[340px]">
                
                <!-- LEFT LED BAR: KO'KRAK KUCHI (CPR FORCE) -->
                <div class="w-12 flex flex-col items-center justify-between">
                    <div class="text-[10px] font-extrabold text-slate-700 tracking-tighter text-center uppercase leading-none">
                        KUCH<br><span id="force-val-text" class="mono font-bold text-red-700 text-xs">0.0 kg</span>
                    </div>
                    
                    <!-- LED Bar Graph Enclosure -->
                    <div class="w-7 h-[265px] bg-[#1a0808] border-2 border-[#572727] rounded-md p-1 flex flex-col-reverse justify-between shadow-inner relative" id="force-bar-container">
                        <!-- 30 LED Segments generated dynamically by JS -->
                    </div>

                    <div class="text-[9px] font-bold text-slate-600">MASSAJ</div>
                </div>

                <!-- CENTER: ANATOMICAL MANIKIN OUTLINE & LED DOTS -->
                <div class="flex-1 relative flex items-center justify-center">
                    
                    <!-- SVG Vector of Torso and Dotted Lines -->
                    <svg viewBox="0 0 300 360" class="w-full h-full" xmlns="http://www.w3.org/2000/svg">
                        
                        <!-- Dotted Pointer Line: Chest LED -> Left Bar -->
                        <line x1="150" y1="190" x2="35" y2="120" class="pointer-line" />

                        <!-- Dotted Pointer Line: Airway/Mouth -> Right Bar -->
                        <line x1="150" y1="95" x2="265" y2="100" class="pointer-line" />

                        <!-- Head & Hair Outline -->
                        <path d="M110,85 C100,50 120,20 150,20 C180,20 200,50 190,85 C185,105 175,115 150,115 C125,115 115,105 110,85 Z" fill="none" stroke="#222" stroke-width="2.5" />
                        <!-- Hair outline -->
                        <path d="M106,65 C100,40 120,15 150,15 C180,15 200,40 194,65 C185,45 170,35 150,35 C130,35 115,45 106,65 Z" fill="#222" />
                        
                        <!-- Face Features (Eyebrows, Eyes, Nose, Mouth) -->
                        <path d="M125,58 Q135,53 143,58" fill="none" stroke="#222" stroke-width="2" />
                        <path d="M157,58 Q165,53 175,58" fill="none" stroke="#222" stroke-width="2" />
                        <path d="M127,65 Q135,72 143,65" fill="none" stroke="#222" stroke-width="2" />
                        <path d="M157,65 Q165,72 173,65" fill="none" stroke="#222" stroke-width="2" />
                        <path d="M150,68 L147,78 L153,78" fill="none" stroke="#222" stroke-width="1.8" />
                        <path d="M138,90 Q150,96 162,90 Q150,94 138,90 Z" fill="#222" />

                        <!-- Neck Outline -->
                        <path d="M135,110 L133,130" stroke="#222" stroke-width="2.5" fill="none" />
                        <path d="M165,110 L167,130" stroke="#222" stroke-width="2.5" fill="none" />
                        <path d="M136,122 Q150,126 164,122" stroke="#222" stroke-width="2" fill="none" />
                        <path d="M138,135 Q150,140 162,135" stroke="#222" stroke-width="2" fill="none" />

                        <!-- Shoulders, Breasts, Ribs, Torso Body Outline -->
                        <path d="M133,130 C100,135 60,150 50,175" stroke="#222" stroke-width="3" fill="none" />
                        <path d="M167,130 C200,135 240,150 250,175" stroke="#222" stroke-width="3" fill="none" />

                        <!-- Torso Outer Sides and Chest Contours -->
                        <path d="M50,175 C45,210 55,270 70,350" stroke="#222" stroke-width="2.5" fill="none" />
                        <path d="M250,175 C255,210 245,270 230,350" stroke="#222" stroke-width="2.5" fill="none" />

                        <!-- Breasts Contour -->
                        <path d="M70,170 C60,195 65,225 95,225 C125,225 130,205 130,190" stroke="#222" stroke-width="2.5" fill="none" />
                        <path d="M230,170 C240,195 235,225 205,225 C175,225 170,205 170,190" stroke="#222" stroke-width="2.5" fill="none" />

                        <!-- Rib Arch (Subcostal Angle) -->
                        <path d="M110,265 C135,240 150,225 150,220 C150,225 165,240 190,265" stroke="#222" stroke-width="2.5" fill="none" />
                    </svg>

                    <!-- PHYSICAL LED INDICATORS MOUNTED PRECISELY ON THE TORSO -->

                    <!-- 1. Airway / Throat LED (Nafas / Puls) -->
                    <div class="absolute top-[102px] left-[50%] -translate-x-1/2 flex flex-col items-center">
                        <div id="led-airway" class="led-indicator"></div>
                    </div>

                    <!-- 2. Central Hand Placement LED (Sternum Qo'l Nuqtasi - Pin 13) -->
                    <div class="absolute top-[166px] left-[50%] -translate-x-1/2 flex flex-col items-center cursor-pointer" onclick="toggleSimPos()">
                        <div id="led-position" class="led-indicator"></div>
                        <span id="pos-status-label" class="text-[8px] font-black text-slate-700 mt-1 uppercase tracking-tighter text-center leading-none">
                            NUQTA (Pin 13)
                        </span>
                    </div>

                    <!-- 3. Stomach Air Hazard LED (Qorin / Oshqozon - Pin 25) -->
                    <div class="absolute bottom-[28px] left-[50%] -translate-x-1/2 flex flex-col items-center">
                        <div id="led-stomach" class="led-indicator"></div>
                        <span class="text-[8px] font-black text-slate-700 mt-0.5 uppercase tracking-tighter">
                            OSHQOZON
                        </span>
                    </div>
                </div>

                <!-- RIGHT LED BAR: O'PKA BOSIMI (VENTILATION / LUNG PRESSURE) -->
                <div class="w-12 flex flex-col items-center justify-between">
                    <div class="text-[10px] font-extrabold text-slate-700 tracking-tighter text-center uppercase leading-none">
                        O'PKA<br><span id="lung-val-text" class="mono font-bold text-red-700 text-xs">0.0 kPa</span>
                    </div>

                    <!-- LED Bar Graph Enclosure -->
                    <div class="w-7 h-[265px] bg-[#1a0808] border-2 border-[#572727] rounded-md p-1 flex flex-col-reverse justify-between shadow-inner relative" id="lung-bar-container">
                        <!-- 30 LED Segments generated dynamically by JS -->
                    </div>

                    <div class="text-[9px] font-bold text-slate-600">VENTILYATSIYA</div>
                </div>

            </div>

            <!-- Ukol va Oshqozon Ogohlantirish Popupi -->
            <div id="console-alert-box" class="hidden mt-1 p-1.5 rounded-lg bg-rose-100 border border-rose-400 text-rose-800 text-[11px] font-bold text-center flex items-center justify-center gap-2 animate-pulse">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <span id="console-alert-text">OGOHLANTIRISH</span>
            </div>

        </div>

        <!-- BOTTOM CONTROL PANEL (Power Switch | Metronome Frequency | Start / Reset) -->
        <div class="mt-3 bg-[#e2ded2] border-2 border-[#b5af9f] rounded-2xl p-3 sm:p-4 flex items-center justify-between shadow-md">
            
            <!-- 1. Power Switch -->
            <div class="flex flex-col items-center">
                <div id="power-switch" class="rocker-switch rocker-on" onclick="togglePower()">
                    <div class="rocker-knob">|</div>
                </div>
                <span class="text-[10px] font-bold text-slate-700 mt-1 uppercase">Power</span>
            </div>

            <!-- 2. Metronome & Status Indicators -->
            <div class="flex flex-col items-center gap-1">
                <div class="flex items-center gap-3">
                    <!-- LED 1: Metronome Tick -->
                    <div class="flex flex-col items-center">
                        <div id="metro-led-1" class="w-2.5 h-2.5 rounded-full bg-slate-400 transition-all duration-75"></div>
                    </div>
                    <!-- LED 2: 100 BPM Mark -->
                    <div class="flex flex-col items-center">
                        <div id="metro-led-2" class="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_8px_#22c55e]"></div>
                        <span class="text-[9px] font-bold text-slate-700 mt-0.5">100</span>
                    </div>
                    <!-- LED 3: Active Status -->
                    <div class="flex flex-col items-center">
                        <div id="metro-led-3" class="w-2.5 h-2.5 rounded-full bg-slate-400 transition-all duration-75"></div>
                    </div>
                </div>

                <!-- Frequency Button -->
                <button onclick="cycleFrequency()" class="btn-beveled px-3 py-1 rounded-lg text-xs font-bold text-slate-800 hover:bg-slate-200 transition">
                    Frequency <span id="freq-text" class="text-indigo-700 font-extrabold">(100)</span>
                </button>
            </div>

            <!-- 3. Start / Training Reset Button -->
            <div class="flex flex-col items-center">
                <button onclick="handleStartBtn()" class="btn-beveled w-16 h-12 rounded-xl text-xs font-black text-slate-800 flex items-center justify-center hover:bg-slate-200 transition shadow">
                    Start
                </button>
            </div>

        </div>

        <!-- SIMULATOR MANUAL TEST CONTROLS (Faqat test qilish uchun qulay slaydlar) -->
        <div class="mt-3 bg-slate-800/80 rounded-xl p-3 text-slate-200 text-xs flex flex-col gap-2">
            <div class="flex items-center justify-between text-[11px] font-bold text-slate-300">
                <span><i class="fa-solid fa-sliders text-indigo-400 mr-1"></i> Dasturiy Test Sinovi (Qo'lda boshqarish):</span>
                <span class="text-[10px] text-slate-400">ESP32 ulanganda avtomatik ishlaydi</span>
            </div>

            <div class="grid grid-cols-2 gap-2">
                <!-- Force Slider -->
                <div>
                    <div class="flex justify-between text-[10px] mb-0.5">
                        <span>Ko'krak Kuchi:</span>
                        <span id="sim-force-lbl" class="mono text-yellow-400 font-bold">0 kg</span>
                    </div>
                    <input type="range" id="sim-force" min="0" max="60" step="0.5" value="0" 
                           oninput="onSimInput()" class="w-full accent-emerald-500 h-1.5 bg-slate-700 rounded-lg">
                </div>

                <!-- Lung Pressure Slider -->
                <div>
                    <div class="flex justify-between text-[10px] mb-0.5">
                        <span>O'pka Bosimi:</span>
                        <span id="sim-lung-lbl" class="mono text-cyan-400 font-bold">0 kPa</span>
                    </div>
                    <input type="range" id="sim-lung" min="0" max="25" step="0.2" value="0" 
                           oninput="onSimInput()" class="w-full accent-cyan-500 h-1.5 bg-slate-700 rounded-lg">
                </div>
            </div>

            <div class="flex items-center justify-between gap-2 mt-1">
                <!-- Hand Position Button Toggle -->
                <button id="btn-toggle-pos" onclick="toggleSimPos()" class="flex-1 py-1 px-2 rounded bg-slate-700 hover:bg-slate-600 font-bold text-[11px] text-center border border-slate-600 transition">
                    🔘 Qo'l Nuqtasi: <span id="pos-btn-text" class="text-rose-400">BO'SH</span>
                </button>

                <!-- Injection Button Toggle -->
                <button id="btn-toggle-inj" onclick="triggerSimInj()" class="flex-1 py-1 px-2 rounded bg-slate-700 hover:bg-slate-600 font-bold text-[11px] text-center border border-slate-600 transition">
                    💉 Ukol: <span id="inj-btn-text" class="text-purple-400">Kiritish</span>
                </button>

                <!-- Stomach Pressure Spike -->
                <button onclick="triggerSimStomach()" class="py-1 px-2 rounded bg-rose-950/80 hover:bg-rose-900 font-bold text-[11px] text-rose-300 border border-rose-700 transition">
                    ⚠️ Oshqozon
                </button>
            </div>
        </div>

    </div>

    <!-- AUDIO ENGINE (Web Audio API Synthesizer) -->
    <script>
        let isPowerOn = true;
        let metronomeBpm = 100;
        let metronomeInterval = null;
        let audioCtx = null;

        function getAudioContext() {
            if (!audioCtx) {
                audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (audioCtx.state === 'suspended') {
                audioCtx.resume();
            }
            return audioCtx;
        }

        function playBeep(freq = 880, duration = 0.06, type = 'sine') {
            if (!isPowerOn) return;
            try {
                const ctx = getAudioContext();
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = type;
                osc.frequency.setValueAtTime(freq, ctx.currentTime);
                gain.gain.setValueAtTime(0.15, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start();
                osc.stop(ctx.currentTime + duration);
            } catch(e) {}
        }

        // Metronome Engine
        function startMetronome() {
            if (metronomeInterval) clearInterval(metronomeInterval);
            if (!isPowerOn || metronomeBpm <= 0) return;

            const intervalMs = 60000 / metronomeBpm;
            metronomeInterval = setInterval(() => {
                playBeep(900, 0.04);
                
                // Flash Metronome LED
                const led = document.getElementById("metro-led-1");
                led.className = "w-2.5 h-2.5 rounded-full bg-yellow-400 shadow-[0_0_8px_#facc15]";
                setTimeout(() => {
                    led.className = "w-2.5 h-2.5 rounded-full bg-slate-400 transition-all duration-75";
                }, 80);
            }, intervalMs);
        }

        function togglePower() {
            isPowerOn = !isPowerOn;
            const sw = document.getElementById("power-switch");
            if (isPowerOn) {
                sw.classList.add("rocker-on");
                startMetronome();
            } else {
                sw.classList.remove("rocker-on");
                if (metronomeInterval) clearInterval(metronomeInterval);
                renderBars(0, 0);
            }
        }

        function cycleFrequency() {
            if (metronomeBpm === 100) metronomeBpm = 110;
            else if (metronomeBpm === 110) metronomeBpm = 120;
            else if (metronomeBpm === 120) metronomeBpm = 0;
            else metronomeBpm = 100;

            document.getElementById("freq-text").innerText = metronomeBpm > 0 ? `(${metronomeBpm})` : '(OFF)';
            document.getElementById("metro-led-2").style.display = metronomeBpm === 100 ? 'block' : 'none';
            startMetronome();
        }

        function handleStartBtn() {
            playBeep(1200, 0.15);
            console.log("Training Session Started / Reset!");
        }

        // ==================== GENERATE LED SEGMENTS ====================
        const NUM_SEGMENTS = 28;

        function createLedSegments(containerId) {
            const container = document.getElementById(containerId);
            container.innerHTML = "";
            for (let i = 0; i < NUM_SEGMENTS; i++) {
                const seg = document.createElement("div");
                seg.className = "led-segment";
                seg.id = `${containerId}-seg-${i}`;
                container.appendChild(seg);
            }
        }

        createLedSegments("force-bar-container");
        createLedSegments("lung-bar-container");

        // ==================== RENDER LED BARS ====================
        function renderBars(forceKg, lungKpa) {
            if (!isPowerOn) return;

            // 1. Render Force Bar (Max: 60 kg)
            // 0 - 35 kg: Yellow (Kam kuch)
            // 38 - 55 kg: Green (Optimal)
            // > 55 kg: Red (Ortiqcha kuch)
            const forcePercent = Math.min(1.0, Math.max(0, forceKg / 60.0));
            const activeForceSegments = Math.round(forcePercent * NUM_SEGMENTS);

            for (let i = 0; i < NUM_SEGMENTS; i++) {
                const seg = document.getElementById(`force-bar-container-seg-${i}`);
                if (!seg) continue;

                if (i < activeForceSegments) {
                    const segPercent = i / NUM_SEGMENTS;
                    if (segPercent < 0.60) {
                        seg.className = "led-segment led-yellow-on"; // Kam kuch
                    } else if (segPercent <= 0.88) {
                        seg.className = "led-segment led-green-on";  // Target Zone (40-55kg)
                    } else {
                        seg.className = "led-segment led-red-on";    // Ortiqcha kuch
                    }
                } else {
                    seg.className = "led-segment";
                }
            }
            document.getElementById("force-val-text").innerText = `${forceKg.toFixed(1)} kg`;

            // 2. Render Lung Pressure Bar (Max: 20 kPa)
            // 0 - 5 kPa: Yellow
            // 5 - 15 kPa: Green
            // > 15 kPa: Red
            const lungPercent = Math.min(1.0, Math.max(0, lungKpa / 20.0));
            const activeLungSegments = Math.round(lungPercent * NUM_SEGMENTS);

            for (let i = 0; i < NUM_SEGMENTS; i++) {
                const seg = document.getElementById(`lung-bar-container-seg-${i}`);
                if (!seg) continue;

                if (i < activeLungSegments) {
                    const segPercent = i / NUM_SEGMENTS;
                    if (segPercent < 0.25) {
                        seg.className = "led-segment led-yellow-on";
                    } else if (segPercent <= 0.75) {
                        seg.className = "led-segment led-green-on";  // Target ventilation
                    } else {
                        seg.className = "led-segment led-red-on";    // Excess pressure
                    }
                } else {
                    seg.className = "led-segment";
                }
            }
            document.getElementById("lung-val-text").innerText = `${lungKpa.toFixed(1)} kPa`;

            // 3. Airway Pulse LED
            const airwayLed = document.getElementById("led-airway");
            if (lungKpa > 2.0) {
                airwayLed.classList.add("led-pulse-active");
            } else {
                airwayLed.classList.remove("led-pulse-active");
            }
        }

        // ==================== UPDATE POSITION & STOMACH LEDS ====================
        function updateIndicators(posBtn, stomachKpa, injBtn) {
            if (!isPowerOn) return;

            // Position LED (Chest Center)
            const posLed = document.getElementById("led-position");
            const posLbl = document.getElementById("pos-btn-text");
            if (posBtn === 1 || posBtn === true) {
                posLed.classList.add("led-pos-active");
                if (posLbl) {
                    posLbl.innerText = "BOSILDI (TO'G'RI)";
                    posLbl.className = "text-emerald-400 font-bold";
                }
            } else {
                posLed.classList.remove("led-pos-active");
                if (posLbl) {
                    posLbl.innerText = "BO'SH";
                    posLbl.className = "text-rose-400";
                }
            }

            // Stomach Warning LED
            const stomachLed = document.getElementById("led-stomach");
            const alertBox = document.getElementById("console-alert-box");
            const alertText = document.getElementById("console-alert-text");

            if (stomachKpa > 0.4) {
                stomachLed.classList.add("led-stomach-active");
                alertBox.classList.remove("hidden");
                alertText.innerText = `⚠️ HAVO OSHQOZONDA! (${stomachKpa.toFixed(1)} kPa)`;
                playBeep(400, 0.08, 'sawtooth');
            } else {
                stomachLed.classList.remove("led-stomach-active");
                if (!injBtn) alertBox.classList.add("hidden");
            }

            // Injection Alert
            if (injBtn === 1 || injBtn === true) {
                alertBox.classList.remove("hidden");
                alertBox.className = "mt-1 p-1.5 rounded-lg bg-purple-100 border border-purple-400 text-purple-900 text-[11px] font-bold text-center flex items-center justify-center gap-2 animate-pulse";
                alertText.innerText = "💉 INYEKSIYA (UKOL TOMIRGA KIRDI!)";
            }
        }

        // ==================== WEBSOCKET LIVE TELEMETRY ====================
        let ws;
        function connectWS() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws/telemetry`);

            ws.onopen = () => {
                document.getElementById("conn-dot").className = "w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_#22c55e]";
                document.getElementById("conn-status").innerText = "ESP32 UART: JONLI ALOQA";
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    const force = parseFloat(data.force !== undefined ? data.force : (data.f_curr || 0));
                    const lungP = parseFloat(data.lung_p || 0);
                    const stomachP = parseFloat(data.stomach_p || 0);
                    const posBtn = data.pos_btn !== undefined ? data.pos_btn : (data.pos_ok ? 1 : 0);
                    const injBtn = data.inj_btn !== undefined ? data.inj_btn : (data.inj_ok ? 1 : 0);

                    renderBars(force, lungP);
                    updateIndicators(posBtn, stomachP, injBtn);
                } catch(e) {}
            };

            ws.onclose = () => {
                document.getElementById("conn-dot").className = "w-2.5 h-2.5 rounded-full bg-yellow-400";
                document.getElementById("conn-status").innerText = "ESP32 UART: Qayta ulanmoqda...";
                setTimeout(connectWS, 1500);
            };
        }

        // ==================== MANUAL TEST HELPERS ====================
        let simPos = 0;
        let simInj = 0;
        let simStomach = 0;

        function onSimInput() {
            const f = parseFloat(document.getElementById("sim-force").value);
            const l = parseFloat(document.getElementById("sim-lung").value);
            document.getElementById("sim-force-lbl").innerText = `${f.toFixed(1)} kg`;
            document.getElementById("sim-lung-lbl").innerText = `${l.toFixed(1)} kPa`;

            renderBars(f, l);
            updateIndicators(simPos, simStomach, simInj);
        }

        function toggleSimPos() {
            simPos = simPos ? 0 : 1;
            onSimInput();
        }

        function triggerSimInj() {
            simInj = 1;
            onSimInput();
            setTimeout(() => { simInj = 0; onSimInput(); }, 1800);
        }

        function triggerSimStomach() {
            simStomach = 2.5;
            onSimInput();
            setTimeout(() => { simStomach = 0.0; onSimInput(); }, 2000);
        }

        // Initialize on load
        window.onload = () => {
            startMetronome();
            connectWS();
        };
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_index():
    return HTMLResponse(content=HTML_CONTENT)

@app.get("/console", response_class=HTMLResponse)
async def get_console():
    return HTMLResponse(content=HTML_CONTENT)

@app.post("/api/telemetry")
async def post_telemetry(request: Request):
    global latest_data
    try:
        data = await request.json()
        latest_data = data
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
    port = int(os.environ.get("PORT", 8600))
    print("=" * 68)
    print("  🎮 GENERAL DOCTOR GD/H126 MANIKEN TEST PULTI (CONSOLE)")
    print("=" * 68)
    print(f"  Kompyuterda ochish:   http://localhost:{port}")
    print(f"  Boshqa qurilmalarda:  http://{local_ip}:{port}")
    print("=" * 68 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
