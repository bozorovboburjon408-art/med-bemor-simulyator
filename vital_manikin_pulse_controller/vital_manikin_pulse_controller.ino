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

// ==================== PINLARNI SOZLASH ====================
#define PIN_PULSE_VALVE   8   // Bo'yin/bilak havo shlangi puls relesi (D8)
#define PIN_PUMP_POWER    7   // Havo nasosi (kompressor) relesi (D7)
#define PIN_HEART_LED     13  // Puls indikator LED (D13)
#define PIN_BUZZER        9   // Monitor beeper tovushi (D9 - Ixtiyoriy)

// ==================== PULS MOTORIKASI O'ZGARUVCHILARI ====================
int targetBPM = 75;                // Veb-saytdan kelgan BPM (0 = Yurak to'xtagan)
int pulseDurationMs = 120;         // Tomirning shishib turish vaqti (ms)
bool isPulseActive = false;        // Hozir rele ochiqmi?
unsigned long lastBeatTime = 0;    // Oxirgi puls vaqti
unsigned long pulseStartTime = 0;  // Rele ochilgan vaqt
unsigned long nextIntervalMs = 800;// Keyingi zarbagacha bo'lgan vaqt

String inputBuffer = "";           // Veb-saytdan kelayotgan buyruq buferi

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  Serial.println(F("\n========================================================"));
  Serial.println(F("GD/H126 VITAL MONITOR TOMIR PULSATORI ISHGA TUSHDI (WEB SYNC)"));
  Serial.println(F("Veb-saytdan buyruqlar kutilmoqda... (115200 bod)"));
  Serial.println(F("========================================================"));

  pinMode(PIN_PULSE_VALVE, OUTPUT);
  pinMode(PIN_PUMP_POWER, OUTPUT);
  pinMode(PIN_HEART_LED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);

  // Boshlang'ich holat
  digitalWrite(PIN_PULSE_VALVE, LOW);
  digitalWrite(PIN_PUMP_POWER, HIGH); // Nasos tayyor
  digitalWrite(PIN_HEART_LED, LOW);
  digitalWrite(PIN_BUZZER, LOW);

  setTargetBPM(75, "Normal Sinus Ritmi (Boshlang'ich)");
}

// ==================== ASOSIY SIKL (LOOP) ====================
void loop() {
  unsigned long currentMillis = millis();

  // 1. Veb-saytdan USB / Serial orqali buyruqlarni o'qish (0ms kechikish)
  readWebCommands();

  // 2. Havo nasosi va rele pulsatsiyasini boshqarish
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

  // 1. To'g'ridan-to'g'ri BPM berilganda: masalan "BPM:135" yoki "135"
  if (cmd.startsWith("BPM:")) {
    int bpm = cmd.substring(4).toInt();
    setTargetBPM(bpm, "Veb: To'g'ridan-to'g'ri BPM");
  }
  // 2. Kompressorni to'g'ridan-to'g'ri yoqish (PUMP:ON / KOMPRESSOR:ON)
  else if (cmd.indexOf("PUMP:ON") >= 0 || cmd.indexOf("KOMPRESSOR:ON") >= 0 || cmd == "START" || cmd == "ON") {
    digitalWrite(PIN_PUMP_POWER, HIGH);
    if (targetBPM <= 0) setTargetBPM(75, "Kompressor Yoqildi (Standart 75 BPM)");
    Serial.println(F(">>> [KOMPRESSOR (PIN D7) YOQILDI]"));
  }
  // 3. Kompressorni to'g'ridan-to'g'ri o'chirish (PUMP:OFF / KOMPRESSOR:OFF)
  else if (cmd.indexOf("PUMP:OFF") >= 0 || cmd.indexOf("KOMPRESSOR:OFF") >= 0 || cmd == "STOP" || cmd == "OFF") {
    digitalWrite(PIN_PUMP_POWER, LOW);
    digitalWrite(PIN_PULSE_VALVE, LOW);
    digitalWrite(PIN_HEART_LED, LOW);
    targetBPM = 0;
    Serial.println(F(">>> [KOMPRESSOR VA PULS RELESI TO'XTATILDI]"));
  }
  // 4. Veb-saytdagi "🟢 Normal (Barqaror)" tugmasi
  else if (cmd.indexOf("NORMAL") >= 0 || cmd == "1") {
    setTargetBPM(75, "Veb: Normal Sinus (75 BPM)");
  }
  // 5. Veb-saytdagi "⚡ Xuruj boshlanyapti!" (Taxikardiya) tugmasi
  else if (cmd.indexOf("TACH") >= 0 || cmd.indexOf("ATTACK") >= 0 || cmd == "2") {
    setTargetBPM(135, "Veb: Taxikardiya Xuruji (135 BPM)");
  }
  // 6. Veb-saytdagi "Bradikardiya" tugmasi
  else if (cmd.indexOf("BRAD") >= 0 || cmd == "3") {
    setTargetBPM(42, "Veb: Bradikardiya (42 BPM)");
  }
  // 7. Veb-saytdagi "🚨 Bemorni yo'qotyapmiz! / Asistoliya" tugmasi
  else if (cmd.indexOf("DYING") >= 0 || cmd.indexOf("ASYSTOLE") >= 0 || cmd == "5") {
    setTargetBPM(0, "Veb: ASISTOLIYA - Puls to'xtadi (0 BPM)");
  }
  // 8. Veb-saytdagi "Defibrillyatsiya (Shok)" tugmasi
  else if (cmd.indexOf("SHOCK") >= 0) {
    handleDefibShock();
  }
  // 9. Veb-saytdagi "✨ Bemor Tirildi (ROSC)" tugmasi
  else if (cmd.indexOf("ROSC") >= 0 || cmd == "6") {
    handleROSCRevival();
  }
  // 10. Agar shunchaki son kelsa (masalan "90")
  else if (cmd.toInt() > 0) {
    setTargetBPM(cmd.toInt(), "Veb: Qiymat bo'yicha");
  }
}

// ==================== BPM VA INTERVALNI O'RNATISH ====================
void setTargetBPM(int bpm, String reason) {
  targetBPM = bpm;

  if (targetBPM <= 0) {
    // Puls yo'q (Yurak to'xtagan)
    nextIntervalMs = 999999;
    digitalWrite(PIN_PULSE_VALVE, LOW);
    digitalWrite(PIN_PUMP_POWER, LOW); // Nasos o'chadi
    digitalWrite(PIN_HEART_LED, LOW);
  } else {
    // Normal / Tez / Sekin puls
    digitalWrite(PIN_PUMP_POWER, HIGH); // Nasos yoqiladi
    nextIntervalMs = 60000UL / targetBPM;

    // Tezlikka qarab havoning zarba davomiyligi
    if (targetBPM >= 120) pulseDurationMs = 80;        // Qisqa tezkor zarba
    else if (targetBPM <= 50) pulseDurationMs = 160;   // Cho'ziqroq kuchli zarba
    else pulseDurationMs = 120;                        // Standart me'yor
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
  if (targetBPM <= 0) return; // Puls to'xtagan

  // 1. Yangi zarba vaqti keldimi? (Rele ochiladi -> Tomir shishadi)
  if (!isPulseActive && (currentMillis - lastBeatTime >= nextIntervalMs)) {
    isPulseActive = true;
    pulseStartTime = currentMillis;
    lastBeatTime = currentMillis;

    digitalWrite(PIN_PULSE_VALVE, HIGH); // Rele ochildi -> Bo'yin/qo'lga havo uriladi
    digitalWrite(PIN_HEART_LED, HIGH);   // Bortdagi LED yondi
    tone(PIN_BUZZER, 880, 25);           // Monitor bleep ovozi
  }

  // 2. Tomir shishib turish vaqti (80-160ms) tugadimi? (Rele yopiladi -> Havo bo'shashadi)
  if (isPulseActive && (currentMillis - pulseStartTime >= (unsigned long)pulseDurationMs)) {
    isPulseActive = false;
    digitalWrite(PIN_PULSE_VALVE, LOW);  // Rele yopildi -> Tomir bo'shashdi
    digitalWrite(PIN_HEART_LED, LOW);
    noTone(PIN_BUZZER);
  }
}

// ==================== SHOK VA JONLANISH EFFEKTLARI ====================
void handleDefibShock() {
  Serial.println(F("⚡⚡⚡ [DEFIBRILLYATOR SHOK BERILDI!] ⚡⚡⚡"));
  digitalWrite(PIN_PULSE_VALVE, HIGH);
  tone(PIN_BUZZER, 2000, 200);
  delay(200);
  digitalWrite(PIN_PULSE_VALVE, LOW);
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
