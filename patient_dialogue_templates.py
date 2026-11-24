"""
RO'TFMXMO va UIM Navoiy filiali — AI Bemor Simulyatori
Bemor bilan Muloqot va Suhbatni Yakunlash Shabloni (Clinical Dialogue & Concluding Templates)
Har bir kasallik uchun alohida chuqur savollar, klinik parvarish va professional yakunlash protokoli.
"""

from typing import Dict, Any, List
import json
import re

# Dastlabki 20 ta kasallik uchun chuqurlashtirilgan maxsus shablonlar
DETAILED_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "normal": {
        "nomi": "1. Normal (Sog'lom ko'rik)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum! Men profilaktik ko'rik bo'yicha navbatchi hamshiraman. Ismingiz Anvar aka, to'g'rimi?",
            "izoh": "Bemor bilan samimiy aloqa o'rnating, xushmuomala bo'ling."
        },
        "savollar": [
            {
                "savol": "O'zingizni bugun qanday his qilyapsiz? Biror joyingizda og'riq yoki noqulaylik bormi?",
                "maqsad": "Umumiy subyektiv holatni baholash"
            },
            {
                "savol": "Oxirgi paytlarda bosh og'rig'i, yurak o'ynashi yoki tez charchash bezovta qilmadimi?",
                "maqsad": "Yashirin astenik va kardiovaskulyar simptomlarni aniqlash"
            },
            {
                "savol": "Qon bosimingiz odatda nechani ko'rsatadi? Doimiy ichadigan dori-darmonlaringiz bormi?",
                "maqsad": "Gipotenziv dorilar va bazaviy gemodinamikani bilish"
            },
            {
                "savol": "Dori vositalariga yoki oziq-ovqatlarga allergik reaksiyangiz bormi?",
                "maqsad": "Allergik anamnezni tekshirish"
            },
            {
                "savol": "Kechasi uyqungiz qanday, ertalab tetik uyg'onyapsizmi?",
                "maqsad": "Psixoemosional va vegetativ holatni tekshirish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni qulay o'tqazing, xotirjam qilib qon bosimi va pulsini o'lchang (norma 120/80 mmHg, 72 bpm). Profilaktik tavsiyalar bering."
        },
        "yakunlash": {
            "matn": "Anvar aka, barcha ko'rsatkichlaringiz ajoyib, sog'lig'ingiz yaxshi holatda. Ma'lumotlarni kartangizga kiritdim. Hozir umumiy xulosa berish uchun terapevt shifokor ko'rigiga yo'naltiraman. Vaqtingiz uchun rahmat, salomat bo'ling!",
            "hisobot": "Bemor Anvar (40 yosh), sog'lom ko'rik. Shikoyati yo'q, gemodinamika stabil (BP 120/80, HR 72). Profilaktik ko'rik yakunlandi."
        }
    },

    "taxikardiya": {
        "nomi": "2. Taxikardiya (Yurak tez urishi)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. O'zingizni erkin tuting, nafas olishingizni rostlab oling.",
            "izoh": "Bemorda xavotir kuchli bo'ladi, xotirjam va sokin ovozda gapiring."
        },
        "savollar": [
            {
                "savol": "Yuragingiz qanchalik tez urayotganini sezyapsiz? Ko'kragingizdan chiqib ketayotgandek tuyulyaptimi?",
                "maqsad": "Yurak urishi hissi va uning subyektiv og'irligini aniqlash"
            },
            {
                "savol": "Bu holat qachon boshlandi? Boshlanishidan oldin energetik ichimlik, ko'p kofe ichmadingizmi yoki kuchli asabiylashmadingizmi?",
                "maqsad": "Provokatsiya qiluvchi omillarni (kofein, stress) aniqlash"
            },
            {
                "savol": "Havo yetishmasligi, hansirash yoki ko'krakda siqilish hissi bormi?",
                "maqsad": "Gipoksiya va miokard ishemiyasi xavfini baholash"
            },
            {
                "savol": "Bosh aylanishi, ko'z tinishi yoki hushdan ketgudek bo'lish holati sezildimi?",
                "maqsad": "Gipotoniya va bosh miya perfuziyasi buzilishini istisno qilish"
            },
            {
                "savol": "Ilgari ham shunaqa yurak o'ynashi bo'lganmi? Qalqonsimon bez yoki yurak kasalliklari bo'yicha hisobda turasizmi?",
                "maqsad": "Anamnezdagi aritmiya yoki tireotoksikozni tekshirish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni darhol yarim o'tirgan holatda yotqizing. Yoqasini va kamarini bo'shating. Toza havo oching yoki kislorod niqobini tayyorlang. Puls va SpO2 o'lchang."
        },
        "yakunlash": {
            "matn": "Xavotir olmang, siz shifoxonadasiz, yoningizdamiz. Chuqur burun bilan nafas olib, og'izdan sekin chiqaring. Men hozir darhol EKG apparatini ulayman va navbatchi shifokorni chaqiraman. Hech qayoqqa qimirlamang.",
            "hisobot": "Bemor 42 yosh, kofe fonida sinusli taxikardiya (HR 135 bpm), xavotir va taxipnoe bor. Zudlik bilan EKG va shifokor ko'rigi zarur."
        }
    },

    "bradikardiya": {
        "nomi": "3. Bradikardiya (Yurak sekin urishi)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Holsizlanib qolgan ko'rinasiz, qimirlamasdan yotavering.",
            "izoh": "Bosh aylanishi va hushdan ketish xavfi bor, bemorni yurgizmaslik shart."
        },
        "savollar": [
            {
                "savol": "O'zingizda qanday o'zgarish sezyapsiz? Bosh aylanishi, ko'z qorong'ilashishi bormi?",
                "maqsad": "Bosh miya gipoperfuziyasi darajasini aniqlash"
            },
            {
                "savol": "Qon bosimi yoki yurak uchun qanday dori ichasiz? Bugun dorini me'yoridan ortiq qabul qilmadilarmi (masalan, beta-blokatorlar)?",
                "maqsad": "Iatrogen medikamentoz bradikardiyani aniqlash"
            },
            {
                "savol": "Hushingizdan ketib qolgan paytingiz bo'ldimi yoki yiqilib tushmadingizmi?",
                "maqsad": "Morganyi-Edams-Stoks (MES) xurujini istisno qilish"
            },
            {
                "savol": "Ko'kragingizda qisilish, sovuq ter yoki og'irlik bormi?",
                "maqsad": "O'tkir koronar sindrom / AV blokada xavfini baholash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni gorizontal yotqizing, oyoqlari tagiga yostiq qo'yib biroz ko'taring (bosh miyaga qon oqimini yaxshilash). Karotid sinusga bosim o'tkazmang. Zudlik bilan puls va EKG tekshiring."
        },
        "yakunlash": {
            "matn": "Iltimos, o'rningizdan turishga harakat qilmang, boshingiz aylanib ketishi mumkin. Men aytgan barcha ma'lumotlaringizni qayd etdim. Hozir reanimatolog va kardiolog shifokorga xabar beraman, kerakli dorilarni tayyorlaymiz. Xotirjam bo'ling.",
            "hisobot": "Bemor 58 yosh, gipotenziv dori ortig'i fonida og'ir bradikardiya (HR 42 bpm), kuchli gipoperfuziya belgilari bor. Shoshilinch kardiologik yordam kerak."
        }
    },

    "aritmiya": {
        "nomi": "4. Aritmiya (Yurak ritmi buzilishi)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Iltimos, chuqur nafas oling, sizga yordam beramiz.",
            "izoh": "Yurak to'xtab-to'xtab urishi bemorni qattiq vahimaga soladi."
        },
        "savollar": [
            {
                "savol": "Yuragingiz qanday uryapti? To'xtab qolgandek, so'ng birdan qattiq urib ketish (sakrash) sezilyaptimi?",
                "maqsad": "Ekstrasistoliya yoki xilpillovchi aritmiya belgilarini aniqlash"
            },
            {
                "savol": "Ushbu noqulaylik qachon boshlandi? Energetik ichimlik, spirtli ichimlik yoki og'ir jismoniy zo'riqish bo'ldimi?",
                "maqsad": "Provokatsion omillarni aniqlash"
            },
            {
                "savol": "Ko'kragingizda sanchuvchi, siquvchi og'riq bormi? Chap yelkaga o'tmayaptimi?",
                "maqsad": "Koronar ishemiya mavjudligini tekshirish"
            },
            {
                "savol": "Nafas olishingiz qanday, havo yetishmasligi hissi bormi?",
                "maqsad": "O'pka dimlanishi va gipoksiya darajasi"
            },
            {
                "savol": "Ilgari yuragingiz uchun Kordaron, Digoksin yoki ritm dorilarini ichganmisiz?",
                "maqsad": "Surunkali aritmiya anamnezini o'rganish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni qulay yarim o'tirgan holatga keltiring. Kislorod ulanishini tayyorlang. 12 kanalli EKG apparatini bemor ko'kragiga tezkor ulay boshlang."
        },
        "yakunlash": {
            "matn": "Ortiqcha harakat qilmang va gapirmaslikka harakat qiling. Hozir bir daqiqada EKG olamiz, ritmingiz qanday buzilganini aniqlab, shifokor bilan birga darhol ritmni tiklash muolajasini boshlaymiz. Rahmat, hozir kelaman.",
            "hisobot": "Bemor 50 yosh, energetik ichimlik fonida paroksizmal aritmiya, ekstrasistoliya va ko'krakda sanchiq. Zudlik bilan EKG registratsiyasi boshlandi."
        }
    },

    "infarkt": {
        "nomi": "5. Miokard Infarkti / Stenokardiya",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Hech qimirlamang, gapirishga zo'riqmang, sizga shoshilinch yordam ko'rsatyapmiz.",
            "izoh": "Har bir daqiqa qadrli! O'tkir koronar sindrom bo'yicha shoshilinch qisqa savollar bering."
        },
        "savollar": [
            {
                "savol": "Og'riq aynan ko'krak qafasining qayerida? Chap qo'lga, yelkaga, bo'yinga yoki pastki jag'ga beryaptimi?",
                "maqsad": "Og'riq irradiatsiyasi va lokalizatsiyasini aniqlash"
            },
            {
                "savol": "Og'riq qanday xarakterda: tosh bosgandek ezuvchi, siquvchimi yoki kuydiruvchimi?",
                "maqsad": "Klassik anginoz og'riq belgisini tasdiqlash"
            },
            {
                "savol": "Og'riq qachon boshlandi? 20 daqiqadan ko'proq davom etyaptimi?",
                "maqsad": "Stenokardiya va o'tkir infarkt differensial diagnostikasi"
            },
            {
                "savol": "Til ostiga Nitroglitserin tabletkasi yoki spreyini qabul qildingizmi? Og'riq kamaydimi yoki o'zgarishsiz qoldimi?",
                "maqsad": "Nitratlarga rezistentlik (infarkt xavfi)ni aniqlash"
            },
            {
                "savol": "Sovuq ter bosishi, kuchli ko'ngil aynishi yoki o'lim qo'rquvi bormi?",
                "maqsad": "Kardiogen shok va o'tkir asoratlar belgilarini aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni qat'iy to'shak rejimiga o'tkazing (harakatlanish mutlaqo man etiladi!). Yuqori oqimli kislorod niqobini taqing. Periferik venaga kateter qo'ying. Zudlik bilan 12 kanalli EKG oling."
        },
        "yakunlash": {
            "matn": "Anvar aka, siz mutlaqo qimirlamang, gapirishga ham urinmang. Aytganlaringiz bo'yicha shifokorga xabar berdim. Hozir reanimatsiya va kardiologiya brigadasi kelmoqda, og'riq qoldiruvchi ukol va EKG muolajalarini zudlik bilan boshlaymiz. Biz siz bilanmiz!",
            "hisobot": "Bemor 55 yosh, o'tkir koronar sindrom / miokard infarkti belgilari: retrosternal bosuvchi og'riq, chap qo'l va jag'ga tarqalmoqda, sovuq ter, nitroglitseringa javob yo'q. Qizil kod — zudlik bilan kardiologiya reanimatsiyasi!"
        }
    },

    "gipertoniya": {
        "nomi": "6. Gipertonik Kriz (Bosim oshishi)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Iltimos, chuqur nafas oling, hozir bosimingizni me'yoriga tushiramiz.",
            "izoh": "Bosimning keskin tushib ketishi insult xavfini tug'dirishi mumkin, xotirjam yondashing."
        },
        "savollar": [
            {
                "savol": "Boshingizning qaysi qismi og'riyapti? Ensa sohasida qattiq lo'qillash yoki og'irlik bormi?",
                "maqsad": "Gipertonik krizga xos bosh og'rig'i turini aniqlash"
            },
            {
                "savol": "Ko'z oldingizda qora nuqtalar, xiralashish yoki pashshalar uchishi sezilyaptimi?",
                "maqsad": "Retinopatiya va ko'ruv nervi zo'riqishini tekshirish"
            },
            {
                "savol": "Ko'ngil aynishi, qusish yoki quloqlarda jaranglagan shovqin bormi?",
                "maqsad": "Miyaning gipertenziv ensefalopatiyasi belgilarini baholash"
            },
            {
                "savol": "Doimiy ichadigan gipotenziv dorilaringizni bugun ichganmidingiz yoki qabul qilishni unutdingizmi?",
                "maqsad": "Dori qabul qilishdagi uzilishni aniqlash"
            },
            {
                "savol": "Yurak sohasida sanchiq yoki nafas qisishi bormi?",
                "maqsad": "Chap qorincha zo'riqishi va o'pka dimlanishini tekshirish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni baland yostiqqa, boshini ko'targan holda yarim o'tqazing. Oyoqlarini pastga tushiring (iliq oyoq vannasi yoki qonni periferiyaga tushirish). Bosimni har 15 daqiqada nazorat qiling."
        },
        "yakunlash": {
            "matn": "Bosimingiz 210/115 mmHg ekan, ancha baland. Hozir krizga qarshi shifokor tayinlagan dori vositasini til ostiga beramiz va ukol qilamiz. Bosimni asta-sekin tushiramiz. Xotirjam dam oling, hozir qaytib bosimingizni qayta o'lchayman.",
            "hisobot": "Bemor 52 yosh, asoratlangan gipertonik kriz (BP 210/115 mmHg), ensefalopatiya belgilari (ensa lo'qillashi, ko'z xiralashishi). Zudlik bilan gipotenziv terapiya boshlandi."
        }
    },

    "astma": {
        "nomi": "7. Bronxial Astma xuruji",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Ko'p gapirmang, faqat bosh silkib javob bersangiz ham bo'ladi.",
            "izoh": "Bemorda ekspirator hansirash kuchli, uni ko'p gapirtirib bo'lmaydi."
        },
        "savollar": [
            {
                "savol": "Nafas chiqarish qiyinlashyaptimi? Ko'kragingizda hushtaksimon xirillash ovozi eshitilyaptimi?",
                "maqsad": "Bronxospazm va ekspirator hansirashni baholash"
            },
            {
                "savol": "Xuruj nimadan boshlandi: lak hidi, bo'yoq, chang, sovuq havomi yoki allergen ta'siridami?",
                "maqsad": "Triggerni aniqlash va bemorni undan ajratish"
            },
            {
                "savol": "Yoningizda shaxsiy ingalyatoringiz (Salbutamol, Berodual) bormi? Bugun necha doza qabul qildingiz?",
                "maqsad": "Oldingi ingalyatsiya dozasini va uning samarasizligini tekshirish"
            },
            {
                "savol": "Balg'am ajralyaptimi yoki quruq qiyin yo'talmi?",
                "maqsad": "Shish va bronxial sekret xarakterini aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni majburiy o'tirgan (ortopnoe — qo'llarini tizzasiga tirab) holatida qoldiring, aslo yotqizmang! Toza havo oching, tor kiyimlarini yeching. Nebulayzer apparatini darhol tayyorlang."
        },
        "yakunlash": {
            "matn": "Sizga hozir nebulayzer orqali bronxni ochuvchi dori bilan nafas oldiramiz va kislorod beramiz. Xavotir olmang, nafas yo'llaringiz tezda ochiladi. Og'iz bilan sekin nafas chiqaring. Shifokor bilan birga yonidagimiz.",
            "hisobot": "Bemor 38 yosh, o'tkir bronxial astma xuruji, lak ta'sirida bo'g'ilish, og'ir ekspirator hansirash, SpO2 88%. Nebulayzer terapiyasi va kislorod ulandi."
        }
    },

    "pnevmoniya": {
        "nomi": "8. Pnevmoniya (O'pka yallig'lanishi)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Qaltirayotgan ekansiz, sizni iliq o'rab qo'yaman.",
            "izoh": "Isitma va qaltirash holatida bemorga psixologik va jismoniy qulaylik bering."
        },
        "savollar": [
            {
                "savol": "Tana haroratingiz nechagacha ko'tarildi? Necha kundan beri isitma qilyapsiz?",
                "maqsad": "Gipertermiya davomiyligi va darajasini aniqlash"
            },
            {
                "savol": "Yo'talganda qanday balg'am kelyapti: sariq, yashilsimon yoki zang rangidami?",
                "maqsad": "Bakterial destruksiya va balg'am xarakterini aniqlash"
            },
            {
                "savol": "Chuqur nafas olganingizda yoki yo'talganda ko'krak qafasining bir tomonida pichoq suqqandek sanchiq bormi?",
                "maqsad": "Plevrit asorati va og'riq xarakterini aniqlash"
            },
            {
                "savol": "Uyda biror antibiotik yoki isitma tushiruvchi dori qabul qildingizmi?",
                "maqsad": "Oldingi antibakterial terapiyani aniqlash"
            },
            {
                "savol": "Holsizlik, ishtahasizlik va ko'p terlash kuchlimi?",
                "maqsad": "Umumiy intoksikatsiya sindromini baholash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni qulay yotqizing, termometriya o'tkazing (39.3°C). Ko'p suyuqlik ichishini ta'minlang. Qon tahlillari va rentgen tekshiruviga tayyorlang."
        },
        "yakunlash": {
            "matn": "Isitma va yo'talingiz bo'yicha shifokorga hisobot berdim. Hozir qaltirashni to'xtatish uchun isitma tushiruvchi ukol qilamiz va shifokor ko'rigidan so'ng o'pka rentgeniga olib boramiz. Iliq dam oling, men hozir dorini olib kelaman.",
            "hisobot": "Bemor 35 yosh, o'ng tomonlama pnevmoniya gumoni: T 39.3°C, balg'amli yo'tal, plevral sanchiq, intoksikatsiya. Rentgenografiya va antibakterial terapiya tayinlandi."
        }
    },

    "insult": {
        "nomi": "9. Bosh miya insulti (O'tkir)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Iltimos, xavotir olmang, meni eshityapsizmi?",
            "izoh": "FAST (Face, Arms, Speech, Time) testini zudlik bilan qo'llang!"
        },
        "savollar": [
            {
                "savol": "Iltimos, menga qarab jilmayishga yoki tishingizni ko'rsatishga harakat qilib ko'ring-chi?",
                "maqsad": "FAST testi: Yuz asimmetriyasini (Face) tekshirish"
            },
            {
                "savol": "Ikkala qo'lingizni oldinga ko'taring va 5 soniya ushlab turing-chi?",
                "maqsad": "FAST testi: Qo'llardagi parez va zaiflikni (Arms) aniqlash"
            },
            {
                "savol": "Menga ism-familiyangizni yoki 'Bugun havo yaxshi' degan gapni qaytarib ayta olasizmi?",
                "maqsad": "FAST testi: Nutq buzilishi (Speech / dizartriya, afaziya)ni baholash"
            },
            {
                "savol": "Bu holat (qo'l-oyoq ishlamay qolishi) aynan soat nechada boshlandi?",
                "maqsad": "FAST testi: 'Terapevtik darcha' (Time: 4.5 soatlik trombolizis imkoniyati)"
            },
            {
                "savol": "Qon bosimingiz ilgari qancha bo'lgan? Qandli diabet yoki yurak xastaligingiz bormi?",
                "maqsad": "Xavf omillarini aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorning bosh qismini 30 darajaga ko'taring. Og'iz bo'shlig'ida so'lak yoki tish protezi bo'lsa tozalang (aspiratsiya xavfi!). Zudlik bilan MSKT/MRT ga tayyorlang."
        },
        "yakunlash": {
            "matn": "Siz mutlaqo xavotirlanmang, barcha aytganlaringizni vaqtiga qarab yozib oldim. Hozir zudlik bilan insult jamoasi va nevropatolog shifokor keladi, bosh miya tomografiyasiga (KT) olib boramiz. Hammasi yaxshi bo'ladi, biz sizning yoningizdamiz.",
            "hisobot": "Bemor 63 yosh, o'tkir bosh miya qon aylanishining buzilishi (insult) belgilari: o'ng tomonlama gemiparez, yuz asimmetriyasi, motor afaziya/dizartriya. Terapevtik darcha hisoblandi — zudlik bilan KT va nevrologiya!"
        }
    },

    "chayqalish": {
        "nomi": "10. Bosh miya chayqalishi (Travma)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Qayeringiz lat yedi, hozir o'rningizdan turmay turing.",
            "izoh": "Bo'yin umurtqalari shikastlangan bo'lishi mumkin, ortiqcha harakat qildirmang."
        },
        "savollar": [
            {
                "savol": "Boshingizni qayerga urib oldingiz? Yiqilgan paytingizni va undan keyingi voqealarni eslay olasizmi?",
                "maqsad": "Retrograd va anterograd amneziyani aniqlash"
            },
            {
                "savol": "Hushingizdan ketib qoldingizmi? Agar ketgan bo'lsangiz, qancha vaqt yotganingizni bilasizmi?",
                "maqsad": "Hush yo'qotish davomiyligini baholash"
            },
            {
                "savol": "Ko'nglingiz aynib, qayt qildingizmi? Necha marta qusish bo'ldi?",
                "maqsad": "Miya ichi bosimi oshishi va serebral qusishni aniqlash"
            },
            {
                "savol": "Ko'zingizga yorug'lik tushganda og'riq kuchayadimi? Quloqlaringizda jaranglash bormi?",
                "maqsad": "Fotofobiya va kranial nervlar zararlanishini tekshirish"
            },
            {
                "savol": "Bo'yningizda, orqangizda og'riq bormi, qo'l-oyoqlaringiz uvishib qolmadimi?",
                "maqsad": "Umurtqa pog'onasi travmasini istisno qilish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni to'liq tinch holatda yotqizing. Boshiga sovuq kompress qo'ying. Yorug'likni kamaytiring (xira xona). Travmatolog va neyroxirurg ko'rigiga tayyorlang."
        },
        "yakunlash": {
            "matn": "Iltimos, telefon yoki yorug'likka qaramang, ko'zingizni yumib yoting. Hozir rentgen va neyroxirurg ko'rigini tashkillashtiramiz. Bosh miyangizni shikastlanishdan asrash uchun barcha muolajalarni qilamiz. Hozir qaytaman.",
            "hisobot": "Bemor 28 yosh, zinadan yiqilish travmasi: bosh miya chayqalishi belgilari, qisqa muddatli hush yo'qotish, 2 karra serebral qusish, fotofobiya. Neyroxirurgik ko'rik kerak."
        }
    },

    "appenditsit": {
        "nomi": "11. O'tkir Appenditsit",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Qorningiz og'riyaptimi, qulay yotib oling.",
            "izoh": "Issiq grelka qo'yish yoki og'riqsizlantiruvchi ichirish mutlaqo man etiladi!"
        },
        "savollar": [
            {
                "savol": "Og'riq dastlab qorinning qaysi joyida boshlandi va keyin qayerga ko'chdi?",
                "maqsad": "Koxer simptomini (kindik atrofidan o'ng yonbosh sohasiga ko'chish) aniqlash"
            },
            {
                "savol": "Og'riq qanday xarakterda? Harakat qilganingizda, yo'talganingizda yoki o'ng tarafga yotganingizda kuchayadimi?",
                "maqsad": "Peritoneal qo'zg'alish va og'riq dinamikasini baholash"
            },
            {
                "savol": "Ko'ngil aynishi, qusish bo'ldimi? Ishtahangiz butunlay yo'qoldimi?",
                "maqsad": "O'tkir appenditsitning dispeptik sindromini aniqlash"
            },
            {
                "savol": "Og'riq boshlangandan keyin og'riqsizlantiruvchi dori (Analgin, Ketonal) ichmadingizmi?",
                "maqsad": "Klinik kartinani xiralashtiruvchi dorilarni tekshirish"
            },
            {
                "savol": "Tana haroratingiz ko'tarildimi, ichingiz kelishi qanday bo'lyapti?",
                "maqsad": "Subfebrilitet va ich kelishi o'zgarishlarini baholash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni chalqancha yotqizib, oyoqlarini tizzadan biroz buktiring (qorin devori bo'shashadi). Qoringa sovuq qo'ying (aslo issiq emas!). Ovqat va suv berishni to'xtating (och qorin operatsiya uchun zarur)."
        },
        "yakunlash": {
            "matn": "Og'riqni o'ng tomoningizda ushlab turganingizni ko'rdim. Hech qanday dori ichmang, qoringa qo'lingizni qattiq botirmang. Hozir shoshilinch navbatchi jarroh shifokorni chaqiraman va umumiy qon tahlili olamiz. Xavotir olmang, biz yordam beramiz.",
            "hisobot": "Bemor 25 yosh, o'tkir appenditsit gumoni: Koxer simptomi musbat (kindikdan o'ng yonboshga), T 37.8°C, qorin devori zo'riqishi. Shoshilinch xirurgik konsultatsiya!"
        }
    },

    "zaharlanish": {
        "nomi": "12. O'tkir Ovqatdan Zaharlanish",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Holsizlanib qolganga o'xshaysiz, sizga zudlik bilan yordam beramiz.",
            "izoh": "Suvsizlanish (degidratatsiya) darajasini baholang."
        },
        "savollar": [
            {
                "savol": "Oxirgi 6-12 soat ichida nimalar iste'mol qildingiz? Ko'chada tayyorlangan ovqat, go'sht, tort, tuxum yoki konserva yeganmidingiz?",
                "maqsad": "Zaharlanish sababchisi bo'lgan ovqat manbasini aniqlash"
            },
            {
                "savol": "Qusish necha marta bo'ldi? Ko'nglingiz tinimsiz ayniyaptimi?",
                "maqsad": "Oshqozon bo'shashishi va intoksikatsiya darajasini baholash"
            },
            {
                "savol": "Ich ketishi (diareya) necha marta bo'ldi? Suvli, ko'p miqdordami, qon yoki shilliq bormi?",
                "maqsad": "Enterit, kolit yoki dizenteriya xususiyatlarini aniqlash"
            },
            {
                "savol": "Og'zingiz qurib qolishi, kuchli chanqash, ko'zlar cho'kishi yoki qo'l-oyoq tortishishi bormi?",
                "maqsad": "Gipovolemik degidratatsiya va elektrolitlar yo'qotilishini aniqlash"
            },
            {
                "savol": "Siz bilan birga ovqatlangan boshqa odamlarda ham shunday belgilar bormi?",
                "maqsad": "Ommaviy toksikoinfeksiyani aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni yotqizing. Qusish paytida boshi yonga burilgan bo'lsin. Rehidratsiya (Regidron, fizioeritma) infuziyasini tayyorlang. Oshqozonni yuvish zaruriyatini shifokor bilan kelishing."
        },
        "yakunlash": {
            "matn": "Ko'p suyuqlik yo'qotganingiz uchun tanangiz suvsizlangan. Hozir zudlik bilan tomir orqali rehidratsion eritmalar (osma ukol) ulaymiz va oshqozonni tozalaymiz. Tez orada o'zingizni ancha yengil his qilasiz. Hozir muolajani boshlaymiz.",
            "hisobot": "Bemor 30 yosh, o'tkir oziq-ovqat toksikoinfeksiyasi, 2-darajali degidratatsiya, 5 marta qusish, 7 marta diareya, T 38.2°C. Zudlik bilan infuzion rehidratsiya boshlandi."
        }
    },

    "gipoglikemiya": {
        "nomi": "13. Gipoglikemiya (Qand tushishi)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Qo'llaringiz titrayapti, chuqur nafas oling.",
            "izoh": "Qondagi glyukoza keskin tushgan, bemor komaga tushmasligi uchun tezkor choralar ko'ring."
        },
        "savollar": [
            {
                "savol": "Qandli diabet bo'yicha hisobda turasizmi? Insulin yoki qand tushiruvchi tabletka (metformin, glibenklamid) qabul qilasizmi?",
                "maqsad": "Diabet va gipoglikemik preparatlar anamnezini aniqlash"
            },
            {
                "savol": "Bugun dori yoki insulin olgandan keyin o'z vaqtida ovqatlandingizmi?",
                "maqsad": "Gipoglikemiyaning eng keng tarqalgan sababini aniqlash"
            },
            {
                "savol": "O'zingizda qanday belgilar sezyapsiz: kuchli sovuq ter, titroq, qorin ochishi yoki bosh aylanishi bormi?",
                "maqsad": "Adrenergik va neyroglikopenik simptomlarni tasdiqlash"
            },
            {
                "savol": "Hozir qoningizdagi qand miqdorini glyukometrda o'lchaymiz, biroz chidaysiz, xo'pmi?",
                "maqsad": "Ekspress glyukometriya o'tkazish (natija 2.1 mmol/l)"
            }
        ],
        "parvarish": {
            "tavsiya": "Agar bemor hushida bo'lsa: darhol tez so'riluvchi shirin choy, 3-4 bo'lak qand yoki shirin sharbat ichiring. Agar hushidan ketayotgan bo'lsa: darhol vena ichiga 40% li Glyukoza eritmasi yuborishga tayyorlang."
        },
        "yakunlash": {
            "matn": "Glyukometringiz qand miqdori 2.1 mmol/l ga tushib ketganini ko'rsatdi, bu juda past. Hozir sizga shirin sharbat beraman va vena ichiga glyukoza eritmamizni ulaymiz. 5-10 daqiqada titroq to'xtab, o'zingizga kelasiz. Xavotir olmang!",
            "hisobot": "Bemor 45 yosh, qandli diabet, ovqatlanmaslik fonida o'tkir gipoglikemiya (glyukoza 2.1 mmol/l), titroq, gipergidroz. 40% glyukoza yuborilmoqda."
        }
    },

    "allergiya": {
        "nomi": "14. Anafilaktik shok (O'tkir allergiya)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Nafasingiz qisilib qoldimi, men yoningizdaman!",
            "izoh": "Bu favqulodda holat! Adrenalin zudlik bilan tayyor bo'lishi kerak!"
        },
        "savollar": [
            {
                "savol": "Sizga hozirgina biror ukol (antibiotik, og'riqsizlantiruvchi) qilindimi yoki hasharot chaqdimi?",
                "maqsad": "Allergen ta'sirini darhol aniqlash va to'xtatish"
            },
            {
                "savol": "Tomog'ingizda tiqilish, tilingiz shishishi yoki yutinish qiyinlashishi sezilyaptimi?",
                "maqsad": "Halqum shishi (asfiksiya xavfi)ni aniqlash"
            },
            {
                "savol": "Badaningiz qichishyaptimi, qizil toshmalar (eshakemi) toshdimi?",
                "maqsad": "Allergik dermatologik belgilarni ko'zdan kechirish"
            },
            {
                "savol": "Bosh aylanishi, ko'z qorong'ilashishi bormi?",
                "maqsad": "Gemodinamik kollaps va bosim keskin tushishini aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Allergen kiritilishini darhol to'xtating! Bemorni oyoqlarini ko'targan holda gorizontal yotqizing. 0.1% Adrenalin (Epinefrin) 0.5 ml mushak orasiga (sonning oldingi-yon qismiga) zudlik bilan yuboriladi. Kislorod ulanadi."
        },
        "yakunlash": {
            "matn": "Sizda allergik reaksiya boshlandi. Hozir darhol oyog'ingizga adrenalin va gormon ukolini qilamiz, nafasingiz ochiladi va bosimingiz ko'tariladi. Hech qo'rqmang, barcha dori vositalarimiz tayyor, reanimatolog yoningizda!",
            "hisobot": "Bemor 33 yosh, novokain inyeksiyasidan so'ng anafilaktik shok: til va tomoq shishi, stridor, toshma, BP 70/40 mmHg. Zudlik bilan Adrenalin 0.5 ml mushak ichiga va Deksametazon yuborildi."
        }
    },

    "gipoksiya": {
        "nomi": "15. O'tkir Gipoksiya & Bronxospazm",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Qimirlamang, gapirishga urinmang, chuqur nafas oling.",
            "izoh": "SpO2 juda past (74%), bemorda o'tkir kislorod tanqisligi bor."
        },
        "savollar": [
            {
                "savol": "Havo umuman yetmayotgandek tuyulyaptimi? Ko'kragingizda qisilish bormi?",
                "maqsad": "Gipoksiya va bronxial obstruktsiya og'irligini aniqlash"
            },
            {
                "savol": "Barmoqlaringiz yoki lablaringiz ko'karib ketganini sezdingizmi?",
                "maqsad": "Markaziy va periferik sianozni tekshirish"
            },
            {
                "savol": "Bu holat qachon boshlandi? Biror gaz, tutun yoki allergen bilan nafas olmadingizmi?",
                "maqsad": "Toksik yoki allergik bronxospazm sababini aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni yarim o'tirgan holatga keltiring. Darhol yuqori oqimli (10-15 l/min) kislorod niqobini taqing. Pulsoksimetrni barmog'iga ulab SpO2 ni kuzating. Bronxolitik ingalyatsiyasini boshlang."
        },
        "yakunlash": {
            "matn": "Saturatsiyangiz 74% ga tushibdi, qoningizda kislorod yetishmayapti. Hozir kislorod niqobini taqdim, tinch va chuqur nafas oling. Kislorod ko'tarilgach o'zingizni ancha yaxshi his qilasiz. Reanimatolog bilan birga yoningizdamiz.",
            "hisobot": "Bemor 38 yosh, o'tkir gipoksiya, SpO2 74%, og'ir sianoz va bronxospazm. Yuqori oqimli kislorodoterapiya va bronxolitiklar boshlandi."
        }
    },

    "shok": {
        "nomi": "16. Gipovolemik Shok / Qon yo'qotish",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Iltimos, xotirjam yoting, qimirlamang.",
            "izoh": "Kuchli qon yo'qotish yoki gipovolemiya, bosim 65/35, puls 145 bpm."
        },
        "savollar": [
            {
                "savol": "Qayeringizdan qon ketyapti? Shikastlanish, jarohat yoki qon qusish bo'ldimi?",
                "maqsad": "Qon ketish manbasini va turini (tashqi/ichki) aniqlash"
            },
            {
                "savol": "Ko'zingiz qorong'ilashib, qulog'ingiz shang'illayaptimi? Kuchli chanqoq sezyapsizmi?",
                "maqsad": "Aylanib yuruvchi qon hajmi (AYQH) tanqisligini aniqlash"
            },
            {
                "savol": "Qorningizda qattiq og'riq bormi, najasingiz qora qatronga o'xshab kelmadimi?",
                "maqsad": "Yashirin oshqozon-ichak qon ketishini tekshirish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni Trendelenburg holatiga keltiring (oyoqlarni 30 gradus ko'tarish). Qon ketish manbasi bo'lsa jgut yoki bosuvchi bog'lam qo'ying. Ikkita yirik periferik venaga kateter o'rnatib kristalloidlar (fizioeritma, Ringer) oqim bilan yuboriladi."
        },
        "yakunlash": {
            "matn": "Bosimingiz juda tushib ketgan, 65/35 mmHg. Hozir darhol tomiringizdan qon o'rnini bosuvchi eritmalarni oqim bilan yuboramiz. Shifokorlar va qon quyish bo'limi ogohlantirildi. Qimirlamay yoting, sizni qutqaramiz!",
            "hisobot": "Bemor 40 yosh, gipovolemik / gemorragik shok 3-daraja: BP 65/35 mmHg, HR 145 bpm, ipsimon puls, sovuq ter. Zudlik bilan 2 ta venoz yo'l ochilib massiv infuziya boshlandi."
        }
    },

    "opioid": {
        "nomi": "17. Opioid Koma & Toksik Bradipnoe",
        "is_child": False,
        "salomlashish": {
            "matn": "Bemorga murojaat: 'Meni eshityapsizmi? Ismingiz nima?' (Bemor komatoz, javob bermaydi).",
            "izoh": "Bemor hushsiz, chuqur komada, nafas daqiqasiga atigi 4 marta, qorachiqlar nuqtadek toraygan."
        },
        "savollar": [
            {
                "savol": "(Hamrohiga/atrofdagilarga): Bemor biror og'riqsizlantiruvchi, sedativ yoki giyohvandlik moddasi qabul qilganmidi?",
                "maqsad": "Opioid toksikologik moddasini aniqlash"
            },
            {
                "savol": "(Ko'rik): Qorachiqlarining kengligi qanday? Ignadan qolgan izlar bormi?",
                "maqsad": "Klassik opioid triadasini (koma, bradipnoe, mioz) tekshirish"
            },
            {
                "savol": "(Ko'rik): Nafas yo'llari ochiqmi, tili orqaga ketib qolmaganmi?",
                "maqsad": "Mexanik asfiksiyani oldini olish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorning nafas yo'lini havo o'tkazgich (Guedel naychasi) bilan oching. Ambu qopi orqali sun'iy nafas bering. Nalokson 0.4 - 0.8 mg vena ichiga shoshilinch yuboriladi."
        },
        "yakunlash": {
            "matn": "Bemor hushsiz, o'tkir gipoventilyatsiyada. Zudlik bilan Nalokson antidotini kiritamiz va Ambu qopi bilan o'pkani sun'iy shamollatamiz. Reanimatolog chaqirildi.",
            "hisobot": "Bemor 40 yosh, toksik opioid koma, nafas 4 ta/daq, SpO2 62%, qorachiqlar tor (mioz). Nalokson 0.4 mg i/v yuborildi, sun'iy shamollatish boshlandi."
        }
    },

    "anafilaksiya": {
        "nomi": "18. Anafilaktik Shok (O'tkir Allergiya)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Hech qorqmang, nafas yo'llaringizni hozir ochamiz!",
            "izoh": "Tezkor allergik asfiksiya xavfi, dori ta'sirini darhol to'xtatish."
        },
        "savollar": [
            {
                "savol": "Inyeksiya yoki dori qabulidan so'ng qancha vaqt o'tib tomoq qisishi boshlandi?",
                "maqsad": "Reaksiya tezligi va shok og'irligini aniqlash"
            },
            {
                "savol": "Nafas olayotganda shovqinli, xirillagan ovoz bormi?",
                "maqsad": "Halqum shishi va laringospazmni baholash"
            },
            {
                "savol": "Badaningiz qizib, qichishish kuchaydimi?",
                "maqsad": "Generalizatsiyalangan eshakemi mavjudligini tekshirish"
            }
        ],
        "parvarish": {
            "tavsiya": "Infuziyani darhol to'xtatib ignani tomirda qoldiring (venoz yo'l uchun). Epinefrin (Adrenalin) 0.5 ml mushak ichiga zudlik bilan qilinadi. Deksametazon 8-16 mg va Dimedrol kiritiladi."
        },
        "yakunlash": {
            "matn": "Adrenalin ukolini qildik, nafas olishingiz hozir yengillashadi. Kislorod niqobini taqdik. Reanimatsiya brigadasi yoningizda. Barchasi nazorat ostida, xotirjam bo'ling.",
            "hisobot": "Bemor 33 yosh, o'tkir anafilaktik shok: halqum shishi, stridor, arterial gipotoniya (BP 70/40). Epinefrin va glyukokortikoidlar kiritildi."
        }
    },

    "asystole": {
        "nomi": "19. Asistoliya / Yurak to'xtashi",
        "is_child": False,
        "salomlashish": {
            "matn": "Bemorga baland ovozda murojaat: 'Meni eshityapsizmi?! Ko'zingizni oching!' — (Bemor hushsiz, javob bermaydi).",
            "izoh": "YURAK TO'XTASHI! Darhol reanimatsion harakatlarni boshlang!"
        },
        "savollar": [
            {
                "savol": "(Harakat): Uyqu arteriyasida (bo'yinda) puls bormi? (10 soniya ichida tekshiring)",
                "maqsad": "Markaziy puls yo'qligini aniqlash (Puls 0 BPM)"
            },
            {
                "savol": "(Harakat): Ko'krak qafasi harakatlanyaptimi, nafas bormi?",
                "maqsad": "Nafas yo'qligi yoki agonal nafasni tasdiqlash"
            },
            {
                "savol": "(Chaqiruv): 'Yordam bering! Reanimatsiya xonasiga zudlik bilan shifokor va defibrillyator kerak!'",
                "maqsad": "Reanimatsion brigadani chaqirish (Code Blue)"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni zudlik bilan qattiq yuzaga (polga yoki reanimatsion taxtaga) yotqizing! Ko'krak qafasi kompressiyasini boshlang: 30 ta bosish (tezligi 100-120/daq, chuqurligi 5-6 sm) va 2 ta nafas (30:2). Adrenalin 1 mg vena ichiga har 3-5 daqiqada tayyorlanadi."
        },
        "yakunlash": {
            "matn": "Yurak qon aylanishi to'xtagan. Yurak-o'pka reanimatsiyasi (SDR/CPR) zudlik bilan boshlandi. Reanimatsion jamoa defibrillyator bilan yetib keldi.",
            "hisobot": "Bemor 40 yosh, klinik o'lim / asistoliya holati (puls 0, nafas 0). Protokol bo'yicha bazaviy va ixtisoslashgan reanimatsiya (BLS/ACLS 30:2) amalga oshirilmoqda."
        }
    },

    "bola_krup": {
        "nomi": "20. Bolalar Krupi (Nafas qisishi & Bo'g'ilish)",
        "is_child": True,
        "salomlashish": {
            "matn": "Salom Madinaxon, qo'rqma qizalog'im, men senga yordam beradigan hamshira opangman. Seni hech kim xafa qilmaydi, xo'pmi?",
            "izoh": "Pediatriya bemori (6 yosh). Ovozingiz juda muloyim, mehrli va xotirjam bo'lsin. Onasiga ham taskin bering."
        },
        "savollar": [
            {
                "savol": "Madinaxon, tomog'ing qichishyaptimi yoki yutinish qiyin bo'lyaptimi, ko'rsatib ber-chi?",
                "maqsad": "Bolaning subyektiv holatini o'rganish"
            },
            {
                "savol": "(Onasiga): Bo'g'ilish xuruji aynan qachon boshlandi? Kechasi to'satdan 'it hurishiga' o'xshash quruq yo'tal paydo bo'ldimi?",
                "maqsad": "Stenozlanuvchi laringotraxeit (krup) xarakterini tasdiqlash"
            },
            {
                "savol": "(Onasiga): Qizaloqning ovozi qanchalik bo'g'ilib qoldi? Nafas olganda bo'yin chuqurchasi ichkariga tortilyaptimi?",
                "maqsad": "Laringeal stenoz darajasini (stridor, inspirator dispnoe) aniqlash"
            },
            {
                "savol": "(Onasiga): Tana harorati ko'tarildimi? Shamollash yoki virusli infeksiya belgilari bo'lganmidi?",
                "maqsad": "Paragripp yoki boshqa O'RVI etiologiyasini aniqlash"
            },
            {
                "savol": "(Onasiga): Oldin krup xuruji bo'lganmi? Uyda bugun biror dori yoki ingalyatsiya qildingizmi?",
                "maqsad": "Oldingi anamnez va qo'llanilgan muolajalarni bilish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bolani onasining quchog'ida qoldiring (onadan ajratish yig'latadi va bo'g'ilishni 2 barobar kuchaytiradi!). Xonani salqin, nam havo bilan ta'minlang. Pulmikort (Budesonid) nebulayzer orqali zudlik bilan ingalyatsiya qilinadi."
        },
        "yakunlash": {
            "matn": "Madinaxon, sen juda aqlli qizaloqsan! Qara, hozir mana bu sehrli apparat (nebulayzer) orqali salqin tuman bilan nafas olamiz, tomog'ing ochilib, oson nafas olasan. Onajoning yoningda bo'ladi. Men doktor amakingni chaqirib kelyapman, tezda tuzalib ketasan!",
            "hisobot": "Bemor Madina (6 yosh), o'tkir stenozlanuvchi laringotraxeit (krup, 2-darajali stenoz): dag'al huruvchi yo'tal, stridor, inspirator nafas qisishi, T 38.3°C. Nebulayzerda Budesonid va kislorod berildi."
        }
    }
}


def generate_fallback_template(disease_key: str, disease_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Qo'lda batafsil yozilmagan kasalliklar (21-112) uchun profil ma'lumotlaridan
    kelib chiqib yuqori sifatli dinamik klinik shablon hosil qiladi.
    """
    nomi = disease_data.get("nomi", "Klinik Holat")
    kategoriya = disease_data.get("kategoriya", "Umumiy tibbiyot")
    tavsif = disease_data.get("tavsif", "")
    bemor_info = disease_data.get("bemor_info", "")
    is_child = disease_data.get("is_child", False)

    # Ism va yoshni ajratib olish
    name_match = re.search(r'Bemor:\s*([A-Za-z\']+)', bemor_info)
    patient_name = name_match.group(1) if name_match else ("Kichkintoy" if is_child else "Bemor")
    
    age_match = re.search(r'(\d+)\s*yosh', bemor_info + " " + tavsif)
    age = age_match.group(1) if age_match else ("Bolalar yoshi" if is_child else "Katta yosh")

    if is_child:
        salomlashish = {
            "matn": f"Salom {patient_name}, men senga yordam beradigan hamshira opangman. Qayering bezovta qilyapti, aytib ber-chi?",
            "izoh": f"Bolalar bo'limi bemori ({age} yosh). Mehrli va sokin ovozda gapiring, onasini yonginasida ushlang."
        }
        savollar = [
            {
                "savol": f"{patient_name}, o'zingni qanday his qilyapsan? Og'riyotgan joyingni qo'ling bilan ko'rsatib bera olasanmi?",
                "maqsad": "Bolaning subyektiv holati va og'riq sohasini aniqlash"
            },
            {
                "savol": "(Onasiga/Otasiga): Bola qachondan beri bezovta bo'lyapti? Bu holat to'satdan boshlandimi yoki asta-sekinmi?",
                "maqsad": "Kasallik dinamikasi va boshlanish vaqtini o'rganish"
            },
            {
                "savol": f"Tana harorati ko'tarildimi? Qaltirash, qusish yoki ovqatdan bosh tortish bormi?",
                "maqsad": f"{kategoriya} bo'yicha intoksikatsiya va umumiy simptomlarni aniqlash"
            },
            {
                "savol": "Oldinroq biror dori berdingizmi? Bolaning biror narsaga allergiyasi bormi?",
                "maqsad": "Medikamentoz va allergik anamnezni tekshirish"
            }
        ]
        parvarish = {
            "tavsiya": f"Bolani qulay va xotirjam holatga keltiring. Termometriya, puls va saturatsiyani o'lchang. Pediatrik tekshiruvga tayyorlang."
        }
        yakunlash = {
            "matn": f"{patient_name}, sen juda botir va aqlli bolasan! Xavotir olma, hozir shifokor amaking/opang bilan birga senga yordam beramiz va tezda tuzalib ketasan. Onang bilan bir oz dam olib tur, xo'pmi?",
            "hisobot": f"Bemor {patient_name} ({age} yosh), tashxis: {nomi}. Tavsif: {tavsif}. Birlamchi tekshiruv o'tkazildi, pediatr ko'rigi zarur."
        }
    else:
        salomlashish = {
            "matn": f"Assalomu alaykum! Men navbatchi hamshiraman. O'zingizni erkin tuting, sizga yordam berish uchun keldim.",
            "izoh": f"Katta yoshli bemor ({age} yosh). Rasmiy va professional muloqot qiling."
        }
        savollar = [
            {
                "savol": "Sizni aynan nima bezovta qilyapti? Og'riq yoki noqulaylik qachon boshlandi?",
                "maqsad": "Asosiy shikoyat va kasallik xronologiyasini aniqlash"
            },
            {
                "savol": "Og'riq yoki noqulaylik qanday xarakterda va qayerga tarqalyapti?",
                "maqsad": f"{kategoriya} patologiyasi simptomlarini aniqlashtirish"
            },
            {
                "savol": "Ushbu holat boshlanishidan oldin biror dori qabul qildingizmi yoki biror noxush omil ta'sir qildimi?",
                "maqsad": "Provokatsion omillar va oldingi muolajalarni bilish"
            },
            {
                "savol": "Ilgari sizda shunday kasallik kuzatilganmi? Surunkali xastaliklaringiz yoki allergiyangiz bormi?",
                "maqsad": "Somatik va allergik anamnezni to'plash"
            }
        ]
        parvarish = {
            "tavsiya": f"Bemorni qulay holatga o'tqazing/yotqizing. Qon bosimi, puls, SpO2 ko'rsatkichlarini o'lchang. {kategoriya} bo'yicha profilaktik parvarish qiling."
        }
        yakunlash = {
            "matn": f"Barcha aytgan ma'lumotlaringizni qayd etdim. Hozir siz tinch, ortiqcha harakat qilmasdan dam oling. Men zudlik bilan navbatchi shifokorga xabar beraman va kerakli choralarni ko'ramiz. Rahmat, hozir kelaman.",
            "hisobot": f"Bemor ({age} yosh), tashxis: {nomi}. Klinik holat: {tavsif}. Vital parametrlar o'lchandi, shifokor konsultatsiyasi talab etiladi."
        }

    return {
        "nomi": nomi,
        "is_child": is_child,
        "salomlashish": salomlashish,
        "savollar": savollar,
        "parvarish": parvarish,
        "yakunlash": yakunlash
    }


def get_dialogue_template(disease_key: str, diseases_dict: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Berilgan kasallik kaliti bo'yicha shablonni qaytaradi.
    Agar DETAILED_TEMPLATES da bo'lsa, o'shani qaytaradi.
    Aks holda, diseases_dict (KASALLIKLAR) asosida dinamik generatsiya qiladi.
    """
    if disease_key in DETAILED_TEMPLATES:
        return DETAILED_TEMPLATES[disease_key]
    
    if diseases_dict and disease_key in diseases_dict:
        return generate_fallback_template(disease_key, diseases_dict[disease_key])
    
    # Standart zaxira shablon
    return {
        "nomi": "Klinik Holat",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum, men navbatchi hamshiraman. O'zingizni qanday his qilyapsiz?",
            "izoh": "Bemor bilan muloqot o'rnating."
        },
        "savollar": [
            {
                "savol": "Sizni aynan nima bezovta qilyapti, qayeringiz og'riyapti?",
                "maqsad": "Shikoyatni aniqlash"
            },
            {
                "savol": "Bu og'riq qachon boshlandi va oldin dori ichdingizmi?",
                "maqsad": "Anamnezni o'rganish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni qulay joylashtiring, hayotiy ko'rsatkichlarni tekshiring."
        },
        "yakunlash": {
            "matn": "Siz xotirjam yoting, men hozir navbatchi shifokorni chaqiraman. Rahmat!",
            "hisobot": "Bemor birlamchi ko'rikdan o'tkazildi, shifokor ko'rigi rejalashtirildi."
        }
    }


def get_all_templates_dict(diseases_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Barcha 112 ta kasallik uchun shablonlar lug'atini hosil qilib beradi.
    """
    all_dict = {}
    for k, v in diseases_dict.items():
        if k in DETAILED_TEMPLATES:
            all_dict[k] = DETAILED_TEMPLATES[k]
        else:
            all_dict[k] = generate_fallback_template(k, v)
    return all_dict
