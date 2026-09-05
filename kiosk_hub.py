# -*- coding: utf-8 -*-
"""
MedLife Touchscreen Kiosk Hub - Sensorli Ekran Ilovalar Markazi
"""

HUB_HTML = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="theme-color" content="#020617">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <link rel="manifest" href="/manifest_hub.json">
    <link rel="icon" href="/static/logo.png">
    <title>RO'TFMXMO va UIM Navoiy filiali — Sensorli Tibbiyot Kiosk Markazi</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Inter:wght@400;500;600;700;800;900&display=swap');
        * {
            -webkit-touch-callout: none;
            touch-action: manipulation;
        }
        body {
            font-family: 'Inter', sans-serif;
            background: radial-gradient(circle at 50% 15%, #0f172a 0%, #020617 100%);
            user-select: none;
            overflow-x: hidden;
        }
        .mono { font-family: 'Share Tech Mono', monospace; }
        .touch-card {
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .touch-card:active {
            transform: scale(0.97);
        }
        @keyframes pulse-glow {
            0%, 100% { opacity: 0.7; transform: scale(1); }
            50% { opacity: 1; transform: scale(1.03); }
        }
        .pulse-effect {
            animation: pulse-glow 3s infinite ease-in-out;
        }
    </style>
</head>
<body class="min-h-screen text-slate-100 flex flex-col justify-between p-4 md:p-8">

    <!-- TOP BAR -->
    <header class="flex flex-wrap items-center justify-between gap-4 bg-slate-900/90 backdrop-blur border border-slate-800 rounded-2xl px-6 py-4 shadow-xl">
        <div class="flex items-center gap-4">
            <img src="/static/logo.png" alt="Markaz Logosi" class="w-14 h-14 object-contain rounded-2xl bg-white/10 p-1 border border-cyan-500/30 shadow-lg shadow-cyan-500/10 shrink-0">
            <div>
                <h1 class="text-lg md:text-xl font-black tracking-wide text-white flex items-center gap-2">
                    RO'TFMXMO va UIM Navoiy filiali
                    <span class="text-cyan-400 font-bold text-xs border border-cyan-500/40 px-2 py-0.5 rounded-full bg-cyan-950/60 hidden sm:inline-block">SENSORLI KIOSK</span>
                </h1>
                <p class="text-xs text-slate-300 font-medium mt-0.5">Respublika o'rta tibbiyot va farmatsevtika xodimlari malakasini oshirish va ularni ixtisoslashtirish markazi</p>
                <p class="text-[11px] text-cyan-400/90 font-semibold">Amaliy ko'nikmalar va imtihon simulyatsiyasi markazi</p>
            </div>
        </div>

        <div class="flex items-center gap-3">
            <div class="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800/80 border border-slate-700 text-slate-300 text-xs font-mono">
                <i class="fa-regular fa-clock text-cyan-400"></i>
                <span id="hub-clock">--:--:--</span>
            </div>

            <!-- INSTALL PWA BUTTON -->
            <button id="pwa-install-btn" onclick="installKioskPWA()" class="hidden px-4 py-2 rounded-xl bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-400 hover:to-emerald-500 text-white font-bold text-xs md:text-sm shadow-lg shadow-emerald-900/40 flex items-center gap-2 cursor-pointer transition">
                <i class="fa-solid fa-cloud-arrow-down text-sm"></i>
                <span>Ilovani O'rnatish</span>
            </button>

            <!-- FULLSCREEN TOGGLE -->
            <button onclick="toggleFullScreen()" class="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs md:text-sm font-bold flex items-center gap-1.5 cursor-pointer transition">
                <i class="fa-solid fa-expand text-cyan-400"></i>
                <span class="hidden sm:inline">To'liq Ekran</span>
            </button>
        </div>
    </header>

    <!-- MAIN APPS GRID -->
    <main class="my-8">
        <div class="text-center mb-8">
            <h2 class="text-2xl md:text-4xl font-extrabold text-white tracking-tight">
                Sensorli Ekranda Kerakli Ilovani Tanlang
            </h2>
            <p class="text-slate-400 text-sm md:text-base mt-2 max-w-2xl mx-auto">
                Har bir ilovani alohida derazada, to'liq ekranda ochish yoki kompyuterga rasmiy ilova (PWA) sifatida o'rnatib olish mumkin.
            </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 max-w-7xl mx-auto">

            <!-- APP 1: BEMOR AI -->
            <div class="touch-card bg-gradient-to-b from-slate-900/90 to-slate-950/90 border-2 border-teal-500/30 hover:border-teal-400/80 rounded-3xl p-6 md:p-8 flex flex-col justify-between shadow-2xl relative overflow-hidden group">
                <div class="absolute -right-8 -top-8 w-40 h-40 bg-teal-500/10 rounded-full blur-3xl pointer-events-none"></div>
                <div>
                    <div class="flex items-center justify-between mb-6">
                        <div class="w-16 h-16 rounded-2xl bg-teal-500/20 border border-teal-500/40 flex items-center justify-center text-teal-300 text-3xl shadow-inner">
                            <i class="fa-solid fa-user-doctor"></i>
                        </div>
                        <span class="text-xs font-bold font-mono px-3 py-1 rounded-full bg-teal-950 border border-teal-800 text-teal-300">
                            ILOVA #1
                        </span>
                    </div>
                    <h3 class="text-2xl font-black text-white group-hover:text-teal-300 transition">
                        AI Bemor Simulyatori
                    </h3>
                    <p class="text-slate-400 text-sm mt-3 leading-relaxed">
                        Bemor bilan ovozli va matnli jonli muloqot. Fonendoskop eshitish, 14 ta chuqurlashtirilgan kasallik profili va real vaqtda sun'iy intellekt javoblari.
                    </p>
                    <div class="flex flex-wrap gap-2 mt-5">
                        <span class="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-slate-800 text-teal-300 border border-slate-700">🗣️ Ovozli Muloqot</span>
                        <span class="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-slate-800 text-teal-300 border border-slate-700">🩺 Fonendoskop</span>
                        <span class="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-slate-800 text-teal-300 border border-slate-700">📋 14 Kasallik</span>
                    </div>
                </div>

                <div class="mt-8 space-y-3">
                    <a href="/" class="w-full py-4 rounded-2xl bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-400 hover:to-emerald-500 text-white font-extrabold text-base shadow-xl shadow-teal-950 flex items-center justify-center gap-3 transition">
                        <i class="fa-solid fa-arrow-up-right-from-square"></i>
                        <span>Sensorli Ekranda Ochish</span>
                    </a>
                    <a href="/?source=pwa" target="_blank" class="w-full py-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs font-bold flex items-center justify-center gap-2 transition">
                        <i class="fa-solid fa-desktop text-teal-400"></i>
                        <span>Alohida Oyna / Kioska</span>
                    </a>
                </div>
            </div>

            <!-- APP 2: VITAL MONITOR -->
            <div class="touch-card bg-gradient-to-b from-slate-900/90 to-slate-950/90 border-2 border-emerald-500/30 hover:border-emerald-400/80 rounded-3xl p-6 md:p-8 flex flex-col justify-between shadow-2xl relative overflow-hidden group">
                <div class="absolute -right-8 -top-8 w-40 h-40 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>
                <div>
                    <div class="flex items-center justify-between mb-6">
                        <div class="w-16 h-16 rounded-2xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-300 text-3xl shadow-inner">
                            <i class="fa-solid fa-heart-pulse"></i>
                        </div>
                        <span class="text-xs font-bold font-mono px-3 py-1 rounded-full bg-emerald-950 border border-emerald-800 text-emerald-300">
                            ILOVA #2
                        </span>
                    </div>
                    <h3 class="text-2xl font-black text-white group-hover:text-emerald-300 transition">
                        ICU Vital Monitor & Pnevmatika
                    </h3>
                    <p class="text-slate-400 text-sm mt-3 leading-relaxed">
                        Reanimatsiya kardiomonitori: EKG ritmi, SpO2, qon bosimi, nafas chastotasi. Arduino USB orqali pnevmatik kompressor va tomir urish klapanini boshqarish.
                    </p>
                    <div class="flex flex-wrap gap-2 mt-5">
                        <span class="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-slate-800 text-emerald-300 border border-slate-700">📈 EKG Sinus/V-Tach</span>
                        <span class="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-slate-800 text-emerald-300 border border-slate-700">💨 Kompressor & Klapan</span>
                        <span class="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-slate-800 text-emerald-300 border border-slate-700">⚡ Defibrillyator</span>
                    </div>
                </div>

                <div class="mt-8 space-y-3">
                    <a href="/vital" class="w-full py-4 rounded-2xl bg-gradient-to-r from-emerald-600 to-green-500 hover:from-emerald-500 hover:to-green-400 text-white font-extrabold text-base shadow-xl shadow-emerald-950 flex items-center justify-center gap-3 transition">
                        <i class="fa-solid fa-arrow-up-right-from-square"></i>
                        <span>Sensorli Ekranda Ochish</span>
                    </a>
                    <a href="/vital?source=pwa" target="_blank" class="w-full py-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs font-bold flex items-center justify-center gap-2 transition">
                        <i class="fa-solid fa-desktop text-emerald-400"></i>
                        <span>Alohida Oyna / Kioska</span>
                    </a>
                </div>
            </div>

            <!-- APP 3: MANIKEN PULTI -->
            <div class="touch-card bg-gradient-to-b from-slate-900/90 to-slate-950/90 border-2 border-indigo-500/30 hover:border-indigo-400/80 rounded-3xl p-6 md:p-8 flex flex-col justify-between shadow-2xl relative overflow-hidden group">
                <div class="absolute -right-8 -top-8 w-40 h-40 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none"></div>
                <div>
                    <div class="flex items-center justify-between mb-6">
                        <div class="w-16 h-16 rounded-2xl bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center text-indigo-300 text-3xl shadow-inner">
                            <i class="fa-solid fa-gamepad"></i>
                        </div>
                        <span class="text-xs font-bold font-mono px-3 py-1 rounded-full bg-indigo-950 border border-indigo-800 text-indigo-300">
                            ILOVA #3
                        </span>
                    </div>
                    <h3 class="text-2xl font-black text-white group-hover:text-indigo-300 transition">
                        Maniken Pulti & Imtihon
                    </h3>
                    <p class="text-slate-400 text-sm mt-3 leading-relaxed">
                        GD/H126 manikeni datchiklari pulti: ko'krak massaji chuqurligi va kuchi (kg), o'pka va oshqozon havo datchiklari, inyeksiya hamda talaba imtihonini baholash.
                    </p>
                    <div class="flex flex-wrap gap-2 mt-5">
                        <span class="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-slate-800 text-indigo-300 border border-slate-700">🏋️ Massaj Kuchi (kg)</span>
                        <span class="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-slate-800 text-indigo-300 border border-slate-700">🫁 O'pka Ventilyatsiyasi</span>
                        <span class="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-slate-800 text-indigo-300 border border-slate-700">🎓 Imtihon Baholash</span>
                    </div>
                </div>

                <div class="mt-8 space-y-3">
                    <a href="/console" class="w-full py-4 rounded-2xl bg-gradient-to-r from-indigo-600 to-blue-500 hover:from-indigo-500 hover:to-blue-400 text-white font-extrabold text-base shadow-xl shadow-indigo-950 flex items-center justify-center gap-3 transition">
                        <i class="fa-solid fa-arrow-up-right-from-square"></i>
                        <span>Sensorli Ekranda Ochish</span>
                    </a>
                    <a href="/console?source=pwa" target="_blank" class="w-full py-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs font-bold flex items-center justify-center gap-2 transition">
                        <i class="fa-solid fa-desktop text-indigo-400"></i>
                        <span>Alohida Oyna / Kioska</span>
                    </a>
                </div>
            </div>

            <!-- APP 4: INTUBATSIYA MODULI -->
            <div class="touch-card bg-gradient-to-b from-slate-900/90 to-slate-950/90 border-2 border-purple-500/30 hover:border-purple-400/80 rounded-3xl p-6 md:p-8 flex flex-col justify-between shadow-2xl relative overflow-hidden group">
                <div class="absolute -right-8 -top-8 w-40 h-40 bg-purple-500/10 rounded-full blur-3xl pointer-events-none"></div>
                <div>
                    <div class="flex items-center justify-between mb-6">
                        <div class="w-16 h-16 rounded-2xl bg-purple-500/20 border border-purple-500/40 flex items-center justify-center text-purple-300 text-3xl shadow-inner">
                            <i class="fa-solid fa-stethoscope"></i>
                        </div>
                        <span class="text-xs font-bold font-mono px-3 py-1 rounded-full bg-purple-950 border border-purple-800 text-purple-300">
                            ILOVA #4
                        </span>
                    </div>

                    <h3 class="text-2xl font-black text-white group-hover:text-purple-300 transition">
                        Intubatsiya Moduli
                    </h3>
                    <p class="text-slate-400 text-sm mt-3 leading-relaxed">
                        Traxeya va qizilo'ngach intubatsiyasi: Tish, O'pka va Oshqozon yo'li datchiklari real vaqt monitoringi, audio ogohlantirish hamda vizual anatomiya animatsiyasi.
                    </p>
                    <div class="flex flex-wrap gap-2 mt-5">
                        <span class="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-slate-800 text-purple-300 border border-slate-700">🩸 Anatomiya Overlay</span>
                        <span class="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-slate-800 text-purple-300 border border-slate-700">🔊 Realtime Audio</span>
                        <span class="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-slate-800 text-purple-300 border border-slate-700">⚡ Web Serial API</span>
                    </div>
                </div>

                <div class="mt-8 space-y-3">
                    <a href="/intubation" class="w-full py-4 rounded-2xl bg-gradient-to-r from-purple-600 to-pink-500 hover:from-purple-500 hover:to-pink-400 text-white font-extrabold text-base shadow-xl shadow-purple-950 flex items-center justify-center gap-3 transition">
                        <i class="fa-solid fa-arrow-up-right-from-square"></i>
                        <span>Sensorli Ekranda Ochish</span>
                    </a>
                    <a href="/intubation?source=pwa" target="_blank" class="w-full py-2.5 rounded-xl bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-300 text-xs font-bold flex items-center justify-center gap-2 transition">
                        <i class="fa-solid fa-desktop text-purple-400"></i>
                        <span>Alohida Oyna / Kioska</span>
                    </a>
                </div>
            </div>

        </div>
    </main>

    <!-- FOOTER / KIOSK INSTRUCTIONS -->
    <footer class="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-4 md:p-6 text-xs text-slate-400 max-w-7xl mx-auto w-full">
        <div class="flex flex-wrap items-center justify-between gap-4">
            <div class="flex items-center gap-3">
                <i class="fa-solid fa-circle-info text-cyan-400 text-lg"></i>
                <div>
                    <span class="font-bold text-slate-200">Sensorli Ekranda Foydalanish Qoidalari:</span>
                    <p class="text-slate-400 text-[11px] mt-0.5">Brauzerda to'liq ekranga o'tish uchun klaviaturadan <b>F11</b> ni bosing yoki yuqoridagi <b>"To'liq Ekran"</b> tugmasidan foydalaning.</p>
                </div>
            </div>
            <div class="flex items-center gap-2 text-slate-400 text-[11px]">
                <span>RO'TFMXMO va UIM Navoiy filiali • Tibbiyot Simulyatori & GD/H126 Maniken Tizimi</span>
                <span>•</span>
                <span class="text-emerald-400 font-mono">v3.0 Kiosk</span>
            </div>
        </div>
    </footer>

    <!-- PWA & KIOSK LOGIC -->
    <script>
        let deferredPrompt = null;

        // Register Service Worker
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js').catch(() => {});
            });
        }

        // Catch PWA Install Prompt
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            const btn = document.getElementById('pwa-install-btn');
            if (btn) btn.classList.remove('hidden');
        });

        async function installKioskPWA() {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                if (outcome === 'accepted') {
                    const btn = document.getElementById('pwa-install-btn');
                    if (btn) btn.classList.add('hidden');
                }
                deferredPrompt = null;
            } else {
                alert("Ilovani o'rnatish uchun brauzer menyusidagi 'O'rnatish' (Install App) tugmasini bosing yoki Chrome/Edge brauzerining manzil satridagi belgi orqali o'rnating.");
            }
        }

        function toggleFullScreen() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(() => {});
            } else {
                if (document.exitFullscreen) document.exitFullscreen().catch(() => {});
            }
        }

        // Live Clock
        setInterval(() => {
            const now = new Date();
            const el = document.getElementById('hub-clock');
            if (el) el.innerText = now.toTimeString().split(' ')[0];
        }, 1000);
    </script>
</body>
</html>
"""
