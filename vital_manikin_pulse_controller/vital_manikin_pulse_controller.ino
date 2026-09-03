/**
 * ======================================================================================
 * GD/H126 TIBBIY MANIKEN VA ICU VITAL MONITOR HAVO PULSATORI (WEB-SYNC)
 * 
 * Vazifasi: Veb-saytdagi tugmalar bosilganda real vaqtda havo nasosi va rele orqali
 *           bo'yin va bilak shlanglarida tomir urishini (BPM) o'zgartirish.
 * 
 * Aloqa: USB Serial (115200 bod) yoki ESP32 UART / Web Serial API
 * ======================================================================================
 */

// ==================== RELE MODULI POLARITETI ====================
// Ko'pchilik Arduino 2/4/8 kanalli ko'k rele modullari (Optopara bilan) Active-LOW bo'ladi!
// Agar sizning relengizda LOW berganda shiqillab yonsa -> RELAY_ACTIVE_LOW = true
// Agar HIGH berganda yonsa -> RELAY_ACTIVE_LOW = false
#define RELAY_ACTIVE_LOW    true

#if RELAY_ACTIVE_LOW
  #define RELAY_ON   LOW
  #define RELAY_OFF  HIGH
#else
  #define RELAY_ON   HIGH
  #define RELAY_OFF  LOW
#endif

// ==================== PINLARNI SOZLASH ====================
#define PIN_PULSE_VALVE   8   // Bo'yin/bilak tomir puls relesi (D8)
#define PIN_RELIEF_VALVE  7   // Ortiqcha bosimni chiqarish / havoni boshqarish solinoid klapani (D7)
#define PIN_HEART_LED     13  // Bortdagi puls LED indikatori (D13)
#define PIN_BUZZER        9   // Monitor beeper tovushi (D9 - Ixtiyoriy)

// ==================== PULS VA BOSIM MOTORIKASI ====================
int targetBPM = 75;                // Veb-saytdan kelgan BPM (0 = Asistoliya/Puls to'xtagan)
int pulseDurationMs = 120;         // Tomirning shishib turish vaqti (ms)
bool isPulseActive = false;        // Hozir D8 puls klapani ochiqmi?
unsigned long lastBeatTime = 0;    // Oxirgi puls vaqti
unsigned long pulseStartTime = 0;  // Klapan ochilgan vaqt
unsigned long nextIntervalMs = 800;// Keyingi zarbagacha bo'lgan vaqt

String inputBuffer = "";           // Veb-saytdan kelayotgan buyruq buferi

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  Serial.println(F("\n========================================================"));
  Serial.println(F("GD/H126 VITAL MONITOR: D7 BOSIM SOLINOIDI & D8 PULS RELESI"));
  Serial.println(F("Kompressor: Doimiy ishlaydi"));
  Serial.println(F("D7: Bosimni chiqarish klapani | D8: Tomir puls klapani"));
  Serial.println(F("Buyruqlar: 0, BPM:75, BPM:135, PUMP:OFF, PUMP:ON, D7:ON, D7:OFF"));
  Serial.println(F("========================================================"));

  pinMode(PIN_PULSE_VALVE, OUTPUT);
  pinMode(PIN_RELIEF_VALVE, OUTPUT);
  pinMode(PIN_HEART_LED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);

  // Boshlang'ich xavfsiz holat:
  digitalWrite(PIN_PULSE_VALVE, RELAY_OFF);
  digitalWrite(PIN_RELIEF_VALVE, RELAY_OFF);
  digitalWrite(PIN_HEART_LED, LOW);
  digitalWrite(PIN_BUZZER, LOW);

  setTargetBPM(75, "Normal Sinus Ritmi (Boshlang'ich)");
}

// ==================== ASOSIY SIKL (LOOP) ====================
void loop() {
  unsigned long currentMillis = millis();

  // 1. Veb-saytdan USB / Serial orqali buyruqlarni o'qish (0ms kechikish)
  readWebCommands();

  // 2. Solinoid klapan va rele pulsatsiyasini boshqarish
  handlePneumaticPulse(currentMillis);
}

// ==================== VEB-SAYTDAN BUYRUQLARNI QABUL QILISH ====================
void readWebCommands() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (inputBuffer.length() > 0) {
        processWebCommand(inputBuffer);
        inputBuffer = "";
      }
    } else {
      inputBuffer += c;
    }
  }
}

void processWebCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();

  // 1. Nol (0) qilish / To'liq to'xtatish (D8 klapan yopiladi, D7 bosimni chiqarish klapani OCHILADI)
  if (cmd == "0" || cmd == "BPM:0" || cmd == "STOP" || cmd == "OFF" || 
      cmd.indexOf("PUMP:OFF") >= 0 || cmd.indexOf("KOMPRESSOR:OFF") >= 0 || 
      cmd.indexOf("DYING") >= 0 || cmd.indexOf("ASYSTOLE") >= 0 || cmd == "5") {
    setTargetBPM(0, "Asistoliya: D8 puls to'xtatildi, D7 ortiqcha bosimni chiqarish ochildi (0 BPM)");
  }
  // 2. To'g'ridan-to'g'ri BPM berilganda (masalan "BPM:135" yoki "BPM:75")
  else if (cmd.startsWith("BPM:")) {
    int bpm = cmd.substring(4).toInt();
    setTargetBPM(bpm, "Veb: Aniq BPM");
  }
  // 3. Kompressor havo oqimini yoqish (PUMP:ON)
  else if (cmd.indexOf("PUMP:ON") >= 0 || cmd.indexOf("KOMPRESSOR:ON") >= 0 || cmd == "START" || cmd == "ON") {
    setTargetBPM(75, "Kompressor Havo oqimi yoqildi (75 BPM)");
  }
  // 4. D7 Solinoidini alohida qo'lda boshqarish
  else if (cmd == "D7:ON" || cmd == "RELIEF:ON") {
    digitalWrite(PIN_RELIEF_VALVE, RELAY_ON);
    Serial.println(F(">>> [D7 SOLINOID: OCHIQ (Bosim chiqmoqda)]"));
  }
  else if (cmd == "D7:OFF" || cmd == "RELIEF:OFF") {
    digitalWrite(PIN_RELIEF_VALVE, RELAY_OFF);
    Serial.println(F(">>> [D7 SOLINOID: YOPIQ (Bosim ushlab turilibdi)]"));
  }
  // 5. D8 Puls klapanini alohida qo'lda boshqarish
  else if (cmd == "D8:ON") {
    digitalWrite(PIN_PULSE_VALVE, RELAY_ON);
    Serial.println(F(">>> [D8 KLAPAN: DOIMIY OCHIQ]"));
  }
  else if (cmd == "D8:OFF") {
    digitalWrite(PIN_PULSE_VALVE, RELAY_OFF);
    Serial.println(F(">>> [D8 KLAPAN: YOPIQ]"));
  }
  // 6. Veb-saytdagi "🟢 Normal (Barqaror)"
  else if (cmd.indexOf("NORMAL") >= 0 || cmd == "1") {
    setTargetBPM(75, "Veb: Normal Sinus (75 BPM)");
  }
  // 7. Veb-saytdagi "⚡ Xuruj boshlanyapti!" (Taxikardiya)
  else if (cmd.indexOf("TACH") >= 0 || cmd.indexOf("ATTACK") >= 0 || cmd == "2") {
    setTargetBPM(135, "Veb: Taxikardiya (135 BPM)");
  }
  // 8. Veb-saytdagi "Bradikardiya"
  else if (cmd.indexOf("BRAD") >= 0 || cmd == "3") {
    setTargetBPM(42, "Veb: Bradikardiya (42 BPM)");
  }
  // 9. Defibrillyatsiya (Shok)
  else if (cmd.indexOf("SHOCK") >= 0) {
    handleDefibShock();
  }
  // 10. ROSC Jonlanish
  else if (cmd.indexOf("ROSC") >= 0 || cmd == "6") {
    handleROSCRevival();
  }
  // 11. Son bo'yicha
  else if (cmd.toInt() > 0) {
    setTargetBPM(cmd.toInt(), "Veb: Qiymat bo'yicha");
  }
}

// ==================== BPM VA INTERVALNI O'RNATISH ====================
void setTargetBPM(int bpm, String reason) {
  targetBPM = bpm;

  if (targetBPM <= 0) {
    // 0 BPM - Asistoliya (Yurak to'xtagan):
    targetBPM = 0;
    nextIntervalMs = 999999;
    isPulseActive = false;
    
    // D8 puls klapani yopiladi (tomirda puls yo'qoladi)
    digitalWrite(PIN_PULSE_VALVE, RELAY_OFF);
    
    // D7 klapani OCHILADI (kompressorning ortiqcha havo bosimi chiqariladi)
    digitalWrite(PIN_RELIEF_VALVE, RELAY_ON);
    
    digitalWrite(PIN_HEART_LED, LOW);
    noTone(PIN_BUZZER);
    Serial.println(F(">>> [NOL QILINDI]: D8 Puls yopildi, D7 Bosim chiqarish ochildi"));
  } else {
    // Normal / Tez / Sekin puls (Yurak uryapti):
    // D7 bosim chiqarish klapani yopiladi (havo tomirga yig'ilsin)
    digitalWrite(PIN_RELIEF_VALVE, RELAY_OFF);
    
    nextIntervalMs = 60000UL / targetBPM;

    // Tezlikka qarab zarba davomiyligi
    if (targetBPM >= 120) pulseDurationMs = 80;
    else if (targetBPM <= 50) pulseDurationMs = 160;
    else pulseDurationMs = 120;
  }

  Serial.print(F(">>> [WEB SYNC] "));
  Serial.print(reason);
  Serial.print(F(" -> BPM: "));
  Serial.print(targetBPM);
  Serial.print(F(" | Interval: "));
  Serial.print(nextIntervalMs);
  Serial.println(F(" ms"));
}

// ==================== PULS VA HAVO SIKLI (MILLIS MOTORIKA) ====================
void handlePneumaticPulse(unsigned long currentMillis) {
  if (targetBPM <= 0) {
    if (isPulseActive) {
      isPulseActive = false;
      digitalWrite(PIN_PULSE_VALVE, RELAY_OFF);
      digitalWrite(PIN_RELIEF_VALVE, RELAY_ON);
      digitalWrite(PIN_HEART_LED, LOW);
      noTone(PIN_BUZZER);
    }
    return;
  }

  // 1. Yangi zarba vaqti keldimi? (D8 rele ochiladi -> Bo'yin/bilak tomiriga havo uriladi)
  if (!isPulseActive && (currentMillis - lastBeatTime >= nextIntervalMs)) {
    isPulseActive = true;
    pulseStartTime = currentMillis;
    lastBeatTime = currentMillis;

    digitalWrite(PIN_PULSE_VALVE, RELAY_ON); // D8 klapan ochildi
    digitalWrite(PIN_HEART_LED, HIGH);       // LED yondi
    tone(PIN_BUZZER, 880, 25);               // Bleep tovushi
  }

  // 2. Tomir shishib turish vaqti (80-160ms) tugadimi? (D8 rele yopiladi -> Havo bo'shashadi)
  if (isPulseActive && (currentMillis - pulseStartTime >= (unsigned long)pulseDurationMs)) {
    isPulseActive = false;
    digitalWrite(PIN_PULSE_VALVE, RELAY_OFF); // D8 klapan yopildi
    digitalWrite(PIN_HEART_LED, LOW);
    noTone(PIN_BUZZER);
  }
}

// ==================== SHOK VA JONLANISH EFFEKTLARI ====================
void handleDefibShock() {
  Serial.println(F("⚡⚡⚡ [DEFIBRILLYATOR SHOK BERILDI!] ⚡⚡⚡"));
  digitalWrite(PIN_PULSE_VALVE, RELAY_ON);
  tone(PIN_BUZZER, 2000, 200);
  delay(200);
  digitalWrite(PIN_PULSE_VALVE, RELAY_OFF);
  noTone(PIN_BUZZER);
  setTargetBPM(75, "Shokdan so'ng Sinus Tiklandi");
}

void handleROSCRevival() {
  Serial.println(F("✨✨✨ [ROSC: BEMOR HU'SHIGA KELDI - PULS TIKLANDI!] ✨✨✨"));
  for (int i = 0; i < 2; i++) {
    tone(PIN_BUZZER, 1046, 70); delay(90);
    tone(PIN_BUZZER, 1318, 70); delay(90);
    tone(PIN_BUZZER, 1568, 100); delay(120);
  }
  setTargetBPM(75, "CPR ROSC Jonlanish");
}
