import time
import json
import requests
import serial
import serial.tools.list_ports

TARGET_URLS = [
    "http://localhost:8500/api/telemetry",
    "http://localhost:8000/api/telemetry"
]
BAUD_RATE = 115200

def find_esp32_port():
    """Mavjud COM portlarni skanerlash va ESP32 ni topish"""
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        return None
    
    for p in ports:
        desc = (p.description or "").lower()
        if any(keyword in desc for keyword in ["ch340", "cp210", "usb-serial", "uart", "esp", "silicon", "prolific", "ftdi"]):
            return p.device
            
    return ports[0].device

def main():
    print("=" * 68)
    print("  🔌 ESP32 UART -> REANIMATSIYA MONITORI KO'PRIGI (SERIAL BRIDGE)")
    print("=" * 68)
    print(f"  Baud tezligi:    {BAUD_RATE}")
    print("=" * 68)
    print("  ⚠️  MUHIM: Arduino IDE dagi 'Serial Monitor' oynasini yoping!")
    print("  (Aks holda Windows portni ochishga ruxsat bermaydi)")
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
                            
                            # Send to active monitor instances
                            for url in TARGET_URLS:
                                try:
                                    requests.post(url, json=pkt, timeout=0.05)
                                except:
                                    pass

                            # Parse fields
                            f_val = pkt.get('force', pkt.get('f_curr', 0.0))
                            lung_p = pkt.get('lung_p', 0.0)
                            stomach_p = pkt.get('stomach_p', 0.0)
                            pos_btn = pkt.get('pos_btn', pkt.get('pos_ok', 0))
                            inj_btn = pkt.get('inj_btn', pkt.get('inj_ok', 0))
                            
                            pos_str = "✅ TO'G'RI" if (pos_btn == 1 or pos_btn is True) else "❌ XATO"
                            inj_str = "💉 UKOL" if (inj_btn == 1 or inj_btn is True) else "-"
                            
                            print(f"📡 [#{packet_count}] Kuch: {f_val:>4.1f} kg | Joyi: {pos_str} | O'pka: {lung_p:>4.1f} | Oshqozon: {stomach_p:>4.1f} | {inj_str}")
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
