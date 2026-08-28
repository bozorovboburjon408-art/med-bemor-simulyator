import time
import json
import requests
import serial
import serial.tools.list_ports
import threading

TARGET_PORTS = [8600, 8500, 8000]
BAUD_RATE = 115200

# Connection pooling session (Keep-Alive for sub-millisecond HTTP posts)
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=5, pool_maxsize=10, max_retries=0)
session.mount('http://', adapter)

active_urls = []

def scan_active_servers():
    """Faol ishlayotgan monitor portlarini aniqlash (Har 3 soniyada)"""
    global active_urls
    while True:
        alive = []
        for p in TARGET_PORTS:
            url = f"http://127.0.0.1:{p}/api/telemetry"
            try:
                # Fast ping
                r = session.get(f"http://127.0.0.1:{p}/", timeout=0.15)
                if r.status_code == 200:
                    alive.append(url)
            except:
                pass
        active_urls = alive
        time.sleep(3.0)

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

def send_telemetry_async(pkt):
    """Ma'lumotni fonda kechikishsiz yuborish"""
    for url in list(active_urls):
        try:
            session.post(url, json=pkt, timeout=0.04)
        except:
            pass

def main():
    print("=" * 68)
    print("  ⚡ ULTRA-TEZKOR ESP32 UART KO'PRIGI (ZERO-LAG 0ms ENGINE)")
    print("=" * 68)
    print(f"  Baud tezligi:    {BAUD_RATE}")
    print("=" * 68)
    print("  ⚠️  MUHIM: Arduino IDE dagi 'Serial Monitor' oynasini yoping!")
    print("=" * 68 + "\n")

    # Start server discovery thread
    t = threading.Thread(target=scan_active_servers, daemon=True)
    t.start()

    while True:
        port = find_esp32_port()
        if not port:
            print("⏳ ESP32 USB kabeli kutilmoqda...", end="\r")
            time.sleep(1.0)
            continue

        print(f"\n🔍 Port aniqlandi: {port}. Ulanish o'rnatilmoqda...")
        try:
            with serial.Serial(port, BAUD_RATE, timeout=0.1) as ser:
                # Flush old hardware buffers
                ser.reset_input_buffer()
                print(f"✅ {port} muvaffaqiyatli ulandi! Jonli oqim boshlandi (Kechikish: 0ms)...\n")
                
                packet_count = 0
                line_buffer = ""
                last_print_time = 0

                while True:
                    # ZERO-LAG BUFFER FLUSH: Agar buferda to'planib qolsa, eng oxirgisini olamiz!
                    in_waiting = ser.in_waiting
                    if in_waiting > 120:
                        raw_data = ser.read(in_waiting).decode('utf-8', errors='ignore')
                        lines = (line_buffer + raw_data).splitlines()
                        line_buffer = lines[-1] if not raw_data.endswith('\n') else ""
                        valid_lines = [l.strip() for l in lines if l.strip().startswith('{') and l.strip().endswith('}')]
                        if valid_lines:
                            target_line = valid_lines[-1] # Eng oxirgi yangi paket!
                        else:
                            continue
                    else:
                        target_line = ser.readline().decode('utf-8', errors='ignore').strip()

                    if not target_line or not (target_line.startswith('{') and target_line.endswith('}')):
                        continue

                    try:
                        pkt = json.loads(target_line)
                        packet_count += 1

                        # Non-blocking instant dispatch to web app
                        threading.Thread(target=send_telemetry_async, args=(pkt,), daemon=True).start()

                        # Terminal print rate limit (har 150 ms da bitta satr, konsol qotmasligi uchun)
                        now = time.time()
                        if now - last_print_time >= 0.15:
                            last_print_time = now
                            f_val = pkt.get('force', pkt.get('f_curr', 0.0))
                            lung_p = pkt.get('lung_p', 0.0)
                            stomach_p = pkt.get('stomach_p', 0.0)
                            pos_btn = pkt.get('pos_btn', pkt.get('pos_ok', 0))
                            inj_btn = pkt.get('inj_btn', pkt.get('inj_ok', 0))

                            pos_str = "🟢 TO'G'RI" if (pos_btn == 1 or pos_btn is True) else "⚪ BO'SH"
                            inj_str = "💉 UKOL" if (inj_btn == 1 or inj_btn is True) else "-"

                            print(f"📡 [#{packet_count}] Kuch: {f_val:>4.1f}kg | Joyi: {pos_str} | O'pka: {lung_p:>4.1f}kPa | Oshqozon: {stomach_p:>4.1f} | {inj_str}   ", end="\r")

                    except json.JSONDecodeError:
                        pass

        except serial.SerialException as e:
            print(f"\n⚠️ {port} band yoki uzildi: {e}")
            time.sleep(2)
        except Exception as e:
            print(f"❌ Xatolik: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
