/**
 * ======================================================================================
 * GD/H126 VITAL MONITOR VA MANIKEN VIBRATOR PULSATOR DASTURI (WEB-SYNC)
 * 
 * Vazifasi: Veb-saytdagi tugmalar orqali bo'yin va bilakdagi vibrator motorchaga
 *           qisqa mikro-impulslar (40-80ms) berib, haqiqiy yurak urishi (tuk... tuk...)
 *           effektini hosil qilish.
 * 
 * Aloqa tezligi: 115200 bod (USB Serial / Web Serial API)
 * ======================================================================================
 */

// ==================== PINLAR ====================
#define PIN_VIBRO_MOTOR   8   // Vibrator motorcha / Rele pini (D8)
#define PIN_HEART_LED     13  // Bortdagi LED indikator (D13)
#define PIN_BUZZER        9   // Ovozli monitor biip signali (D9 - Ixtiyoriy)

// ==================== SOZLAMALAR ====================
int targetBPM = 75;                // Veb-saytdan kelgan BPM (0 = Asistoliya)
int vibroPulseMs = 60;             // Motorchaning aylanish davomiyligi (ms) - ZARBA KUCHI
bool isMotorRunning = false;       // Hozir motorcha aylanmoqdami?
unsigned long lastBeatTime = 0;    // Oxirgi zarba vaqti
unsigned long motorStartTime = 0;  // Motorcha yoqilgan vaqt
unsigned long nextIntervalMs = 800;// Keyingi zarbagacha bo'lgan vaqt

String inputBuffer = "";           // Veb-saytdan keluvchi xabarlar buferi

// ==================== SETUP ====================
void setup() {
  Serial.begin(115200);
  Serial.println(F("\n========================================================"));
  Serial.println(F("GD/H126 VIBROMOTORLI YURAK PULSATORI TAYYOR (WEB SYNC)"));
  Serial.println(F("Buyruqlar: BPM:75, BPM:135, BPM:42, BPM:0, ROSC, SHOCK"));
  Serial.println(F("========================================================"));

  pinMode(PIN_VIBRO_MOTOR, OUTPUT);
  pinMode(PIN_HEART_LED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);

  digitalWrite(PIN_VIBRO_MOTOR, LOW);
  digitalWrite(PIN_HEART_LED, LOW);
  digitalWrite(PIN_BUZZER, LOW);

  setTargetBPM(75, "Normal Sinus Ritmi (75 BPM)");
}

// ==================== ASOSIY SIKL ====================
void loop() {
  unsigned long currentMillis = millis();

  // 1. Veb-saytdan USB orqali buyruqlarni o'qish (0ms kechikish)
  readSerialWebCommands();

  // 2. Mikro-impulsli yurak urish motorikasi
  handleVibroPulseEngine(currentMillis);
}

// ==================== VEB-SAYTDAN BUYRUQLARNI QABUL QILISH ====================
void readSerialWebCommands() {
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

  // 1. To'g'ridan-to'g'ri BPM (masalan "BPM:135" yoki "BPM:42")
  if (cmd.startsWith("BPM:")) {
    int bpm = cmd.substring(4).toInt();
    setTargetBPM(bpm, "Veb: Aniq BPM");
  }
  // 2. Veb-saytdagi "🟢 Normal" tugmasi
  else if (cmd.indexOf("NORMAL") >= 0 || cmd == "1") {
    setTargetBPM(75, "Veb: Normal Sinus (75 BPM)");
  }
  // 3. Veb-saytdagi "⚡ Taxikardiya" tugmasi
  else if (cmd.indexOf("TACH") >= 0 || cmd.indexOf("ATTACK") >= 0 || cmd == "2") {
    setTargetBPM(135, "Veb: Taxikardiya (135 BPM)");
  }
  // 4. Veb-saytdagi "Bradikardiya" tugmasi
  else if (cmd.indexOf("BRAD") >= 0 || cmd == "3") {
    setTargetBPM(42, "Veb: Bradikardiya (42 BPM)");
  }
  // 5. Veb-saytdagi "🚨 Bemorni yo'qotyapmiz / Asistoliya" tugmasi
  else if (cmd.indexOf("DYING") >= 0 || cmd.indexOf("ASYSTOLE") >= 0 || cmd.indexOf("STOP") >= 0 || cmd == "5") {
    setTargetBPM(0, "Veb: ASISTOLIYA - Puls to'xtadi (0 BPM)");
  }
  // 6. Veb-saytdagi "Defibrillyatsiya (Shok)" tugmasi
  else if (cmd.indexOf("SHOCK") >= 0) {
    handleDefibShock();
  }
  // 7. Veb-saytdagi "✨ Bemor Tirildi (ROSC)" tugmasi
  else if (cmd.indexOf("ROSC") >= 0 || cmd == "6") {
    handleROSCRevival();
  }
  // 8. Shunchaki raqam kelsa
  else if (cmd.toInt() > 0) {
    setTargetBPM(cmd.toInt(), "Veb: Raqam");
  }
}

// ==================== BPM VA ZARBA VAQTINI O'RNATISH ====================
void setTargetBPM(int bpm, String reason) {
  targetBPM = bpm;

  if (targetBPM <= 0) {
    // Puls to'xtagan (Yurak urmayapti)
    nextIntervalMs = 999999;
    digitalWrite(PIN_VIBRO_MOTOR, LOW);
    digitalWrite(PIN_HEART_LED, LOW);
  } else {
    nextIntervalMs = 60000UL / targetBPM;

    // Ritmga qarab zarbaning qisqaligi va o'tkirligi:
    // Taxikardiyada qisqa tez zarba (45ms), Bradikardiyada kuchliroq og'ir zarba (80ms)
    if (targetBPM >= 120) vibroPulseMs = 45;       // Tezkor qisqa zarba
    else if (targetBPM <= 50) vibroPulseMs = 85;   // Og'ir, sekin zarba
    else vibroPulseMs = 60;                        // Standart me'yor (75 BPM)
  }

  Serial.print(F(">>> [VIBRO SYNC] "));
  Serial.print(reason);
  Serial.print(F(" -> BPM: "));
  Serial.print(targetBPM);
  Serial.print(F(" | Interval: "));
  Serial.print(nextIntervalMs);
  Serial.print(F("ms | Zarba davomiyligi: "));
  Serial.print(vibroPulseMs);
  Serial.println(F("ms"));
}

// ==================== MIKRO-IMPULSLI PULS MOTORIKASI ====================
void handleVibroPulseEngine(unsigned long currentMillis) {
  if (targetBPM <= 0) return; // Asistoliya (yurak to'xtagan)

  // 1. Yangi zarba vaqti keldimi? (Motorcha yoqiladi)
  if (!isMotorRunning && (currentMillis - lastBeatTime >= nextIntervalMs)) {
    isMotorRunning = true;
    motorStartTime = currentMillis;
    lastBeatTime = currentMillis;

    digitalWrite(PIN_VIBRO_MOTOR, HIGH); // Motorcha juda qisqa vaqtga yoqildi
    digitalWrite(PIN_HEART_LED, HIGH);    // LED yondi
    tone(PIN_BUZZER, 880, 20);            // Qisqa biip
  }

  // 2. Mikro-zarba vaqti (45-80ms) tugadimi? (Motorcha darhol o'chiriladi)
  if (isMotorRunning && (currentMillis - motorStartTime >= (unsigned long)vibroPulseMs)) {
    isMotorRunning = false;
    digitalWrite(PIN_VIBRO_MOTOR, LOW);   // Motorcha o'chdi (g'uvillashga ulgurmaydi!)
    digitalWrite(PIN_HEART_LED, LOW);
    noTone(PIN_BUZZER);
  }
}

// ==================== SHOK VA JONLANISH ====================
void handleDefibShock() {
  Serial.println(F("⚡⚡⚡ [DEFIBRILLYATOR SHOK] ⚡⚡⚡"));
  digitalWrite(PIN_VIBRO_MOTOR, HIGH);
  tone(PIN_BUZZER, 2000, 150);
  delay(150);
  digitalWrite(PIN_VIBRO_MOTOR, LOW);
  setTargetBPM(75, "Shokdan so'ng Sinus Tiklandi");
}

void handleROSCRevival() {
  Serial.println(F("✨✨✨ [ROSC: BEMORNING PULSI TIKLANDI!] ✨✨✨"));
  for (int i = 0; i < 2; i++) {
    digitalWrite(PIN_VIBRO_MOTOR, HIGH);
    tone(PIN_BUZZER, 1046, 60); delay(70);
    digitalWrite(PIN_VIBRO_MOTOR, LOW);
    tone(PIN_BUZZER, 1318, 60); delay(70);
  }
  setTargetBPM(75, "CPR ROSC Jonlanish");
}
