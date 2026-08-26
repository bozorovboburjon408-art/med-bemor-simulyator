import time
import requests
import json

URL = "http://localhost:8500/api/telemetry"

print("=" * 60)
print("  MANIKEN DATCHIKLARI SIMULYATORI (TEST YUBORUVCHI)")
print("=" * 60)
print("Har 0.5 soniyada JSON ma'lumotlari yuborilmoqda...\n")

test_packets = [
    # 1. Normal holat
    {"lung_p": 0.0, "stomach_p": 0.0, "force_kg": 0.0, "pos_valid": True, "timestamp": 100000},
    
    # 2. Yurak massaji (CPR kompressiyasi - 42.5 kg, To'g'ri joy)
    {"lung_p": 0.0, "stomach_p": 0.0, "force_kg": 42.5, "pos_valid": True, "timestamp": 100500},
    {"lung_p": 0.0, "stomach_p": 0.0, "force_kg": 0.0, "pos_valid": True, "timestamp": 101000},
    {"lung_p": 0.0, "stomach_p": 0.0, "force_kg": 44.0, "pos_valid": True, "timestamp": 101500},
    {"lung_p": 0.0, "stomach_p": 0.0, "force_kg": 0.0, "pos_valid": True, "timestamp": 102000},
    
    # 3. Noto'g'ri joy bosilishi (Xato joy)
    {"lung_p": 0.0, "stomach_p": 0.0, "force_kg": 25.0, "pos_valid": False, "timestamp": 102500},
    {"lung_p": 0.0, "stomach_p": 0.0, "force_kg": 0.0, "pos_valid": True, "timestamp": 103000},
    
    # 4. Ambu qopi orqali o'pkaga nafas berish (18.6 cmH2O)
    {"lung_p": 18.6, "stomach_p": 0.0, "force_kg": 0.0, "pos_valid": True, "timestamp": 103500},
    {"lung_p": 0.0, "stomach_p": 0.0, "force_kg": 0.0, "pos_valid": True, "timestamp": 104000},
    
    # 5. Havo oshqozonga ketib qolishi (Stomach pressure 3.5)
    {"lung_p": 5.0, "stomach_p": 3.5, "force_kg": 0.0, "pos_valid": True, "timestamp": 104500},
]

for idx, pkt in enumerate(test_packets, 1):
    try:
        resp = requests.post(URL, json=pkt, timeout=1.0)
        print(f"[{idx}] Yuborildi: {pkt} -> Status: {resp.status_code}")
    except Exception as e:
        print(f"[{idx}] Xatolik (Server yoqilganligini tekshiring): {e}")
    time.sleep(1.0)

print("\nSinov yakunlandi!")
