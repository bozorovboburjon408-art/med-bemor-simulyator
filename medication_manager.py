# -*- coding: utf-8 -*-
"""
Dori-darmonlar bazasini doimiy saqlash (JSON), yangi qo'shish,
tahrirlash, o'chirish va standart holatga qaytarish moduli.
"""
import os
import json
from typing import List, Dict, Any

MEDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "medications.json")

DEFAULT_MEDICATIONS: List[Dict[str, Any]] = [
    {
        "id": "adrenalin",
        "code": "ADR-01",
        "name": "Adrenalin (Epinefrin) 1 mg/ml",
        "barcodes": ["ADR01", "ADR-01", "ADRENALIN", "EPINEPHRINE", "4780001001"],
        "group": "Adrenomimetik (Vazopressor)",
        "desc": "Yurak to'xtashi, asistoliya va anafilaktik shokda asosiy vosita.",
        "badgeBg": "#7e22ce",
        "btnColor": "bg-purple-600 hover:bg-purple-700",
        "appropriate_for": ["asystole", "bradycardia", "shock", "hypoxia"],
        "dangerous_for": ["tachycardia"]
    },
    {
        "id": "amiodaron",
        "code": "AMI-02",
        "name": "Amiodaron (Kordaron) 150 mg",
        "barcodes": ["AMI02", "AMI-02", "AMIODARON", "CORDARONE", "4780001002"],
        "group": "Antiaritmik (III-sinf)",
        "desc": "Qorincha taxikardiyasi (VTach) va aritmiyalarni to'xtatuvchi.",
        "badgeBg": "#0284c7",
        "btnColor": "bg-sky-600 hover:bg-sky-700",
        "appropriate_for": ["tachycardia"],
        "dangerous_for": ["bradycardia", "asystole"]
    },
    {
        "id": "atropin",
        "code": "ATR-03",
        "name": "Atropin sulfat 1 mg/ml",
        "barcodes": ["ATR03", "ATR-03", "ATROPIN", "ATROPINE", "4780001003"],
        "group": "M-Xolinoblokator",
        "desc": "Sust puls (bradikardiya) va AV-blokadalarda ritmni oshiradi.",
        "badgeBg": "#d97706",
        "btnColor": "bg-amber-600 hover:bg-amber-700",
        "appropriate_for": ["bradycardia"],
        "dangerous_for": ["tachycardia"]
    },
    {
        "id": "nitro",
        "code": "NIT-04",
        "name": "Nitroglitserin 0.5 mg",
        "barcodes": ["NIT04", "NIT-04", "NITRO", "NITROGLYCERIN", "4780001004"],
        "group": "Periferik vazodilatator",
        "desc": "O'tkir gipertonik kriz va stenokardiyada bosimni tushiradi.",
        "badgeBg": "#e11d48",
        "btnColor": "bg-rose-600 hover:bg-rose-700",
        "appropriate_for": ["attack"],
        "dangerous_for": ["shock", "asystole"]
    },
    {
        "id": "metoprolol",
        "code": "MET-05",
        "name": "Metoprolol (Beta-blokator) 5 mg",
        "barcodes": ["MET05", "MET-05", "METOPROLOL", "BETALOC", "4780001005"],
        "group": "Beta-1 adrenoblokator",
        "desc": "Taxikardiyada puls va miokard kislorod talabini pasaytiradi.",
        "badgeBg": "#4f46e5",
        "btnColor": "bg-indigo-600 hover:bg-indigo-700",
        "appropriate_for": ["tachycardia"],
        "dangerous_for": ["bradycardia", "asystole", "hypoxia"]
    },
    {
        "id": "saline",
        "code": "SAL-06",
        "name": "Fizrastvor (0.9% NaCl) 500 ml",
        "barcodes": ["SAL06", "SAL-06", "NACL", "FIZRASTVOR", "SALINE", "4780001006"],
        "group": "Kristalloid plazma o'rnini bosuvchi",
        "desc": "Gipovolemik va qon yo'qotish shokida qon bosimini tiklaydi.",
        "badgeBg": "#2563eb",
        "btnColor": "bg-blue-600 hover:bg-blue-700",
        "appropriate_for": ["shock", "hypoxia"],
        "dangerous_for": []
    },
    {
        "id": "dexa",
        "code": "DEX-07",
        "name": "Deksametazon 8 mg/2ml",
        "barcodes": ["DEX07", "DEX-07", "DEXA", "DEXAMETHASONE", "4780001007"],
        "group": "Glikokortikosteroid (Gormon)",
        "desc": "Bronxospazm, anafilaksiya va o'tkir gipoksiyani bartaraf etadi.",
        "badgeBg": "#059669",
        "btnColor": "bg-emerald-600 hover:bg-emerald-700",
        "appropriate_for": ["hypoxia"],
        "dangerous_for": []
    },
    {
        "id": "naloxone",
        "code": "NAL-08",
        "name": "Nalokson 0.4 mg/ml",
        "barcodes": ["NAL08", "NAL-08", "NALOXON", "NALOXONE", "4780001008"],
        "group": "Opioid retseptorlari antagonisti",
        "desc": "Narkotik intoksikatsiyasi va nafas tormozlanishiga qarshi vosita.",
        "badgeBg": "#0d9488",
        "btnColor": "bg-teal-600 hover:bg-teal-700",
        "appropriate_for": ["hypoxia"],
        "dangerous_for": []
    },
    {
        "id": "kcl",
        "code": "KCL-09",
        "name": "Kaliy xlorid (KCl 4%) 20 ml",
        "barcodes": ["KCL09", "KCL-09", "KCL", "POTASSIUM", "4780001009"],
        "group": "Elektrolit (Toksik konsentrat)",
        "desc": "DIQQAT: Sof holda vena ichiga yuborish kardioplegiya chaqiradi!",
        "badgeBg": "#dc2626",
        "btnColor": "bg-red-600 hover:bg-red-700",
        "appropriate_for": [],
        "dangerous_for": ["asystole", "normal", "shock", "bradycardia", "tachycardia"]
    },
    {
        "id": "furosemide",
        "code": "FUR-10",
        "name": "Furosemid (Laziks) 20 mg",
        "barcodes": ["FUR10", "FUR-10", "FUROSEMID", "LASIX", "4780001010"],
        "group": "Halqa diuretigi",
        "desc": "O'pka shishi va gipertoniyada tezkor suyuqlik haydovchi vosita.",
        "badgeBg": "#0891b2",
        "btnColor": "bg-cyan-600 hover:bg-cyan-700",
        "appropriate_for": ["attack"],
        "dangerous_for": ["shock", "asystole"]
    }
]

def load_medications() -> List[Dict[str, Any]]:
    if not os.path.exists(MEDS_FILE):
        save_medications(DEFAULT_MEDICATIONS)
        return DEFAULT_MEDICATIONS
    try:
        with open(MEDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                return data
    except Exception as e:
        print(f"Medications load error: {e}")
    save_medications(DEFAULT_MEDICATIONS)
    return DEFAULT_MEDICATIONS

def save_medications(meds: List[Dict[str, Any]]) -> bool:
    try:
        with open(MEDS_FILE, "w", encoding="utf-8") as f:
            json.dump(meds, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Medications save error: {e}")
        return False

def add_or_update_medication(med_data: Dict[str, Any]) -> Dict[str, Any]:
    meds = load_medications()
    code = (med_data.get("code") or "MED-99").upper().strip()
    med_id = med_data.get("id") or code.lower().replace("-", "_")
    med_data["id"] = med_id
    med_data["code"] = code
    
    # Ensure barcodes array
    barcodes = med_data.get("barcodes") or []
    if isinstance(barcodes, str):
        barcodes = [b.strip() for b in barcodes.split(",") if b.strip()]
    if code and code not in barcodes:
        barcodes.insert(0, code)
    clean_code = code.replace("-", "")
    if clean_code and clean_code not in barcodes:
        barcodes.append(clean_code)
    med_data["barcodes"] = barcodes

    if not med_data.get("badgeBg"):
        med_data["badgeBg"] = "#6366f1"
    if not med_data.get("btnColor"):
        med_data["btnColor"] = "bg-indigo-600 hover:bg-indigo-700"
    if not med_data.get("group"):
        med_data["group"] = "Klinik dori"
    if not med_data.get("desc"):
        med_data["desc"] = "Shoshilinch dori vositasi"
    if not med_data.get("appropriate_for"):
        med_data["appropriate_for"] = []
    if not med_data.get("dangerous_for"):
        med_data["dangerous_for"] = []

    existing_idx = next((i for i, m in enumerate(meds) if m.get("id") == med_id or m.get("code", "").upper() == code), None)
    if existing_idx is not None:
        meds[existing_idx] = med_data
    else:
        meds.append(med_data)
        
    save_medications(meds)
    return med_data

def delete_medication(med_id: str) -> bool:
    meds = load_medications()
    clean_id = med_id.lower().strip()
    initial_len = len(meds)
    meds = [m for m in meds if m.get("id", "").lower() != clean_id and m.get("code", "").lower() != clean_id]
    if len(meds) < initial_len:
        save_medications(meds)
        return True
    return False

def reset_to_defaults() -> List[Dict[str, Any]]:
    save_medications(DEFAULT_MEDICATIONS)
    return DEFAULT_MEDICATIONS
