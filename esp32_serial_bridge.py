import time
import json
import requests
import serial
import serial.tools.list_ports

TARGET_URL = "http://localhost:8500/api/telemetry"
BAUD_RATE = 115200

def find_esp32_port():
    """Mavjud COM portlarni skanerlash va ESP32 ni topish"""
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        return None
    
    for p in ports:
        desc = (p.description or "").lower()
        if any(keyword in desc for keyword in ["ch340", "cp210", "usb-serial", "uart", "esp", "silicon", "prolific"]):
            return p.device
            
    return ports[0].device

def main():
    print("=" * 68)
    print("  🔌 ESP32 UART -> REANIMATSIYA MONITORI KO'PRIGI (SERIAL BRIDGE)")
    print("=" * 68)
    print(f"  Baud tezligi:    {BAUD_RATE}")
    print(f"  Monitor manzili: {TARGET_URL}")
    print("=" * 68)
    print("  ⚠️  MUHIM: Arduino IDE dagi 'Serial Monitor' oynasini yoping!")
    print("  (Aks holda Windows portni boshqa dasturga ochishga ruxsat bermaydi)")
    print("=" * 68 + "\n")

    while True:
        port = find_esp32_port()
        if not port:
            print("⏳ ESP32 USB kabeli kompyuterga ulanishi kutilmoqda...", end="\r")
            time.sleep(1.5)
            continue

        print(f"\n🔍 Port aniqlandi: {port}. Ulanishga urinilmoqda...")
        try:
            with serial.Serial(port, BAUD_RATE, timeout=1.0) as ser:
                print(f"✅ {port} porti muvaffaqiyatli ochildi!")
                print("🚀 Jonli telemetriya oqimi monitorga uzatilmoqda...\n")
                
                packet_count = 0
                while True:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if not line:
                        continue
                    
                    if line.startswith("{") and line.endswith("}"):
                        try:
                            pkt = json.loads(line)
                            packet_count += 1
                            # Send to Monitor Web App
                            try:
                                requests.post(TARGET_URL, json=pkt, timeout=0.1)
                                f_curr = pkt.get('f_curr', 0.0)
                                bpm = pkt.get('bpm', 0)
                                d_ok = pkt.get('d_ok', False)
                                pos_ok = pkt.get('pos_ok', False)
                                lung_p = pkt.get('lung_p', 0.0)
                                inj_ok = pkt.get('inj_ok', False)
                                
                                print(f"📡 [ESP32 #{packet_count}] Kuch: {f_curr}kg | BPM: {bpm} | Chuqurlik: {'✅' if d_ok else '❌'} | Joyi: {'✅' if pos_ok else '❌'} | O'pka: {lung_p} | Ukol: {'💉' if inj_ok else '-'}")
                            except Exception as req_err:
                                # Monitor might not be open yet
                                pass
                        except json.JSONDecodeError:
                            pass
        except serial.SerialException as e:
            print(f"\n⚠️ {port} band yoki uzildi: {e}")
            print("👉 Iltimos, Arduino IDE dagi Serial Monitor oynasini yoping va qayta urinib ko'ring!\n")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Xatolik: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
