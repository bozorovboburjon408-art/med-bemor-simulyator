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

app = FastAPI(title="Bemor Maniken Test Pulti")

active_websockets: List[WebSocket] = []

latest_data = {
    "force": 0.0,
    "lung_p": 0.0,
    "stomach_p": 0.0,
    "pos_btn": 0,
    "inj_btn": 0
}

HTML_CONTENT = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bemor Maniken Test Pulti (CPR, O'pka va Ukol)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@500;700;900&display=swap');

        body {
            background-color: #0e131f;
            font-family: 'Inter', sans-serif;
            user-select: none;
            overflow-x: hidden;
        }

        .mono {
            font-family: 'Share Tech Mono', monospace;
        }

        /* Medical Console Bezel Casing */
        .casing {
            background: linear-gradient(145deg, #ded9cb, #cbc4b3);
            box-shadow: 0 25px 50px rgba(0,0,0,0.7), inset 0 2px 4px rgba(255,255,255,0.9), inset 0 -3px 6px rgba(0,0,0,0.25);
            border: 4px solid #b3ab98;
        }

        .panel-inset {
            background: #e6e2d6;
            box-shadow: inset 0 3px 8px rgba(0,0,0,0.18), 0 1px 0 rgba(255,255,255,0.9);
            border: 2px solid #b8b19e;
        }

        /* Segmented LED Bar Styles */
        .led-segment {
            transition: all 0.04s ease-out;
            border-radius: 1.5px;
            margin-bottom: 2px;
            height: 7.5px;
            background-color: #3b1919;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.8);
        }

        .led-yellow-on {
            background-color: #facc15 !important;
            box-shadow: 0 0 12px #facc15, inset 0 0 4px #ffffff !important;
        }

        .led-green-on {
            background-color: #22c55e !important;
            box-shadow: 0 0 14px #22c55e, inset 0 0 4px #ffffff !important;
        }

        .led-red-on {
            background-color: #ef4444 !important;
            box-shadow: 0 0 14px #ef4444, inset 0 0 4px #ffffff !important;
        }

        /* Anatomical LED Indicator Lights */
        .led-indicator {
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: #4a1919;
            border: 2px solid #290e0e;
            transition: all 0.08s ease;
        }

        .led-pos-active {
            background: #22c55e !important;
            box-shadow: 0 0 18px #22c55e, 0 0 35px #22c55e, inset 0 0 6px #ffffff !important;
            border-color: #15803d !important;
            animation: pulseLed 0.35s infinite alternate;
        }

        .led-inj-active {
            background: #a855f7 !important;
            box-shadow: 0 0 20px #a855f7, 0 0 40px #c084fc, inset 0 0 6px #ffffff !important;
            border-color: #7e22ce !important;
            animation: pulseInj 0.25s infinite alternate;
        }

        .led-stomach-active {
            background: #ef4444 !important;
            box-shadow: 0 0 18px #ef4444, 0 0 35px #ef4444, inset 0 0 6px #ffffff !important;
            border-color: #b91c1c !important;
            animation: blinkFast 0.2s infinite;
        }

        .led-pulse-active {
            background: #38bdf8 !important;
            box-shadow: 0 0 14px #38bdf8, inset 0 0 4px #ffffff !important;
            border-color: #0284c7 !important;
        }

        @keyframes pulseLed {
            0% { transform: scale(1); filter: brightness(1); }
            100% { transform: scale(1.18); filter: brightness(1.4); }
        }

        @keyframes pulseInj {
            0% { transform: scale(1); filter: brightness(1.1); }
            100% { transform: scale(1.25); filter: brightness(1.6); }
        }

        @keyframes blinkFast {
            0%, 100% { opacity: 1; filter: brightness(1.5); }
            50% { opacity: 0.2; filter: brightness(0.5); }
        }

        /* Pointer Dashed Lines */
        .pointer-line {
            stroke: #222222;
            stroke-width: 2;
            stroke-dasharray: 4, 3;
        }
    </style>
</head>
<body class="min-h-screen flex flex-col items-center justify-center p-2 sm:p-4">

    <!-- Top Connection & Navigation Bar -->
    <div class="w-full max-w-xl flex items-center justify-between mb-2 text-slate-300 text-xs px-2">
        <div class="flex items-center gap-2">
            <span id="conn-dot" class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
            <span id="conn-status" class="font-bold text-slate-200">ESP32 UART: Kutish holatida</span>
        </div>
        <div class="flex items-center gap-2">
            <a href="/monitor" target="_blank" class="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-lg transition shadow text-[11px]">
                <i class="fa-solid fa-heart-pulse mr-1"></i> ICU Monitor
            </a>
            <a href="/" target="_blank" class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg transition shadow text-[11px]">
                <i class="fa-solid fa-user-doctor mr-1"></i> AI Bemor
            </a>
        </div>
    </div>

    <!-- MAIN CONSOLE DEVICE (FOCUSED CLEAN HARDWARE PANEL) -->
    <div class="w-full max-w-[500px] casing rounded-3xl p-3 sm:p-4 flex flex-col">
        
        <!-- MAIN DISPLAY PANEL (LEFT BAR | MALE TORSO + ARMS | RIGHT BAR) -->
        <div class="panel-inset rounded-2xl p-3 relative overflow-hidden flex flex-col">
            
            <div class="flex items-stretch justify-between relative h-[390px]">
                
                <!-- LEFT LED BAR: KO'KRAK MASSAJ KUCHI (CPR FORCE) -->
                <div class="w-14 flex flex-col items-center justify-between py-1 z-10">
                    <div class="text-center">
                        <div class="text-[11px] font-black text-slate-800 tracking-tight uppercase leading-none">KUCH</div>
                        <div id="force-val-text" class="mono font-black text-rose-700 text-sm mt-0.5">0.0 kg</div>
                    </div>
                    
                    <!-- LED Bar Graph Enclosure (30 Segments) -->
                    <div class="w-8 h-[305px] bg-[#1a0808] border-2 border-[#542525] rounded-md p-1 flex flex-col-reverse justify-between shadow-inner relative" id="force-bar-container">
                        <!-- LED Segments generated by JS -->
                    </div>

                    <div class="text-[10px] font-black text-slate-700 uppercase tracking-tighter">MASSAJ</div>
                </div>

                <!-- CENTER: MALE ANATOMICAL MANIKIN WITH 2 ARMS & LED INDICATORS -->
                <div class="flex-1 relative flex items-center justify-center">
                    
                    <!-- SVG Vector of Strong Male Torso & Two Arms -->
                    <svg viewBox="0 0 340 390" class="w-full h-full" xmlns="http://www.w3.org/2000/svg">
                        
                        <!-- Dotted Pointer Line: Chest Center LED -> Left Force Bar -->
                        <line x1="170" y1="200" x2="35" y2="135" class="pointer-line" />

                        <!-- Dotted Pointer Line: Airway/Trachea LED -> Right Lung Bar -->
                        <line x1="170" y1="105" x2="305" y2="115" class="pointer-line" />

                        <!-- Dotted Pointer Line: Right Arm Vein LED -> Injection Needle Pointer -->
                        <line x1="285" y1="245" x2="250" y2="245" class="pointer-line" stroke="#7e22ce" stroke-width="1.5" />

                        <!-- Male Head & Short Hair -->
                        <path d="M130,80 C120,48 140,22 170,22 C200,22 220,48 210,80 C205,100 192,112 170,112 C148,112 135,100 130,80 Z" fill="none" stroke="#222" stroke-width="2.6" />
                        <path d="M126,62 C120,38 138,16 170,16 C202,16 220,38 214,62 C205,42 190,30 170,30 C150,30 135,42 126,62 Z" fill="#222" />
                        
                        <!-- Male Facial Features -->
                        <path d="M142,58 Q154,52 162,58" fill="none" stroke="#222" stroke-width="2.2" />
                        <path d="M178,58 Q186,52 198,58" fill="none" stroke="#222" stroke-width="2.2" />
                        <path d="M144,66 Q153,72 162,66" fill="none" stroke="#222" stroke-width="2" />
                        <path d="M178,66 Q187,72 196,66" fill="none" stroke="#222" stroke-width="2" />
                        <path d="M170,68 L167,78 L173,78" fill="none" stroke="#222" stroke-width="1.8" />
                        <path d="M156,90 Q170,96 184,90" fill="none" stroke="#222" stroke-width="2.2" />

                        <!-- Strong Masculine Neck -->
                        <path d="M152,108 L150,132" stroke="#222" stroke-width="2.6" fill="none" />
                        <path d="M188,108 L190,132" stroke="#222" stroke-width="2.6" fill="none" />
                        <path d="M154,124 Q170,128 186,124" stroke="#222" stroke-width="1.8" fill="none" />

                        <!-- Broad Shoulders & Clavicles -->
                        <path d="M150,132 C115,138 75,150 55,178" stroke="#222" stroke-width="3" fill="none" />
                        <path d="M190,132 C225,138 265,150 285,178" stroke="#222" stroke-width="3" fill="none" />
                        <path d="M135,138 Q170,146 205,138" stroke="#222" stroke-width="2" fill="none" />

                        <!-- ==================== LEFT ARM (CHAP QO'L) ==================== -->
                        <!-- Shoulder -> Bicep -> Elbow -> Forearm -> Wrist -->
                        <path d="M55,178 C40,205 32,240 35,280 C36,305 42,340 48,375" stroke="#222" stroke-width="2.8" fill="none" />
                        <path d="M78,198 C72,235 68,280 66,375" stroke="#222" stroke-width="2.4" fill="none" />
                        <!-- Left Elbow Crease & Vein line -->
                        <path d="M42,260 Q52,266 62,258" stroke="#222" stroke-width="1.6" fill="none" />

                        <!-- ==================== RIGHT ARM (O'NG QO'L - UKOL TOMIRI) ==================== -->
                        <!-- Shoulder -> Bicep -> Elbow -> Forearm -> Wrist -->
                        <path d="M285,178 C300,205 308,240 305,280 C304,305 298,340 292,375" stroke="#222" stroke-width="2.8" fill="none" />
                        <path d="M262,198 C268,235 272,280 274,375" stroke="#222" stroke-width="2.4" fill="none" />
                        <!-- Right Elbow Crease (Tirsak tomiri) -->
                        <path d="M278,260 Q288,266 298,258" stroke="#222" stroke-width="1.6" fill="none" />

                        <!-- ==================== MALE CHEST & TORSO ==================== -->
                        <!-- Left Pectoral -->
                        <path d="M162,155 L162,192 C162,206 145,212 105,208 C88,206 78,192 78,180" stroke="#222" stroke-width="2.4" fill="none" />
                        <!-- Right Pectoral -->
                        <path d="M178,155 L178,192 C178,206 195,212 235,208 C252,206 262,192 262,180" stroke="#222" stroke-width="2.4" fill="none" />

                        <!-- Sternum line -->
                        <line x1="170" y1="145" x2="170" y2="185" stroke="#222" stroke-width="1.5" stroke-dasharray="2,2" />

                        <!-- Torso Inner Body Lines -->
                        <path d="M78,198 C72,240 80,300 95,375" stroke="#222" stroke-width="2.6" fill="none" />
                        <path d="M262,198 C268,240 260,300 245,375" stroke="#222" stroke-width="2.6" fill="none" />

                        <!-- Rib Arch (Qovurg'a yoyi & Qorin) -->
                        <path d="M125,260 C152,230 170,215 170,210 C170,215 188,230 215,260" stroke="#222" stroke-width="2.4" fill="none" />
                        <line x1="170" y1="215" x2="170" y2="295" stroke="#222" stroke-width="1.8" stroke-dasharray="3,3" />
                    </svg>

                    <!-- ==================== PHYSICAL LED INDICATOR LIGHTS ==================== -->

                    <!-- 1. Airway / Throat LED (Bo'yin / Tomir puls) -->
                    <div class="absolute top-[102px] left-[50%] -translate-x-1/2 flex flex-col items-center">
                        <div id="led-airway" class="led-indicator"></div>
                    </div>

                    <!-- 2. Central Hand Placement LED (Sternum Markaziy Nuqtasi - Pin 13) -->
                    <div class="absolute top-[190px] left-[50%] -translate-x-1/2 flex flex-col items-center cursor-pointer" onclick="toggleSimPos()">
                        <div id="led-position" class="led-indicator"></div>
                        <span id="pos-status-label" class="text-[9px] font-black text-slate-800 mt-1 uppercase tracking-tighter text-center leading-none">
                            NUQTA (Pin 13)
                        </span>
                    </div>

                    <!-- 3. Right Arm Injection LED (O'ng qo'l tirsak tomiri - Pin 4) -->
                    <div class="absolute top-[236px] right-[24px] flex flex-col items-center cursor-pointer" onclick="triggerSimInj()">
                        <div id="led-injection" class="led-indicator"></div>
                        <span class="text-[8px] font-black text-purple-900 mt-0.5 uppercase tracking-tighter text-center leading-none">
                            UKOL (Pin 4)
                        </span>
                    </div>

                    <!-- 4. Stomach Air Hazard LED (Oshqozon - Pin 25) -->
                    <div class="absolute bottom-[28px] left-[50%] -translate-x-1/2 flex flex-col items-center">
                        <div id="led-stomach" class="led-indicator"></div>
                        <span class="text-[8px] font-black text-slate-800 mt-0.5 uppercase tracking-tighter">
                            OSHQOZON
                        </span>
                    </div>
                </div>

                <!-- RIGHT LED BAR: O'PKA BOSIMI (VENTILATION) -->
                <div class="w-14 flex flex-col items-center justify-between py-1 z-10">
                    <div class="text-center">
                        <div class="text-[11px] font-black text-slate-800 tracking-tight uppercase leading-none">O'PKA</div>
                        <div id="lung-val-text" class="mono font-black text-rose-700 text-sm mt-0.5">0.0 kPa</div>
                    </div>

                    <!-- LED Bar Graph Enclosure (30 Segments) -->
                    <div class="w-8 h-[305px] bg-[#1a0808] border-2 border-[#542525] rounded-md p-1 flex flex-col-reverse justify-between shadow-inner relative" id="lung-bar-container">
                        <!-- LED Segments generated by JS -->
                    </div>

                    <div class="text-[10px] font-black text-slate-700 uppercase tracking-tighter">VENTILYATSIYA</div>
                </div>

            </div>

            <!-- Ukol va Oshqozon Ogohlantirish Popupi -->
            <div id="console-alert-box" class="hidden mt-2 p-1.5 rounded-lg bg-rose-100 border border-rose-400 text-rose-900 text-xs font-bold text-center flex items-center justify-center gap-2 animate-pulse">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <span id="console-alert-text">OGOHLANTIRISH</span>
            </div>

        </div>

        <!-- SIMULATOR MANUAL TEST CONTROLS (Slayderlar) -->
        <div class="mt-2.5 bg-slate-900/90 rounded-xl p-2.5 text-slate-200 text-xs flex flex-col gap-2 border border-slate-800">
            <div class="flex items-center justify-between text-[11px] font-bold text-slate-300">
                <span><i class="fa-solid fa-sliders text-indigo-400 mr-1"></i> Dasturiy Test Sinovi (Slayderlar):</span>
                <span class="text-[10px] text-emerald-400 font-bold">ESP32 Jonli ishlaydi</span>
            </div>

            <div class="grid grid-cols-2 gap-2">
                <!-- Force Slider -->
                <div>
                    <div class="flex justify-between text-[10px] mb-0.5">
                        <span>Ko'krak Kuchi:</span>
                        <span id="sim-force-lbl" class="mono text-yellow-400 font-bold">0 kg</span>
                    </div>
                    <input type="range" id="sim-force" min="0" max="60" step="0.5" value="0" 
                           oninput="onSimInput()" class="w-full accent-emerald-500 h-1.5 bg-slate-700 rounded-lg cursor-pointer">
                </div>

                <!-- Lung Pressure Slider -->
                <div>
                    <div class="flex justify-between text-[10px] mb-0.5">
                        <span>O'pka Bosimi:</span>
                        <span id="sim-lung-lbl" class="mono text-cyan-400 font-bold">0 kPa</span>
                    </div>
                    <input type="range" id="sim-lung" min="0" max="4.0" step="0.1" value="0" 
                           oninput="onSimInput()" class="w-full accent-cyan-500 h-1.5 bg-slate-700 rounded-lg cursor-pointer">
                </div>
            </div>

            <div class="flex items-center justify-between gap-2 mt-0.5">
                <!-- Hand Position Button Toggle -->
                <button id="btn-toggle-pos" onclick="toggleSimPos()" class="flex-1 py-1 px-2 rounded bg-slate-800 hover:bg-slate-700 font-bold text-[11px] text-center border border-slate-700 transition">
                    🔘 Nuqta: <span id="pos-btn-text" class="text-rose-400">BO'SH</span>
                </button>

                <!-- Injection Button Toggle -->
                <button id="btn-toggle-inj" onclick="triggerSimInj()" class="flex-1 py-1 px-2 rounded bg-slate-800 hover:bg-slate-700 font-bold text-[11px] text-center border border-slate-700 transition">
                    💉 Ukol: <span id="inj-btn-text" class="text-purple-400">Kiritish</span>
                </button>

                <!-- Stomach Pressure Spike -->
                <button onclick="triggerSimStomach()" class="py-1 px-2 rounded bg-rose-950 hover:bg-rose-900 font-bold text-[11px] text-rose-300 border border-rose-800 transition">
                    ⚠️ Oshqozon
                </button>
            </div>
        </div>

    </div>

    <script>
        // ==================== GENERATE LED SEGMENTS ====================
        const NUM_SEGMENTS = 30;

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
            // 1. Render Force Bar (Max: 60 kg)
            // 0 - 38 kg: Yellow (Kam kuch)
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
                        seg.className = "led-segment led-green-on";  // Target Zone (38-55kg)
                    } else {
                        seg.className = "led-segment led-red-on";    // Ortiqcha kuch
                    }
                } else {
                    seg.className = "led-segment";
                }
            }
            document.getElementById("force-val-text").innerText = `${forceKg.toFixed(1)} kg`;

            // 2. Render Lung Pressure Bar (Max: 3.5 kPa / 35 cmH2O Standard)
            // 0 - 1.9 kPa (<20 cmH2O): Yellow (Kam havo / Qattiqroq siqing)
            // 2.0 - 3.0 kPa (20 - 30 cmH2O): YORQIN YASHIL (TO'G'RI VA YETARLI NAFAS)
            // > 3.1 kPa (>32 cmH2O): Qizil (Ortiqcha bosim / Barotravma xavfi)
            const lungPercent = Math.min(1.0, Math.max(0, lungKpa / 3.5));
            const activeLungSegments = Math.round(lungPercent * NUM_SEGMENTS);

            for (let i = 0; i < NUM_SEGMENTS; i++) {
                const seg = document.getElementById(`lung-bar-container-seg-${i}`);
                if (!seg) continue;

                if (i < activeLungSegments) {
                    const segPercent = i / NUM_SEGMENTS;
                    if (segPercent < 0.55) {
                        seg.className = "led-segment led-yellow-on"; // Kam havo (<2.0 kPa)
                    } else if (segPercent <= 0.88) {
                        seg.className = "led-segment led-green-on";  // Me'yor: 2.0 - 3.0 kPa (20-30 cmH2O)
                    } else {
                        seg.className = "led-segment led-red-on";    // Ortiqcha bosim (>3.1 kPa)
                    }
                } else {
                    seg.className = "led-segment";
                }
            }
            const cmH2O = (lungKpa * 10.2).toFixed(0);
            document.getElementById("lung-val-text").innerText = `${lungKpa.toFixed(1)} kPa (${cmH2O} cmH2O)`;

            // 3. Airway Pulse LED (Nafas kurganda)
            const airwayLed = document.getElementById("led-airway");
            if (lungKpa > 0.8) {
                airwayLed.classList.add("led-pulse-active");
            } else {
                airwayLed.classList.remove("led-pulse-active");
            }
        }

        // ==================== UPDATE POSITION, INJECTION & STOMACH LEDS ====================
        function updateIndicators(posBtn, stomachKpa, injBtn) {
            // Position LED (Chest Center - Pin 13)
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

            // Injection LED (Right Arm Vein - Pin 4)
            const injLed = document.getElementById("led-injection");
            const alertBox = document.getElementById("console-alert-box");
            const alertText = document.getElementById("console-alert-text");

            if (injBtn === 1 || injBtn === true) {
                injLed.classList.add("led-inj-active");
                alertBox.classList.remove("hidden");
                alertBox.className = "mt-2 p-1.5 rounded-lg bg-purple-100 border border-purple-400 text-purple-900 text-xs font-bold text-center flex items-center justify-center gap-2 animate-pulse";
                alertText.innerText = "💉 INYEKSIYA (UKOL TOMIRGA KIRDI!)";
            } else {
                injLed.classList.remove("led-inj-active");
            }

            // Stomach Warning LED
            const stomachLed = document.getElementById("led-stomach");
            if (stomachKpa > 0.4) {
                stomachLed.classList.add("led-stomach-active");
                alertBox.classList.remove("hidden");
                alertBox.className = "mt-2 p-1.5 rounded-lg bg-rose-100 border border-rose-400 text-rose-900 text-xs font-bold text-center flex items-center justify-center gap-2 animate-pulse";
                alertText.innerText = `⚠️ HAVO OSHQOZONDA! (${stomachKpa.toFixed(1)} kPa)`;
            } else {
                stomachLed.classList.remove("led-stomach-active");
                if (!injBtn) alertBox.classList.add("hidden");
            }
        }

        // ==================== WEBSOCKET LIVE TELEMETRY ====================
        let ws;
        function connectWS() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(`${protocol}//${window.location.host}/ws/telemetry`);

            ws.onopen = () => {
                document.getElementById("conn-dot").className = "w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_#22c55e]";
                document.getElementById("conn-status").innerText = "ESP32 UART: JONLI ALOQA (0ms)";
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

        window.onload = () => {
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
    print("  🎮 BEMOR MANIKEN TEST PULTI (FOCUSED HARDWARE CONSOLE)")
    print("=" * 68)
    print(f"  Kompyuterda ochish:   http://localhost:{port}")
    print(f"  Boshqa qurilmalarda:  http://{local_ip}:{port}")
    print("=" * 68 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
