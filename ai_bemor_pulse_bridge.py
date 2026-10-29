"""
AI Bemor Simulyatori uchun Avtomatik USB Puls Ko'prigi
Arduino 9600 bod tezlikda ulanadi va har bir kasallikka mos BPM yuboradi.
"""
import re
import time
import threading

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None

active_pulse_port = None
pulse_serial_lock = threading.Lock()
current_active_bpm = 75  # Standart boshlang'ich BPM

def send_pulse_bpm(val):
    """
    Arduinoga faqat toza butun son ko'rinishida BPM yuboradi.
    Masalan: 75 -> "75\n", "BPM:135" -> "135\n"
    Hech qanday harf ("T", "B", "A", "S") yuborilmaydi!
    """
    global active_pulse_port, current_active_bpm
    if not val:
        return False

    # Faqat raqamlarni ajratib olish
    digits = re.sub(r'[^0-9]', '', str(val))
    if not digits:
        return False

    bpm_int = int(digits)
    if bpm_int <= 0:
        return False

    current_active_bpm = bpm_int

    if not serial:
        print(f"[PULS]: pyserial o'rnatilmagan, lekin BPM belgilandi: {bpm_int}")
        return False

    with pulse_serial_lock:
        if active_pulse_port and active_pulse_port.is_open:
            try:
                msg = f"{bpm_int}\n"
                active_pulse_port.write(msg.encode("utf-8"))
                active_pulse_port.flush()
                print(f"💓 [AI Bemor Puls]: Arduinoga yuborildi: {bpm_int} BPM")
                return True
            except Exception as e:
                print(f"⚠️ [PULS]: Portga yozish xatosi: {e}")
                try: active_pulse_port.close()
                except: pass
                active_pulse_port = None
    return False

def auto_detect_pulse_port():
    """
    USB portga ulangan Arduinoni avtomatik aniqlash va 9600 bodda ulash.
    """
    global active_pulse_port, current_active_bpm
    if not serial:
        return

    while True:
        if not active_pulse_port or not active_pulse_port.is_open:
            try:
                ports = list(serial.tools.list_ports.comports())
                for p in ports:
                    desc = (p.description or "").lower()
                    hwid = (p.hwid or "").lower()
                    # Arduino, FTDI, CH340, CP210 yoki umumiy USB-Serial drayverlar
                    if any(k in desc or k in hwid for k in ["ch340", "cp210", "usb-serial", "arduino", "uart", "ftdi", "silicon", "prolific"]):
                        try:
                            # 9600 bod tezlikda ulanish
                            s = serial.Serial(p.device, 9600, timeout=0.2)
                            time.sleep(1.8) # Arduino yuklanishini kutish
                            active_pulse_port = s
                            print(f"✅ [PULS]: Arduino Pulsatori ulandi ({p.device}, 9600 bod)")
                            # Ulanishi bilan joriy BPM ni yuborib tizimni faollashtiramiz
                            s.write(f"{current_active_bpm}\n".encode("utf-8"))
                            s.flush()
                            break
                        except Exception:
                            pass
            except Exception:
                pass
        time.sleep(2.5)

# Avtomatik skanerlash fon threadida doimiy ishlaydi
threading.Thread(target=auto_detect_pulse_port, daemon=True).start()
