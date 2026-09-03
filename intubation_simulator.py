# -*- coding: utf-8 -*-
"""
MedLife Intubation Manikin Simulator - Intubatsiya Simulyatori
Web Serial API + SVG Anatomiya Overlay + Realtime Tashxis va Ovoz
"""

INTUBATION_HTML = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>MedLife — Intubatsiya Simulyatori</title>
    <meta name="theme-color" content="#0f172a">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@400;500;600;700;800;900&display=swap');
        * { -webkit-touch-callout: none; touch-action: manipulation; }
        body { font-family: 'Inter', sans-serif; background-color: #090d16; color: #f1f5f9; }
        .mono { font-family: 'Share Tech Mono', monospace; }
        
        @keyframes mk-ping {
            0% { transform: translate(-50%, -50%) scale(0.6); opacity: 0.8; }
            100% { transform: translate(-50%, -50%) scale(3.2); opacity: 0; }
        }
        .ping-effect { animation: mk-ping 1.2s cubic-bezier(0, 0, 0.2, 1) infinite; }
        
        @keyframes mk-confetti {
            0% { transform: translate3d(0, -10%, 0) rotate(var(--rot)); opacity: 1; }
            100% { transform: translate3d(var(--drift), 110vh, 0) rotate(calc(var(--rot) + 1080deg)); opacity: 0.9; }
        }
        @keyframes mk-burst {
            0% { transform: translate(-50%,-50%) scale(0.2); opacity: 0.95; }
            60% { opacity: 0.4; }
            100% { transform: translate(-50%,-50%) scale(4); opacity: 0; }
        }
    </style>
</head>
<body class="min-h-screen flex flex-col justify-between p-3 md:p-6">

    <!-- HEADER -->
    <header class="flex flex-wrap items-center justify-between gap-4 bg-slate-900/90 border border-slate-800 rounded-2xl px-5 py-3.5 shadow-2xl">
        <div class="flex items-center gap-3">
            <a href="/hub" class="w-10 h-10 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 flex items-center justify-center text-slate-300 transition">
                <i class="fa-solid fa-house"></i>
            </a>
            <div>
                <h1 class="text-lg md:text-xl font-black text-white flex items-center gap-2">
                    INTUBATSIYA MANIKENI <span class="text-xs bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 px-2 py-0.5 rounded-full font-mono">Web Serial API</span>
                </h1>
                <p class="text-xs text-slate-400">Traxeya trubkasi va sensorlar monitoringi</p>
            </div>
        </div>

        <div class="flex items-center gap-3">
            <!-- SOUND TOGGLE -->
            <button id="sound-btn" onclick="toggleSound()" class="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-bold flex items-center gap-2 text-emerald-400 transition">
                <i id="sound-icon" class="fa-solid fa-volume-high"></i>
                <span id="sound-text" class="hidden sm:inline">Ovoz Yoniq</span>
            </button>
            
            <!-- STATUS BADGE -->
            <div id="connection-badge" class="px-3 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-slate-400 text-xs font-semibold flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full bg-slate-500"></span>
                <span id="status-text">Ulanmagan</span>
            </div>
        </div>
    </header>

    <!-- MAIN CONTENT -->
    <main class="my-4 grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-7xl mx-auto w-full">

        <!-- LEFT COL: ANATOMY & DIAGNOSIS (7 cols) -->
        <div class="lg:col-span-7 flex flex-col gap-4">
            
            <!-- ANATOMY CANVAS OVERLAY -->
            <div class="relative w-full overflow-hidden rounded-2xl border-2 border-slate-800 bg-slate-950/80 shadow-2xl" style="aspect-ratio: 1536 / 1024;">
                <img src="/intubation/assets/tibbiy_sensor_anatomy.svg" alt="Maniken Anatomiyasi" class="absolute inset-0 w-full h-full object-contain pointer-events-none">
                
                <!-- CONFETTI CONTAINER -->
                <div id="confetti-holder" class="pointer-events-none absolute inset-0 z-30 overflow-hidden hidden">
                    <div id="confetti-pieces"></div>
                    <span class="absolute left-1/2 top-1/3 size-32 -translate-x-1/2 -translate-y-1/2 rounded-full blur-2xl bg-emerald-500 opacity-0" style="animation: mk-burst 3.5s ease-out forwards;"></span>
                </div>

                <!-- OVERLAY SENSOR INDICATORS -->
                <!-- 1. TEETH (Tish) -->
                <div id="dot-teeth" class="absolute -translate-x-1/2 -translate-y-1/2" style="left: 33.9%; top: 29.2%;">
                    <span id="ping-teeth" class="hidden absolute left-1/2 top-1/2 w-8 h-8 -translate-x-1/2 -translate-y-1/2 rounded-full bg-rose-500/40 ping-effect"></span>
                    <span id="glow-teeth" class="hidden absolute left-1/2 top-1/2 w-12 h-12 -translate-x-1/2 -translate-y-1/2 rounded-full bg-rose-500/60 blur-md"></span>
                    <span class="relative block w-4 h-4 rounded-full border-2 border-rose-500 bg-slate-900 opacity-60 transition-all duration-300"></span>
                </div>

                <!-- 2. TRACHEA (Traxeya / O'pka) -->
                <div id="dot-trachea" class="absolute -translate-x-1/2 -translate-y-1/2" style="left: 38.6%; top: 53.4%;">
                    <span id="ping-trachea" class="hidden absolute left-1/2 top-1/2 w-8 h-8 -translate-x-1/2 -translate-y-1/2 rounded-full bg-sky-500/40 ping-effect"></span>
                    <span id="glow-trachea" class="hidden absolute left-1/2 top-1/2 w-12 h-12 -translate-x-1/2 -translate-y-1/2 rounded-full bg-sky-500/60 blur-md"></span>
                    <span class="relative block w-4 h-4 rounded-full border-2 border-sky-400 bg-slate-900 opacity-60 transition-all duration-300"></span>
                </div>

                <!-- 3. ESOPHAGUS (Qizilo'ngach / Oshqozon) -->
                <div id="dot-esophagus" class="absolute -translate-x-1/2 -translate-y-1/2" style="left: 43.3%; top: 86.0%;">
                    <span id="ping-esophagus" class="hidden absolute left-1/2 top-1/2 w-8 h-8 -translate-x-1/2 -translate-y-1/2 rounded-full bg-amber-500/40 ping-effect"></span>
                    <span id="glow-esophagus" class="hidden absolute left-1/2 top-1/2 w-12 h-12 -translate-x-1/2 -translate-y-1/2 rounded-full bg-amber-500/60 blur-md"></span>
                    <span class="relative block w-4 h-4 rounded-full border-2 border-amber-400 bg-slate-900 opacity-60 transition-all duration-300"></span>
                </div>

                <!-- ANATOMY LEGEND -->
                <div class="absolute right-3 top-3 flex flex-col gap-2 rounded-xl bg-slate-900/85 p-3 backdrop-blur-md border border-slate-800 shadow-lg text-xs">
                    <div class="flex items-center justify-between gap-3 font-semibold">
                        <div class="flex items-center gap-2 text-rose-400">
                            <span id="leg-dot-teeth" class="w-2.5 h-2.5 rounded-full bg-rose-500 opacity-40"></span>
                            <span>Tish sensori</span>
                        </div>
                        <span id="leg-txt-teeth" class="mono text-[11px] text-slate-500">jim</span>
                    </div>
                    <div class="flex items-center justify-between gap-3 font-semibold">
                        <div class="flex items-center gap-2 text-sky-400">
                            <span id="leg-dot-trachea" class="w-2.5 h-2.5 rounded-full bg-sky-400 opacity-40"></span>
                            <span>O'pka yo'li (Traxeya)</span>
                        </div>
                        <span id="leg-txt-trachea" class="mono text-[11px] text-slate-500">jim</span>
                    </div>
                    <div class="flex items-center justify-between gap-3 font-semibold">
                        <div class="flex items-center gap-2 text-amber-400">
                            <span id="leg-dot-esophagus" class="w-2.5 h-2.5 rounded-full bg-amber-400 opacity-40"></span>
                            <span>Oshqozon yo'li</span>
                        </div>
                        <span id="leg-txt-esophagus" class="mono text-[11px] text-slate-500">jim</span>
                    </div>
                </div>
            </div>

            <!-- DIAGNOSIS ALERT BOX -->
            <div id="diag-box" class="rounded-2xl border border-slate-800 bg-slate-900/80 p-4 transition-all duration-300 flex items-start gap-4 shadow-xl">
                <div id="diag-icon-box" class="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center text-xl text-slate-400 shrink-0">
                    <i class="fa-solid fa-stethoscope"></i>
                </div>
                <div>
                    <h3 id="diag-title" class="text-base font-bold text-slate-200">Signal kutilmoqda</h3>
                    <p id="diag-detail" class="text-xs text-slate-400 mt-1">Hozircha sensorlardan ma'lumot kelmayapti. Arduino portini ulang yoki Demo rejimini bosing.</p>
                </div>
            </div>

            <!-- LIVE SENSOR VALUES READOUT -->
            <div class="grid grid-cols-3 gap-3">
                <div id="card-teeth" class="rounded-xl border border-slate-800 bg-slate-900/60 p-3 text-center transition">
                    <p class="text-[11px] text-slate-400 font-medium">Tish Sensori</p>
                    <p id="val-teeth" class="text-xl font-bold mono text-slate-200 mt-0.5">0</p>
                    <span id="st-teeth" class="text-[10px] uppercase font-bold text-slate-500">jim</span>
                </div>
                <div id="card-trachea" class="rounded-xl border border-slate-800 bg-slate-900/60 p-3 text-center transition">
                    <p class="text-[11px] text-slate-400 font-medium">Traxeya (O'pka)</p>
                    <p id="val-trachea" class="text-xl font-bold mono text-slate-200 mt-0.5">0</p>
                    <span id="st-trachea" class="text-[10px] uppercase font-bold text-slate-500">jim</span>
                </div>
                <div id="card-esophagus" class="rounded-xl border border-slate-800 bg-slate-900/60 p-3 text-center transition">
                    <p class="text-[11px] text-slate-400 font-medium">Qizilo'ngach</p>
                    <p id="val-esophagus" class="text-xl font-bold mono text-slate-200 mt-0.5">0</p>
                    <span id="st-esophagus" class="text-[10px] uppercase font-bold text-slate-500">jim</span>
                </div>
            </div>

        </div>

        <!-- RIGHT COL: CONTROLS & MONITOR (5 cols) -->
        <div class="lg:col-span-5 flex flex-col gap-4">

            <!-- CONNECTION PANEL -->
            <div class="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl">
                <h3 class="text-sm font-bold text-slate-200 flex items-center gap-2 mb-4">
                    <i class="fa-solid fa-plug text-cyan-400"></i> Apparat Ulanishi (Arduino)
                </h3>
                
                <div class="grid grid-cols-2 gap-3 mb-4">
                    <div>
                        <label class="block text-xs text-slate-400 mb-1 font-medium">Baud Rate</label>
                        <select id="baud-select" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500">
                            <option value="9600" selected>9600</option>
                            <option value="19200">19200</option>
                            <option value="38400">38400</option>
                            <option value="57600">57600</option>
                            <option value="115200">115200</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs text-slate-400 mb-1 font-medium">Analog Chegara</label>
                        <input id="thresh-input" type="number" value="300" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-cyan-500">
                    </div>
                </div>

                <div class="flex flex-wrap gap-2">
                    <button id="connect-btn" onclick="toggleConnect()" class="flex-1 px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs shadow-lg shadow-cyan-900/30 flex items-center justify-center gap-2 transition cursor-pointer">
                        <i class="fa-solid fa-bolt"></i> Portga Ulanish
                    </button>
                    <button id="demo-btn" onclick="toggleDemo()" class="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-bold text-xs flex items-center gap-2 transition cursor-pointer">
                        <i class="fa-solid fa-circle-play text-amber-400"></i> Demo
                    </button>
                </div>
            </div>

            <!-- SAMPLE INTUBATION VIDEO CARD -->
            <div class="rounded-2xl border border-slate-800 bg-slate-900/90 p-4 shadow-xl">
                <div class="flex items-center justify-between mb-2">
                    <h4 class="text-xs font-bold text-slate-300 flex items-center gap-2">
                        <i class="fa-solid fa-film text-purple-400"></i> To'g'ri Intubatsiya Namuna Videosi
                    </h4>
                    <button onclick="toggleVideo()" class="text-[11px] text-slate-400 hover:text-white transition">
                        <span id="vid-btn-txt">Yashirish</span>
                    </button>
                </div>
                <div id="video-container" class="rounded-xl overflow-hidden bg-black border border-slate-800">
                    <video id="sample-video" controls class="w-full h-auto" style="aspect-ratio: 16/9;" preload="metadata">
                        <source src="/intubation/assets/intubation_sample.mp4" type="video/mp4">
                    </video>
                </div>
            </div>

            <!-- SERIAL TERMINAL & LOGS -->
            <div class="rounded-2xl border border-slate-800 bg-slate-900/90 p-4 shadow-xl flex-1 flex flex-col">
                <div class="flex items-center justify-between mb-2">
                    <h4 class="text-xs font-bold text-slate-300 flex items-center gap-2">
                        <i class="fa-solid fa-terminal text-emerald-400"></i> Serial Ma'lumotlar Logi
                    </h4>
                    <button onclick="clearLogs()" class="text-[11px] text-slate-400 hover:text-rose-400 transition flex items-center gap-1">
                        <i class="fa-solid fa-trash"></i> Tozalash
                    </button>
                </div>
                <div id="log-box" class="h-44 overflow-y-auto bg-slate-950 rounded-xl p-3 mono text-[11px] text-slate-400 space-y-1 border border-slate-800">
                    <p class="text-slate-600">// Serial ma'lumotlar oqimi shu yerda ko'rinadi...</p>
                </div>
            </div>

        </div>

    </main>

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

            const pairs = [...text.matchAll(/([a-zA-Z_\u0400-\u04FF']+)\s*[:=]\s*(-?\d+(?:\.\d+)?)/g)];
            if (pairs.length) {
                const out = {};
                for (let m of pairs) {
                    let key = ALIASES[(m[1] || "").toLowerCase().replace(/[^a-z]/g, "")];
                    if (key) out[key] = Number(m[2]);
                }
                return Object.keys(out).length ? out : null;
            }

            const nums = text.split(/[,;\s]+/).map(Number);
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

        function getThreshold() {
            return Number(document.getElementById('thresh-input').value) || 300;
        }

        function isSensorActive(val) {
            const thresh = getThreshold();
            if (val <= 1) return val >= 1;
            return val >= thresh;
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
                st.className = `text-[10px] uppercase font-bold ${act ? (k==='trachea'?'text-sky-400':'text-rose-400') : 'text-slate-500'}`;
                
                legTxt.innerText = act ? "FAOL" : "jim";
                legTxt.className = `mono text-[11px] ${act ? 'text-white font-bold' : 'text-slate-500'}`;
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
            let dx = { level: "idle", title: "Signal kutilmoqda", detail: "Hozircha hech bir sensor faol emas." };

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

            // SUSTAINED OK CONFETTI TRIGGER (2s)
            if (dx.level === "ok") {
                if (!sustainedOkTimer) {
                    sustainedOkTimer = setTimeout(() => triggerConfetti(), 2000);
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
                box.className = "rounded-2xl border-2 border-rose-500/60 bg-rose-950/40 p-4 flex items-start gap-4 shadow-xl shadow-rose-950/50";
                iconBox.className = "w-12 h-12 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center text-xl shrink-0";
                iconBox.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';
            } else if (dx.level === "warn") {
                box.className = "rounded-2xl border-2 border-amber-500/60 bg-amber-950/40 p-4 flex items-start gap-4 shadow-xl shadow-amber-950/50";
                iconBox.className = "w-12 h-12 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center text-xl shrink-0";
                iconBox.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i>';
            } else if (dx.level === "ok") {
                box.className = "rounded-2xl border-2 border-emerald-500/60 bg-emerald-950/40 p-4 flex items-start gap-4 shadow-xl shadow-emerald-950/50";
                iconBox.className = "w-12 h-12 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xl shrink-0";
                iconBox.innerHTML = '<i class="fa-solid fa-circle-check"></i>';
            } else {
                box.className = "rounded-2xl border border-slate-800 bg-slate-900/80 p-4 flex items-start gap-4 shadow-xl";
                iconBox.className = "w-12 h-12 rounded-xl bg-slate-800 text-slate-400 flex items-center justify-center text-xl shrink-0";
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
                btn.className = "px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-bold flex items-center gap-2 text-emerald-400 transition";
            } else {
                icon.className = "fa-solid fa-volume-xmark";
                txt.innerText = "Ovoz O'chiq";
                btn.className = "px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-bold flex items-center gap-2 text-slate-500 transition";
                stopAllAudio();
            }
        }

        // CONFETTI EFFECT
        function triggerConfetti() {
            const holder = document.getElementById('confetti-holder');
            const container = document.getElementById('confetti-pieces');
            container.innerHTML = '';
            
            const colors = ['#22c55e', '#38bdf8', '#facc15', '#f472b6', '#a78bfa', '#fb923c'];
            for (let i = 0; i < 120; i++) {
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

        // WEB SERIAL CONNECT
        async function toggleConnect() {
            if (isConnected) {
                disconnectSerial();
                return;
            }
            if (!("serial" in navigator)) {
                alert("Bu brauzer Web Serial API'ni qo'llab-quvvatlamaydi. Iltimos Google Chrome yoki Microsoft Edge ishlating.");
                return;
            }

            try {
                const baud = Number(document.getElementById('baud-select').value) || 9600;
                port = await navigator.serial.requestPort();
                await port.open({ baudRate: baud });
                
                isConnected = true;
                updateStatus("connected", "Ulangan");

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
                disconnectSerial();
            }
        }

        function disconnectSerial() {
            isConnected = false;
            if (reader) { try { reader.cancel(); } catch(e){} reader = null; }
            if (port) { try { port.close(); } catch(e){} port = null; }
            updateStatus("disconnected", "Ulanmagan");
        }

        // DEMO SCRIPT
        function toggleDemo() {
            if (isDemo) {
                clearInterval(demoInterval);
                isDemo = false;
                updateStatus("disconnected", "Ulanmagan");
                document.getElementById('demo-btn').innerHTML = '<i class="fa-solid fa-circle-play text-amber-400"></i> Demo';
                updateState({ teeth: 0, esophagus: 0, trachea: 0 });
                return;
            }

            isDemo = true;
            updateStatus("demo", "Demo Rejim");
            document.getElementById('demo-btn').innerHTML = '<i class="fa-solid fa-circle-stop text-rose-400"></i> To'xtatish';

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
                badge.className = "px-3 py-1.5 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-400 text-xs font-semibold flex items-center gap-2";
                badge.querySelector('span').className = "w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping";
                btn.innerHTML = '<i class="fa-solid fa-plug-circle-xmark"></i> Uzish';
                btn.className = "flex-1 px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow-lg shadow-rose-900/30 flex items-center justify-center gap-2 transition cursor-pointer";
            } else if (type === "demo") {
                badge.className = "px-3 py-1.5 rounded-xl bg-amber-950/60 border border-amber-500/40 text-amber-400 text-xs font-semibold flex items-center gap-2";
                badge.querySelector('span').className = "w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse";
            } else {
                badge.className = "px-3 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-slate-400 text-xs font-semibold flex items-center gap-2";
                badge.querySelector('span').className = "w-2.5 h-2.5 rounded-full bg-slate-500";
                btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Portga Ulanish';
                btn.className = "flex-1 px-4 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs shadow-lg shadow-cyan-900/30 flex items-center justify-center gap-2 transition cursor-pointer";
            }
        }

        function logSerial(msg) {
            const box = document.getElementById('log-box');
            const time = new Date().toLocaleTimeString();
            const p = document.createElement('p');
            p.innerText = `[${time}] ${msg}`;
            box.appendChild(p);
            box.scrollTop = box.scrollHeight;
        }

        function clearLogs() {
            document.getElementById('log-box').innerHTML = '<p class="text-slate-600">// Log tozalandi</p>';
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
