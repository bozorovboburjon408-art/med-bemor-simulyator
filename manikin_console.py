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
    <title>Bemor Maniken Test va Imtihon Pulti</title>
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

        <!-- Mode Buttons (Erkin Mashq vs Imtihon Rejimi) -->
        <div class="flex items-center gap-1.5 bg-slate-800/80 p-1 rounded-xl border border-slate-700">
            <button id="tab-practice" onclick="switchMode('practice')" class="px-3 py-1 rounded-lg font-bold text-xs bg-indigo-600 text-white transition shadow">
                🔘 Erkin Mashq
            </button>
            <button id="tab-exam" onclick="switchMode('exam')" class="px-3 py-1 rounded-lg font-bold text-xs bg-slate-700 text-slate-300 hover:bg-slate-600 transition flex items-center gap-1.5">
                <i class="fa-solid fa-clipboard-check text-amber-400"></i> Imtihon / Baholash
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

    <!-- EXAM MODE LIVE ASSESSMENT HUD (Real-Vaqtda Hisoblagich va To'g'ri/Xato Tahlili) -->
    <div id="exam-hud-card" class="hidden w-full max-w-[560px] mb-2 bg-gradient-to-br from-slate-900 via-indigo-950/80 to-slate-900 border-2 border-indigo-500/80 rounded-2xl p-3 shadow-2xl flex flex-col gap-2.5">
        
        <!-- Header with Timer and Control -->
        <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
                <span class="px-2.5 py-0.5 rounded-full text-xs font-black bg-indigo-600 text-white tracking-wide uppercase flex items-center gap-1">
                    <i class="fa-solid fa-stopwatch"></i> IMTIHON JARAYONI
                </span>
                <span id="exam-live-feedback" class="text-xs font-bold text-amber-300">Tayyor</span>
            </div>

            <!-- Timer & Actions -->
            <div class="flex items-center gap-2">
                <span id="exam-timer" class="mono text-lg font-black text-emerald-400 tracking-wider bg-black/70 px-2.5 py-0.5 rounded-lg border border-slate-700">02:00</span>
                
                <button id="btn-exam-toggle" onclick="toggleExamState()" class="px-3 py-1 rounded-lg font-black text-xs bg-emerald-500 hover:bg-emerald-600 text-slate-900 transition shadow flex items-center gap-1">
                    <i class="fa-solid fa-play"></i> Boshlash
                </button>
                <button id="btn-exam-finish" onclick="finishExamManually()" class="hidden px-2.5 py-1 rounded-lg font-bold text-xs bg-indigo-600 hover:bg-indigo-500 text-white transition shadow flex items-center gap-1">
                    Yakunlash
                </button>
            </div>
        </div>

        <!-- 4 REAL-TIME SCORE BOXES (Jami Bosildi, To'g'ri, Xato, Nafas) -->
        <div class="grid grid-cols-4 gap-2 text-center">
            
            <!-- 1. Total Compressions Attempted -->
            <div class="bg-black/50 p-2 rounded-xl border border-slate-700">
                <div class="text-[10px] font-bold text-slate-400 uppercase tracking-tight">Jami Bosildi</div>
                <div id="stat-total-comps" class="mono text-xl font-black text-white mt-0.5">0</div>
                <div class="text-[9px] text-slate-400">zarba</div>
            </div>

            <!-- 2. Correct Compressions (To'g'ri) -->
            <div class="bg-emerald-950/40 p-2 rounded-xl border border-emerald-600/60">
                <div class="text-[10px] font-bold text-emerald-400 uppercase tracking-tight">To'g'ri</div>
                <div id="stat-correct-comps" class="mono text-xl font-black text-emerald-400 mt-0.5">0</div>
                <div id="stat-correct-pct" class="text-[9px] text-emerald-300 font-bold">0%</div>
            </div>

            <!-- 3. Errors / Faults (Xatolar) -->
            <div class="bg-rose-950/40 p-2 rounded-xl border border-rose-600/60">
                <div class="text-[10px] font-bold text-rose-400 uppercase tracking-tight">Xatolar</div>
                <div id="stat-wrong-comps" class="mono text-xl font-black text-rose-400 mt-0.5">0</div>
                <div id="stat-wrong-reasons" class="text-[9px] text-rose-300 truncate">0 ta</div>
            </div>

            <!-- 4. Breaths / Ventilations (O'pka nafasi) -->
            <div class="bg-cyan-950/40 p-2 rounded-xl border border-cyan-600/60">
                <div class="text-[10px] font-bold text-cyan-400 uppercase tracking-tight">Nafas</div>
                <div id="stat-total-vents" class="mono text-xl font-black text-cyan-400 mt-0.5">0</div>
                <div id="stat-vent-status" class="text-[9px] text-cyan-300">0 to'g'ri</div>
            </div>

        </div>

        <!-- Live Quality Percentage Bar -->
        <div class="flex flex-col gap-1 bg-black/40 p-2 rounded-xl border border-slate-800">
            <div class="flex justify-between items-center text-xs font-bold">
                <span class="text-slate-300">CPR Umumiy Sifat Darajasi:</span>
                <span id="stat-live-quality" class="mono font-black text-emerald-400 text-sm">100%</span>
            </div>
            <div class="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div id="stat-quality-bar" class="bg-emerald-500 h-full rounded-full transition-all duration-150" style="width: 100%;"></div>
            </div>
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

    <!-- ==================== EXAM RESULTS MODAL SCORECARD (KLINIK PROTOKOL) ==================== -->
    <div id="exam-modal" class="fixed inset-0 bg-black/85 backdrop-blur-md flex items-center justify-center p-4 z-50 hidden">
        <div class="bg-slate-900 border-2 border-indigo-500 rounded-3xl max-w-lg w-full p-5 sm:p-6 shadow-2xl text-white flex flex-col gap-4">
            
            <div class="text-center border-b border-slate-800 pb-3">
                <span id="modal-status-badge" class="px-4 py-1 rounded-full text-xs font-black uppercase tracking-widest bg-emerald-500/20 text-emerald-400 border border-emerald-500 inline-block mb-2">
                    🏆 IMTIHONDAN O'TDI (PASSED)
                </span>
                <h2 class="text-xl font-black text-slate-100">CPR IMTIHON VA BAHOLASH PROTOKOLI</h2>
                <p class="text-xs text-slate-400">Amaliy Tibbiy Ko'nikmalarni Tekshirish Natijalari</p>
            </div>

            <!-- Total Score & Grade -->
            <div class="flex items-center justify-between bg-slate-800/80 p-4 rounded-2xl border border-slate-700">
                <div>
                    <div class="text-xs text-slate-400 font-semibold">Umumiy Sifat Bahosi:</div>
                    <div id="modal-total-score" class="mono text-3xl font-black text-emerald-400">92%</div>
                </div>
                <div class="text-right">
                    <div class="text-xs text-slate-400 font-semibold">Sarflangan Vaqt:</div>
                    <div id="modal-time-spent" class="mono text-lg font-bold text-amber-300">01:52 soniya</div>
                </div>
            </div>

            <!-- Detailed Breakdown Metrics (Jami, To'g'ri, Xato, Xatolar sababi) -->
            <div class="grid grid-cols-2 gap-2 text-xs">
                
                <div class="bg-slate-800/50 p-2.5 rounded-xl border border-slate-700/60">
                    <div class="text-slate-400 font-medium">🔢 Jami Kompressiyalar:</div>
                    <div id="modal-total-comps" class="mono font-bold text-white text-sm mt-0.5">30 ta</div>
                </div>

                <div class="bg-slate-800/50 p-2.5 rounded-xl border border-slate-700/60">
                    <div class="text-emerald-400 font-medium">✅ To'g'ri Bajarilgani:</div>
                    <div id="modal-correct-comps" class="mono font-bold text-emerald-400 text-sm mt-0.5">26 ta (87%)</div>
                </div>

                <div class="bg-slate-800/50 p-2.5 rounded-xl border border-slate-700/60">
                    <div class="text-rose-400 font-medium">❌ Xato Bajarilgani:</div>
                    <div id="modal-wrong-comps" class="mono font-bold text-rose-400 text-sm mt-0.5">4 ta</div>
                </div>

                <div class="bg-slate-800/50 p-2.5 rounded-xl border border-slate-700/60">
                    <div class="text-slate-400 font-medium">⏱️ O'rtacha Tezlik (BPM):</div>
                    <div id="modal-bpm-avg" class="mono font-bold text-amber-300 text-sm mt-0.5">112 /min</div>
                </div>

                <div class="bg-slate-800/50 p-2.5 rounded-xl border border-slate-700/60 col-span-2">
                    <div class="text-slate-400 font-medium mb-1">🔍 Xatolar Tafsiloti:</div>
                    <div id="modal-error-details" class="space-y-0.5 text-[11px] text-slate-300">
                        <!-- Filled by JS -->
                    </div>
                </div>

                <div class="bg-slate-800/50 p-2.5 rounded-xl border border-slate-700/60 col-span-2">
                    <div class="text-cyan-400 font-medium">🫁 O'pka Ventilyatsiyasi:</div>
                    <div id="modal-vent-summary" class="mono text-xs text-slate-200 mt-0.5">Jami: 2 ta | To'g'ri: 2 ta | Oshqozon: 0 ta</div>
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

        // ==================== REAL-WORLD EXAM & ASSESSMENT ENGINE ====================
        let currentAppMode = "practice"; // "practice" or "exam"
        let isExamActive = false;
        let examTimerInterval = null;
        let examTimeLeft = 120; // 2 minutes (120 seconds)

        // Real Action Counters
        let examStats = {
            totalComps: 0,      // Every single chest compression attempted
            correctComps: 0,    // Perfectly executed compressions (Correct point + Correct depth + Good recoil)
            wrongComps: 0,      // Faulty compressions
            
            // Error classifications
            shallowErrors: 0,   // Force < 38kg (Sayoz)
            excessErrors: 0,    // Force > 55kg (Ortiqcha kuchli)
            posErrors: 0,       // Hand not on sternum point (Pin 13 != 1)
            recoilErrors: 0,    // Did not release chest between strokes (<5kg)
            
            // Ventilations
            totalVents: 0,      // Total breaths given
            correctVents: 0,    // Breaths in 2.0 - 3.0 kPa
            stomachErrors: 0,   // Breaths went to stomach

            strokeTimes: []
        };

        function switchMode(mode) {
            currentAppMode = mode;
            const tabPrac = document.getElementById("tab-practice");
            const tabExam = document.getElementById("tab-exam");
            const hudCard = document.getElementById("exam-hud-card");

            if (mode === "exam") {
                tabExam.className = "px-3 py-1 rounded-lg font-bold text-xs bg-indigo-600 text-white transition shadow flex items-center gap-1.5";
                tabPrac.className = "px-3 py-1 rounded-lg font-bold text-xs bg-slate-700 text-slate-300 hover:bg-slate-600 transition";
                hudCard.classList.remove("hidden");
                resetExamState();
            } else {
                tabPrac.className = "px-3 py-1 rounded-lg font-bold text-xs bg-indigo-600 text-white transition shadow";
                tabExam.className = "px-3 py-1 rounded-lg font-bold text-xs bg-slate-700 text-slate-300 hover:bg-slate-600 transition flex items-center gap-1.5";
                hudCard.classList.add("hidden");
                if (isExamActive) toggleExamState();
            }
        }

        function resetExamState() {
            if (examTimerInterval) clearInterval(examTimerInterval);
            isExamActive = false;
            examTimeLeft = 120;

            examStats = {
                totalComps: 0,
                correctComps: 0,
                wrongComps: 0,
                shallowErrors: 0,
                excessErrors: 0,
                posErrors: 0,
                recoilErrors: 0,
                totalVents: 0,
                correctVents: 0,
                stomachErrors: 0,
                strokeTimes: []
            };

            updateExamHUD();
            const btn = document.getElementById("btn-exam-toggle");
            btn.innerHTML = '<i class="fa-solid fa-play"></i> Boshlash';
            btn.className = "px-3 py-1 rounded-lg font-black text-xs bg-emerald-500 hover:bg-emerald-600 text-slate-900 transition shadow flex items-center gap-1";
            document.getElementById("btn-exam-finish").classList.add("hidden");
            document.getElementById("exam-live-feedback").innerText = "Tayyor: 'Boshlash' tugmasini bosing!";
        }

        function toggleExamState() {
            if (!isExamActive) {
                // START EXAM
                resetExamState();
                isExamActive = true;
                const btn = document.getElementById("btn-exam-toggle");
                btn.innerHTML = '<i class="fa-solid fa-stop"></i> To\'xtatish';
                btn.className = "px-3 py-1 rounded-lg font-black text-xs bg-rose-500 hover:bg-rose-600 text-white transition shadow flex items-center gap-1";
                document.getElementById("btn-exam-finish").classList.remove("hidden");

                document.getElementById("exam-live-feedback").innerText = "Mashqni boshlang (Kompressiya va Nafas)!";

                examTimerInterval = setInterval(() => {
                    examTimeLeft--;
                    updateTimerDisplay();
                    if (examTimeLeft <= 0) {
                        finishExamManually();
                    }
                }, 1000);
            } else {
                // STOP EXAM
                resetExamState();
            }
        }

        function finishExamManually() {
            if (examTimerInterval) clearInterval(examTimerInterval);
            isExamActive = false;

            const total = examStats.totalComps || 1;
            const correct = examStats.correctComps;
            const correctPct = Math.round((correct / total) * 100);

            // Average BPM
            let avgBpm = 110;
            if (examStats.strokeTimes.length > 2) {
                let deltas = [];
                for (let i = 1; i < examStats.strokeTimes.length; i++) {
                    const d = examStats.strokeTimes[i] - examStats.strokeTimes[i-1];
                    if (d > 200 && d < 1500) deltas.push(d);
                }
                if (deltas.length > 0) {
                    const avgDelta = deltas.reduce((a, b) => a + b, 0) / deltas.length;
                    avgBpm = Math.round(60000 / avgDelta);
                }
            }

            // Overall Score
            let overallScore = correctPct;
            if (examStats.stomachErrors > 0) {
                overallScore = Math.max(0, overallScore - (examStats.stomachErrors * 5));
            }

            // Fill Modal
            document.getElementById("modal-total-score").innerText = `${overallScore}%`;
            document.getElementById("modal-time-spent").innerText = `${120 - examTimeLeft} soniya`;
            document.getElementById("modal-total-comps").innerText = `${examStats.totalComps} ta`;
            document.getElementById("modal-correct-comps").innerText = `${examStats.correctComps} ta (${correctPct}%)`;
            document.getElementById("modal-wrong-comps").innerText = `${examStats.wrongComps} ta`;
            document.getElementById("modal-bpm-avg").innerText = `${avgBpm} /min`;

            // Error details
            const errDiv = document.getElementById("modal-error-details");
            errDiv.innerHTML = `
                <div>• ⚠️ Sayoz bosilgan (<38 kg): <b>${examStats.shallowErrors} ta</b></div>
                <div>• ⚠️ Ortiqcha qattiq bosilgan (>55 kg): <b>${examStats.excessErrors} ta</b></div>
                <div>• ❌ Qo'l noto'g'ri joyda bosilgan: <b>${examStats.posErrors} ta</b></div>
                <div>• 🔄 Ko'krak to'liq bo'shatilmagan (recoil): <b>${examStats.recoilErrors} ta</b></div>
            `;

            document.getElementById("modal-vent-summary").innerText = 
                `Jami: ${examStats.totalVents} ta | To'g'ri (2.0-3.0 kPa): ${examStats.correctVents} ta | Oshqozon xatosi: ${examStats.stomachErrors} ta`;

            const badge = document.getElementById("modal-status-badge");
            if (overallScore >= 80 && examStats.totalComps >= 20) {
                badge.innerText = "🏆 IMTIHONDAN O'TDI (PASSED)";
                badge.className = "px-4 py-1 rounded-full text-xs font-black uppercase tracking-widest bg-emerald-500/20 text-emerald-400 border border-emerald-500 inline-block mb-2";
            } else {
                badge.innerText = "❌ YIQILDI (FAILED)";
                badge.className = "px-4 py-1 rounded-full text-xs font-black uppercase tracking-widest bg-rose-500/20 text-rose-400 border border-rose-500 inline-block mb-2";
            }

            document.getElementById("exam-modal").classList.remove("hidden");
        }

        function updateTimerDisplay() {
            const mins = Math.floor(examTimeLeft / 60);
            const secs = examTimeLeft % 60;
            const str = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
            const el = document.getElementById("exam-timer");
            el.innerText = str;
            if (examTimeLeft <= 20) {
                el.className = "mono text-lg font-black text-rose-400 tracking-wider bg-rose-950/70 px-2.5 py-0.5 rounded-lg border border-rose-600 animate-pulse";
            } else {
                el.className = "mono text-lg font-black text-emerald-400 tracking-wider bg-black/70 px-2.5 py-0.5 rounded-lg border border-slate-700";
            }
        }

        function updateExamHUD() {
            // 1. Total Compressions
            document.getElementById("stat-total-comps").innerText = examStats.totalComps;

            // 2. Correct Compressions
            document.getElementById("stat-correct-comps").innerText = examStats.correctComps;
            const total = examStats.totalComps;
            const pct = total > 0 ? Math.round((examStats.correctComps / total) * 100) : 100;
            document.getElementById("stat-correct-pct").innerText = `${pct}% to'g'ri`;

            // 3. Wrong Compressions
            document.getElementById("stat-wrong-comps").innerText = examStats.wrongComps;
            document.getElementById("stat-wrong-reasons").innerText = `${examStats.wrongComps} ta xato`;

            // 4. Ventilations
            document.getElementById("stat-total-vents").innerText = examStats.totalVents;
            document.getElementById("stat-vent-status").innerText = `${examStats.correctVents} to'g'ri`;

            // Quality bar
            document.getElementById("stat-live-quality").innerText = `${pct}%`;
            document.getElementById("stat-quality-bar").style.width = `${pct}%`;

            if (pct >= 80) {
                document.getElementById("stat-quality-bar").className = "bg-emerald-500 h-full rounded-full transition-all duration-150";
                document.getElementById("stat-live-quality").className = "mono font-black text-emerald-400 text-sm";
            } else if (pct >= 50) {
                document.getElementById("stat-quality-bar").className = "bg-yellow-500 h-full rounded-full transition-all duration-150";
                document.getElementById("stat-live-quality").className = "mono font-black text-yellow-400 text-sm";
            } else {
                document.getElementById("stat-quality-bar").className = "bg-rose-500 h-full rounded-full transition-all duration-150";
                document.getElementById("stat-live-quality").className = "mono font-black text-rose-400 text-sm";
            }

            updateTimerDisplay();
        }

        function closeModal() {
            document.getElementById("exam-modal").classList.add("hidden");
            resetExamState();
        }

        function restartExam() {
            closeModal();
            toggleExamState();
        }

        // ==================== REAL ACTION STROKE ANALYZER ====================
        let cprStrokeState = "idle";
        let cprPeak = 0;
        let cprPosAtPeak = false;

        function processExamHardware(forceKg, lungKpa, stomachKpa, posBtn) {
            if (!isExamActive) return;

            const now = Date.now();

            // 1. Process Every Compression Attempt
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
                    // STROKE PEAK COMPLETED -> EVALUATE THIS COMPRESSION!
                    cprStrokeState = "recoiling";
                    examStats.totalComps++;
                    examStats.strokeTimes.push(now);

                    let strokeErrors = [];

                    // Check Depth / Force
                    if (cprPeak < 38.0) {
                        examStats.shallowErrors++;
                        strokeErrors.push("Sayoz (<38kg)");
                    } else if (cprPeak > 55.0) {
                        examStats.excessErrors++;
                        strokeErrors.push("Juda qattiq (>55kg)");
                    }

                    // Check Hand Position
                    if (!cprPosAtPeak) {
                        examStats.posErrors++;
                        strokeErrors.push("Qo'l noto'g'ri joyda");
                    }

                    if (strokeErrors.length === 0) {
                        // PERFECT STROKE!
                        examStats.correctComps++;
                        document.getElementById("exam-live-feedback").innerText = `✅ To'g'ri zarba (${cprPeak.toFixed(1)} kg)`;
                        document.getElementById("exam-live-feedback").className = "text-xs font-bold text-emerald-400";
                    } else {
                        // FAULTY STROKE!
                        examStats.wrongComps++;
                        document.getElementById("exam-live-feedback").innerText = `❌ Xato: ${strokeErrors.join(', ')}`;
                        document.getElementById("exam-live-feedback").className = "text-xs font-bold text-rose-400";
                    }

                    updateExamHUD();
                }
            } else if (cprStrokeState === "recoiling") {
                if (forceKg <= 5.0) {
                    cprStrokeState = "idle";
                } else if (forceKg > (cprPeak - 1.0) && forceKg > 5.0) {
                    // Stroke repeated without full chest release
                    examStats.recoilErrors++;
                    cprStrokeState = "compressing";
                    cprPeak = forceKg;
                }
            }

            // 2. Process Ventilation Breath
            if (lungKpa >= 1.0 && !window._ventTriggered) {
                window._ventTriggered = true;
                examStats.totalVents++;

                if (lungKpa >= 2.0 && lungKpa <= 3.0) {
                    examStats.correctVents++;
                    document.getElementById("exam-live-feedback").innerText = `🫁 ✅ A'lo nafas (${lungKpa.toFixed(1)} kPa)`;
                    document.getElementById("exam-live-feedback").className = "text-xs font-bold text-cyan-300";
                } else if (lungKpa < 2.0) {
                    document.getElementById("exam-live-feedback").innerText = `🫁 ⚠️ Kam havo (<2.0 kPa)`;
                    document.getElementById("exam-live-feedback").className = "text-xs font-bold text-yellow-300";
                } else {
                    document.getElementById("exam-live-feedback").innerText = `🫁 🚨 Ortiqcha bosim (>3.0 kPa)`;
                    document.getElementById("exam-live-feedback").className = "text-xs font-bold text-rose-400";
                }

                updateExamHUD();
            } else if (lungKpa < 0.5) {
                window._ventTriggered = false;
            }

            // 3. Process Stomach Hazard
            if (stomachKpa > 0.8 && !window._stomachTriggered) {
                window._stomachTriggered = true;
                examStats.stomachErrors++;
                document.getElementById("exam-live-feedback").innerText = `⚠️ XATO: Havo oshqozonga ketdi!`;
                document.getElementById("exam-live-feedback").className = "text-xs font-bold text-rose-400 animate-pulse";
                updateExamHUD();
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
    print("  🎓 BEMOR MANIKEN TEST VA IMTIHON PULTI")
    print("=" * 68)
    print(f"  Kompyuterda ochish:   http://localhost:{port}")
    print(f"  Boshqa qurilmalarda:  http://{local_ip}:{port}")
    print("=" * 68 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
