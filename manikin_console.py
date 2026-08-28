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
    <title>Bemor Maniken Test Pulti (CPR & Havo Bosimi)</title>
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
    <div class="w-full max-w-[480px] casing rounded-3xl p-3 sm:p-4 flex flex-col">
        
        <!-- MAIN DISPLAY PANEL (LEFT BAR | MALE TORSO | RIGHT BAR) -->
        <div class="panel-inset rounded-2xl p-3 relative overflow-hidden flex flex-col">
            
            <div class="flex items-stretch justify-between relative h-[380px]">
                
                <!-- LEFT LED BAR: KO'KRAK MASSAJ KUCHI (CPR FORCE) -->
                <div class="w-14 flex flex-col items-center justify-between py-1">
                    <div class="text-center">
                        <div class="text-[11px] font-black text-slate-800 tracking-tight uppercase leading-none">KUCH</div>
                        <div id="force-val-text" class="mono font-black text-rose-700 text-sm mt-0.5">0.0 kg</div>
                    </div>
                    
                    <!-- LED Bar Graph Enclosure (30 Segments) -->
                    <div class="w-8 h-[300px] bg-[#1a0808] border-2 border-[#542525] rounded-md p-1 flex flex-col-reverse justify-between shadow-inner relative" id="force-bar-container">
                        <!-- LED Segments generated by JS -->
                    </div>

                    <div class="text-[10px] font-black text-slate-700 uppercase tracking-tighter">MASSAJ</div>
                </div>

                <!-- CENTER: MALE ANATOMICAL MANIKIN OUTLINE & LED DOTS -->
                <div class="flex-1 relative flex items-center justify-center">
                    
                    <!-- SVG Vector of Strong Male Torso -->
                    <svg viewBox="0 0 320 380" class="w-full h-full" xmlns="http://www.w3.org/2000/svg">
                        
                        <!-- Dotted Pointer Line: Chest Center LED -> Left Force Bar -->
                        <line x1="160" y1="200" x2="35" y2="135" class="pointer-line" />

                        <!-- Dotted Pointer Line: Airway/Trachea LED -> Right Lung Bar -->
                        <line x1="160" y1="105" x2="285" y2="115" class="pointer-line" />

                        <!-- Male Head & Short Hair -->
                        <path d="M120,80 C110,48 130,22 160,22 C190,22 210,48 200,80 C195,100 182,112 160,112 C138,112 125,100 120,80 Z" fill="none" stroke="#222" stroke-width="2.6" />
                        <path d="M116,62 C110,38 128,16 160,16 C192,16 210,38 204,62 C195,42 180,30 160,30 C140,30 125,42 116,62 Z" fill="#222" />
                        
                        <!-- Male Facial Features -->
                        <path d="M132,58 Q144,52 152,58" fill="none" stroke="#222" stroke-width="2.2" />
                        <path d="M168,58 Q176,52 188,58" fill="none" stroke="#222" stroke-width="2.2" />
                        <path d="M134,66 Q143,72 152,66" fill="none" stroke="#222" stroke-width="2" />
                        <path d="M168,66 Q177,72 186,66" fill="none" stroke="#222" stroke-width="2" />
                        <path d="M160,68 L157,78 L163,78" fill="none" stroke="#222" stroke-width="1.8" />
                        <path d="M146,90 Q160,96 174,90" fill="none" stroke="#222" stroke-width="2.2" />

                        <!-- Strong Masculine Neck -->
                        <path d="M142,108 L140,132" stroke="#222" stroke-width="2.6" fill="none" />
                        <path d="M178,108 L180,132" stroke="#222" stroke-width="2.6" fill="none" />
                        <path d="M144,124 Q160,128 176,124" stroke="#222" stroke-width="1.8" fill="none" />

                        <!-- Broad Male Shoulders & Collarbone -->
                        <path d="M140,132 C105,138 60,150 45,178" stroke="#222" stroke-width="3" fill="none" />
                        <path d="M180,132 C215,138 260,150 275,178" stroke="#222" stroke-width="3" fill="none" />
                        <path d="M125,138 Q160,146 195,138" stroke="#222" stroke-width="2" fill="none" />

                        <!-- Male Chest (Pectoralis Major - To'g'ri burchakli, tekis erkak ko'kragi) -->
                        <path d="M152,155 L152,192 C152,206 135,212 95,208 C75,206 65,190 60,178" stroke="#222" stroke-width="2.4" fill="none" />
                        <path d="M168,155 L168,192 C168,206 185,212 225,208 C245,206 255,190 260,178" stroke="#222" stroke-width="2.4" fill="none" />

                        <!-- Sternum line -->
                        <line x1="160" y1="145" x2="160" y2="185" stroke="#222" stroke-width="1.5" stroke-dasharray="2,2" />

                        <!-- Outer Torso Lines -->
                        <path d="M45,178 C40,220 50,280 65,360" stroke="#222" stroke-width="2.8" fill="none" />
                        <path d="M275,178 C280,220 270,280 255,360" stroke="#222" stroke-width="2.8" fill="none" />

                        <!-- Rib Arch (Qovurg'a yoyi & Qorin) -->
                        <path d="M115,260 C142,230 160,215 160,210 C160,215 178,230 205,260" stroke="#222" stroke-width="2.4" fill="none" />
                        <line x1="160" y1="215" x2="160" y2="295" stroke="#222" stroke-width="1.8" stroke-dasharray="3,3" />
                    </svg>

                    <!-- PHYSICAL LED INDICATORS MOUNTED PRECISELY ON THE MALE TORSO -->

                    <!-- 1. Airway / Throat LED -->
                    <div class="absolute top-[100px] left-[50%] -translate-x-1/2 flex flex-col items-center">
                        <div id="led-airway" class="led-indicator"></div>
                    </div>

                    <!-- 2. Central Hand Placement LED (Sternum Markaziy Nuqtasi - Pin 13) -->
                    <div class="absolute top-[188px] left-[50%] -translate-x-1/2 flex flex-col items-center cursor-pointer" onclick="toggleSimPos()">
                        <div id="led-position" class="led-indicator"></div>
                        <span id="pos-status-label" class="text-[9px] font-black text-slate-800 mt-1 uppercase tracking-tighter text-center leading-none">
                            NUQTA (Pin 13)
                        </span>
                    </div>

                    <!-- 3. Stomach Air Hazard LED (Oshqozon - Pin 25) -->
                    <div class="absolute bottom-[28px] left-[50%] -translate-x-1/2 flex flex-col items-center">
                        <div id="led-stomach" class="led-indicator"></div>
                        <span class="text-[8px] font-black text-slate-800 mt-0.5 uppercase tracking-tighter">
                            OSHQOZON
                        </span>
                    </div>
                </div>

                <!-- RIGHT LED BAR: O'PKA BOSIMI (VENTILATION) -->
                <div class="w-14 flex flex-col items-center justify-between py-1">
                    <div class="text-center">
                        <div class="text-[11px] font-black text-slate-800 tracking-tight uppercase leading-none">O'PKA</div>
                        <div id="lung-val-text" class="mono font-black text-rose-700 text-sm mt-0.5">0.0 kPa</div>
                    </div>

                    <!-- LED Bar Graph Enclosure (30 Segments) -->
                    <div class="w-8 h-[300px] bg-[#1a0808] border-2 border-[#542525] rounded-md p-1 flex flex-col-reverse justify-between shadow-inner relative" id="lung-bar-container">
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

        <!-- SIMULATOR MANUAL TEST CONTROLS (Qo'lda sinab ko'rish uchun qulay panel) -->
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
                    <input type="range" id="sim-lung" min="0" max="30" step="0.2" value="0" 
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

            // 2. Render Lung Pressure Bar (Max: 30 kPa)
            // 0 - 5 kPa: Yellow
            // 5 - 20 kPa: Green
            // > 20 kPa: Red
            const lungPercent = Math.min(1.0, Math.max(0, lungKpa / 30.0));
            const activeLungSegments = Math.round(lungPercent * NUM_SEGMENTS);

            for (let i = 0; i < NUM_SEGMENTS; i++) {
                const seg = document.getElementById(`lung-bar-container-seg-${i}`);
                if (!seg) continue;

                if (i < activeLungSegments) {
                    const segPercent = i / NUM_SEGMENTS;
                    if (segPercent < 0.20) {
                        seg.className = "led-segment led-yellow-on";
                    } else if (segPercent <= 0.70) {
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
            if (lungKpa > 1.5) {
                airwayLed.classList.add("led-pulse-active");
            } else {
                airwayLed.classList.remove("led-pulse-active");
            }
        }

        // ==================== UPDATE POSITION & STOMACH LEDS ====================
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

            // Stomach Warning LED
            const stomachLed = document.getElementById("led-stomach");
            const alertBox = document.getElementById("console-alert-box");
            const alertText = document.getElementById("console-alert-text");

            if (stomachKpa > 0.4) {
                stomachLed.classList.add("led-stomach-active");
                alertBox.classList.remove("hidden");
                alertBox.className = "mt-2 p-1.5 rounded-lg bg-rose-100 border border-rose-400 text-rose-900 text-xs font-bold text-center flex items-center justify-center gap-2 animate-pulse";
                alertText.innerText = `⚠️ HAVO OSHQOZONDA! (${stomachKpa.toFixed(1)} kPa)`;
            } else {
                stomachLed.classList.remove("led-stomach-active");
                if (!injBtn) alertBox.classList.add("hidden");
            }

            // Injection Alert
            if (injBtn === 1 || injBtn === true) {
                alertBox.classList.remove("hidden");
                alertBox.className = "mt-2 p-1.5 rounded-lg bg-purple-100 border border-purple-400 text-purple-900 text-xs font-bold text-center flex items-center justify-center gap-2 animate-pulse";
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
