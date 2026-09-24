import os
import subprocess

# 1. Edge / Chrome path detection
edge_paths = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe"
]
browser_exe = None
for p in edge_paths:
    if os.path.exists(p):
        browser_exe = p
        break

if not browser_exe:
    raise RuntimeError("Browser for PDF generation not found!")

# Common CSS for official document styling
COMMON_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap');

@page {
    size: A4;
    margin: 15mm 15mm 15mm 15mm;
}

* {
    box-sizing: border-box;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #0f172a;
    line-height: 1.5;
    font-size: 10.5pt;
    background: #ffffff;
    margin: 0;
    padding: 0;
}

.mono {
    font-family: 'JetBrains Mono', monospace;
}

/* Headers & Document Cover */
.doc-header {
    border-bottom: 2px solid #1e3a8a;
    padding-bottom: 12px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.doc-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 8.5pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.badge-blue { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
.badge-emerald { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
.badge-purple { background: #faf5ff; color: #6b21a8; border: 1px solid #e9d5ff; }

.main-title {
    font-size: 16pt;
    font-weight: 900;
    color: #0f172a;
    line-height: 1.3;
    margin: 10px 0 6px 0;
}

.subtitle {
    font-size: 10pt;
    color: #475569;
    font-weight: 500;
    margin-bottom: 15px;
}

/* Section Styling */
.section {
    margin-bottom: 18px;
    page-break-inside: avoid;
}

.section-title {
    font-size: 11.5pt;
    font-weight: 800;
    color: #1e3a8a;
    border-left: 4px solid #2563eb;
    padding-left: 8px;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

.section-title.emerald {
    color: #065f46;
    border-left-color: #059669;
}

p {
    margin: 0 0 8px 0;
    text-align: justify;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0 14px 0;
    font-size: 9.5pt;
}

th, td {
    border: 1px solid #cbd5e1;
    padding: 6px 10px;
    text-align: left;
    vertical-align: top;
}

th {
    background-color: #f1f5f9;
    font-weight: 700;
    color: #1e293b;
}

.table-highlight {
    background-color: #f8fafc;
}

/* Highlight boxes */
.info-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #3b82f6;
    border-radius: 6px;
    padding: 10px 12px;
    margin: 10px 0;
    font-size: 9.5pt;
}

.info-box.success {
    background: #f0fdf4;
    border-color: #bbf7d0;
    border-left-color: #16a34a;
}

.info-box.warning {
    background: #fffbeb;
    border-color: #fde68a;
    border-left-color: #d97706;
}

.grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}

.grid-3 {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 10px;
}

.stat-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 8px 12px;
    text-align: center;
}

.stat-num {
    font-size: 14pt;
    font-weight: 900;
    color: #1d4ed8;
}

.stat-label {
    font-size: 8pt;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
}

.page-break {
    page-break-before: always;
}

.footer-sign {
    margin-top: 25px;
    padding-top: 15px;
    border-top: 1px dashed #cbd5e1;
    display: flex;
    justify-content: space-between;
    font-size: 9pt;
    color: #475569;
}
"""

# ==============================================================================
# 1-LOYIHA: Vital Monitor & CPR Simulyatori HTML
# ==============================================================================
HTML_LOYIHA_1 = f"""<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="utf-8">
    <title>MedLife 1 - Vital Monitor va CPR Reanimatsiya Simulyatori Tavsifnomasi</title>
    <style>{COMMON_CSS}</style>
</head>
<body>

    <!-- Header / Passport -->
    <div class="doc-header">
        <div>
            <div style="font-size: 8pt; font-weight: 800; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">
                O'zbekiston Respublikasi Oliy Ta'lim, Fan va Innovatsiyalar Vazirligi
            </div>
            <div style="font-size: 9pt; font-weight: 700; color: #1e3a8a;">
                «Ixtiro va Innovatsion Ishlanmalar Tanlovi» (Ixtiro.ilmiy.uz)
            </div>
        </div>
        <div class="doc-badge badge-blue">
            Loyiha Pasporti & Tavsifnomasi
        </div>
    </div>

    <div class="main-title">
        MedLife: Vital Monitor va CPR Reanimatsiya Imtihon Simulyatori
    </div>
    <div class="subtitle">
        ESP32 datchikli maniken, pnevmo-tenso telemetriya, RFID dori skaneri va ICU Vital Monitor baholash majmuasi
    </div>

    <!-- 1. Loyiha Pasporti Jadvali -->
    <div class="section">
        <div class="section-title">1. Loyiha Pasporti (Asosiy Ko'rsatkichlar)</div>
        <table>
            <tr>
                <th style="width: 30%;">Loyiha nomi</th>
                <td style="width: 70%; font-weight: 700;">MedLife: Vital Monitor va CPR Reanimatsiya Imtihon Simulyatori</td>
            </tr>
            <tr>
                <th>Ariza yo'nalishi va turi</th>
                <td>Ixtiro / Amaliy dasturiy-apparat majmuasi (Tibbiy simulyatsiya va bioinjiniring)</td>
            </tr>
            <tr>
                <th>Bajaruvchi muassasa</th>
                <td>RO'TFMXMO va UIM Navoiy filiali hamda NDKTU CAIL laboratoriyasi</td>
            </tr>
            <tr>
                <th>Loyiha umumiy qiymati</th>
                <td style="color: #1d4ed8; font-weight: 800;">400 000 000 (To'rt yuz million) so'm</td>
            </tr>
            <tr>
                <th>Xorijiy analoglar narxi</th>
                <td style="color: #b91c1c; font-weight: 800;">1 000 000 000 — 1 500 000 000 so'm ($80 000 - $120 000)</td>
            </tr>
            <tr>
                <th>Iqtisodiy tejamkorlik</th>
                <td style="color: #15803d; font-weight: 800;">Har bir xaridda kamida 600 - 800 mln so'm (2.5 - 3 baravar arzon)</td>
            </tr>
            <tr>
                <th>Asosiy texnologiyalar</th>
                <td>ESP32, HX711 tenzo-kuch datchigi, MPX5010 pnevmo-datchik, RFID RC522, WebSerial API, Python FastAPI, WebSockets</td>
            </tr>
        </table>
    </div>

    <!-- 2. Muammoning Dolzarbligi -->
    <div class="section">
        <div class="section-title">2. Muammoning Dolzarbligi va Tahlili</div>
        <p>
            Shoshilinch tibbiy yordam va reanimatsiyada <b>Yurak-o'pka reanimatsiyasi (CPR 30:2)</b> ko'nikmasi inson hayotini saqlab qolishda hal qiluvchi ahamiyatga ega. Biroq an'anaviy tibbiyot ta'limida talabalarning reanimatsiya sifatini aniq, millisekundlarda va raqamli o'lchash imkoniyati mavjud emas.
        </p>
        <div class="info-box warning">
            <b>Mavjud asosiy muammolar:</b>
            <ul style="margin: 4px 0 0 15px; padding: 0;">
                <li><b>Subyektiv baholash:</b> O'qituvchi talabaning ko'krak qafasini qanchalik chuqur bosgani (40-60 kg) yoki nafas hajmini ko'z bilan xolis baholay olmaydi.</li>
                <li><b>Xorijiy simulyatorlarning haddan tashqari qimmatligi:</b> Import qilinadigan tizimlar (Laerdal SimMan, Gaumard) narxi 1-1.5 mlrd so'mdan oshadi va ularni O'zbekistonning barcha tibbiyot kollejlari va oliygohlariga yetkazish davlat byudjetiga katta yuk bo'ladi.</li>
                <li><b>Xolis imtihon bayonnomasi yo'qligi:</b> Talaba va rezidentlar uchun avtomatlashgan, xolis protokol chiqarib beruvchi milliy tizim mavjud emas.</li>
            </ul>
        </div>
    </div>

    <!-- 3. Loyihaning Maqsadi va Ilmiy-Texnik Yechimi -->
    <div class="section">
        <div class="section-title">3. Loyihaning Maqsadi va Innovatsion Yechimi</div>
        <p>
            Loyiha AHA/ERC xalqaro standartlari asosida ishlaydigan, mahalliy komponentlardan yasalgan va arzon tannarxga ega bo'lgan <b>raqamli CPR imtihon majmuasi</b>ni yaratishni maqsad qilgan.
        </p>
        <div class="grid-3">
            <div class="stat-card">
                <div class="stat-num">40-60 kg</div>
                <div class="stat-label">Bosish kuchi datchigi</div>
            </div>
            <div class="stat-card">
                <div class="stat-num">100-120</div>
                <div class="stat-label">BPM Ritm & Chastota</div>
            </div>
            <div class="stat-card">
                <div class="stat-num">0.8-2.2 kPa</div>
                <div class="stat-label">O'pka nafas bosimi</div>
            </div>
        </div>
    </div>

    <div class="page-break"></div>

    <!-- 4. Apparat va Dasturiy Majmua Arxitekturasi -->
    <div class="section">
        <div class="doc-header" style="margin-bottom: 10px;">
            <div style="font-size: 8.5pt; font-weight: 700; color: #64748b;">MedLife: Vital Monitor va CPR Simulyatori</div>
            <div class="doc-badge badge-blue">Texnik Arxitektura</div>
        </div>

        <div class="section-title">4. Apparat va Dasturiy Arxitektura (Hardware & Software)</div>
        <p>
            Majmua ikki asosiy o'zaro sinxron moduldan tashkil topgan:
        </p>
        <table>
            <thead>
                <tr>
                    <th style="width: 25%;">Komponent</th>
                    <th style="width: 35%;">Texnik Tavsifi</th>
                    <th style="width: 40%;">Bajaradigan Vazifasi</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><b>ESP32 Maniken Moduli</b></td>
                    <td>240 MHz 32-bit mikrokontroller, 10 ta GPIO sensor kanallari</td>
                    <td>Kuch datchigi (HX711), pnevmo-datchiklar, pozitsiya tugmalari va RFID dori modulidan signallarni 50 Hz chastotada o'qiydi.</td>
                </tr>
                <tr>
                    <td><b>ICU Vital Monitor (Web)</b></td>
                    <td>FastAPI, WebSerial API, WebSockets, HTML5 Canvas/SVG</td>
                    <td>EKG (II-lead), SpO2 pletizmogramma, NIBP, Kapnografiya, defibrillyatsiya zarbasi va dori infuziyalarini real vaqtda chizadi.</td>
                </tr>
                <tr>
                    <td><b>Smart Farmakoterapiya</b></td>
                    <td>13.56 MHz RFID va Shtrix-kod skaneri</td>
                    <td>Adrenalin, Atropin, Amiodaron kabi 10+ reanimatsion dorilar kiritilishini millisekundda aniqlab, EKG ritmini o'zgartiradi.</td>
                </tr>
                <tr>
                    <td><b>Imtihon Baholash Pulti</b></td>
                    <td>Xolis tahlil algoritmi, PDF/Chop etish generatori</td>
                    <td>Talabaning 30:2 massaj chuqurligi, chastotasi, qo'l pozitsiyasi va dori vaqtini tahlil qilib, 100 ballik imtihon varaqasini chiqaradi.</td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- 5. Bosqichma-bosqich Reanimatsiya Stsenariylari -->
    <div class="section">
        <div class="section-title">5. Xalqaro 4 Bosqichli Klinik Reanimatsiya Jarayoni</div>
        <div class="info-box success">
            <b>AHA/ERC standartlariga mos stsenariy dinamikasi:</b>
            <ol style="margin: 4px 0 0 18px; padding: 0;">
                <li><b>0-BOSQICH (Asistoliya — 0 BPM):</b> Bemor hushsiz, puls yo'q. CPR 30:2 massaji va Adrenalin kutiladi.</li>
                <li><b>1-BOSQICH (Qorinchalar fibrillyatsiyasi — VFIB):</b> CPR boshlangach EKG da xaotik VFIB paydo bo'ladi. Zudlik bilan Defibrillyatsiya (200 J) talab etiladi.</li>
                <li><b>2-BOSQICH (Taxikardiya/Bradikardiya):</b> Defibrillyatsiyadan so'ng ritm tiklanadi, talaba qon bosimi va Amiodaron/Atropin yuboradi.</li>
                <li><b>3-BOSQICH (Sinus Ritmi — 75 BPM):</b> Bemor to'liq jonlanadi, sun'iy nafas barqarorlashadi va tizim talabani g'alaba bilan tabriklaydi.</li>
            </ol>
        </div>
    </div>

    <!-- 6. Iqtisodiy Asosnoma va Import O'rnini Bosish -->
    <div class="section">
        <div class="section-title">6. Iqtisodiy Asosnoma va Bozor Salohiyati</div>
        <table>
            <thead>
                <tr>
                    <th>Ko'rsatkich</th>
                    <th>Xorijiy Simulyator (Import)</th>
                    <th>MedLife Milliy Simulyatori</th>
                    <th>Iqtisodiy Tejamkorlik</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>1 dona majmua narxi</td>
                    <td>1 200 000 000 so'm</td>
                    <td>400 000 000 so'm</td>
                    <td style="font-weight: 700; color: #15803d;">800 000 000 so'm tejaladi</td>
                </tr>
                <tr>
                    <td>Dasturiy ta'minot tili</td>
                    <td>Faqat Ingliz / Rus</td>
                    <td>To'liq O'zbek tili</td>
                    <td>Ona tilida milliy ta'lim</td>
                </tr>
                <tr>
                    <td>Xizmat ko'rsatish / Ehtiyot qismlar</td>
                    <td>Qimmat va uzoq vaqt talab etadi</td>
                    <td>Mahalliy tezkor servis</td>
                    <td>90% arzonroq texnik xizmat</td>
                </tr>
            </tbody>
        </table>
        <p>
            <b>Bozor sig'imi:</b> O'zbekistondagi 14 ta tibbiyot oliygohi, 70 dan ortiq Abu Ali ibn Sino nomidagi Jamoat salomatligi texnikumlari va shoshilinch tibbiy yordam o'quv markazlari.
        </p>
    </div>

    <!-- Footer Signatures -->
    <div class="footer-sign">
        <div>
            <b>Loyiha rahbari / Muallif:</b> ____________________<br>
            NDKTU CAIL Laboratoriyasi
        </div>
        <div style="text-align: right;">
            <b>RO'TFMXMO va UIM Navoiy filiali</b><br>
            Sana: «24» sentabr 2026-yil
        </div>
    </div>

</body>
</html>
"""

# ==============================================================================
# 2-LOYIHA: AI Sensorli Bemor Simulyatori HTML
# ==============================================================================
HTML_LOYIHA_2 = f"""<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="utf-8">
    <title>MedLife 2 - AI Sensorli Bemor Simulyatori Tavsifnomasi</title>
    <style>{COMMON_CSS}</style>
</head>
<body>

    <!-- Header / Passport -->
    <div class="doc-header">
        <div>
            <div style="font-size: 8pt; font-weight: 800; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px;">
                O'zbekiston Respublikasi Oliy Ta'lim, Fan va Innovatsiyalar Vazirligi
            </div>
            <div style="font-size: 9pt; font-weight: 700; color: #065f46;">
                «Ixtiro va Innovatsion Ishlanmalar Tanlovi» (Ixtiro.ilmiy.uz)
            </div>
        </div>
        <div class="doc-badge badge-emerald">
            Loyiha Pasporti & Tavsifnomasi
        </div>
    </div>

    <div class="main-title">
        MedLife AI: Sensorli Maniken Bilan Integratsiyalashgan O'zbek Tilli Sun'iy Intellektli Bemor Simulyatori
    </div>
    <div class="subtitle">
        Kiber-fizik sensorli maniken, o'zbek tilidagi generativ AI klinik muloqot, 19 ta kasallik profili va real-vaqt telemetriyasi
    </div>

    <!-- 1. Loyiha Pasporti Jadvali -->
    <div class="section">
        <div class="section-title emerald">1. Loyiha Pasporti (Asosiy Ko'rsatkichlar)</div>
        <table>
            <tr>
                <th style="width: 30%;">Loyiha nomi</th>
                <td style="width: 70%; font-weight: 700;">MedLife AI: Sensorli Maniken Bilan Integratsiyalashgan O'zbek Tilli Sun'iy Intellektli Bemor Simulyatori</td>
            </tr>
            <tr>
                <th>Ariza yo'nalishi va turi</th>
                <td>Ixtiro / Sun'iy intellekt va kiber-fizik tibbiy simulyatsiya majmuasi</td>
            </tr>
            <tr>
                <th>Bajaruvchi muassasa</th>
                <td>RO'TFMXMO va UIM Navoiy filiali hamda NDKTU CAIL laboratoriyasi</td>
            </tr>
            <tr>
                <th>Loyiha umumiy qiymati</th>
                <td style="color: #059669; font-weight: 800;">400 000 000 (To'rt yuz million) so'm</td>
            </tr>
            <tr>
                <th>Xorijiy analoglar narxi</th>
                <td style="color: #b91c1c; font-weight: 800;">1 000 000 000 — 1 600 000 000 so'm ($80 000 - $130 000)</td>
            </tr>
            <tr>
                <th>Iqtisodiy tejamkorlik</th>
                <td style="color: #15803d; font-weight: 800;">Har bir majmuada kamida 600 - 1 000 mln so'm (2.5 - 3 baravar arzon)</td>
            </tr>
            <tr>
                <th>Asosiy texnologiyalar</th>
                <td>Multimodal Generativ LLM, Speech-to-Text (STT), Neural TTS (O'zbek ovozi), ESP32, TTP223 sig'imli teginish datchiklari, WebSocket</td>
            </tr>
        </table>
    </div>

    <!-- 2. Muammoning Dolzarbligi -->
    <div class="section">
        <div class="section-title emerald">2. Muammoning Dolzarbligi va Tahlili</div>
        <p>
            Shifokor tayyorlashda <b>bemor bilan muloqot qilish, to'g'ri so'rov o'tkazish (anamnez yig'ish) va jismoniy tekshirish (palpatsiya)</b> orqali tashxis qo'yish eng muhim bosqichdir. Lekin an'anaviy ta'limda talabalar og'ir kasallar ustida erkin mashq qila olmaydi.
        </p>
        <div class="info-box warning">
            <b>Mavjud tizimdagi asosiy to'siqlar:</b>
            <ul style="margin: 4px 0 0 15px; padding: 0;">
                <li><b>Oddiy manikenlarning «hissiz va soqov»ligi:</b> Mavjud o'quv manikenlari gapirmaydi, savollarga javob bermaydi va talaba ularni ushlaganda hech qanday reaksiya bildirmaydi.</li>
                <li><b>Lisoniy to'siq (Ona tili yo'qligi):</b> Xorijiy AI simulyatorlari faqat ingliz yoki rus tillarida ishlaydi. O'zbekistonlik talaba esa xalqimiz bilan sof o'zbek tilida, xalqona shikoyatlarni tushunib muloqot qilishi shart.</li>
                <li><b>Xorijiy texnologiyalarning haddan tashqari qimmatligi:</b> Chet eldan keltiriladigan robot-bemorlar 1 milliard so'mdan oshadi.</li>
            </ul>
        </div>
    </div>

    <!-- 3. Innovatsion Yechim: Sensorli Fizik Maniken + AI -->
    <div class="section">
        <div class="section-title emerald">3. Loyihaning Ilmiy-Innovatsion Yechimi</div>
        <p>
            "MedLife AI Bemor" — <b>haqiqiy fizik manikenni generativ sun'iy intellekt bilan birlashtirgan gibrid platformadir</b>. Talaba manikenga jismoniy teginganda, AI buni his qiladi va ovozli muloqot qiladi:
        </p>
        <div class="grid-3">
            <div class="stat-card">
                <div class="stat-num" style="color: #059669;">19 ta</div>
                <div class="stat-label">Klinik patologiya profili</div>
            </div>
            <div class="stat-card">
                <div class="stat-num" style="color: #059669;">100%</div>
                <div class="stat-label">O'zbekcha ovoz & muloqot</div>
            </div>
            <div class="stat-card">
                <div class="stat-num" style="color: #059669;">10+ Sensor</div>
                <div class="stat-label">Palpatsiya & Teginish</div>
            </div>
        </div>
    </div>

    <div class="page-break"></div>

    <!-- 4. Texnik va Sun'iy Intellekt Arxitekturasi -->
    <div class="section">
        <div class="doc-header" style="margin-bottom: 10px;">
            <div style="font-size: 8.5pt; font-weight: 700; color: #64748b;">MedLife AI: Sensorli Bemor Simulyatori</div>
            <div class="doc-badge badge-emerald">Sun'iy Intellekt & Arxitektura</div>
        </div>

        <div class="section-title emerald">4. Texnik va Sun'iy Intellekt Arxitekturasi</div>
        <table>
            <thead>
                <tr>
                    <th style="width: 25%;">Modul</th>
                    <th style="width: 35%;">Texnologik Yechim</th>
                    <th style="width: 40%;">Funksional Imkoniyati</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><b>Fizik Sensorli Maniken</b></td>
                    <td>ESP32 + TTP223 sig'imli teginish datchiklari, bosim sensorlari</td>
                    <td>Qorin (jigar, appenditsit), ko'krak qafasi, bo'yin tomiri (puls) va inyeksiya joylaridagi jismoniy palpatsiyani aniqlaydi.</td>
                </tr>
                <tr>
                    <td><b>Klinik Neyrotarmoq (LLM)</b></td>
                    <td>Generativ AI va Klinik Prompt Muhandisligi</td>
                    <td>Bemor nomidan talaba savollariga xarakter, shikoyat, hayot tarzi va og'riq darajasiga mos ravishda real vaqtda javob beradi.</td>
                </tr>
                <tr>
                    <td><b>Nutq Tizimi (STT/TTS)</b></td>
                    <td>Whisper/Gemini STT va O'zbekcha Neural TTS</td>
                    <td>Talabaning og'zaki nutqini taniydi va bemorning javobini jonli, ravon o'zbek tilida (erkak/ayol tembri) audio qiladi.</td>
                </tr>
                <tr>
                    <td><b>Dinamik Holat Moduli</b></td>
                    <td>Real-vaqt telemetriya va dorilar javobi</td>
                    <td>Talaba to'g'ri dori berganda bemor holati yaxshilanadi, kechiktirilganda esa nafas qisib, og'irlashadi.</td>
                </tr>
            </tbody>
        </table>
    </div>

    <!-- 5. 19 ta Klinik Patologiya Profillari -->
    <div class="section">
        <div class="section-title emerald">5. 19 ta Chuqurlashtirilgan Klinik Kasalliklar Bazasi</div>
        <div class="info-box success">
            <b>Tizimga kiritilgan asosiy nozologiyalar:</b>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin-top: 6px; font-size: 8.5pt;">
                <div>1. Normal (Sog'lom ko'rik)</div>
                <div>2. O'tkir Miokard Infarkti</div>
                <div>3. Paroksizmal Taxikardiya</div>
                <div>4. Og'ir Bradikardiya (45 bpm)</div>
                <div>5. Aritmiya va Ekstrasistoliya</div>
                <div>6. Gipertonik Kriz (210/115 mmHg)</div>
                <div>7. Bronxial Astma xuruji</div>
                <div>8. O'tkir Pnevmoniya (39.3 °C)</div>
                <div>9. Bosh miya insulti (Dizartriya)</div>
                <div>10. Bosh miya chayqalishi</div>
                <div>11. O'tkir Appenditsit (Palpatsiya og'rig'i)</div>
                <div>12. O'tkir Ovqatdan Zaharlanish</div>
                <div>13. Gipoglikemiya (Qand 2.1 mmol/l)</div>
                <div>14. Anafilaktik Shok (Dori allergiyasi)</div>
                <div>15. O'tkir Gipoksiya (SpO2 74%)</div>
                <div>16. Gipovolemik Shok (65/35 mmHg)</div>
                <div>17. Opioid Koma (Bradipnoe)</div>
                <div>18. Asistoliya (Yurak to'xtashi)</div>
            </div>
        </div>
    </div>

    <!-- 6. Iqtisodiy Asosnoma va Solishtirma Tahlil -->
    <div class="section">
        <div class="section-title emerald">6. Iqtisodiy Asosnoma va Import O'rnini Bosish</div>
        <table>
            <thead>
                <tr>
                    <th>Xususiyat</th>
                    <th>Xorijiy Simulyator (AQSH / Yevropa)</th>
                    <th>MedLife AI Milliy Simulyatori</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><b>Loyiha / Mahsulot narxi</b></td>
                    <td style="color: #b91c1c; font-weight: 700;">1 000 000 000 — 1 600 000 000 so'm</td>
                    <td style="color: #059669; font-weight: 800;">400 000 000 so'm (2.5x tejamkor)</td>
                </tr>
                <tr>
                    <td><b>Muloqot tili</b></td>
                    <td>Faqat Ingliz yoki Rus tili</td>
                    <td style="font-weight: 700; color: #059669;">100% Sof O'zbek tili</td>
                </tr>
                <tr>
                    <td><b>Sensorli fizik maniken integratsiyasi</b></td>
                    <td>Alohida qimmat modullar talab etadi</td>
                    <td style="font-weight: 700; color: #059669;">To'liq o'rnatilgan sensorli integratsiya</td>
                </tr>
                <tr>
                    <td><b>Mahalliylashtirish darajasi</b></td>
                    <td>0% (To'liq xorijiy import)</td>
                    <td style="font-weight: 700; color: #059669;">100% Mahalliy ilmiy ishlanma</td>
                </tr>
            </tbody>
        </table>
        <p>
            <b>Xulosa:</b> Ishlanma O'zbekiston tibbiyot ta'limida xalqaro standartdagi interaktiv kiber-fizik simulyatsiyani yo'lga qo'yish, import xarajatlarini 60-70% ga qisqartirish va bo'lajak shifokorlarning amaliy malakasini xavfsiz shakllantirish imkonini beradi.
        </p>
    </div>

    <!-- Footer Signatures -->
    <div class="footer-sign">
        <div>
            <b>Loyiha rahbari / Muallif:</b> ____________________<br>
            NDKTU CAIL Laboratoriyasi
        </div>
        <div style="text-align: right;">
            <b>RO'TFMXMO va UIM Navoiy filiali</b><br>
            Sana: «24» sentabr 2026-yil
        </div>
    </div>

</body>
</html>
"""

# Generate HTML and PDF files
def build_pdf(html_text, html_filename, pdf_filename):
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_text)
    
    target_pdf = os.path.abspath(pdf_filename)
    src_html = os.path.abspath(html_filename)
    cmd = [
        browser_exe,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={target_pdf}",
        src_html
    ]
    subprocess.run(cmd, check=True)
    size_kb = os.path.getsize(target_pdf) / 1024
    print(f"Generated: {pdf_filename} ({size_kb:.1f} KB)")

if __name__ == "__main__":
    build_pdf(HTML_LOYIHA_1, "MedLife_1_Vital_Monitor_va_CPR.html", "MedLife_1_Vital_Monitor_va_CPR_Simulyatori_Tavsifnoma.pdf")
    build_pdf(HTML_LOYIHA_2, "MedLife_2_AI_Sensorli_Bemor.html", "MedLife_2_AI_Sensorli_Bemor_Simulyatori_Tavsifnoma.pdf")
    print("ALL 2 OFFICIAL PROJECT SPECIFICATION PDFS GENERATED SUCCESSFULLY!")
