import os
import sys
import io
import wave
import base64
import asyncio
import socket
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from google import genai
from google.genai import types
import uvicorn
from vital_monitor import HTML_CONTENT as MONITOR_HTML, active_websockets as monitor_websockets, latest_telemetry


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
Hamshira savollariga xotirjam, muloyim, aniq va samimiy javob ber."""
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
PSIXOLOGIYA: Xavotirdasan, qo'rqyapsan: 'Yuragim to'xtab qolmaydimi, opa?' deb so'raysan.
Hamshira savollariga xansirab, qiynalib, qisqa-qisqa javob ber."""
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
XULQ-ATVOR: Juda sekin, holsiz, pichirlab, zo'rg'a gapirasan: 'Madorim yo'q, opa... ko'zim tinib ketyapti...' deb uzuq-yuluq javob ber."""
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
PSIXOLOGIYA: Yuraging to'xtab qolishidan qo'rqyapsan: 'Yuragim to'xtab-to'xtab uryapti opa, qo'rqyapman...' deb qisqa javob ber."""
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
PSIXOLOGIYA: Chap ko'kragingni ushlab, ingrab: 'Opa, tosh bosyapti... o'lib qolmaymanmi, tezroq yordam bering...' deb zo'rg'a gapir."""
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
XULQ-ATVOR: Yorug'likdan ko'zingni qisib, past ovozda: 'Boshingizni baland ko'taring... ensam yorilib ketay deyapti...' deb gapir."""
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
XULQ-ATVOR: Bo'g'ilib, xansirab, 1-2 so'z bilan: 'Havo... yetmayapti... ingalyator... bering...' deb zo'rg'a javob ber."""
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
XULQ-ATVOR: Yo'talib, titrab, darmonsiz: 'Isitma... qiynayapti opa, ich-etim qaltirab ketyapti...' deb javob ber."""
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
XULQ-ATVOR: Tiling zo'rg'a aylanib, tushunarsizroq, sekin: 'S-salom... t-tilim... aylanmayapti... o'ng qo'lim... og'ir...' deb qiynalib gapir."""
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
XULQ-ATVOR: Boshingni ushlab, ko'zingni yumib: 'Yorug'likni o'chiring... boshim yorilib ketyapti... ko'nglim aynyapti...' deb past ovozda gapir."""
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
XULQ-ATVOR: Qorning o'ng tomonini ushlab, egilib: 'Asta bosing opa... o'ng tomonim pichoq suqqandek sanchyapti... qimirlolmayapman...' deb ingra."""
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
XULQ-ATVOR: Juda madorsiz, zo'rg'a: 'Suv bering... tinmay ichim ketyapti... qornim burab buralib og'riyapti...' deb ingrab javob ber."""
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
XULQ-ATVOR: Titrab, tili g'uldirab: 'Opa... shakar bering... qand bering... titrab ketyapman... qornim och...' deb javob ber."""
    },
    "allergiya": {
        "nomi": "14. Anafilaktik shok (O'tkir allergiya)",
        "kategoriya": "Allergik reaksiyalar",
        "tavsif": "33 yoshli bemor. Tish do'xtirida Novokain ukolidan so'ng tomoq va til shishi, bo'g'ilish, toshma, bosim 70/40.",
        "rang": "#DC2626",
        "prompt": """Sen dori ukolidan keyin o'tkir allergik reaksiyaga uchragan 33 yoshli erkak bemorsan. Isming Anvar Karimov.
KASBI: Do'kon sotuvchisi. Uylangansan.
BOSHLANISHI: 15 daqiqa oldin stomatolog tishingga Novokain/Lidokain ukol qilgandi. 5 minutda reaksiya boshlandi.
SHIKOYATING: Tomog'ing ichi va tiling shishib ketdi, havo kirmay bo'g'ilyapsan (Kvinke shishi). Yuzing, lablaring shishgan. Butun badaningga qichimaydigan qizil toshmalar toshgan.
QON BOSIMING: 70/40 mmHg ga tushib ketgan, ko'zlaring qorayib hushdan ketay deyapsan.
ALLERGIYA: Yoshligingda Novokainga allergiyang bo'lgan, lekin do'xtirga aytish esingdan chiqqandi!
XULQ-ATVOR: Bo'g'ilib, xirillab: 'Bo'g'ilyapman... tomog'im... shishyapti... havo... yetmayapti...' deb zo'rg'a pichirlab gapir."""
    }
}

UMUMIY_PROMPT = """QAT'IY QOIDALAR:
1. Sen 100% haqiqiy bemorsan. Isming Anvar Karimov. Erkak kishisan (40 yosh).
2. FAQAT O'ZBEK TILIDA GAPIR!
3. Har bir savolga 1 ta aniq va qisqa gap bilan javob ber (1-2 gapdan oshmasin).
4. Tibbiy tashxis nomini aytma (masalan 'menda appenditsit' dema, 'qornim o'ng tomoni pichoqdek sanchyapti' de).
5. Hamshiraga hurmat bilan 'opa' deb murojaat qil.
6. QAT'IYAN TAQIQLANADI: Harakat nomlarini (masalan, '(yo'taladi)', '(aksiradi)', '(ingraydi)', '(xansiraydi)') qavsda yoki so'z sifatida aslo yozma va aytma!
"""

app = FastAPI(title="Bemor Maniken Simulyatori Web App")

# HTML Content (Single Page Responsive App)
HTML_CONTENT = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="theme-color" content="#4338ca">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Bemor Simulyatori">
    <link rel="manifest" href="/manifest.json">
    <link rel="icon" href="https://cdn-icons-png.flatsome.org/512/2966/2966327.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .chat-scroll::-webkit-scrollbar { width: 6px; }
        .chat-scroll::-webkit-scrollbar-track { background: #f1f5f9; }
        .chat-scroll::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
    </style>
</head>
<body class="bg-slate-100 min-h-screen font-sans text-slate-800 flex flex-col">

    <!-- Header -->
    <header class="bg-indigo-700 text-white shadow-md sticky top-0 z-50">
        <div class="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center text-xl">
                    <i class="fa-solid fa-hospital-user"></i>
                </div>
                <div>
                    <h1 class="font-bold text-lg leading-tight">Bemor Maniken Simulyatori</h1>
                    <p class="text-xs text-indigo-200">Gemini Live AI — Erkak ovozi (Anvar, 40 yosh)</p>
                </div>
            </div>
            <div class="flex items-center space-x-3">
                <a href="/monitor" target="_blank" class="px-3 py-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-xs flex items-center gap-1.5 shadow transition">
                    <i class="fa-solid fa-heart-pulse"></i>
                    <span>📊 Vital Monitor</span>
                </a>
                <div id="top-status" class="flex items-center space-x-2 bg-indigo-800/60 px-3 py-1.5 rounded-full text-xs">
                    <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
                    <span id="conn-text">Tizim tayyor</span>
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
                    <div class="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center text-xl">
                        <i class="fa-solid fa-user-injured"></i>
                    </div>
                    <div>
                        <div class="font-bold text-base leading-tight" id="patient-name">Bemor: Anvar (40 yosh)</div>
                        <div class="text-xs opacity-90" id="current-disease-name">1. Normal (Sog'lom ko'rik)</div>
                    </div>
                </div>
                <div class="flex items-center space-x-2">
                    <button id="speaker-btn" onclick="toggleSpeaker()" title="Ovozni yoqish/o'chirish"
                            class="p-2 rounded-xl bg-white/20 hover:bg-white/30 transition text-sm">
                        <i class="fa-solid fa-volume-high"></i>
                    </button>
                    <button onclick="resetChat()" title="Suhbatni tozalash"
                            class="p-2 rounded-xl bg-white/20 hover:bg-white/30 transition text-sm">
                        <i class="fa-solid fa-rotate-right"></i>
                    </button>
                </div>
            </div>

            <!-- Messages Log -->
            <div id="chat-box" class="flex-1 p-4 overflow-y-auto chat-scroll space-y-4 bg-slate-50 min-h-[380px] max-h-[500px]">
                <div class="bg-indigo-50 border border-indigo-100 rounded-xl p-3 text-xs text-indigo-800 text-center">
                    🟢 <b>Jonli simulyatsiya faol!</b> Hamshira sifatida bemordan ahvolini so'rang (masalan: <i>"Qayeringiz og'riyapti?", "Qachon boshlandi?"</i>). Bemor gapirib javob qaytaradi.
                </div>
            </div>

            <!-- Status bar -->
            <div class="px-4 py-1.5 bg-slate-100 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
                <div id="typing-status" class="flex items-center gap-1.5">
                    <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
                    <span>Tayyor</span>
                </div>
                <div class="text-slate-400">Gemini Live Native Audio (Puck)</div>
            </div>

            <!-- Input area -->
            <div class="p-3 bg-white border-t border-slate-200">
                <form id="chat-form" onsubmit="sendMessage(event)" class="flex items-center gap-2">
                    <button type="button" id="mic-btn" onclick="toggleVoiceInput()" title="Ovoz bilan gapirish"
                            class="w-11 h-11 rounded-xl bg-slate-100 text-slate-600 hover:bg-indigo-100 hover:text-indigo-600 transition flex items-center justify-center">
                        <i class="fa-solid fa-microphone text-base"></i>
                    </button>
                    <input type="text" id="user-input" placeholder="Hamshira savolini yozing (yoki mikrofondan gapiring)..." 
                           autocomplete="off"
                           class="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500">
                    <button type="submit" id="send-btn" 
                            class="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-semibold text-sm transition flex items-center gap-1.5 shadow-sm">
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
        let recognition = null;
        let isRecording = false;
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
            
            // Connect WebSocket
            connectWebSocket();
            
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

        // Connect WebSocket
        function connectWebSocket() {
            if (ws) {
                ws.close();
            }
            
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/chat/${currentKey}`;
            
            updateStatus("⏳ Ulanmoqda...", "orange");
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                updateStatus("✅ Tayyor", "emerald");
                document.getElementById("conn-text").innerText = "Live AI ulandi";
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === "response") {
                    addPatientMessage(data.text);
                    if (data.audio && speakerEnabled) {
                        playBase64Audio(data.audio, data.format || "wav");
                    }
                    setProcessing(false);
                } else if (data.type === "status") {
                    updateStatus(data.message, "indigo");
                } else if (data.type === "error") {
                    addSystemMessage(`❌ Xatolik: ${data.message}`);
                    setProcessing(false);
                }
            };
            
            ws.onclose = () => {
                updateStatus("🔄 Qayta ulanilmoqda...", "orange");
                document.getElementById("conn-text").innerText = "Ulanish kutilmoqda";
            };
            
            ws.onerror = (err) => {
                console.error("WS error:", err);
                setProcessing(false);
            };
        }

        // Send Message
        function sendMessage(e) {
            if (e) e.preventDefault();
            if (isProcessing) return;
            
            const inputEl = document.getElementById("user-input");
            const text = inputEl.value.trim();
            if (!text) return;
            
            inputEl.value = "";
            addNurseMessage(text);
            
            setProcessing(true);
            updateStatus("⏳ Bemor javob bermoqda...", "orange");
            
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ text: text }));
            } else {
                addSystemMessage("❌ Ulanish yo'q. Qaytadan ulanmoqda...");
                connectWebSocket();
                setTimeout(() => {
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({ text: text }));
                    } else {
                        setProcessing(false);
                    }
                }, 1000);
            }
        }

        // Play Audio (Base64 WAV / MP3)
        function playBase64Audio(base64Data, format = "wav") {
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
                    <div class="font-bold text-xs text-indigo-200 mb-0.5"><i class="fa-solid fa-user-nurse mr-1"></i> Hamshira</div>
                    <div>${escapeHtml(text)}</div>
                </div>
                <div class="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold shrink-0">
                    <i class="fa-solid fa-user-nurse"></i>
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
            document.getElementById("send-btn").disabled = state;
            if (!state) {
                updateStatus("✅ Tayyor", "emerald");
                document.getElementById("user-input").focus();
            }
        }

        function toggleSpeaker() {
            speakerEnabled = !speakerEnabled;
            const btn = document.getElementById("speaker-btn");
            btn.innerHTML = speakerEnabled ? '<i class="fa-solid fa-volume-high"></i>' : '<i class="fa-solid fa-volume-xmark"></i>';
        }

        function resetChat() {
            document.getElementById("chat-box").innerHTML = `
                <div class="bg-indigo-50 border border-indigo-100 rounded-xl p-3 text-xs text-indigo-800 text-center">
                    🟢 <b>Suhbat tozalandi.</b> Bemorga savol berishingiz mumkin.
                </div>
            `;
        }

        // Voice Input (Web Speech API)
        function toggleVoiceInput() {
            if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
                alert("Brauzeringiz mikrofondan ovozni matnga aylantirishni qo'llab-quvvatlamaydi. Chrome yoki Edge brauzeridan foydalaning.");
                return;
            }
            
            const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
            
            if (isRecording) {
                if (recognition) recognition.stop();
                isRecording = false;
                document.getElementById("mic-btn").classList.remove("bg-red-500", "text-white", "animate-pulse");
                return;
            }
            
            recognition = new SpeechRec();
            recognition.lang = 'uz-UZ';
            recognition.continuous = false;
            recognition.interimResults = false;
            
            recognition.onstart = () => {
                isRecording = true;
                const btn = document.getElementById("mic-btn");
                btn.classList.add("bg-red-500", "text-white", "animate-pulse");
                updateStatus("🎙️ Tinglamoqda...", "red");
            };
            
            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                document.getElementById("user-input").value = transcript;
                sendMessage();
            };
            
            recognition.onend = () => {
                isRecording = false;
                const btn = document.getElementById("mic-btn");
                btn.classList.remove("bg-red-500", "text-white", "animate-pulse");
                updateStatus("✅ Tayyor", "emerald");
            };
            
            recognition.onerror = (e) => {
                console.log("Speech err:", e);
                isRecording = false;
                document.getElementById("mic-btn").classList.remove("bg-red-500", "text-white", "animate-pulse");
            };
            
            recognition.start();
        }

        function escapeHtml(str) {
            return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }

        // Filter event
        document.getElementById("search-box").addEventListener("input", (e) => {
            renderDiseases(e.target.value);
        });

        // Initialize on load
        window.onload = () => {
            loadDiseases();
        };
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_index():
    return HTMLResponse(content=HTML_CONTENT)

@app.get("/monitor", response_class=HTMLResponse)
async def get_monitor():
    return HTMLResponse(content=MONITOR_HTML)

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
        )
    )
    
    try:
        async with client.aio.live.connect(
            model="gemini-2.5-flash-native-audio-latest",
            config=config
        ) as session:
            while True:
                data = await websocket.receive_json()
                user_text = data.get("text", "").strip()
                if not user_text:
                    continue
                
                # Send to Live API
                await session.send_client_content(
                    turns=[types.Content(
                        role="user",
                        parts=[types.Part(text=user_text)]
                    )]
                )
                
                audio_chunks = []
                transcription_parts = []
                
                try:
                    async def receive_turn():
                        async for response in session.receive():
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
                    
                    audio_bytes = b''.join(audio_chunks)
                    clean_text = "".join(transcription_parts).strip()
                    
                    if not clean_text or len(audio_bytes) == 0:
                        clean_text = "Eslolmayapman, opa... juda qiynalyapman..."
                        # Edge-TTS fallback
                        tts_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_fallback.mp3")
                        comm = edge_tts.Communicate(text=clean_text, voice="uz-UZ-SardorNeural")
                        await comm.save(tts_file)
                        with open(tts_file, "rb") as f:
                            mp3_base64 = base64.b64encode(f.read()).decode('utf-8')
                        try:
                            os.remove(tts_file)
                        except:
                            pass
                        
                        await websocket.send_json({
                            "type": "response",
                            "text": clean_text,
                            "audio": mp3_base64,
                            "format": "mp3"
                        })
                        continue
                    
                    # Convert PCM to WAV in memory
                    wav_io = io.BytesIO()
                    with wave.open(wav_io, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(24000)
                        wf.writeframes(audio_bytes)
                    
                    wav_base64 = base64.b64encode(wav_io.getvalue()).decode('utf-8')
                    
                    await websocket.send_json({
                        "type": "response",
                        "text": clean_text,
                        "audio": wav_base64,
                        "format": "wav"
                    })
                    
                except asyncio.TimeoutError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Javob kutish vaqti tugadi. Qaytadan urinib ko'ring."
                    })
                    break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass

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
