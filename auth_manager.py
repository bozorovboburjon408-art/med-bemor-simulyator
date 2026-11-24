# -*- coding: utf-8 -*-
"""
MedLife Xavfsizlik va Avtorizatsiya Moduli (Auth & Device Tracking Manager)
========================================================================
1. Foydalanuvchi va Admin autentifikatsiyasi (Cookie-based session)
2. Kirilgan barcha qurilmalarni aniqlash va kuzatish (Device, OS, Browser, IP)
3. Umumiy statistika va monitoring (Admin Dashboard)
"""

import os
import json
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import Request, Response, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

AUTH_FILE = os.path.join(os.path.dirname(__file__), "auth_sessions.json")
COOKIE_NAME = "medlife_auth_token"
SESSION_LIFETIME_DAYS = 30

# Standart hisob ma'lumotlari
ACCOUNTS = {
    "malaka@gmail.com": {
        "password": "malaka123",
        "role": "user",
        "name": "Malaka Markazi"
    },
    "admin@gmail.com": {
        "password": "admin123",
        "role": "admin",
        "name": "Tizim Administratori"
    }
}

# ==============================================================================
# QURILMA VA BRAUZERNI ANIQLASH (USER-AGENT PARSER)
# ==============================================================================
def parse_user_agent(ua_string: str) -> Dict[str, str]:
    ua = ua_string or ""
    
    # 1. Operatsion tizim (OS)
    os_name = "Noma'lum OS"
    if "Windows NT 10.0" in ua:
        os_name = "Windows 10/11"
    elif "Windows NT 6.3" in ua:
        os_name = "Windows 8.1"
    elif "Windows NT 6.1" in ua:
        os_name = "Windows 7"
    elif "Windows" in ua:
        os_name = "Windows"
    elif "Android" in ua:
        m = re.search(r"Android\s+([\d\.]+)", ua)
        os_name = f"Android {m.group(1)}" if m else "Android"
    elif "iPhone" in ua:
        m = re.search(r"OS\s+([\d_]+)", ua)
        ver = m.group(1).replace("_", ".") if m else ""
        os_name = f"iOS {ver}" if ver else "iOS (iPhone)"
    elif "iPad" in ua:
        os_name = "iPadOS"
    elif "Macintosh" in ua or "Mac OS X" in ua:
        os_name = "macOS"
    elif "Linux" in ua:
        os_name = "Linux"

    # 2. Qurilma turi
    device_type = "Kompyuter (Desktop)"
    if "Mobile" in ua or ("Android" in ua and "Tablet" not in ua) or "iPhone" in ua:
        device_type = "Telefon (Mobile)"
    elif "Tablet" in ua or "iPad" in ua:
        device_type = "Planshet (Tablet)"

    # 3. Brauzer
    browser = "Noma'lum Brauzer"
    if "Edg/" in ua or "Edge/" in ua:
        m = re.search(r"Edg[e]?\/([\d\.]+)", ua)
        browser = f"MS Edge {m.group(1).split('.')[0]}" if m else "Edge"
    elif "OPR/" in ua or "Opera" in ua:
        browser = "Opera"
    elif "Chrome/" in ua and "Chromium" not in ua:
        m = re.search(r"Chrome\/([\d\.]+)", ua)
        browser = f"Chrome {m.group(1).split('.')[0]}" if m else "Chrome"
    elif "Safari/" in ua and "Chrome" not in ua:
        m = re.search(r"Version\/([\d\.]+)", ua)
        browser = f"Safari {m.group(1).split('.')[0]}" if m else "Safari"
    elif "Firefox/" in ua:
        m = re.search(r"Firefox\/([\d\.]+)", ua)
        browser = f"Firefox {m.group(1).split('.')[0]}" if m else "Firefox"

    return {
        "os": os_name,
        "browser": browser,
        "device_type": device_type
    }

def get_client_ip(request: Request) -> str:
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip.strip()
    if request.client and request.client.host:
        return request.client.host.strip()
    return "127.0.0.1"

# ==============================================================================
# MA'LUMOTLARNI SAQLASH VA YUKLASH
# ==============================================================================
def load_auth_data() -> Dict[str, Any]:
    if not os.path.exists(AUTH_FILE):
        return {
            "sessions": {},
            "history": [],
            "stats": {
                "total_logins": 0,
                "user_logins": 0,
                "admin_logins": 0,
                "ai_calls": 0
            }
        }
    try:
        with open(AUTH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"sessions": {}, "history": [], "stats": {"total_logins": 0, "user_logins": 0, "admin_logins": 0, "ai_calls": 0}}

def save_auth_data(data: Dict[str, Any]):
    try:
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Xatolik auth saqlashda: {e}")

# ==============================================================================
# SESSIYA BOSHQARUVI
# ==============================================================================
def create_session(email: str, role: str, ip: str, user_agent: str) -> str:
    data = load_auth_data()
    token = secrets.token_urlsafe(32)
    ua_info = parse_user_agent(user_agent)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    session_record = {
        "session_id": token,
        "email": email,
        "role": role,
        "name": ACCOUNTS.get(email, {}).get("name", email),
        "ip": ip,
        "os": ua_info["os"],
        "browser": ua_info["browser"],
        "device_type": ua_info["device_type"],
        "user_agent": user_agent[:150],
        "login_time": now_str,
        "last_active": now_str,
        "is_active": True
    }

    data["sessions"][token] = session_record
    
    # Tarixga qo'shish (oxirgi 100 ta kirish saqlanadi)
    history_record = {
        "email": email,
        "role": role,
        "ip": ip,
        "os": ua_info["os"],
        "browser": ua_info["browser"],
        "device_type": ua_info["device_type"],
        "time": now_str
    }
    data["history"].insert(0, history_record)
    if len(data["history"]) > 100:
        data["history"] = data["history"][:100]

    # Statistika hisoblagichlarini yangilash
    stats = data.setdefault("stats", {"total_logins": 0, "user_logins": 0, "admin_logins": 0, "ai_calls": 0})
    stats["total_logins"] = stats.get("total_logins", 0) + 1
    if role == "admin":
        stats["admin_logins"] = stats.get("admin_logins", 0) + 1
    else:
        stats["user_logins"] = stats.get("user_logins", 0) + 1

    save_auth_data(data)
    return token

def get_session(token: Optional[str]) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    data = load_auth_data()
    session = data.get("sessions", {}).get(token)
    if session and session.get("is_active"):
        return session
    return None

def update_session_activity(token: str, ip: Optional[str] = None):
    if not token:
        return
    data = load_auth_data()
    session = data.get("sessions", {}).get(token)
    if session and session.get("is_active"):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session["last_active"] = now_str
        if ip:
            session["ip"] = ip
        save_auth_data(data)

def terminate_session(token: str) -> bool:
    data = load_auth_data()
    if token in data.get("sessions", {}):
        data["sessions"][token]["is_active"] = False
        save_auth_data(data)
        return True
    return False

def terminate_all_except(current_token: Optional[str] = None) -> int:
    data = load_auth_data()
    count = 0
    for tok, sess in list(data.get("sessions", {}).items()):
        if tok != current_token and sess.get("is_active"):
            sess["is_active"] = False
            count += 1
    save_auth_data(data)
    return count

def record_ai_call():
    data = load_auth_data()
    stats = data.setdefault("stats", {"total_logins": 0, "user_logins": 0, "admin_logins": 0, "ai_calls": 0})
    stats["ai_calls"] = stats.get("ai_calls", 0) + 1
    save_auth_data(data)

def get_admin_dashboard_data() -> Dict[str, Any]:
    data = load_auth_data()
    sessions = list(data.get("sessions", {}).values())
    
    # 15 daqiqa ichida faol bo'lganlar - Online hisoblanadi
    now = datetime.now()
    active_devices = []
    inactive_devices = []

    for s in sessions:
        if not s.get("is_active"):
            continue
        try:
            last_dt = datetime.strptime(s["last_active"], "%Y-%m-%d %H:%M:%S")
            is_online = (now - last_dt) <= timedelta(minutes=15)
        except Exception:
            is_online = False
        
        s_copy = dict(s)
        s_copy["is_online"] = is_online
        if is_online:
            active_devices.append(s_copy)
        else:
            inactive_devices.append(s_copy)

    # Qurilmalar turlari bo'yicha taqsimot
    device_counts = {"Desktop": 0, "Mobile": 0, "Tablet": 0}
    for s in active_devices + inactive_devices:
        dtype = s.get("device_type", "")
        if "Desktop" in dtype or "Kompyuter" in dtype:
            device_counts["Desktop"] += 1
        elif "Mobile" in dtype or "Telefon" in dtype:
            device_counts["Mobile"] += 1
        elif "Tablet" in dtype or "Planshet" in dtype:
            device_counts["Tablet"] += 1

    stats = data.get("stats", {})
    return {
        "stats": {
            "total_logins": stats.get("total_logins", 0),
            "user_logins": stats.get("user_logins", 0),
            "admin_logins": stats.get("admin_logins", 0),
            "ai_calls": stats.get("ai_calls", 0),
            "online_devices": len(active_devices),
            "total_sessions": len(active_devices) + len(inactive_devices),
            "device_types": device_counts
        },
        "active_devices": active_devices,
        "inactive_devices": inactive_devices[:30],
        "history": data.get("history", [])[:30]
    }

# ==============================================================================
# LOGIN VA ADMIN HTML SHABLONLARI
# ==============================================================================
LOGIN_PAGE_HTML = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>Kirish — RO'TFMXMO va UIM Navoiy filiali | MedLife</title>
    <link rel="icon" href="/static/logo.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: #0b1120;
            background-image: 
                radial-gradient(circle at 20% 20%, rgba(14, 165, 233, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 80% 80%, rgba(99, 102, 241, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.08) 0%, transparent 50%);
        }
        .glass-card {
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
    </style>
</head>
<body class="min-h-screen flex items-center justify-center p-4 text-slate-100">
    <div class="w-full max-w-md">
        <!-- Markaziy Kirish Kartochkasi -->
        <div class="glass-card rounded-3xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
            <!-- Yuqori dekorativ chiziq -->
            <div class="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-cyan-500 via-indigo-500 to-emerald-500"></div>

            <!-- Logo & Sarlavha -->
            <div class="text-center mb-6 pt-2">
                <div class="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-white/10 p-2 border border-white/20 shadow-lg shadow-cyan-500/20 mb-4">
                    <img src="/static/logo.png" alt="MedLife Logo" class="w-full h-full object-contain">
                </div>
                <div class="inline-block px-3 py-1 rounded-full bg-cyan-950/80 border border-cyan-500/40 text-cyan-300 text-[11px] font-bold uppercase tracking-wider mb-2">
                    RO'TFMXMO va UIM Navoiy filiali
                </div>
                <h1 class="text-2xl font-black text-white tracking-tight">Tibbiy Simulyator Tizimi</h1>
                <p class="text-xs text-slate-400 mt-1">Xavfsiz boshqaruv va simulyatsiyaga kirish</p>
            </div>

            <!-- Xatolik xabari -->
            <div id="error-alert" class="hidden mb-4 p-3.5 rounded-xl bg-rose-950/80 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2.5">
                <i class="fa-solid fa-circle-exclamation text-rose-400 text-base shrink-0"></i>
                <span id="error-message">Login yoki parol noto'g'ri</span>
            </div>

            <!-- Forma -->
            <form id="login-form" onsubmit="handleLogin(event)" class="space-y-4">
                <div>
                    <label class="block text-xs font-bold text-slate-300 mb-1.5 flex items-center gap-1.5">
                        <i class="fa-regular fa-envelope text-cyan-400"></i> Login (Email)
                    </label>
                    <div class="relative">
                        <input type="email" id="email" required autocomplete="username"
                               placeholder="Email manzilingiz"
                               class="w-full bg-slate-800/90 border border-slate-700 focus:border-cyan-400 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 outline-none transition shadow-inner">
                    </div>
                </div>

                <div>
                    <label class="block text-xs font-bold text-slate-300 mb-1.5 flex items-center gap-1.5">
                        <i class="fa-solid fa-lock text-cyan-400"></i> Maxfiy Parol
                    </label>
                    <div class="relative">
                        <input type="password" id="password" required autocomplete="current-password"
                               placeholder="••••••••"
                               class="w-full bg-slate-800/90 border border-slate-700 focus:border-cyan-400 rounded-xl px-4 py-3 pr-11 text-sm text-white placeholder-slate-500 outline-none transition shadow-inner">
                        <button type="button" onclick="togglePasswordVisibility()" class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white transition text-sm p-1">
                            <i id="password-toggle-icon" class="fa-regular fa-eye"></i>
                        </button>
                    </div>
                </div>

                <div class="flex items-center text-xs text-slate-400 pt-1">
                    <label class="flex items-center gap-2 cursor-pointer select-none">
                        <input type="checkbox" id="remember" checked class="rounded border-slate-700 bg-slate-800 text-cyan-500 focus:ring-0">
                        <span>Qurilmani eslab qolish</span>
                    </label>
                </div>

                <button type="submit" id="submit-btn" class="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-cyan-500 via-indigo-600 to-emerald-500 hover:from-cyan-400 hover:via-indigo-500 hover:to-emerald-400 text-white font-bold text-sm shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 transition-all duration-200 cursor-pointer mt-2">
                    <i class="fa-solid fa-right-to-bracket"></i>
                    <span id="btn-text">Tizimga Kirish</span>
                </button>
            </form>

            <!-- Footer -->
            <div class="text-center text-[10px] text-slate-500 mt-6 pt-5 border-t border-slate-800/80 flex items-center justify-center gap-1.5">
                <i class="fa-solid fa-shield-halved text-emerald-400"></i>
                <span>Xavfsiz sessiya va qurilmalar nazorati faol &copy; 2026</span>
            </div>
        </div>
    </div>

    <script>
        function togglePasswordVisibility() {
            const pass = document.getElementById("password");
            const icon = document.getElementById("password-toggle-icon");
            if (pass.type === "password") {
                pass.type = "text";
                icon.className = "fa-regular fa-eye-slash";
            } else {
                pass.type = "password";
                icon.className = "fa-regular fa-eye";
            }
        }

        async function handleLogin(e) {
            e.preventDefault();
            const email = document.getElementById("email").value.trim();
            const password = document.getElementById("password").value.trim();
            const errAlert = document.getElementById("error-alert");
            const errMsg = document.getElementById("error-message");
            const submitBtn = document.getElementById("submit-btn");
            const btnText = document.getElementById("btn-text");

            errAlert.classList.add("hidden");
            submitBtn.disabled = true;
            btnText.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Tekshirilmoqda...';

            try {
                const res = await fetch("/api/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password })
                });
                const data = await res.json();
                if (res.ok && data.status === "ok") {
                    btnText.innerHTML = '<i class="fa-solid fa-circle-check text-emerald-400"></i> Muvaffaqiyatli!';
                    const urlParams = new URLSearchParams(window.location.search);
                    const nextUrl = urlParams.get("next") || data.redirect || "/hub";
                    setTimeout(() => {
                        window.location.href = nextUrl;
                    }, 400);
                } else {
                    errMsg.innerText = data.message || "Login yoki parol noto'g'ri kiritildi!";
                    errAlert.classList.remove("hidden");
                    submitBtn.disabled = false;
                    btnText.innerText = "Tizimga Kirish";
                }
            } catch(err) {
                errMsg.innerText = "Server bilan bog'lanishda xatolik yuz berdi.";
                errAlert.classList.remove("hidden");
                submitBtn.disabled = false;
                btnText.innerText = "Tizimga Kirish";
            }
        }
    </script>
</body>
</html>
"""

ADMIN_PANEL_HTML = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>Admin Dashboard — Qurilmalar va Statistika | MedLife</title>
    <link rel="icon" href="/static/logo.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap');
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: #0b1120;
        }
        .mono {
            font-family: 'JetBrains Mono', monospace;
        }
    </style>
</head>
<body class="min-h-screen text-slate-100 flex flex-col">
    <!-- Top Navigation -->
    <header class="bg-slate-900/90 border-b border-slate-800 backdrop-blur sticky top-0 z-50 px-4 md:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-3">
            <img src="/static/logo.png" alt="Logo" class="w-10 h-10 object-contain rounded-xl bg-white/10 p-1 border border-indigo-500/30">
            <div>
                <div class="flex items-center gap-2">
                    <h1 class="text-base md:text-lg font-black tracking-tight text-white flex items-center gap-2">
                        MedLife Admin Panel
                    </h1>
                    <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">Xavfsizlik & Qurilmalar</span>
                </div>
                <div class="text-[11px] text-slate-400">RO'TFMXMO va UIM Navoiy filiali</div>
            </div>
        </div>

        <div class="flex items-center gap-2.5">
            <div class="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800 border border-slate-700 text-xs">
                <i class="fa-solid fa-user-shield text-indigo-400"></i>
                <span class="font-medium text-slate-300">admin@gmail.com</span>
            </div>

            <a href="/hub" class="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-bold flex items-center gap-1.5 transition">
                <i class="fa-solid fa-shapes text-cyan-400"></i>
                <span>Ilovalar Markazi</span>
            </a>

            <a href="/" class="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-bold flex items-center gap-1.5 transition">
                <i class="fa-solid fa-heart-pulse text-emerald-400"></i>
                <span>AI Bemor</span>
            </a>

            <a href="/logout" class="px-3.5 py-1.5 rounded-xl bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40 text-xs font-bold flex items-center gap-1.5 transition">
                <i class="fa-solid fa-right-from-bracket"></i>
                <span>Chiqish</span>
            </a>
        </div>
    </header>

    <!-- Main Content -->
    <main class="flex-1 max-w-7xl w-full mx-auto p-4 md:p-8 space-y-6">
        <!-- Quick Stats Cards Grid -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <!-- 1. Hozir Onlayn -->
            <div class="p-4 md:p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg relative overflow-hidden">
                <div class="flex items-center justify-between text-xs text-slate-400 mb-2">
                    <span class="font-bold uppercase tracking-wider">Hozir Onlayn</span>
                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping"></span>
                </div>
                <div class="text-2xl md:text-3xl font-black text-white" id="stat-online-devices">--</div>
                <div class="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
                    <i class="fa-solid fa-circle-check"></i> Faol qurilmalar
                </div>
            </div>

            <!-- 2. Jami Kirishlar -->
            <div class="p-4 md:p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg">
                <div class="flex items-center justify-between text-xs text-slate-400 mb-2">
                    <span class="font-bold uppercase tracking-wider">Jami Kirishlar</span>
                    <i class="fa-solid fa-right-to-bracket text-indigo-400"></i>
                </div>
                <div class="text-2xl md:text-3xl font-black text-white" id="stat-total-logins">--</div>
                <div class="text-[11px] text-slate-400 mt-1">
                    Malaka: <span id="stat-user-logins" class="text-cyan-400 font-bold">--</span> | Admin: <span id="stat-admin-logins" class="text-indigo-400 font-bold">--</span>
                </div>
            </div>

            <!-- 3. AI Bemor Muloqotlari -->
            <div class="p-4 md:p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg">
                <div class="flex items-center justify-between text-xs text-slate-400 mb-2">
                    <span class="font-bold uppercase tracking-wider">AI Bemor Seanslari</span>
                    <i class="fa-solid fa-stethoscope text-cyan-400"></i>
                </div>
                <div class="text-2xl md:text-3xl font-black text-white" id="stat-ai-calls">--</div>
                <div class="text-[11px] text-cyan-400 mt-1">
                    Jonli muloqot va tekshiruvlar
                </div>
            </div>

            <!-- 4. Qurilmalar turlari -->
            <div class="p-4 md:p-5 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-lg">
                <div class="flex items-center justify-between text-xs text-slate-400 mb-2">
                    <span class="font-bold uppercase tracking-wider">Qurilma Turlari</span>
                    <i class="fa-solid fa-desktop text-amber-400"></i>
                </div>
                <div class="text-sm font-bold text-white space-y-0.5 mt-1">
                    <div class="flex justify-between text-xs"><span>💻 Kompyuter:</span> <b id="stat-dev-desktop" class="text-slate-200">--</b></div>
                    <div class="flex justify-between text-xs"><span>📱 Telefon:</span> <b id="stat-dev-mobile" class="text-slate-200">--</b></div>
                    <div class="flex justify-between text-xs"><span>📟 Planshet:</span> <b id="stat-dev-tablet" class="text-slate-200">--</b></div>
                </div>
            </div>
        </div>

        <!-- Kirilgan Qurilmalar Jadvali -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
            <div class="p-4 md:p-5 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-slate-900/50">
                <div>
                    <h2 class="text-base font-bold text-white flex items-center gap-2">
                        <i class="fa-solid fa-network-wired text-cyan-400"></i>
                        Kirilgan Qurilmalar Monitoringi
                    </h2>
                    <p class="text-xs text-slate-400">Tizimga ulangan barcha qurilmalar, ularning IP manzili va holati</p>
                </div>
                <div class="flex items-center gap-2">
                    <button onclick="fetchAdminData()" class="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold flex items-center gap-1.5 transition">
                        <i class="fa-solid fa-rotate text-cyan-400"></i> Yangilash
                    </button>
                    <button onclick="kickAllOtherDevices()" class="px-3 py-1.5 rounded-xl bg-rose-950/80 hover:bg-rose-900 text-rose-300 border border-rose-500/40 text-xs font-bold flex items-center gap-1.5 transition">
                        <i class="fa-solid fa-ban text-rose-400"></i> Boshqa barcha qurilmalardan chiqarish
                    </button>
                </div>
            </div>

            <!-- Table -->
            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs text-slate-300">
                    <thead class="bg-slate-950/60 text-slate-400 font-bold uppercase tracking-wider text-[10px] border-b border-slate-800">
                        <tr>
                            <th class="py-3 px-4">Qurilma / Tizim</th>
                            <th class="py-3 px-4">Brauzer</th>
                            <th class="py-3 px-4">Akkaunt</th>
                            <th class="py-3 px-4">IP Manzil</th>
                            <th class="py-3 px-4">Kirilgan Vaqt</th>
                            <th class="py-3 px-4">Oxirgi Faollik</th>
                            <th class="py-3 px-4">Holat</th>
                            <th class="py-3 px-4 text-right">Amal</th>
                        </tr>
                    </thead>
                    <tbody id="devices-table-body" class="divide-y divide-slate-800/60 font-medium">
                        <tr>
                            <td colspan="8" class="text-center py-8 text-slate-500">
                                <i class="fa-solid fa-spinner animate-spin text-lg mb-2"></i><br>Qurilmalar yuklanmoqda...
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Oxirgi Kirishlar Tarixi (Audit Log) -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
            <div class="p-4 md:p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
                <div>
                    <h2 class="text-base font-bold text-white flex items-center gap-2">
                        <i class="fa-solid fa-clock-rotate-left text-indigo-400"></i>
                        Oxirgi Kirishlar Tarixi (Audit Log)
                    </h2>
                    <p class="text-xs text-slate-400">Tizimga kirish bo'yicha so'nggi xronologik ro'yxat</p>
                </div>
                <span class="text-xs text-slate-500 font-mono">So'nggi 30 ta yozuv</span>
            </div>

            <div class="overflow-x-auto max-h-80 overflow-y-auto">
                <table class="w-full text-left text-xs text-slate-300">
                    <thead class="bg-slate-950/60 text-slate-400 font-bold uppercase tracking-wider text-[10px] sticky top-0 border-b border-slate-800">
                        <tr>
                            <th class="py-2.5 px-4">Vaqt</th>
                            <th class="py-2.5 px-4">Akkaunt</th>
                            <th class="py-2.5 px-4">IP Manzil</th>
                            <th class="py-2.5 px-4">Operatsion Tizim</th>
                            <th class="py-2.5 px-4">Brauzer</th>
                            <th class="py-2.5 px-4">Qurilma</th>
                        </tr>
                    </thead>
                    <tbody id="history-table-body" class="divide-y divide-slate-800/60">
                        <tr>
                            <td colspan="6" class="text-center py-6 text-slate-500">Yuklanmoqda...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </main>

    <!-- Footer -->
    <footer class="mt-auto border-t border-slate-800/80 py-4 px-6 text-center text-xs text-slate-500 flex flex-wrap items-center justify-between gap-2">
        <div class="flex items-center gap-2">
            <i class="fa-solid fa-shield-halved text-emerald-400"></i>
            <span>MedLife Xavfsizlik & Monitoring Tizimi &copy; 2026</span>
        </div>
        <div class="text-[11px] text-slate-400">
            RO'TFMXMO va UIM Navoiy filiali
        </div>
    </footer>

    <script>
        function escapeHtml(str) {
            if (!str) return '';
            return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        }

        function getDeviceIcon(deviceType) {
            if (deviceType.includes('Telefon') || deviceType.includes('Mobile')) return 'fa-mobile-screen text-cyan-400';
            if (deviceType.includes('Planshet') || deviceType.includes('Tablet')) return 'fa-tablet-screen-button text-amber-400';
            return 'fa-laptop text-indigo-400';
        }

        async function fetchAdminData() {
            try {
                const res = await fetch("/api/admin/devices");
                if (res.status === 401 || res.status === 403) {
                    window.location.href = "/login?next=/admin";
                    return;
                }
                const data = await res.json();
                renderStats(data.stats);
                renderDevices(data.active_devices, data.inactive_devices);
                renderHistory(data.history);
            } catch(e) {
                console.error("Admin ma'lumotlarini yuklashda xatolik:", e);
            }
        }

        function renderStats(stats) {
            if (!stats) return;
            document.getElementById("stat-online-devices").innerText = stats.online_devices + " ta";
            document.getElementById("stat-total-logins").innerText = stats.total_logins;
            document.getElementById("stat-user-logins").innerText = stats.user_logins;
            document.getElementById("stat-admin-logins").innerText = stats.admin_logins;
            document.getElementById("stat-ai-calls").innerText = stats.ai_calls;

            const dt = stats.device_types || {};
            document.getElementById("stat-dev-desktop").innerText = dt.Desktop || 0;
            document.getElementById("stat-dev-mobile").innerText = dt.Mobile || 0;
            document.getElementById("stat-dev-tablet").innerText = dt.Tablet || 0;
        }

        function renderDevices(active, inactive) {
            const tbody = document.getElementById("devices-table-body");
            const all = [...(active || []), ...(inactive || [])];
            
            if (all.length === 0) {
                tbody.innerHTML = `<tr><td colspan="8" class="text-center py-8 text-slate-500">Hech qanday qurilma topilmadi</td></tr>`;
                return;
            }

            tbody.innerHTML = all.map(d => {
                const icon = getDeviceIcon(d.device_type || '');
                const statusBadge = d.is_online 
                    ? `<span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-500/30 font-bold text-[10px]"><span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>Onlayn</span>`
                    : `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700 font-medium text-[10px]"><span class="w-1.5 h-1.5 rounded-full bg-slate-500"></span>Oflayn</span>`;

                const roleBadge = d.role === 'admin'
                    ? `<span class="px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 font-bold border border-indigo-500/30 text-[10px]">Admin</span>`
                    : `<span class="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 font-bold border border-cyan-500/30 text-[10px]">Foydalanuvchi</span>`;

                return `
                    <tr class="hover:bg-slate-800/40 transition">
                        <td class="py-3 px-4">
                            <div class="flex items-center gap-2.5">
                                <i class="fa-solid ${icon} text-base"></i>
                                <div>
                                    <div class="font-bold text-white">${escapeHtml(d.os || 'Nomaʼlum')}</div>
                                    <div class="text-[10px] text-slate-400">${escapeHtml(d.device_type || '')}</div>
                                </div>
                            </div>
                        </td>
                        <td class="py-3 px-4 text-slate-200">${escapeHtml(d.browser || 'Nomaʼlum')}</td>
                        <td class="py-3 px-4">
                            <div class="font-bold text-slate-200">${escapeHtml(d.email || '')}</div>
                            ${roleBadge}
                        </td>
                        <td class="py-3 px-4 mono text-cyan-400">${escapeHtml(d.ip || '127.0.0.1')}</td>
                        <td class="py-3 px-4 text-slate-400 mono text-[11px]">${escapeHtml(d.login_time || '')}</td>
                        <td class="py-3 px-4 text-slate-300 mono text-[11px]">${escapeHtml(d.last_active || '')}</td>
                        <td class="py-3 px-4">${statusBadge}</td>
                        <td class="py-3 px-4 text-right">
                            <button onclick="kickDevice('${escapeHtml(d.session_id)}')" class="px-2.5 py-1 rounded-lg bg-rose-950/70 hover:bg-rose-900 text-rose-300 border border-rose-500/40 text-[11px] font-bold transition" title="Sessiyani to'xtatish">
                                <i class="fa-solid fa-xmark mr-1"></i> Chiqarish
                            </button>
                        </td>
                    </tr>
                `;
            }).join("");
        }

        function renderHistory(history) {
            const tbody = document.getElementById("history-table-body");
            if (!history || history.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center py-6 text-slate-500">Tarix bo'sh</td></tr>`;
                return;
            }

            tbody.innerHTML = history.map(h => `
                <tr class="hover:bg-slate-800/30 transition">
                    <td class="py-2.5 px-4 text-slate-400 mono text-[11px]">${escapeHtml(h.time || '')}</td>
                    <td class="py-2.5 px-4 font-bold text-slate-200">
                        ${escapeHtml(h.email || '')} 
                        <span class="text-[10px] text-slate-500">(${escapeHtml(h.role || '')})</span>
                    </td>
                    <td class="py-2.5 px-4 mono text-cyan-400">${escapeHtml(h.ip || '')}</td>
                    <td class="py-2.5 px-4 text-slate-300">${escapeHtml(h.os || '')}</td>
                    <td class="py-2.5 px-4 text-slate-300">${escapeHtml(h.browser || '')}</td>
                    <td class="py-2.5 px-4 text-slate-400">${escapeHtml(h.device_type || '')}</td>
                </tr>
            `).join("");
        }

        async function kickDevice(sessionId) {
            if (!confirm("Ushbu qurilmani tizimdan chiqarib yubormoqchimisiz?")) return;
            try {
                const res = await fetch("/api/admin/kick_device", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ session_id: sessionId })
                });
                if (res.ok) {
                    await fetchAdminData();
                }
            } catch(e) {
                alert("Xatolik yuz berdi: " + e.message);
            }
        }

        async function kickAllOtherDevices() {
            if (!confirm("O'zingizdan tashqari barcha boshqa qurilmalarni tizimdan chiqarib yubormoqchimisiz?")) return;
            try {
                const res = await fetch("/api/admin/clear_all", { method: "POST" });
                if (res.ok) {
                    await fetchAdminData();
                }
            } catch(e) {
                alert("Xatolik yuz berdi: " + e.message);
            }
        }

        // Dastlabki yuklash va avto-yangilanish (har 15 soniyada)
        fetchAdminData();
        setInterval(fetchAdminData, 15000);
    </script>
</body>
</html>
"""

def get_login_html() -> str:
    return LOGIN_PAGE_HTML

def get_admin_html() -> str:
    return ADMIN_PANEL_HTML


# ==============================================================================
# FASTAPI AUTH MIDDLEWARE
# ==============================================================================
def apply_auth_middleware(app):
    """
    FastAPI ilovasiga xavfsiz avtorizatsiya middleware'ini o'rnatadi.
    Tizimga kirmagan har qanday foydalanuvchini /login sahifasiga yo'naltiradi.
    """
    @app.middleware("http")
    async def _auth_guard_middleware(request: Request, call_next):
        path = request.url.path

        # Dasturchi master kaliti orqali kirish
        if request.query_params.get("unlock_key") == "21082007Bb":
            return await call_next(request)

        # 1. Ochiq yo'llar (Login, Logout, Static, Favicon, Manifest, SW)
        if (
            path == "/login" or
            path == "/api/login" or
            path == "/logout" or
            path == "/api/logout" or
            path.startswith("/static/") or
            path.startswith("/manifest") or
            path == "/sw.js" or
            path == "/favicon.ico" or
            path == "/manikin_photo.png" or
            path.startswith("/audio/") or
            path.startswith("/intubation/assets/")
        ):
            return await call_next(request)

        # 2. Cookie orqali sessiyani tekshirish
        token = request.cookies.get(COOKIE_NAME)
        session = get_session(token) if token else None

        if session:
            # Faollikni yangilash
            update_session_activity(token, get_client_ip(request))
            request.state.user = session

            # Admin yo'llariga kirishni tekshirish
            if path == "/admin" or path.startswith("/api/admin/"):
                if session.get("role") != "admin":
                    if path.startswith("/api/"):
                        return JSONResponse(status_code=403, content={"status": "error", "message": "Faqat administrator uchun ruxsat etilgan"})
                    return RedirectResponse(url="/hub?err=admin_only", status_code=303)

            return await call_next(request)

        # 3. Agar sessiya yo'q bo'lsa
        if path.startswith("/api/"):
            return JSONResponse(status_code=401, content={"status": "error", "message": "Avtorizatsiyadan o'tilmagan. Iltimos, tizimga kiring."})

        # Veb-sahifalar uchun login sahifasiga yo'naltirish
        next_param = f"?next={path}" if path not in ["/", "/hub"] else ""
        return RedirectResponse(url=f"/login{next_param}", status_code=303)
