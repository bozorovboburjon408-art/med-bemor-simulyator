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
    },

    "bola_appenditsit": {
        "nomi": "21. Bolalarda O'tkir Qorin Og'rig'i (Appenditsit)",
        "is_child": True,
        "salomlashish": {
            "matn": "Salom Zilolaxon, qo'rqma jonim, men hamshira opangman. Qayering og'riyapti, ko'rsata olasanmi?",
            "izoh": "Pediatriya bemori (8 yosh). Bolaga mehrli gapiring, 'hamshira opa' deb ayting, onasiga ham taskin bering."
        },
        "savollar": [
            {
                "savol": "Zilolaxon, qorning qayerda og'riyapti? Kindiging atrofidami yoki o'ng tomoning pastidami?",
                "maqsad": "Lokalizatsiya va Koxer simptomi (kindikdan o'ng yonboshga ko'chish)"
            },
            {
                "savol": "Og'riq pichoqdek sanchyaptimi? O'ng oyog'ingni bukkanda yoki qimirlatganda og'riq kuchayadimi?",
                "maqsad": "Psoas-simptomi va peritoneal ta'sirlanishni aniqlash"
            },
            {
                "savol": "(Onasiga): Qusish yoki ko'ngil aynishi bo'ldimi? Necha marta qayt qildi?",
                "maqsad": "Appenditsitdagi dispeptik sindromni baholash"
            },
            {
                "savol": "(Onasiga): Qorin og'rig'i boshlangandan keyin isitmasi ko'tarildimi (37.8°C)? Og'riqsizlantiruvchi dori bermadingizmi?",
                "maqsad": "Subfebrilitet va dori anamnezini aniqlash"
            },
            {
                "savol": "(Onasiga): Ich kelishi qanday bo'ldi, qotish yoki ich ketish kuzatildimi?",
                "maqsad": "Ichak peristaltikasi va intoksikatsiyani tekshirish"
            }
        ],
        "parvarish": {
            "tavsiya": "Qizaloqni o'ng oyog'ini tizzadan biroz bukkan holda chalqancha yotqizing. Qoringa issiq grelka qo'yish yoki dori ichirish qat'iyan taqiqlanadi! Bolalar jarrohini zudlik bilan chaqiring."
        },
        "yakunlash": {
            "matn": "Zilolaxon, sen juda sabrli va chiroyli qizsan! Qorningga qo'lingni qattiq bosma, qimirlamay yotib tur. Hozir doktor amaking keladi, birgalikda seni ko'rib og'riqni qoldiramiz, xo'pmi? Barakalla!",
            "hisobot": "Bemor Zilola (8 yosh), o'tkir appenditsit gumoni: o'ng yonbosh sohasida o'tkir sanchiq, Koxer va psoas simptomi musbat, T 37.8°C. Bolalar jarrohi zudlik bilan chaqirildi."
        }
    },

    "bola_allergiya": {
        "nomi": "22. Bolalar Allergiyasi & Yuz Shishi (Kvinke)",
        "is_child": True,
        "salomlashish": {
            "matn": "Salom Rayhonaxon! Qo'rqma qizalog'im, men hamshira opangman. Nafas olishing qiyinlashmayaptimi?",
            "izoh": "Pediatriya bemori (7 yosh). Kvinke shishi va bo'g'ilish xavfi bor, nafas yo'llarini tezkor nazorat qiling."
        },
        "savollar": [
            {
                "savol": "Rayhonaxon, lablaring yoki ko'zlaring qichishyaptimi? Tomog'ingda tiqilish yoki achishish bormi?",
                "maqsad": "Halqum shishi va asfiksiya xavfini aniqlash"
            },
            {
                "savol": "(Onasiga): Qizaloq bugun nimalar yegandi? Mandarin, shokolad yoki yong'oq iste'mol qildimi?",
                "maqsad": "Allergen manbasini aniqlash"
            },
            {
                "savol": "(Onasiga): Yuz va qovoqlar shishi qancha vaqt ichida paydo bo'ldi? Shish kattalashyaptimi?",
                "maqsad": "Kvinke shishi dinamikasini baholash"
            },
            {
                "savol": "Badaningda qizil toshmalar, qichishish bormi, ko'rsat-chi?",
                "maqsad": "Eshakemi (urtikariya) belgilarini ko'zdan kechirish"
            },
            {
                "savol": "(Onasiga): Oldin biror dori yoki ovqatga allergiya bo'lganmi? Uyda antigistamin (Suprastin, Fenistil) berdingizmi?",
                "maqsad": "Allergik anamnezni tekshirish"
            }
        ],
        "parvarish": {
            "tavsiya": "Allergen ta'sirini darhol to'xtating. Bolani yarim o'tirgan holatga keltiring. Kislorod ulanadi. Prednizolon yoki Deksametazon, shuningdek antigistamin preparati shifokor ko'rsatmasi bilan tayyorlanadi."
        },
        "yakunlash": {
            "matn": "Rayhonaxon, sen juda aqlli qizaloqsan! Hozir mana bu kichkina dori bilan yuzingdagi shishlar qaytadi, ko'zlaring ochilib, qichishish to'xtaydi. Xavotir olma, onang yoningda. Hozir kelaman!",
            "hisobot": "Bemor Rayhona (7 yosh), o'tkir allergik Kvinke shishi: lab va periorbital shish, yuz eritemasi, toshma. Halqum shishi xavfi bor, zudlik bilan antiallergik terapiya boshlandi."
        }
    },

    "bola_shamollash": {
        "nomi": "23. Bolalar O'tkir Isitmasi (39.5°C Gipertermiya)",
        "is_child": True,
        "salomlashish": {
            "matn": "Salom Madinaxon! Men hamshira opangman, seni issig'ingni tushirishga yordam beraman, xo'pmi?",
            "izoh": "Pediatriya bemori (6 yosh). Yuqori febril harorat (39.5°C) fonida febril talvasa (sudorogi) xavfini oldini oling."
        },
        "savollar": [
            {
                "savol": "Madinaxon, boshing og'riyaptimi, tomog'ing yutinganda og'riyaptimi?",
                "maqsad": "Bosh og'rig'i va O'RVI kataral belgilarini aniqlash"
            },
            {
                "savol": "(Onasiga): Tana harorati 39.5°C ga qachon chiqdi? Bola qaltirab sovuq qotyaptimi yoki badani qizib ketganmi?",
                "maqsad": "'Oq' yoki 'qizil' gipertermiyani ajratish"
            },
            {
                "savol": "(Onasiga): Bolada qo'l-oyoqlar tortishishi, ko'zlarining yuqoriga ketib qolishi (talvasa) kuzatilmadimi?",
                "maqsad": "Febril tutqanoqni istisno qilish"
            },
            {
                "savol": "(Onasiga): Qanday isitma tushiruvchi dori (Paratsetamol, Ibuprofen) berdingiz va qachon berildi?",
                "maqsad": "Dori dozasi va vaqtini aniqlash"
            },
            {
                "savol": "(Onasiga): Bola suyuqlik (suv, choy) ichyaptimi yoki qusib tashlayaptimi?",
                "maqsad": "Degidratatsiya va intoksikatsiya darajasini baholash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bolani qalin kiyimlardan bo'shating (o'rab tashlamang!). Agar qo'l-oyoqlari issiq bo'lsa: iliq suv bilan jismoniy sovutish (peshana, bo'yin, chov sohasiga kompress). Paratsetamol/Ibuprofen siropi yoki shamchasi qo'llaniladi."
        },
        "yakunlash": {
            "matn": "Madinaxon, jonim, peshanangga mana bu salqin dastro'molni qo'yamiz va mazali sirop ichiramiz. Issig'ing tezda tushib, yana o'ynab ketasan, xo'pmi? Onajoning bilan yotib tur, hozir dorini olib kelaman.",
            "hisobot": "Bemor Madina (6 yosh), o'tkir gipertermiya sindromi: T 39.5°C, intoksikatsiya, qaltirash. Jismoniy sovutish va antipiretik terapiya boshlandi."
        }
    },

    "yurak_yetishmovchiligi": {
        "nomi": "24. Surunkali Yurak Yetishmovchiligi (Dekompenzatsiya)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Sobir ota. Men navbatchi hamshiraman. Holsizlanib qolganga o'xshaysiz, nafas olishingizni rostlab oling.",
            "izoh": "Katta yoshli bemor (67 yosh). Yurak yetishmovchiligi dekompenzatsiyasi, o'tirgan holatda ortopnoe."
        },
        "savollar": [
            {
                "savol": "Sobir ota, nafas qisishi qachondan beri kuchaydi? Yotganingizda bo'g'ilish kuchayib, baland yostiqqa suyanib o'tirishga majbur bo'lyapsizmi?",
                "maqsad": "Ortopnoe va o'pka dimlanishini baholash"
            },
            {
                "savol": "Oyoqlaringizdagi shish qachon paydo bo'ldi? Paypoq yoki poyabzalingiz siqib, ertalab ham qaytmayaptimi?",
                "maqsad": "Katta qon aylanish doirasidagi periferik venoz dimlanish"
            },
            {
                "savol": "Ko'kragingizda og'irlik, quruq yo'tal yoki kechasi bo'g'ilib uyg'onish xurujlari bo'lyaptimi?",
                "maqsad": "Yurak astmasi paroksizmini aniqlash"
            },
            {
                "savol": "Siyishingiz kamayib ketmadimi? Siydik haydovchi (Furosemid, Torasemid) dorilaringizni ichyapsizmi?",
                "maqsad": "Diurez va diuretiklar nazoratini tekshirish"
            },
            {
                "savol": "Yurak uchun qanday dorilar (Digoksin, Kardiomagnil, Enalapril) qabul qilasiz?",
                "maqsad": "Kardiologik dori anamnezini aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni baland yostiqda, yarim o'tirgan (ortopnoe) holatga keltiring. Oyoqlarini pastga tushiring (yurakka venoz oqimni kamaytirish). Namlangan kislorod ulanadi. Arterial bosim, puls va SpO2 o'lchanadi."
        },
        "yakunlash": {
            "matn": "Sobir ota, hech xavotirlanmang. Sizni balandroq suyab qo'ydim, nafas olishingiz ancha yengillashadi. Hozir kardiolog shifokor keladi, suyuqlikni haydaydigan dori va kislorod beramiz. Sekin, chuqur nafas oling.",
            "hisobot": "Bemor Sobir ota (67 yosh), surunkali yurak yetishmovchiligi (IIB-III bosqich) dekompenzatsiyasi: ortopnoe, ikkala boldirda massiv shishlar, taxipnoe, SpO2 89%. Kardiologik yordam zarur."
        }
    },

    "paroksizmal_taxikardiya": {
        "nomi": "25. Paroksizmal Supraventrikulyar Taxikardiya (PSVT)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Qo'rqmang, xotirjam bo'ling, yuragingizni ritmini hozir tekshiramiz.",
            "izoh": "Yurak 175 bpm ga to'satdan tezlashgan, vagal sinamalar yoki dori kerak."
        },
        "savollar": [
            {
                "savol": "Yuragingiz gupillashi birdaniga, xuddi tugma bosilgandek boshlandimi? Qancha vaqtdan beri davom etyapti?",
                "maqsad": "Paroksizmning to'satdan boshlanish xususiyatini aniqlash"
            },
            {
                "savol": "Bosh aylanishi, ko'z tinishi yoki quloqda jaranglash hissi bormi?",
                "maqsad": "Gipoperfuziya va bosim pasayishini baholash"
            },
            {
                "savol": "Ko'kragingizda qisilish, og'riq yoki havo yetishmasligi bormi?",
                "maqsad": "Ishemiya va taxikardiyaning asoratlarini tekshirish"
            },
            {
                "savol": "Bunday kuchli urish ilgari ham bo'lganmi? Vagus sinamalarini (masalan, nafasni ushlab zo'riqish — Valsalva) qilib ko'rganmisiz?",
                "maqsad": "Valsalva manevri va ritm tiklanish anamnezi"
            },
            {
                "savol": "Bugun ko'p kofe, energetik ichdingizmi yoki kuchli stress bo'ldimi?",
                "maqsad": "Provokatsion omillarni aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni yotqizing. Shifokor nazorati ostida Valsalva sinamasini (chuqur nafas olib, 15 soniya kuchanish) bajartiring. 12 kanalli EKG apparatini darhol ulang. Vena ichiga Adenozin (ATF) yuborishga tayyor turing."
        },
        "yakunlash": {
            "matn": "Jamshid aka, ritmingiz daqiqasiga 175 ta ekan, bu paroksizmal taxikardiya. Hozir birga nafas mashqini bajaramiz va EKG qog'ozini chiqaramiz. Shifokor bilan darhol ritmni to'xtatuvchi muolajani qilamiz. Hammasi yaxshi bo'ladi!",
            "hisobot": "Bemor Jamshid (29 yosh), paroksizmal supraventrikulyar taxikardiya (HR 175 bpm, ritmik), BP 105/70 mmHg. EKG yozilmoqda, kardiologik tiklash choralari talab etiladi."
        }
    },

    "qorinchalar_taxikardiyasi": {
        "nomi": "26. Paroksizmal Qorinchalar Taxikardiyasi (VT)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Iltimos, mutlaqo qimirlamang, chuqur nafas oling!",
            "izoh": "HAYOTGA XAVFLI ARITMIYA! Bemor hushidan ketishi va qorinchalar fibrillyatsiyasiga o'tishi mumkin!"
        },
        "savollar": [
            {
                "savol": "Ko'kragingizda qattiq zarba yoki gupillash qachon boshlandi?",
                "maqsad": "Paroksizm boshlanish vaqtini aniqlash"
            },
            {
                "savol": "Ko'zingiz qorong'ilashib, hushdan ketayotgandek bo'lyapsizmi? Boshingiz aylanyaptimi?",
                "maqsad": "Gemodinamik beqarorlik va kollaps xavfini aniqlash"
            },
            {
                "savol": "Ko'kragingizda siquvchi og'riq bormi, sovuq ter bosyaptimi?",
                "maqsad": "Koronar ishemiya va shok belgilarini tekshirish"
            },
            {
                "savol": "Ilgari infarkt o'tkazganmisiz yoki yuragingizda chandiq bormi?",
                "maqsad": "VT ning organik zaminini aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni zudlik bilan gorizontal yotqizing. Defibrillyator apparatini darhol yoniga keltiring va elektrodlarini tayyorlang! Kislorod niqobini taqing. Amiodaron (Kordaron) yoki Lidokain infuziyasiga tayyorlaning."
        },
        "yakunlash": {
            "matn": "Baxtiyor aka, hech qayoqqa qimirlamang. Hozir reanimatsiya shifokorlari kelmoqda, yurak ritmingizni barqarorlashtirish uchun dori tomizamiz va monitoring qilamiz. Biz yoningizdamiz!",
            "hisobot": "Bemor Baxtiyor (55 yosh), gemodinamik beqaror qorinchalar taxikardiyasi (VT, HR 160 bpm), BP 85/50 mmHg, hushdan ketish xavfi, sovuq ter. Qizil kod — defibrillyator va reanimatsiya brigadasi chaqirildi!"
        }
    },

    "miokardit": {
        "nomi": "27. O'tkir Infeksion Miokardit",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Ko'kragingizdagi og'riq bo'yicha yordam beramiz, qulay o'tirib oling.",
            "izoh": "Gripp yoki virusli infeksiyadan keyingi asorat."
        },
        "savollar": [
            {
                "savol": "Ko'krak sohasidagi og'riq qanday: simillovchi, bosuvchimi yoki sanchuvchimi? Nafas olganda o'zgaradimi?",
                "maqsad": "Miokarditga xos noaniq og'riqni baholash"
            },
            {
                "savol": "Yaqinda (1-2 hafta oldin) kuchli gripp, tomoq og'rig'i yoki virusli shamollash o'tkazganmidingiz?",
                "maqsad": "Postinfeksion etiologiyani aniqlash"
            },
            {
                "savol": "Ozgina harakat qilsangiz ham yuragingiz tez urib, hansirab qolyapsizmi?",
                "maqsad": "Sinusli taxikardiya va yurak yetishmovchiligini tekshirish"
            },
            {
                "savol": "Tana haroratingiz ko'tarilib turibdimi (subfebrilitet 37.5 - 38°C)?",
                "maqsad": "Yallig'lanish sindromini aniqlash"
            },
            {
                "savol": "Kuchli holsizlik, bo'g'imlarda zirqirash yoki mushak og'riqlari bormi?",
                "maqsad": "Astenovegetativ intoksikatsiyani baholash"
            }
        ],
        "parvarish": {
            "tavsiya": "Jismoniy yuklamani mutlaqo to'xtating, qat'iy yarim to'shak rejimi. Puls va haroratni o'lchang. EKG, Exokardiografiya va qon tahlillariga (Troponin, SRB) tayyorlang."
        },
        "yakunlash": {
            "matn": "Alisher aka, o'tkazilgan grippdan so'ng yurak mushagida yallig'lanish boshlangan bo'lishi mumkin. Hozir sizga to'liq tinchlik kerak. EKG olamiz va kardiolog shifokor bilan yallig'lanishga qarshi davolashni boshlaymiz. Xotirjam dam oling.",
            "hisobot": "Bemor Alisher (34 yosh), o'tkir infeksion-allergik miokardit gumoni: postgrippoz davr, doimiy taxikardiya (HR 110 bpm), ko'krakda simillovchi og'riq, T 37.8°C. Kardiologik ko'rik kerak."
        }
    },

    "perikardit": {
        "nomi": "28. O'tkir Quruq Perikardit",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Oldinga engashib o'tiribsiz, shunday o'tirish qulayroqmi?",
            "izoh": "Klassik perikardit belgisi: oldinga egilganda og'riq kamayadi, chalqancha yotsa chidab bo'lmaydi."
        },
        "savollar": [
            {
                "savol": "Ko'kragingizdagi og'riq qachon kuchayadi: orqaga chalqancha yotganingizda yoki chuqur nafas olganingizda og'riq kuchayadimi?",
                "maqsad": "Pozitsion og'riq va plevroperikardial belgilarni aniqlash"
            },
            {
                "savol": "Oldinga engashib o'tirganingizda og'riq biroz bosilyaptimi?",
                "maqsad": "Perikarditning patognomik belgisini tasdiqlash"
            },
            {
                "savol": "Og'riq chap yelkaga yoki trapetsiyasimon mushakka tarqalyaptimi?",
                "maqsad": "Frenikus nervi irradiatsiyasini tekshirish"
            },
            {
                "savol": "Isitma, qaltirash yoki yaqinda shamollash bo'lganmidi?",
                "maqsad": "Infeksion perikardit sababini aniqlash"
            },
            {
                "savol": "Yutinayotganingizda ko'krakda noqulaylik bormi?",
                "maqsad": "Disfagiya va qizilo'ngachga yaqinlikni tekshirish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorga qulay bo'lgan holatda (oldinga biroz engashgan) o'tirishiga ruxsat bering, zo'rlab chalqancha yotqizmang! EKG da ST segmentining barcha tarmoqlarda konkav ko'tarilishini tekshiring."
        },
        "yakunlash": {
            "matn": "Dilshod aka, sizdagi holat yurak xaltasi (perikard) yallig'lanishiga o'xshaydi. O'zingizga qulay o'tiring, zo'riqmang. Hozir shifokor bilan EKG va Exokardiografiya qilib, yallig'lanish va og'riqni qoldiruvchi dorilarni kiritamiz.",
            "hisobot": "Bemor Dilshod (41 yosh), o'tkir quruq perikardit: to'sh ortida o'tkir og'riq, pozitsion xarakter (oldinga engashganda yengillashadi), taxikardiya. Kardiolog ko'rigi va EKG zarur."
        }
    },

    "endokardit": {
        "nomi": "29. Infeksion Bakterial Endokardit",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Holsizlanib qolibsiz, haroratingizni o'lchab beraman.",
            "izoh": "Infeksion bakterial endokardit, klapanlar zararlanishi xavfi."
        },
        "savollar": [
            {
                "savol": "Isitma va qaltirash qancha vaqtdan beri davom etyapti? Kechalari ko'p terlash bormi?",
                "maqsad": "Septik isitma va kechki terlashni aniqlash"
            },
            {
                "savol": "Yaqinda stomatologda tish oldirdingizmi yoki biror jarrohlik/urologik muolaja qildirdingizmi?",
                "maqsad": "Bakteremiya kirish darvozasini aniqlash"
            },
            {
                "savol": "Bo'g'imlaringizda og'riq, tez charchash, vazn yo'qotish kuzatildimi?",
                "maqsad": "Tizimli yallig'lanish belgilarini baholash"
            },
            {
                "savol": "Barmoqlaringiz uchida, kaftlaringizda yoki tirnoqlaringiz ostida qizil-jigarrang nuqtalar paydo bo'lmadimi?",
                "maqsad": "Osler tugunchalari va petexiyalarni tekshirish"
            },
            {
                "savol": "Yurak sohasida shovqin yoki yangi paydo bo'lgan yurak o'ynashi sezildimi?",
                "maqsad": "Klapan yetishmovchiligi shovqinini tekshirish"
            }
        ],
        "parvarish": {
            "tavsiya": "Harorat, puls va bosimni o'lchang. Antibakterial dori berishdan oldin qonni steril ekmaga (gemokultura 3 marta) olishga tayyorlang. Exokardiografiyaga yozing."
        },
        "yakunlash": {
            "matn": "Umid aka, davomiy isitma va tish muolajasidan keyingi holsizlik yurak klapanlariga ta'sir qilgan bo'lishi mumkin. Hozir qon tahlillari olamiz va shifokor bilan kuchli antibiotik terapiyasini boshlaymiz. Dam oling, hammasi nazorat ostida.",
            "hisobot": "Bemor Umid (32 yosh), infeksion endokardit gumoni: tish ekstraktsiyasidan so'ng 2 haftalik septik isitma, taxikardiya, anemiya va holsizlik. Zudlik bilan qon ekmasi va Exokardiografiya kerak."
        }
    },

    "aorta_anevrizmasi": {
        "nomi": "30. Ko'krak Qafasi Aorta Anevrizmasi (Yorilish xavfi)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Hech qimirlamang, gapirishga zo'riqmang!",
            "izoh": "O'TA XAVFLI! Aorta yorilishi xavfi bor, har qanday zo'riqish va bosim oshishi o'limga olib kelishi mumkin."
        },
        "savollar": [
            {
                "savol": "Og'riq qayerda: ko'krak qafasining ichkarisida, xuddi ichingiz yirtilayotgandek chidab bo'lmas og'riqmi?",
                "maqsad": "Aortaning qavatlanuvchi anevrizmasi og'rig'ini aniqlash"
            },
            {
                "savol": "Og'riq orqangizga, ikki kurak o'rtasiga yoki belingizga qarab tarqalyaptimi?",
                "maqsad": "Og'riq irradiatsiyasi va qavatlanish yo'nalishini aniqlash"
            },
            {
                "savol": "Ovozingiz bo'g'ilib qolmadimi yoki yutinish qiyinlashmadimi?",
                "maqsad": "Qaytuvchi hiqildoq nervi va qizilo'ngach kompressiyasini tekshirish"
            },
            {
                "savol": "Qon bosimingiz ilgari doim baland (gipertoniya) bo'lganmi?",
                "maqsad": "Asosiy xavf omilini aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Qat'iy gorizontal yotqizish, harakatlanish mutlaqo man etiladi! Ikkala qo'lda ham qon bosimini o'lchang (qo'llar orasida bosim farqini aniqlash). Qon tomir jarrohi va reanimatsiyani zudlik bilan xabardor qiling."
        },
        "yakunlash": {
            "matn": "Rustam aka, siz mutlaqo qimirlamay yoting, chuqur va xotirjam nafas oling. Barcha ma'lumotlarni oldim, hozir shoshilinch qon tomir jarrohlari va reanimatsiya brigadasi kelmoqda. Biz yoningizdamiz!",
            "hisobot": "Bemor Rustam aka (62 yosh), ko'krak aortasining qavatlanuvchi anevrizmasi gumoni: to'sh orqasida yirtuvchi og'riq, kuraklar orasiga tarqalishi, qon bosimi 190/100 mmHg. Qizil kod — shoshilinch angioxirurgiya va KT-angiografiya!"
        }
    },

    "yurak_tamponadasi": {
        "nomi": "31. O'tkir Yurak Tamponadasi (Bek triadasi)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Holsizlanib qolibsiz, chuqur nafas oling.",
            "izoh": "Bek triadasi: bo'rtgan bo'yin venalari, gipotoniya, kariklashgan yurak tonlari."
        },
        "savollar": [
            {
                "savol": "Havo yetishmasligi, kuchli hansirash va ko'krakda siqilish hissi qachon boshlandi?",
                "maqsad": "Tamponada va o'tkir gipodiastoliyani baholash"
            },
            {
                "savol": "Ko'kragingizga yaqinda zarba tekkanmidi, travma yoki yurak operatsiyasi bo'lganmidi?",
                "maqsad": "Gematoperikard sababini aniqlash"
            },
            {
                "savol": "Boshingiz aylanib, hushdan ketayotgandek bo'lyapsizmi?",
                "maqsad": "Arterial bosim qulashi va serebral gipoperfuziyani aniqlash"
            },
            {
                "savol": "Nafas olganingizda tomir urishi (puls) susayib ketayotganini sezyapsizmi?",
                "maqsad": "Paradoksal puls (Pulsus paradoxus) mavjudligini tekshirish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni yarim o'tirgan holatda ushlang. Yuqori oqimli kislorod bering. Shoshilinch perikardiotsentez (yurak xaltasidan suyuqlikni igna bilan tortish) to'plamini tayyorlang."
        },
        "yakunlash": {
            "matn": "Sanjar aka, yuragingiz atrofida suyuqlik to'plangan bo'lishi mumkin. Hozir zudlik bilan reanimatolog va kardioxirurg shifokor keladi, ultratovush (ExoKG) nazoratida yordam ko'rsatamiz. Xotirjam bo'ling.",
            "hisobot": "Bemor Sanjar (44 yosh), o'tkir yurak tamponadasi (Bek triadasi): arterial gipotoniya (BP 80/50), bo'yin venalari bo'rtishi, paradoksal puls. Shoshilinch perikardiotsentezga tayyorgarlik!"
        }
    },

    "ortostatik_kollaps": {
        "nomi": "32. Ortostatik Kollaps va Vazovagal Hushdan Ketish",
        "is_child": False,
        "salomlashish": {
            "matn": "Shahnozaxon, ko'zingizni oching, men hamshira opangizman. Xavotir olmang, siz xavfsiz joydasiz.",
            "izoh": "Vazovagal sinkope / ortostatik gipotoniya, hushiga keltirish."
        },
        "savollar": [
            {
                "savol": "O'zingizga keldingizmi? Tik turganda birdan ko'zingiz qorong'ilashib, qulog'ingiz shang'illab ketdimi?",
                "maqsad": "Kollaps xarakterini aniqlash"
            },
            {
                "savol": "Bugun ertalab nonushta qilganmidingiz? Suv ichganmidingiz?",
                "maqsad": "Gipoglikemiya va gipovolemiyani aniqlash"
            },
            {
                "savol": "Hushingizdan ketishdan oldin ko'ngil aynishi, sovuq ter bosishi bo'ldimi?",
                "maqsad": "Vazovagal prodromni baholash"
            },
            {
                "savol": "Yiqilganingizda boshingizni biror joyga urib olmadingizmi?",
                "maqsad": "Kalla suyagi shikastlanishini tekshirish"
            },
            {
                "savol": "Ilgari ham issiqda yoki uzoq tik turganda shunday hushdan ketish bo'lganmi?",
                "maqsad": "Anamnezni tekshirish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni gorizontal yotqizib, oyoqlarini 30-45 gradusga ko'taring (bosh miyaga qon quyilishi yaxshilanadi). Yoqasini bo'shating, toza havo bering. Novshadil spirti hidlatilishi mumkin. Suv yoki shirin choy ichiring."
        },
        "yakunlash": {
            "matn": "Shahnozaxon, hozir o'rningizdan turishga shoshilmang, 10-15 daqiqa oyoqlaringizni ko'tarib yoting. Bosimingiz 85/50 ga tushib ketgan ekan, hozir shirin choy beraman, o'zingizga kelasiz. Yoningizdaman.",
            "hisobot": "Bemor Shahnoza (19 yosh), ortostatik kollaps va vazovagal hushdan ketish: BP 85/50 mmHg, travma yo'q, hushiga keldi, gemodinamika tiklanmoqda."
        }
    },

    "dvt_tromboz": {
        "nomi": "33. Pastki Oyoq Chuqur Venalari Trombozi (DVT)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Oyog'ingizdagi og'riq bo'yicha yordam beramiz, yotib oling.",
            "izoh": "Chuqur venalar trombozi, oyog'ini aslo massaj qilmang (tromboemboliya xavfi)!"
        },
        "savollar": [
            {
                "savol": "Chap oyog'ingiz qachondan beri shishib, og'riyapti? O'ng oyog'ingizdan sezilarli darajada yo'g'onlashganmi?",
                "maqsad": "Asimmetrik shish va og'riqni baholash"
            },
            {
                "savol": "Uzoq vaqt harakatsiz o'tirdingizmi (masalan, mashinada, samolyotda yoki kasallik tufayli to'shakda)?",
                "maqsad": "Venoz staz xavf omilini aniqlash"
            },
            {
                "savol": "Boldir mushagini bosganda yoki oyoq panjasini yuqoriga bukkanda qattiq og'riq bormi?",
                "maqsad": "Xomans simptomi va chuqur vena zararlanishini tekshirish"
            },
            {
                "savol": "Ko'krak qafasingizda to'satdan sanchiq yoki nafas qisishi paydo bo'lmadimi?",
                "maqsad": "TELA asoratini istisno qilish"
            },
            {
                "savol": "Ilgari venalaringizda varikoz yoki tromboz bo'lganmi?",
                "maqsad": "Trombotik anamnezni tekshirish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni yotqizing, oyog'ini baland yostiqqa ko'tarib qo'ying. DIQQAT: Oyog'ini massaj qilish, issiq vannalar qilish qat'iyan taqiqlanadi! Past molekulyar geparin (antikoagulyant) va UZDG tomirlar tekshiruviga tayyorlang."
        },
        "yakunlash": {
            "matn": "Qodir aka, oyog'ingizdagi tomirda tromboz bo'lishi ehtimoli bor. Hech qachon oyog'ingizni uqalamang yoki massaj qilmang. Hozir qon suyultiruvchi ukol qilamiz va qon tomir jarrohi tekshiradi. Xotirjam dam oling.",
            "hisobot": "Bemor Qodir aka (52 yosh), chap oyoq chuqur venalari o'tkir trombozi gumoni: boldir asimmetrik shishi, Xomans simptomi musbat, TELA belgilari yo'q. Zudlik bilan antikoagulyant va UZDG kerak."
        }
    },

    "reyno_sindromi": {
        "nomi": "34. Reyno Sindromi (Barmoqlar o'tkir ishemiyasi)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Nigora opa. Men navbatchi hamshiraman. Qo'llaringiz muzlab qolibdi, sizga yordam beramiz.",
            "izoh": "Periferik tomirlar o'tkir spazmi, sovuq ta'siri."
        },
        "savollar": [
            {
                "savol": "Barmoqlaringiz rangi qanday o'zgardi: avval oppoq oqarib, keyin ko'karib, isiganda qizarib ketadimi?",
                "maqsad": "Klassik 3 fazali Reyno o'zgarishini aniqlash"
            },
            {
                "savol": "Bu holat sovuq suv tekkanda yoki sovuq havoga chiqqanda boshlandimi?",
                "maqsad": "Sovuq triggeryni aniqlash"
            },
            {
                "savol": "Barmoqlaringizda muzdek qotish, uvishish, igna sanchilgandek og'riq bormi?",
                "maqsad": "Ishemiya va paresteziyani tekshirish"
            },
            {
                "savol": "Bo'g'imlaringizda og'riq, terida qattiqlashish yoki toshmalar bormi?",
                "maqsad": "Tizimli sklerodermiya yoki revmatologik kasallikni tekshirish"
            },
            {
                "savol": "Chekasizmi yoki qon tomir toraytiruvchi dori qabul qilasizmi?",
                "maqsad": "Spazmni kuchaytiruvchi omillarni aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Qo'llarni asta-sekin iliq muhitda isiting (issiq suvga solmang!). Bemorni tinchlantiring, issiq choy bering. Tomir kengaytiruvchi dori (kalsiy kanallari blokatori) tayinlash uchun shifokorni chaqiring."
        },
        "yakunlash": {
            "matn": "Nigora opa, barmoqlaringizdagi tomirlar qattiq qisqarib qolgan. Hozir qo'llaringizni iliq ushlab, tomirni kengaytiruvchi dori beramiz, tez orada qon aylanishi tiklanib, og'riq to'xtaydi. Xavotir olmang.",
            "hisobot": "Bemor Nigora (28 yosh), Reyno sindromi o'tkir vazospastik xuruji: ikki tomonlama barmoqlar oqarishi, sianoz va kuydiruvchi og'riq. Isitish va vazodilatator terapiya rejalashtirildi."
        }
    },

    "kardiogen_shok": {
        "nomi": "35. Kardiogen Shok (O'tkir nasos yetishmovchiligi)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Karim aka. Men navbatchi hamshiraman. Gapirmasdan tinch yotavering, sizga yordam beryapmiz.",
            "izoh": "O'TA OG'IR HOLAT! Miokard infarkti fonida qon bosimi 70/40 mmHg ga tushgan."
        },
        "savollar": [
            {
                "savol": "To'shingiz orqasidagi og'riq davom etyaptimi? Chidab bo'lmas tosh ezgandek og'riqmi?",
                "maqsad": "Og'ir infarkt og'rig'ini baholash"
            },
            {
                "savol": "Havo yetmayaptimi, bo'g'ilish hissi bormi?",
                "maqsad": "Chap qorincha yetishmovchiligini baholash"
            },
            {
                "savol": "Bosh aylanishi, ko'z qorong'ilashishi bormi?",
                "maqsad": "Bosh miya gipoperfuziyasini aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni gorizontal yotqizib, boshini biroz ko'taring (o'pka shishi bo'lmasa). Yuqori oqimli kislorod ulanadi. Markaziy venaga kateter qo'yiladi. Inotrop preparatlar (Dofamin, Noradrenalin) perfuzor orqali yuborishga tayyorlanadi."
        },
        "yakunlash": {
            "matn": "Karim aka, mutlaqo gapirishga zo'riqmang. Reanimatsiya brigadasi barcha dori vositalari bilan yoningizda. Bosimingizni ko'tarish va yuragingizni quvvatlash uchun barcha muolajalarni qilamiz. Siz bilan birgamiz!",
            "hisobot": "Bemor Karim aka (59 yosh), o'tkir kardiogen shok: BP 70/40 mmHg, ipsimon puls 120 bpm, marmarsimon teri, anuriya, anginoz holat. Qizil kod — shoshilinch kardioreanimatsiya va inotropik terapiya!"
        }
    },

    "pnevmotoraks": {
        "nomi": "36. Spontan Taranglashgan Pnevmotoraks",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Hech qimirlamang, sekin nafas oling.",
            "izoh": "Spontan pnevmotoraks: o'pka yorilib plevra bo'shlig'iga havo to'plangan."
        },
        "savollar": [
            {
                "savol": "Ko'kragingizdagi o'tkir pichoqdek og'riq aynan qaysi tomonda: o'ngdami yoki chapda?",
                "maqsad": "Pnevmotoraks tomonini aniqlash"
            },
            {
                "savol": "Og'ir yuk ko'targaningizda yoki qattiq yo'talganingizda birdaniga boshlandimi?",
                "maqsad": "Spontan bulla yorilishini aniqlash"
            },
            {
                "savol": "Har nafas olganingizda o'sha tomonda og'riq kuchayib, havo yetishmayaptimi?",
                "maqsad": "Plevral og'riq va taxipnoeni baholash"
            },
            {
                "savol": "Ovoz chiqarganingizda ko'kragingizda havo qisilib qolgandek tuyulyaptimi?",
                "maqsad": "O'pka kollapsini aniqlash"
            },
            {
                "savol": "Ilgari ko'krak qafasidan travma olganmisiz yoki pnevmotoraks bo'lganmi?",
                "maqsad": "Anamnezni tekshirish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni yarim o'tirgan holatga keltiring. Kislorod niqobini taqing. Ko'krak qafasi a'zolarining qarama-qarshi tomonga siljishini kuzating (taranglashgan pnevmotoraks xavfi!). Shoshilinch plevra ponksiyasi yoki drenajlashga (Byulau drenaji) tayyorlang."
        },
        "yakunlash": {
            "matn": "Bobur, o'pkangiz atrofida havo to'planib qolganga o'xshaydi. Tinch o'tiring, chuqur nafas olishga urinmang. Hozir torakal jarroh shifokor keladi, rentgen qilib havoni chiqarib tashlaymiz va nafasingiz darhol ochiladi.",
            "hisobot": "Bemor Bobur (23 yosh), o'ng tomonlama o'tkir spontan pnevmotoraks gumoni: pichoqsimon og'riq, o'ng o'pkada nafas eshitilmaydi, SpO2 86%, taxipnoe. Shoshilinch torakal xirurgik yordam!"
        }
    },

    "tela": {
        "nomi": "37. O'pka Arteriyasi Tromboemboliyasi (TELA)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Manzura opa. Men navbatchi hamshiraman. Qimirlamang, gapirmang, kislorod niqobini taqaman.",
            "izoh": "O'TA XAVFLI SHOSHILINCH HOLAT! Operatsiyadan keyingi to'satdan TELA."
        },
        "savollar": [
            {
                "savol": "Bo'g'ilish to'satdan, birdaniga boshlandimi? Havo umuman kirmayotgandek tuyulyaptimi?",
                "maqsad": "O'tkir asfiksiya va gipoksiyani aniqlash"
            },
            {
                "savol": "Ko'krak qafasingizda o'tkir sanchiq bormi?",
                "maqsad": "Plevral ishemiya og'rig'ini tekshirish"
            },
            {
                "savol": "Yo'talganda qon aralash balg'am (qon tupurish) keldilarmi?",
                "maqsad": "O'pka infarkti belgisini aniqlash"
            },
            {
                "savol": "Yaqinda operatsiya o'tkazganmidingiz yoki oyoqlaringizda shish, tomir og'rig'i bo'lganmidi?",
                "maqsad": "Chuqur venalar trombozi manbasini aniqlash"
            },
            {
                "savol": "Yuragingiz juda tez urib, hushdan ketayotgandek bo'lyapsizmi?",
                "maqsad": "O'tkir o'pka yuragi va kollapsni baholash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni qat'iy to'shak rejimiga o'tkazing (harakatlanish qat'iyan man etiladi!). Yuqori oqimli kislorod bering. Darhol 2 ta venoz kateter qo'ying. Trombolizis yoki geparinoterapiyaga tayyorlaning."
        },
        "yakunlash": {
            "matn": "Manzura opa, hech xavotir olmang, qimirlamay yoting. Kislorod ulandik. Reanimatsiya va kardiologiya jamoasi yoningizda, tomirdagi tiqilmani erituvchi maxsus dorilarni zudlik bilan boshlaymiz. Biz siz bilanmiz!",
            "hisobot": "Bemor Manzura opa (56 yosh), massiv o'pka arteriyasi tromboemboliyasi (TELA): o'tkir bo'g'ilish, diffuz sianoz, taxikardiya (HR 130 bpm), BP 90/60 mmHg, qon tupurish. Qizil kod — reanimatsiya va trombolitik terapiya!"
        }
    },

    "kosl_obstruksiya": {
        "nomi": "38. KO'SL (Surunkali Obstruktiv O'pka Kasalligi zo'rayishi)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Ahmad aka. Men navbatchi hamshiraman. Nafasingizni rostlab oling, sizga dori beramiz.",
            "izoh": "Surunkali obstruktiv o'pka kasalligi zo'rayishi, uzoq yillik chekuvchi."
        },
        "savollar": [
            {
                "savol": "Nafas chiqarishingiz juda qiyinlashib ketdimi? Ko'kragingizda qaynash va xirillash eshitilyaptimi?",
                "maqsad": "Ekspirator bronxial obstruktsiyani baholash"
            },
            {
                "savol": "Yo'talganda qanday balg'am chiqyapti: sarg'ish-yashil yiringlimi, ko'chishi qiyinmi?",
                "maqsad": "Bakterial infeksiya zo'rayishini tekshirish"
            },
            {
                "savol": "Necha yildan beri tamaki chekasiz, kuniga necha dona chekardingiz?",
                "maqsad": "Kashandalik indeksini aniqlash"
            },
            {
                "savol": "Uyda doimiy ingalyator (Spiriva, Berodual, Seretid) ishlatasizmi? Bugun necha marta qabul qildingiz?",
                "maqsad": "Bazis terapiya samaradorligini baholash"
            },
            {
                "savol": "Tana haroratingiz ko'tarildimi, holsizlik kuchaydimi?",
                "maqsad": "Yallig'lanish sindromini aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni qo'llariga tayanib o'tirgan holatda qoldiring (yotqizmang!). Past oqimli (1-2 l/min) kislorod bering (yuqori oqim giperkapniyaga olib kelishi mumkin!). Nebulayzer orqali Berodual va Budesonid bilan ingalyatsiya qiling."
        },
        "yakunlash": {
            "matn": "Ahmad aka, o'pka yo'llaringiz torayib, balg'am to'plangan. Hozir nebulayzer orqali bronxni kengaytiruvchi dori beramiz va kislorod ulaymiz. Nafas olishingiz tezda yengillashadi. Xotirjam o'tiring.",
            "hisobot": "Bemor Ahmad aka (64 yosh), KO'SL zo'rayish bosqichi, III darajali nafas yetishmovchiligi: og'ir ekspirator dispnoe, SpO2 85%, yiringli balg'am. Nebulayzer terapiyasi va nazoratli kislorod berildi."
        }
    },

    "opka_shishi": {
        "nomi": "39. O'tkir Alveolyar O'pka Shishi",
        "is_child": False,
        "salomlashish": {
            "matn": "Salima opa, eshityapsizmi meni? Men navbatchi hamshiraman. Hech qimirlamang, yordam beramiz!",
            "izoh": "O'TA XAVFLI! Alveolyar o'pka shishi: og'izdan pushti ko'pikli balg'am, uzoqdan eshitiluvchi qaynashsimon xirillash."
        },
        "savollar": [
            {
                "savol": "Bo'g'ilish qachon boshlandi? Yotganda umuman nafas ololmay qoldingizmi?",
                "maqsad": "O'tkir chap qorincha yetishmovchiligini aniqlash"
            },
            {
                "savol": "Qon bosimingiz ilgari juda baland ko'tarilarmidi yoki yurak infarkti bo'lganmidi?",
                "maqsad": "Kardiogen etiologiyani aniqlash"
            },
            {
                "savol": "Og'zingizdan ko'pik kelyaptimi?",
                "maqsad": "Alveolalar gemorragik suyuqlik bilan to'lishini baholash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni zudlik bilan oyoqlarini pastga osiltirgan holda o'tqazing! Etil spirti bug'lari orqali namlangan yuqori oqimli kislorod bering (spirt ko'pik so'ndiruvchi sifatida ishlatiladi!). Vena ichiga Furosemid (Lasix) 40-80 mg va Morfin tayyorlang."
        },
        "yakunlash": {
            "matn": "Salima opa, oyoqlaringizni tushirib o'tiring, aslo yotmang. Kislorod niqobini taqdim, bu ko'pikni yo'qotadi. Hozir tomiringizdan o'pkadagi suvni haydaydigan dori yuboramiz. Reanimatsiya shifokorlari yoningizda!",
            "hisobot": "Bemor Salima opa (61 yosh), o'tkir alveolyar o'pka shishi: pushti ko'pikli balg'am, masofadan eshitiluvchi klokotan nam xirillashlar, ortopnoe, SpO2 78%, BP 180/100 mmHg. Qizil kod — kardioreanimatsiya, ko'pik so'ndiruvchi kislorod va Furosemid!"
        }
    },

    "plevrit": {
        "nomi": "40. O'tkir Ekssudativ Plevrit",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Sherzod aka. Men navbatchi hamshiraman. Nafasingiz qisayotganga o'xshaydi, keling sizni qulay joylashtiraman.",
            "izoh": "Ekssudativ plevrit, plevra bo'shlig'ida suyuqlik to'plangan."
        },
        "savollar": [
            {
                "savol": "Ko'kragingizdagi og'irlik qachon paydo bo'ldi? Avval o'tkir sanchiq bo'lib, keyin tosh bosgandek bosimga aylandimi?",
                "maqsad": "Quruq plevritdan ekssudativ plevritga o'tish dinamikasi"
            },
            {
                "savol": "Qaysi tomonga yotganingizda nafas olishingiz osonlashadi: og'riyotgan chap tomoningizgami?",
                "maqsad": "Kasal tomonga yotganda sog'lom o'pka erkin nafas olishini aniqlash"
            },
            {
                "savol": "Hansirash jismoniy harakatda kuchayadimi? Tana haroratingiz ko'tarildimi?",
                "maqsad": "Respirator yetishmovchilik va intoksikatsiyani baholash"
            },
            {
                "savol": "Quruq yo'tal bezovta qilyaptimi?",
                "maqsad": "Plevral yo'talni tekshirish"
            },
            {
                "savol": "Yaqinda zotiljam (pnevmoniya) yoki sil kasalligi bilan og'riganmidingiz?",
                "maqsad": "Plevrit etiologiyasini aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni kasal (chap) tomoniga yarim yotqizing (sog'lom o'pka to'liq ekskursiya qilishi uchun). Kislorod bering. Plevral ponksiya (torakotsentez) o'tkazish uchun shifokorga yordamga tayyorlaning."
        },
        "yakunlash": {
            "matn": "Sherzod aka, chap o'pkangiz atrofida suyuqlik yig'ilib qolgan ekan. Chap yoningizga yonboshlab yoting, nafasingiz osonlashadi. Hozir shifokor bilan rentgen qilib, kerak bo'lsa igna bilan suyuqlikni tortib olamiz, shunda o'pkangiz darhol yoziladi. Xotirjam dam oling.",
            "hisobot": "Bemor Sherzod (36 yosh), chap tomonlama o'tkir ekssudativ plevrit: chap o'pka pastki qismida nafas yo'qligi, perkussiyada to'mtoq tovush, taxipnoe (24/daq), SpO2 91%. Torakal ponksiyaga tayyorgarlik ko'rilmoqda."
        }
    },

    "opka_absessi": {
        "nomi": "41. O'pka Absessi (Yiringli destruksiya)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Botir aka. Men navbatchi hamshiraman. Og'zingizni chayib olishingizga yordam beraman, qulay o'tiring.",
            "izoh": "Bemor to'satdan ko'p miqdorda sasigan yiringli balg'am qusgan, nafas olish yo'llarini aspiratsiyadan saqlang."
        },
        "savollar": [
            {
                "savol": "Yo'talganda to'satdan ko'p miqdorda (og'iz to'lib) qo'lansa hidli balg'am keldilarmi? Taxminan necha millilitr chiqdi?",
                "maqsad": "Absessning bronxga yorilishi va yiring hajmini aniqlash"
            },
            {
                "savol": "Balg'am chiqqandan keyin ko'kragingizdagi og'riq va nafas qisishi biroz yengillashdimi?",
                "maqsad": "Bo'shliq drenajlanishi dinamikasini baholash"
            },
            {
                "savol": "Isitmangiz necha kundan beri 39°C dan tushmayapti? Qattiq qaltirash va kechasi terlash bo'lyaptimi?",
                "maqsad": "Gektik isitma va yiringli intoksikatsiyani baholash"
            },
            {
                "savol": "Balg'amda qon tomirlari yoki qon quyqalari bormi?",
                "maqsad": "O'pka qon ketishi xavfini aniqlash"
            },
            {
                "savol": "Yaqinda zotiljam (pnevmoniya) o'tkazganmidingiz yoki hushsiz holatda yotganmisiz?",
                "maqsad": "Absessning aspiratsion yoki metapnevmonik etiologiyasini aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni drenajlovchi holatga (sog'lom tomonga yonboshlatib, bosh qismini biroz pastlatish) keltiring. Balg'am yig'uvchi idish va og'iz chayish uchun antiseptik eritma bering. Kislorod ulanadi. Shoshilinch ko'krak qafasi rentgeni va antibakterial terapiyaga tayyorlang."
        },
        "yakunlash": {
            "matn": "Botir aka, o'pkadagi yiringli bo'shliq bronxga ochilibdi. Hozir og'zingizni tozalab, nafas olishingizni yengillashtiramiz. Ko'p suyuqlik ichib turing. Shifokor bilan zudlik bilan kuchli antibiotik va o'pkani tozalash muolajasini boshlaymiz. Xavotir olmang.",
            "hisobot": "Bemor Botir (48 yosh), o'pka absessi o'tkir bosqichi: bronxga yorilish (300 ml fuzid yiringli balg'am), T 39.5°C, intoksikatsiya, o'ng o'pkada amforik nafas. Torakal pulmonologiya ko'rigi talab etiladi."
        }
    },

    "bronxoektaz": {
        "nomi": "42. Bronxoektatik Kasallik va Qon Tupurish",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Jasur aka. Men navbatchi hamshiraman. Yo'talishingizni yengillatishga yordam beramiz, qulay o'tiring.",
            "izoh": "Surunkali yiringli jarayon, qon tupurish xavfi bor."
        },
        "savollar": [
            {
                "savol": "Ertalab uyg'onganingizda ko'p miqdorda (og'iz to'la) balg'am ajraladimi? Idishda turganda 3 qavatga ajralishini sezganmisiz?",
                "maqsad": "Bronxoektazga xos ertalabki 3 qatlamli balg'am xarakterini aniqlash"
            },
            {
                "savol": "Balg'amingizda qon chiziqlari yoki qon quyqalari bormi? Bugun qon tupurdingizmi?",
                "maqsad": "Gemoptizis (o'pka qon ketishi) darajasini baholash"
            },
            {
                "savol": "Barmoqlaringiz uchlari yo'g'onlashgani (baraban cho'plari) va tirnoqlaringiz soat oynasiga o'xshab qolganiga ancha bo'lganmi?",
                "maqsad": "Surunkali uzoq yillik gipoksiya belgilarini tasdiqlash"
            },
            {
                "savol": "Tana haroratingiz ko'tarilib, holsizlik kuchaydimi?",
                "maqsad": "Bronxoektatik infeksiya zo'rayishini baholash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni yarim o'tirgan holatda tuting. Qon tupurish bo'lsa: to'liq jismoniy va ovozli tinchlik, ko'krak qafasiga muz xaltasi qo'yiladi. Issiq ovqat va ichimliklar man etiladi. Gemostatik preparatlar (Etamzilat, Aminokapron kislota) tayyorlanadi."
        },
        "yakunlash": {
            "matn": "Jasur aka, qon tupurganingiz uchun hozir mutlaqo yo'talmaslikka va qattiq gapirmaslikka harakat qiling. Ko'kragingizga muz qo'yamiz va qon to'xtatuvchi ukol qilamiz. Hozir shifokor bilan bronxoskopiya va davolashni kelishamiz. Dam oling.",
            "hisobot": "Bemor Jasur (39 yosh), bronxoektatik kasallik zo'rayishi, qon tupurish (gemoptizis): yiringli balg'amda qon quyqalari, baraban cho'plari simptomi, T 37.6°C. Shoshilinch gemostaz va pulmonolog ko'rigi."
        }
    },

    "respirator_distress": {
        "nomi": "43. O'tkir Respirator Distress Sindromi (ARDS)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Dilshod aka. Men navbatchi hamshiraman. Hech gapirmang, faqat nafas olishga e'tibor bering!",
            "izoh": "O'TA OG'IR! Refrakter gipoksemiya (SpO2 78%), o'pkaning noxirurgik diffuz zararlanishi, intubatsiya kerak."
        },
        "savollar": [
            {
                "savol": "Kislorod niqobida ham havo yetmayotgandek tuyulyaptimi? Ko'kragingizda qattiq qisilish bormi?",
                "maqsad": "Refrakter gipoksemiya va og'ir nafas yetishmovchiligini baholash"
            },
            {
                "savol": "Nafas olishingiz juda tezlashib ketganini (daqiqasiga 30-35 marta) sezyapsizmi?",
                "maqsad": "Taxipnoe va respirator charchoqni aniqlash"
            },
            {
                "savol": "Yaqinda og'ir virusli pnevmoniya, sepsis yoki travma o'tkazganmidingiz?",
                "maqsad": "ARDS qo'zg'atuvchi omilini aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni pron-pozitsiyaga (qorin bilan yotqizish — o'pkaning orqa segmentlarini shamollatish uchun) o'tkazing. Rezervuarli niqob orqali 100% kislorod bering. Reanimatologni zudlik bilan chaqirib, endotraxeal intubatsiya va O'SV apparatiga (PEEP rejimi) tayyorlang."
        },
        "yakunlash": {
            "matn": "Dilshod aka, o'pkangizga maxsus apparat orqali chuqur nafas berishimiz kerak. Reanimatsiya brigadasi barcha apparatlar bilan yoningizda. Sizni uxlatib, nafas olishingizni to'liq mashina nazoratiga olamiz, kislorodingiz ko'tariladi. Biz siz bilanmiz!",
            "hisobot": "Bemor Dilshod (45 yosh), o'tkir respirator distress sindromi (ARDS, og'ir daraja): SpO2 78% (O2 niqobida), RR 34/daq, diffuz infiltratsiya, refrakter gipoksiya. Zudlik bilan intubatsiya va O'SV (IVL) talab etiladi!"
        }
    },

    "yot_jism_asfiksiya": {
        "nomi": "44. Yuqori Nafas Yo'llariga Yot Jism Tiqilishi",
        "is_child": False,
        "salomlashish": {
            "matn": "Bemorga zudlik bilan murojaat: 'Bo'g'ilyapsizmi?! Tiqilib qoldimi?!' (Bemor gapira olmaydi, bo'ynini ikki qo'li bilan ushlagan — Geymlix belgisi).",
            "izoh": "FAVQULODDA HOLAT! Sekundlar hal qiladi! Bemor gapira olmaydi, darhol Geymlix manevrini bajaring!"
        },
        "savollar": [
            {
                "savol": "(Tezkor harakat): Bemor yo'tala olyaptimi? (Agar yo'tala olmasa va gapirmasa — to'liq obstruktsiya)",
                "maqsad": "Nafas yo'li to'liq yoki qisman to'silganini aniqlash"
            },
            {
                "savol": "(Ko'rik): Yuz va lablarida sianoz (ko'karish) boshlandimi?",
                "maqsad": "O'tkir asfiksiya darajasini baholash"
            },
            {
                "savol": "(Atrofdagilarga): Ovqatlanayotganda go'sht yoki suyak tiqilib qoldimi?",
                "maqsad": "Yot jism turini aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "GEYMLIX MANEVRINI BAJARING: Bemorning orqasiga o'ting, qo'llaringizni uning qorniga (kindik va xanjarsimon o'simta o'rtasiga) o'rab, mushtingizni ichkariga va yuqoriga qarab 5 marta keskin siltang! Agar hushidan ketsa: chalqancha yotqizib yurak-o'pka reanimatsiyasini boshlang va krikotireotomiya/laringoskopiyaga tayyorlaning."
        },
        "yakunlash": {
            "matn": "Geymlix manevri bajarildi! Go'sht bo'lagi tashqariga otilib chiqdi. Bemor chuqur nafas ola boshladi, lablaridagi ko'karish qaytmoqda.",
            "hisobot": "Bemor Otabek (33 yosh), yuqori nafas yo'liga go'sht luqmasi tiqilishi (asfiksiya). Geymlix usuli orqali yot jism muvaffaqiyatli chiqarildi, nafas yo'llari o'tkazuvchanligi tiklandi."
        }
    },

    "tuberkulyoz": {
        "nomi": "45. O'pka Tuberkulyozi (Sil intoksikatsiyasi)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Ravshan aka. Men navbatchi hamshiraman. Keling, sizga himoya niqobini beraman, o'zingizni erkin tuting.",
            "izoh": "Sil infeksiyasi xavfi, hamshira va bemor respirator/niqob taqishi shart."
        },
        "savollar": [
            {
                "savol": "Yo'talingiz necha haftadan beri davom etyapti? 3 haftadan oshib ketganmi?",
                "maqsad": "Surunkali yo'tal davomiyligini aniqlash"
            },
            {
                "savol": "Har kuni kechqurun isitmangiz 37.2 - 37.4°C ga ko'tarilib, kechalari kiyimingizni almashtiradigan darajada qattiq terlaysizmi?",
                "maqsad": "Klassik tuberkulyoz intoksikatsiyasi va tungi terlashni aniqlash"
            },
            {
                "savol": "Oxirgi oylarda sezilarli darajada vazn yo'qotdingizmi? Necha kilo ozdingiz?",
                "maqsad": "Sil kasalligidagi kaxeksiya va oziqlanish tanqisligini baholash"
            },
            {
                "savol": "Yo'talganda balg'amda qon tomirlari chiqmadimi?",
                "maqsad": "O'pka destruksiyasi va qon tupurishni tekshirish"
            },
            {
                "savol": "Oilangizda yoki ishxonangizda uzoq yo'taladigan yoki sil bilan og'rigan odam bormidi?",
                "maqsad": "Epidemiologik kontakt anamnezini o'rganish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni alohida ventilyatsiyalanuvchi xonaga ajrating (izolyatsiya). Bemorni N95 respirator bilan ta'minlang. Balg'amni mikobakteriyaga (BK tahlili va GenXpert) yig'ish uchun 3 ta steril idish tayyorlang. Flyurografiya/Rentgenografiyaga yo'naltiring."
        },
        "yakunlash": {
            "matn": "Ravshan aka, 2 oylik yo'tal, isitma va ozish o'pkangizda jiddiy infeksiya borligini ko'rsatmoqda. Hozir balg'amingizni maxsus laboratoriyaga jo'natamiz va rentgen qilamiz. Ftiziatr shifokor ko'rib, to'liq davolash kursini belgilaydi. Hech tushkunlikka tushmang, sil to'liq davolanadigan kasallik.",
            "hisobot": "Bemor Ravshan (41 yosh), o'pka tuberkulyozi gumoni: 2 oylik yo'tal, tungi gipergidroz, subfebrilitet (37.3°C), 8 kg vazn yo'qotishi. BK mikroskopiyasi va rentgen tekshiruviga yuborildi."
        }
    },

    "pankreatit": {
        "nomi": "46. O'tkir Destruktiv Pankreatit (Kamar og'rig'i)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum. Men navbatchi hamshiraman. Qorningiz qattiq og'riyaptimi, zudlik bilan yotib oling.",
            "izoh": "O'tkir kamar shaklidagi og'riq, oshqozon osti bezi fermentativ autolizi xavfi."
        },
        "savollar": [
            {
                "savol": "Og'riq qorinning yuqori qismida xuddi kamar bog'lagandek orqangizga va ikki yoningizga o'rab og'riyaptimi?",
                "maqsad": "Pankreatitga xos kamar shaklidagi (opoyasyvayushchaya) og'riqni aniqlash"
            },
            {
                "savol": "Og'riq yog'li ovqat (kabob, go'sht) yoki spirtli ichimlik iste'molidan keyin boshlandimi?",
                "maqsad": "Alimentar va alkogol provokatsion omillarini aniqlash"
            },
            {
                "savol": "Qusish necha marta bo'ldi? Qayt qilganingizdan keyin og'riq yengillashdimi yoki o'zgarishsiz qoldimi?",
                "maqsad": "Yengillik keltirmaydigan to'xtovsiz qusishni aniqlash"
            },
            {
                "savol": "Qorningiz shishib, gaz chiqishi to'xtab qolmadimi?",
                "maqsad": "Parez va ichak tutilishi belgilarini baholash"
            },
            {
                "savol": "Kindik atrofida yoki biqin sohasida ko'kargan dog'lar paydo bo'lmadimi?",
                "maqsad": "Kallen va Grey-Terner simptomlarini (gemorragik pankreonekroz) ko'zdan kechirish"
            }
        ],
        "parvarish": {
            "tavsiya": "QAT'IY QOIDA: 'OCHLIK, SOVUQ VA TINCHLIK' (Golod, xolod i pokoy). Og'iz orqali ovqat va suv berish mutlaqo man etiladi! Qorinning yuqori sohasiga muz xaltasi qo'yiladi. Nazogastral zond qo'yishga tayyorlang. Spazmolitiklar, og'riqsizlantiruvchi va proteaz ingibitorlari (Kontrikal/Gordoks) tayyorlanadi."
        },
        "yakunlash": {
            "matn": "Shavkat aka, sizda oshqozon osti bezining o'tkir yallig'lanishi (pankreatit). Hozir hech narsa yemang va ichmang, qorningizga muz qo'yamiz. Zudlik bilan shoshilinch jarroh chaqirildi, vena orqali osma ukollar bilan og'riqni qoldiramiz. Chidab turing, yordam beramiz!",
            "hisobot": "Bemor Shavkat (46 yosh), o'tkir destruktiv pankreatit xuruji: kamar shaklidagi chidab bo'lmas og'riq, yengillik bermaydigan qayta qusish, takogen taomlar anamnezi. Shoshilinch xirurgik statsionar va intensiv terapiya."
        }
    },

    "xolesistit": {
        "nomi": "47. O'tkir Kalkulyoz Xolesistit (O't sanchig'i)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Gulnora opa. Men navbatchi hamshiraman. O'ng qovurg'angiz tagidagi og'riq bo'yicha yordam beramiz, yotib oling.",
            "izoh": "O't pufagida tosh tiqilishi va yallig'lanish, og'izda taxirlik."
        },
        "savollar": [
            {
                "savol": "Og'riq aynan o'ng qovurg'angiz ostidami? O'ng yelkaga, kurakka yoki bo'yningizga tarqalyaptimi?",
                "maqsad": "O't yo'llari og'rig'i irradiatsiyasini aniqlash"
            },
            {
                "savol": "Kecha qovurilgan, yog'li ovqat (somsa, tuxum, mayonez) yeganingizdan keyin boshlandimi?",
                "maqsad": "Xolestatik alimentar triggerni aniqlash"
            },
            {
                "savol": "Og'zingizda achchiq taxir ta'm bormi? Ko'nglingiz aynib, sariq o't qusdingizmi?",
                "maqsad": "O't refluksi va intoksikatsiyani baholash"
            },
            {
                "savol": "Ko'zingiz oqi yoki teringiz sarg'ayib qolmadimi? Siydigingiz rangi pivo rangidek to'qlashmadimi?",
                "maqsad": "Mexanik sariqlik (o't yo'li tosh bilan to'silishi)ni tekshirish"
            },
            {
                "savol": "Tana haroratingiz ko'tarilib, qaltirash bo'ldimi?",
                "maqsad": "Destruktiv xolesistit yoki xolangit asoratini tekshirish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni to'shakka yotqizing. Ovqatlanishni to'xtating. O'ng qovurg'a ostiga sovuq qo'yiladi (aslo issiq grelka emas!). Spazmolitiklar (No-shpa, Platifillin) tayyorlanadi. Qorin bo'shlig'i UTT (UZI) tekshiruviga tayyorlang."
        },
        "yakunlash": {
            "matn": "Gulnora opa, o't pufagingiz yallig'langan, tosh tiqilib qolgan bo'lishi mumkin. Hozir qorningizga sovuq qo'yib, spazmni yozuvchi ukol qilamiz, og'riq ancha pasayadi. Shoshilinch UZI tekshiruvidan o'tkazamiz va jarroh ko'radi. Xotirjam bo'ling.",
            "hisobot": "Bemor Gulnora opa (52 yosh), o'tkir kalkulyoz xolesistit, o't sanchig'i: o'ng qovurg'a ostida og'riq, o'ng yelkaga irradiatsiya, Orttner va Myursi simptomi musbat, T 37.8°C. Shoshilinch UTT va xirurgik yordam."
        }
    },

    "oshqozon_perforatsiya": {
        "nomi": "48. Oshqozon Yarasi Teshilishi (Xanjarsimon og'riq)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Shuhrat aka. Men navbatchi hamshiraman. Hech qimirlamang, gapirishga urinmang!",
            "izoh": "FAVQULODDA XIRURGIK HOLAT! Oshqozon teshilgan, xanjarsimon og'riq, taxtasimon qorin, peritonit xavfi."
        },
        "savollar": [
            {
                "savol": "Qorningizga to'satdan xuddi pichoq yoki xanjar suqqandek dahshatli og'riq kirdimi?",
                "maqsad": "Teshilish (perforatsiya)ning patognomik xanjarsimon og'rig'ini aniqlash"
            },
            {
                "savol": "Og'riq aynan qaysi daqiqada boshlandi?",
                "maqsad": "Peritonit boshlanish vaqtini daqiqasigacha hisoblash"
            },
            {
                "savol": "Ilgari oshqozon yoki 12 barmoqli ichak yarasidan davolanganmisiz?",
                "maqsad": "Yara kasalligi anamnezini tasdiqlash"
            },
            {
                "savol": "Nafas olganingizda qorningiz qimirlayaptimi yoki og'riqdan qorin devori taxtadek qotib qolganmi?",
                "maqsad": "Taxtasimon qorin (defans muskulyar) belgisini tekshirish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni zudlik bilan zambilda gorizontal yotqizing, har qanday harakatlanish man etiladi! Og'iz orqali suv va dori berish mutlaqo taqiqlanadi! Qoringa muz qo'yiladi. Vena ichiga 2 ta kateter qo'yiladi. Operatsion xona va shoshilinch jarrohlik brigadasi ogohlantiriladi."
        },
        "yakunlash": {
            "matn": "Shuhrat aka, siz mutlaqo qimirlamay yoting. Oshqozon yarangiz teshilgan bo'lishi ehtimoli juda yuqori. Hozir zudlik bilan jarrohlar kelmoqda, operatsiya xonasini tayyorlayapmiz. Sizni qutqaramiz, xotirjam bo'ling!",
            "hisobot": "Bemor Shuhrat aka (43 yosh), oshqozon yarasi perforatsiyasi gumoni: to'satdan xanjarsimon og'riq, taxtasimon qorin (defans), Shchyotkin-Blyumberg musbat, qorin nafasda qatnashmaydi. Qizil kod — shoshilinch laparotomiya!"
        }
    },

    "oshqozon_qonash": {
        "nomi": "49. Oshqozondan O'tkir Qon Ketish (Qon qusish va Melena)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Bahrom aka. Men navbatchi hamshiraman. Boshingiz aylanayotgan bo'lsa darhol yotib oling, boshni ko'tarmang.",
            "izoh": "Massiv qon yo'qotish va kollaps xavfi, kofe quyqasidek qusish yoki melena."
        },
        "savollar": [
            {
                "savol": "Qusganingizda rangi qanday edi: to'q qizil qonmi yoki 'kofe quyqasi'ga o'xshagan jigarrang-qoramtirmi?",
                "maqsad": "Qonash manbasi va xlorid kislota bilan reaksiyasini aniqlash"
            },
            {
                "savol": "Hojatga borganingizda najasingiz qora smolaga (qatronga) o'xshab keldimi (melena)?",
                "maqsad": "Oshqozon-ichak qonashining asosiy belgisi (melena)ni tekshirish"
            },
            {
                "savol": "Kuchli bosh aylanishi, quloqda shang'illash, ko'z qorong'ilashishi bormi?",
                "maqsad": "O'tkir anemiya va gipovolemiya darajasini baholash"
            },
            {
                "savol": "Oldin oshqozon yarasi bo'lganmi yoki og'riq qoldiruvchi dorilar (Aspirin, Diklofenak, Ketonal) ichganmidingiz?",
                "maqsad": "Medikamentoz yoki yarali eroziyani aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni qat'iy yotqizing, oyoqlarini biroz ko'taring. Epigastral sohaga muz xaltasi qo'yiladi. Muzdek suv ichirilishi mumkin. Gemostatik dorilar (Ditsinon/Etamzilat, Traneksam, Vikasol) vena ichiga yuboriladi. Qon guruhi va rezus-omil zudlik bilan aniqlanadi."
        },
        "yakunlash": {
            "matn": "Bahrom aka, qon bosimingiz 80/50 ga tushibdi, oshqozoningizdan qon ketmoqda. Hozir qorningizga muz qo'yib, tomiringizdan qon to'xtatuvchi dorilarni kiritamiz. Endoskopist shifokor qonayotgan tomirni kuydirib to'xtatadi. Qimirlamay yoting, barchasi nazoratda.",
            "hisobot": "Bemor Bahrom (47 yosh), o'tkir oshqozon-ichakdan qon ketishi: kofe quyqasimon qusish, melena, gemorragik shok I-II daraja (BP 80/50, HR 115). Shoshilinch EGDFS (gastroskopiya) va gemostaz."
        }
    },

    "ichak_tutilishi": {
        "nomi": "50. O'tkir Mexanik Ichak Tutilishi",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Mansur aka. Men navbatchi hamshiraman. Qorningiz qattiq shishib ketibdi, keling sizni qulay yotqizaylik.",
            "izoh": "Ichak buralishi / tutilishi, gaz va najas chiqmasligi, ichak gangrenasi xavfi."
        },
        "savollar": [
            {
                "savol": "Necha kundan beri ichingiz kelmadi va gaz chiqishi butunlay to'xtab qoldi?",
                "maqsad": "Ichak tutilishining bosh triadasi (najas va gaz to'xtashi)ni aniqlash"
            },
            {
                "savol": "Qorningizdagi og'riq to'lqinsimon xarakterdami (tutib-tutib kuchayib, keyin biroz bosiladimi)?",
                "maqsad": "Mexanik tutilishdagi kuchli peristaltik to'lqinlarni aniqlash"
            },
            {
                "savol": "Qusish bo'lyaptimi? Qusgan narsangizda noxush ichak hidi (axlat hidi) bormi?",
                "maqsad": "Fekaloid qusish va yuqori/pastki tutilishni aniqlash"
            },
            {
                "savol": "Ilgari qorin bo'shlig'ida operatsiya bo'lganmisiz (spayka/chandiqlar bormi)?",
                "maqsad": "Spayechnaya ichak tutilishi xavfini baholash"
            }
        ],
        "parvarish": {
            "tavsiya": "Ovqat va suv berish taqiqlanadi! Hech qanday surgi dori (ich suruvchi) bermang (ichak yorilishiga olib kelishi mumkin!). Oshqozonni dekompressiya qilish uchun nazogastral zond o'rnating. Shoshilinch qorin bo'shlig'i umumiy rentgenografiyasiga (Kloyber kosachalari) tayyorlang."
        },
        "yakunlash": {
            "matn": "Mansur aka, ichaklaringizda to'silish yuzaga kelgan. Hozir burningizdan ingichka naycha orqali oshqozondagi suyuqlikni tortib olamiz, qorningiz shishi ancha pasayadi. Rentgen qilib, shoshilinch jarrohlik yo'li bilan ichakni ochamiz. Xotirjam bo'ling.",
            "hisobot": "Bemor Mansur aka (53 yosh), o'tkir mexanik (spayechnaya) ichak tutilishi: to'lqinsimon og'riq, qorin asimmetrik shishi, gaz va axlat yo'qligi, ko'p karra qusish. Shoshilinch rentgen va xirurgik amaliyot."
        }
    },

    "qisilgan_churra": {
        "nomi": "51. Bo'g'ilgan Chov Churrasi (Inkarseratsiya)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Ilhom aka. Men navbatchi hamshiraman. Chov sohasidagi og'riq bo'yicha yordam beramiz, yotib oling.",
            "izoh": "Churra qisilib qolgan, o'zicha ichkariga tiqish mutlaqo taqiqlanadi (ichak nekrozi xavfi)!"
        },
        "savollar": [
            {
                "savol": "Chov sohangizdagi shish qachon paydo bo'ldi va qattiqlashib qoldi? Ilgari yotganingizda o'z-o'zidan ichkariga kirib ketarmidi?",
                "maqsad": "Churraning erkin qaytuvchanlikdan qisilgan holatga o'tishini aniqlash"
            },
            {
                "savol": "Bu shishni ichkariga qaytarishga o'zingiz urinib ko'rmadingizmi?",
                "maqsad": "Qisilgan churra to'qimasini majburan tiqish asoratlarini tekshirish"
            },
            {
                "savol": "Og'ir yuk ko'targaningizdan keyin birdan qattiq og'riq boshlandimi?",
                "maqsad": "Inkarseratsiya sababini aniqlash"
            },
            {
                "savol": "Ko'ngil aynishi, qusish yoki qorningiz shishishi kuzatildimi?",
                "maqsad": "Ichak tutilishi asoratlarini baholash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni gorizontal yotqizing. DIQQAT: Qisilgan churra xaltasini qo'l bilan ichkariga kiritishga urinish QAT'IYAN TAQIQLANADI (chunki qisilgan ichak nekrozga uchragan bo'lishi mumkin!). Chov sohasiga muz xaltasi qo'yiladi. Shoshilinch operatsiyaga tayyorlanadi."
        },
        "yakunlash": {
            "matn": "Ilhom aka, churrangiz qisilib qolgan, uni qo'l bilan bosib bo'lmaydi. Hozir sizga muz qo'yib, og'riqsizlantiruvchi muolajani qilamiz. Navbatchi jarroh shifokor churra darvozasini operatsiya yo'li bilan kengaytirib, ichakni qutqarib qoladi. Xotirjam yoting.",
            "hisobot": "Bemor Ilhom aka (50 yosh), bo'g'ilgan o'ng chov churrasi (inkarseratsiya): qaytmas qattiq o'tkir og'riqli hosila, yo'tal turtkisi manfiy, 3 soatlik davomiylik. Zudlik bilan shoshilinch gerniotomiya!"
        }
    },

    "peritonit": {
        "nomi": "52. Tarqalgan Yiringli Peritonit",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Aziz aka. Men navbatchi hamshiraman. Iltimos qimirlamang, sekin nafas oling.",
            "izoh": "OG'IR INTOTSIKATSIYA! Qorin pardasi yallig'lanishi, tili quruq jigarrang, Gipokrat yuzi."
        },
        "savollar": [
            {
                "savol": "Qorningizning barcha qismida qattiq og'riq bormi? Harakat qilganda, yo'talganda og'riq chidab bo'lmas darajada kuchayadimi?",
                "maqsad": "Diffuz peritoneal og'riqni baholash"
            },
            {
                "savol": "Tilingiz qaqrab qurib qolganini sezyapsizmi? Ko'p chanqayapsizmi?",
                "maqsad": "Og'ir intoksikatsiya va suvsizlanish darajasini aniqlash"
            },
            {
                "savol": "Bu holat boshlanishidan 1-2 kun oldin qorningizning biron joyi (masalan, appenditsit yoki oshqozon) og'riganmidi?",
                "maqsad": "Peritonitning birlamchi manbasini aniqlash"
            },
            {
                "savol": "Tana haroratingiz juda yuqori bo'lib, keyin birdan pasayib ketmadimi?",
                "maqsad": "Toksik faza va septik shok xavfini baholash"
            }
        ],
        "parvarish": {
            "tavsiya": "Qorin devoriga qo'l tekkizganda ehtiyot bo'ling (Shchyotkin-Blyumberg belgisi kuchli og'riq beradi). Bemorni zambilda yotqizing. Ikkita yirik venaga kateter qo'yib massiv detoksikatsion infuziya boshlang. Shoshilinch operatsiyaga (laparotomiya va sanatsiya) tayyorlang."
        },
        "yakunlash": {
            "matn": "Aziz aka, qorin pardangizda jiddiy yallig'lanish bor. Hozir tomiringizdan zaharli moddalarni haydaydigan eritmalarni ulaymiz. Jarrohlar jamoasi zudlik bilan operatsiya qilib, qorin bo'shlig'ini yuvib tozalaydi. Biz siz bilanmiz!",
            "hisobot": "Bemor Aziz (35 yosh), tarqalgan o'tkir peritonit, toksik faza: qorin devori defansi, Shchyotkin-Blyumberg musbat, quruq karashli til, taxikardiya (HR 125), taxipnoe. Qizil kod — shoshilinch laparotomiya va sanatsiya!"
        }
    },

    "mezenterial_tromboz": {
        "nomi": "53. Mezenterial Qon Tomirlar Trombozi",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Valijon aka. Men navbatchi hamshiraman. Mutlaqo qimirlamang, og'riqni qoldirishga yordam beramiz.",
            "izoh": "O'TA XAVFLI! Ichak arteriyasi trombozi, qorin yumshoq bo'lsa ham dahshatli og'riq bo'ladi (ichak infarkti)."
        },
        "savollar": [
            {
                "savol": "Og'riq kindik atrofida to'satdan boshlandimi? Hech qanday og'riq qoldiruvchi dori ta'sir qilmayaptimi?",
                "maqsad": "O'tkir mezenterial ishemiyaning doimiy chidab bo'lmas og'rig'ini aniqlash"
            },
            {
                "savol": "Sizda yurak ritmi buzilishi (miltillovchi aritmiya) yoki infarkt bo'lganmi?",
                "maqsad": "Kardiyogen emboliya manbasini aniqlash"
            },
            {
                "savol": "Qon aralash suyuq ich ketishi yoki qusish kuzatildimi?",
                "maqsad": "Ichak shilliq qavati nekrozi va qonashini aniqlash"
            },
            {
                "savol": "Boshingiz aylanib, sovuq ter bosyaptimi?",
                "maqsad": "Ishemik shok rivojlanishini baholash"
            }
        ],
        "parvarish": {
            "tavsiya": "Har bir daqiqa qadrli (ichak nekrozi 2-4 soatda boshlanadi!). Vena ichiga Geparin/antikoagulyantlar va infuziya boshlang. Shoshilinch angioxirurg va umumiy jarrohni chaqirib, KT-angiografiya va laparotomiyaga tayyorlang."
        },
        "yakunlash": {
            "matn": "Valijon aka, ichak tomiringizda tiqilma bo'lishi mumkin. Qimirlamay yoting, tomiringizdan qon aylanishini tiklovchi dorilarni kiritamiz. Jarrohlar zudlik bilan tomirni ochib ichakni saqlab qoladi. Yoningizdamiz!",
            "hisobot": "Bemor Valijon aka (65 yosh), mezenterial qon tomirlar o'tkir trombozemboliyasi: kindik sohasida refrakter dahshatli og'riq, qonli diareya, miltillovchi aritmiya anamnezi. Zudlik bilan shoshilinch angioxirurgik ko'rik!"
        }
    },

    "yarali_kolit": {
        "nomi": "54. Nospetsifik Yarali Kolit (O'tkir qonli diareya)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Nodira opa. Men navbatchi hamshiraman. Holsizlanib qolibsiz, yotib dam oling.",
            "izoh": "NYaK zo'rayishi, qonli diareya, tenezmlar, anemiya va suvsizlanish."
        },
        "savollar": [
            {
                "savol": "Bir kunda necha marta hojatga boryapsiz? 10-15 martadan ko'pmi?",
                "maqsad": "Diareya chastotasi va NYaK og'irlik darajasini aniqlash"
            },
            {
                "savol": "Najasingizda qip-qizil qon, shilimshiq yoki yiring aralash kelyaptimi?",
                "maqsad": "Yo'g'on ichak shilliq qavati destruksiyasini baholash"
            },
            {
                "savol": "Qorin pastki chap sohasida og'riq va hojatga soxta qistovlar (tenezmlar) bezovta qilyaptimi?",
                "maqsad": "Sigmasimon va to'g'ri ichak spastik tenezmlarini aniqlash"
            },
            {
                "savol": "Tana haroratingiz ko'tarilib, vazningiz keskin kamaydimi?",
                "maqsad": "Tizimli yallig'lanish va intoksikatsiyani baholash"
            },
            {
                "savol": "Ilgari Koloskopiya qildirganmisiz, qanday dori (Salofalk, Prednizolon) qabul qilasiz?",
                "maqsad": "Bazis terapiyani tekshirish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni yotqizing. Qon yo'qotish va suvsizlanishni qoplash uchun kristalloid va elektrolit eritmalar infuziyasini o'tkazing. Shifokor bilan glyukokortikoidlar (Gidrokortizon/Prednizolon) va gemostatiklar berilishini muvofiqlashtiring."
        },
        "yakunlash": {
            "matn": "Nodira opa, ichakdagi yallig'lanish tufayli ko'p suyuqlik va qon yo'qotgansiz. Hozir tomiringizdan osma ukol bilan darmon dorilar va yallig'lanishni to'xtatuvchi preparatlarni beramiz, ichingiz kelishi tezda kamayadi. Xotirjam dam oling.",
            "hisobot": "Bemor Nodira (30 yosh), nospetsifik yarali kolit (NYaK) o'tkir zo'rayish bosqichi: gemokolit (12-15 marta qonli diareya), tenezmlar, T 38.0°C, anemiya. Shoshilinch gastroenterologik va infuzion terapiya."
        }
    },

    "jigar_sirrozi": {
        "nomi": "55. Jigar Sirrozi Dekompenzatsiyasi va Astsit",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Yoqub aka. Men navbatchi hamshiraman. Nafas olishingiz qiyinlashgan bo'lsa baland yostiqqa suyab qo'yaman.",
            "izoh": "Portal gipertenziya, astsit (qorin suv to'lishi), sariqlik va jigar ensefalopatiyasi xavfi."
        },
        "savollar": [
            {
                "savol": "Qorningiz shishib, ichiga suv to'planishi (astsit) qachondan beri kuchaydi? Yotganingizda hansirash bo'lyaptimi?",
                "maqsad": "Astsit hajmi va diafragma baland ko'tarilishini baholash"
            },
            {
                "savol": "Ko'zingiz oqi yoki teringiz sarg'ayib ketganini sezdingizmi? Qichishish bormi?",
                "maqsad": "Xolestaz va parenximatoz sariqlikni aniqlash"
            },
            {
                "savol": "Burundan qon ketish, badanda ko'karishlar paydo bo'lishi bormi?",
                "maqsad": "Jigarning oqsil va qon ivish omillari yetishmovchiligini tekshirish"
            },
            {
                "savol": "Uyqungiz buzilishi, kunduzi uxlab kechasi uyg'oq bo'lish yoki xotira chalkashishi kuzatilmadimi?",
                "maqsad": "Jigar ensefalopatiyasi (prekoma) belgilarini erta aniqlash"
            },
            {
                "savol": "Ilgari Gepatit B yoki C bilan og'riganmisiz?",
                "maqsad": "Sirroz etiologiyasini aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni yarim o'tirgan holatda joylashtiring. Qorin aylanasi va tana vaznini har kuni o'lchang. Tuzsiz parhez. Siydik miqdorini (diurez) qat'iy nazorat qiling. Laparotsentez (qorindagi suyuqlikni chiqarish) uchun shifokorga yordamga tayyorlaning."
        },
        "yakunlash": {
            "matn": "Yoqub aka, jigaringiz zo'riqqani uchun qorningizga suyuqlik to'plangan. Hozir sizga albumin va peshob haydovchi dorilar beramiz, nafas olishingiz osonlashadi. Shifokor bilan doimiy nazorat qilamiz. Xotirjam yoting.",
            "hisobot": "Bemor Yoqub aka (57 yosh), jigar sirrozi dekompenzatsiyasi, portal gipertenziya: tarqalgan astsit, sariqlik, terida telangiektaziyalar, nafas qisishi. Diuretik va gepatoprotektiv terapiya boshlandi."
        }
    },

    "qizilo'ngach_varikoz": {
        "nomi": "56. Qizilo'ngach Venalari Yirtilishi (Massiv gematemezis)",
        "is_child": False,
        "salomlashish": {
            "matn": "Tohir aka, boshni yonga buring! Men navbatchi hamshiraman. Qonni yutmang, og'zingizdan chiqarib tashlang!",
            "izoh": "FAVQULODDA XAVFLI! Favvora shaklida qon qusish, bemor bir necha daqiqada qonsizlanishi mumkin!"
        },
        "savollar": [
            {
                "savol": "(Ko'rik): Qusilgan qon to'q qizil (venoz) rangdami? Necha litr qon chiqdi?",
                "maqsad": "Qon yo'qotish og'irligini ko'zdan kechirish"
            },
            {
                "savol": "Sizda jigar sirrozi yoki qizilo'ngach venalari varikozi borligi ma'lummidi?",
                "maqsad": "Portal gipertenziya anamnezini tasdiqlash"
            },
            {
                "savol": "Hozir ko'zingiz qorong'ilashib, qulog'ingiz shang'illayaptimi?",
                "maqsad": "Gemorragik shok va kollapsni aniqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorning boshini yonga burib gorizontal yotqizing (qon nafas yo'liga ketmasligi uchun!). Zudlik bilan Blekmore-Sengstaken obturator zondini tayyorlang va shifokorga bering (zond baloni shishirilib qonayotgan venalar bosiladi). Ikkita yirik tomirga kateter qo'yib plazma/kristalloid va Oktreotid (Sandostatin) infuziyasini boshlang."
        },
        "yakunlash": {
            "matn": "Tohir aka, qimirlamang. Qonayotgan tomirni to'xtatish uchun maxsus ballonli zond o'rnatamiz va qon to'xtatuvchi ukol qilamiz. Reanimatsiya va endoskopiya brigadasi yoningizda. Sizni qutqaramiz, chidab turing!",
            "hisobot": "Bemor Tohir (51 yosh), qizilo'ngach varikoz venalaridan massiv qon ketishi: favvorasimon to'q qon qusish, gemorragik shok III daraja (BP 75/40, HR 135). Qizil kod — Blekmore zondi o'rnatilmoqda, shoshilinch qon quyish va endoskopik ligaturalash!"
        }
    },

    "mallory_weiss": {
        "nomi": "57. Mallori-Veys Sindromi",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Sherali aka. Men navbatchi hamshiraman. Nafasingizni rostlang, qon qusish bo'yicha yordam beramiz.",
            "izoh": "Kuchli qayt qilish oqibatida qizilo'ngach-oshqozon shilliq qavati yirtilishi."
        },
        "savollar": [
            {
                "savol": "Avval oddiy ovqat qusib, keyin ketma-ket qattiq zo'riqib qusganingizdan so'ng qizil qon aralashib ketdimi?",
                "maqsad": "Mallori-Veys sindromiga xos ikki bosqichli qusish xarakterini aniqlash"
            },
            {
                "savol": "Qusish boshlanishidan oldin ko'p spirtli ichimlik ichilganmidi yoki zaharlanish bo'lganmidi?",
                "maqsad": "Alkogol yoki alimentar emetik provokatsiyani aniqlash"
            },
            {
                "savol": "To'shingiz orqasida yoki qorin yuqori qismida yirtilgandek achishish bormi?",
                "maqsad": "Kardioezofageal sohadagi yoriq og'rig'ini baholash"
            },
            {
                "savol": "Hozir qon kelishi to'xtadimi yoki yana qusyapsizmi?",
                "maqsad": "Davomiy qonashni tekshirish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni tinch holatda yotqizing. Qusishga qarshi dori (Metoklopramid/Serukal yoki Ondansetron) yuboring (zo'riqishni to'xtatish uchun). Qoringa muz xaltasi qo'ying. Gemostatiklar va proton nasosi ingibitorlari (Omeprazol/Pantoprazol) vena ichiga beriladi."
        },
        "yakunlash": {
            "matn": "Sherali aka, qattiq qayt qilganingiz uchun qizilo'ngach shilliq qavati biroz yirtilgan. Hozir qayt qilishni to'xtatuvchi va qonni ivituvchi ukol qilamiz. Shifokor gastroskopiya orqali yoriqni ko'rib davolaydi. Qimirlamay dam oling.",
            "hisobot": "Bemor Sherali (38 yosh), Mallori-Veys sindromi: ketma-ket emetik zo'riqishdan so'ng yangi qon aralash qusish, gemodinamika nisbatan stabil (BP 110/70, HR 90). Gemostaz va EGDFS rejalashtirildi."
        }
    },

    "divertikulit": {
        "nomi": "58. Yo'g'on Ichak O'tkir Divertikuliti",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Halima xola. Men navbatchi hamshiraman. Qorningizdagi og'riq bo'yicha yordam beramiz, yotib oling.",
            "izoh": "Chap yonbosh sohasida o'tkir og'riq ('chap tomonlama appenditsit'), perforatsiya xavfi."
        },
        "savollar": [
            {
                "savol": "Og'riq qorinning chap tomoni pastida (chap yonboshda) joylashganmi? Doimiy sanchib og'riyaptimi?",
                "maqsad": "Sigmasimon ichak divertikuliti lokalizatsiyasini aniqlash"
            },
            {
                "savol": "Ichingiz qotishi yoki ich ketishi almashinib turadimi? Qorningiz dam bo'lyaptimi?",
                "maqsad": "Ichak disfunksiyasini baholash"
            },
            {
                "savol": "Tana haroratingiz ko'tarilib (38°C), qaltirash bo'ldimi?",
                "maqsad": "Yiringli yallig'lanish yoki mikroperforatsiyani aniqlash"
            },
            {
                "savol": "Najasingizda qon yoki shilimshiq ko'rindingizmi?",
                "maqsad": "Divertikuldan qonash yoki yiringlashni tekshirish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorni yotqizing. Qorinni bosmang. Issiq qo'yish yoki klizma qilish mutlaqo taqiqlanadi (divertikul yorilishi xavfi!). Ovqatlanishni cheklang. Spazmolitiklar va keng ta'sirli antibiotiklar tayyorlanadi."
        },
        "yakunlash": {
            "matn": "Halima xola, yo'g'on ichagingizning chap qismida yallig'lanish bor ekan. Qorningizga qo'lingizni bosmang. Hozir antibiotik va og'riq qoldiruvchi dorilarni kiritamiz, shifokor tekshirib kerakli muolajani qiladi. Xotirjam dam oling.",
            "hisobot": "Bemor Halima xola (66 yosh), yo'g'on ichak chap tomonlama o'tkir divertikuliti: chap yonbosh sohasida og'riq va mushak zo'riqishi, T 38.3°C, leykositoz. Xirurgik nazorat va antibakterial terapiya."
        }
    },

    "gemorroy_tromboz": {
        "nomi": "59. Gemorroidal Tugunlarning O'tkir Trombozi",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Umid aka. Men navbatchi hamshiraman. Og'riq kuchli ekanini tushunaman, qulay yonboshlab yoting.",
            "izoh": "Tashqi gemorroy tuguni o'tkir trombozi, o'ta kuchli mahalliy og'riq, o'tira olmaslik."
        },
        "savollar": [
            {
                "savol": "Orqa chiqaruv teshigi sohasida yong'oqdek qattiq va o'ta og'riqli shish qachon paydo bo'ldi?",
                "maqsad": "O'tkir trombozlangan gemorroidal tugunni aniqlash"
            },
            {
                "savol": "Og'ir yuk ko'targaningizdan yoki kuchli ich qotishidan keyin boshlandimi?",
                "maqsad": "Vena ichi bosimi oshishi omilini aniqlash"
            },
            {
                "savol": "O'tirish, yurish yoki hojatga borish chidab bo'lmas darajada og'riyaptimi?",
                "maqsad": "Funksional cheklanish darajasini baholash"
            },
            {
                "savol": "Tugundan qon oqishi yoki shilliq ajralishi bormi?",
                "maqsad": "Tromblangan tugun nekrozi va o'z-o'zidan yorilishini tekshirish"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorga qorin bilan yoki yonboshlab yotishni tavsiya qiling (aslo o'tirmasin!). Mahalliy sovuq kompress qo'yiladi. Og'riqsizlantiruvchi va antikoagulyantli malhamlar (Geparin, Troksevazin) qo'llanadi. Shoshilinch proktologik ko'rik (trombektomiya imkoniyati)."
        },
        "yakunlash": {
            "matn": "Umid aka, gemorroy tomirida tromb hosil bo'lib qattiq qisilibdi. Hozir og'riqsizlantiruvchi dori va maxsus malham qo'yamiz. Proktolog shifokor ko'rib, kerak bo'lsa 5 daqiqada kichik kesim bilan trombni olib tashlaydi va og'riq bir zumda butunlay yo'qoladi. Chidab turing!",
            "hisobot": "Bemor Umid (42 yosh), tashqi gemorroidal tugunlarning o'tkir trombozi: perianal ko'kargan o'tkir og'riqli tugun, kuchli sfinkter spazmi, o'tira olmaslik. Shoshilinch proktologik konsultatsiya va trombektomiya."
        }
    },

    "gemorragik_insult": {
        "nomi": "60. Bosh Miyaga Qon Quyilishi (Gemorragik insult)",
        "is_child": False,
        "salomlashish": {
            "matn": "Assalomu alaykum Odil aka. Meni eshityapsizmi? Men navbatchi hamshiraman. Hech qimirlamang!",
            "izoh": "FAVQULODDA O'TA OG'IR! Gipertonik kriz (230/120) fonida kalla ichiga qon quyilishi, miya shishi xavfi."
        },
        "savollar": [
            {
                "savol": "Boshingizga xuddi zarba berilgandek dahshatli og'riq kirdimi? Qayt qildingizmi?",
                "maqsad": "Miya ichi qonashining to'satdan 'zarba' shaklida boshlanishi va serebral qusishni aniqlash"
            },
            {
                "savol": "Chap qo'lingiz va oyog'ingiz butunlay ishlamay, bo'shashib qoldimi?",
                "maqsad": "Gemiplegiya (falajlik) darajasini baholash"
            },
            {
                "savol": "Gapirishingiz qiyinlashib, tilingiz aylanmay qoldimi?",
                "maqsad": "Nutq markazi zararlanishini tekshirish"
            },
            {
                "savol": "Doimiy qon bosimingiz juda baland bo'larmidi (bugun bosim 230/120 mmHg)?",
                "maqsad": "Gipertenziv intracerebral gematoma sababini tasdiqlash"
            }
        ],
        "parvarish": {
            "tavsiya": "Bemorning boshini 30 darajaga ko'taring (miya shishini kamaytirish). Nafas yo'llari ochiqligini ta'minlang (qusish aspiratsiyasidan saqlash). Qon bosimini asta-sekin pasaytiring (keskin tushirish man etiladi!). Zudlik bilan shoshilinch bosh miya MSKT (kompyuter tomografiyasi) va neyroxirurgik brigadani chaqiring."
        },
        "yakunlash": {
            "matn": "Odil aka, siz mutlaqo qimirlamay yoting. Qon bosimingiz juda ko'tarilib ketgani uchun shoshilinch yordam ko'rsatyapmiz. Neyroreanimatsiya jamoasi yoningizda, miya tomografiyasiga olib boramiz va bosimni me'yoriga keltiramiz. Biz siz bilanmiz!",
            "hisobot": "Bemor Odil aka (58 yosh), o'tkir gemorragik insult (bosh miyaga qon quyilishi): BP 230/120 mmHg, chap tomonlama chuqur gemiplegiya, hushning karaxtlashishi, anizokoriya. Qizil kod — shoshilinch neyroKT va neyroxirurgiya!"
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
