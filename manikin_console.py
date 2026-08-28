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

app = FastAPI(title="Bemor Maniken Test va Imtihon Pulti")

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
    <title>Bemor Maniken Test va Imtihon Pulti (30:2 CPR Standart)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@400;600;700;900&display=swap');

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

        /* Real-world Backlit LED Illuminations on the Image */
        .photo-led {
            border-radius: 50%;
            position: absolute;
            transform: translate(-50%, -50%);
            pointer-events: auto;
            cursor: pointer;
            transition: all 0.12s ease-out;
            opacity: 0;
        }

        /* Chest Center (PIN 13) Backlit Green LED */
        .pos-led-on {
            opacity: 1 !important;
            background: radial-gradient(circle, rgba(74, 222, 128, 0.95) 15%, rgba(34, 197, 94, 0.85) 60%, rgba(34, 197, 94, 0.4) 100%) !important;
            mix-blend-mode: screen;
            box-shadow: 0 0 25px #22c55e, 0 0 50px #22c55e, 0 0 80px rgba(34, 197, 94, 0.8) !important;
            border: 2px solid rgba(255, 255, 255, 0.95) !important;
            animation: ledPulse 0.35s infinite alternate;
        }

        /* Injection Arm (PIN 4) Backlit Purple LED */
        .inj-led-on {
            opacity: 1 !important;
            background: radial-gradient(circle, rgba(192, 132, 252, 0.95) 15%, rgba(168, 85, 247, 0.85) 60%, rgba(168, 85, 247, 0.4) 100%) !important;
            mix-blend-mode: screen;
            box-shadow: 0 0 30px #a855f7, 0 0 60px #c084fc, 0 0 90px rgba(168, 85, 247, 0.8) !important;
            border: 2px solid rgba(255, 255, 255, 0.95) !important;
            animation: ledPulse 0.25s infinite alternate;
        }

        /* Airway Throat Backlit Cyan LED */
        .airway-led-on {
            opacity: 1 !important;
            background: radial-gradient(circle, rgba(56, 189, 248, 0.95) 15%, rgba(6, 182, 212, 0.85) 60%, rgba(6, 182, 212, 0.4) 100%) !important;
            mix-blend-mode: screen;
            box-shadow: 0 0 25px #06b6d4, 0 0 50px #06b6d4, 0 0 75px rgba(6, 182, 212, 0.8) !important;
            border: 2px solid rgba(255, 255, 255, 0.95) !important;
        }

        /* Stomach Warning Flashing Red */
        .stomach-led-on {
            opacity: 1 !important;
            background: radial-gradient(ellipse, rgba(239, 68, 68, 0.95) 10%, rgba(239, 68, 68, 0.7) 60%, transparent 100%) !important;
            mix-blend-mode: screen;
            box-shadow: 0 0 30px #ef4444, 0 0 60px #ef4444 !important;
            animation: blinkFast 0.2s infinite;
        }

        @keyframes ledPulse {
            0% { transform: translate(-50%, -50%) scale(1); filter: brightness(1); }
            100% { transform: translate(-50%, -50%) scale(1.1); filter: brightness(1.35); }
        }

        @keyframes blinkFast {
            0%, 100% { opacity: 1; filter: brightness(1.5); }
            50% { opacity: 0.2; filter: brightness(0.5); }
        }
    </style>
</head>
<body class="min-h-screen flex flex-col items-center justify-center p-2 sm:p-4">

    <!-- Top Connection & Mode Switcher Bar -->
    <div class="w-full max-w-2xl flex items-center justify-between mb-2 text-slate-300 text-xs px-2">
        <div class="flex items-center gap-2">
            <span id="conn-dot" class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
            <span id="conn-status" class="font-bold text-slate-200">ESP32 UART: Kutish holatida</span>
        </div>

        <!-- Mode Buttons (Erkin Mashq vs 30:2 Imtihon) -->
        <div class="flex items-center gap-1.5 bg-slate-800/80 p-1 rounded-xl border border-slate-700">
            <button id="tab-practice" onclick="switchMode('practice')" class="px-3 py-1 rounded-lg font-bold text-xs bg-indigo-600 text-white transition shadow">
                🔘 Erkin Mashq
            </button>
            <button id="tab-exam" onclick="switchMode('exam')" class="px-3 py-1 rounded-lg font-bold text-xs bg-slate-700 text-slate-300 hover:bg-slate-600 transition">
                🎓 30:2 Imtihon Rejimi
            </button>
        </div>

        <div class="flex items-center gap-2">
            <a href="/monitor" target="_blank" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-lg transition border border-slate-700 text-[11px]">
                <i class="fa-solid fa-heart-pulse text-indigo-400 mr-1"></i> Monitor
            </a>
            <a href="/" target="_blank" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-lg transition border border-slate-700 text-[11px]">
                <i class="fa-solid fa-user-doctor text-emerald-400 mr-1"></i> Bemor
            </a>
        </div>
    </div>

    <!-- EXAM MODE LIVE HUD BANNER (Faqat Imtihon Rejimida chiqadi) -->
    <div id="exam-hud-card" class="hidden w-full max-w-[560px] mb-2 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 border-2 border-indigo-500/80 rounded-2xl p-3 shadow-xl flex flex-col gap-2">
        <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
                <span class="px-2.5 py-0.5 rounded-full text-xs font-black bg-indigo-600 text-white tracking-wide uppercase flex items-center gap-1">
                    <i class="fa-solid fa-graduation-cap"></i> OSCE IMTIHON
                </span>
                <span id="exam-cycle-text" class="text-xs font-black text-amber-300">Tsikl: 1 / 5</span>
            </div>

            <!-- Timer Countdown -->
            <div class="flex items-center gap-2">
                <span class="text-xs text-slate-400 font-semibold">Qolgan vaqt:</span>
                <span id="exam-timer" class="mono text-lg font-black text-emerald-400 tracking-wider bg-black/60 px-2 py-0.5 rounded-lg border border-slate-700">02:00</span>
            </div>
        </div>

        <!-- 30:2 Live Progress Tracker -->
        <div class="grid grid-cols-2 gap-3 items-center bg-black/40 p-2 rounded-xl border border-slate-800">
            
            <!-- 1. Compressions Counter [ /30] -->
            <div class="flex flex-col">
                <div class="flex justify-between items-center text-xs font-bold text-slate-300 mb-0.5">
                    <span><i class="fa-solid fa-hand-fist text-indigo-400 mr-1"></i> Kompressiya (30 ta):</span>
                    <span id="exam-comp-num" class="mono font-black text-amber-400 text-sm">0 / 30</span>
                </div>
                <div class="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                    <div id="exam-comp-bar" class="bg-amber-500 h-full rounded-full transition-all duration-75" style="width: 0%;"></div>
                </div>
            </div>

            <!-- 2. Ventilation Counter [ /2] -->
            <div class="flex flex-col">
                <div class="flex justify-between items-center text-xs font-bold text-slate-300 mb-0.5">
                    <span><i class="fa-solid fa-lungs text-cyan-400 mr-1"></i> Nafas (2 ta):</span>
                    <span id="exam-vent-num" class="mono font-black text-cyan-400 text-sm">0 / 2</span>
                </div>
                <div class="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                    <div id="exam-vent-bar" class="bg-cyan-500 h-full rounded-full transition-all duration-75" style="width: 0%;"></div>
                </div>
            </div>

        </div>

        <!-- Live Instructor Prompt -->
        <div class="flex items-center justify-between px-1">
            <div id="exam-instruction-text" class="text-xs font-bold text-emerald-300 flex items-center gap-1.5 animate-pulse">
                <i class="fa-solid fa-circle-info"></i> 1-tsikl: Ko'krak markazini 30 marta bosing!
            </div>
            
            <!-- Start / Stop Button -->
            <button id="btn-exam-toggle" onclick="toggleExamState()" class="px-3 py-1 rounded-lg font-black text-xs bg-emerald-500 hover:bg-emerald-600 text-slate-900 transition shadow flex items-center gap-1">
                <i class="fa-solid fa-play"></i> Boshlash
            </button>
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
                        <div id="led-airway" class="photo-led top-[33.74%] left-[50.85%] w-[6.5%] h-[4.5%] flex items-center justify-center pointer-events-none">
                        </div>

                        <!-- 2. Chest Center Position LED (NUQTA PIN 13) -->
                        <div id="led-position" onclick="toggleSimPos()" class="photo-led top-[56.30%] left-[50.85%] w-[8.2%] h-[5.7%] flex items-center justify-center" title="Qo'l nuqtasi (Pin 13)">
                        </div>

                        <!-- 3. Right Arm Injection LED (UKOL PIN 4) -->
                        <div id="led-injection" onclick="triggerSimInj()" class="photo-led top-[68.41%] left-[91.58%] w-[9.0%] h-[6.2%] flex items-center justify-center" title="Ukol / Inyeksiya (Pin 4)">
                        </div>

                        <!-- 4. Stomach Warning LED (OSHQOZON) -->
                        <div id="led-stomach" class="photo-led top-[93.0%] left-[51.0%] w-[18.0%] h-[4.5%] flex items-center justify-center pointer-events-none" title="Oshqozon bosimi" style="border-radius: 6px;">
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

    <!-- ==================== EXAM RESULTS MODAL SCORECARD (OSCE PROTOKOL) ==================== -->
    <div id="exam-modal" class="fixed inset-0 bg-black/85 backdrop-blur-md flex items-center justify-center p-4 z-50 hidden">
        <div class="bg-slate-900 border-2 border-indigo-500 rounded-3xl max-w-lg w-full p-5 sm:p-6 shadow-2xl text-white flex flex-col gap-4">
            
            <div class="text-center border-b border-slate-800 pb-3">
                <span id="modal-status-badge" class="px-4 py-1 rounded-full text-xs font-black uppercase tracking-widest bg-emerald-500/20 text-emerald-400 border border-emerald-500 inline-block mb-2">
                    🏆 IMTIHONDAN O'TDI (PASSED)
                </span>
                <h2 class="text-xl font-black text-slate-100">CPR REANIMATSIYA IMTIHONI NATIJASI</h2>
                <p class="text-xs text-slate-400">Xalqaro AHA/ERC 30:2 Standart Protokoli</p>
            </div>

            <!-- Total Score & Grade -->
            <div class="flex items-center justify-between bg-slate-800/80 p-4 rounded-2xl border border-slate-700">
                <div>
                    <div class="text-xs text-slate-400 font-semibold">Umumiy CPR Sifat Balli:</div>
                    <div id="modal-total-score" class="mono text-3xl font-black text-emerald-400">92%</div>
                </div>
                <div class="text-right">
                    <div class="text-xs text-slate-400 font-semibold">Sarflangan Vaqt:</div>
                    <div id="modal-time-spent" class="mono text-lg font-bold text-amber-300">01:52 soniya</div>
                </div>
            </div>

            <!-- Detailed Breakdown Metrics -->
            <div class="grid grid-cols-2 gap-2 text-xs">
                
                <div class="bg-slate-800/50 p-2.5 rounded-xl border border-slate-700/60">
                    <div class="text-slate-400 font-medium">🎯 Qo'l Nuqtasi Aniqligi:</div>
                    <div id="modal-pos-acc" class="mono font-bold text-emerald-400 text-sm mt-0.5">96%</div>
                </div>

                <div class="bg-slate-800/50 p-2.5 rounded-xl border border-slate-700/60">
                    <div class="text-slate-400 font-medium">🏋️ To'g'ri Chuqurlik (38-55kg):</div>
                    <div id="modal-depth-acc" class="mono font-bold text-emerald-400 text-sm mt-0.5">88%</div>
                </div>

                <div class="bg-slate-800/50 p-2.5 rounded-xl border border-slate-700/60">
                    <div class="text-slate-400 font-medium">🔄 To'liq Bo'shatish (Recoil):</div>
                    <div id="modal-recoil-acc" class="mono font-bold text-emerald-400 text-sm mt-0.5">100%</div>
                </div>

                <div class="bg-slate-800/50 p-2.5 rounded-xl border border-slate-700/60">
                    <div class="text-slate-400 font-medium">⏱️ O'rtacha Tezlik (BPM):</div>
                    <div id="modal-bpm-avg" class="mono font-bold text-amber-300 text-sm mt-0.5">112 /min</div>
                </div>

                <div class="bg-slate-800/50 p-2.5 rounded-xl border border-slate-700/60">
                    <div class="text-slate-400 font-medium">🫁 To'g'ri Nafas (2.0-3.0 kPa):</div>
                    <div id="modal-vent-acc" class="mono font-bold text-cyan-400 text-sm mt-0.5">9 / 10 ta</div>
                </div>

                <div class="bg-slate-800/50 p-2.5 rounded-xl border border-slate-700/60">
                    <div class="text-slate-400 font-medium">⚠️ Oshqozon Xatolari:</div>
                    <div id="modal-stomach-errs" class="mono font-bold text-rose-400 text-sm mt-0.5">0 ta (A'lo)</div>
                </div>

            </div>

            <!-- Modal Action Buttons -->
            <div class="flex items-center gap-3 mt-1">
                <button onclick="restartExam()" class="flex-1 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-bold text-xs text-white transition shadow flex items-center justify-center gap-2">
                    <i class="fa-solid fa-rotate-right"></i> Qayta Topshirish
                </button>
                <button onclick="closeModal()" class="py-2.5 px-4 rounded-xl bg-slate-700 hover:bg-slate-600 font-bold text-xs text-slate-200 transition">
                    Yopish
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

        // ==================== EXAM MODE ENGINE (30:2 PROTOCOL) ====================
        let currentAppMode = "practice"; // "practice" or "exam"
        let isExamActive = false;
        let examTimerInterval = null;
        let examTimeLeft = 120; // 2 minutes (120 seconds)
        let examCycle = 1;      // 1 to 5
        let examStage = "compress"; // "compress" (30 times) or "ventilate" (2 times)
        let examCompCount = 0;  // 0 to 30
        let examVentCount = 0;  // 0 to 2

        // Exam Statistics for Scoring
        let stats = {
            totalComps: 0,
            correctDepth: 0,
            correctPos: 0,
            correctRecoil: 0,
            totalVents: 0,
            correctVents: 0,
            stomachErrors: 0,
            strokeTimes: []
        };

        function switchMode(mode) {
            currentAppMode = mode;
            const tabPrac = document.getElementById("tab-practice");
            const tabExam = document.getElementById("tab-exam");
            const hudCard = document.getElementById("exam-hud-card");

            if (mode === "exam") {
                tabExam.className = "px-3 py-1 rounded-lg font-bold text-xs bg-indigo-600 text-white transition shadow";
                tabPrac.className = "px-3 py-1 rounded-lg font-bold text-xs bg-slate-700 text-slate-300 hover:bg-slate-600 transition";
                hudCard.classList.remove("hidden");
                resetExamState();
            } else {
                tabPrac.className = "px-3 py-1 rounded-lg font-bold text-xs bg-indigo-600 text-white transition shadow";
                tabExam.className = "px-3 py-1 rounded-lg font-bold text-xs bg-slate-700 text-slate-300 hover:bg-slate-600 transition";
                hudCard.classList.add("hidden");
                if (isExamActive) toggleExamState();
            }
        }

        function resetExamState() {
            if (examTimerInterval) clearInterval(examTimerInterval);
            isExamActive = false;
            examTimeLeft = 120;
            examCycle = 1;
            examStage = "compress";
            examCompCount = 0;
            examVentCount = 0;

            stats = {
                totalComps: 0,
                correctDepth: 0,
                correctPos: 0,
                correctRecoil: 0,
                totalVents: 0,
                correctVents: 0,
                stomachErrors: 0,
                strokeTimes: []
            };

            updateExamUI();
            const btn = document.getElementById("btn-exam-toggle");
            btn.innerHTML = '<i class="fa-solid fa-play"></i> Boshlash';
            btn.className = "px-3 py-1 rounded-lg font-black text-xs bg-emerald-500 hover:bg-emerald-600 text-slate-900 transition shadow flex items-center gap-1";
            document.getElementById("exam-instruction-text").innerText = "Tayyormisiz? 'Boshlash' tugmasini bosing!";
        }

        function toggleExamState() {
            if (!isExamActive) {
                // START EXAM
                resetExamState();
                isExamActive = true;
                const btn = document.getElementById("btn-exam-toggle");
                btn.innerHTML = '<i class="fa-solid fa-stop"></i> To\'xtatish';
                btn.className = "px-3 py-1 rounded-lg font-black text-xs bg-rose-500 hover:bg-rose-600 text-white transition shadow flex items-center gap-1";

                document.getElementById("exam-instruction-text").innerText = `1-tsikl: Ko'krakni 30 marta bosing!`;

                examTimerInterval = setInterval(() => {
                    examTimeLeft--;
                    updateTimerDisplay();
                    if (examTimeLeft <= 0) {
                        finishExam();
                    }
                }, 1000);
            } else {
                // STOP EXAM
                resetExamState();
            }
        }

        function updateTimerDisplay() {
            const mins = Math.floor(examTimeLeft / 60);
            const secs = examTimeLeft % 60;
            const str = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
            const el = document.getElementById("exam-timer");
            el.innerText = str;
            if (examTimeLeft <= 20) {
                el.className = "mono text-lg font-black text-rose-400 tracking-wider bg-rose-950/60 px-2 py-0.5 rounded-lg border border-rose-600 animate-pulse";
            } else {
                el.className = "mono text-lg font-black text-emerald-400 tracking-wider bg-black/60 px-2 py-0.5 rounded-lg border border-slate-700";
            }
        }

        function updateExamUI() {
            document.getElementById("exam-cycle-text").innerText = `Tsikl: ${examCycle} / 5`;
            document.getElementById("exam-comp-num").innerText = `${examCompCount} / 30`;
            document.getElementById("exam-comp-bar").style.width = `${(examCompCount / 30) * 100}%`;

            document.getElementById("exam-vent-num").innerText = `${examVentCount} / 2`;
            document.getElementById("exam-vent-bar").style.width = `${(examVentCount / 2) * 100}%`;
            updateTimerDisplay();
        }

        function finishExam() {
            if (examTimerInterval) clearInterval(examTimerInterval);
            isExamActive = false;

            // Calculate Final Scores
            const totalComps = stats.totalComps || 1;
            const posAcc = Math.round((stats.correctPos / totalComps) * 100);
            const depthAcc = Math.round((stats.correctDepth / totalComps) * 100);
            const recoilAcc = Math.round((stats.correctRecoil / totalComps) * 100);
            
            // Average BPM
            let avgBpm = 110;
            if (stats.strokeTimes.length > 2) {
                let deltas = [];
                for (let i = 1; i < stats.strokeTimes.length; i++) {
                    const d = stats.strokeTimes[i] - stats.strokeTimes[i-1];
                    if (d > 200 && d < 1500) deltas.push(d);
                }
                if (deltas.length > 0) {
                    const avgDelta = deltas.reduce((a, b) => a + b, 0) / deltas.length;
                    avgBpm = Math.round(60000 / avgDelta);
                }
            }

            const totalVents = stats.totalVents || 1;
            const ventAcc = `${stats.correctVents} / ${Math.max(stats.totalVents, examCycle * 2)} ta`;

            // Weighted Overall Score (100% max)
            const overallScore = Math.min(100, Math.round(
                (posAcc * 0.25) + (depthAcc * 0.35) + (recoilAcc * 0.15) + 
                ((stats.correctVents / Math.max(1, examCycle * 2)) * 100 * 0.25) - 
                (stats.stomachErrors * 5)
            ));

            // Populate Scorecard
            document.getElementById("modal-total-score").innerText = `${Math.max(0, overallScore)}%`;
            document.getElementById("modal-time-spent").innerText = `${120 - examTimeLeft} soniya`;
            document.getElementById("modal-pos-acc").innerText = `${posAcc}%`;
            document.getElementById("modal-depth-acc").innerText = `${depthAcc}%`;
            document.getElementById("modal-recoil-acc").innerText = `${recoilAcc}%`;
            document.getElementById("modal-bpm-avg").innerText = `${avgBpm} /min`;
            document.getElementById("modal-vent-acc").innerText = ventAcc;
            document.getElementById("modal-stomach-errs").innerText = `${stats.stomachErrors} ta`;

            const badge = document.getElementById("modal-status-badge");
            if (overallScore >= 80 && examCycle >= 3) {
                badge.innerText = "🏆 IMTIHONDAN O'TDI (PASSED)";
                badge.className = "px-4 py-1 rounded-full text-xs font-black uppercase tracking-widest bg-emerald-500/20 text-emerald-400 border border-emerald-500 inline-block mb-2";
            } else {
                badge.innerText = "❌ YIQILDI (FAILED)";
                badge.className = "px-4 py-1 rounded-full text-xs font-black uppercase tracking-widest bg-rose-500/20 text-rose-400 border border-rose-500 inline-block mb-2";
            }

            document.getElementById("exam-modal").classList.remove("hidden");
        }

        function closeModal() {
            document.getElementById("exam-modal").classList.add("hidden");
            resetExamState();
        }

        function restartExam() {
            closeModal();
            toggleExamState();
        }

        // ==================== CPR PEAK & VENTILATION PROCESSOR ====================
        let cprStrokeState = "idle";
        let cprPeak = 0;
        let cprPosAtPeak = false;

        function processExamHardware(forceKg, lungKpa, stomachKpa, posBtn) {
            if (!isExamActive) return;

            const now = Date.now();

            // 1. Process Compression Strokes
            if (cprStrokeState === "idle") {
                if (forceKg > 5.0) {
                    cprStrokeState = "compressing";
                    cprPeak = forceKg;
                    cprPosAtPeak = (posBtn === 1 || posBtn === true);
                }
            } else if (cprStrokeState === "compressing") {
                if (forceKg > cprPeak) {
                    cprPeak = forceKg;
                    if (posBtn === 1 || posBtn === true) cprPosAtPeak = true;
                }
                if (forceKg < (cprPeak - 4.0)) {
                    // STROKE FINISHED
                    cprStrokeState = "recoiling";
                    stats.totalComps++;
                    stats.strokeTimes.push(now);

                    const isDepthOk = (cprPeak >= 38.0 && cprPeak <= 55.0);
                    if (isDepthOk) stats.correctDepth++;
                    if (cprPosAtPeak) stats.correctPos++;

                    if (examStage === "compress") {
                        examCompCount++;
                        updateExamUI();

                        if (examCompCount >= 30) {
                            // SWITCH TO VENTILATION STAGE
                            examStage = "ventilate";
                            examCompCount = 30;
                            examVentCount = 0;
                            updateExamUI();
                            document.getElementById("exam-instruction-text").innerText = `🫁 30 ta bo'ldi! Endi 2 ta Ambu nafasi bering!`;
                        }
                    }
                }
            } else if (cprStrokeState === "recoiling") {
                if (forceKg <= 5.0) {
                    stats.correctRecoil++;
                    cprStrokeState = "idle";
                } else if (forceKg > (cprPeak - 1.0) && forceKg > 5.0) {
                    // Failed recoil
                    cprStrokeState = "compressing";
                    cprPeak = forceKg;
                }
            }

            // 2. Process Ventilation Breath
            if (examStage === "ventilate") {
                if (lungKpa >= 2.0 && !window._ventTriggered) {
                    window._ventTriggered = true;
                    stats.totalVents++;
                    if (lungKpa >= 2.0 && lungKpa <= 3.0) stats.correctVents++;
                    examVentCount++;
                    updateExamUI();

                    if (examVentCount >= 2) {
                        // CYCLE COMPLETE!
                        if (examCycle < 5) {
                            examCycle++;
                            examStage = "compress";
                            examCompCount = 0;
                            examVentCount = 0;
                            updateExamUI();
                            document.getElementById("exam-instruction-text").innerText = `🏋️ ${examCycle}-tsikl boshlandi: 30 marta bosing!`;
                        } else {
                            // ALL 5 CYCLES COMPLETE!
                            finishExam();
                        }
                    }
                } else if (lungKpa < 0.6) {
                    window._ventTriggered = false;
                }
            }

            // 3. Stomach Warning Errors
            if (stomachKpa > 0.8 && !window._stomachTriggered) {
                window._stomachTriggered = true;
                stats.stomachErrors++;
            } else if (stomachKpa < 0.3) {
                window._stomachTriggered = false;
            }
        }

        // ==================== RENDER LED BARS ====================
        function renderBars(forceKg, lungKpa) {
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
                    processExamHardware(force, lungP, stomachP, posBtn);
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
            processExamHardware(f, l, simStomach, simPos);
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
    print("  🎓 BEMOR MANIKEN TEST VA IMTIHON PULTI (30:2 CPR OSCE)")
    print("=" * 68)
    print(f"  Kompyuterda ochish:   http://localhost:{port}")
    print(f"  Boshqa qurilmalarda:  http://{local_ip}:{port}")
    print("=" * 68 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
