import os
import sys
import json
import socket
import asyncio
from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
import uvicorn
import webbrowser
import threading

try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

app = FastAPI(title="MedLife: Yurak-O'pka Reanimatsiyasi Simulyatori")

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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>MedLife — Yurak-O'pka Reanimatsiyasi (CPR) Simulyatori</title>
    <meta name="theme-color" content="#0f172a">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Maniken Pulti">
    <link rel="manifest" href="/manifest_console.json">
    <link rel="icon" href="/static/icons/console_192.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@400;500;600;700;800;900&display=swap');
        * { -webkit-touch-callout: none; touch-action: manipulation; }
        body {
            background-color: #f8fafc;
            color: #0f172a;
            font-family: 'Inter', sans-serif;
            user-select: none;
            overflow-x: hidden;
        }

        .mono {
            font-family: 'Share Tech Mono', monospace;
        }

        /* Medical Console Bezel Casing */
        .med-casing {
            background: linear-gradient(145deg, #ffffff, #f1f5f9);
            box-shadow: 0 10px 30px -5px rgba(0,0,0,0.08), 0 0 0 1px #cbd5e1;
            border-radius: 1.5rem;
        }

        .med-panel-inset {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
            border-radius: 1rem;
        }

        /* Segmented LED Bar Styles */
        .led-segment {
            transition: background-color 0.03s ease, box-shadow 0.03s ease;
            border-radius: 2px;
            margin-bottom: 2.5px;
            height: 9px;
            width: 100%;
            background-color: #331414;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.6);
        }

        /* Real-world Backlit LED Illuminations on the Image */
        .photo-led {
            border-radius: 50%;
            position: absolute;
            transform: translate(-50%, -50%);
            pointer-events: auto;
            cursor: pointer;
            transition: opacity 0.12s ease, background-color 0.12s ease;
            opacity: 0;
            z-index: 20;
        }

        /* Chest Center (PIN 13) Solid Neon Green Glow */
        .pos-led-on {
            opacity: 0.95 !important;
            background-color: #22c55e !important;
            box-shadow: 0 0 25px #22c55e, 0 0 50px #22c55e, inset 0 0 8px #ffffff !important;
            border: 3px solid #ffffff !important;
        }

        /* Injection Arm (PIN 4) Solid Neon Purple Glow */
        .inj-led-on {
            opacity: 0.95 !important;
            background-color: #a855f7 !important;
            box-shadow: 0 0 25px #a855f7, 0 0 50px #c084fc, inset 0 0 8px #ffffff !important;
            border: 3px solid #ffffff !important;
        }

        /* Airway Throat Solid Neon Cyan Glow */
        .airway-led-on {
            opacity: 0.95 !important;
            background-color: #06b6d4 !important;
            box-shadow: 0 0 20px #06b6d4, 0 0 40px #06b6d4, inset 0 0 6px #ffffff !important;
            border: 2px solid #ffffff !important;
        }

        /* Stomach Warning Solid Neon Red Glow */
        .stomach-led-on {
            opacity: 0.95 !important;
            background-color: #ef4444 !important;
            box-shadow: 0 0 25px #ef4444, 0 0 50px #ef4444, inset 0 0 8px #ffffff !important;
            border: 2px solid #ffffff !important;
        }

        /* Countdown Pulse Animation */
        @keyframes countPulse {
            0% { transform: scale(0.6); opacity: 0; }
            50% { transform: scale(1.15); opacity: 1; }
            100% { transform: scale(1.0); opacity: 1; }
        }

        .animate-countdown {
            animation: countPulse 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
        }



        /* ==================== PROFESSIONAL PRINT SHEET STYLING ==================== */
        @media print {
            body {
                background: white !important;
                color: black !important;
                padding: 0 !important;
            }
            .no-print {
                display: none !important;
            }
            #print-protocol-container {
                display: block !important;
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                background: white;
                color: black;
            }
        }
    </style>
</head>
<body class="min-h-screen flex flex-col items-center justify-start p-3 sm:p-5">


    <!-- Top Medical Navigation & Device Header (Clean White Medical Styling) -->
    <header class="no-print w-full max-w-7xl bg-white border border-slate-200 rounded-2xl px-4 py-3 mb-4 shadow-sm flex flex-wrap items-center justify-between gap-3">
        
        <!-- Left: Logo & Hospital Badge -->
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white text-lg shadow-sm">
                <i class="fa-solid fa-hand-holding-heart"></i>
            </div>
            <div>
                <h1 class="font-extrabold text-slate-900 text-base leading-tight">YURAK-O'PKA REANIMATSIYASI (CPR) SIMULYATORI</h1>
                <p class="text-xs text-slate-500 font-medium">MedLife: Tibbiy Ko'nikmalarni Baholash va Trening Markazi</p>
            </div>
        </div>

        <!-- Center: Live Hardware Status & Direct USB Connect Button -->
        <div class="flex items-center gap-2">
            <button id="btn-direct-serial" onclick="connectDirectSerial()" class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl transition text-xs flex items-center gap-1.5 shadow cursor-pointer">
                <i class="fa-brands fa-usb text-blue-200"></i>
                <span id="btn-serial-text">🔌 Maniken (USB) ga Ulanish</span>
            </button>

            <div class="flex items-center gap-2 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-700">
                <span id="conn-dot" class="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_8px_#22c55e]"></span>
                <span id="conn-status">ESP32: Kutish holatida</span>
            </div>
        </div>

        <!-- Right: Mode Switches and Links -->
        <div class="flex flex-wrap items-center gap-2">
            <a href="/hub" class="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-cyan-300 font-bold rounded-xl transition border border-cyan-500/40 text-xs flex items-center gap-1.5 shadow-sm">
                <i class="fa-solid fa-hospital text-cyan-400"></i> Kiosk Hub
            </a>
            <button id="pwa-console-btn" onclick="installConsolePWA()" class="hidden px-3 py-1.5 bg-amber-400 hover:bg-amber-300 text-slate-950 font-black rounded-xl transition text-xs flex items-center gap-1.5 shadow cursor-pointer">
                <i class="fa-solid fa-download"></i> O'rnatish
            </button>
            <a href="/vital" target="_blank" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl transition border border-slate-300 text-xs flex items-center gap-1.5 shadow-sm">
                <i class="fa-solid fa-heart-pulse text-emerald-600"></i> Vital Monitor
            </a>
            <a href="/" target="_blank" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl transition border border-slate-300 text-xs flex items-center gap-1.5 shadow-sm">
                <i class="fa-solid fa-hospital-user text-indigo-600"></i> AI Bemor
            </a>
            <button onclick="toggleFullScreenConsole()" class="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-xl transition border border-slate-300 text-xs flex items-center gap-1 cursor-pointer">
                <i class="fa-solid fa-expand"></i>
            </button>
        </div>

    </header>

    <!-- MAIN 2-COLUMN MEDICAL WORKSPACE (LEFT: MANIKIN DEVICE | RIGHT: LARGE CONTROLS & EXAM HUD) -->
    <main class="no-print w-full max-w-7xl grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        
        <!-- ==================== LEFT COLUMN (5/12): MEDICAL MANIKIN DEVICE ==================== -->
        <section class="lg:col-span-5 flex flex-col gap-3">
            
            <div class="med-casing p-3 sm:p-4 flex flex-col">
                
                <!-- Title Header inside Bezel -->
                <div class="flex items-center justify-between border-b border-slate-200 pb-2 mb-2">
                    <span class="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
                        <i class="fa-solid fa-microchip text-blue-600"></i> INTERAKTIV DATCHIKLAR PANELI
                    </span>
                    <span class="text-[11px] font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">0ms Kechikish</span>
                </div>

                <!-- MAIN DISPLAY PANEL (LEFT BAR | PHOTO OF MANIKIN WITH OVERLAYS | RIGHT BAR) -->
                <div class="med-panel-inset p-2 relative overflow-hidden flex flex-col">
                    
                    <div class="flex items-stretch justify-between relative" style="height: 520px;">
                        
                        <!-- LEFT LED BAR: KO'KRAK MASSAJ KUCHI (CPR FORCE) -->
                        <div class="w-16 flex flex-col items-center justify-between py-1 z-10">
                            <div class="text-center w-full">
                                <div class="text-[10px] font-black text-slate-700 tracking-tight uppercase leading-none">KUCH</div>
                                <div id="force-val-text" ondblclick="tareForceSensor()" title="Nolga tushirish uchun 2 marta bosing" class="mono font-black text-rose-600 text-sm sm:text-base mt-0.5 cursor-pointer select-none">0.0 kg</div>
                                <button type="button" onclick="tareForceSensor()" title="Boshlang'ich massani 0 qilish (Tare / Kalibrovka)" class="mt-1 w-full py-0.5 px-1 bg-slate-100 hover:bg-rose-100 hover:text-rose-700 text-slate-700 font-extrabold text-[9px] rounded border border-slate-300 shadow-xs flex items-center justify-center gap-0.5 transition cursor-pointer active:scale-95">
                                    <i class="fa-solid fa-scale-balanced text-[8px]"></i> 0 qilish
                                </button>
                            </div>
                            
                            <!-- LED Bar Graph Enclosure (30 Segments) with Bulletproof Inline Style -->
                            <div id="force-bar-container" style="width: 36px; height: 380px; background-color: #1a0808; border: 2px solid #4a1d1d; border-radius: 6px; padding: 4px; display: flex; flex-direction: column-reverse; justify-content: space-between; box-shadow: inset 0 2px 6px rgba(0,0,0,0.8); position: relative;">
                                <!-- LED Segments generated by JS -->
                            </div>

                            <div class="text-[10px] font-black text-slate-700 uppercase tracking-tighter">MASSAJ</div>
                        </div>

                        <!-- CENTER: REALISTIC HIGH-INTEL MANIKIN PHOTO WITH PIXEL-PERFECT LED OVERLAYS -->
                        <div class="flex-1 relative flex items-center justify-center mx-1 overflow-hidden rounded-xl border border-slate-200 shadow-inner bg-slate-50 h-full">
                            
                            <!-- Aspect Ratio Locked Image Wrapper (Zero Shift Error) -->
                            <div class="relative h-full flex items-center justify-center" style="aspect-ratio: 707 / 1024; position: relative;">
                                
                                <!-- Base Manikin Photo -->
                                <img src="manikin_photo.png" alt="Maniken" class="w-full h-full block object-fill pointer-events-none select-none">

                                <!-- ==================== BULLETPROOF INLINE-STYLED LED OVERLAYS ==================== -->

                                <!-- 1. Airway / Throat LED (Bo'yin/Tomir nuqtasi) -->
                                <div id="led-airway" class="photo-led" style="position: absolute; top: 33.74%; left: 50.85%; width: 42px; height: 42px; transform: translate(-50%, -50%); border-radius: 50%;">
                                </div>

                                <!-- 2. Chest Center Position LED (NUQTA PIN 13) -->
                                <div id="led-position" onclick="toggleSimPos()" class="photo-led" style="position: absolute; top: 56.30%; left: 50.85%; width: 52px; height: 52px; transform: translate(-50%, -50%); border-radius: 50%; cursor: pointer;" title="Qo'l nuqtasi (Pin 13)">
                                </div>

                                <!-- 3. Right Arm Injection LED (UKOL PIN 4) -->
                                <div id="led-injection" onclick="triggerSimInj()" class="photo-led" style="position: absolute; top: 68.41%; left: 91.58%; width: 56px; height: 56px; transform: translate(-50%, -50%); border-radius: 50%; cursor: pointer;" title="Ukol / Inyeksiya (Pin 4)">
                                </div>

                                <!-- 4. Stomach Warning LED (OSHQOZON) -->
                                <div id="led-stomach" class="photo-led" style="position: absolute; top: 93.0%; left: 51.0%; width: 120px; height: 32px; transform: translate(-50%, -50%); border-radius: 6px;" title="Oshqozon bosimi">
                                </div>



                            </div>

                        </div>

                        <!-- RIGHT LED BAR: O'PKA BOSIMI (VENTILATION) -->
                        <div class="w-16 flex flex-col items-center justify-between py-2 z-10">
                            <div class="text-center">
                                <div class="text-[11px] font-black text-slate-800 tracking-tight uppercase leading-none">O'PKA</div>
                                <div id="lung-val-text" class="mono font-black text-cyan-600 text-sm mt-0.5">0.0 kPa</div>
                            </div>

                            <!-- LED Bar Graph Enclosure (30 Segments) with Bulletproof Inline Style -->
                            <div id="lung-bar-container" style="width: 36px; height: 410px; background-color: #1a0808; border: 2px solid #4a1d1d; border-radius: 6px; padding: 4px; display: flex; flex-direction: column-reverse; justify-content: space-between; box-shadow: inset 0 2px 6px rgba(0,0,0,0.8); position: relative;">
                                <!-- LED Segments generated by JS -->
                            </div>

                            <div class="text-[11px] font-black text-slate-700 uppercase tracking-tighter">NAFAS</div>
                        </div>

                    </div>



                    <!-- Ukol va Oshqozon Ogohlantirish Popupi -->
                    <div id="console-alert-box" class="hidden mt-2 p-2.5 rounded-xl bg-rose-50 border border-rose-300 text-rose-900 text-xs font-bold text-center flex items-center justify-center gap-2 shadow-sm animate-pulse">
                        <i class="fa-solid fa-triangle-exclamation text-rose-600"></i>
                        <span id="console-alert-text">OGOHLANTIRISH</span>
                    </div>

                </div>

            </div>

        </section>

        <!-- ==================== RIGHT COLUMN (7/12): MAIN CLINICAL ASSESSMENT & CONTROLS ==================== -->
        <section class="lg:col-span-7 flex flex-col gap-4">
            
            <!-- 1. ENLARGED PROMINENT MODE SELECTOR (KATTALASHTIRILGAN REJIM TANLASH) -->
            <div class="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm flex flex-col gap-3">
                <div class="text-xs font-black text-slate-500 uppercase tracking-wider">MASHG'ULOT REJIMINI TANLANG:</div>
                
                <div class="grid grid-cols-2 gap-3">
                    <!-- Erkin Mashq Button -->
                    <button type="button" id="tab-practice" onclick="switchMode('practice')" 
                            class="py-4 px-4 rounded-2xl font-black text-sm sm:text-base bg-blue-600 text-white transition shadow-md flex items-center justify-center gap-2.5 cursor-pointer border-2 border-blue-700">
                        <i class="fa-solid fa-dumbbell text-lg"></i> 🔘 ERKIN MASHQ
                    </button>

                    <!-- Imtihon Rejimi Button -->
                    <button type="button" id="tab-exam" onclick="switchMode('exam')" 
                            class="py-4 px-4 rounded-2xl font-black text-sm sm:text-base bg-slate-50 text-slate-700 hover:bg-slate-100 transition border-2 border-slate-200 flex items-center justify-center gap-2.5 cursor-pointer shadow-sm">
                        <i class="fa-solid fa-graduation-cap text-lg text-amber-500"></i> 🎓 IMTIHON REJIMI
                    </button>
                </div>

                <!-- Active Status Banner -->
                <div id="mode-status-banner" class="flex items-center justify-between bg-blue-50/70 border border-blue-200/80 px-3.5 py-2.5 rounded-xl text-xs">
                    <div class="flex items-center gap-2 text-slate-800">
                        <i id="mode-status-icon" class="fa-solid fa-circle-check text-blue-600 text-sm"></i>
                        <span id="hud-student-display" class="font-bold">Erkin Mashq: Cheklovlarsiz mashq qiling, barcha harakatlar hisoblanadi</span>
                    </div>
                    <button type="button" id="btn-reset-practice" onclick="resetPracticeCounts()" class="px-2.5 py-1 bg-white hover:bg-slate-100 text-slate-700 font-bold rounded-lg border border-slate-300 transition text-[11px] shadow-sm">
                        <i class="fa-solid fa-rotate-right mr-1"></i> Qayta boshlash
                    </button>
                </div>
            </div>

            <!-- 2. REAL-TIME ASSESSMENT METRICS HUD (BOTH IN PRACTICE & EXAM MODES) -->
            <div id="exam-hud-card" class="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm flex flex-col gap-3">
                
                <!-- Exam-Specific Controls Header (Visible only when in Exam mode) -->
                <div id="exam-controls-header" class="hidden flex items-center justify-between border-b border-slate-100 pb-3">
                    <div class="flex flex-col">
                        <div class="flex items-center gap-2">
                            <span class="px-2.5 py-0.5 rounded-full text-xs font-black bg-indigo-50 text-indigo-700 border border-indigo-200 uppercase tracking-wide flex items-center gap-1">
                                <i class="fa-solid fa-stopwatch"></i> RASMIY IMTIHON VAQTI
                            </span>
                            <span id="exam-live-feedback" class="text-xs font-bold text-slate-600">Tayyor: 'Boshlash' tugmasini bosing!</span>
                        </div>
                    </div>

                    <!-- Timer & Actions -->
                    <div class="flex items-center gap-2">
                        <span id="exam-timer" class="mono text-xl font-black text-slate-900 tracking-wider bg-slate-100 px-3 py-1 rounded-xl border border-slate-300">02:00</span>
                        
                        <button type="button" id="btn-exam-toggle" onclick="requestStartExam()" class="px-4 py-2 rounded-xl font-black text-xs bg-emerald-600 hover:bg-emerald-500 text-white transition shadow flex items-center gap-1.5 cursor-pointer">
                            <i class="fa-solid fa-play"></i> Boshlash
                        </button>
                        <button type="button" id="btn-exam-finish" onclick="finishExamManually()" class="hidden px-4 py-2 rounded-xl font-bold text-xs bg-blue-600 hover:bg-blue-500 text-white transition shadow flex items-center gap-1.5 cursor-pointer">
                            Yakunlash
                        </button>
                    </div>
                </div>

                <!-- 4 LARGE REAL-TIME SCORE BOXES (Jami, To'g'ri, Xatolar, Nafas) -->
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-center">
                    
                    <!-- 1. Total Compressions Attempted -->
                    <div class="bg-slate-50 p-3 rounded-xl border border-slate-200">
                        <div class="text-[11px] font-bold text-slate-500 uppercase tracking-tight">Jami Bosildi</div>
                        <div id="stat-total-comps" class="mono text-2xl font-black text-slate-900 mt-0.5">0</div>
                        <div class="text-[10px] text-slate-400 font-medium">kompressiya</div>
                    </div>

                    <!-- 2. Correct Compressions (To'g'ri) -->
                    <div class="bg-emerald-50 p-3 rounded-xl border border-emerald-300">
                        <div class="text-[11px] font-bold text-emerald-800 uppercase tracking-tight">To'g'ri (38-55kg)</div>
                        <div id="stat-correct-comps" class="mono text-2xl font-black text-emerald-600 mt-0.5">0</div>
                        <div id="stat-correct-pct" class="text-[10px] text-emerald-700 font-bold">0% to'g'ri</div>
                    </div>

                    <!-- 3. Errors / Faults (Xatolar) -->
                    <div class="bg-rose-50 p-3 rounded-xl border border-rose-300">
                        <div class="text-[11px] font-bold text-rose-800 uppercase tracking-tight">Xatolar</div>
                        <div id="stat-wrong-comps" class="mono text-2xl font-black text-rose-600 mt-0.5">0</div>
                        <div id="stat-wrong-reasons" class="text-[10px] text-rose-700 truncate font-semibold">0 ta xato</div>
                    </div>

                    <!-- 4. Breaths / Ventilations (O'pka nafasi) -->
                    <div class="bg-cyan-50 p-3 rounded-xl border border-cyan-300">
                        <div class="text-[11px] font-bold text-cyan-800 uppercase tracking-tight">Nafas (2.0-3.0 kPa)</div>
                        <div id="stat-total-vents" class="mono text-2xl font-black text-cyan-600 mt-0.5">0</div>
                        <div id="stat-vent-status" class="text-[10px] text-cyan-700 font-semibold">0 to'g'ri</div>
                    </div>

                </div>

                <!-- Live Quality Percentage Bar -->
                <div class="flex flex-col gap-1.5 bg-slate-50 p-3 rounded-xl border border-slate-200">
                    <div class="flex justify-between items-center text-xs font-bold">
                        <span class="text-slate-700">CPR Umumiy Sifat Ko'rsatkichi:</span>
                        <span id="stat-live-quality" class="mono font-black text-emerald-600 text-sm">100%</span>
                    </div>
                    <div class="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
                        <div id="stat-quality-bar" class="bg-emerald-500 h-full rounded-full transition-all duration-150" style="width: 100%;"></div>
                    </div>
                </div>

                <!-- Practice Live Status Line -->
                <div id="practice-live-status-line" class="text-xs font-bold text-slate-600 text-center py-1">
                    Hozirgi holat: <span id="practice-feedback-text" class="text-blue-600">Ko'krakni 38-55 kg kuch bilan bosing yoki Ambu qopi bilan nafas bering</span>
                </div>

            </div>

            <!-- 3. PERSISTENT EXAM RESULTS HISTORY LOG (COLLAPSIBLE, SEARCHABLE, SORTABLE) -->
            <div id="exam-history-card" class="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden flex flex-col">
                
                <!-- Header Toggle Button -->
                <button type="button" onclick="toggleHistoryPanel()" 
                        class="w-full py-3.5 px-4 bg-slate-50 hover:bg-slate-100 text-slate-700 font-bold text-xs flex items-center justify-between border-b border-slate-100 transition cursor-pointer">
                    <div class="flex items-center gap-2">
                        <i class="fa-solid fa-clock-rotate-left text-blue-600"></i>
                        <span class="font-extrabold uppercase tracking-wider text-slate-800">IMTIHON NATIJALARI JURNALI</span>
                        <span id="history-count-badge" class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-blue-100 text-blue-800 border border-blue-200">
                            0 ta
                        </span>
                    </div>
                    <div class="flex items-center gap-1.5 text-[11px] text-slate-400">
                        <span id="history-panel-status-text">Yopish</span>
                        <i id="history-panel-icon" class="fa-solid fa-chevron-up text-xs transition-transform duration-200"></i>
                    </div>
                </button>

                <!-- Collapsible Content Wrapper -->
                <div id="history-content-wrapper" class="p-4 flex flex-col gap-3 bg-white">
                    <!-- Search & Sort Controls Bar -->
                    <div class="flex flex-col sm:flex-row items-center gap-2">
                        <!-- Search Input -->
                        <div class="relative flex-1 w-full">
                            <i class="fa-solid fa-magnifying-glass absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs"></i>
                            <input type="text" id="history-search-input" oninput="onHistoryFilterChange()" 
                                   placeholder="Talaba F.I.SH. yoki guruhi bo'yicha qidirish..." 
                                   class="w-full pl-8 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-800 focus:outline-none focus:border-blue-600 font-medium placeholder:text-slate-400">
                        </div>

                        <!-- Filter by Status Dropdown -->
                        <select id="history-filter-status" onchange="onHistoryFilterChange()" 
                                class="w-full sm:w-auto px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 font-bold focus:outline-none focus:border-blue-600 cursor-pointer">
                            <option value="all">Barcha natijalar</option>
                            <option value="passed">🏆 Faqat O'tganlar</option>
                            <option value="failed">❌ Faqat Yiqilganlar</option>
                        </select>

                        <!-- Sort Dropdown -->
                        <select id="history-sort-by" onchange="onHistoryFilterChange()" 
                                class="w-full sm:w-auto px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 font-bold focus:outline-none focus:border-blue-600 cursor-pointer">
                            <option value="newest">🕒 Eng yangilari</option>
                            <option value="oldest">🕒 Eng eskisi</option>
                            <option value="score_desc">📈 Yuqori ball</option>
                            <option value="score_asc">📉 Past ball</option>
                            <option value="name_asc">🔤 Alifbo (A-Z)</option>
                        </select>

                        <!-- Clear All Button -->
                        <button type="button" onclick="clearAllExamHistory()" title="Barcha natijalarni tozalash"
                                class="w-full sm:w-auto px-3 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold rounded-xl border border-rose-200 transition text-xs flex items-center justify-center gap-1 cursor-pointer whitespace-nowrap">
                            <i class="fa-solid fa-trash-can text-xs"></i> Tozalash
                        </button>
                    </div>

                    <!-- History Table / Records Container -->
                    <div id="history-list-container" class="max-h-72 overflow-y-auto space-y-2 pr-1">
                        <!-- Dynamic Records Loaded by JS -->
                    </div>

                    <div id="history-empty-placeholder" class="text-center py-4 text-xs text-slate-400 font-medium">
                        Hali topshirilgan imtihonlar mavjud emas. Imtihon topshirilgach natijalar avtomatik saqlanadi.
                    </div>
                </div>

            </div>

            <!-- 4. COLLAPSIBLE SOFTWARE SIMULATION CONTROLS (YASHIRILGAN TEST BOSHQARUVI) -->
            <div class="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden flex flex-col">
                
                <!-- Header Toggle Button -->
                <button type="button" onclick="toggleTestPanel()" 
                        class="w-full py-3 px-4 bg-slate-50 hover:bg-slate-100 text-slate-600 font-bold text-xs flex items-center justify-between border-b border-slate-100 transition cursor-pointer">
                    <span class="flex items-center gap-2 text-slate-700">
                        <i class="fa-solid fa-sliders text-blue-600"></i>
                        <span>Dasturiy Test va Simulyatsiya Slayderlari (Qo'lda sinash uchun)</span>
                    </span>
                    <span class="flex items-center gap-1.5 text-[11px] text-slate-400">
                        <span id="test-panel-status-text">Ochish</span>
                        <i id="test-panel-icon" class="fa-solid fa-chevron-down text-xs transition-transform duration-200"></i>
                    </span>
                </button>

                <!-- Hidden Simulation Controls by default -->
                <div id="simulation-controls-wrapper" class="hidden p-4 flex flex-col gap-3.5 bg-white">
                    
                    <!-- 2 Large Fast-Action Buttons -->
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <button type="button" onclick="simSingleStroke(45.0)" class="py-3 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 active:scale-98 font-bold text-xs text-white text-center shadow-sm transition flex items-center justify-center gap-2 cursor-pointer">
                            <i class="fa-solid fa-hand-fist"></i> 🖐️ 1 ta CPR Bosish (45 kg)
                        </button>

                        <button type="button" onclick="simSingleBreath(2.6)" class="py-3 px-4 rounded-xl bg-sky-600 hover:bg-sky-700 active:scale-98 font-bold text-xs text-white text-center shadow-sm transition flex items-center justify-center gap-2 cursor-pointer">
                            <i class="fa-solid fa-lungs"></i> 🫁 1 ta Nafas (2.6 kPa)
                        </button>
                    </div>

                    <!-- 2 Sliders -->
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 bg-slate-50 p-3 rounded-xl border border-slate-200">
                        <div>
                            <div class="flex justify-between text-xs font-bold text-slate-700 mb-1">
                                <span>Ko'krak Kuchi:</span>
                                <span id="sim-force-lbl" class="mono text-rose-600 font-bold">0.0 kg</span>
                            </div>
                            <input type="range" id="sim-force" min="0" max="60" step="0.5" value="0" 
                                   oninput="onSimInput()" class="w-full accent-rose-600 h-2 bg-slate-300 rounded-lg cursor-pointer">
                        </div>

                        <div>
                            <div class="flex justify-between text-xs font-bold text-slate-700 mb-1">
                                <span>O'pka Bosimi:</span>
                                <span id="sim-lung-lbl" class="mono text-cyan-600 font-bold">0.0 kPa</span>
                            </div>
                            <input type="range" id="sim-lung" min="0" max="4.0" step="0.1" value="0" 
                                   oninput="onSimInput()" class="w-full accent-cyan-600 h-2 bg-slate-300 rounded-lg cursor-pointer">
                        </div>
                    </div>

                    <!-- 3 Toggles -->
                    <div class="grid grid-cols-3 gap-2">
                        <button type="button" id="btn-toggle-pos" onclick="toggleSimPos()" class="py-2 px-2 rounded-lg bg-slate-100 hover:bg-slate-200 font-bold text-xs text-center border border-slate-300 transition cursor-pointer text-slate-800">
                            🔘 Nuqta: <span id="pos-btn-text" class="text-rose-600">BO'SH</span>
                        </button>

                        <button type="button" id="btn-toggle-inj" onclick="triggerSimInj()" class="py-2 px-2 rounded-lg bg-purple-50 hover:bg-purple-100 font-bold text-xs text-center border border-purple-200 transition cursor-pointer text-purple-900">
                            💉 Ukol: <span id="inj-btn-text" class="text-purple-700">Kiritish</span>
                        </button>

                        <button type="button" onclick="triggerSimStomach()" class="py-2 px-2 rounded-lg bg-rose-50 hover:bg-rose-100 font-bold text-xs text-rose-800 border border-rose-200 transition cursor-pointer">
                            ⚠️ Oshqozon
                        </button>
                    </div>

                </div>

            </div>

        </section>

    </main>

    <!-- ==================== COUNTDOWN OVERLAY (3... 2... 1... START!) ==================== -->
    <div id="countdown-overlay" class="no-print fixed inset-0 bg-slate-900/80 backdrop-blur-md flex flex-col items-center justify-center p-4 z-50 hidden">
        <div class="text-center flex flex-col items-center">
            <div class="text-white/80 font-bold text-lg mb-2 tracking-widest uppercase">IMTIHON BOSHLANMOQDA:</div>
            
            <div id="countdown-number-circle" class="w-36 h-36 rounded-full bg-blue-600 border-4 border-white/80 flex items-center justify-center text-white text-6xl font-black shadow-2xl animate-countdown">
                3
            </div>

            <div id="countdown-subtitle" class="text-slate-200 font-bold text-sm mt-4 tracking-wide">
                Qo'llaringizni maniken ko'kragiga qo'ying!
            </div>
        </div>
    </div>

    <!-- ==================== 1. STUDENT REGISTRATION MODAL ==================== -->
    <div id="student-modal" class="no-print fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 hidden">
        <div class="bg-white border border-slate-300 rounded-3xl max-w-md w-full p-6 shadow-2xl text-slate-900 flex flex-col gap-4">
            
            <div class="text-center border-b border-slate-100 pb-3">
                <div class="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-200 flex items-center justify-center mx-auto mb-2 text-blue-600 text-xl shadow-sm">
                    <i class="fa-solid fa-user-graduate"></i>
                </div>
                <h2 class="text-lg font-black text-slate-900">TALABA / KURSANTNI RO'YXATGA OLISH</h2>
                <p class="text-xs text-slate-500">Imtihon natijalari ushbu ma'lumotlar bilan rasmiylashtiriladi</p>
            </div>

            <form onsubmit="confirmStartExam(event)" class="flex flex-col gap-3">
                <!-- F.I.SH -->
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">
                        👤 Talaba F.I.SH. (Familiya, Ism, Sharif): <span class="text-rose-500">*</span>
                    </label>
                    <input type="text" id="input-student-name" required placeholder="Masalan: Bozorov Boburjon" 
                           class="w-full px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-900 focus:outline-none focus:border-blue-600 font-semibold placeholder:text-slate-400">
                </div>

                <!-- Guruh / ID -->
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="block text-xs font-bold text-slate-700 mb-1">
                            🏷️ Guruh / Fakultet: <span class="text-rose-500">*</span>
                        </label>
                        <input type="text" id="input-student-group" required placeholder="Davolash 402" 
                               class="w-full px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-900 focus:outline-none focus:border-blue-600 font-semibold placeholder:text-slate-400">
                    </div>
                    <div>
                        <label class="block text-xs font-bold text-slate-700 mb-1">
                            🆔 ID / Bilet №:
                        </label>
                        <input type="text" id="input-student-id" placeholder="№ 14" 
                               class="w-full px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-900 focus:outline-none focus:border-blue-600 font-semibold placeholder:text-slate-400">
                    </div>
                </div>

                <!-- O'qituvchi / Imtihonchi -->
                <div>
                    <label class="block text-xs font-bold text-slate-700 mb-1">
                        🩺 Imtihonchi (O'qituvchi):
                    </label>
                    <input type="text" id="input-examiner" placeholder="Kafedra o'qituvchisi" value="Kafedra Assistent / O'qituvchisi" 
                           class="w-full px-3 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-900 focus:outline-none focus:border-blue-600 font-semibold placeholder:text-slate-400">
                </div>

                <!-- Action Buttons -->
                <div class="flex items-center gap-2 mt-2">
                    <button type="submit" class="flex-1 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 font-bold text-xs text-white transition shadow-md flex items-center justify-center gap-2 cursor-pointer">
                        <i class="fa-solid fa-play"></i> Imtihonni Boshlash
                    </button>
                    <button type="button" onclick="closeStudentModal()" class="py-3 px-4 rounded-xl bg-slate-100 hover:bg-slate-200 font-bold text-xs text-slate-700 transition cursor-pointer border border-slate-300">
                        Bekor qilish
                    </button>
                </div>
            </form>

        </div>
    </div>

    <!-- ==================== 2. EXAM RESULTS MODAL SCORECARD ==================== -->
    <div id="exam-modal" class="no-print fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 hidden">
        <div class="bg-white border border-slate-300 rounded-3xl max-w-lg w-full p-6 shadow-2xl text-slate-900 flex flex-col gap-4">
            
            <div class="text-center border-b border-slate-100 pb-3">
                <span id="modal-status-badge" class="px-4 py-1 rounded-full text-xs font-black uppercase tracking-widest bg-emerald-50 text-emerald-700 border border-emerald-300 inline-block mb-2">
                    🏆 IMTIHONDAN O'TDI (PASSED)
                </span>
                <h2 class="text-xl font-black text-slate-900">CPR IMTIHON VA BAHOLASH PROTOKOLI</h2>
                <p id="modal-student-header" class="text-xs text-blue-700 font-semibold mt-0.5">Talaba: -</p>
            </div>

            <!-- Total Score & Grade -->
            <div class="flex items-center justify-between bg-slate-50 p-4 rounded-2xl border border-slate-200">
                <div>
                    <div class="text-xs text-slate-500 font-semibold">Umumiy Sifat Bahosi:</div>
                    <div id="modal-total-score" class="mono text-3xl font-black text-emerald-600">92%</div>
                </div>
                <div class="text-right">
                    <div class="text-xs text-slate-500 font-semibold">Sarflangan Vaqt:</div>
                    <div id="modal-time-spent" class="mono text-lg font-bold text-slate-800">01:52 soniya</div>
                </div>
            </div>

            <!-- Detailed Breakdown Metrics (Jami, To'g'ri, Xato, Xatolar sababi) -->
            <div class="grid grid-cols-2 gap-2 text-xs">
                
                <div class="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                    <div class="text-slate-500 font-semibold">🔢 Jami Kompressiyalar:</div>
                    <div id="modal-total-comps" class="mono font-bold text-slate-900 text-sm mt-0.5">30 ta</div>
                </div>

                <div class="bg-emerald-50/70 p-2.5 rounded-xl border border-emerald-200">
                    <div class="text-emerald-800 font-semibold">✅ To'g'ri Bajarilgani:</div>
                    <div id="modal-correct-comps" class="mono font-bold text-emerald-700 text-sm mt-0.5">26 ta (87%)</div>
                </div>

                <div class="bg-rose-50/70 p-2.5 rounded-xl border border-rose-200">
                    <div class="text-rose-800 font-semibold">❌ Xato Bajarilgani:</div>
                    <div id="modal-wrong-comps" class="mono font-bold text-rose-700 text-sm mt-0.5">4 ta</div>
                </div>

                <div class="bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                    <div class="text-slate-500 font-semibold">⏱️ O'rtacha Tezlik (BPM):</div>
                    <div id="modal-bpm-avg" class="mono font-bold text-slate-800 text-sm mt-0.5">112 /min</div>
                </div>

                <div class="bg-slate-50 p-2.5 rounded-xl border border-slate-200 col-span-2">
                    <div class="text-slate-600 font-bold mb-1">🔍 Xatolar Tafsiloti:</div>
                    <div id="modal-error-details" class="space-y-0.5 text-[11px] text-slate-700">
                        <!-- Filled by JS -->
                    </div>
                </div>

                <div class="bg-cyan-50/70 p-2.5 rounded-xl border border-cyan-200 col-span-2">
                    <div class="text-cyan-800 font-bold">🫁 O'pka Ventilyatsiyasi:</div>
                    <div id="modal-vent-summary" class="mono text-xs text-cyan-900 mt-0.5">Jami: 2 ta | To'g'ri: 2 ta | Oshqozon: 0 ta</div>
                </div>

            </div>



            <!-- Modal Action Buttons (Printerga Chiqarish & Qayta topshirish) -->
            <div class="flex items-center gap-2 mt-1">
                <!-- PRINT PROTOCOL BUTTON -->
                <button type="button" onclick="printExamProtocol()" class="flex-1 py-3 rounded-xl bg-blue-600 hover:bg-blue-700 font-bold text-xs text-white transition shadow-md flex items-center justify-center gap-2 cursor-pointer">
                    <i class="fa-solid fa-print text-sm"></i> 🖨️ Printerga Chiqarish (A4 / PDF)
                </button>

                <button type="button" onclick="restartExam()" class="py-3 px-3.5 rounded-xl bg-slate-100 hover:bg-slate-200 font-bold text-xs text-slate-800 transition border border-slate-300 flex items-center justify-center gap-1.5 cursor-pointer">
                    <i class="fa-solid fa-rotate-right"></i> Qayta
                </button>
                <button type="button" onclick="closeModal()" class="py-3 px-3.5 rounded-xl bg-slate-100 hover:bg-slate-200 font-bold text-xs text-slate-700 transition border border-slate-300 cursor-pointer">
                    Yopish
                </button>
            </div>

        </div>
    </div>

    <!-- ==================== 3. OFFICIAL PRINTABLE PROTOCOL SHEET (A4 FORMAT) ==================== -->
    <div id="print-protocol-container" class="hidden p-8 max-w-4xl mx-auto bg-white text-black font-sans">
        
        <!-- Header -->
        <div class="text-center border-b-2 border-black pb-4 mb-4">
            <h1 class="text-xl font-black uppercase tracking-wider">TIBBIY KO'NIKMALARNI BAHOLASH VA SIMULYATSIYA MARKAZI</h1>
            <h2 class="text-lg font-bold text-slate-800 mt-1">CPR VA YURAK-O'PKA REANIMATSIYASI IMTIHON PROTOKOLI</h2>
            <div class="text-xs text-slate-600 mt-1">Qurilma: GD/H126 Intelligent CPR & Airway Manikin System | Protokol №: <span id="print-protocol-no" class="font-bold">CPR-2026-001</span></div>
        </div>

        <!-- Student & Exam Details Table -->
        <div class="grid grid-cols-2 gap-4 border border-black p-4 mb-4 rounded text-xs">
            <div>
                <p><b>👤 Talaba (F.I.SH.):</b> <span id="print-student-name" class="font-bold text-sm underline">-</span></p>
                <p class="mt-1.5"><b>🏷️ Guruh / Fakultet:</b> <span id="print-student-group">-</span></p>
                <p class="mt-1.5"><b>🆔 Bilet / ID №:</b> <span id="print-student-id">-</span></p>
            </div>
            <div>
                <p><b>📅 Imtihon Sanasi:</b> <span id="print-exam-date">-</span></p>
                <p class="mt-1.5"><b>⏱️ Sarflangan Vaqt:</b> <span id="print-exam-duration">-</span></p>
                <p class="mt-1.5"><b>🩺 Imtihon Oluvchi:</b> <span id="print-examiner">-</span></p>
            </div>
        </div>

        <!-- Grade Banner -->
        <div class="flex items-center justify-between border-2 border-black p-4 mb-4 rounded bg-slate-50">
            <div>
                <div class="text-xs font-bold text-slate-600 uppercase">YAKUNIY BAHOLASH NATIJASI:</div>
                <div id="print-status-text" class="text-2xl font-black mt-0.5">🏆 IMTIHONDAN O'TDI (PASSED)</div>
            </div>
            <div class="text-right">
                <div class="text-xs font-bold text-slate-600 uppercase">UMUMIY SIFAT DARAJASI:</div>
                <div id="print-total-pct" class="text-3xl font-black text-black">92%</div>
            </div>
        </div>

        <!-- Metric Table -->
        <table class="w-full border-collapse border border-black text-xs mb-4">
            <thead>
                <tr class="bg-slate-200">
                    <th class="border border-black p-2 text-left">№</th>
                    <th class="border border-black p-2 text-left">Klinik Mezon va Ko'rsatkich</th>
                    <th class="border border-black p-2 text-center">Talab etilgan Me'yor</th>
                    <th class="border border-black p-2 text-center">Amalda Bajarildi</th>
                    <th class="border border-black p-2 text-center">Xulosa</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td class="border border-black p-2 text-center font-bold">1</td>
                    <td class="border border-black p-2">Jami Kompressiyalar (Zarbalar soni)</td>
                    <td class="border border-black p-2 text-center">Kamida 20 - 30 ta</td>
                    <td class="border border-black p-2 text-center font-bold" id="print-val-total-comps">0 ta</td>
                    <td class="border border-black p-2 text-center" id="print-res-total-comps">Qoniqarli</td>
                </tr>
                <tr>
                    <td class="border border-black p-2 text-center font-bold">2</td>
                    <td class="border border-black p-2">To'g'ri chuqurlik va nuqtadagi zarbalar</td>
                    <td class="border border-black p-2 text-center">≥ 80% (38 - 55 kg)</td>
                    <td class="border border-black p-2 text-center font-bold" id="print-val-correct-comps">0 ta (0%)</td>
                    <td class="border border-black p-2 text-center" id="print-res-correct-comps">-</td>
                </tr>
                <tr>
                    <td class="border border-black p-2 text-center font-bold">3</td>
                    <td class="border border-black p-2">Ko'krak qafasining to'liq bo'shatilishi (Recoil)</td>
                    <td class="border border-black p-2 text-center">To'liq (< 5 kg)</td>
                    <td class="border border-black p-2 text-center font-bold" id="print-val-recoil">0 ta xato</td>
                    <td class="border border-black p-2 text-center" id="print-res-recoil">-</td>
                </tr>
                <tr>
                    <td class="border border-black p-2 text-center font-bold">4</td>
                    <td class="border border-black p-2">Kompressiya tezligi (BPM)</td>
                    <td class="border border-black p-2 text-center">100 - 120 /min</td>
                    <td class="border border-black p-2 text-center font-bold" id="print-val-bpm">110 /min</td>
                    <td class="border border-black p-2 text-center" id="print-res-bpm">Me'yorda</td>
                </tr>
                <tr>
                    <td class="border border-black p-2 text-center font-bold">5</td>
                    <td class="border border-black p-2">O'pka ventilyatsiyasi (Ambu nafasi)</td>
                    <td class="border border-black p-2 text-center">2.0 - 3.0 kPa (20-30 cmH2O)</td>
                    <td class="border border-black p-2 text-center font-bold" id="print-val-vents">0 to'g'ri</td>
                    <td class="border border-black p-2 text-center" id="print-res-vents">-</td>
                </tr>
                <tr>
                    <td class="border border-black p-2 text-center font-bold">6</td>
                    <td class="border border-black p-2">Oshqozonga havo ketishi (Xato)</td>
                    <td class="border border-black p-2 text-center">0 ta (Bo'lmasligi shart)</td>
                    <td class="border border-black p-2 text-center font-bold" id="print-val-stomach">0 ta</td>
                    <td class="border border-black p-2 text-center" id="print-res-stomach">Xavfsiz</td>
                </tr>
            </tbody>
        </table>

        <!-- Error Summary -->
        <div class="border border-black p-3 mb-6 rounded text-xs">
            <p class="font-bold text-slate-800">🔍 Yo'l qo'yilgan xatolar ro'yxati:</p>
            <div id="print-error-list" class="mt-1 space-y-0.5 text-slate-700">
                <!-- Filled by JS -->
            </div>
        </div>

        <!-- Signatures -->
        <div class="grid grid-cols-2 gap-8 pt-6 border-t-2 border-black text-xs">
            <div>
                <p><b>Imtihon oluvchi o'qituvchi:</b></p>
                <div class="mt-6 border-b border-black w-3/4"></div>
                <p class="text-[10px] text-slate-500 mt-1">(Imzo / F.I.SH.)</p>
            </div>
            <div>
                <p><b>Talaba / Kursant:</b></p>
                <div class="mt-6 border-b border-black w-3/4"></div>
                <p class="text-[10px] text-slate-500 mt-1">(Imzo / F.I.SH.)</p>
            </div>
        </div>

        <div class="text-center text-[10px] text-slate-400 mt-8">
            Ushbu protokol tibbiy simulyatsiya markazining kompyuterlashgan GD/H126 tizimi orqali avtomatik shakllantirildi.
        </div>

    </div>

    <script>
        // ==================== GENERATE LED SEGMENTS ====================
        const NUM_SEGMENTS = 30;

        function createLedSegments(containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;
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

        // ==================== BEEP SOUND SYNTHESIZER FOR COUNTDOWN ====================
        function playBeep(freq = 440, duration = 0.15) {
            try {
                const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = audioCtx.createOscillator();
                const gain = audioCtx.createGain();
                osc.type = "sine";
                osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
                gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start();
                osc.stop(audioCtx.currentTime + duration);
            } catch(e) {}
        }

        // ==================== TOGGLE HIDDEN TEST PANEL ====================
        let isTestPanelOpen = false;
        function toggleTestPanel() {
            isTestPanelOpen = !isTestPanelOpen;
            const wrapper = document.getElementById("simulation-controls-wrapper");
            const icon = document.getElementById("test-panel-icon");
            const txt = document.getElementById("test-panel-status-text");

            if (isTestPanelOpen) {
                wrapper.classList.remove("hidden");
                icon.style.transform = "rotate(180deg)";
                txt.innerText = "Yopish";
            } else {
                wrapper.classList.add("hidden");
                icon.style.transform = "rotate(0deg)";
                txt.innerText = "Ochish";
            }
        }

        // ==================== STUDENT REGISTRATION & EXAM STATE ====================
        let studentInfo = {
            name: "",
            group: "",
            id: "",
            examiner: "Kafedra Assistent / O'qituvchisi"
        };

        let currentAppMode = "practice"; // "practice" or "exam"
        let isExamActive = false;
        let examTimerInterval = null;
        let examTimeLeft = 120;

        let liveStats = {
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

        function switchMode(mode) {
            currentAppMode = mode;
            const tabPrac = document.getElementById("tab-practice");
            const tabExam = document.getElementById("tab-exam");
            const examHeader = document.getElementById("exam-controls-header");
            const pracStatusLine = document.getElementById("practice-live-status-line");
            const btnResetPrac = document.getElementById("btn-reset-practice");
            const banner = document.getElementById("mode-status-banner");
            const bannerIcon = document.getElementById("mode-status-icon");
            const bannerText = document.getElementById("hud-student-display");

            if (mode === "exam") {
                tabExam.className = "py-4 px-4 rounded-2xl font-black text-sm sm:text-base bg-blue-600 text-white transition shadow-md flex items-center justify-center gap-2.5 cursor-pointer border-2 border-blue-700";
                tabPrac.className = "py-4 px-4 rounded-2xl font-black text-sm sm:text-base bg-slate-50 text-slate-700 hover:bg-slate-100 transition border-2 border-slate-200 flex items-center justify-center gap-2.5 cursor-pointer shadow-sm";
                
                examHeader.classList.remove("hidden");
                pracStatusLine.classList.add("hidden");
                btnResetPrac.classList.add("hidden");

                banner.className = "flex items-center justify-between bg-amber-50 border border-amber-200 px-3.5 py-2.5 rounded-xl text-xs";
                bannerIcon.className = "fa-solid fa-graduation-cap text-amber-600 text-sm";
                bannerText.innerText = studentInfo.name ? `Talaba: ${studentInfo.name} (${studentInfo.group})` : "Imtihon rejimi: Talaba ro'yxatdan o'tkazilmoqda...";

                if (!studentInfo.name) {
                    openStudentModal();
                }
            } else {
                tabPrac.className = "py-4 px-4 rounded-2xl font-black text-sm sm:text-base bg-blue-600 text-white transition shadow-md flex items-center justify-center gap-2.5 cursor-pointer border-2 border-blue-700";
                tabExam.className = "py-4 px-4 rounded-2xl font-black text-sm sm:text-base bg-slate-50 text-slate-700 hover:bg-slate-100 transition border-2 border-slate-200 flex items-center justify-center gap-2.5 cursor-pointer shadow-sm";
                
                examHeader.classList.add("hidden");
                pracStatusLine.classList.remove("hidden");
                btnResetPrac.classList.remove("hidden");

                banner.className = "flex items-center justify-between bg-blue-50/70 border border-blue-200/80 px-3.5 py-2.5 rounded-xl text-xs";
                bannerIcon.className = "fa-solid fa-circle-check text-blue-600 text-sm";
                bannerText.innerText = "Erkin Mashq: Cheklovlarsiz mashq qiling, barcha harakatlar hisoblanadi";

                if (isExamActive) resetExamState();
            }
        }

        function resetPracticeCounts() {
            liveStats = {
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
            document.getElementById("practice-feedback-text").innerText = "Hisoblagich yangilandi. Ko'krakni bosing yoki nafas bering!";
        }

        function openStudentModal() {
            document.getElementById("student-modal").classList.remove("hidden");
            setTimeout(() => {
                document.getElementById("input-student-name").focus();
            }, 100);
        }

        function closeStudentModal() {
            document.getElementById("student-modal").classList.add("hidden");
            if (!studentInfo.name && currentAppMode === "exam") {
                switchMode("practice");
            }
        }

        function requestStartExam() {
            if (!studentInfo.name) {
                openStudentModal();
            } else {
                startExamWithCountdown();
            }
        }

        function confirmStartExam(e) {
            if (e) e.preventDefault();
            const nameVal = document.getElementById("input-student-name").value.trim();
            const groupVal = document.getElementById("input-student-group").value.trim();
            const idVal = document.getElementById("input-student-id").value.trim();
            const examVal = document.getElementById("input-examiner").value.trim();

            if (!nameVal || !groupVal) {
                alert("Iltimos, Talaba F.I.SH. va Guruhini kiriting!");
                return;
            }

            studentInfo = {
                name: nameVal,
                group: groupVal,
                id: idVal || "№ 01",
                examiner: examVal || "Kafedra O'qituvchisi"
            };

            document.getElementById("hud-student-display").innerText = `Talaba: ${studentInfo.name} (${studentInfo.group})`;
            closeStudentModal();

            startExamWithCountdown();
        }

        // ==================== 3... 2... 1... TESKARI HISOB VA BOSHLASH ====================
        function startExamWithCountdown() {
            if (isExamActive) {
                resetExamState();
                return;
            }

            const overlay = document.getElementById("countdown-overlay");
            const circle = document.getElementById("countdown-number-circle");
            const sub = document.getElementById("countdown-subtitle");

            overlay.classList.remove("hidden");

            let count = 3;
            circle.innerText = count;
            circle.className = "w-36 h-36 rounded-full bg-blue-600 border-4 border-white/80 flex items-center justify-center text-white text-6xl font-black shadow-2xl animate-countdown";
            sub.innerText = "Qo'llaringizni maniken ko'kragiga qo'ying!";
            playBeep(440, 0.2);

            const countInterval = setInterval(() => {
                count--;
                if (count > 0) {
                    circle.innerText = count;
                    circle.className = "w-36 h-36 rounded-full bg-blue-600 border-4 border-white/80 flex items-center justify-center text-white text-6xl font-black shadow-2xl animate-countdown";
                    playBeep(440, 0.2);
                } else if (count === 0) {
                    circle.innerText = "🚀";
                    circle.className = "w-36 h-36 rounded-full bg-emerald-500 border-4 border-white flex items-center justify-center text-white text-6xl font-black shadow-2xl animate-countdown";
                    sub.innerText = "BOSHLANG! (Kompressiya va Nafas)";
                    playBeep(880, 0.35);
                } else {
                    clearInterval(countInterval);
                    overlay.classList.add("hidden");
                    actuallyStartExamTimer();
                }
            }, 900);
        }

        function actuallyStartExamTimer() {
            resetExamState();
            isExamActive = true;
            const btn = document.getElementById("btn-exam-toggle");
            if (btn) {
                btn.innerHTML = `<i class="fa-solid fa-stop"></i> To'xtatish`;
                btn.className = "px-4 py-2 rounded-xl font-black text-xs bg-rose-600 hover:bg-rose-500 text-white transition shadow flex items-center gap-1.5 cursor-pointer";
            }
            const finishBtn = document.getElementById("btn-exam-finish");
            if (finishBtn) finishBtn.classList.remove("hidden");

            const fb = document.getElementById("exam-live-feedback");
            if (fb) fb.innerText = "Imtihon ketyapti: Massaj va nafas bering!";

            examTimerInterval = setInterval(() => {
                examTimeLeft--;
                updateTimerDisplay();
                if (examTimeLeft <= 0) {
                    finishExamManually();
                }
            }, 1000);
        }

        function resetExamState() {
            if (examTimerInterval) clearInterval(examTimerInterval);
            isExamActive = false;
            examTimeLeft = 120;

            liveStats = {
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
            if (btn) {
                btn.innerHTML = `<i class="fa-solid fa-play"></i> Boshlash`;
                btn.className = "px-4 py-2 rounded-xl font-black text-xs bg-emerald-600 hover:bg-emerald-500 text-white transition shadow flex items-center gap-1.5 cursor-pointer";
            }
            const finishBtn = document.getElementById("btn-exam-finish");
            if (finishBtn) finishBtn.classList.add("hidden");
            const fb = document.getElementById("exam-live-feedback");
            if (fb) fb.innerText = "Tayyor: 'Boshlash' tugmasini bosing!";
        }

        function finishExamManually() {
            if (examTimerInterval) clearInterval(examTimerInterval);
            isExamActive = false;

            const total = liveStats.totalComps || 1;
            const correct = liveStats.correctComps;
            const correctPct = Math.round((correct / total) * 100);

            let avgBpm = 110;
            if (liveStats.strokeTimes.length > 2) {
                let deltas = [];
                for (let i = 1; i < liveStats.strokeTimes.length; i++) {
                    const d = liveStats.strokeTimes[i] - liveStats.strokeTimes[i-1];
                    if (d > 200 && d < 1500) deltas.push(d);
                }
                if (deltas.length > 0) {
                    const avgDelta = deltas.reduce((a, b) => a + b, 0) / deltas.length;
                    avgBpm = Math.round(60000 / avgDelta);
                }
            }

            let overallScore = correctPct;
            if (liveStats.stomachErrors > 0) {
                overallScore = Math.max(0, overallScore - (liveStats.stomachErrors * 5));
            }

            const timeSpentSecs = 120 - examTimeLeft;
            const isPassed = overallScore >= 80 && liveStats.totalComps >= 20;

            const d = new Date();
            const dateStr = `${d.getDate().toString().padStart(2, '0')}.${(d.getMonth()+1).toString().padStart(2, '0')}.${d.getFullYear()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
            const protocolNo = `CPR-${d.getFullYear()}-${Math.floor(1000 + Math.random()*9000)}`;

            const examRecord = {
                id: protocolNo,
                name: studentInfo.name || "Noma'lum Talaba",
                group: studentInfo.group || "Guruhsiz",
                ticket: studentInfo.id || "№ 01",
                examiner: studentInfo.examiner || "Kafedra O'qituvchisi",
                date: dateStr,
                timeSpent: timeSpentSecs,
                totalComps: liveStats.totalComps,
                correctComps: liveStats.correctComps,
                correctPct: correctPct,
                wrongComps: liveStats.wrongComps,
                shallowErrors: liveStats.shallowErrors,
                excessErrors: liveStats.excessErrors,
                posErrors: liveStats.posErrors,
                recoilErrors: liveStats.recoilErrors,
                totalVents: liveStats.totalVents,
                correctVents: liveStats.correctVents,
                stomachErrors: liveStats.stomachErrors,
                bpm: avgBpm,
                score: overallScore,
                passed: isPassed
            };

            // Save to LocalStorage History
            saveExamToHistory(examRecord);

            // Populate Modal & Printable Sheet
            renderProtocolFromRecord(examRecord);

            if (currentAppMode === "exam") {
                document.getElementById("exam-modal").classList.remove("hidden");
            }
        }

        function renderProtocolFromRecord(record) {
            // 1. Populate Screen Modal
            document.getElementById("modal-student-header").innerText = `Talaba: ${record.name} (${record.group})`;
            document.getElementById("modal-total-score").innerText = `${record.score}%`;
            document.getElementById("modal-time-spent").innerText = `${record.timeSpent} soniya`;
            document.getElementById("modal-total-comps").innerText = `${record.totalComps} ta`;
            document.getElementById("modal-correct-comps").innerText = `${record.correctComps} ta (${record.correctPct}%)`;
            document.getElementById("modal-wrong-comps").innerText = `${record.wrongComps} ta`;
            document.getElementById("modal-bpm-avg").innerText = `${record.bpm} /min`;

            const errDiv = document.getElementById("modal-error-details");
            errDiv.innerHTML = `
                <div>• ⚠️ Sayoz bosilgan (<38 kg): <b>${record.shallowErrors} ta</b></div>
                <div>• ⚠️ Ortiqcha qattiq bosilgan (>55 kg): <b>${record.excessErrors} ta</b></div>
                <div>• ❌ Qo'l noto'g'ri joyda bosilgan: <b>${record.posErrors} ta</b></div>
                <div>• 🔄 Ko'krak to'liq bo'shatilmagan (recoil): <b>${record.recoilErrors} ta</b></div>
            `;

            document.getElementById("modal-vent-summary").innerText = 
                `Jami: ${record.totalVents} ta | To'g'ri (2.0-3.0 kPa): ${record.correctVents} ta | Oshqozon xatosi: ${record.stomachErrors} ta`;

            const badge = document.getElementById("modal-status-badge");

            if (record.passed) {
                badge.innerText = "🏆 IMTIHONDAN O'TDI (PASSED)";
                badge.className = "px-4 py-1 rounded-full text-xs font-black uppercase tracking-widest bg-emerald-50 text-emerald-700 border border-emerald-300 inline-block mb-2";
            } else {
                badge.innerText = "❌ YIQILDI (FAILED)";
                badge.className = "px-4 py-1 rounded-full text-xs font-black uppercase tracking-widest bg-rose-50 text-rose-700 border border-rose-300 inline-block mb-2";
            }

            // 2. Populate Printable Sheet
            document.getElementById("print-protocol-no").innerText = record.id;
            document.getElementById("print-student-name").innerText = record.name;
            document.getElementById("print-student-group").innerText = record.group;
            document.getElementById("print-student-id").innerText = record.ticket;
            document.getElementById("print-exam-date").innerText = record.date;
            document.getElementById("print-exam-duration").innerText = `${record.timeSpent} soniya`;
            document.getElementById("print-examiner").innerText = record.examiner;

            document.getElementById("print-status-text").innerText = record.passed ? "🏆 IMTIHONDAN O'TDI (PASSED)" : "❌ YIQILDI (FAILED)";
            document.getElementById("print-status-text").style.color = record.passed ? "#15803d" : "#b91c1c";
            document.getElementById("print-total-pct").innerText = `${record.score}%`;

            document.getElementById("print-val-total-comps").innerText = `${record.totalComps} ta`;
            document.getElementById("print-res-total-comps").innerText = record.totalComps >= 20 ? "Qoniqarli" : "Kam";

            document.getElementById("print-val-correct-comps").innerText = `${record.correctComps} ta (${record.correctPct}%)`;
            document.getElementById("print-res-correct-comps").innerText = record.correctPct >= 80 ? "A'lo" : "Yetarli emas";

            document.getElementById("print-val-recoil").innerText = `${record.recoilErrors} ta xato`;
            document.getElementById("print-res-recoil").innerText = record.recoilErrors === 0 ? "Mukammal" : "E'tibor bering";

            document.getElementById("print-val-bpm").innerText = `${record.bpm} /min`;
            document.getElementById("print-res-bpm").innerText = (record.bpm >= 100 && record.bpm <= 120) ? "Me'yorda" : "Tuzatish lozim";

            document.getElementById("print-val-vents").innerText = `${record.correctVents} / ${record.totalVents} to'g'ri`;
            document.getElementById("print-res-vents").innerText = record.correctVents > 0 ? "Muvaffaqiyatli" : "Nafas berilmadi";

            document.getElementById("print-val-stomach").innerText = `${record.stomachErrors} ta`;
            document.getElementById("print-res-stomach").innerText = record.stomachErrors === 0 ? "Toza" : "XATO (Oshqozon)";

            const printErrList = document.getElementById("print-error-list");
            printErrList.innerHTML = `
                <div>• Sayoz bosilgan (<38 kg): <b>${record.shallowErrors} ta</b></div>
                <div>• Ortiqcha qattiq bosilgan (>55 kg): <b>${record.excessErrors} ta</b></div>
                <div>• Qo'l noto'g'ri nuqtada bosilgan: <b>${record.posErrors} ta</b></div>
                <div>• Ko'krak to'liq bo'shatilmagan (recoil): <b>${record.recoilErrors} ta</b></div>
                <div>• Oshqozonga havo qochishi: <b>${record.stomachErrors} ta</b></div>
            `;
        }

        // ==================== CPR SUCCESS STATE ====================
        function resetRevivalEffects() {}
        function triggerPatientRevivalEffect() {}

        // ==================== PERSISTENT EXAM HISTORY STORAGE & MANAGEMENT ====================
        let isHistoryPanelOpen = true;

        function toggleHistoryPanel() {
            isHistoryPanelOpen = !isHistoryPanelOpen;
            const wrapper = document.getElementById("history-content-wrapper");
            const icon = document.getElementById("history-panel-icon");
            const txt = document.getElementById("history-panel-status-text");

            if (isHistoryPanelOpen) {
                wrapper.classList.remove("hidden");
                icon.style.transform = "rotate(0deg)";
                txt.innerText = "Yopish";
            } else {
                wrapper.classList.add("hidden");
                icon.style.transform = "rotate(180deg)";
                txt.innerText = "Ochish";
            }
        }

        function onHistoryFilterChange() {
            renderExamHistory();
        }

        function getExamHistory() {
            try {
                const raw = localStorage.getItem("cpr_exam_records");
                return raw ? JSON.parse(raw) : [];
            } catch(e) {
                return [];
            }
        }

        function saveExamToHistory(record) {
            try {
                const list = getExamHistory();
                list.unshift(record); // Add to top
                localStorage.setItem("cpr_exam_records", JSON.stringify(list));
                renderExamHistory();
            } catch(e) {}
        }

        function deleteSingleExamRecord(id) {
            const list = getExamHistory().filter(r => r.id !== id);
            localStorage.setItem("cpr_exam_records", JSON.stringify(list));
            renderExamHistory();
        }

        function clearAllExamHistory() {
            const list = getExamHistory();
            if (list.length === 0) {
                alert("Tarix allaqachon bo'sh!");
                return;
            }
            if (confirm("Haqiqatan ham barcha saqlangan imtihon natijalarini o'chirmoqchimisiz?")) {
                localStorage.removeItem("cpr_exam_records");
                renderExamHistory();
            }
        }

        function openHistoryRecord(id) {
            const record = getExamHistory().find(r => r.id === id);
            if (record) {
                renderProtocolFromRecord(record);
                document.getElementById("exam-modal").classList.remove("hidden");
            }
        }

        function renderExamHistory() {
            let list = getExamHistory();
            const container = document.getElementById("history-list-container");
            const emptyEl = document.getElementById("history-empty-placeholder");
            const badge = document.getElementById("history-count-badge");

            if (badge) badge.innerText = `${list.length} ta`;

            const searchInput = document.getElementById("history-search-input");
            const filterStatus = document.getElementById("history-filter-status");
            const sortBy = document.getElementById("history-sort-by");

            const query = searchInput ? searchInput.value.trim().toLowerCase() : "";
            const statusVal = filterStatus ? filterStatus.value : "all";
            const sortVal = sortBy ? sortBy.value : "newest";

            // 1. Filter by Search Query
            if (query) {
                list = list.filter(item => {
                    const name = (item.name || "").toLowerCase();
                    const group = (item.group || "").toLowerCase();
                    const id = (item.id || "").toLowerCase();
                    const ticket = (item.ticket || "").toLowerCase();
                    const date = (item.date || "").toLowerCase();
                    return name.includes(query) || group.includes(query) || id.includes(query) || ticket.includes(query) || date.includes(query);
                });
            }

            // 2. Filter by Status (Passed / Failed)
            if (statusVal === "passed") {
                list = list.filter(item => item.passed);
            } else if (statusVal === "failed") {
                list = list.filter(item => !item.passed);
            }

            // 3. Sort
            if (sortVal === "newest") {
                // Already newest first
            } else if (sortVal === "oldest") {
                list = [...list].reverse();
            } else if (sortVal === "score_desc") {
                list = [...list].sort((a, b) => (b.score || 0) - (a.score || 0));
            } else if (sortVal === "score_asc") {
                list = [...list].sort((a, b) => (a.score || 0) - (b.score || 0));
            } else if (sortVal === "name_asc") {
                list = [...list].sort((a, b) => (a.name || "").localeCompare(b.name || ""));
            }

            if (list.length === 0) {
                if (container) container.innerHTML = "";
                if (emptyEl) {
                    emptyEl.classList.remove("hidden");
                    emptyEl.innerText = query ? "Qidiruv bo'yicha hech qanday natija topilmadi." : "Hali topshirilgan imtihonlar mavjud emas.";
                }
                return;
            }

            if (emptyEl) emptyEl.classList.add("hidden");
            if (!container) return;

            container.innerHTML = list.map(item => `
                <div class="flex flex-col sm:flex-row sm:items-center justify-between p-3 rounded-xl border ${item.passed ? 'bg-emerald-50/40 border-emerald-200' : 'bg-rose-50/40 border-rose-200'} text-xs gap-2 transition hover:shadow-sm">
                    <div class="flex flex-col">
                        <div class="font-black text-slate-900 flex items-center gap-1.5">
                            <span>${item.name}</span>
                            <span class="text-[11px] font-semibold text-slate-500">(${item.group})</span>
                            <span class="text-[10px] text-slate-400">${item.ticket ? '[' + item.ticket + ']' : ''}</span>
                        </div>
                        <div class="text-[11px] text-slate-500 mt-0.5 flex flex-wrap gap-x-2">
                            <span>📅 ${item.date}</span>
                            <span>• Kompressiya: <b>${item.correctComps}/${item.totalComps}</b> (${item.correctPct || 0}%)</span>
                            <span>• Nafas: <b>${item.correctVents}</b></span>
                            <span>• Tezlik: <b>${item.bpm || 110} BPM</b></span>
                        </div>
                    </div>

                    <div class="flex items-center gap-2 self-end sm:self-center">
                        <span class="px-2.5 py-1 rounded-lg text-xs font-black ${item.passed ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' : 'bg-rose-100 text-rose-800 border border-rose-300'}">
                            ${item.score}% (${item.passed ? "O'TDI" : "YIQILDI"})
                        </span>
                        
                        <button type="button" onclick="openHistoryRecord('${item.id}')" title="Protokolni ko'rish va chop etish" class="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs transition shadow-sm cursor-pointer flex items-center gap-1">
                            <i class="fa-solid fa-print"></i> Protokol
                        </button>
                        
                        <button type="button" onclick="deleteSingleExamRecord('${item.id}')" title="O'chirish" class="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition cursor-pointer">
                            <i class="fa-solid fa-trash-can text-sm"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        }

        function printExamProtocol() {
            window.print();
        }

        function updateTimerDisplay() {
            const el = document.getElementById("exam-timer");
            if (!el) return;
            const mins = Math.floor(examTimeLeft / 60);
            const secs = examTimeLeft % 60;
            const str = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
            el.innerText = str;
            if (examTimeLeft <= 20) {
                el.className = "mono text-xl font-black text-rose-600 tracking-wider bg-rose-50 px-3 py-1 rounded-xl border border-rose-300 animate-pulse";
            } else {
                el.className = "mono text-xl font-black text-slate-900 tracking-wider bg-slate-100 px-3 py-1 rounded-xl border border-slate-300";
            }
        }

        function updateExamHUD() {
            const elTotal = document.getElementById("stat-total-comps");
            if (!elTotal) return;

            elTotal.innerText = liveStats.totalComps;
            document.getElementById("stat-correct-comps").innerText = liveStats.correctComps;
            
            const total = liveStats.totalComps;
            const pct = total > 0 ? Math.round((liveStats.correctComps / total) * 100) : 100;
            document.getElementById("stat-correct-pct").innerText = `${pct}% to'g'ri`;

            document.getElementById("stat-wrong-comps").innerText = liveStats.wrongComps;
            document.getElementById("stat-wrong-reasons").innerText = `${liveStats.wrongComps} ta xato`;

            document.getElementById("stat-total-vents").innerText = liveStats.totalVents;
            document.getElementById("stat-vent-status").innerText = `${liveStats.correctVents} to'g'ri`;

            document.getElementById("stat-live-quality").innerText = `${pct}%`;
            const qBar = document.getElementById("stat-quality-bar");
            qBar.style.width = `${pct}%`;

            if (pct >= 80) {
                qBar.className = "bg-emerald-500 h-full rounded-full transition-all duration-150";
                document.getElementById("stat-live-quality").className = "mono font-black text-emerald-600 text-sm";
            } else if (pct >= 50) {
                qBar.className = "bg-amber-500 h-full rounded-full transition-all duration-150";
                document.getElementById("stat-live-quality").className = "mono font-black text-amber-600 text-sm";
            } else {
                qBar.className = "bg-rose-500 h-full rounded-full transition-all duration-150";
                document.getElementById("stat-live-quality").className = "mono font-black text-rose-600 text-sm";
            }

            updateTimerDisplay();
        }

        function closeModal() {
            document.getElementById("exam-modal").classList.add("hidden");
            resetExamState();
        }

        function restartExam() {
            closeModal();
            requestStartExam();
        }

        // ==================== REAL ACTION STROKE ANALYZER (BOTH MODES) ====================
        let cprStrokeState = "idle";
        let cprPeak = 0;
        let cprPosAtPeak = false;

        function processExamHardware(forceKg, lungKpa, stomachKpa, posBtn) {
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
                    cprStrokeState = "recoiling";
                    liveStats.totalComps++;
                    liveStats.strokeTimes.push(now);

                    let strokeErrors = [];

                    if (cprPeak < 38.0) {
                        liveStats.shallowErrors++;
                        strokeErrors.push("Sayoz (<38kg)");
                    } else if (cprPeak > 55.0) {
                        liveStats.excessErrors++;
                        strokeErrors.push("Juda qattiq (>55kg)");
                    }

                    if (!cprPosAtPeak) {
                        liveStats.posErrors++;
                        strokeErrors.push("Qo'l noto'g'ri joyda");
                    }

                    const fb = document.getElementById("exam-live-feedback");
                    const pfb = document.getElementById("practice-feedback-text");

                    if (strokeErrors.length === 0) {
                        liveStats.correctComps++;
                        if (fb) {
                            fb.innerText = `✅ To'g'ri zarba (${cprPeak.toFixed(1)} kg)`;
                            fb.className = "text-xs font-bold text-emerald-600";
                        }
                        if (pfb) {
                            pfb.innerText = `✅ A'LO ZARBA: ${cprPeak.toFixed(1)} kg (Me'yor: 38-55 kg)`;
                            pfb.className = "text-emerald-600 font-bold";
                        }
                    } else {
                        liveStats.wrongComps++;
                        const errStr = strokeErrors.join(', ');
                        if (fb) {
                            fb.innerText = `❌ Xato: ${errStr}`;
                            fb.className = "text-xs font-bold text-rose-600";
                        }
                        if (pfb) {
                            pfb.innerText = `❌ XATO: ${errStr} (${cprPeak.toFixed(1)} kg)`;
                            pfb.className = "text-rose-600 font-bold";
                        }
                    }

                    updateExamHUD();
                }
            } else if (cprStrokeState === "recoiling") {
                if (forceKg <= 5.0) {
                    cprStrokeState = "idle";
                } else if (forceKg > (cprPeak - 1.0) && forceKg > 5.0) {
                    liveStats.recoilErrors++;
                    cprStrokeState = "compressing";
                    cprPeak = forceKg;
                }
            }

            // 2. Process Ventilation Breath
            if (lungKpa >= 1.0 && !window._ventTriggered) {
                window._ventTriggered = true;
                liveStats.totalVents++;

                const fb = document.getElementById("exam-live-feedback");
                const pfb = document.getElementById("practice-feedback-text");

                if (lungKpa >= 2.0 && lungKpa <= 3.0) {
                    liveStats.correctVents++;
                    if (fb) {
                        fb.innerText = `🫁 ✅ A'lo nafas (${lungKpa.toFixed(1)} kPa)`;
                        fb.className = "text-xs font-bold text-sky-600";
                    }
                    if (pfb) {
                        pfb.innerText = `🫁 ✅ TO'G'RI NAFAS: ${lungKpa.toFixed(1)} kPa (20-30 cmH2O)`;
                        pfb.className = "text-sky-600 font-bold";
                    }
                } else if (lungKpa < 2.0) {
                    if (fb) {
                        fb.innerText = `🫁 ⚠️ Kam havo (<2.0 kPa)`;
                        fb.className = "text-xs font-bold text-amber-600";
                    }
                    if (pfb) {
                        pfb.innerText = `🫁 ⚠️ QATTIQROQ SIQING: Kam havo (${lungKpa.toFixed(1)} kPa < 2.0)`;
                        pfb.className = "text-amber-600 font-bold";
                    }
                } else {
                    if (fb) {
                        fb.innerText = `🫁 🚨 Ortiqcha bosim (>3.0 kPa)`;
                        fb.className = "text-xs font-bold text-rose-600";
                    }
                    if (pfb) {
                        pfb.innerText = `🫁 🚨 JUDA KUCHLI: Barotravma xavfi (${lungKpa.toFixed(1)} kPa > 3.0)`;
                        pfb.className = "text-rose-600 font-bold";
                    }
                }

                updateExamHUD();
            } else if (lungKpa < 0.5) {
                window._ventTriggered = false;
            }

            // 3. Process Stomach Hazard
            if (stomachKpa > 0.8 && !window._stomachTriggered) {
                window._stomachTriggered = true;
                liveStats.stomachErrors++;
                const fb = document.getElementById("exam-live-feedback");
                const pfb = document.getElementById("practice-feedback-text");
                if (fb) {
                    fb.innerText = `⚠️ XATO: Havo oshqozonga ketdi!`;
                    fb.className = "text-xs font-bold text-rose-600 animate-pulse";
                }
                if (pfb) {
                    pfb.innerText = `⚠️ XATO: Havo oshqozonga qochdi! Boshni to'g'ri buking.`;
                    pfb.className = "text-rose-600 font-bold animate-pulse";
                }
                updateExamHUD();
            } else if (stomachKpa < 0.3) {
                window._stomachTriggered = false;
            }
        }

        // ==================== RENDER LED BARS (DIRECT INLINE COLORS) ====================
        function renderBars(forceKg, lungKpa) {
            const forcePercent = Math.min(1.0, Math.max(0, forceKg / 60.0));
            const activeForceSegments = Math.round(forcePercent * NUM_SEGMENTS);

            for (let i = 0; i < NUM_SEGMENTS; i++) {
                const seg = document.getElementById(`force-bar-container-seg-${i}`);
                if (!seg) continue;

                if (i < activeForceSegments) {
                    const segPercent = i / NUM_SEGMENTS;
                    if (segPercent < 0.60) {
                        seg.style.backgroundColor = "#facc15";
                        seg.style.boxShadow = "0 0 12px #facc15";
                    } else if (segPercent <= 0.88) {
                        seg.style.backgroundColor = "#22c55e";
                        seg.style.boxShadow = "0 0 16px #22c55e, inset 0 0 4px #ffffff";
                    } else {
                        seg.style.backgroundColor = "#ef4444";
                        seg.style.boxShadow = "0 0 16px #ef4444, inset 0 0 4px #ffffff";
                    }
                } else {
                    seg.style.backgroundColor = "#331414";
                    seg.style.boxShadow = "none";
                }
            }
            const forceText = document.getElementById("force-val-text");
            if (forceText) forceText.innerText = `${forceKg.toFixed(1)} kg`;

            // 2. Render Lung Pressure Bar
            const lungPercent = Math.min(1.0, Math.max(0, lungKpa / 3.5));
            const activeLungSegments = Math.round(lungPercent * NUM_SEGMENTS);

            for (let i = 0; i < NUM_SEGMENTS; i++) {
                const seg = document.getElementById(`lung-bar-container-seg-${i}`);
                if (!seg) continue;

                if (i < activeLungSegments) {
                    const segPercent = i / NUM_SEGMENTS;
                    if (segPercent < 0.55) {
                        seg.style.backgroundColor = "#facc15";
                        seg.style.boxShadow = "0 0 12px #facc15";
                    } else if (segPercent <= 0.88) {
                        seg.style.backgroundColor = "#22c55e";
                        seg.style.boxShadow = "0 0 16px #22c55e, inset 0 0 4px #ffffff";
                    } else {
                        seg.style.backgroundColor = "#ef4444";
                        seg.style.boxShadow = "0 0 16px #ef4444, inset 0 0 4px #ffffff";
                    }
                } else {
                    seg.style.backgroundColor = "#331414";
                    seg.style.boxShadow = "none";
                }
            }
            const lungText = document.getElementById("lung-val-text");
            if (lungText) lungText.innerText = `${lungKpa.toFixed(1)} kPa`;

            // 3. Airway Pulse LED
            const airwayLed = document.getElementById("led-airway");
            if (airwayLed) {
                if (lungKpa > 0.8) {
                    airwayLed.classList.add("airway-led-on");
                } else {
                    airwayLed.classList.remove("airway-led-on");
                }
            }
        }

        // ==================== UPDATE POSITION, INJECTION & STOMACH LEDS ====================
        function updateIndicators(posBtn, stomachKpa, injBtn) {
            // Position LED (Chest Center - Pin 13)
            const posLed = document.getElementById("led-position");
            const posLbl = document.getElementById("pos-btn-text");
            if (posLed) {
                if (posBtn === 1 || posBtn === true) {
                    posLed.classList.add("pos-led-on");
                    if (posLbl) {
                        posLbl.innerText = "BOSILDI";
                        posLbl.className = "text-emerald-600 font-black";
                    }
                } else {
                    posLed.classList.remove("pos-led-on");
                    if (posLbl) {
                        posLbl.innerText = "BO'SH";
                        posLbl.className = "text-rose-600 font-black";
                    }
                }
            }

            // Injection LED (Right Arm Vein - Pin 4)
            const injLed = document.getElementById("led-injection");
            const alertBox = document.getElementById("console-alert-box");
            const alertText = document.getElementById("console-alert-text");

            if (injLed) {
                if (injBtn === 1 || injBtn === true) {
                    injLed.classList.add("inj-led-on");
                    if (alertBox && alertText) {
                        alertBox.classList.remove("hidden");
                        alertBox.className = "mt-2 p-2.5 rounded-xl bg-purple-50 border border-purple-300 text-purple-900 text-xs font-bold text-center flex items-center justify-center gap-2 shadow-sm animate-pulse";
                        alertText.innerText = "💉 INYEKSIYA (UKOL TOMIRGA KIRDI!)";
                    }
                } else {
                    injLed.classList.remove("inj-led-on");
                }
            }

            // Stomach Warning LED
            const stomachLed = document.getElementById("led-stomach");
            if (stomachLed) {
                if (stomachKpa > 0.6) {
                    stomachLed.classList.add("stomach-led-on");
                    if (alertBox && alertText) {
                        alertBox.classList.remove("hidden");
                        alertBox.className = "mt-2 p-2.5 rounded-xl bg-rose-50 border border-rose-300 text-rose-900 text-xs font-bold text-center flex items-center justify-center gap-2 shadow-sm animate-pulse";
                        alertText.innerText = `⚠️ HAVO OSHQOZONDA! (${stomachKpa.toFixed(1)} kPa)`;
                    }
                } else {
                    stomachLed.classList.remove("stomach-led-on");
                    if (alertBox && !injBtn) alertBox.classList.add("hidden");
                }
            }
        }

        // ==================== TARE & ZEROING KALIBROVKA (BOSHLANG'ICH MASSANI 0 QILISH) ====================
        let forceTareOffset = 0.0;
        let lastRawForce = 0.0;
        let isInitialTareCaptured = false;
        let initialTareSamples = [];

        // Sahifa yuklanganda saqlangan tare kalibrovkani o'qish
        try {
            const savedTare = localStorage.getItem("manikin_force_tare");
            if (savedTare !== null) {
                forceTareOffset = parseFloat(savedTare) || 0.0;
                isInitialTareCaptured = true;
            }
        } catch(e) {}

        function tareForceSensor(manualOffset = null) {
            if (manualOffset !== null) {
                forceTareOffset = manualOffset;
            } else {
                forceTareOffset = lastRawForce;
            }
            try {
                localStorage.setItem("manikin_force_tare", forceTareOffset.toFixed(2));
            } catch(e) {}
            
            // Datchik chipiga ham TARE buyrug'ini yuborish (agar Web Serial ulangan bo'lsa)
            sendDirectSerialCommand("TARE");
            
            showTareToast(`⚖️ Kuch 0.0 kg ga sozlandi (Tare: -${forceTareOffset.toFixed(1)} kg)`);
            renderBars(0.0, 0.0);
        }

        function resetTareSensor() {
            forceTareOffset = 0.0;
            isInitialTareCaptured = false;
            initialTareSamples = [];
            try {
                localStorage.removeItem("manikin_force_tare");
            } catch(e) {}
            showTareToast(`↺ Kalibrovka asliga qaytarildi (0.0 kg)`);
        }

        function showTareToast(msg) {
            let toast = document.getElementById("tare-toast");
            if (!toast) {
                toast = document.createElement("div");
                toast.id = "tare-toast";
                toast.className = "fixed bottom-6 left-1/2 -translate-x-1/2 bg-slate-900 text-emerald-300 border border-emerald-500/50 px-4 py-2 rounded-xl text-xs font-black shadow-2xl z-50 pointer-events-none transition-all duration-300";
                document.body.appendChild(toast);
            }
            toast.innerText = msg;
            toast.style.opacity = "1";
            toast.style.transform = "translate(-50%, 0)";
            setTimeout(() => {
                toast.style.opacity = "0";
                toast.style.transform = "translate(-50%, 15px)";
            }, 2500);
        }

        // ==================== CENTRAL TELEMETRY HANDLER ====================
        function handleIncomingTelemetryData(data) {
            const rawForce = parseFloat(data.force !== undefined ? data.force : (data.f_curr || 0));
            lastRawForce = rawForce;

            // Boshlang'ich vaznni 0 deb olish (Boshida tinch turganda avtomatik nolga sozlaydi)
            if (!isInitialTareCaptured) {
                if (rawForce < 15.0) {
                    initialTareSamples.push(rawForce);
                    if (initialTareSamples.length >= 4) {
                        const avg = initialTareSamples.reduce((a, b) => a + b, 0) / initialTareSamples.length;
                        if (avg > 0.15) {
                            forceTareOffset = avg;
                            try {
                                localStorage.setItem("manikin_force_tare", forceTareOffset.toFixed(2));
                            } catch(e) {}
                        }
                        isInitialTareCaptured = true;
                    }
                } else {
                    isInitialTareCaptured = true;
                }
            }

            // Boshlang'ich massa ayirib tashlangan sof ko'krak kuchi:
            let force = Math.max(0, rawForce - forceTareOffset);
            if (force < 0.2) force = 0.0; // Tinch holatdagi shovqinni nolga tenglash

            const lungP = parseFloat(data.lung_p || 0);
            const stomachP = parseFloat(data.stomach_p || 0);
            const posBtn = data.pos_btn !== undefined ? data.pos_btn : (data.pos_ok ? 1 : 0);
            const injBtn = data.inj_btn !== undefined ? data.inj_btn : (data.inj_ok ? 1 : 0);

            renderBars(force, lungP);
            updateIndicators(posBtn, stomachP, injBtn);
            processExamHardware(force, lungP, stomachP, posBtn);
        }

        // ==================== DIRECT WEB SERIAL API (NO PYTHON / ONE-CLICK USB) ====================
        let directSerialPort = null;
        let directSerialReader = null;
        let directSerialWriter = null;
        let directSerialBuffer = "";

        async function connectDirectSerial() {
            if (!("serial" in navigator)) {
                alert("Brauzeringiz Web Serial API-ni qo'llab-quvvatlamaydi. Iltimos Google Chrome yoki Microsoft Edge brauzeridan foydalaning!");
                return;
            }
            try {
                directSerialPort = await navigator.serial.requestPort();
                await directSerialPort.open({ baudRate: 115200 });

                const btn = document.getElementById("btn-direct-serial");
                const btnText = document.getElementById("btn-serial-text");
                if (btn) btn.className = "px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl transition text-xs flex items-center gap-1.5 shadow";
                if (btnText) btnText.innerText = "✅ Maniken Ulandi (USB)";

                const dot = document.getElementById("conn-dot");
                if (dot) dot.className = "w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_8px_#22c55e]";
                const st = document.getElementById("conn-status");
                if (st) st.innerText = "USB WEB SERIAL: JONLI OQIM (0ms)";

                // Writer for sending commands (ROSC, Pulse, etc.)
                const textEncoder = new TextEncoderStream();
                textEncoder.readable.pipeTo(directSerialPort.writable);
                directSerialWriter = textEncoder.writable.getWriter();

                readDirectSerialLoop();
            } catch(err) {
                console.error("Web Serial ulanish xatosi:", err);
            }
        }

        async function sendDirectSerialCommand(cmd) {
            if (directSerialWriter) {
                try {
                    await directSerialWriter.write(cmd + String.fromCharCode(10));
                } catch(e) {}
            }
        }

        async function readDirectSerialLoop() {
            try {
                const textDecoder = new TextDecoderStream();
                directSerialPort.readable.pipeTo(textDecoder.writable);
                directSerialReader = textDecoder.readable.getReader();

                while (true) {
                    const { value, done } = await directSerialReader.read();
                    if (done) break;
                    if (value) {
                        directSerialBuffer += value;
                        let lines = directSerialBuffer.split(String.fromCharCode(10));
                        directSerialBuffer = lines.pop();
                        for (let line of lines) {
                            line = line.trim();
                            if (line.startsWith("{") && line.endsWith("}")) {
                                try {
                                    const data = JSON.parse(line);
                                    handleIncomingTelemetryData(data);
                                    if (ws && ws.readyState === WebSocket.OPEN) {
                                        ws.send(line);
                                    }
                                } catch(e) {}
                            }
                        }
                    }
                }
            } catch(err) {
                console.warn("Web Serial oqimi tugadi:", err);
                const btn = document.getElementById("btn-direct-serial");
                const btnText = document.getElementById("btn-serial-text");
                if (btn) btn.className = "px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl transition text-xs flex items-center gap-1.5 shadow";
                if (btnText) btnText.innerText = "🔌 Qayta Ulanish (USB)";
            }
        }

        // ==================== WEBSOCKET LIVE TELEMETRY ====================
        let ws;
        function connectWS() {
            try {
                let wsHost = window.location.host;
                if (!wsHost || wsHost === "") wsHost = "127.0.0.1:8600";
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                ws = new WebSocket(`${protocol}//${wsHost}/ws/telemetry`);

                ws.onopen = () => {
                    const dot = document.getElementById("conn-dot");
                    if (dot && (!directSerialPort)) dot.className = "w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_8px_#22c55e]";
                    const st = document.getElementById("conn-status");
                    if (st && (!directSerialPort)) st.innerText = "ESP32 UART: JONLI ALOQA (0ms)";
                };

                ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        handleIncomingTelemetryData(data);
                    } catch(e) {}
                };

                ws.onclose = () => {
                    const dot = document.getElementById("conn-dot");
                    if (dot) dot.className = "w-2.5 h-2.5 rounded-full bg-amber-400";
                    const st = document.getElementById("conn-status");
                    if (st) st.innerText = "ESP32 UART: Qayta ulanmoqda...";
                    setTimeout(connectWS, 1500);
                };

                ws.onerror = () => {
                    const dot = document.getElementById("conn-dot");
                    if (dot) dot.className = "w-2.5 h-2.5 rounded-full bg-amber-400";
                    const st = document.getElementById("conn-status");
                    if (st) st.innerText = "ESP32: Dasturiy rejim (Lokal)";
                };
            } catch(e) {}
        }

        // ==================== MANUAL TEST HELPERS ====================
        let simPos = 0;
        let simInj = 0;
        let simStomach = 0;

        function onSimInput() {
            const f = parseFloat(document.getElementById("sim-force").value);
            const l = parseFloat(document.getElementById("sim-lung").value);
            const lblF = document.getElementById("sim-force-lbl");
            if (lblF) lblF.innerText = `${f.toFixed(1)} kg`;
            const cm = (l * 10.2).toFixed(0);
            const lblL = document.getElementById("sim-lung-lbl");
            if (lblL) lblL.innerText = `${l.toFixed(1)} kPa (${cm} cmH2O)`;

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

        function simSingleStroke(targetForce = 45.0) {
            simPos = 1;
            const steps = [12, 28, targetForce, targetForce - 10, 15, 0];
            let idx = 0;
            const iv = setInterval(() => {
                if (idx < steps.length) {
                    const fEl = document.getElementById("sim-force");
                    if (fEl) fEl.value = steps[idx];
                    onSimInput();
                    idx++;
                } else {
                    clearInterval(iv);
                }
            }, 55);
        }

        function simSingleBreath(targetKpa = 2.6) {
            const steps = [0.8, 1.8, targetKpa, 1.2, 0];
            let idx = 0;
            const iv = setInterval(() => {
                if (idx < steps.length) {
                    const lEl = document.getElementById("sim-lung");
                    if (lEl) lEl.value = steps[idx];
                    onSimInput();
                    idx++;
                } else {
                    clearInterval(iv);
                }
            }, 80);
        }

        // ==================== PWA INSTALL & FULLSCREEN (SENSORLI KIOSK) ====================
        let deferredPromptConsole = null;
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js').catch(() => {});
            });
        }
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPromptConsole = e;
            const btn = document.getElementById('pwa-console-btn');
            if (btn) btn.classList.remove('hidden');
        });
        async function installConsolePWA() {
            if (deferredPromptConsole) {
                deferredPromptConsole.prompt();
                const { outcome } = await deferredPromptConsole.userChoice;
                if (outcome === 'accepted') {
                    const btn = document.getElementById('pwa-console-btn');
                    if (btn) btn.classList.add('hidden');
                }
                deferredPromptConsole = null;
            } else {
                alert("Ilovani o'rnatish uchun brauzer menyusidagi 'O'rnatish' (Install App) tugmasini bosing.");
            }
        }
        function toggleFullScreenConsole() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(() => {});
            } else {
                if (document.exitFullscreen) document.exitFullscreen().catch(() => {});
            }
        }

        window.onload = () => {
            connectWS();
            renderExamHistory();
            onSimInput();
        };
    </script>
</body>
</html>
"""

NO_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0"
}

@app.get("/", response_class=HTMLResponse)
async def get_index():
    return HTMLResponse(content=HTML_CONTENT, headers=NO_CACHE_HEADERS)

@app.get("/console", response_class=HTMLResponse)
async def get_console():
    return HTMLResponse(content=HTML_CONTENT, headers=NO_CACHE_HEADERS)

@app.get("/pult", response_class=HTMLResponse)
async def get_pult():
    return HTMLResponse(content=HTML_CONTENT, headers=NO_CACHE_HEADERS)

@app.get("/exam", response_class=HTMLResponse)
async def get_exam():
    return HTMLResponse(content=HTML_CONTENT, headers=NO_CACHE_HEADERS)

def open_browser_delayed(url):
    import time
    time.sleep(0.8)
    try:
        webbrowser.open(url)
    except:
        pass

@app.on_event("startup")
async def on_startup():
    port = int(os.environ.get("PORT", 8600))
    threading.Thread(target=open_browser_delayed, args=(f"http://localhost:{port}",), daemon=True).start()

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
