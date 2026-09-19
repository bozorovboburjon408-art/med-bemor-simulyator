"""
Tizim Xavfsizlik va Litsenziya Boshqaruvi Moduli (System Lock & License Guard)
===========================================================================
Ushbu modul obuna muddati tugaganida butun tizimni (veb-sahifalar, API va WebSockets)
to'liq va chetlab o'tib bo'lmaydigan qilib qulflash uchun xizmat qiladi.

Qulflashni o'chirish / yoqish:
- SYSTEM_LOCKED = True   -> Tizim to'liq bloklangan ("Obuna muddati tugadi, dasturchiga murojaat qiling")
- SYSTEM_LOCKED = False  -> Tizim normal, ochiq holatda ishlaydi

Dasturchi master paroli: "cail2026" (yoki URL parametri: ?unlock_key=cail2026)
"""

import os
from typing import Optional
from fastapi import Request, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse

# ==============================================================================
# ASOSIY SOZLAMALAR
# ==============================================================================
SYSTEM_LOCKED = True  # True = Qulflangan, False = Ochiq
MASTER_UNLOCK_KEY = "cail2026"  # Dasturchi favqulodda kaliti
LOCK_MESSAGE = "Obuna muddati tugadi, dasturchiga murojaat qiling"

# ==============================================================================
# QULF HOLATINI TEKSHIRISH
# ==============================================================================
def is_system_locked(request: Optional[Request] = None) -> bool:
    """Tizim qulflanganligini tekshiradi (Developer bypass hisobga olingan holda)"""
    if not SYSTEM_LOCKED:
        return False
        
    if request is not None:
        # 1. URL query parametri orqali tekshirish: ?unlock_key=cail2026 yoki ?key=cail2026
        query_key = request.query_params.get("unlock_key") or request.query_params.get("key") or request.query_params.get("dev")
        if query_key == MASTER_UNLOCK_KEY:
            return False
            
        # 2. Cookie orqali tekshirish (dasturchi qulf oynasida parolni kiritgan bo'lsa)
        cookie_key = request.cookies.get("med_dev_unlock_token")
        if cookie_key == MASTER_UNLOCK_KEY:
            return False
            
        # 3. Header orqali tekshirish
        header_key = request.headers.get("X-Dev-Unlock-Key")
        if header_key == MASTER_UNLOCK_KEY:
            return False
            
    return True

def is_system_locked_simple() -> bool:
    """WebSockets yoki oddiy kontekstlar uchun tezkor tekshiruv"""
    return SYSTEM_LOCKED

# ==============================================================================
# HIMOYALANGAN QULF EKRANI (HTML + CSS + JS)
# ==============================================================================
LOCK_SCREEN_HTML = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>Xizmat to'xtatilgan — Obuna muddati tugadi</title>
    <link rel="icon" href="/static/logo.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap');
        
        * {
            -webkit-touch-callout: none;
            -webkit-user-select: none;
            user-select: none;
            box-sizing: border-box;
        }

        body {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #060913;
            color: #f8fafc;
            min-height: 100vh;
            margin: 0;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 50% 20%, rgba(220, 38, 38, 0.18) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(245, 158, 11, 0.08) 0%, transparent 40%),
                radial-gradient(circle at 20% 80%, rgba(220, 38, 38, 0.08) 0%, transparent 40%);
        }

        .mono {
            font-family: 'JetBrains Mono', monospace;
        }

        /* Pulse Animations */
        @keyframes lockPulse {
            0%, 100% {
                transform: scale(1);
                box-shadow: 0 0 35px rgba(239, 68, 68, 0.4), inset 0 0 20px rgba(239, 68, 68, 0.2);
            }
            50% {
                transform: scale(1.05);
                box-shadow: 0 0 60px rgba(239, 68, 68, 0.7), inset 0 0 30px rgba(239, 68, 68, 0.4);
            }
        }

        @keyframes ringWave {
            0% { transform: scale(0.9); opacity: 0.8; }
            100% { transform: scale(1.45); opacity: 0; }
        }

        .lock-icon-container {
            position: relative;
            width: 100px;
            height: 100px;
            border-radius: 50%;
            background: linear-gradient(135deg, #1e1b2e 0%, #0f172a 100%);
            border: 2px solid #ef4444;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: lockPulse 2.8s infinite ease-in-out;
            cursor: pointer;
        }

        .lock-ring {
            position: absolute;
            inset: -8px;
            border-radius: 50%;
            border: 2px solid rgba(239, 68, 68, 0.5);
            animation: ringWave 2.8s infinite cubic-bezier(0.2, 0.8, 0.2, 1);
            pointer-events: none;
        }

        /* Glassmorphism Card */
        .glass-card {
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(239, 68, 68, 0.25);
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8), 0 0 40px -10px rgba(220, 38, 38, 0.25);
        }

        .glass-inset {
            background: rgba(8, 12, 22, 0.65);
            border: 1px solid rgba(255, 255, 255, 0.07);
        }

        /* Scanline effect */
        .scanlines {
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%);
            background-size: 100% 4px;
            z-index: 1;
            pointer-events: none;
            opacity: 0.35;
        }

        /* Modal transitions */
        .modal-active {
            opacity: 1 !important;
            pointer-events: auto !important;
            transform: scale(1) !important;
        }
    </style>
</head>
<body oncontextmenu="return false;">
    <div class="scanlines"></div>

    <main class="relative z-10 w-full max-w-2xl px-4 py-8 mx-auto">
        <div class="glass-card rounded-3xl p-6 sm:p-10 text-center relative overflow-hidden transition-all duration-300">
            
            <!-- Top Gradient Bar -->
            <div class="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-red-600 via-amber-500 to-red-600"></div>

            <!-- Organization Badge -->
            <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-red-950/60 border border-red-500/30 text-red-400 text-xs sm:text-sm font-semibold mb-6 uppercase tracking-wider">
                <span class="w-2 h-2 rounded-full bg-red-500 animate-ping"></span>
                <span>RO'TFMXMO va UIM Navoiy filiali</span>
            </div>

            <!-- Glowing Lock Icon -->
            <div class="flex justify-center mb-6">
                <div id="lockBadge" class="lock-icon-container" title="Dasturchi kirishi uchun bosing" onclick="handleLockClick()">
                    <div class="lock-ring"></div>
                    <i class="fa-solid fa-lock text-4xl text-red-500 drop-shadow-[0_0_12px_rgba(239,68,68,0.8)]"></i>
                </div>
            </div>

            <!-- Main Notice -->
            <h1 class="text-2xl sm:text-3xl md:text-4xl font-black text-white tracking-tight leading-tight mb-4">
                Obuna muddati tugadi, dasturchiga murojat qiling
            </h1>

            <p class="text-slate-300 text-sm sm:text-base leading-relaxed max-w-lg mx-auto mb-8 font-normal">
                Ushbu tibbiy simulyator va monitoring tizimidan foydalanish litsenziyasi muddati yakunlangan. Barcha interaktiv klinik modullar, AI bemor va telemetriya vaqtincha muzlatilgan.
            </p>

            <!-- Information Details Inset -->
            <div class="glass-inset rounded-2xl p-4 sm:p-5 text-left mb-8 space-y-3">
                <div class="flex items-center justify-between text-xs sm:text-sm py-1 border-b border-slate-800/80">
                    <span class="text-slate-400 flex items-center gap-2">
                        <i class="fa-solid fa-shield-halved text-red-400"></i> Xavfsizlik holati:
                    </span>
                    <span class="font-bold text-red-400 uppercase tracking-wide">Xizmat to'xtatilgan</span>
                </div>
                <div class="flex items-center justify-between text-xs sm:text-sm py-1 border-b border-slate-800/80">
                    <span class="text-slate-400 flex items-center gap-2">
                        <i class="fa-solid fa-fingerprint text-slate-400"></i> Tizim ID:
                    </span>
                    <span class="mono font-semibold text-slate-200">MED-SIM-UZ-7704</span>
                </div>
                <div class="flex items-center justify-between text-xs sm:text-sm py-1">
                    <span class="text-slate-400 flex items-center gap-2">
                        <i class="fa-solid fa-headset text-emerald-400"></i> Qayta faollashtirish:
                    </span>
                    <span class="font-semibold text-emerald-400">Dasturchi / CAIL Lab</span>
                </div>
            </div>

            <!-- Footer / Secret Unlock Trigger -->
            <div class="flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500 pt-4 border-t border-slate-800/60">
                <div class="flex items-center gap-2">
                    <i class="fa-solid fa-microchip text-slate-600"></i>
                    <span>NDKTU CAIL Laboratoriyasi &copy; 2026</span>
                </div>
                <button onclick="openUnlockModal()" class="text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1.5 focus:outline-none">
                    <i class="fa-solid fa-key text-[11px]"></i>
                    <span>Dasturchi kaliti</span>
                </button>
            </div>
        </div>
    </main>

    <!-- Developer Unlock Modal -->
    <div id="unlockModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md opacity-0 pointer-events-none transform scale-95 transition-all duration-300">
        <div class="glass-card w-full max-w-md rounded-2xl p-6 sm:p-8 text-left border border-slate-700 shadow-2xl relative">
            <button onclick="closeUnlockModal()" class="absolute top-4 right-4 text-slate-400 hover:text-white text-xl">
                <i class="fa-solid fa-xmark"></i>
            </button>
            
            <div class="flex items-center gap-3 mb-4">
                <div class="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 text-lg">
                    <i class="fa-solid fa-unlock-keyhole"></i>
                </div>
                <div>
                    <h3 class="text-lg font-bold text-white">Dasturchi kirishi</h3>
                    <p class="text-xs text-slate-400">Favqulodda ochish kalitini kiriting</p>
                </div>
            </div>

            <form id="unlockForm" onsubmit="submitUnlock(event)" class="space-y-4">
                <div>
                    <label class="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">Master Kalit</label>
                    <input type="password" id="devKeyInput" placeholder="Kalitni kiriting..." required
                        class="w-full px-4 py-3 rounded-xl bg-slate-900/90 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 mono text-sm">
                </div>

                <div id="unlockError" class="hidden text-xs text-red-400 font-medium flex items-center gap-1.5">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <span>Kiritilgan kalit noto'g'ri!</span>
                </div>

                <div class="flex gap-2 pt-2">
                    <button type="button" onclick="closeUnlockModal()" class="flex-1 py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-sm transition-all">
                        Bekor qilish
                    </button>
                    <button type="submit" class="flex-1 py-2.5 px-4 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-sm shadow-lg shadow-amber-500/20 transition-all">
                        Ochish
                    </button>
                </div>
            </form>
        </div>
    </div>

    <script>
        // Prevent all inspect shortcuts and context menus
        document.addEventListener('contextmenu', e => e.preventDefault());
        document.addEventListener('keydown', e => {
            // F12, Ctrl+Shift+I, Ctrl+Shift+J, Ctrl+U, Ctrl+S
            if (
                e.key === 'F12' ||
                (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'i' || e.key === 'J' || e.key === 'j' || e.key === 'C' || e.key === 'c')) ||
                (e.ctrlKey && (e.key === 'u' || e.key === 'U' || e.key === 's' || e.key === 'S'))
            ) {
                e.preventDefault();
                return false;
            }
            // Shortcut to open developer unlock: Ctrl + Alt + U
            if (e.ctrlKey && e.altKey && (e.key === 'u' || e.key === 'U')) {
                e.preventDefault();
                openUnlockModal();
            }
        });

        let clickCount = 0;
        let clickTimer = null;
        function handleLockClick() {
            clickCount++;
            if (clickCount >= 3) {
                clickCount = 0;
                clearTimeout(clickTimer);
                openUnlockModal();
            } else {
                clearTimeout(clickTimer);
                clickTimer = setTimeout(() => { clickCount = 0; }, 1200);
            }
        }

        function openUnlockModal() {
            const modal = document.getElementById('unlockModal');
            modal.classList.add('modal-active');
            document.getElementById('devKeyInput').value = '';
            document.getElementById('unlockError').classList.add('hidden');
            setTimeout(() => document.getElementById('devKeyInput').focus(), 100);
        }

        function closeUnlockModal() {
            const modal = document.getElementById('unlockModal');
            modal.classList.remove('modal-active');
        }

        async function submitUnlock(e) {
            e.preventDefault();
            const key = document.getElementById('devKeyInput').value.trim();
            if (!key) return;

            // Set cookie for 7 days
            document.cookie = `med_dev_unlock_token=${encodeURIComponent(key)}; path=/; max-age=604800; SameSite=Lax`;

            // Test if valid by doing a fetch to /api/diseases or current path
            try {
                const res = await fetch('/api/diseases');
                if (res.ok) {
                    // Success: Reload page
                    window.location.reload();
                } else {
                    document.getElementById('unlockError').classList.remove('hidden');
                }
            } catch (err) {
                // If fetch fails or key was invalid
                window.location.href = window.location.pathname + '?unlock_key=' + encodeURIComponent(key);
            }
        }
    </script>
</body>
</html>
"""

def get_lock_html() -> str:
    """Qulf ekrani HTML matnini qaytaradi"""
    return LOCK_SCREEN_HTML

def apply_system_lock_middleware(app):
    """
    FastAPI ilovasiga avtomatik qulf middleware o'rnatadi.
    Barcha HTTP so'rovlarni (HTML, JSON, API) to'xtatadi.
    """
    @app.middleware("http")
    async def _system_lock_guard_middleware(request: Request, call_next):
        if is_system_locked(request):
            # API endpointlar uchun 403 JSON qaytarish
            if request.url.path.startswith("/api/"):
                return JSONResponse(
                    status_code=403,
                    content={
                        "status": "error",
                        "code": "SUBSCRIPTION_EXPIRED",
                        "message": LOCK_MESSAGE,
                        "locked": True
                    }
                )
            # Static favicons/logos if needed can be served or returned directly
            if request.url.path == "/static/logo.png" or request.url.path == "/favicon.ico":
                return await call_next(request)
                
            # Barcha boshqa sahifalar (/, /vital, /console, /hub, /intubation va h.k.) uchun qulf sahifasi
            return HTMLResponse(content=get_lock_html(), status_code=403)
            
        return await call_next(request)
