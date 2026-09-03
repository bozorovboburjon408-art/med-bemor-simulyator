# -*- coding: utf-8 -*-
"""
MedLife Intubation Manikin Simulator - Intubatsiya Simulyatori
Medical White Theme + Web Serial API + Anatomiya Overlay + Congratulatory Modal Animation
"""

INTUBATION_HTML = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>MedLife — Intubatsiya Simulyatori</title>
    <meta name="theme-color" content="#ffffff">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@400;500;600;700;800;900&display=swap');
        * { -webkit-touch-callout: none; touch-action: manipulation; }
        body { font-family: 'Inter', sans-serif; background-color: #f8fafc; color: #0f172a; }
        .mono { font-family: 'Share Tech Mono', monospace; }
        
        @keyframes mk-ping {
            0% { transform: translate(-50%, -50%) scale(0.6); opacity: 0.85; }
            100% { transform: translate(-50%, -50%) scale(3.2); opacity: 0; }
        }
        .ping-effect { animation: mk-ping 1.2s cubic-bezier(0, 0, 0.2, 1) infinite; }
        
        @keyframes mk-confetti {
            0% { transform: translate3d(0, -10%, 0) rotate(var(--rot)); opacity: 1; }
            100% { transform: translate3d(var(--drift), 110vh, 0) rotate(calc(var(--rot) + 1080deg)); opacity: 0.95; }
        }
        @keyframes mk-burst {
            0% { transform: translate(-50%,-50%) scale(0.2); opacity: 0.95; }
            60% { opacity: 0.4; }
            100% { transform: translate(-50%,-50%) scale(4); opacity: 0; }
        }
        @keyframes modalPop {
            0% { transform: scale(0.85); opacity: 0; }
            100% { transform: scale(1); opacity: 1; }
        }
        .animate-pop { animation: modalPop 0.35s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; }
    </style>
</head>
<body class="min-h-screen flex flex-col justify-between p-3 md:p-6 bg-slate-50">

    <!-- HEADER (Medical White) -->
    <header class="flex flex-wrap items-center justify-between gap-4 bg-white border border-slate-200 rounded-2xl px-5 py-3.5 shadow-sm">
        <div class="flex items-center gap-3">
            <a href="/hub" class="w-10 h-10 rounded-xl bg-slate-100 hover:bg-slate-200 border border-slate-300 flex items-center justify-center text-slate-700 transition">
                <i class="fa-solid fa-house"></i>
            </a>
            <div>
                <h1 class="text-lg md:text-xl font-black text-slate-900 flex items-center gap-2">
                    INTUBATSIYA MODULI <span class="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full font-mono font-bold">Simulyatsiya & Amaliyot</span>
                </h1>
                <p class="text-xs text-slate-500 font-medium">Traxeya trubkasi va sensorlar real-vaqt monitoringi</p>
            </div>
        </div>

        <div class="flex items-center gap-3">
            <!-- SOUND TOGGLE -->
            <button id="sound-btn" onclick="toggleSound()" class="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 border border-slate-300 text-xs font-bold flex items-center gap-2 text-emerald-700 transition cursor-pointer">
                <i id="sound-icon" class="fa-solid fa-volume-high"></i>
                <span id="sound-text" class="hidden sm:inline">Ovoz Yoniq</span>
            </button>
            
            <!-- STATUS BADGE -->
            <div id="connection-badge" class="px-3.5 py-1.5 rounded-xl bg-slate-100 border border-slate-300 text-slate-600 text-xs font-bold flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full bg-slate-400"></span>
                <span id="status-text">Ulanmagan</span>
            </div>
        </div>
    </header>

    <!-- MAIN CONTENT -->
    <main class="my-4 grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-7xl mx-auto w-full">

        <!-- LEFT COL: ANATOMY & DIAGNOSIS (7 cols) -->
        <div class="lg:col-span-7 flex flex-col gap-4">
            
            <!-- ANATOMY CANVAS OVERLAY -->
            <div class="relative w-full overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm" style="aspect-ratio: 1536 / 1024;">
                <img src="/intubation/assets/tibbiy_sensor_anatomy.svg" alt="Maniken Anatomiyasi" class="absolute inset-0 w-full h-full object-contain pointer-events-none">
                
                <!-- CONFETTI CONTAINER -->
                <div id="confetti-holder" class="pointer-events-none absolute inset-0 z-30 overflow-hidden hidden">
                    <div id="confetti-pieces"></div>
                    <span class="absolute left-1/2 top-1/3 size-32 -translate-x-1/2 -translate-y-1/2 rounded-full blur-2xl bg-emerald-400 opacity-0" style="animation: mk-burst 3.5s ease-out forwards;"></span>
                </div>

                <!-- OVERLAY SENSOR INDICATORS -->
                <!-- 1. TEETH (Tish) -->
                <div id="dot-teeth" class="absolute -translate-x-1/2 -translate-y-1/2" style="left: 33.9%; top: 29.2%;">
                    <span id="ping-teeth" class="hidden absolute left-1/2 top-1/2 w-8 h-8 -translate-x-1/2 -translate-y-1/2 rounded-full bg-rose-500/40 ping-effect"></span>
                    <span id="glow-teeth" class="hidden absolute left-1/2 top-1/2 w-12 h-12 -translate-x-1/2 -translate-y-1/2 rounded-full bg-rose-500/60 blur-md"></span>
                    <span class="relative block w-4 h-4 rounded-full border-2 border-rose-600 bg-white opacity-70 transition-all duration-300"></span>
                </div>

                <!-- 2. TRACHEA (Traxeya / O'pka) -->
                <div id="dot-trachea" class="absolute -translate-x-1/2 -translate-y-1/2" style="left: 38.6%; top: 53.4%;">
                    <span id="ping-trachea" class="hidden absolute left-1/2 top-1/2 w-8 h-8 -translate-x-1/2 -translate-y-1/2 rounded-full bg-sky-500/40 ping-effect"></span>
                    <span id="glow-trachea" class="hidden absolute left-1/2 top-1/2 w-12 h-12 -translate-x-1/2 -translate-y-1/2 rounded-full bg-sky-500/60 blur-md"></span>
                    <span class="relative block w-4 h-4 rounded-full border-2 border-sky-500 bg-white opacity-70 transition-all duration-300"></span>
                </div>

                <!-- 3. ESOPHAGUS (Qizilo'ngach / Oshqozon) -->
                <div id="dot-esophagus" class="absolute -translate-x-1/2 -translate-y-1/2" style="left: 43.3%; top: 86.0%;">
                    <span id="ping-esophagus" class="hidden absolute left-1/2 top-1/2 w-8 h-8 -translate-x-1/2 -translate-y-1/2 rounded-full bg-amber-500/40 ping-effect"></span>
                    <span id="glow-esophagus" class="hidden absolute left-1/2 top-1/2 w-12 h-12 -translate-x-1/2 -translate-y-1/2 rounded-full bg-amber-500/60 blur-md"></span>
                    <span class="relative block w-4 h-4 rounded-full border-2 border-amber-500 bg-white opacity-70 transition-all duration-300"></span>
                </div>

                <!-- ANATOMY LEGEND -->
                <div class="absolute right-3 top-3 flex flex-col gap-2 rounded-xl bg-white/90 p-3 backdrop-blur-md border border-slate-200 shadow-md text-xs">
                    <div class="flex items-center justify-between gap-3 font-bold">
                        <div class="flex items-center gap-2 text-rose-600">
                            <span id="leg-dot-teeth" class="w-2.5 h-2.5 rounded-full bg-rose-600 opacity-40"></span>
                            <span>Tish sensori</span>
                        </div>
                        <span id="leg-txt-teeth" class="mono text-[11px] text-slate-400">jim</span>
                    </div>
                    <div class="flex items-center justify-between gap-3 font-bold">
                        <div class="flex items-center gap-2 text-sky-600">
                            <span id="leg-dot-trachea" class="w-2.5 h-2.5 rounded-full bg-sky-600 opacity-40"></span>
                            <span>O'pka yo'li (Traxeya)</span>
                        </div>
                        <span id="leg-txt-trachea" class="mono text-[11px] text-slate-400">jim</span>
                    </div>
                    <div class="flex items-center justify-between gap-3 font-bold">
                        <div class="flex items-center gap-2 text-amber-600">
                            <span id="leg-dot-esophagus" class="w-2.5 h-2.5 rounded-full bg-amber-600 opacity-40"></span>
                            <span>Oshqozon yo'li</span>
                        </div>
                        <span id="leg-txt-esophagus" class="mono text-[11px] text-slate-400">jim</span>
                    </div>
                </div>
            </div>

            <!-- DIAGNOSIS ALERT BOX (Medical White) -->
            <div id="diag-box" class="rounded-2xl border border-slate-200 bg-white p-4 transition-all duration-300 flex items-start gap-4 shadow-sm">
                <div id="diag-icon-box" class="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center text-xl text-slate-500 shrink-0">
                    <i class="fa-solid fa-stethoscope"></i>
                </div>
                <div>
                    <h3 id="diag-title" class="text-base font-bold text-slate-800">Signal kutilmoqda</h3>
                    <p id="diag-detail" class="text-xs text-slate-500 mt-1">Hozircha datchiklardan signal kelmayapti. Portga ulaning yoki Demo tugmasini bosing.</p>
                </div>
            </div>

            <!-- LIVE SENSOR VALUES READOUT & MANUAL TEST BUTTONS -->
            <div class="grid grid-cols-3 gap-3">
                <button onclick="triggerManualSensor('teeth')" class="rounded-xl border border-slate-200 bg-white hover:bg-rose-50 hover:border-rose-300 p-3 text-center transition cursor-pointer active:scale-95 shadow-sm">
                    <p class="text-[11px] text-slate-500 font-medium">Tish Sensori (Sinov)</p>
                    <p id="val-teeth" class="text-xl font-bold mono text-slate-800 mt-0.5">0</p>
                    <span id="st-teeth" class="text-[10px] uppercase font-bold text-slate-400">jim</span>
                </button>
                <button onclick="triggerManualSensor('trachea')" class="rounded-xl border border-slate-200 bg-white hover:bg-sky-50 hover:border-sky-300 p-3 text-center transition cursor-pointer active:scale-95 shadow-sm">
                    <p class="text-[11px] text-slate-500 font-medium">Traxeya (O'pka)</p>
                    <p id="val-trachea" class="text-xl font-bold mono text-slate-800 mt-0.5">0</p>
                    <span id="st-trachea" class="text-[10px] uppercase font-bold text-slate-400">jim</span>
                </button>
                <button onclick="triggerManualSensor('esophagus')" class="rounded-xl border border-slate-200 bg-white hover:bg-amber-50 hover:border-amber-300 p-3 text-center transition cursor-pointer active:scale-95 shadow-sm">
                    <p class="text-[11px] text-slate-500 font-medium">Qizilo'ngach (Sinov)</p>
                    <p id="val-esophagus" class="text-xl font-bold mono text-slate-800 mt-0.5">0</p>
                    <span id="st-esophagus" class="text-[10px] uppercase font-bold text-slate-400">jim</span>
                </button>
            </div>

        </div>

        <!-- RIGHT COL: CONTROLS & MONITOR (5 cols) -->
        <div class="lg:col-span-5 flex flex-col gap-4">

            <!-- CONNECTION PANEL (SIMPLIFIED: PORT CONNECT & DEMO ONLY) -->
            <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <h3 class="text-sm font-bold text-slate-800 flex items-center gap-2 mb-4">
                    <i class="fa-solid fa-plug text-emerald-600"></i> Apparat Ulanishi
                </h3>

                <div class="flex flex-wrap gap-3">
                    <button id="connect-btn" onclick="toggleConnect()" class="flex-1 py-3 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-xs shadow-md shadow-emerald-600/20 flex items-center justify-center gap-2 transition cursor-pointer">
                        <i class="fa-solid fa-bolt"></i> Portga Ulanish
                    </button>
                    <button id="demo-btn" onclick="toggleDemo()" class="flex-1 py-3 px-4 rounded-xl bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 text-indigo-700 font-extrabold text-xs shadow-xs flex items-center justify-center gap-2 transition cursor-pointer">
                        <i class="fa-solid fa-circle-play text-indigo-600"></i> Demo Rejim
                    </button>
                </div>
            </div>

            <!-- SAMPLE INTUBATION VIDEO CARD -->
            <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <div class="flex items-center justify-between mb-2">
                    <h4 class="text-xs font-bold text-slate-700 flex items-center gap-2">
                        <i class="fa-solid fa-film text-purple-600"></i> To'g'ri Intubatsiya Namuna Videosi
                    </h4>
                    <button onclick="toggleVideo()" class="text-[11px] text-slate-400 hover:text-slate-700 transition cursor-pointer">
                        <span id="vid-btn-txt">Yashirish</span>
                    </button>
                </div>
                <div id="video-container" class="rounded-xl overflow-hidden bg-black border border-slate-200">
                    <video id="sample-video" controls class="w-full h-auto" style="aspect-ratio: 16/9;" preload="metadata">
                        <source src="/intubation/assets/intubation_sample.mp4" type="video/mp4">
                    </video>
                </div>
            </div>

            <!-- SERIAL TERMINAL & LOGS -->
            <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm flex-1 flex flex-col">
                <div class="flex items-center justify-between mb-2">
                    <h4 class="text-xs font-bold text-slate-700 flex items-center gap-2">
                        <i class="fa-solid fa-terminal text-slate-600"></i> Serial Ma'lumotlar Logi
                    </h4>
                    <button onclick="clearLogs()" class="text-[11px] text-slate-400 hover:text-rose-600 transition flex items-center gap-1 cursor-pointer">
                        <i class="fa-solid fa-trash"></i> Tozalash
                    </button>
                </div>
                <div id="log-box" class="h-44 overflow-y-auto bg-slate-900 rounded-xl p-3 mono text-[11px] text-slate-300 space-y-1 border border-slate-800">
                    <p class="text-slate-500">// Serial ma'lumotlar oqimi shu yerda ko'rinadi...</p>
                </div>
            </div>

        </div>

    </main>

    <!-- CONGRATULATORY SUCCESS MODAL FOR NURSE -->
    <div id="success-modal" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-md hidden p-4">
        <div class="bg-white border-2 border-emerald-400 rounded-3xl p-6 md:p-8 max-w-md w-full shadow-2xl text-center relative overflow-hidden animate-pop">
            <div class="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600 text-4xl mx-auto mb-4 shadow-lg shadow-emerald-500/20">
                <i class="fa-solid fa-trophy"></i>
            </div>
            
            <span class="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 font-extrabold text-xs uppercase tracking-wider inline-block mb-2">
                👏 BARAKALLA! MASHQ MUVAFFAQIYATLI
            </span>
            
            <h2 class="text-2xl font-black text-slate-900 mb-2">
                Intubatsiya To'g'ri Bajarildi!
            </h2>
            
            <p class="text-xs md:text-sm text-slate-600 leading-relaxed mb-6">
                Hamshira intubatsiya trubkasini traxeyaga (o'pka yo'liga) ziyon yetkazmasdan va tishlarga tegmasdan juda to'g'ri joylashtirdi!
            </p>
            
            <div class="flex gap-3 justify-center">
                <button onclick="closeSuccessModal()" class="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-sm shadow-lg shadow-emerald-600/30 transition cursor-pointer">
                    <i class="fa-solid fa-circle-check mr-1"></i> Rahmat, Davom Etish
                </button>
            </div>
        </div>
    </div>

    <!-- AUDIO ELEMENTS -->
    <audio id="audio-esophagus" loop src="/intubation/assets/esophagus.mp3" preload="auto"></audio>
    <audio id="audio-failed" loop src="/intubation/assets/failed.mp3" preload="auto"></audio>
    <audio id="audio-success" src="/intubation/assets/success.mp3" preload="auto"></audio>

    <script>
        // SENSOR ALIASES & PARSING LOGIC
        const ALIASES = {
            t: "teeth", teeth: "teeth", tish: "teeth", tooth: "teeth",
            e: "esophagus", eso: "esophagus", esophagus: "esophagus", oshqazon: "esophagus", qizilongach: "esophagus", stomach: "esophagus",
            l: "trachea", lung: "trachea", opka: "trachea", trachea: "trachea", tracheal: "trachea", airway: "trachea", tomoq: "trachea"
        };

        let port = null;
        let reader = null;
        let isConnected = false;
        let isDemo = false;
        let demoInterval = null;
        let soundEnabled = true;

        let sensorData = { teeth: 0, esophagus: 0, trachea: 0 };
        let lastSeen = { teeth: 0, esophagus: 0, trachea: 0 };
        let sustainedOkTimer = null;
        let celebrateTimer = null;

        // Default constant settings
        const DEFAULT_BAUD = 9600;
        const DEFAULT_THRESHOLD = 300;

        // PARSE SERIAL LINE
        function parseLine(line) {
            const text = line.trim();
            if (!text) return null;

            if (text.startsWith("{")) {
                try {
                    const obj = JSON.parse(text);
                    const out = {};
                    for (let [k, v] of Object.entries(obj)) {
                        let key = ALIASES[k.toLowerCase().replace(/[^a-z]/g, "")];
                        if (key) out[key] = typeof v === "boolean" ? (v ? 1 : 0) : (Number(v) || 0);
                    }
                    return Object.keys(out).length ? out : null;
                } catch (e) { return null; }
            }

            const pairs = [...text.matchAll(/([a-zA-Z_\\u0400-\\u04FF']+)\\s*[:=]\\s*(-?\\d+(?:\\.\\d+)?)/g)];
            if (pairs.length) {
                const out = {};
                for (let m of pairs) {
                    let key = ALIASES[(m[1] || "").toLowerCase().replace(/[^a-z]/g, "")];
                    if (key) out[key] = Number(m[2]);
                }
                return Object.keys(out).length ? out : null;
            }

            const nums = text.split(/[,;\\s]+/).map(Number);
            if (nums.length >= 3 && nums.slice(0, 3).every(n => Number.isFinite(n))) {
                return { teeth: nums[0], esophagus: nums[1], trachea: nums[2] };
            }

            // TEXT PARSER fallback
            const t = text.toLowerCase();
            if (t.includes("tish") || t.includes("button")) return { teeth: 1 };
            if (t.includes("oshqazon") || t.includes("qizil")) return { esophagus: 1 };
            if (t.includes("tomoq") || t.includes("traxe") || t.includes("o'pka") || t.includes("opka")) return { trachea: 1 };

            return null;
        }

        function isSensorActive(val) {
            if (val <= 1) return val >= 1;
            return val >= DEFAULT_THRESHOLD;
        }

        // UPDATE UI & DIAGNOSIS
        function updateState(partial) {
            const now = Date.now();
            for (let k in partial) {
                sensorData[k] = partial[k];
                if (partial[k] > 0) lastSeen[k] = now;
            }

            const active = {
                teeth: isSensorActive(sensorData.teeth),
                esophagus: isSensorActive(sensorData.esophagus),
                trachea: isSensorActive(sensorData.trachea)
            };

            // Update DOM text readings
            ['teeth', 'trachea', 'esophagus'].forEach(k => {
                document.getElementById(`val-${k}`).innerText = sensorData[k];
                const act = active[k];
                const st = document.getElementById(`st-${k}`);
                const legTxt = document.getElementById(`leg-txt-${k}`);
                const legDot = document.getElementById(`leg-dot-${k}`);
                
                st.innerText = act ? "FAOL" : "jim";
                st.className = `text-[10px] uppercase font-bold ${act ? (k==='trachea'?'text-sky-600':'text-rose-600') : 'text-slate-400'}`;
                
                legTxt.innerText = act ? "FAOL" : "jim";
                legTxt.className = `mono text-[11px] ${act ? 'text-slate-900 font-bold' : 'text-slate-400'}`;
                legDot.style.opacity = act ? '1' : '0.4';

                // Anatomy Overlay dots
                const ping = document.getElementById(`ping-${k}`);
                const glow = document.getElementById(`glow-${k}`);
                if (act) {
                    ping.classList.remove('hidden');
                    glow.classList.remove('hidden');
                } else {
                    ping.classList.add('hidden');
                    glow.classList.add('hidden');
                }
            });

            // DIAGNOSE
            let dx = { level: "idle", title: "Signal kutilmoqda", detail: "Hozircha datchiklardan signal kelmayapti." };

            if (active.esophagus) {
                dx = {
                    level: "danger",
                    title: "Trubka qizilo'ngachga (oshqazon yo'liga) kirdi!",
                    detail: "Oshqazon yo'li sensori faollashdi. Bu noto'g'ri joylashuv — trubkani darhol chiqarib, qayta urinish kerak."
                };
            } else if (active.trachea) {
                dx = {
                    level: active.teeth ? "warn" : "ok",
                    title: active.teeth ? "Traxeyaga kirdi, lekin tishga tegdi!" : "Trubka traxeyaga (o'pka yo'liga) to'g'ri kirdi!",
                    detail: active.teeth 
                        ? "O'pka yo'li sensori faol — joylashuv to'g'ri, ammo tish sensori ham ishga tushdi (tish/lab jarohati xavfi)."
                        : "O'pka yo'li sensori faollashdi va oshqazon yo'li sensori jim — joylashuv to'g'ri deb qayd etildi."
                };
            } else if (active.teeth) {
                dx = {
                    level: "warn",
                    title: "Tishga tegish qayd etildi!",
                    detail: "Laringoskop yoki trubka tishga tayanmoqda. Tayanch nuqtasini o'zgartiring."
                };
            }

            renderDiagnosis(dx);
            handleAudio(dx.level);

            // SUSTAINED OK CONFETTI & TABRIKLASH MODAL TRIGGER (1.5s)
            if (dx.level === "ok") {
                if (!sustainedOkTimer) {
                    sustainedOkTimer = setTimeout(() => {
                        triggerConfetti();
                        showSuccessModal();
                    }, 1500);
                }
            } else {
                if (sustainedOkTimer) { clearTimeout(sustainedOkTimer); sustainedOkTimer = null; }
            }
        }

        // AUTO RESET SILENT SENSORS (after 500ms)
        setInterval(() => {
            const now = Date.now();
            const off = {};
            ['teeth', 'esophagus', 'trachea'].forEach(k => {
                if (lastSeen[k] && now - lastSeen[k] > 500) {
                    off[k] = 0;
                    lastSeen[k] = 0;
                }
            });
            if (Object.keys(off).length) updateState(off);
        }, 250);

        function renderDiagnosis(dx) {
            const box = document.getElementById('diag-box');
            const iconBox = document.getElementById('diag-icon-box');
            const title = document.getElementById('diag-title');
            const detail = document.getElementById('diag-detail');

            title.innerText = dx.title;
            detail.innerText = dx.detail;

            if (dx.level === "danger") {
                box.className = "rounded-2xl border-2 border-rose-300 bg-rose-50 p-4 flex items-start gap-4 shadow-sm";
                iconBox.className = "w-12 h-12 rounded-xl bg-rose-100 text-rose-600 flex items-center justify-center text-xl shrink-0";
                iconBox.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';
            } else if (dx.level === "warn") {
                box.className = "rounded-2xl border-2 border-amber-300 bg-amber-50 p-4 flex items-start gap-4 shadow-sm";
                iconBox.className = "w-12 h-12 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center text-xl shrink-0";
                iconBox.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i>';
            } else if (dx.level === "ok") {
                box.className = "rounded-2xl border-2 border-emerald-400 bg-emerald-50 p-4 flex items-start gap-4 shadow-sm";
                iconBox.className = "w-12 h-12 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center text-xl shrink-0";
                iconBox.innerHTML = '<i class="fa-solid fa-circle-check"></i>';
            } else {
                box.className = "rounded-2xl border border-slate-200 bg-white p-4 flex items-start gap-4 shadow-sm";
                iconBox.className = "w-12 h-12 rounded-xl bg-slate-100 text-slate-500 flex items-center justify-center text-xl shrink-0";
                iconBox.innerHTML = '<i class="fa-solid fa-stethoscope"></i>';
            }
        }

        // AUDIO CONTROLS
        function stopAllAudio() {
            ['audio-esophagus', 'audio-failed', 'audio-success'].forEach(id => {
                const a = document.getElementById(id);
                a.pause();
                a.currentTime = 0;
            });
        }

        let currentAudioLevel = "idle";
        function handleAudio(level) {
            if (!soundEnabled) { stopAllAudio(); return; }
            if (currentAudioLevel === level) return;
            currentAudioLevel = level;

            stopAllAudio();
            if (level === "danger") {
                document.getElementById('audio-esophagus').play().catch(()=>{});
            } else if (level === "warn") {
                document.getElementById('audio-failed').play().catch(()=>{});
            } else if (level === "ok") {
                document.getElementById('audio-success').play().catch(()=>{});
            }
        }

        function toggleSound() {
            soundEnabled = !soundEnabled;
            const icon = document.getElementById('sound-icon');
            const txt = document.getElementById('sound-text');
            const btn = document.getElementById('sound-btn');
            
            if (soundEnabled) {
                icon.className = "fa-solid fa-volume-high";
                txt.innerText = "Ovoz Yoniq";
                btn.className = "px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 border border-slate-300 text-xs font-bold flex items-center gap-2 text-emerald-700 transition cursor-pointer";
            } else {
                icon.className = "fa-solid fa-volume-xmark";
                txt.innerText = "Ovoz O'chiq";
                btn.className = "px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 border border-slate-300 text-xs font-bold flex items-center gap-2 text-slate-400 transition cursor-pointer";
                stopAllAudio();
            }
        }

        // CONFETTI EFFECT
        function triggerConfetti() {
            const holder = document.getElementById('confetti-holder');
            const container = document.getElementById('confetti-pieces');
            container.innerHTML = '';
            
            const colors = ['#22c55e', '#38bdf8', '#facc15', '#f472b6', '#a78bfa', '#fb923c'];
            for (let i = 0; i < 140; i++) {
                const p = document.createElement('span');
                p.className = 'absolute top-0 block rounded-sm';
                p.style.left = `${Math.random() * 100}%`;
                p.style.width = `${6 + Math.random() * 8}px`;
                p.style.height = `${10 + Math.random() * 14}px`;
                p.style.backgroundColor = colors[i % colors.length];
                p.style.setProperty('--drift', `${(Math.random() - 0.5) * 160}px`);
                p.style.setProperty('--rot', `${Math.random() * 360}deg`);
                p.style.animation = `mk-confetti ${4 + Math.random() * 2}s cubic-bezier(.2,.6,.4,1) ${Math.random() * 1}s forwards`;
                container.appendChild(p);
            }
            
            holder.classList.remove('hidden');
            if (celebrateTimer) clearTimeout(celebrateTimer);
            celebrateTimer = setTimeout(() => {
                holder.classList.add('hidden');
            }, 6500);
        }

        function showSuccessModal() {
            const modal = document.getElementById('success-modal');
            if (modal) modal.classList.remove('hidden');
        }

        function closeSuccessModal() {
            const modal = document.getElementById('success-modal');
            if (modal) modal.classList.add('hidden');
        }

        // SENSOR TEST MANUAL BUTTON HANDLER
        function triggerManualSensor(sensorKey) {
            logSerial(`[SINOV] ${sensorKey} sensori bosildi`);
            const updateObj = { [sensorKey]: 1 };
            updateState(updateObj);
        }

        // WEB SERIAL CONNECT
        async function toggleConnect() {
            if (isConnected) {
                disconnectSerial();
                return;
            }
            if (!("serial" in navigator)) {
                alert("Bu brauzer Web Serial API'ni qo'llab-quvvatlamaydi. Iltimos Google Chrome yoki Microsoft Edge ishlating.");
                logSerial("[XATO] Brauzer Web Serial API-ni qo'llab-quvvatlamaydi.");
                return;
            }

            try {
                logSerial(`[ULANISH] COM Port so'ralmoqda (Baud: ${DEFAULT_BAUD})...`);
                port = await navigator.serial.requestPort();
                await port.open({ baudRate: DEFAULT_BAUD });
                
                isConnected = true;
                updateStatus("connected", "Ulangan");
                logSerial("✅ Arduino COM porti muvaffaqiyatli ulandi!");

                const decoder = new TextDecoderStream();
                port.readable.pipeTo(decoder.writable);
                reader = decoder.readable.getReader();

                let buffer = "";
                while (isConnected) {
                    const { value, done } = await reader.read();
                    if (done) break;
                    buffer += value;
                    let parts = buffer.split(/\\r?\\n/);
                    buffer = parts.pop();
                    for (let line of parts) {
                        if (line.trim()) {
                            logSerial(line);
                            const parsed = parseLine(line);
                            if (parsed) updateState(parsed);
                        }
                    }
                }
            } catch (e) {
                console.error("Serial error:", e);
                logSerial(`[XATO] Port ulanmadi: ${e.message || e}`);
                disconnectSerial();
            }
        }

        function disconnectSerial() {
            isConnected = false;
            if (reader) { try { reader.cancel(); } catch(e){} reader = null; }
            if (port) { try { port.close(); } catch(e){} port = null; }
            updateStatus("disconnected", "Ulanmagan");
            logSerial("[UZILDIS] Port ulanishi uzildi.");
        }

        // DEMO SCRIPT
        function toggleDemo() {
            if (isDemo) {
                clearInterval(demoInterval);
                demoInterval = null;
                isDemo = false;
                updateStatus("disconnected", "Ulanmagan");
                document.getElementById('demo-btn').innerHTML = '<i class="fa-solid fa-circle-play text-indigo-600"></i> Demo Rejim';
                updateState({ teeth: 0, esophagus: 0, trachea: 0 });
                logSerial("[DEMO] Demo rejim to'xtatildi.");
                return;
            }

            isDemo = true;
            updateStatus("demo", "Demo Rejim");
            document.getElementById('demo-btn').innerHTML = '<i class="fa-solid fa-circle-stop text-rose-600"></i> To&apos;xtatish';
            logSerial("[DEMO] Demo rejim ishga tushdi! (Ssenariy o'ynamoqda...)");

            const demoSteps = [
                { teeth: 0, esophagus: 0, trachea: 0 },
                { teeth: 1, esophagus: 0, trachea: 0 },
                { teeth: 0, esophagus: 1, trachea: 0 },
                { teeth: 0, esophagus: 0, trachea: 0 },
                { teeth: 0, esophagus: 0, trachea: 1 },
                { teeth: 0, esophagus: 0, trachea: 1 }
            ];

            let step = 0;
            demoInterval = setInterval(() => {
                const s = demoSteps[step % demoSteps.length];
                const raw = `T:${s.teeth} E:${s.esophagus} L:${s.trachea}`;
                logSerial(`[DEMO] ${raw}`);
                updateState(s);
                step++;
            }, 1800);
        }

        function updateStatus(type, label) {
            const badge = document.getElementById('connection-badge');
            const txt = document.getElementById('status-text');
            const btn = document.getElementById('connect-btn');
            
            txt.innerText = label;
            if (type === "connected") {
                badge.className = "px-3.5 py-1.5 rounded-xl bg-emerald-100 border border-emerald-300 text-emerald-800 text-xs font-bold flex items-center gap-2";
                badge.querySelector('span').className = "w-2.5 h-2.5 rounded-full bg-emerald-600 animate-ping";
                btn.innerHTML = '<i class="fa-solid fa-plug-circle-xmark"></i> Uzish';
                btn.className = "flex-1 py-3 px-4 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-extrabold text-xs shadow-md flex items-center justify-center gap-2 transition cursor-pointer";
            } else if (type === "demo") {
                badge.className = "px-3.5 py-1.5 rounded-xl bg-indigo-100 border border-indigo-300 text-indigo-800 text-xs font-bold flex items-center gap-2";
                badge.querySelector('span').className = "w-2.5 h-2.5 rounded-full bg-indigo-600 animate-pulse";
            } else {
                badge.className = "px-3.5 py-1.5 rounded-xl bg-slate-100 border border-slate-300 text-slate-600 text-xs font-bold flex items-center gap-2";
                badge.querySelector('span').className = "w-2.5 h-2.5 rounded-full bg-slate-400";
                btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Portga Ulanish';
                btn.className = "flex-1 py-3 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-xs shadow-md shadow-emerald-600/20 flex items-center justify-center gap-2 transition cursor-pointer";
            }
        }

        function logSerial(msg) {
            const box = document.getElementById('log-box');
            if (!box) return;
            const time = new Date().toLocaleTimeString();
            const p = document.createElement('p');
            p.innerText = `[${time}] ${msg}`;
            box.appendChild(p);
            box.scrollTop = box.scrollHeight;
        }

        function clearLogs() {
            document.getElementById('log-box').innerHTML = '<p class="text-slate-500">// Log tozalandi</p>';
        }

        function toggleVideo() {
            const container = document.getElementById('video-container');
            const txt = document.getElementById('vid-btn-txt');
            if (container.classList.contains('hidden')) {
                container.classList.remove('hidden');
                txt.innerText = "Yashirish";
            } else {
                container.classList.add('hidden');
                txt.innerText = "Ko'rsatish";
            }
        }
    </script>
</body>
</html>
"""
