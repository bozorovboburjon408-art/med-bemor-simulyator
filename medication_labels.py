# -*- coding: utf-8 -*-
"""
A4 Formatdagi 10 ta Shoshilinch Dori Shtrix va QR Kodlari Stikerlari.
Haqiqiy 1D va 2D skanerlar uchun yuqori kontrastli vektor shtrix-kodlar.
"""

LABELS_HTML = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dori Shtrix va QR Kodlari — 1 ta A4 Chop Etish (Print)</title>
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
            height: 297mm;
            padding: 6mm 8mm 6mm 8mm;
            margin: 12px auto;
            background: #ffffff;
            box-shadow: 0 4px 20px rgba(0,0,0,0.12);
            position: relative;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        /* 2 Columns x 5 Rows Grid */
        .stickers-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            grid-template-rows: repeat(5, 1fr);
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
                height: 100vh !important;
                min-height: 100% !important;
                margin: 0 !important;
                padding: 6mm 8mm 6mm 8mm !important;
                box-shadow: none !important;
                border: none !important;
                page-break-after: avoid !important;
                page-break-inside: avoid !important;
            }
        }
    </style>
</head>
<body>

    <!-- FLOATING TOP CONTROLS (NO-PRINT) -->
    <div class="no-print sticky top-0 z-50 bg-slate-900 text-white px-4 py-3 shadow-lg flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center gap-2">
            <span class="w-8 h-8 rounded-lg bg-purple-600 text-white flex items-center justify-center font-bold">
                <i class="fa-solid fa-barcode"></i>
            </span>
            <div>
                <h1 class="font-black text-sm text-white">IMTIHON DORILARI SHTRIX & QR KODLAR STIKERLARI</h1>
                <p class="text-[11px] text-slate-300">10 ta dori aniq 1 ta A4 varag'iga sig'dirilgan. Chop etib, qirqib oling.</p>
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
            <div class="flex items-center gap-2">
                <span class="w-6 h-6 rounded-md bg-slate-900 text-white flex items-center justify-center text-xs font-black">
                    <i class="fa-solid fa-hospital"></i>
                </span>
                <div>
                    <span class="font-black text-xs text-slate-900 uppercase tracking-wide">TIBBIY SIMULYATSIYA MARKAZI — IMTIHON DORILARI SHTRIX & QR KODLARI</span>
                    <span class="text-[9px] text-slate-600 font-semibold ml-2">Standart A4 | 10 ta Ampula Stikeri</span>
                </div>
            </div>
            <div class="text-[9px] font-bold text-slate-700 mono bg-slate-100 px-2 py-0.5 rounded border border-slate-300">
                1D Code-128 + 2D QR Code
            </div>
        </div>

        <!-- 2x5 Stickers Grid (All 10 fit on this single sheet) -->
        <div class="stickers-grid" id="stickers-container">
            <!-- Dynamically populated or rendered below -->
        </div>

        <!-- Sheet Footer -->
        <div class="border-t border-slate-300 pt-1 flex items-center justify-between text-[8px] text-slate-500 font-bold">
            <span>✂️ Chiziqlar bo'ylab qaychi bilan qirqib oling va ampula / flakonlarga yopishtiring</span>
            <span>OSCE Medical Simulation Exam System • Web Serial / HID Barcode Ready</span>
        </div>

    </div>

    <script>
        const MEDICATIONS = [
            {
                code: "ADR-01",
                name: "ADRENALIN (Epinefrin) 1 mg/ml",
                group: "Adrenomimetik (Vazopressor)",
                desc: "ACLS • Asistoliya • Anafilaksiya",
                barcodeNum: "4780001001",
                badgeBg: "#7e22ce"
            },
            {
                code: "AMI-02",
                name: "AMIODARON (Kordaron) 150 mg",
                group: "Antiaritmik (III-sinf)",
                desc: "Qorincha taxikardiyasi (VTach)",
                barcodeNum: "4780001002",
                badgeBg: "#0284c7"
            },
            {
                code: "ATR-03",
                name: "ATROPIN SULFAT 1 mg/ml",
                group: "M-Xolinoblokator",
                desc: "Bradikardiya • Sust puls",
                barcodeNum: "4780001003",
                badgeBg: "#d97706"
            },
            {
                code: "NIT-04",
                name: "NITROGLITSERIN 0.5 mg",
                group: "Periferik vazodilatator",
                desc: "Gipertonik kriz • Stenokardiya",
                barcodeNum: "4780001004",
                badgeBg: "#e11d48"
            },
            {
                code: "MET-05",
                name: "METOPROLOL (Betalok) 5 mg",
                group: "Beta-1 adrenoblokator",
                desc: "Taxikardiya • Gipertoniya",
                barcodeNum: "4780001005",
                badgeBg: "#4f46e5"
            },
            {
                code: "SAL-06",
                name: "FIZRASTVOR (0.9% NaCl) 500 ml",
                group: "Kristalloid plazma o'rnini bosuvchi",
                desc: "Gipovolemik shok • Bosim tiklash",
                barcodeNum: "4780001006",
                badgeBg: "#2563eb"
            },
            {
                code: "DEX-07",
                name: "DEKSAMETAZON 8 mg/2ml",
                group: "Glikokortikosteroid (Gormon)",
                desc: "Bronxospazm • O'tkir gipoksiya",
                barcodeNum: "4780001007",
                badgeBg: "#059669"
            },
            {
                code: "NAL-08",
                name: "NALOKSON 0.4 mg/ml",
                group: "Opioid retseptorlari antagonisti",
                desc: "Narkotik intoksikatsiyasi",
                barcodeNum: "4780001008",
                badgeBg: "#0d9488"
            },
            {
                code: "KCL-09",
                name: "KALIY XLORID (KCl 4%) 20 ml",
                group: "Elektrolit (Toksik konsentrat)",
                desc: "DIQQAT: Toksik kardioplegiya!",
                barcodeNum: "4780001009",
                badgeBg: "#dc2626"
            },
            {
                code: "FUR-10",
                name: "FUROSEMID (Laziks) 20 mg",
                group: "Halqa diuretigi",
                desc: "O'pka shishi • Diurez tezlatuvchi",
                barcodeNum: "4780001010",
                badgeBg: "#0891b2"
            }
        ];

        function renderStickers() {
            const container = document.getElementById("stickers-container");
            container.innerHTML = MEDICATIONS.map(m => `
                <div class="sticker-card">
                    <!-- Cut icon indicator -->
                    <span class="cut-marker top-0.5 right-1">✂️</span>

                    <!-- 1. Header: Name & Code Badge -->
                    <div class="flex items-center justify-between border-b border-slate-200 pb-1">
                        <div>
                            <div class="font-black text-[11px] text-slate-900 leading-none uppercase">${m.name}</div>
                            <div class="text-[8px] font-bold text-slate-500 leading-tight">${m.group}</div>
                        </div>
                        <span class="mono font-black text-[10px] text-white px-2 py-0.5 rounded shadow-xs" style="background-color: ${m.badgeBg};">
                            ${m.code}
                        </span>
                    </div>

                    <!-- 2. Middle Row: 2D QR Code + 1D Barcode -->
                    <div class="flex items-center justify-between my-1 gap-2">
                        <!-- Left: Crisp 2D QR Code -->
                        <div class="flex flex-col items-center bg-white p-0.5 rounded border border-slate-200 shrink-0">
                            <div id="qr-${m.code}" class="w-[32mm] h-[32mm] flex items-center justify-center"></div>
                            <span class="text-[7px] font-black text-slate-600 mt-0.5 mono">QR: ${m.code}</span>
                        </div>

                        <!-- Right: Crisp 1D Barcode (Code 128) -->
                        <div class="flex-1 flex flex-col items-center justify-center bg-white p-1 rounded border border-slate-200 overflow-hidden">
                            <svg id="barcode-${m.code}" class="w-full max-h-[30mm] block"></svg>
                        </div>
                    </div>

                    <!-- 3. Bottom Footer: Indication & Barcode Text -->
                    <div class="flex items-center justify-between border-t border-slate-200 pt-0.5 text-[8px]">
                        <span class="font-black text-slate-700">${m.desc}</span>
                        <span class="mono font-bold text-slate-500">Barkod: ${m.code}</span>
                    </div>
                </div>
            `).join("");

            // Now generate each barcode and QR code
            setTimeout(() => {
                MEDICATIONS.forEach(m => {
                    // Generate 1D Barcode
                    try {
                        JsBarcode(`#barcode-${m.code}`, m.code, {
                            format: "CODE128",
                            width: 1.5,
                            height: 34,
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
                                width: 72,
                                height: 72,
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
