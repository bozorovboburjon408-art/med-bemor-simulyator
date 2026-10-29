/*
 ====================================================================
   🩺 ESP32 BEMOR MANIKENI — BARCHA SENSORLARNI DIAGNOSTIKA QILISH
 ====================================================================
   Ushbu dastur har bir datchikni ALOHIDA tekshiradi va Arduino IDE
   Serial Monitorida (115200 baud) qaysi datchik ishlayotgani va 
   qaysi birida aloqa yo'qligini aniq ko'rsatib beradi.
 ====================================================================
*/

#include <Arduino.h>
#include <HX711.h>

// --- PINLAR ---
const int LUNG_DOUT        = 32;
const int LUNG_SCK         = 33;

const int STOMACH_DOUT     = 25;
const int STOMACH_SCK      = 26;

const int LOADCELL_DOUT    = 27;
const int LOADCELL_SCK     = 14;

const int POSITION_BTN_PIN = 13;
const int TOUCH_PIN        = 4;

HX711 lungSensor;
HX711 stomachSensor;
HX711 forceSensor;

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("\n========================================================");
  Serial.println("  🩺 MANIKEN SENSORLARINI DIAGNOSTIKA QILISH BOSHLANDI");
  Serial.println("========================================================");

  // Pinlarni sozlash
  pinMode(POSITION_BTN_PIN, INPUT_PULLUP);
  pinMode(TOUCH_PIN, INPUT_PULLDOWN);

  // Datchiklarni boshlash
  lungSensor.begin(LUNG_DOUT, LUNG_SCK);
  stomachSensor.begin(STOMACH_DOUT, STOMACH_SCK);
  forceSensor.begin(LOADCELL_DOUT, LOADCELL_SCK);

  Serial.println("1. Datchiklar ulanishi tekshirilmoqda...\n");

  // Har bir HX711 ning aloqasini alohida tekshirish
  if (forceSensor.wait_ready_timeout(500)) {
    Serial.println("  [1] KO'KRAK KUCHI (HX711: Pin 27, 14) -> ✅ ULANDI (ISHLAYAPTI)");
    forceSensor.set_scale(2280.0);
  } else {
    Serial.println("  [1] KO'KRAK KUCHI (HX711: Pin 27, 14) -> ❌ ALOQA YO'Q (Simlarni tekshiring!)");
  }

  if (lungSensor.wait_ready_timeout(500)) {
    Serial.println("  [2] O'PKA BOSIMI  (HX711: Pin 32, 33) -> ✅ ULANDI (ISHLAYAPTI)");
    lungSensor.set_scale(420.0);
  } else {
    Serial.println("  [2] O'PKA BOSIMI  (HX711: Pin 32, 33) -> ❌ ALOQA YO'Q (Simlarni tekshiring!)");
  }

  if (stomachSensor.wait_ready_timeout(500)) {
    Serial.println("  [3] OSHQOZON     (HX711: Pin 25, 26) -> ✅ ULANDI (ISHLAYAPTI)");
    stomachSensor.set_scale(420.0);
  } else {
    Serial.println("  [3] OSHQOZON     (HX711: Pin 25, 26) -> ❌ ALOQA YO'Q (Simlarni tekshiring!)");
  }

  Serial.println("--------------------------------------------------------");
  Serial.println("Quyida har 0.5 soniyada jonli qiymatlar ko'rsatiladi:");
  Serial.println("Ko'krakni bosing, Ambu qopini puflang, tugmani bosing!\n");
  delay(1500);
}

void loop() {
  // 1. KO'KRAK KUCH DATCHIGI (LOAD CELL)
  String forceStatus = "";
  float forceVal = 0.0;
  long forceRaw = 0;
  if (forceSensor.is_ready()) {
    forceRaw = forceSensor.read();
    forceVal = forceSensor.get_units(1);
    forceStatus = "✅ [RAW: " + String(forceRaw) + " | KUCH: " + String(forceVal, 1) + " kg]";
  } else {
    forceStatus = "❌ [ALOQA YO'Q]";
  }

  // 2. O'PKA DATCHIGI
  String lungStatus = "";
  float lungVal = 0.0;
  long lungRaw = 0;
  if (lungSensor.is_ready()) {
    lungRaw = lungSensor.read();
    lungVal = lungSensor.get_units(1);
    lungStatus = "✅ [RAW: " + String(lungRaw) + " | BOSIM: " + String(lungVal, 1) + " cmH2O]";
  } else {
    lungStatus = "❌ [ALOQA YO'Q]";
  }

  // 3. OSHQOZON DATCHIGI
  String stomachStatus = "";
  float stomachVal = 0.0;
  long stomachRaw = 0;
  if (stomachSensor.is_ready()) {
    stomachRaw = stomachSensor.read();
    stomachVal = stomachSensor.get_units(1);
    stomachStatus = "✅ [RAW: " + String(stomachRaw) + " | BOSIM: " + String(stomachVal, 1) + "]";
  } else {
    stomachStatus = "❌ [ALOQA YO'Q]";
  }

  // 4. QO'L JOYI TUGMASI (PIN 13)
  int btnState = digitalRead(POSITION_BTN_PIN);
  String btnStatus = (btnState == LOW) ? "🟢 BOSILDI (TO'G'RI JOY)" : "⚪ BO'SH";

  // 5. UKOL DATCHIGI (PIN 4)
  int touchDigital = digitalRead(TOUCH_PIN);
  int touchRaw = touchRead(TOUCH_PIN); // ESP32 ichki touch qiymati
  String touchStatus = (touchDigital == HIGH) ? "💉 UKOL TEGDI (HIGH)" : "⚪ BO'SH (TouchRaw: " + String(touchRaw) + ")";

  // Ekranga chiqarish
  Serial.println("==================== [JONLI NATIJALAR] ====================");
  Serial.print(" 🏋️ Ko'krak kuchi (HX711 27/14): "); Serial.println(forceStatus);
  Serial.print(" 🫁 O'pka bosimi  (HX711 32/33): "); Serial.println(lungStatus);
  Serial.print(" 🍔 Oshqozon      (HX711 25/26): "); Serial.println(stomachStatus);
  Serial.print(" 🔘 Qo'l joyi     (Pin 13)      : "); Serial.println(btnStatus);
  Serial.print(" 💉 Ukol datchigi (Pin 4)       : "); Serial.println(touchStatus);
  Serial.println();

  delay(500); // Har yarim soniyada yangilash
}
