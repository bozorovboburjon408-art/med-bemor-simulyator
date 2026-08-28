import os
import sys
import json
import socket
import asyncio
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
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
            background-color: #0b0f19;
            font-family: 'Inter', sans-serif;
            user-select: none;
            overflow-x: hidden;
        }

        .mono {
            font-family: 'Share Tech Mono', monospace;
        }

        /* Medical Console Bezel Casing */
        .casing {
            background: linear-gradient(145deg, #e2ded4, #ccc5b3);
            box-shadow: 0 25px 60px rgba(0,0,0,0.8), inset 0 2px 4px rgba(255,255,255,0.9), inset 0 -3px 6px rgba(0,0,0,0.3);
            border: 4px solid #aba28d;
        }

        .panel-inset {
            background: #ffffff;
            box-shadow: inset 0 3px 8px rgba(0,0,0,0.2), 0 1px 0 rgba(255,255,255,0.9);
            border: 2px solid #b5ad9a;
        }

        /* Segmented LED Bar Styles */
        .led-segment {
            transition: all 0.04s ease-out;
            border-radius: 2px;
            margin-bottom: 2.5px;
            height: 9px;
            background-color: #3b1919;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.8);
        }

        .led-yellow-on {
            background-color: #facc15 !important;
            box-shadow: 0 0 14px #facc15, inset 0 0 4px #ffffff !important;
        }

        .led-green-on {
            background-color: #22c55e !important;
            box-shadow: 0 0 16px #22c55e, inset 0 0 4px #ffffff !important;
        }

        .led-red-on {
            background-color: #ef4444 !important;
            box-shadow: 0 0 16px #ef4444, inset 0 0 4px #ffffff !important;
        }

        /* Over-the-Photo Dynamic LED Glow Overlays */
        .photo-led {
            border-radius: 50%;
            transition: all 0.12s ease-out;
            pointer-events: auto;
            cursor: pointer;
            opacity: 0; /* In idle state, completely invisible so only the photo's circle is seen */
        }

        /* Chest Center Position LED (PIN 13) */
        .pos-led-on {
            opacity: 1 !important;
            background: radial-gradient(circle, #4ade80 20%, rgba(34, 197, 94, 0.85) 60%, rgba(34, 197, 94, 0) 100%) !important;
            box-shadow: 0 0 25px #22c55e, 0 0 50px #22c55e, 0 0 80px rgba(34, 197, 94, 0.6) !important;
            animation: pulseGlow 0.35s infinite alternate;
        }

        /* Airway Throat LED */
        .airway-led-on {
            opacity: 1 !important;
            background: radial-gradient(circle, #38bdf8 20%, rgba(6, 182, 212, 0.85) 60%, rgba(6, 182, 212, 0) 100%) !important;
            box-shadow: 0 0 25px #06b6d4, 0 0 50px #06b6d4 !important;
        }

        /* Injection Arm LED (PIN 4) */
        .inj-led-on {
            opacity: 1 !important;
            background: radial-gradient(circle, #c084fc 20%, rgba(168, 85, 247, 0.85) 60%, rgba(168, 85, 247, 0) 100%) !important;
            box-shadow: 0 0 30px #a855f7, 0 0 60px #c084fc, 0 0 90px rgba(168, 85, 247, 0.6) !important;
            animation: pulseGlow 0.25s infinite alternate;
        }

        /* Stomach Hazard LED */
        .stomach-led-on {
            opacity: 1 !important;
            background: radial-gradient(circle, #f87171 20%, rgba(239, 68, 68, 0.85) 60%, rgba(239, 68, 68, 0) 100%) !important;
            box-shadow: 0 0 30px #ef4444, 0 0 60px #ef4444 !important;
            animation: blinkFast 0.2s infinite;
        }

        @keyframes pulseGlow {
            0% { transform: scale(1); filter: brightness(1); }
            100% { transform: scale(1.15); filter: brightness(1.4); }
        }

        @keyframes blinkFast {
            0%, 100% { opacity: 1; filter: brightness(1.5); }
            50% { opacity: 0.2; filter: brightness(0.5); }
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

    <!-- MAIN CONSOLE DEVICE -->
    <div class="w-full max-w-[560px] casing rounded-3xl p-3 sm:p-4 flex flex-col">
        
        <!-- MAIN DISPLAY PANEL (LEFT BAR | PHOTO OF MANIKIN WITH OVERLAYS | RIGHT BAR) -->
        <div class="panel-inset rounded-2xl p-2 sm:p-3 relative overflow-hidden flex flex-col">
            
            <div class="flex items-stretch justify-between relative h-[480px]">
                
                <!-- LEFT LED BAR: KO'KRAK MASSAJ KUCHI (CPR FORCE) -->
                <div class="w-16 flex flex-col items-center justify-between py-2 z-10">
                    <div class="text-center">
                        <div class="text-[12px] font-black text-slate-900 tracking-tight uppercase leading-none">KUCH</div>
                        <div id="force-val-text" class="mono font-black text-rose-700 text-sm sm:text-base mt-0.5">0.0 kg</div>
                    </div>
                    
                    <!-- LED Bar Graph Enclosure (30 Segments) -->
                    <div class="w-9 h-[380px] bg-[#1a0808] border-2 border-[#542525] rounded-md p-1 flex flex-col-reverse justify-between shadow-inner relative" id="force-bar-container">
                        <!-- LED Segments generated by JS -->
                    </div>

                    <div class="text-[11px] font-black text-slate-800 uppercase tracking-tighter">MASSAJ</div>
                </div>

                <!-- CENTER: REALISTIC HIGH-INTEL MANIKIN PHOTO WITH PIXEL-PERFECT LED OVERLAYS -->
                <div class="flex-1 relative flex items-center justify-center mx-1 overflow-hidden rounded-xl border border-slate-300 shadow-inner bg-slate-100 h-full">
                    
                    <!-- Aspect Ratio Locked Image Wrapper (Zero Shift Error) -->
                    <div class="relative h-full flex items-center justify-center" style="aspect-ratio: 707 / 1024;">
                        
                        <!-- Base Manikin Photo -->
                        <img src="/manikin_photo.png" alt="Maniken" class="w-full h-full block object-fill pointer-events-none select-none">

                        <!-- ==================== PIXEL-PERFECT INTERACTIVE LED OVERLAYS ==================== -->

                        <!-- 1. Airway / Throat LED (Bo'yin/Tomir nuqtasi) -->
                        <div id="led-airway" class="photo-led absolute top-[33.74%] left-[50.85%] -translate-x-1/2 -translate-y-1/2 w-[8.5%] h-[6.0%] flex items-center justify-center pointer-events-none">
                        </div>

                        <!-- 2. Chest Center Position LED (NUQTA PIN 13) -->
                        <div id="led-position" onclick="toggleSimPos()" class="photo-led absolute top-[56.30%] left-[50.85%] -translate-x-1/2 -translate-y-1/2 w-[12.5%] h-[8.6%] flex items-center justify-center" title="Qo'l nuqtasi (Pin 13)">
                        </div>

                        <!-- 3. Right Arm Injection LED (UKOL PIN 4) -->
                        <div id="led-injection" onclick="triggerSimInj()" class="photo-led absolute top-[68.41%] left-[91.58%] -translate-x-1/2 -translate-y-1/2 w-[13.0%] h-[9.0%] flex items-center justify-center" title="Ukol / Inyeksiya (Pin 4)">
                        </div>

                        <!-- 4. Stomach Warning LED (OSHQOZON) -->
                        <div id="led-stomach" class="photo-led absolute top-[92.7%] left-[51.0%] -translate-x-1/2 -translate-y-1/2 w-[11.0%] h-[7.6%] flex items-center justify-center pointer-events-none" title="Oshqozon bosimi">
                        </div>

                    </div>

                </div>

                <!-- RIGHT LED BAR: O'PKA BOSIMI (VENTILATION) -->
                <div class="w-16 flex flex-col items-center justify-between py-2 z-10">
                    <div class="text-center">
                        <div class="text-[12px] font-black text-slate-900 tracking-tight uppercase leading-none">O'PKA</div>
                        <div id="lung-val-text" class="mono font-black text-rose-700 text-xs sm:text-sm mt-0.5">0.0 kPa</div>
                    </div>

                    <!-- LED Bar Graph Enclosure (30 Segments) -->
                    <div class="w-9 h-[380px] bg-[#1a0808] border-2 border-[#542525] rounded-md p-1 flex flex-col-reverse justify-between shadow-inner relative" id="lung-bar-container">
                        <!-- LED Segments generated by JS -->
                    </div>

                    <div class="text-[11px] font-black text-slate-800 uppercase tracking-tighter">VENTILYATSIYA</div>
                </div>

            </div>

            <!-- Ukol va Oshqozon Ogohlantirish Popupi -->
            <div id="console-alert-box" class="hidden mt-2 p-2 rounded-lg bg-rose-100 border border-rose-400 text-rose-900 text-xs font-bold text-center flex items-center justify-center gap-2 animate-pulse">
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
                        <span id="sim-lung-lbl" class="mono text-cyan-400 font-bold">0 kPa (0 cmH2O)</span>
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
                        seg.className = "led-segment led-yellow-on"; // Kam kuch (<38kg)
                    } else if (segPercent <= 0.88) {
                        seg.className = "led-segment led-green-on";  // Target Zone (38-55kg)
                    } else {
                        seg.className = "led-segment led-red-on";    // Ortiqcha kuch (>55kg)
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
            document.getElementById("lung-val-text").innerText = `${lungKpa.toFixed(1)} kPa`;

            // 3. Airway Pulse LED (Nafas kurganda)
            const airwayLed = document.getElementById("led-airway");
            if (lungKpa > 0.8) {
                airwayLed.classList.add("airway-led-on");
            } else {
                airwayLed.classList.remove("airway-led-on");
            }
        }

        // ==================== UPDATE POSITION, INJECTION & STOMACH LEDS ====================
        function updateIndicators(posBtn, stomachKpa, injBtn) {
            // Position LED (Chest Center - Pin 13)
            const posLed = document.getElementById("led-position");
            const posLbl = document.getElementById("pos-btn-text");
            if (posBtn === 1 || posBtn === true) {
                posLed.classList.add("pos-led-on");
                if (posLbl) {
                    posLbl.innerText = "BOSILDI (TO'G'RI)";
                    posLbl.className = "text-emerald-400 font-bold";
                }
            } else {
                posLed.classList.remove("pos-led-on");
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
                injLed.classList.add("inj-led-on");
                alertBox.classList.remove("hidden");
                alertBox.className = "mt-2 p-2 rounded-lg bg-purple-100 border border-purple-400 text-purple-900 text-xs font-bold text-center flex items-center justify-center gap-2 animate-pulse";
                alertText.innerText = "💉 INYEKSIYA (UKOL TOMIRGA KIRDI!)";
            } else {
                injLed.classList.remove("inj-led-on");
            }

            // Stomach Warning LED
            const stomachLed = document.getElementById("led-stomach");
            if (stomachKpa > 0.6) {
                stomachLed.classList.add("stomach-led-on");
                alertBox.classList.remove("hidden");
                alertBox.className = "mt-2 p-2 rounded-lg bg-rose-100 border border-rose-400 text-rose-900 text-xs font-bold text-center flex items-center justify-center gap-2 animate-pulse";
                alertText.innerText = `⚠️ HAVO OSHQOZONDA! (${stomachKpa.toFixed(1)} kPa)`;
            } else {
                stomachLed.classList.remove("stomach-led-on");
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
            const cm = (l * 10.2).toFixed(0);
            document.getElementById("sim-lung-lbl").innerText = `${l.toFixed(1)} kPa (${cm} cmH2O)`;

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

@app.get("/manikin_photo.png")
async def get_photo():
    photo_path = os.path.join(os.path.dirname(__file__), "manikin_photo.png")
    if os.path.exists(photo_path):
        return FileResponse(photo_path, media_type="image/png")
    return JSONResponse(content={"error": "Photo not found"}, status_code=404)

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
