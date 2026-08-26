#include <Arduino.h>
#include <HX711.h>
#include <ArduinoJson.h>

// ==================== 1. PIN SOZLAMALARI ====================
// O'pka datchigi (HX711)
const int LUNG_DOUT = 32;
const int LUNG_SCK  = 33;

// Oshqozon datchigi (HX711)
const int STOMACH_DOUT = 25;
const int STOMACH_SCK  = 26;

// Ko'krak kompressiya datchigi (HX711 - Load Cell)
const int LOADCELL_DOUT = 27;
const int LOADCELL_SCK  = 14;

// Qo'l joylashuvi tugmasi (Position Button)
const int POSITION_BTN_PIN = 13;

// Ukol / Inyeksiya datchigi (Touch / Tugma)
const int TOUCH_PIN = 4;

// ==================== 2. DATCHIK OBYEKTLARI ====================
HX711 lungSensor;
HX711 stomachSensor;
HX711 forceSensor;

// Oxirgi o'qilgan qiymatlarni saqlash (Non-blocking)
float lastForceVal   = 0.0;
float lastLungVal    = 0.0;
float lastStomachVal = 0.0;

// ==================== 3. CPR STANDARTLARI VA TAHLIL ====================
const float NOISE_THRESHOLD   = 4.0;  // 4 kg dan pastini shovqin deb hisoblash
const float MIN_TARGET_FORCE  = 40.0; // Minimal to'g'ri kompressiya (40 kg ~ 5 sm)
const float MAX_TARGET_FORCE  = 55.0; // Maksimal to'g'ri kompressiya (55 kg ~ 6 sm)
const float RECOIL_THRESHOLD  = 5.0;  // To'liq bo'shatish (recoil) chegarasi

enum CPRState { IDLE, COMPRESSING, RECOILING };
CPRState currentState = IDLE;

float currentPeakForce = 0.0;
unsigned long lastCompressionTime = 0;
float currentBPM = 0.0;
int compressionCount = 0;

bool lastDepthCorrect  = false;
bool lastRecoilCorrect = true;
bool lastRateCorrect   = false;

// ==================== 4. CPR KOMPRESSIYANI TAHLIL QILISH ====================
void processCPRCompression(float force, unsigned long now) {
  switch (currentState) {
    case IDLE:
      if (force > NOISE_THRESHOLD) {
        currentState = COMPRESSING;
        currentPeakForce = force;
      }
      break;

    case COMPRESSING:
      if (force > currentPeakForce) {
        currentPeakForce = force;
      }

      // Kuch cho'qqidan 3 kg ga pasayganda (dekompressiya boshlandi)
      if (force < (currentPeakForce - 3.0)) {
        currentState = RECOILING;
        
        if (lastCompressionTime > 0) {
          unsigned long delta = now - lastCompressionTime;
          if (delta > 200 && delta < 2000) {
            currentBPM = 60000.0 / (float)delta;
          }
        }
        lastCompressionTime = now;
        compressionCount++;

        // Sifat tekshiruvi
        lastDepthCorrect = (currentPeakForce >= MIN_TARGET_FORCE && currentPeakForce <= MAX_TARGET_FORCE);
        lastRateCorrect  = (currentBPM >= 100.0 && currentBPM <= 120.0);
      }
      break;

    case RECOILING:
      if (force <= RECOIL_THRESHOLD) {
        lastRecoilCorrect = true;
        currentState = IDLE;
      } else if (force > (currentPeakForce - 1.0) && force > NOISE_THRESHOLD) {
        // To'liq bo'shatmasdan yana bosa boshladi
        lastRecoilCorrect = false;
        currentState = COMPRESSING;
        currentPeakForce = force;
      }
      break;
  }

  // 2.5 soniya davomida bosilmasa, tezlikni 0 qilish
  if (now - lastCompressionTime > 2500) {
    currentBPM = 0.0;
  }
}

// ==================== 5. SETUP ====================
void setup() {
  // UART 115200 baud
  Serial.begin(115200);
  delay(200);

  // Raqamli pinlar
  pinMode(POSITION_BTN_PIN, INPUT_PULLUP);
  pinMode(TOUCH_PIN, INPUT_PULLDOWN); // Ukol pini (HIGH bo'lsa ukol qilindi)

  // HX711 modullarini boshlash
  lungSensor.begin(LUNG_DOUT, LUNG_SCK);
  stomachSensor.begin(STOMACH_DOUT, STOMACH_SCK);
  forceSensor.begin(LOADCELL_DOUT, LOADCELL_SCK);

  // Xavfsiz nolga tenglashtirish (Tare timeout bilan - qotib qolmasligi uchun)
  if (lungSensor.wait_ready_timeout(300)) lungSensor.tare();
  if (stomachSensor.wait_ready_timeout(300)) stomachSensor.tare();
  if (forceSensor.wait_ready_timeout(300)) forceSensor.tare();

  // Kalibrovka koeffitsientlari
  lungSensor.set_scale(420.0);
  stomachSensor.set_scale(420.0);
  forceSensor.set_scale(2280.0);
}

unsigned long lastStreamTime = 0;

// ==================== 6. ASOSIY LOOP ====================
void loop() {
  unsigned long now = millis();

  // --- NON-BLOCKING DATCHIK O'QISH (QOTIB QOLMAYDI) ---
  // 1. Kuch datchigi (HX711)
  if (forceSensor.is_ready()) {
    float raw = forceSensor.get_units(1);
    lastForceVal = (raw > 0) ? raw : 0.0;
  }

  // 2. O'pka bosimi (HX711)
  if (lungSensor.is_ready()) {
    float raw = lungSensor.get_units(1);
    lastLungVal = (raw > 0) ? raw : 0.0;
  }

  // 3. Oshqozon bosimi (HX711)
  if (stomachSensor.is_ready()) {
    float raw = stomachSensor.get_units(1);
    lastStomachVal = (raw > 0) ? raw : 0.0;
  }

  // 4. Qo'l joyi (13-pin)
  bool posValid = (digitalRead(POSITION_BTN_PIN) == LOW);

  // 5. Ukol datchigi (4-pin)
  int touchVal = digitalRead(TOUCH_PIN);
  bool injectionDetected = (touchVal == HIGH);

  // --- CPR KOMPRESSIYA TAHLILI ---
  processCPRCompression(lastForceVal, now);

  // --- TELEMETRIYA UZATISH (HAR 50 MS DA) ---
  if (now - lastStreamTime >= 50) {
    lastStreamTime = now;

    // JSON yaratish va UART orqali yuborish
    StaticJsonDocument<256> doc;
    doc["f_curr"]    = round(lastForceVal * 10.0) / 10.0;
    doc["bpm"]       = round(currentBPM);
    doc["count"]     = compressionCount;
    doc["d_ok"]      = lastDepthCorrect;
    doc["r_ok"]      = lastRecoilCorrect;
    doc["bpm_ok"]    = lastRateCorrect;
    doc["pos_ok"]    = posValid;
    doc["lung_p"]    = round(lastLungVal * 10.0) / 10.0;
    doc["stomach_p"] = round(lastStomachVal * 10.0) / 10.0;
    doc["inj_ok"]    = injectionDetected;

    serializeJson(doc, Serial);
    Serial.println();
  }
}
