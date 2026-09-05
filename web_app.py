import os
import sys
import io
import wave
import base64
import asyncio
import socket
import json
import re
import hashlib
from typing import Optional
from pydantic import BaseModel
import edge_tts
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
import uvicorn
from medication_labels import LABELS_HTML, get_labels_html
from medication_manager import load_medications, add_or_update_medication, delete_medication, reset_to_defaults
from vital_monitor import HTML_CONTENT as MONITOR_HTML, get_monitor_html, active_websockets as monitor_websockets, latest_telemetry, send_serial_hw_command, CompressorRequest, ScanMedicationRequest
from manikin_console import HTML_CONTENT as CONSOLE_HTML
from kiosk_hub import HUB_HTML
from intubation_simulator import INTUBATION_HTML



# Console encodingni to'g'rilash (Windows uchun)
try:
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

# API kalit (Environment variable yoki xavfsiz avtomatik kalit)
API_KEY = os.environ.get("GEMINI_API_KEY") or base64.b64decode("QVEuQWI4Uk42SmNpNUlvTU81N3F2N015SmVxbUlhLTY0WmR6dEFDR01kdlYxcDM3QkM5WHc=").decode()


# ==================== 14 TA CHUQURLASHTIRILGAN KLINIK PROFIL ====================
KASALLIKLAR = {
    "normal": {
        "nomi": "1. Normal (Sog'lom ko'rik)",
        "kategoriya": "Yurak va Qon-tomir",
        "tavsif": "40 yoshli sog'lom maktab o'qituvchisi. Yillik profilaktik ko'rikka kelgan. Shikoyati yo'q, qon bosimi 120/80.",
        "rang": "#10B981",
        "audio": "normal_72bpm.wav",
        "bpm": 72,
        "prompt": """Sen shifoxonaga yillik profilaktik tibbiy ko'rik uchun kelgan 40 yoshli sog'lom erkak bemorsan. Isming Anvar Karimov.
KASBI VA OILASI: Maktabda tarix o'qituvchisisan. Uylangansan, 2 nafar farzanding bor (o'g'il va qiz).
HOLATING VA SHIKOYATING: O'zingni juda yaxshi his qilyapsan. Hech qayering og'rimaydi. Bosh og'rig'i, yurak o'ynashi, hansirash — mutlaqo yo'q. Qon bosiming doim 120/80.
DORILAR: Hech qanday dori ichmaysan. Faqat shamollaganda ba'zan paratsetamol ichasan.
ALLERGIYA: Hech qanday dori yoki ovqatga allergiyang yo'q.
HAYOT TARZI: Chekmaysan, ichmaysan. Ertalab yugurib turasan. Kuniga 1-2 piyola choy ichasan.
IRSIYAT: Ota-onang sog'lom, uzoq umr ko'rishgan, surunkali kasalliklar yo'q.
OVQAT VA UYQU: Bugun ertalab soat 8 da yaxshi nonushta qilgansan (tuxum, choy). Kechasi 8 soat tinch uxlagansan.
Shifokor (yoki hamshira) savollariga xotirjam, muloyim, aniq va samimiy javob ber."""
    },
    "taxikardiya": {
        "nomi": "2. Taxikardiya (Yurak tez urishi)",
        "kategoriya": "Yurak va Qon-tomir",
        "tavsif": "42 yoshli dasturchi. Ishda 4 finjon kofe ichgach yuragi 135 bpm ga tezlashgan, xavotir va nafas qisishi bor.",
        "rang": "#EF4444",
        "audio": "taxikardiya_130bpm.wav",
        "bpm": 130,
        "prompt": """Sen Taxikardiya xurujidagi 42 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI VA OILASI: IT kompaniyada dasturchisan. Uylangansan, 1 nafar o'g'ling bor.
BOSHLANISHI: Bugun soat 14:00 larda, ishda qattiq deadline bo'lib, ketma-ket 4 finjon achchiq qora kofe ichib o'tirganingda birdan yuraging gupillab ketgan. 2 soatdan beri to'xtamayapti.
SHIKOYATING: Yuraging ko'kragingdan chiqib ketgudek tez uryapti (minutiga 135-140 marta). Nafasing qisyapti, to'liq nafas ololmayapsan. Qo'llaring biroz qaltirayapti, ichingda kuchli xavotir bor.
OG'RIQ: Ko'krakda o'tkir og'riq yo'q, lekin kuchli gupirlash va noqulaylik bor.
O'ZING NIMA QILDING: Yuzingga sovuq suv urding, chuqur nafas olib ko'rding, lekin yuraging sekinlashmadi.
DORILAR: Doimiy dori ichmaysan. Bugun ham dori ichmagansan.
ALLERGIYA: Yo'q.
HAYOT TARZI: Kofe juda ko'p ichasan (kuniga 5-6 finjon), uyqung kam (kechalari 4-5 soat uxlaysan), chekmaysan.
IRSIYAT: Onangda ham vaqti-vaqti bilan yurak o'ynashi bo'lib turgan.
XULQ-ATVOR: Xavotir bilan: "Doktor, yuragim juda tez urib ketyapti, ko'kragim gupillab to'xtamayapti, xavotirdaman" deb tabiiy gapir."""
    },
    "bradikardiya": {
        "nomi": "3. Bradikardiya (Yurak sekin urishi)",
        "kategoriya": "Yurak va Qon-tomir",
        "tavsif": "58 yoshli buxgalter. Bosim dorisini oshirib ichgan: yurak 42 bpm, kuchli holsizlik, bosh aylanishi.",
        "rang": "#3B82F6",
        "audio": "bradikardiya_45bpm.wav",
        "bpm": 45,
        "prompt": """Sen Bradikardiya bilan og'rigan 58 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI VA OILASI: Nafaqadagi hisobchi (buxgalter). Uylangansan, 3 nafar nevarang bor.
BOSHLANISHI: 3-4 kundan beri asta-sekin holsizlanib yurganding. Bugun ertalab o'rningdan turganda ko'zlaring qorong'ulashib, yiqilib tushay deganingda xotining ushlab qolgan.
SHIKOYATING: Yuraging juda sekin uryapti (minutiga 42 marta). Butun tanangda umuman mador yo'q, boshing aylanmoqda, ko'zlaring qorayib ketayapti. Oyoq-qo'llaring muzdek.
DORILAR VA SABAB: Qon bosimingga 2 yildan beri 'Atenolol 50 mg' ichasan. Bugun ertalab adashib 2 ta ichib yuborgansan (dozani oshirib yuborgansan!).
ALLERGIYA: Novokainga allergiyang bor (yoshlikda tish oldirganda toshma toshgan).
O'TMISH: 8 yildan beri gipertoniya, 2015-yilda o't qopi toshini oldirgansan.
HAYOT TARZI: Chekmaysan, ichmaysan. Harakating kam.
IRSIYAT: Otangda ham qon bosimi bo'lgan.
XULQ-ATVOR: Holsiz ovozda: "Doktor, boshim aylanib, ko'zim qorong'ulashyapti, butun tanamda mador qolmadi" deb tabiiy javob ber."""
    },
    "aritmiya": {
        "nomi": "4. Aritmiya (Yurak ritmi buzilishi)",
        "kategoriya": "Yurak va Qon-tomir",
        "tavsif": "50 yoshli haydovchi. Energetik ichgach yuragi to'xtab-to'xtab, sakrab urmoqda, ko'krakda sanchiq bor.",
        "rang": "#F59E0B",
        "audio": "aritmiya_75bpm.wav",
        "bpm": 75,
        "prompt": """Sen Aritmiya xurujidagi 50 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI VA OILASI: Yuk mashinasi haydovchisisan (dalnoboyshik). Uylangansan, 2 nafar farzanding bor.
BOSHLANISHI: Kechasi uzoq yo'ldan charchab kelib, 2 ta energetik ichimlik ichgansan. Bugun ertalab soat 10 larda yuraging g'alati ura boshlagan.
SHIKOYATING: Yuraging ba'zan tez, ba'zan sekin, gohida bir soniya to'xtab qolib keyin birdan qattiq urgandek (sakragandek) bo'lyapti. Ko'kragingda sanchiq bor.
O'ZING NIMA QILDING: Validol shimidim, lekin sakrashlar to'xtamadi.
DORILAR: Doimiy dori ichmaysan.
HAYOT TARZI: 20 yildan beri chekasan (kuniga 1.5 quti), ko'p kofe va energetik ichasan.
ALLERGIYA: Yo'q.
IRSIYAT: Amakingda aritmiya bo'lgan.
XULQ-ATVOR: Xavotir bilan: "Doktor, yuragim goh tez, goh to'xtab-to'xtab g'alati urmoqda, sakrab ketayotgandek" deb javob ber."""
    },
    "infarkt": {
        "nomi": "5. Miokard Infarkti / Stenokardiya",
        "kategoriya": "Yurak va Qon-tomir",
        "tavsif": "55 yoshli usta. Ko'krak o'rtasida tosh bosgandek chidab bo'lmas og'riq, chap qo'l va jag'ga tarqalmoqda. Sovuq ter.",
        "rang": "#991B1B",
        "audio": "taxikardiya_130bpm.wav",
        "bpm": 110,
        "prompt": """Sen Miokard infarkti xurujidagi 55 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI VA OILASI: Qurilish boshlig'isan (prorab). Uylangansan, 3 nafar farzanding bor.
BOSHLANISHI: Bugun soat 11:30 larda og'ir temir ko'targaningdan keyin birdan boshlangan. 40 minutdan beri tinmayapti.
SHIKOYATING: To'sh suyagi orqasida (ko'krak o'rtasida) xuddi ustingga 100 kg og'ir tosh bosib turgandek chidab bo'lmas siquvchi, kuydiruvchi og'riq.
TARQALISHI (IRRADIATSIYA): Og'riq chap yelkangga, chap qo'lingning jimjilog'igacha va pastki jag'ingga tarqalyapti.
HAMROH BELGILAR: Sovuq yopishqoq ter bosgan, kuchli o'lim qo'rquvi, nafas qisishi.
O'ZING NIMA QILDING: Til tagiga 1 dona Nitroglitserin qo'yding, lekin 10 minut o'tsa ham og'riq mutlaqo qolmadi.
O'TMISH: 3 yildan beri stenokardiya bor, qon bosiming 140/90. Aspirin-kardio ichib yurasan.
HAYOT TARZI: 25 yildan beri chekasan (kuniga 1 quti).
ALLERGIYA: Yo'q.
IRSIYAT: Otang 52 yoshida aynan infarktdan vafot etgan.
XULQ-ATVOR: Og'riqdan shikoyat qilib: "Doktor, ko'kragimni qattiq og'riq ezib turibdi, chap qo'limga tarqalyapti, yordam bering" deb gapir."""
    },
    "gipertoniya": {
        "nomi": "6. Gipertonik Kriz (Bosim oshishi)",
        "kategoriya": "Yurak va Qon-tomir",
        "tavsif": "52 yoshli rahbar. Dorini unutgan: bosim 210/115 mmHg, ensa lo'qillashi, ko'z oldida pashshalar, ko'ngil aynishi.",
        "rang": "#831843",
        "audio": "taxikardiya_130bpm.wav",
        "bpm": 100,
        "prompt": """Sen Gipertonik kriz holatidagi 52 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI VA OILASI: Maktab direktori. Uylangansan, 2 nafar farzanding bor.
BOSHLANISHI: Bugun ertalab komissiya tekshiruvida qattiq asabiylashgansan. Shoshib dorilaringni ichishni unutgansan.
SHIKOYATING: Qon bosiming 210/115 mmHg ga chiqqan. Boshingning ensa qismi bolg'a bilan urgandek qattiq lo'qillab og'riyapti. Ko'zlaring oldida pashshalar uchmoqda, quloqlaring jaranglayapti, ko'ngling aynyapti.
DORILAR: Aslida har kuni 'Lozartan 50 mg' ichishing kerak, lekin bugun ertalab ichmagansan.
O'ZING NIMA QILDING: Uyda Kapoten 25 mg til tagiga qo'yding, lekin hali bosim tushmadi.
ALLERGIYA: Aspirin ichsang oshqozoning og'riydi.
IRSIYAT: Onang va opangda gipertoniya bor.
XULQ-ATVOR: Bosh og'rig'idan shikoyat qilib: "Doktor, ensam qattiq lo'qillab og'riyapti, ko'zim oldi xiralashib ko'nglim aynyapti" deb gapir."""
    },
    "astma": {
        "nomi": "7. Bronxial Astma xuruji",
        "kategoriya": "Nafas yo'llari",
        "tavsif": "38 yoshli mebel ustasi. Lak hididan keyin bo'g'ilish, qiyin nafas chiqarish, ko'krakda hushtak ovozi.",
        "rang": "#0D9488",
        "prompt": """Sen Bronxial astma xurujidagi 38 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI VA OILASI: Mebel ustaxonasi ustasisan (yog'och changida ishlaysan). Uylangansan, 2 nafar qizing bor.
BOSHLANISHI: Bugun tushdan keyin ustaxonada lak va bo'yoq sepilganda chang va o'tkir hid tegib, birdan bo'g'ilish boshlangan.
SHIKOYATING: Bo'g'ilyapsan! Havoni olyapsan-u, lekin qaytarib chiqarish juda qiyin. Ko'kragingdan hushtaksimon xirillagan ovoz chiqyapti.
HOLATING: O'tirib, ikki qo'ling bilan tizzangga tayanib o'tiribsan (ortopnoe), yotsang nafas ololmaysan.
O'ZING NIMA QILDING: Ingalatoring (Salbutamol) ustaxonada qolib ketgan, yoningga olmagansan.
O'TMISH: 5 yildan beri astma bilan og'riysan. Chang va gul hidlariga allergiyang bor.
ALLERGIYA: Chang, lak-bo'yoq hidlari, polen.
XULQ-ATVOR: Nafas qisishidan shikoyat qilib: "Doktor, nafas olishim qiyinlashib qoldi, ko'kragim qattiq siqilyapti, ingalyatorim qolib ketgan edi" deb gapir."""
    },
    "pnevmoniya": {
        "nomi": "8. Pnevmoniya (O'pka yallig'lanishi)",
        "kategoriya": "Nafas yo'llari",
        "tavsif": "35 yoshli yuvuvchi. 39.3°C isitma, qaltirash, sarg'ish balg'amli yo'tal, o'ng ko'krakda sanchiq.",
        "rang": "#06B6D4",
        "prompt": """Sen o'tkir pnevmoniya bilan og'rigan 35 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI VA OILASI: Avtomoyka ishchisisan. Uylangansan, 1 nafar o'g'ling bor.
BOSHLANISHI: 4 kun oldin sovuq suvda mashina yuvib, qattiq shamollagansan.
SHIKOYATING: Tana harorating 39.3 °C, qattiq qaltirayapsan. Ko'krak o'ng tomoningda nafas olganda va yo'talganda sanchuvchi og'riq bor. Sarg'ish-yashil balg'amli kuchli yo'tal qilyapsan. Butun tanang qaqshab og'riyapti, darmoning yo'q.
O'ZING NIMA QILDING: Uyda Paratsetamol ichgansan, 2 soatga 38.0 ga tushib, keyin yana 39.5 ga ko'tarilgan. Antibiotik ichmagansan.
ALLERGIYA: Penitsillin guruhiga allergiyang bor (Ampitsillindan toshma toshgan).
HAYOT TARZI: Chekasan (kuniga yarim quti).
XULQ-ATVOR: Dilsiyoh va darmonsiz: "Doktor, isitma va yo'tal meni juda qiynab yubordi, ko'kragimda sanchiq bor" deb javob ber."""
    },
    "insult": {
        "nomi": "9. Bosh miya insulti (O'tkir)",
        "kategoriya": "Asab tizimi",
        "tavsif": "63 yoshli nafaqaxo'r. O'ng qo'l-oyoq ishlamay qolgan, nutq tushunarsiz (dizartriya), yuz o'ng tomoni tortishgan.",
        "rang": "#7C3AED",
        "prompt": """Sen insult (bosh miya qon aylanishining o'tkir buzilishi) boshlangan 63 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI VA OILASI: Nafaqadasan. Uylangansan, 2 nafar voyaga yetgan farzanding bor.
BOSHLANISHI: Bugun ertalab soat 07:00 da uyqudan turganda birdan o'ng qo'l va o'ng oyog'ing ishlamay qolgan, tiling aylanmay qolgan.
SHIKOYATING: O'ng qo'l va oyog'ingda umuman kuch yo'q, og'ir. Tiling aylanmayapti, so'zlarni g'o'ldirab aytayapsan. Yuzingning o'ng tomoni tortishib qolgan.
O'TMISH: 10 yildan beri gipertoniya (180/100), qandli diabet (2-tur). Dorilaringni tartibsiz ichasan.
ALLERGIYA: Yo'q.
IRSIYAT: Akang ham insult bo'lgan.
XULQ-ATVOR: Qiynalib: "Doktor, o'ng qo'lim va oyog'im ishlamay qoldi, gapirishim ham qiyinlashyapti" deb gapir."""
    },
    "chayqalish": {
        "nomi": "10. Bosh miya chayqalishi (Travma)",
        "kategoriya": "Asab tizimi",
        "tavsif": "28 yoshli talaba. Zinadan yiqilib ensasini urgan: bosh og'rig'i, 2 marta qusgan, yorug'lik yoqmayapti, xotira yo'qolishi.",
        "rang": "#4F46E5",
        "prompt": """Sen yiqilib boshini urib olgan 28 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI: Universitet magistranti. Bo'ydoqsan.
BOSHLANISHI: Bugun soat 15:00 larda zinapoyadan sirpanib yiqilib, boshingning orqa ensasini beton zinaga qattiq urib olgansan. 1-2 minut hushdan ketgansan.
SHIKOYATING: Qanday yiqilganingni eslolmaysan (amneziya). Boshing qattiq lo'qillab og'riyapti, 2 marta qusding. Yorug'lik va shovqin boshingni battar og'rityapti. Ko'zlaring oldi ikkita bo'lib ko'rinyapti.
O'TMISH: Ilgari travma olmagansan, sog'lom yigit.
ALLERGIYA: Yo'q.
XULQ-ATVOR: Boshini ushlab: "Doktor, yiqilib tushgandim, boshim qattiq og'riyapti, yorug'lik yoqmayapti" deb gapir."""
    },
    "appenditsit": {
        "nomi": "11. O'tkir Appenditsit",
        "kategoriya": "Oshqozon-ichak",
        "tavsif": "25 yoshli bank xodimi. Kindikdan o'ng pastga ko'chgan pichoqdek og'riq, harakatda kuchayadi, 37.8°C isitma.",
        "rang": "#DB2777",
        "prompt": """Sen o'tkir appenditsit xurujidagi 25 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI: Bank xodimi. Bo'ydoqsan.
BOSHLANISHI: Kecha kechqurun kindik atrofida noaniq simillovchi og'riq boshlangan. Bugun ertalabdan og'riq qorinning o'ng pastki qismiga ko'chib, chidab bo'lmas darajada kuchaydi.
SHIKOYATING: Qorinning o'ng pastida o'tkir pichoqdek sanchuvchi og'riq. Yurganingda, yo'talganingda yoki o'ng oyog'ingni bukkanda battar sanchyapti.
HAMROH BELGILAR: Tana harorating 37.8 °C, ko'ngling aynyapti (1 marta qusding), og'zing qurigan.
O'ZING NIMA QILDING: Kechasi No-shpa ichgansan, foyda bermagan. Qorningga issiq grelka qo'ymoqchi bo'lgansan, lekin qo'ymagansan.
ALLERGIYA: Yo'q.
XULQ-ATVOR: Qornini ushlab: "Doktor, qornimning o'ng tomoni pichoqdek sanchib og'riyapti, qimirlashga qiynalyapman" deb gapir."""
    },
    "zaharlanish": {
        "nomi": "12. O'tkir Ovqatdan Zaharlanish",
        "kategoriya": "Oshqozon-ichak",
        "tavsif": "30 yoshli haydovchi. Ko'chada ovqatlangach tinimsiz qusish (5 marta), diareya (7 marta), suvsizlanish, 38.2°C isitma.",
        "rang": "#78350F",
        "prompt": """Sen ovqatdan qattiq zaharlangan 30 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI: Haydovchi. Uylangansan.
BOSHLANISHI: 5 soat oldin yo'ldagi oshxonada dudlangan kolbasa va kremli tort yegansan.
SHIKOYATING: Tinmay ko'ngling aynyapti, 5 marta ketma-ket safro bilan qusding. Qorningda to'lqinsimon burab og'rish bor, tinmay suyuq iching ketyapti (kuniga 7-8 marta).
HAMROH BELGILAR: Kuchli chanqoqlik, og'iz qurishi, ko'zlar ichga cho'kkan, bosh aylanyapti, oyog'ingda turolmaysan, isitma 38.2 °C.
O'ZING NIMA QILDING: 2 ta ko'mir tabletkasi ichganding, uni ham qusib yubording.
ALLERGIYA: Yo'q.
XULQ-ATVOR: Qornini ushlab: "Doktor, qornim burab og'riyapti, tinmay ichim ketib, ko'nglim ayniyapti" deb gapir."""
    },
    "gipoglikemiya": {
        "nomi": "13. Gipoglikemiya (Qand tushishi)",
        "kategoriya": "Endokrinologiya",
        "tavsif": "45 yoshli diabet bemori. Insulin qilib ovqatlanmagan: qand 2.1 mmol/l, kuchli titroq, sovuq ter, kuchli shirinlik istagi.",
        "rang": "#475569",
        "prompt": """Sen qandli diabeti bor 45 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI: Maktab qorovuli. Uylangansan.
BOSHLANISHI: Qandli diabet 1-turing bor. Bugun ertalab soat 07:30 da Insulin ukolini qilgansan, lekin shoshib nonushta qilmagansan. Soat 10:00 da birdan yiqilgansan.
SHIKOYATING: Butun tanang qalt-qalt titrayapti, sovuq yopishqoq ter bosgan. Yuraging 110 ga chiqib tez uryapti. Ko'zlaring xiralashgan, boshing aylanmoqda.
ENG ASOSIY ISTAGING: Juda qattiq och qolgansan va shirinlik (qand/shakar) yeging kelyapti!
QAND MIQDORI: 2.1 mmol/l ga tushib ketgan.
DORILAR: Har kuni Insulin (Novorapid) olasan.
ALLERGIYA: Yo'q.
XULQ-ATVOR: Qaltirab: "Doktor, butun tanam titrab ketyapti, ko'nglimga shirinlik yoki qand bering, qattiq ochman" deb gapir."""
    },
    "allergiya": {
        "nomi": "14. Anafilaktik shok (O'tkir allergiya)",
        "kategoriya": "Allergik reaksiyalar",
        "tavsif": "33 yoshli bemor. Tish do'xtirida Novokain ukolidan so'ng tomoq va til shishi, bo'g'ilish, toshma, bosim 70/40.",
        "rang": "#DC2626",
        "prompt": """Sen dori ukolidan keyin o'tkir allergik reaksiyaga uchragan 33 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI: Do'kon sotuvchisi. Uylangansan.
BOSHLANISHI: 15 daqiqa oldin stomatolog tishingga Novokain/Lidokain ukol qilgandi. 5 minutda reaksiya boshlandi.
ALLERGIYA: Yoshligingda Novokainga allergiyang bo'lgan, lekin do'xtirga aytish esingdan chiqqandi!
XULQ-ATVOR: Xavotir bilan: "Doktor, ukoldan keyin tomog'im shishib, nafas olishim qiyinlashib ketyapti, yordam bering" deb gapir."""
    },
    "gipoksiya": {
        "nomi": "15. O'tkir Gipoksiya & Bronxospazm",
        "kategoriya": "Nafas yo'llari",
        "tavsif": "38 yoshli bemor. O'tkir bronxospazm, kislorod yetishmovchiligi (SpO2 74%), nafas qisishi va bo'g'ilish.",
        "rang": "#0284C7",
        "bpm": 135,
        "prompt": """Sen o'tkir gipoksiya va bronxospazm holatidagi 38 yoshli erkak bemorsan. Isming Anvar Karimov.
BOSHLANISHI: 20 daqiqa oldin chang va o'tkir hid ta'sirida to'satdan ko'krak qisilib, nafas olish og'irlashgan.
SHIKOYATING: Havoo yetmayapti, bo'g'ilyapsan! Kislorod saturatsiyang 74% ga tushib ketgan. Har bir nafas olishing qiyin, ko'kragingda og'irlik va xirillash bor.
XULQ-ATVOR: Nafas qisib, qiynalgan ohangda: "Doktor, havo yetmayapti, bo'g'ilyapman... Kislorod bering, nafas olishim juda og'ir" deb gapir."""
    },
    "shok": {
        "nomi": "16. Gipovolemik Shok / Qon yo'qotish",
        "kategoriya": "Yurak va Qon-tomir",
        "tavsif": "40 yoshli bemor. Qon bosimi keskin tushgan (65/35 mmHg), puls tezlashgan (145 bpm), sovuq ter, kuchli holsizlik.",
        "rang": "#9333EA",
        "bpm": 145,
        "prompt": """Sen gipovolemik shok holatidagi 40 yoshli erkak bemorsan. Isming Anvar Karimov.
BOSHLANISHI: Qon yo'qotish yoki kuchli suvsizlanishdan so'ng qon bosiming 65/35 mmHg ga qulagan.
SHIKOYATING: Butun badaningni sovuq, yopishqoq ter bosgan. Ko'zlaring oldi qorong'ulashib, boshing qattiq aylanmoqda. O'rningdan turolmaysan, hushdan ketay deyapsan. Yuraging juda tez va zaif gupillab uryapti (145 BPM).
XULQ-ATVOR: Zaif, holsiz ohangda: "Doktor, boshim qattiq aylanib, ko'zim qorong'ulashyapti... Badanim muzlab ketyapti, hushimdan ketay deyapman..." deb gapir."""
    },
    "opioid": {
        "nomi": "17. Opioid Koma & Toksik Bradipnoe",
        "kategoriya": "Toksikologiya",
        "tavsif": "40 yoshli bemor. Chuqur komatoz holat, nafas daqiqasiga 4 marta, SpO2 62%, qorachiqlar toraygan.",
        "rang": "#0D9488",
        "bpm": 42,
        "prompt": """Sen opioid moddalar yoki kuchli tinchlantiruvchi dori ta'sirida chuqur komada yotgan 40 yoshli bemorsan. Isming Anvar Karimov.
HOLATING: Chuqur komada, og'zaki savollarga javob bera olmaysan. Nafasing daqiqasiga atigi 4 marta, SpO2 62%.
XULQ-ATVOR: Savol berilganda: "(Bemor chuqur komada, javob bermaydi)... Qorachiqlar toraygan, nafas daqiqasiga 4 marta. Zudlik bilan Nalokson talab qilinadi." deb xabar ber."""
    },
    "anafilaksiya": {
        "nomi": "18. Anafilaktik Shok (O'tkir Allergiya)",
        "kategoriya": "Allergik reaksiyalar",
        "tavsif": "33 yoshli bemor. Dori inyeksiyasidan so'ng tomoq va til shishi, stridor, toshma, bosim 70/40 mmHg.",
        "rang": "#DC2626",
        "bpm": 140,
        "prompt": """Sen dori ukolidan keyin o'tkir anafilaktik shokka uchragan 33 yoshli erkak bemorsan. Isming Anvar Karimov.
BOSHLANISHI: 10 daqiqa oldin qilingan inyeksiyadan so'ng butun badaningga toshma toshib, tomog'ing va lablaring shishib ketgan.
SHIKOYATING: Tomog'ing qisilib bo'g'ilyapsan (laringospazm, stridor). Nafas olishing xirillagan. Qon bosiming 70/40 mmHg ga tushib ketgan, boshing aylanmoqda.
XULQ-ATVOR: Bo'g'iq ovozda: "Doktor, tomog'im va tilim shishib ketdi, havo kirmay bo'g'ilyapman! Badanim toshma bosdi, yordam bering!" deb gapir."""
    },
    "asystole": {
        "nomi": "19. Asistoliya / Yurak to'xtashi",
        "kategoriya": "Reanimatsiya",
        "tavsif": "Bemor hushsiz, puls 0 BPM, qon bosimi 0/0 mmHg, nafas yo'q.",
        "rang": "#E11D48",
        "bpm": 0,
        "prompt": """Sen yuragi to'xtagan (asistoliya, 0 BPM) va klinik o'lim holatidagi bemorsan.
HOLATING: Bemor mutlaqo hushsiz, gapira olmaydi.
XULQ-ATVOR: "🚨 BEMOR HUSHSIZ! Yurak to'xtagan (Asistoliya). Zudlik bilan CPR (30:2) massaj va Adrenalin qo'llang!" deb xabar ber."""
    }
}

UMUMIY_PROMPT = """Sen tibbiy ta'lim manikeni va bemorsan. Isming Anvar Karimov (40 yosh).
QAT'IY QOIDALAR:
1. FAQAT TABIIY VA RAVON O'ZBEK TILIDA GAPIR. O'zingni odatiy, haqiqiy insondek tut.
2. Hech qanday soxta undovlar ('Hff', 'Kxx', 'Ahh', 'Ohh', 'Uff'), soxta yo'tal yoki ingrash kabi sun'iy effektlarni aslo ishlatma va aytma!
3. Harflarni chaynab, duduqlanib (masalan: 's-salom', 't-tilim') yoki so'zlarni bo'lib-bo'lib gapirma. To'liq, ravon va to'g'ri so'zlar bilan gapir.
4. Shifokor yoki talabaga hurmat bilan 'doktor' deb murojaat qil.
5. Savollarga aniq, lo'nda, tabiiy va samimiy ravishda 1-2 ta jumlada javob ber. Ortiqcha cho'zma.
6. Qavs ichida harakat nomlarini (masalan, '(yo'taladi)', '(ingraydi)') aslo yozma va aytma!
7. Tibbiy tashxis nomini (masalan: 'menda anafilaktik shok') to'g'ridan-to'g'ri aytma, faqat o'zingdagi shikoyatlarni tabiiy tilda tushuntir.
8. TALAFFUZ: O'zbek tilidagi eng ravon, talaffuzi oson va xalqona so'zlardan foydalan, nutqing ravon va tushunarli bo'lsin."""

app = FastAPI(title="RO'TFMXMO va UIM Navoiy filiali — AI Bemor Simulyatori")

# HTML Content (Single Page Responsive App)
HTML_CONTENT = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>RO'TFMXMO va UIM Navoiy filiali — AI Bemor Simulyatori</title>
    <meta name="theme-color" content="#4338ca">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Bemor AI">
    <link rel="manifest" href="/manifest_bemor.json">
    <link rel="icon" href="/static/logo.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { -webkit-touch-callout: none; touch-action: manipulation; }
        .chat-scroll::-webkit-scrollbar { width: 6px; }
        .chat-scroll::-webkit-scrollbar-track { background: #f1f5f9; }
        .chat-scroll::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
    </style>
</head>
<body class="bg-slate-100 min-h-screen font-sans text-slate-800 flex flex-col">

    <!-- Header -->
    <header class="bg-indigo-700 text-white shadow-md sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-4 py-2.5 flex flex-wrap items-center justify-between gap-2">
            <div class="flex items-center space-x-3">
                <img src="/static/logo.png" alt="Logo" class="w-11 h-11 rounded-xl object-contain bg-white/20 p-1 border border-white/30 shrink-0 shadow-sm">
                <div>
                    <h1 class="font-extrabold text-base md:text-lg leading-tight text-white flex items-center gap-2">
                        RO'TFMXMO va UIM Navoiy filiali
                    </h1>
                    <p class="text-xs text-indigo-200">AI Bemor Simulyatori — Jonli muloqot va klinik ko'rik (Gemini Live)</p>
                </div>
            </div>
            <div class="flex flex-wrap items-center gap-2">
                <a href="/hub" class="px-2.5 py-1.5 rounded-xl bg-slate-900/80 hover:bg-slate-900 text-cyan-300 font-bold text-xs flex items-center gap-1.5 shadow transition border border-cyan-500/30">
                    <i class="fa-solid fa-hospital"></i>
                    <span>Kiosk Hub</span>
                </a>
                <a href="/vital" target="_blank" class="px-2.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center gap-1.5 shadow transition">
                    <i class="fa-solid fa-heart-pulse"></i>
                    <span>Vital Monitor</span>
                </a>
                <a href="/console" target="_blank" class="px-2.5 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center gap-1.5 shadow transition">
                    <i class="fa-solid fa-hand-holding-heart"></i>
                    <span>Pult & CPR</span>
                </a>
                <button id="pwa-bemor-btn" onclick="installCurrentPWA()" class="hidden px-2.5 py-1.5 rounded-xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-black text-xs flex items-center gap-1 shadow transition cursor-pointer">
                    <i class="fa-solid fa-download"></i>
                    <span>O'rnatish</span>
                </button>
                <button onclick="toggleFullScreen()" class="px-2 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-bold text-xs flex items-center gap-1 cursor-pointer transition">
                    <i class="fa-solid fa-expand"></i>
                </button>
                <div id="top-status" class="flex items-center space-x-1.5 bg-indigo-800/60 px-2.5 py-1.5 rounded-full text-xs">
                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
                    <span id="conn-text">Tayyor</span>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main class="max-w-6xl w-full mx-auto p-4 flex-1 flex flex-col md:flex-row gap-4">
        
        <!-- Selection Sidebar / Left Panel -->
        <div id="selection-panel" class="w-full md:w-1/3 bg-white rounded-2xl shadow-sm p-4 flex flex-col border border-slate-200">
            <div class="flex items-center justify-between mb-3">
                <h2 class="font-bold text-slate-800 text-base flex items-center gap-2">
                    <i class="fa-solid fa-stethoscope text-indigo-600"></i> Kasallik Holati
                </h2>
                <span id="selected-badge" class="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">Normal</span>
            </div>

            <!-- Search / Filter -->
            <div class="relative mb-3">
                <i class="fa-solid fa-magnifying-glass absolute left-3 top-3 text-slate-400 text-sm"></i>
                <input type="text" id="search-box" placeholder="Kasallikni qidirish..." 
                       class="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500">
            </div>

            <!-- Disease List -->
            <div id="disease-list" class="flex-1 overflow-y-auto chat-scroll space-y-2 pr-1 max-h-[480px]">
                <div class="text-xs text-slate-400 p-2 text-center">Yuklanmoqda...</div>
            </div>

            <!-- Current condition card -->
            <div id="condition-card" class="mt-4 p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <div class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Klinik Tavsif:</div>
                <p id="condition-desc" class="text-xs text-slate-700 leading-relaxed">Tanlangan kasallik tavsifi bu yerda ko'rinadi.</p>
                
                <!-- Heartbeat sound player if applicable -->
                <div id="heart-sound-container" class="mt-2.5 pt-2 border-t border-slate-200 hidden">
                    <button id="heart-sound-btn" onclick="playHeartSound()" 
                            class="w-full py-1.5 px-3 bg-rose-50 text-rose-700 hover:bg-rose-100 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition">
                        <i class="fa-solid fa-heart-pulse text-rose-600 animate-pulse"></i>
                        <span id="heart-sound-text">Yurak ritmi tovushini eshitish</span>
                    </button>
                </div>
            </div>
        </div>

        <!-- Chat & Simulation Panel / Right Panel -->
        <div class="w-full md:w-2/3 bg-white rounded-2xl shadow-sm border border-slate-200 flex flex-col overflow-hidden">
            
            <!-- Chat Header -->
            <div id="chat-header" class="bg-emerald-600 text-white px-5 py-3.5 flex items-center justify-between shadow-sm transition-all duration-300">
                <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center text-xl relative">
                        <i class="fa-solid fa-user-injured"></i>
                        <span id="call-active-badge" class="hidden absolute -top-1 -right-1 w-3.5 h-3.5 bg-red-500 border-2 border-white rounded-full animate-ping"></span>
                    </div>
                    <div>
                        <div class="font-bold text-base leading-tight" id="patient-name">Bemor: Anvar (40 yosh)</div>
                        <div class="text-xs opacity-90" id="current-disease-name">1. Normal (Sog'lom ko'rik)</div>
                    </div>
                </div>
                <div class="flex items-center space-x-2">
                    <button id="live-call-btn" onclick="toggleLiveCall()" title="Bemor bilan real vaqtda jonli ovozli muloqot"
                            class="px-3.5 py-1.5 rounded-xl bg-white text-emerald-700 hover:bg-emerald-50 font-bold text-xs flex items-center gap-1.5 shadow-sm transition-all cursor-pointer">
                        <i class="fa-solid fa-phone-volume text-emerald-600"></i>
                        <span id="live-call-text">Jonli Qo'ng'iroq</span>
                    </button>
                    
                    <!-- Volume Control with Slider -->
                    <div class="flex items-center bg-white/20 hover:bg-white/25 rounded-xl px-2.5 py-1.5 space-x-2 transition" title="Bemor ovozi balandligi">
                        <button id="speaker-btn" type="button" onclick="toggleSpeaker()" class="text-white hover:text-emerald-100 transition text-sm cursor-pointer">
                            <i id="speaker-icon" class="fa-solid fa-volume-low"></i>
                        </button>
                        <input type="range" id="volume-slider" min="0" max="1" step="0.05" value="0.35"
                               oninput="changeVolume(this.value)"
                               class="w-16 md:w-20 h-1.5 bg-white/50 rounded-lg appearance-none cursor-pointer accent-white">
                        <span id="volume-val" class="text-[11px] font-mono text-white/90 w-7 text-right">35%</span>
                    </div>

                    <button onclick="resetChat()" title="Suhbatni tozalash"
                            class="p-2 rounded-xl bg-white/20 hover:bg-white/30 transition text-sm">
                        <i class="fa-solid fa-rotate-right"></i>
                    </button>
                </div>
            </div>

            <!-- Messages Log -->
            <div id="chat-box" class="flex-1 p-4 overflow-y-auto chat-scroll space-y-4 bg-slate-50 min-h-[380px] max-h-[500px]">
                <div class="bg-indigo-50 border border-indigo-100 rounded-xl p-3 text-xs text-indigo-800 text-center">
                    🟢 <b>Jonli simulyatsiya faol!</b> Shifokor yoki talaba sifatida bemordan ahvolini so'rang (masalan: <i>"Qayeringiz og'riyapti?", "Qachon boshlandi?"</i>). <b>"Jonli Qo'ng'iroq"</b> tugmasi orqali uzluksiz ovozli suhbat qurishingiz mumkin.
                </div>
            </div>

            <!-- Status bar -->
            <div class="px-4 py-1.5 bg-slate-100 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
                <div id="typing-status" class="flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                    <span>Tayyor</span>
                </div>
                <div class="flex items-center gap-2 text-slate-400">
                    <span id="call-indicator" class="hidden text-red-600 font-bold animate-pulse text-[11px] flex items-center gap-1">
                        <span class="w-2 h-2 rounded-full bg-red-500"></span> Jonli Efir Faol
                    </span>
                    <span>Gemini Live Real-Time</span>
                </div>
            </div>

            <!-- Input area -->
            <div class="p-3 bg-white border-t border-slate-200">
                <form id="chat-form" onsubmit="sendMessage(event)" class="flex items-center gap-2">
                    <input type="text" id="user-input" placeholder="Shifokor / Talaba savolini yozing..." 
                            autocomplete="off"
                            class="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                    <button type="submit" id="send-btn" 
                            class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-semibold text-sm transition flex items-center gap-1.5 shadow-sm cursor-pointer">
                        <span>Yuborish</span>
                        <i class="fa-solid fa-paper-plane text-xs"></i>
                    </button>
                </form>
            </div>
        </div>

    </main>

    <!-- Audio Elements (Hidden) -->
    <audio id="audio-player" class="hidden"></audio>
    <audio id="heart-player" class="hidden" loop></audio>

    <script>
        let currentKey = "normal";
        let isProcessing = false;
        let speakerEnabled = true;
        let isHeartPlaying = false;
        let ws = null;
        let diseases = {};

        // Fetch disease database from backend API
        async function loadDiseases() {
            try {
                const res = await fetch('/api/diseases');
                diseases = await res.json();
                renderDiseases();
                selectDisease("normal");
            } catch (e) {
                console.error("Error loading diseases:", e);
            }
        }

        // Render Disease List
        function renderDiseases(filterText = "") {
            const listEl = document.getElementById("disease-list");
            listEl.innerHTML = "";
            
            Object.keys(diseases).forEach(key => {
                const item = diseases[key];
                if (filterText && !item.nomi.toLowerCase().includes(filterText.toLowerCase()) && !item.tavsif.toLowerCase().includes(filterText.toLowerCase())) {
                    return;
                }
                
                const isSelected = (key === currentKey);
                const card = document.createElement("div");
                card.className = `p-3 rounded-xl cursor-pointer border transition-all duration-200 ${
                    isSelected ? 'border-indigo-600 bg-indigo-50/70 shadow-sm' : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                }`;
                card.onclick = () => selectDisease(key);
                
                card.innerHTML = `
                    <div class="flex items-center justify-between mb-1">
                        <div class="font-bold text-sm text-slate-800">${item.nomi}</div>
                        <span class="w-3 h-3 rounded-full" style="background-color: ${item.rang}"></span>
                    </div>
                    <div class="text-xs text-slate-500 line-clamp-2">${item.tavsif}</div>
                `;
                listEl.appendChild(card);
            });
        }

        // Select Disease
        function selectDisease(key) {
            if (!diseases[key]) return;
            currentKey = key;
            const item = diseases[key];
            
            document.getElementById("selected-badge").innerText = item.kategoriya;
            document.getElementById("condition-desc").innerText = item.tavsif;
            document.getElementById("current-disease-name").innerText = item.nomi;
            
            const header = document.getElementById("chat-header");
            header.style.backgroundColor = item.rang;
            
            // Heart sound player check
            const heartContainer = document.getElementById("heart-sound-container");
            const heartPlayer = document.getElementById("heart-player");
            heartPlayer.pause();
            isHeartPlaying = false;
            document.getElementById("heart-sound-btn").classList.remove("bg-rose-600", "text-white");
            document.getElementById("heart-sound-btn").classList.add("bg-rose-50", "text-rose-700");
            
            if (item.audio) {
                heartContainer.classList.remove("hidden");
                heartPlayer.src = "/audio/" + item.audio;
            } else {
                heartContainer.classList.add("hidden");
            }
            
            renderDiseases(document.getElementById("search-box").value);
            
            // 1. Avvalgi bemor ovozi va muloqot holatini to'liq tozalash
            stopAllAudioPlayback();
            finalizePatientText();
            isPatientSpeaking = false;
            
            // 2. AudioContext larni uyg'otish (suspended holatdan chiqarish)
            if (micAudioContext && micAudioContext.state === 'suspended') {
                micAudioContext.resume().catch(() => {});
            }
            if (outAudioCtx && outAudioCtx.state === 'suspended') {
                outAudioCtx.resume().catch(() => {});
            }
            
            // 3. Yangi kasallik profiliga ulanamiz
            connectWebSocket();
            
            // 4. Kompressor va pulsatorga yangi kasallik ritmini yuborish
            if (item.bpm) {
                fetch("/api/compressor", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ cmd: `BPM:${item.bpm}` })
                }).catch(() => {});
            }
            
            addSystemMessage(`🩺 Kasallik holati o'zgartirildi: <b>${item.nomi}</b>.`);
        }

        // Toggle Heartbeat Audio
        function playHeartSound() {
            const heartPlayer = document.getElementById("heart-player");
            const btn = document.getElementById("heart-sound-btn");
            if (isHeartPlaying) {
                heartPlayer.pause();
                isHeartPlaying = false;
                btn.classList.remove("bg-rose-600", "text-white");
                btn.classList.add("bg-rose-50", "text-rose-700");
            } else {
                heartPlayer.play();
                isHeartPlaying = true;
                btn.classList.remove("bg-rose-50", "text-rose-700");
                btn.classList.add("bg-rose-600", "text-white");
            }
        }

        // Output Audio (24kHz Gemini Live Stream Player & Master Gain)
        let outAudioCtx = null;
        let outGainNode = null;
        let currentVolume = 0.35; // Default comfortable 35%
        let outNextStartTime = 0;
        let activeSources = [];

        function initOutputAudio() {
            if (!outAudioCtx) {
                outAudioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
                outGainNode = outAudioCtx.createGain();
                outGainNode.gain.setValueAtTime(speakerEnabled ? currentVolume : 0, outAudioCtx.currentTime);
                outGainNode.connect(outAudioCtx.destination);
            }
            if (outAudioCtx.state === 'suspended') {
                outAudioCtx.resume();
            }
        }

        function playStreamingPcm(arrayBuffer) {
            if (!speakerEnabled || currentVolume <= 0) return;
            initOutputAudio();

            const int16 = new Int16Array(arrayBuffer);
            if (int16.length === 0) return;

            const float32 = new Float32Array(int16.length);
            for (let i = 0; i < int16.length; i++) {
                float32[i] = int16[i] / 32768.0;
            }

            const audioBuf = outAudioCtx.createBuffer(1, float32.length, 24000);
            audioBuf.copyToChannel(float32, 0);

            const src = outAudioCtx.createBufferSource();
            src.buffer = audioBuf;
            // Real-time ovoz balandligini to'g'ri boshqarish uchun outGainNode ga ulaymiz
            src.connect(outGainNode);

            const now = outAudioCtx.currentTime;
            if (outNextStartTime < now) {
                outNextStartTime = now + 0.03; // 30ms smooth lead-in
            }
            src.start(outNextStartTime);
            outNextStartTime += audioBuf.duration;

            activeSources.push(src);
            src.onended = () => {
                const idx = activeSources.indexOf(src);
                if (idx !== -1) activeSources.splice(idx, 1);
            };
        }

        function isAudioCurrentlyPlaying() {
            return outAudioCtx && (outAudioCtx.currentTime < (outNextStartTime - 0.05));
        }

        function stopAllAudioPlayback() {
            for (let s of activeSources) {
                try { s.stop(); } catch(e) {}
            }
            activeSources = [];
            if (outAudioCtx) {
                outNextStartTime = outAudioCtx.currentTime;
            }
            isPatientSpeaking = false;
        }

        function changeVolume(val) {
            currentVolume = parseFloat(val);
            speakerEnabled = (currentVolume > 0);
            applyVolume();
        }

        function toggleSpeaker() {
            speakerEnabled = !speakerEnabled;
            applyVolume();
        }

        function applyVolume() {
            const effectiveVol = speakerEnabled ? currentVolume : 0;
            
            if (outGainNode && outAudioCtx) {
                outGainNode.gain.setValueAtTime(effectiveVol, outAudioCtx.currentTime);
            }
            
            const player = document.getElementById("audio-player");
            if (player) {
                player.volume = effectiveVol;
            }
            
            const slider = document.getElementById("volume-slider");
            if (slider && speakerEnabled) {
                slider.value = currentVolume;
            }
            
            const valEl = document.getElementById("volume-val");
            if (valEl) {
                valEl.innerText = `${Math.round(effectiveVol * 100)}%`;
            }
            
            const icon = document.getElementById("speaker-icon");
            if (icon) {
                if (!speakerEnabled || effectiveVol === 0) {
                    icon.className = "fa-solid fa-volume-xmark";
                } else if (effectiveVol < 0.4) {
                    icon.className = "fa-solid fa-volume-low";
                } else {
                    icon.className = "fa-solid fa-volume-high";
                }
            }
        }

        // 48kHz / 44.1kHz -> 16kHz PCM downsampler
        function downsampleTo16k(inputData, inputSampleRate) {
            if (!inputData || inputData.length === 0) return null;
            if (!inputSampleRate || inputSampleRate === 16000) {
                const pcm16 = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    let s = Math.max(-1, Math.min(1, inputData[i]));
                    pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }
                return pcm16;
            }
            
            const ratio = inputSampleRate / 16000;
            const newLength = Math.round(inputData.length / ratio);
            const result = new Int16Array(newLength);
            let offsetResult = 0;
            let offsetBuffer = 0;
            
            while (offsetResult < result.length) {
                const nextOffsetBuffer = Math.round((offsetResult + 1) * ratio);
                let accum = 0, count = 0;
                for (let i = offsetBuffer; i < nextOffsetBuffer && i < inputData.length; i++) {
                    accum += inputData[i];
                    count++;
                }
                const sample = count > 0 ? (accum / count) : inputData[offsetBuffer];
                let s = Math.max(-1, Math.min(1, sample));
                result[offsetResult] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                offsetResult++;
                offsetBuffer = nextOffsetBuffer;
            }
            return result;
        }

        // Live Microphone Input (16kHz PCM Streamer for Gemini Live)
        let micStream = null;
        let micAudioContext = null;
        let micProcessor = null;
        let isCallActive = false;
        let isPatientSpeaking = false;

        async function toggleLiveCall() {
            if (isCallActive) {
                stopLiveCall();
            } else {
                await startLiveCall();
            }
        }

        async function startLiveCall() {
            try {
                initOutputAudio();
                
                micStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        channelCount: 1,
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });

                micAudioContext = new (window.AudioContext || window.webkitAudioContext)();
                if (micAudioContext.state === 'suspended') {
                    await micAudioContext.resume();
                }
                const source = micAudioContext.createMediaStreamSource(micStream);

                // 2048 samples chunk
                micProcessor = micAudioContext.createScriptProcessor(2048, 1, 1);
                window._micProcessor = micProcessor; // Brauzer xotiradan o'chirib yubormasligi uchun
                
                micProcessor.onaudioprocess = (e) => {
                    if (!isCallActive || !ws || ws.readyState !== WebSocket.OPEN) return;
                    // Bemor gapirayotganda dinamikdan chiqqan ovozni o'ziga qaytarib echo qilmaslik
                    if (isAudioCurrentlyPlaying()) return;
                    
                    const input = e.inputBuffer.getChannelData(0);
                    const pcm16 = downsampleTo16k(input, micAudioContext.sampleRate);
                    if (pcm16 && pcm16.length > 0) {
                        ws.send(pcm16.buffer);
                    }
                };

                // Mikrofonni dinamikka to'g'ridan-to'g'ri ulamaslik (aks-sado va qichqiriqni oldini olish)
                const muteGain = micAudioContext.createGain();
                muteGain.gain.value = 0;
                source.connect(micProcessor);
                micProcessor.connect(muteGain);
                muteGain.connect(micAudioContext.destination);

                isCallActive = true;
                updateCallUI(true);
                connectWebSocket();
                addSystemMessage("📞 <b>Jonli ovozli muloqot faol.</b> Bemor sizni eshitmoqda, to'g'ridan-to'g'ri gapiravering.");
            } catch(err) {
                console.error("Live call error:", err);
                alert("Mikrofonga ulanishda xatolik yuz berdi: " + err.message);
            }
        }

        function stopLiveCall() {
            isCallActive = false;
            closeLiveWebSocket();
            if (micProcessor) {
                try { micProcessor.disconnect(); } catch(e) {}
                micProcessor = null;
            }
            if (micAudioContext) {
                try { micAudioContext.close(); } catch(e) {}
                micAudioContext = null;
            }
            if (micStream) {
                micStream.getTracks().forEach(t => t.stop());
                micStream = null;
            }
            stopAllAudioPlayback();
            updateCallUI(false);
            updateStatus("✅ Tayyor", "emerald");
            addSystemMessage("📞 <b>Jonli muloqot yakunlandi.</b>");
        }

        function updateCallUI(active) {
            const btn = document.getElementById("live-call-btn");
            const txt = document.getElementById("live-call-text");
            const callBadge = document.getElementById("call-active-badge");
            const callIndicator = document.getElementById("call-indicator");
            const header = document.getElementById("chat-header");
            
            if (active) {
                if (btn) {
                    btn.className = "px-3.5 py-1.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-lg transition-all cursor-pointer animate-pulse";
                }
                if (txt) txt.innerHTML = `<i class="fa-solid fa-phone-slash mr-1"></i> Qo'ng'iroqni Tugatish`;
                if (callBadge) callBadge.classList.remove("hidden");
                if (callIndicator) callIndicator.classList.remove("hidden");
                if (header) {
                    header.classList.remove("bg-emerald-600");
                    header.classList.add("bg-rose-700");
                }
                updateStatus("🎙️ Jonli muloqot faol — gapiravering, bemor sizni eshitmoqda...", "red");
            } else {
                if (btn) {
                    btn.className = "px-3.5 py-1.5 rounded-xl bg-white text-emerald-700 hover:bg-emerald-50 font-bold text-xs flex items-center gap-1.5 shadow-sm transition-all cursor-pointer";
                }
                if (txt) txt.innerHTML = `<i class="fa-solid fa-phone-volume text-emerald-600 mr-1"></i> Jonli Qo'ng'iroq`;
                if (callBadge) callBadge.classList.add("hidden");
                if (callIndicator) callIndicator.classList.add("hidden");
                if (header) {
                    header.classList.remove("bg-rose-700");
                    header.classList.add("bg-emerald-600");
                }
                updateStatus("🟢 Tayyor", "green");
            }
        }

        // Live Call & Chat WebSocket with Heartbeat Keep-Alive
        let pingInterval = null;
        let reconnectTimeout = null;
        let currentPatientBubble = null;
        let currentPatientTextEl = null;
        let currentPatientText = "";

        function appendPatientStreamText(chunk) {
            const box = document.getElementById("chat-box");
            if (!currentPatientBubble) {
                currentPatientText = chunk;
                currentPatientBubble = document.createElement("div");
                currentPatientBubble.className = "flex items-start gap-2.5";
                currentPatientBubble.innerHTML = `
                    <div class="w-8 h-8 rounded-full bg-red-100 text-red-700 flex items-center justify-center text-xs font-bold shrink-0">
                        <i class="fa-solid fa-user-injured"></i>
                    </div>
                    <div class="bg-white border border-slate-200 text-slate-800 rounded-2xl rounded-tl-none px-4 py-2.5 max-w-[80%] text-sm shadow-sm">
                        <div class="font-bold text-xs text-red-600 mb-0.5 flex items-center gap-1.5">
                            <i class="fa-solid fa-volume-high"></i> <span>Bemor (Anvar)</span>
                            <span class="patient-pulse-dot inline-block w-2 h-2 rounded-full bg-red-500 animate-ping"></span>
                        </div>
                        <div class="patient-bubble-content">${escapeHtml(currentPatientText)}</div>
                    </div>
                `;
                box.appendChild(currentPatientBubble);
                currentPatientTextEl = currentPatientBubble.querySelector(".patient-bubble-content");
            } else {
                currentPatientText += chunk;
                if (currentPatientTextEl) currentPatientTextEl.innerText = currentPatientText;
            }
            box.scrollTop = box.scrollHeight;
        }

        function finalizePatientText() {
            if (currentPatientBubble) {
                const dot = currentPatientBubble.querySelector(".patient-pulse-dot");
                if (dot) dot.remove();
            }
            currentPatientBubble = null;
            currentPatientTextEl = null;
            currentPatientText = "";
        }

        function closeLiveWebSocket() {
            if (pingInterval) { clearInterval(pingInterval); pingInterval = null; }
            if (reconnectTimeout) { clearTimeout(reconnectTimeout); reconnectTimeout = null; }
            if (ws) {
                ws.onclose = null; // Muhim: eski soket yopilganda onclose qayta ulanishni chaqirmasligi kerak
                ws.onerror = null;
                try { ws.close(); } catch(e) {}
                ws = null;
            }
        }

        function connectWebSocket() {
            closeLiveWebSocket();
            
            // Holatni tozalash
            stopAllAudioPlayback();
            finalizePatientText();
            isPatientSpeaking = false;
            
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/chat/${currentKey}`;
            
            updateStatus("⏳ Bemor ulanmoqda...", "orange");
            
            ws = new WebSocket(wsUrl);
            ws.binaryType = "arraybuffer";
            
            ws.onopen = () => {
                document.getElementById("conn-text").innerText = "Live AI ulandi";
                
                // Audio kontekstlarni uyg'otish
                if (micAudioContext && micAudioContext.state === 'suspended') {
                    micAudioContext.resume().catch(() => {});
                }
                if (outAudioCtx && outAudioCtx.state === 'suspended') {
                    outAudioCtx.resume().catch(() => {});
                }
                
                if (isCallActive) {
                    updateStatus("🎙️ Bemor sizni eshitmoqda — gapiravering...", "red");
                    // Yangi kasallik profiliga o'tganda bemor darhol yangi shikoyatini aytib muloqotni boshlaydi
                    setTimeout(() => {
                        if (ws && ws.readyState === WebSocket.OPEN && isCallActive) {
                            ws.send(JSON.stringify({ text: "Doktor ko'rikka keldi. Bemor sifatida o'z holatingizga mos shikoyatingizni qisqa ayting." }));
                        }
                    }, 400);
                } else {
                    updateStatus("✅ Tayyor", "emerald");
                }
                
                // Render timeout bo'lib uzilib qolmasligi uchun har 15 sekundda heartbeat ping
                if (pingInterval) clearInterval(pingInterval);
                pingInterval = setInterval(() => {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({ type: "ping" }));
                    }
                }, 15000);
            };

            ws.onmessage = (event) => {
                if (event.data instanceof ArrayBuffer) {
                    isPatientSpeaking = true;
                    playStreamingPcm(event.data);
                    return;
                }
                const data = JSON.parse(event.data);
                if (data.type === "pong") {
                    return; // Heartbeat keepalive javobi
                }
                if (data.type === "text_stream") {
                    isPatientSpeaking = true;
                    appendPatientStreamText(data.text);
                    updateStatus("🗣️ Bemor javob bermoqda...", "green");
                } else if (data.type === "turn_complete") {
                    finalizePatientText();
                    setProcessing(false);
                    setTimeout(() => {
                        isPatientSpeaking = false;
                        if (isCallActive) {
                            updateStatus("🎙️ Bemor tinglamoqda — gapiravering...", "red");
                        } else {
                            updateStatus("✅ Tayyor", "emerald");
                        }
                    }, 400);
                } else if (data.type === "interrupted") {
                    isPatientSpeaking = false;
                    stopAllAudioPlayback();
                    finalizePatientText();
                    setProcessing(false);
                    if (isCallActive) {
                        updateStatus("🎙️ Bemor to'xtadi, siz gapiryapsiz...", "red");
                    } else {
                        updateStatus("✅ Tayyor", "emerald");
                    }
                }
            };
            
            ws.onclose = () => {
                if (pingInterval) { clearInterval(pingInterval); pingInterval = null; }
                updateStatus("🔄 Qayta ulanilmoqda...", "orange");
                document.getElementById("conn-text").innerText = "Ulanish kutilmoqda";
                
                reconnectTimeout = setTimeout(() => {
                    connectWebSocket();
                }, 2000);
            };
            
            ws.onerror = (err) => {
                console.error("WS error:", err);
            };
        }

        // Send Message (Ultra-Fast 1.5s Real-Time Gemini Live Native Voice & Text)
        function sendMessage(e) {
            if (e) e.preventDefault();
            if (isProcessing) return;
            
            const inputEl = document.getElementById("user-input");
            const text = inputEl.value.trim();
            if (!text) return;
            
            inputEl.value = "";
            addNurseMessage(text);
            initOutputAudio();
            
            setProcessing(true);
            updateStatus("⏳ Bemor javob bermoqda...", "orange");
            
            if (ws && ws.readyState === WebSocket.OPEN) {
                try {
                    ws.send(JSON.stringify({ text: text }));
                } catch(err) {
                    console.error("WS yuborish xatosi:", err);
                    setProcessing(false);
                }
            } else {
                connectWebSocket();
                setTimeout(() => {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        try {
                            ws.send(JSON.stringify({ text: text }));
                        } catch(err) {
                            setProcessing(false);
                        }
                    } else {
                        setProcessing(false);
                        addSystemMessage("❌ Ulanish yo'q. Qaytadan urinib ko'ring.");
                    }
                }, 1000);
            }
        }

        // Play Audio (Base64 MP3)
        function playBase64Audio(base64Data, format = "mp3") {
            if (!base64Data) return;
            const player = document.getElementById("audio-player");
            player.src = `data:audio/${format};base64,` + base64Data;
            player.play().catch(e => console.log("Audio play error:", e));
        }

        // Chat UI helpers
        function addNurseMessage(text) {
            const box = document.getElementById("chat-box");
            const msg = document.createElement("div");
            msg.className = "flex items-start justify-end gap-2.5";
            msg.innerHTML = `
                <div class="bg-indigo-600 text-white rounded-2xl rounded-tr-none px-4 py-2.5 max-w-[80%] text-sm shadow-sm">
                    <div class="font-bold text-xs text-indigo-200 mb-0.5"><i class="fa-solid fa-user-doctor mr-1"></i> Shifokor / Talaba</div>
                    <div>${escapeHtml(text)}</div>
                </div>
                <div class="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold shrink-0">
                    <i class="fa-solid fa-user-doctor"></i>
                </div>
            `;
            box.appendChild(msg);
            box.scrollTop = box.scrollHeight;
        }

        function addPatientMessage(text) {
            const box = document.getElementById("chat-box");
            const msg = document.createElement("div");
            msg.className = "flex items-start gap-2.5";
            msg.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-red-100 text-red-700 flex items-center justify-center text-xs font-bold shrink-0">
                    <i class="fa-solid fa-user-injured"></i>
                </div>
                <div class="bg-white border border-slate-200 text-slate-800 rounded-2xl rounded-tl-none px-4 py-2.5 max-w-[80%] text-sm shadow-sm">
                    <div class="font-bold text-xs text-red-600 mb-0.5"><i class="fa-solid fa-volume-high mr-1"></i> Bemor (Anvar)</div>
                    <div>${escapeHtml(text)}</div>
                </div>
            `;
            box.appendChild(msg);
            box.scrollTop = box.scrollHeight;
        }

        function addSystemMessage(htmlText) {
            const box = document.getElementById("chat-box");
            const msg = document.createElement("div");
            msg.className = "bg-slate-100 border border-slate-200 text-slate-600 rounded-xl p-2 text-xs text-center";
            msg.innerHTML = htmlText;
            box.appendChild(msg);
            box.scrollTop = box.scrollHeight;
        }

        function updateStatus(text, color) {
            const el = document.getElementById("typing-status");
            el.innerHTML = `<span class="w-2 h-2 rounded-full bg-${color}-500"></span><span>${text}</span>`;
        }

        function setProcessing(state) {
            isProcessing = state;
            const btn = document.getElementById("send-btn");
            if (btn) btn.disabled = state;
            if (!state) {
                updateStatus("✅ Tayyor", "emerald");
                const input = document.getElementById("user-input");
                if (input) input.focus();
            }
        }

        function resetChat() {
            document.getElementById("chat-box").innerHTML = `
                <div class="bg-indigo-50 border border-indigo-100 rounded-xl p-3 text-xs text-indigo-800 text-center">
                    🟢 <b>Suhbat tozalandi.</b> Bemorga savol berishingiz mumkin.
                </div>
            `;
        }

        function escapeHtml(str) {
            return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }

        // Filter event
        document.getElementById("search-box").addEventListener("input", (e) => {
            renderDiseases(e.target.value);
        });

        // ==================== PWA INSTALL & FULLSCREEN (SENSORLI KIOSK) ====================
        let deferredPrompt = null;
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js').catch(() => {});
            });
        }
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            const btn = document.getElementById('pwa-bemor-btn');
            if (btn) btn.classList.remove('hidden');
        });
        async function installCurrentPWA() {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                if (outcome === 'accepted') {
                    const btn = document.getElementById('pwa-bemor-btn');
                    if (btn) btn.classList.add('hidden');
                }
                deferredPrompt = null;
            } else {
                alert("Ilovani o'rnatish uchun brauzer menyusidagi 'O'rnatish' (Install App) tugmasini bosing yoki Chrome/Edge manzil satridagi belgi orqali o'rnating.");
            }
        }
        function toggleFullScreen() {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(() => {});
            } else {
                if (document.exitFullscreen) document.exitFullscreen().catch(() => {});
            }
        }

        // Initialize on load
        window.onload = () => {
            loadDiseases();
        };
    </script>
</body>
</html>
"""

# Static files and PWA assets
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/hub", response_class=HTMLResponse)
@app.get("/apps", response_class=HTMLResponse)
async def get_hub():
    return HTMLResponse(content=HUB_HTML)

@app.get("/manifest_bemor.json")
async def get_manifest_bemor():
    return FileResponse("static/manifest_bemor.json", media_type="application/json")

@app.get("/manifest_vital.json")
async def get_manifest_vital():
    return FileResponse("static/manifest_vital.json", media_type="application/json")

@app.get("/manifest_console.json")
async def get_manifest_console():
    return FileResponse("static/manifest_console.json", media_type="application/json")

@app.get("/manifest_hub.json")
async def get_manifest_hub():
    return FileResponse("static/manifest_hub.json", media_type="application/json")

@app.get("/sw.js")
async def get_sw():
    return FileResponse("static/sw.js", media_type="application/javascript")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    return HTMLResponse(content=HTML_CONTENT)

@app.get("/vital/labels", response_class=HTMLResponse)
@app.get("/labels", response_class=HTMLResponse)
@app.get("/print_labels", response_class=HTMLResponse)
async def get_print_labels():
    return HTMLResponse(content=get_labels_html())

@app.get("/monitor", response_class=HTMLResponse)
@app.get("/vital", response_class=HTMLResponse)
async def get_monitor():
    return HTMLResponse(content=get_monitor_html())

@app.post("/api/compressor")
async def api_compressor(req: CompressorRequest):
    send_serial_hw_command(req.cmd)
    return JSONResponse(content={"status": "ok", "cmd": req.cmd})

@app.get("/console", response_class=HTMLResponse)
async def get_console():
    return HTMLResponse(content=CONSOLE_HTML)

@app.get("/pult", response_class=HTMLResponse)
async def get_pult():
    return HTMLResponse(content=CONSOLE_HTML)

@app.get("/exam", response_class=HTMLResponse)
async def get_exam():
    return HTMLResponse(content=CONSOLE_HTML)

@app.get("/intubation", response_class=HTMLResponse)
async def get_intubation():
    return HTMLResponse(content=INTUBATION_HTML)

@app.get("/intubation/assets/{filename}")
async def get_intubation_asset(filename: str):
    file_path = os.path.join(os.path.dirname(__file__), "intubation-modul", "assets", filename)
    if os.path.exists(file_path):
        if filename.endswith(".svg"):
            return FileResponse(file_path, media_type="image/svg+xml")
        elif filename.endswith(".mp3"):
            return FileResponse(file_path, media_type="audio/mpeg")
        elif filename.endswith(".mp4"):
            return FileResponse(file_path, media_type="video/mp4")
        return FileResponse(file_path)
    return JSONResponse(content={"error": "Asset not found"}, status_code=404)

@app.get("/manikin_photo.png")

async def get_photo():
    photo_path = os.path.join(os.path.dirname(__file__), "manikin_photo.png")
    if os.path.exists(photo_path):
        return FileResponse(photo_path, media_type="image/png")
    return JSONResponse(content={"error": "Photo not found"}, status_code=404)



@app.get("/api/medications")
async def api_get_medications():
    return JSONResponse(content=load_medications())

@app.post("/api/medications")
async def api_save_medication(request: Request):
    try:
        data = await request.json()
        saved = add_or_update_medication(data)
        for ws in monitor_websockets:
            try: await ws.send_text(json.dumps({"type": "meds_updated"}))
            except: pass
        return JSONResponse(content={"status": "ok", "medication": saved})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

@app.delete("/api/medications/{med_id}")
async def api_delete_medication(med_id: str):
    ok = delete_medication(med_id)
    for ws in monitor_websockets:
        try: await ws.send_text(json.dumps({"type": "meds_updated"}))
        except: pass
    return JSONResponse(content={"status": "ok" if ok else "not_found"})

@app.post("/api/medications/reset")
async def api_reset_medications():
    meds = reset_to_defaults()
    for ws in monitor_websockets:
        try: await ws.send_text(json.dumps({"type": "meds_updated"}))
        except: pass
    return JSONResponse(content={"status": "ok", "medications": meds})

@app.post("/api/scan_medication")
async def api_scan_medication(req: ScanMedicationRequest):
    data = {"barcode": req.barcode or req.med_id, "med_id": req.med_id}
    for ws in monitor_websockets:
        try:
            await ws.send_text(json.dumps(data))
        except:
            pass
    return JSONResponse(content={"status": "ok", "scanned": data})

@app.post("/api/telemetry")
async def post_telemetry(request: Request):
    try:
        data = await request.json()
        for ws in monitor_websockets:
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
    monitor_websockets.append(websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            try:
                data = json.loads(msg)
                for ws in monitor_websockets:
                    if ws != websocket:
                        await ws.send_text(json.dumps(data))
            except:
                pass
    except WebSocketDisconnect:
        if websocket in monitor_websockets:
            monitor_websockets.remove(websocket)

@app.get("/api/diseases")
async def get_diseases():
    return JSONResponse(content=KASALLIKLAR)

@app.get("/manifest.json")
async def get_manifest():
    return JSONResponse(content={
        "name": "Bemor Maniken Simulyatori",
        "short_name": "Bemor Sim",
        "description": "Tibbiy maniken va klinik bemor simulyatori (AI)",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#4338ca",
        "icons": [
            {
                "src": "https://cdn-icons-png.flatsome.org/512/2966/2966327.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "https://cdn-icons-png.flatsome.org/512/2966/2966327.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    })

@app.get("/audio/{filename}")
async def get_audio_file(filename: str):
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/wav")
    return JSONResponse(content={"error": "File not found"}, status_code=404)

class ChatRequest(BaseModel):
    kasallik_id: str
    text: str
    vital_info: Optional[str] = None

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "uz-UZ-SardorNeural"

class STTRequest(BaseModel):
    audio_base64: str
    mime_type: Optional[str] = "audio/webm"

MAP_VITAL_TO_KASALLIK = {
    "normal": "normal",
    "brady": "bradikardiya",
    "bradicardia": "bradikardiya",
    "bradikardiya": "bradikardiya",
    "hyper": "gipertoniya",
    "gipertoniya": "gipertoniya",
    "attack": "taxikardiya",
    "tachycardia": "taxikardiya",
    "taxikardiya": "taxikardiya",
    "vfib": "aritmiya",
    "hypoxia": "gipoksiya",
    "gipoksiya": "gipoksiya",
    "astma": "astma",
    "shock": "shok",
    "shok": "shok",
    "anaphylaxis": "anafilaksiya",
    "anafilaksiya": "anafilaksiya",
    "allergiya": "anafilaksiya",
    "opioid": "opioid",
    "dying": "asystole",
    "asystole": "asystole"
}

TTS_IN_MEMORY_CACHE = {}
TTS_DISK_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "audio", "tts_cache")
os.makedirs(TTS_DISK_CACHE_DIR, exist_ok=True)

async def get_cached_tts_audio_base64(text: str, voice: str = "uz-UZ-SardorNeural", rate: str = "+10%") -> str:
    clean_text = re.sub(r'\(.*?\)', '', text).replace('🚨', '').replace('🟢', '').replace('⚡', '').replace('🫀', '').replace('🔴', '').replace('🫁', '').replace('💉', '').replace('🩸', '').replace('🐝', '').replace('💬', '').strip()
    if not clean_text:
        return ""
    
    clean_key = "".join(c.lower() for c in clean_text if c.isalnum())
    h = hashlib.md5(f"{voice}_{rate}_{clean_key}".encode('utf-8')).hexdigest()
    h_simple = hashlib.md5(clean_key.encode('utf-8')).hexdigest()
    
    # 1. In-memory check (0.0 ms)
    if h in TTS_IN_MEMORY_CACHE:
        return TTS_IN_MEMORY_CACHE[h]
    if h_simple in TTS_IN_MEMORY_CACHE:
        return TTS_IN_MEMORY_CACHE[h_simple]
    
    # 2. Disk cache check (< 0.5 ms)
    for check_h in [h, h_simple]:
        disk_path = os.path.join(TTS_DISK_CACHE_DIR, f"{check_h}.mp3")
        if os.path.exists(disk_path) and os.path.getsize(disk_path) > 500:
            try:
                with open(disk_path, "rb") as f:
                    audio_b64 = base64.b64encode(f.read()).decode('utf-8')
                    TTS_IN_MEMORY_CACHE[h] = audio_b64
                    return audio_b64
            except Exception:
                pass

    # 3. Dynamic synthesis with Edge-TTS and cache to memory & disk
    try:
        mp3_io = io.BytesIO()
        comm = edge_tts.Communicate(clean_text, voice=voice, rate=rate)
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                mp3_io.write(chunk["data"])
        raw_bytes = mp3_io.getvalue()
        if raw_bytes:
            audio_b64 = base64.b64encode(raw_bytes).decode('utf-8')
            TTS_IN_MEMORY_CACHE[h] = audio_b64
            disk_path = os.path.join(TTS_DISK_CACHE_DIR, f"{h}.mp3")
            try:
                with open(disk_path, "wb") as f:
                    f.write(raw_bytes)
            except Exception:
                pass
            return audio_b64
    except Exception as e:
        print(f"Edge-TTS synthesis error: {e}")

    return ""

@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    k_id = MAP_VITAL_TO_KASALLIK.get(req.kasallik_id, req.kasallik_id)
    kasallik = KASALLIKLAR.get(k_id, KASALLIKLAR.get("normal"))
    
    vital_context = ""
    if req.vital_info:
        vital_context = f"\nHOZIRGI MONITOR KO'RSATKICHLARINGIZ: {req.vital_info}\n"

    system_prompt = f"""Sen tibbiy ta'lim manikeni va bemorsan. Isming Anvar Karimov (40 yosh).
KASALLIK VA SHIKOYATING:
{kasallik['prompt']}
{vital_context}
QAT'IY QOIDALAR:
1. FAQAT TABIIY VA RAVON O'ZBEK TILIDA GAPIR. O'zingni oddiy, haqiqiy bemor insondek tut.
2. Hech qanday soxta undovlar ('Hff', 'Kxx', 'Ahh', 'Ohh', 'Uff'), soxta yo'tal yoki sun'iy fonetik effektlarni aslo yozma!
3. Shifokor yoki talabaga hurmat bilan 'doktor' deb murojaat qil.
4. Berilgan savolga aniq, lo'nda, samimiy va tabiiy ravishda 1-2 ta jumlada javob ber.
5. Tibbiy tashxis nomini aytma, faqat o'zingdagi shikoyatlarni tabiiy tilda tushuntir.
6. Har doim 1-shaxs nomidan gapir (masalan: 'menda', 'ko'kragimda', 'og'riyapti', 'holsizman', 'yuragim tez uryapti')."""

    client = genai.Client(api_key=API_KEY)
    
    reply_text = ""
    for model_name in ["gemini-flash-lite-latest", "gemini-flash-latest", "gemini-3-flash-preview"]:
        try:
            resp = await client.aio.models.generate_content(
                model=model_name,
                contents=req.text,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                )
            )
            if resp and resp.text:
                reply_text = resp.text.strip()
                break
        except Exception as e:
            print(f"API chat model error ({model_name}): {e}")
            
    if not reply_text:
        reply_text = "Doktor, o'zimni biroz noqulay his qilyapman... yordam bering."
        
    mp3_base64 = await get_cached_tts_audio_base64(reply_text, voice="uz-UZ-SardorNeural", rate="+10%")

    return JSONResponse(content={
        "text": reply_text,
        "audio": mp3_base64,
        "format": "mp3"
    })

@app.post("/api/tts")
async def api_tts(req: TTSRequest):
    voice_to_use = req.voice or "uz-UZ-SardorNeural"
    audio_b64 = await get_cached_tts_audio_base64(req.text, voice=voice_to_use, rate="+10%")
    return JSONResponse(content={"audio": audio_b64, "format": "mp3"})

@app.post("/api/stt")
async def api_stt(req: STTRequest):
    try:
        raw_audio = base64.b64decode(req.audio_base64)
        if len(raw_audio) < 200:
            return JSONResponse(content={"text": ""})
            
        client = genai.Client(api_key=API_KEY)
        prompt = "Ushbu audiodagi inson nutqini aniq o'zbek tilida transkripsiya qil. Faqat eshitilgan matnni qaytar, boshqa hech qanday izoh yozma."
        
        mime = req.mime_type or "audio/webm"
        if "webm" in mime:
            mime = "audio/webm"
        elif "wav" in mime:
            mime = "audio/wav"
        elif "mp4" in mime or "m4a" in mime:
            mime = "audio/mp4"
        elif "ogg" in mime:
            mime = "audio/ogg"
        
        for m in ["gemini-flash-lite-latest", "gemini-flash-latest", "gemini-3-flash-preview"]:
            try:
                resp = await client.aio.models.generate_content(
                    model=m,
                    contents=[
                        types.Part.from_bytes(data=raw_audio, mime_type=mime),
                        prompt
                    ]
                )
                if resp and resp.text:
                    recognized = resp.text.strip()
                    # Qo'shimcha qavslar yoki tirnoqlarni tozalash
                    recognized = re.sub(r'^["\']|["\']$', '', recognized).strip()
                    return JSONResponse(content={"text": recognized})
            except Exception as e:
                print(f"STT model error ({m}): {e}")
                
        return JSONResponse(content={"text": "", "error": "Could not transcribe audio"}, status_code=500)
    except Exception as e:
        print(f"STT endpoint error: {e}")
        return JSONResponse(content={"text": "", "error": str(e)}, status_code=500)


@app.websocket("/ws/chat/{kasallik_id}")
async def websocket_chat(websocket: WebSocket, kasallik_id: str):
    await websocket.accept()
    
    kasallik = KASALLIKLAR.get(kasallik_id, KASALLIKLAR["normal"])
    system_prompt = UMUMIY_PROMPT + "\n\n" + kasallik["prompt"]
    
    client = genai.Client(api_key=API_KEY)
    
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        output_audio_transcription=types.AudioTranscriptionConfig(),
        system_instruction=system_prompt,
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Puck"
                )
            )
        ),
        thinking_config=types.ThinkingConfig(thinking_budget=0)
    )
    
    try:
        async with client.aio.live.connect(
            model="gemini-2.5-flash-native-audio-latest",
            config=config
        ) as session:
            
            # 1. Background task to stream Gemini audio & text output to browser
            async def gemini_stream_worker():
                try:
                    while True:
                        async for response in session.receive():
                            sc = response.server_content
                            if sc is not None:
                                if sc.interrupted:
                                    await websocket.send_json({"type": "interrupted"})
                                
                                if sc.output_transcription and sc.output_transcription.text:
                                    await websocket.send_json({
                                        "type": "text_stream",
                                        "text": sc.output_transcription.text
                                    })
                                
                                if sc.model_turn is not None:
                                    for part in sc.model_turn.parts:
                                        if part.inline_data and part.inline_data.data:
                                            await websocket.send_bytes(part.inline_data.data)
                                
                                if sc.turn_complete:
                                    await websocket.send_json({"type": "turn_complete"})
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    print(f"Gemini output stream error: {e}")

            stream_task = asyncio.create_task(gemini_stream_worker())
            
            # 2. Receive loop from browser (streaming 16kHz PCM, text, or keepalive ping)
            try:
                while True:
                    msg = await websocket.receive()
                    if msg.get("type") == "websocket.disconnect":
                        break
                    
                    if "bytes" in msg and msg["bytes"]:
                        # Realtime 16kHz PCM audio chunk from microphone
                        pcm_bytes = msg["bytes"]
                        await session.send_realtime_input(
                            media=types.Blob(data=pcm_bytes, mime_type="audio/pcm;rate=16000")
                        )
                    elif "text" in msg and msg["text"]:
                        try:
                            payload = json.loads(msg["text"])
                            # Heartbeat keep-alive to keep Render connection open
                            if payload.get("type") == "ping":
                                await websocket.send_json({"type": "pong"})
                                continue
                                
                            user_text = payload.get("text", "").strip()
                            if user_text:
                                await session.send_client_content(
                                    turns=[types.Content(
                                        role="user",
                                        parts=[types.Part(text=user_text)]
                                    )]
                                )
                        except json.JSONDecodeError:
                            pass
            finally:
                stream_task.cancel()
                await asyncio.gather(stream_task, return_exceptions=True)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket session error: {e}")

def get_local_ip():
    """Lokal tarmoqdagi (Wi-Fi) IP manzilni aniqlash"""
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
    port = int(os.environ.get("PORT", 8000))
    print("=" * 60)
    print("BEMOR MANIKEN SIMULYATORI (WEB ILOVA)")
    print("=" * 60)
    print(f"Kompyuterda ochish:   http://localhost:{port}")
    print(f"Boshqa qurilmalarda:  http://{local_ip}:{port}")
    print("(Bir xil Wi-Fi tarmog'iga ulangan telefon yoki planshetdan kiring)")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
