# -*- coding: utf-8 -*-
"""
A4 Formatdagi Shoshilinch Dori Shtrix va QR Kodlari Stikerlari.
Dinamik ravishda medications.json bazasidan yuklanadi va 1 ta A4 qog'ozda chop etiladi.
"""
import json
from medication_manager import load_medications

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RO'TFMXMO va UIM Navoiy filiali — Dori Shtrix va QR Kodlari (A4)</title>
    <link rel="icon" href="/static/logo.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Local & CDN Fallback Barcode & QR Libraries -->
    <script src="/static/js/jsbarcode.min.js"></script>
    <script src="/static/js/qrcode.min.js"></script>
    <script>
        if (typeof JsBarcode === 'undefined') {
            document.write('<script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.5/dist/JsBarcode.all.min.js"><\/script>');
        }
        if (typeof QRCode === 'undefined') {
            document.write('<script src="https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js"><\/script>');
        }
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@600;700;800;900&display=swap');
        
        * {
            box-sizing: border-box;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }

        body {
            font-family: 'Rajdhani', sans-serif;
            background-color: #f1f5f9;
            margin: 0;
            padding: 0;
        }

        .mono {
            font-family: 'Share Tech Mono', monospace;
        }

        /* EXACT A4 PAGE SPECIFICATIONS (210mm x 297mm) */
        .a4-sheet {
            width: 210mm;
            min-height: 297mm;
            padding: 6mm 8mm 6mm 8mm;
            margin: 12px auto;
            background: #ffffff;
            box-shadow: 0 4px 20px rgba(0,0,0,0.12);
            position: relative;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        /* 2 Columns Grid (Fits 10 or more dynamically) */
        .stickers-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 4mm;
            flex: 1;
            margin-top: 2mm;
        }

        /* Individual Sticker Box (approx 94mm x 52mm) */
        .sticker-card {
            border: 1.5px dashed #475569;
            border-radius: 8px;
            padding: 5px 8px 4px 8px;
            background: #ffffff;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
            page-break-inside: avoid;
            overflow: hidden;
            min-height: 48mm;
        }

        .cut-marker {
            position: absolute;
            font-size: 9px;
            color: #94a3b8;
        }

        /* PRINT STYLES */
        @page {
            size: A4 portrait;
            margin: 0;
        }

        @media print {
            body {
                background: #ffffff !important;
            }
            .no-print {
                display: none !important;
            }
            .a4-sheet {
                width: 100% !important;
                margin: 0 !important;
                padding: 6mm 8mm 6mm 8mm !important;
                box-shadow: none !important;
                border: none !important;
                page-break-after: auto !important;
                page-break-inside: avoid !important;
            }
        }
    </style>
</head>
<body>

    <!-- FLOATING TOP CONTROLS (NO-PRINT) -->
    <div class="no-print sticky top-0 z-50 bg-slate-900 text-white px-4 py-2.5 shadow-lg flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center gap-2.5">
            <img src="/static/logo.png" alt="Logo" class="w-9 h-9 rounded-lg object-contain bg-white p-0.5 shrink-0">
            <div>
                <h1 class="font-black text-sm text-white">RO'TFMXMO va UIM Navoiy filiali — Imtihon Dorilari Stikerlari</h1>
                <p class="text-[11px] text-slate-300">Jami <span id="label-count-text">10</span> ta dori stikeri (A4). Chop etib, qirqib oling.</p>
            </div>
        </div>

        <div class="flex items-center gap-2">
            <button onclick="window.print()" class="px-5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-black text-xs rounded-xl shadow-md flex items-center gap-2 cursor-pointer transition active:scale-95">
                <i class="fa-solid fa-print text-sm"></i> 🖨️ A4 CHOP ETISH (PRINT)
            </button>

            <a href="/vital" class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-bold text-xs rounded-xl border border-slate-700 flex items-center gap-1.5 transition">
                <i class="fa-solid fa-arrow-left"></i> Monitorga Qaytish
            </a>
        </div>
    </div>

    <!-- PRINTABLE A4 SHEET -->
    <div class="a4-sheet">
        
        <!-- Sheet Header Info -->
        <div class="border-b-2 border-slate-800 pb-1.5 flex items-center justify-between">
            <div class="flex items-center gap-2.5">
                <img src="/static/logo.png" alt="Logo" class="w-9 h-9 object-contain shrink-0">
                <div>
                    <div class="font-black text-xs text-slate-900 uppercase tracking-wide">RO'TFMXMO va UIM Navoiy filiali</div>
                    <div class="text-[9px] text-slate-600 font-bold">Simulyatsion Imtihon va Amaliyot Dorilari Shtrix & QR Kodlari (A4)</div>
                </div>
            </div>
            <div class="text-[9px] font-bold text-slate-700 mono bg-slate-100 px-2 py-0.5 rounded border border-slate-300">
                1D Code-128 + 2D QR Code
            </div>
        </div>

        <!-- Stickers Grid -->
        <div class="stickers-grid" id="stickers-container"></div>

        <!-- Sheet Footer -->
        <div class="border-t border-slate-300 pt-1 mt-2 flex items-center justify-between text-[8px] text-slate-500 font-bold">
            <span>✂️ Chiziqlar bo'ylab qaychi bilan qirqib oling va ampula / flakonlarga yopishtiring</span>
            <span>OSCE Medical Simulation Exam System • Web Serial / HID Barcode Ready</span>
        </div>

    </div>

    <script>
        const MEDICATIONS = __MEDICATIONS_JSON__;

        function renderStickers() {
            const countEl = document.getElementById("label-count-text");
            if (countEl) countEl.innerText = MEDICATIONS.length;

            const container = document.getElementById("stickers-container");
            container.innerHTML = MEDICATIONS.map(m => `
                <div class="sticker-card">
                    <!-- Cut icon indicator -->
                    <span class="cut-marker top-0.5 right-1">✂️</span>

                    <!-- 1. Header: Name & Code Badge -->
                    <div class="flex items-center justify-between border-b border-slate-200 pb-1">
                        <div>
                            <div class="font-black text-[11px] text-slate-900 leading-none uppercase">${m.name}</div>
                            <div class="text-[8px] font-bold text-slate-500 leading-tight">${m.group || "Klinik dori"}</div>
                        </div>
                        <span class="mono font-black text-[10px] text-white px-2 py-0.5 rounded shadow-xs" style="background-color: ${m.badgeBg || '#4f46e5'};">
                            ${m.code}
                        </span>
                    </div>

                    <!-- 2. Middle Row: 2D QR Code + 1D Barcode -->
                    <div class="flex items-center justify-between my-1 gap-2">
                        <!-- Left: Crisp 2D QR Code -->
                        <div class="flex flex-col items-center bg-white p-0.5 rounded border border-slate-200 shrink-0">
                            <div id="qr-${m.code}" class="w-[30mm] h-[30mm] flex items-center justify-center"></div>
                            <span class="text-[7px] font-black text-slate-600 mt-0.5 mono">QR: ${m.code}</span>
                        </div>

                        <!-- Right: Crisp 1D Barcode (Code 128) -->
                        <div class="flex-1 flex flex-col items-center justify-center bg-white p-1 rounded border border-slate-200 overflow-hidden">
                            <svg id="barcode-${m.code}" class="w-full max-h-[28mm] block"></svg>
                        </div>
                    </div>

                    <!-- 3. Bottom Footer: Indication & Barcode Text -->
                    <div class="flex items-center justify-between border-t border-slate-200 pt-0.5 text-[8px]">
                        <span class="font-black text-slate-700 truncate mr-1">${m.desc || m.group}</span>
                        <span class="mono font-bold text-slate-500 shrink-0">Barkod: ${m.code}</span>
                    </div>
                </div>
            `).join("");

            // Generate each barcode and QR code
            setTimeout(() => {
                MEDICATIONS.forEach(m => {
                    // Generate 1D Barcode
                    try {
                        JsBarcode(`#barcode-${m.code}`, m.code, {
                            format: "CODE128",
                            width: 1.5,
                            height: 32,
                            displayValue: true,
                            fontSize: 10,
                            font: "Share Tech Mono, monospace",
                            textMargin: 1,
                            margin: 0
                        });
                    } catch(e) {
                        console.error("JsBarcode error for " + m.code, e);
                    }

                    // Generate 2D QR Code
                    try {
                        const qrContainer = document.getElementById(`qr-${m.code}`);
                        if (qrContainer) {
                            qrContainer.innerHTML = "";
                            new QRCode(qrContainer, {
                                text: m.code,
                                width: 68,
                                height: 68,
                                colorDark: "#000000",
                                colorLight: "#ffffff",
                                correctLevel: QRCode.CorrectLevel.M
                            });
                        }
                    } catch(e) {
                        console.error("QRCode error for " + m.code, e);
                    }
                });
            }, 100);
        }

        window.onload = renderStickers;
    </script>
</body>
</html>
"""

def get_labels_html() -> str:
    meds = load_medications()
    meds_json = json.dumps(meds, ensure_ascii=False)
    return HTML_TEMPLATE.replace("__MEDICATIONS_JSON__", meds_json)

LABELS_HTML = get_labels_html()
