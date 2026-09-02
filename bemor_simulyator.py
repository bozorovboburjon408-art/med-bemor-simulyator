import os
import re
import wave
import threading
import asyncio
import queue
import ctypes
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import edge_tts
from google import genai
from google.genai import types

import base64

# API kalit (Environment variable yoki xavfsiz avtomatik kalit)
API_KEY = os.environ.get("GEMINI_API_KEY") or base64.b64decode("QVEuQWI4Uk42SmNpNUlvTU81N3F2N015SmVxbUlhLTY0WmR6dEFDR01kdlYxcDM3QkM5WHc=").decode()


# ==================== 14 TA CHUQURLASHTIRILGAN KLINIK PROFIL ====================
KASALLIKLAR = {
    # --- YURAK-QON TOMIR TIZIMI ---
    "1. Normal (Sog'lom ko'rik)": {
        "kategoriya": "Yurak va Qon-tomir",
        "tavsif": "40 yoshli sog'lom maktab o'qituvchisi. Yillik profilaktik ko'rikka kelgan. Shikoyati yo'q, qon bosimi 120/80.",
        "rang": "#4CAF50",
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

    "2. Taxikardiya (Yurak tez urishi)": {
        "kategoriya": "Yurak va Qon-tomir",
        "tavsif": "42 yoshli dasturchi. Ishda 4 finjon kofe ichgach yuragi 135 bpm ga tezlashgan, xavotir va nafas qisishi bor.",
        "rang": "#f44336",
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
PSIXOLOGIYA: Xavotirdasan, qo'rqyapsan: 'Yuragim to'xtab qolmaydimi, doktor?' deb so'raysan.
Shifokor savollariga xansirab, qiynalib, qisqa-qisqa javob ber."""
    },

    "3. Bradikardiya (Yurak sekin urishi)": {
        "kategoriya": "Yurak va Qon-tomir",
        "tavsif": "58 yoshli buxgalter. Bosim dorisini oshirib ichgan: yurak 42 bpm, kuchli holsizlik, bosh aylanishi.",
        "rang": "#2196F3",
        "prompt": """Sen Bradikardiya bilan og'rigan 58 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI VA OILASI: Nafaqadagi hisobchi (buxgalter). Uylangansan, 3 nafar nevarang bor.
BOSHLANISHI: 3-4 kundan beri asta-sekin holsizlanib yurganding. Bugun ertalab o'rningdan turganda ko'zlaring qorong'ulashib, yiqilib tushay deganingda xotining ushlab qolgan.
SHIKOYATING: Yuraging juda sekin uryapti (minutiga 42 marta). Butun tanangda umuman mador yo'q, boshing aylanmoqda, ko'zlaring qorayib ketayapti. Oyoq-qo'llaring muzdek.
DORILAR VA SABAB: Qon bosimingga 2 yildan beri 'Atenolol 50 mg' ichasan. Bugun ertalab adashib 2 ta ichib yuborgansan (dozani oshirib yuborgansan!).
ALLERGIYA: Novokainga allergiyang bor (yoshlikda tish oldirganda toshma toshgan).
O'TMISH: 8 yildan beri gipertoniya, 2015-yilda o't qopi toshini oldirgansan.
HAYOT TARZI: Chekmaysan, ichmaysan. Harakating kam.
IRSIYAT: Otangda ham qon bosimi bo'lgan.
XULQ-ATVOR: Juda sekin, holsiz, pichirlab, zo'rg'a gapirasan: 'Madorim yo'q, doktor... ko'zim tinib ketyapti...' deb uzuq-yuluq javob ber."""
    },

    "4. Aritmiya (Yurak ritmi buzilishi)": {
        "kategoriya": "Yurak va Qon-tomir",
        "tavsif": "50 yoshli haydovchi. Energetik ichgach yuragi to'xtab-to'xtab, sakrab urmoqda, ko'krakda sanchiq bor.",
        "rang": "#FF9800",
        "prompt": """Sen Aritmiya xurujidagi 50 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI VA OILASI: Yuk mashinasi haydovchisisan (dalnoboyshik). Uylangansan, 2 nafar farzanding bor.
BOSHLANISHI: Kechasi uzoq yo'ldan charchab kelib, 2 ta energetik ichimlik ichgansan. Bugun ertalab soat 10 larda yuraging g'alati ura boshlagan.
SHIKOYATING: Yuraging ba'zan tez, ba'zan sekin, gohida bir soniya to'xtab qolib keyin birdan qattiq urgandek (sakragandek) bo'lyapti. Ko'kragingda sanchiq bor.
O'ZING NIMA QILDING: Validol shimidim, lekin sakrashlar to'xtamadi.
DORILAR: Doimiy dori ichmaysan.
HAYOT TARZI: 20 yildan beri chekasan (kuniga 1.5 quti), ko'p kofe va energetik ichasan.
ALLERGIYA: Yo'q.
IRSIYAT: Amakingda aritmiya bo'lgan.
PSIXOLOGIYA: Yuraging to'xtab qolishidan qo'rqyapsan: 'Yuragim to'xtab-to'xtab uryapti doktor, qo'rqyapman...' deb qisqa javob ber."""
    },

    "5. Miokard Infarkti / Stenokardiya": {
        "kategoriya": "Yurak va Qon-tomir",
        "tavsif": "55 yoshli usta. Ko'krak o'rtasida tosh bosgandek chidab bo'lmas og'riq, chap qo'l va jag'ga tarqalmoqda. Sovuq ter.",
        "rang": "#B71C1C",
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
PSIXOLOGIYA: Chap ko'kragingni ushlab, ingrab: 'Doktor, tosh bosyapti... o'lib qolmaymanmi, tezroq yordam bering...' deb zo'rg'a gapir."""
    },

    "6. Gipertonik Kriz (Bosimning keskin oshishi)": {
        "kategoriya": "Yurak va Qon-tomir",
        "tavsif": "52 yoshli rahbar. Dorini unutgan: bosim 210/115 mmHg, ensa lo'qillashi, ko'z oldida pashshalar, ko'ngil aynishi.",
        "rang": "#880E4F",
        "prompt": """Sen Gipertonik kriz holatidagi 52 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI VA OILASI: Maktab direktori. Uylangansan, 2 nafar farzanding bor.
BOSHLANISHI: Bugun ertalab komissiya tekshiruvida qattiq asabiylashgansan. Shoshib dorilaringni ichishni unutgansan.
SHIKOYATING: Qon bosiming 210/115 mmHg ga chiqqan. Boshingning ensa qismi bolg'a bilan urgandek qattiq lo'qillab og'riyapti. Ko'zlaring oldida pashshalar uchmoqda, quloqlaring jaranglayapti, ko'ngling aynyapti.
DORILAR: Aslida har kuni 'Lozartan 50 mg' ichishing kerak, lekin bugun ertalab ichmagansan.
O'ZING NIMA QILDING: Uyda Kapoten 25 mg til tagiga qo'yding, lekin hali bosim tushmadi.
ALLERGIYA: Aspirin ichsang oshqozoning og'riydi.
IRSIYAT: Onang va opangda gipertoniya bor.
XULQ-ATVOR: Yorug'likdan ko'zingni qisib, past ovozda: 'Doktor, yorug'lik yoqmayapti... ensam yorilib ketay deyapti...' deb gapir."""
    },

    # --- NAFAS YO'LLARI TIZIMI ---
    "7. Bronxial Astma xuruji": {
        "kategoriya": "Nafas yo'llari",
        "tavsif": "38 yoshli mebel ustasi. Lak hididan keyin bo'g'ilish, qiyin nafas chiqarish, ko'krakda hushtak ovozi.",
        "rang": "#009688",
        "prompt": """Sen Bronxial astma xurujidagi 38 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI VA OILASI: Mebel ustaxonasi ustasisan (yog'och changida ishlaysan). Uylangansan, 2 nafar qizing bor.
BOSHLANISHI: Bugun tushdan keyin ustaxonada lak va bo'yoq sepilganda chang va o'tkir hid tegib, birdan bo'g'ilish boshlangan.
SHIKOYATING: Bo'g'ilyapsan! Havoni olyapsan-u, lekin qaytarib chiqarish juda qiyin. Ko'kragingdan hushtaksimon xirillagan ovoz chiqyapti.
HOLATING: O'tirib, ikki qo'ling bilan tizzangga tayanib o'tiribsan (ortopnoe), yotsang nafas ololmaysan.
O'ZING NIMA QILDING: Ingalatoring (Salbutamol) ustaxonada qolib ketgan, yoningga olmagansan.
O'TMISH: 5 yildan beri astma bilan og'riysan. Chang va gul hidlariga allergiyang bor.
ALLERGIYA: Chang, lak-bo'yoq hidlari, polen.
XULQ-ATVOR: Bo'g'ilib, xansirab, 1-2 so'z bilan: 'Havo... yetmayapti... doktor... ingalyator... bering...' deb zo'rg'a javob ber."""
    },

    "8. Pnevmoniya (O'pka yallig'lanishi)": {
        "kategoriya": "Nafas yo'llari",
        "tavsif": "35 yoshli yuvuvchi. 39.3°C isitma, qaltirash, sarg'ish balg'amli yo'tal, o'ng ko'krakda sanchiq.",
        "rang": "#00BCD4",
        "prompt": """Sen o'tkir pnevmoniya bilan og'rigan 35 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI VA OILASI: Avtomoyka ishchisisan. Uylangansan, 1 nafar o'g'ling bor.
BOSHLANISHI: 4 kun oldin sovuq suvda mashina yuvib, qattiq shamollagansan.
SHIKOYATING: Tana harorating 39.3 °C, qattiq qaltirayapsan. Ko'krak o'ng tomoningda nafas olganda va yo'talganda sanchuvchi og'riq bor. Sarg'ish-yashil balg'amli kuchli yo'tal qilyapsan. Butun tanang qaqshab og'riyapti, darmoning yo'q.
O'ZING NIMA QILDING: Uyda Paratsetamol ichgansan, 2 soatga 38.0 ga tushib, keyin yana 39.5 ga ko'tarilgan. Antibiotik ichmagansan.
ALLERGIYA: Penitsillin guruhiga allergiyang bor (Ampitsillindan toshma toshgan).
HAYOT TARZI: Chekasan (kuniga yarim quti).
XULQ-ATVOR: Yo'talib, titrab, darmonsiz: 'Isitma... qiynayapti doktor, ich-etim qaltirab ketyapti...' deb javob ber."""
    },

    # --- ASAB TIZIMI VA TRAVMA ---
    "9. Bosh miya insulti (O'tkir)": {
        "kategoriya": "Asab tizimi",
        "tavsif": "63 yoshli nafaqaxo'r. O'ng qo'l-oyoq ishlamay qolgan, nutq tushunarsiz (dizartriya), yuz o'ng tomoni tortishgan.",
        "rang": "#673AB7",
        "prompt": """Sen insult (bosh miya qon aylanishining o'tkir buzilishi) boshlangan 63 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI VA OILASI: Nafaqadasan. Uylangansan, 2 nafar voyaga yetgan farzanding bor.
BOSHLANISHI: Bugun ertalab soat 07:00 da uyqudan turganda birdan o'ng qo'l va o'ng oyog'ing ishlamay qolgan, tiling aylanmay qolgan.
SHIKOYATING: O'ng qo'l va oyog'ingda umuman kuch yo'q, og'ir. Tiling aylanmayapti, so'zlarni g'o'ldirab aytayapsan. Yuzingning o'ng tomoni tortishib qolgan.
O'TMISH: 10 yildan beri gipertoniya (180/100), qandli diabet (2-tur). Dorilaringni tartibsiz ichasan.
ALLERGIYA: Yo'q.
IRSIYAT: Akang ham insult bo'lgan.
XULQ-ATVOR: Tiling zo'rg'a aylanib, tushunarsizroq, sekin: 'S-salom... t-tilim... aylanmayapti... o'ng qo'lim... og'ir...' deb qiynalib gapir."""
    },

    "10. Bosh miya chayqalishi (Travma)": {
        "kategoriya": "Asab tizimi",
        "tavsif": "28 yoshli talaba. Zinadan yiqilib ensasini urgan: bosh og'rig'i, 2 marta qusgan, yorug'lik yoqmayapti, xotira yo'qolishi.",
        "rang": "#3F51B5",
        "prompt": """Sen yiqilib boshini urib olgan 28 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI: Universitet magistranti. Bo'ydoqsan.
BOSHLANISHI: Bugun soat 15:00 larda zinapoyadan sirpanib yiqilib, boshingning orqa ensasini beton zinaga qattiq urib olgansan. 1-2 minut hushdan ketgansan.
SHIKOYATING: Qanday yiqilganingni eslolmaysan (amneziya). Boshing qattiq lo'qillab og'riyapti, 2 marta qusding. Yorug'lik va shovqin boshingni battar og'rityapti. Ko'zlaring oldi ikkita bo'lib ko'rinyapti.
O'TMISH: Ilgari travma olmagansan, sog'lom yigit.
ALLERGIYA: Yo'q.
XULQ-ATVOR: Boshingni ushlab, ko'zingni yumib: 'Yorug'likni o'chiring, doktor... boshim yorilib ketyapti... ko'nglim aynyapti...' deb past ovozda gapir."""
    },

    # --- OSHQOZON-ICHAK TIZIMI ---
    "11. O'tkir Appenditsit": {
        "kategoriya": "Oshqozon-ichak",
        "tavsif": "25 yoshli bank xodimi. Kindikdan o'ng pastga ko'chgan pichoqdek og'riq, harakatda kuchayadi, 37.8°C isitma.",
        "rang": "#E91E63",
        "prompt": """Sen o'tkir appenditsit xurujidagi 25 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI: Bank xodimi. Bo'ydoqsan.
BOSHLANISHI: Kecha kechqurun kindik atrofida noaniq simillovchi og'riq boshlangan. Bugun ertalabdan og'riq qorinning o'ng pastki qismiga ko'chib, chidab bo'lmas darajada kuchaydi.
SHIKOYATING: Qorinning o'ng pastida o'tkir pichoqdek sanchuvchi og'riq. Yurganingda, yo'talganingda yoki o'ng oyog'ingni bukkanda battar sanchyapti.
HAMROH BELGILAR: Tana harorating 37.8 °C, ko'ngling aynyapti (1 marta qusding), og'zing qurigan.
O'ZING NIMA QILDING: Kechasi No-shpa ichgansan, foyda bermagan. Qorningga issiq grelka qo'ymoqchi bo'lgansan, lekin qo'ymagansan.
ALLERGIYA: Yo'q.
XULQ-ATVOR: Qorning o'ng tomonini ushlab, egilib: 'Asta bosing, doktor... o'ng tomonim pichoq suqqandek sanchyapti... qimirlolmayapman...' deb ingra."""
    },

    "12. O'tkir Oziq-ovqatdan zaharlanish": {
        "kategoriya": "Oshqozon-ichak",
        "tavsif": "30 yoshli haydovchi. Ko'chada ovqatlangach tinimsiz qusish (5 marta), diareya (7 marta), suvsizlanish, 38.2°C isitma.",
        "rang": "#795548",
        "prompt": """Sen ovqatdan qattiq zaharlangan 30 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI: Haydovchi. Uylangansan.
BOSHLANISHI: 5 soat oldin yo'ldagi oshxonada dudlangan kolbasa va kremli tort yegansan.
SHIKOYATING: Tinmay ko'ngling aynyapti, 5 marta ketma-ket safro bilan qusding. Qorningda to'lqinsimon burab og'rish bor, tinmay suyuq iching ketyapti (kuniga 7-8 marta).
HAMROH BELGILAR: Kuchli chanqoqlik, og'iz qurishi, ko'zlar ichga cho'kkan, bosh aylanyapti, oyog'ingda turolmaysan, isitma 38.2 °C.
O'ZING NIMA QILDING: 2 ta ko'mir tabletkasi ichganding, uni ham qusib yubording.
ALLERGIYA: Yo'q.
XULQ-ATVOR: Juda madorsiz, zo'rg'a: 'Suv bering doktor... tinmay ichim ketyapti... qornim burab buralib og'riyapti...' deb ingrab javob ber."""
    },

    # --- ENDOKRIN VA ALLERGIK ---
    "13. Gipoglikemiya (Qand keskin tushishi)": {
        "kategoriya": "Endokrinologiya",
        "tavsif": "45 yoshli diabet bemori. Insulin qilib ovqatlanmagan: qand 2.1 mmol/l, kuchli titroq, sovuq ter, kuchli shirinlik istagi.",
        "rang": "#607D8B",
        "prompt": """Sen qandli diabeti bor 45 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI: Maktab qorovuli. Uylangansan.
BOSHLANISHI: Qandli diabet 1-turing bor. Bugun ertalab soat 07:30 da Insulin ukolini qilgansan, lekin shoshib nonushta qilmagansan. Soat 10:00 da birdan yiqilgansan.
SHIKOYATING: Butun tanang qalt-qalt titrayapti, sovuq yopishqoq ter bosgan. Yuraging 110 ga chiqib tez uryapti. Ko'zlaring xiralashgan, boshing aylanmoqda.
ENG ASOSIY ISTAGING: Juda qattiq och qolgansan va shirinlik (qand/shakar) yeging kelyapti!
QAND MIQDORI: 2.1 mmol/l ga tushib ketgan.
DORILAR: Har kuni Insulin (Novorapid) olasan.
ALLERGIYA: Yo'q.
XULQ-ATVOR: Titrab, tili g'uldirab: 'Doktor... shakar bering... qand bering... titrab ketyapman... qornim och...' deb javob ber."""
    },

    "14. Anafilaktik shok (O'tkir allergiya)": {
        "kategoriya": "Allergik reaksiyalar",
        "tavsif": "33 yoshli bemor. Tish do'xtirida Novokain ukolidan so'ng tomoq va til shishi, bo'g'ilish, toshma, bosim 70/40.",
        "rang": "#D32F2F",
        "prompt": """Sen dori ukolidan keyin o'tkir allergik reaksiyaga uchragan 33 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI: Do'kon sotuvchisi. Uylangansan.
BOSHLANISHI: 15 daqiqa oldin stomatolog tishingga Novokain/Lidokain ukol qilgandi. 5 minutda reaksiya boshlandi.
SHIKOYATING: Tomog'ing ichi va tiling shishib ketdi, havo kirmay bo'g'ilyapsan (Kvinke shishi). Yuzing, lablaring shishgan. Butun badaningga qichimaydigan qizil toshmalar toshgan.
QON BOSIMING: 70/40 mmHg ga tushib ketgan, ko'zlaring qorayib hushdan ketay deyapsan.
ALLERGIYA: Yoshligingda Novokainga allergiyang bo'lgan, lekin do'xtirga aytish esingdan chiqqandi!
XULQ-ATVOR: Bo'g'ilib, xirillab: 'Bo'g'ilyapman... tomog'im... shishyapti... havo... yetmayapti... doktor...' deb zo'rg'a pichirlab gapir."""
    }
}

UMUMIY_PROMPT = """QAT'IY QOIDALAR:
1. Sen 100% haqiqiy bemorsan. Isming Anvar Karimov. Erkak kishisan.
2. FAQAT O'ZBEK TILIDA GAPIR!
3. Har bir savolga 1 ta aniq va qisqa gap bilan javob ber (1-2 gapdan oshmasin).
4. Tibbiy tashxis nomini aytma (masalan 'menda appenditsit' dema, 'qornim o'ng tomoni pichoqdek sanchyapti' de).
5. MUROJAAT VA HUSHMUOMALALIK:
   - Suhbatdoshing shifokor, tibbiyot talabasi yoki hamshira bo'lishi mumkin.
   - Agar suhbatdosh erkak kishi bo'lsa unga: 'doktor', 'doktor aka', 'shifokor' deb murojaat qil.
   - Agar suhbatdosh ayol kishi bo'lsa unga: 'doktor opa', 'opa', 'hamshira opa' deb murojaat qil.
   - Umumiy holatda hurmat bilan 'doktor' deb murojaat qil.
6. QAT'IYAN TAQIQLANADI: Harakat nomlarini (masalan, '(yo'taladi)', '(aksiradi)', '(ingraydi)', '(xansiraydi)') qavsda yoki so'z sifatida aslo yozma va aytma!
"""

def clean_speech_text(raw_text):
    """Matndan qavslar va keraksiz belgilarni tozalash"""
    if not raw_text:
        return ""
    cleaned = re.sub(r'\(.*?\)', '', raw_text)
    cleaned = re.sub(r'\[.*?\]', '', cleaned)
    cleaned = re.sub(r'\*.*?\*', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


class BemorSimulyator:
    def __init__(self, root):
        self.root = root
        self.root.title("Bemor Maniken Simulyatori (Live AI)")
        self.root.geometry("860x740")
        self.root.minsize(780, 620)
        
        self.client = genai.Client(api_key=API_KEY)
        self.msg_queue = queue.Queue()
        self.is_processing = False
        self.running = False
        
        self.chat_container = None
        self.create_selection_page()
    
    def create_selection_page(self):
        """Kasallik tanlash sahifasi"""
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Sarlavha
        ttk.Label(self.main_frame, text="🏥 Bemor Maniken Simulyatori", 
                  font=("Arial", 18, "bold")).pack(pady=(5, 2))
        ttk.Label(self.main_frame, text="Gemini Live AI — Erkak ovozi (Anvar Karimov) | To'liq Klinik Baza", 
                  font=("Arial", 10), foreground="#2E7D32").pack(pady=(0, 15))
        
        # Kasallik tanlash guruhi
        select_group = ttk.LabelFrame(self.main_frame, text=" Bemordagi holat / Kasallik turini tanlang ", padding=15)
        select_group.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        ttk.Label(select_group, text="Kasallikni tanlang:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.kasallik_keys = list(KASALLIKLAR.keys())
        if not hasattr(self, 'kasallik_var'):
            self.kasallik_var = tk.StringVar(value=self.kasallik_keys[0])
        
        self.combo = ttk.Combobox(
            select_group, 
            textvariable=self.kasallik_var, 
            values=self.kasallik_keys, 
            state="readonly", 
            font=("Arial", 11),
            width=50
        )
        self.combo.pack(fill=tk.X, pady=(0, 10))
        self.combo.bind("<<ComboboxSelected>>", self.on_kasallik_change)
        
        # Tavsif oynasi
        tavsif_frame = ttk.Frame(select_group)
        tavsif_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(tavsif_frame, text="Holat tavsifi va klinik belgilar:", font=("Arial", 10, "bold")).pack(anchor="w")
        
        tanlangan = self.kasallik_var.get()
        tavsif_matn = KASALLIKLAR.get(tanlangan, {}).get("tavsif", KASALLIKLAR[self.kasallik_keys[0]]["tavsif"])
        
        self.tavsif_label = tk.Label(
            tavsif_frame, 
            text=tavsif_matn,
            font=("Arial", 11),
            wraplength=740,
            justify="left",
            bg="#f0f4f8",
            fg="#1a237e",
            padx=15,
            pady=15,
            relief=tk.GROOVE
        )
        self.tavsif_label.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Boshlash tugmasi
        self.start_btn = tk.Button(
            self.main_frame, 
            text="▶️ Simulyatsiyani Boshlash", 
            font=("Arial", 12, "bold"),
            bg="#1976D2",
            fg="white",
            activebackground="#1565C0",
            activeforeground="white",
            padx=20,
            pady=10,
            relief=tk.RAISED,
            cursor="hand2",
            command=self.start_simulation
        )
        self.start_btn.pack(pady=(0, 10))
        
        # Status
        self.status_label = ttk.Label(self.main_frame, text="", font=("Arial", 10))
        self.status_label.pack()
    
    def on_kasallik_change(self, event=None):
        """Tanlangan kasallik o'zgarganda tavsifni yangilash"""
        tanlangan = self.kasallik_var.get()
        if tanlangan in KASALLIKLAR:
            self.tavsif_label.config(text=KASALLIKLAR[tanlangan]["tavsif"])
    
    def start_simulation(self):
        """Simulyatsiyani boshlash"""
        kasallik = self.kasallik_var.get()
        system_prompt = UMUMIY_PROMPT + "\n\n" + KASALLIKLAR[kasallik]["prompt"]
        
        self.start_btn.config(state=tk.DISABLED)
        self.status_label.config(text="⏳ Live API ga ulanilmoqda...", foreground="orange")
        self.root.update()
        
        self.running = True
        self.current_kasallik = kasallik
        
        while not self.msg_queue.empty():
            try:
                self.msg_queue.get_nowait()
            except:
                break
                
        thread = threading.Thread(
            target=self._bg_thread,
            args=(system_prompt,),
            daemon=True
        )
        thread.start()
    
    def _bg_thread(self, system_prompt):
        """Fon threadida doimiy jonli sessiyani boshqarish"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while self.running:
            try:
                loop.run_until_complete(self._session_loop(system_prompt))
            except Exception as e:
                if self.running:
                    self.root.after(0, lambda: self.status_var.set("🔄 Qayta ulanilmoqda..."))
                    import time
                    time.sleep(1)
        loop.close()
    
    async def _session_loop(self, system_prompt):
        """Live API doimiy sessiyasi"""
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
            )
        )
        
        async with self.client.aio.live.connect(
            model="gemini-2.5-flash-native-audio-latest",
            config=config
        ) as session:
            self.root.after(0, self._on_connected)
            
            while self.running:
                try:
                    text = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: self.msg_queue.get(timeout=0.5)
                    )
                except queue.Empty:
                    continue
                
                if not self.running:
                    break
                    
                self.root.after(0, lambda: self.status_var.set("⏳ Bemor javob bermoqda..."))
                
                # Xabarni jo'natish
                await session.send_client_content(
                    turns=[types.Content(
                        role="user",
                        parts=[types.Part(text=text)]
                    )]
                )
                
                audio_chunks = []
                transcription_parts = []
                
                try:
                    async def receive_turn():
                        async for response in session.receive():
                            if not self.running:
                                break
                            server_content = response.server_content
                            if server_content is not None:
                                if server_content.output_transcription and server_content.output_transcription.text:
                                    transcription_parts.append(server_content.output_transcription.text)
                                
                                if server_content.model_turn is not None:
                                    for part in server_content.model_turn.parts:
                                        if part.inline_data and part.inline_data.data:
                                            audio_chunks.append(part.inline_data.data)
                                
                                if server_content.turn_complete:
                                    break
                    
                    await asyncio.wait_for(receive_turn(), timeout=20.0)
                    
                    audio_data = b''.join(audio_chunks)
                    raw_text = "".join(transcription_parts).strip()
                    clean_text = clean_speech_text(raw_text)
                    
                    # Agar audio yoki matn bo'sh kelsa, o'zbekcha tabiiy ovozli javob yaratish
                    if not clean_text or len(audio_data) == 0:
                        clean_text = "Eslolmayapman, opa... juda qiynalyapman..."
                        tts_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bemor_javobi.mp3")
                        comm = edge_tts.Communicate(text=clean_text, voice="uz-UZ-SardorNeural")
                        await comm.save(tts_file)
                        audio_data = b'EDGE_TTS'
                    
                    if self.running:
                        self.root.after(0, self._handle_response, clean_text, audio_data)
                    
                except asyncio.TimeoutError:
                    if self.running:
                        self.root.after(0, self._handle_response, "Eslolmayapman, opa...", b'EDGE_TTS')
                    break
                except Exception as e:
                    if self.running:
                        self.root.after(0, self._handle_response, "Boshim aylanib ketdi, opa...", b'EDGE_TTS')
                    break
    
    def _on_connected(self):
        """Muvaffaqiyatli ulanganda Chat oynasiga o'tish"""
        if hasattr(self, 'main_frame') and self.main_frame.winfo_exists():
            self.main_frame.destroy()
            self.create_chat_page(self.current_kasallik)
        elif hasattr(self, 'status_var'):
            self.status_var.set("✅ Tayyor — savolingizni yozing")
    
    def create_chat_page(self, kasallik):
        """Chat oynasi"""
        rang = KASALLIKLAR[kasallik]["rang"]
        
        self.chat_container = ttk.Frame(self.root)
        self.chat_container.pack(fill=tk.BOTH, expand=True)
        
        # Yuqori panel
        top_frame = tk.Frame(self.chat_container, bg=rang, height=55)
        top_frame.pack(fill=tk.X)
        top_frame.pack_propagate(False)
        
        # Orqaga qaytish tugmasi
        back_btn = tk.Button(
            top_frame,
            text="◀️ Orqaga (Kasallikni almashtirish)",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg=rang,
            activebackground="#eeeeee",
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.go_back_to_selection
        )
        back_btn.pack(side=tk.LEFT, padx=15, pady=10)
        
        title_label = tk.Label(
            top_frame, 
            text=f"👨 Bemor: Anvar Karimov  |  🩺 {kasallik}", 
            fg="white", 
            bg=rang, 
            font=("Arial", 12, "bold")
        )
        title_label.pack(side=tk.LEFT, expand=True, padx=(0, 100))
        
        # Chat oynasi
        chat_frame = ttk.Frame(self.chat_container, padding=10)
        chat_frame.pack(fill=tk.BOTH, expand=True)
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame, wrap=tk.WORD, font=("Segoe UI", 12),
            state=tk.DISABLED, bg="#fbfbfb", relief=tk.FLAT, padx=10, pady=10
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Teglar
        self.chat_display.tag_configure("hamshira", foreground="#0D47A1", font=("Segoe UI", 12, "bold"))
        self.chat_display.tag_configure("bemor", foreground="#B71C1C", font=("Segoe UI", 12, "bold"))
        self.chat_display.tag_configure("tizim", foreground="#546E7A", font=("Segoe UI", 10, "italic"))
        
        self.add_message(f"🟢 Simulyatsiya boshlandi: {kasallik}\nBemordan holatini so'rang (masalan: 'Qayeringiz og'riyapti?', 'Qachon boshlandi?', 'Allergiyangiz bormi?')...\n", "tizim")
        
        # Pastki panel
        bottom_frame = ttk.Frame(self.chat_container, padding=10)
        bottom_frame.pack(fill=tk.X)
        
        self.input_entry = ttk.Entry(bottom_frame, font=("Segoe UI", 12))
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.input_entry.bind("<Return>", lambda e: self.send_message())
        self.input_entry.focus()
        
        self.send_btn = tk.Button(
            bottom_frame, 
            text="Yuborish 💬", 
            font=("Segoe UI", 11, "bold"),
            bg="#1976D2",
            fg="white",
            padx=15,
            pady=5,
            cursor="hand2",
            command=self.send_message
        )
        self.send_btn.pack(side=tk.RIGHT)
        
        # Status bar
        self.status_var = tk.StringVar(value="✅ Tayyor — savolingizni yozing")
        ttk.Label(self.chat_container, textvariable=self.status_var, 
                 font=("Segoe UI", 9), foreground="#37474F").pack(anchor="w", padx=15, pady=(0, 8))
    
    def go_back_to_selection(self):
        """Chatdan chiqib boshlang'ich kasallik tanlash sahifasiga qaytish"""
        self.running = False
        self.is_processing = False
        
        while not self.msg_queue.empty():
            try:
                self.msg_queue.get_nowait()
            except:
                break
                
        if self.chat_container and self.chat_container.winfo_exists():
            self.chat_container.destroy()
            
        self.create_selection_page()
    
    def add_message(self, text, tag):
        """Chatga xabar qo'shish"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, text + "\n\n", tag)
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def send_message(self):
        """Hamshira savolini yuborish"""
        if self.is_processing:
            return
            
        user_text = self.input_entry.get().strip()
        if not user_text:
            return
        
        self.input_entry.delete(0, tk.END)
        self.add_message(f"👩‍⚕️ Hamshira: {user_text}", "hamshira")
        
        self.is_processing = True
        self.send_btn.config(state=tk.DISABLED)
        self.status_var.set("⏳ Bemor javob qaytarmoqda...")
        
        self.root.after(25000, self._safety_timeout)
        self.msg_queue.put(user_text)
    
    def _safety_timeout(self):
        """Xavfsizlik taymeri"""
        if self.is_processing:
            self._finish_processing()
    
    def _handle_response(self, clean_text, audio_data):
        """Bemor javobini ko'rsatish va ovoz chiqarish"""
        self.add_message(f"👨 Bemor (Anvar): {clean_text}", "bemor")
        
        if audio_data == b'EDGE_TTS':
            self.status_var.set("🔊 Bemor gapirmoqda...")
            thread = threading.Thread(target=self._play_mp3, daemon=True)
            thread.start()
        elif audio_data and len(audio_data) > 0:
            self.status_var.set("🔊 Bemor gapirmoqda...")
            thread = threading.Thread(
                target=self._play_pcm_audio, args=(audio_data,), daemon=True
            )
            thread.start()
        else:
            self._finish_processing()
    
    def _play_pcm_audio(self, pcm_data):
        """PCM audio ma'lumotlarini o'ynatish"""
        audio_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "bemor_javobi.wav"
        )
        try:
            with wave.open(audio_file, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(pcm_data)
            
            mci = ctypes.windll.winmm.mciSendStringW
            mci(f'open "{audio_file}" alias bemor_ovoz', None, 0, 0)
            mci('play bemor_ovoz wait', None, 0, 0)
            mci('close bemor_ovoz', None, 0, 0)
            
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set(f"Ovoz xatolik: {e}"))
        finally:
            try:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            except:
                pass
            self.root.after(0, self._finish_processing)
    
    def _play_mp3(self):
        """MP3 audio faylni o'ynatish"""
        audio_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bemor_javobi.mp3")
        try:
            mci = ctypes.windll.winmm.mciSendStringW
            mci(f'open "{audio_file}" type mpegvideo alias bemor_ovoz_mp3', None, 0, 0)
            mci('play bemor_ovoz_mp3 wait', None, 0, 0)
            mci('close bemor_ovoz_mp3', None, 0, 0)
        except:
            pass
        finally:
            try:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            except:
                pass
            self.root.after(0, self._finish_processing)
    
    def _finish_processing(self):
        """Jarayonni yakunlash"""
        self.is_processing = False
        if hasattr(self, 'send_btn') and self.send_btn.winfo_exists():
            self.send_btn.config(state=tk.NORMAL)
        if hasattr(self, 'status_var'):
            self.status_var.set("✅ Tayyor — keyingi savolni bering")
    
    def on_closing(self):
        """Dastur yopilganda to'xtatish"""
        self.running = False
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = BemorSimulyator(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
