#include <Arduino.h>
#include <HX711.h>
#include <ArduinoJson.h>

// ============================================================================
// 1. APPARAT QISMI (HARDWARE PINOUT)
// ============================================================================

// Ko'krak massaji kuchi (Load Cell 50kg/100kg datchigi va HX711 kuchaytirgichi)
const int LOADCELL_DOUT     = 14; // HX711 Data chiqishi
const int LOADCELL_SCK      = 27; // HX711 Soat (Clock) impulsi

// Massaj to'g'ri nuqtasini tekshirish tugmasi (Ko'krak markazidagi mikrotugma)
const int POSITION_BTN_PIN  = 13; // Bosilganda GND ga ulanadi (INPUT_PULLUP)

// O'pka havo bosimi datchigi (MPS20N0040D datchigi + HX710B / HX711 moduli)
const int LUNG_DOUT         = 32; // O'pka bosim moduli Data chiqishi
const int LUNG_SCK          = 33; // O'pka bosim moduli Soat impulsi

// Oshqozonga qochgan havo bosimi datchigi (MPS20N0040D + HX710B / HX711 moduli)
const int STOMACH_DOUT      = 25; // Oshqozon bosim moduli Data chiqishi
const int STOMACH_SCK       = 26; // Oshqozon bosim moduli Soat impulsi

// Injektsiya (Ukol tomirga kirdi) tugmasi
const int INJECTION_BTN_PIN = 4;  // Bosilganda GND ga ulanadi (INPUT_PULLUP)

// ============================================================================
// 2. DATCHIK OBYEKTLARI VA KALIBRATSIYA KOEFFITSIENTLARI
// ============================================================================

HX711 forceSensor;   // Kuch datchigi obyekti
HX711 lungSensor;    // O'pka bosimi datchigi obyekti
HX711 stomachSensor; // Oshqozon bosimi datchigi obyekti

// Ushbu koeffitsientlar xom (raw) ADC qiymatini aniq fizik birliklarga o'giradi:
// - forceCalib: Chiqishni Kilogramm (kg) ga aylantirish uchun
// - lungCalib / stomachCalib: Chiqishni Kilopaskal (kPa) yoki havo birligiga aylantirish uchun
float forceCalib   = 23000.0; // Natija: Kilogramm (kg)
float lungCalib    = 4200.0;  // Natija: Kilopaskal (kPa)
float stomachCalib = 4200.0;  // Natija: Kilopaskal (kPa)

// Hozirgi datchik o'lchovlarini saqlash o'zgaruvchilari
float curForce   = 0.0; // Massaj kuchi (kg)
float curLung    = 0.0; // O'pka bosimi (kPa)
float curStomach = 0.0; // Oshqozon bosimi (kPa)

// Paket uzatish vaqti nazorati
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 30; // Har 30 ms da uzatish (33 Hz chastota, 0ms kechikish)

// ============================================================================
// 3. SOZLASH (SETUP)
// ============================================================================

void setup() {
  // UART aloqasini 115200 bod tezlikda ochish
  Serial.begin(115200);

  // Tugmalarni ichki tortuvchi rezistor (INPUT_PULLUP) bilan sozlash
  // Tugma ochiq bo'lsa -> HIGH (1), bosilsa (GND ga tegsa) -> LOW (0) bo'ladi
  pinMode(POSITION_BTN_PIN, INPUT_PULLUP);
  pinMode(INJECTION_BTN_PIN, INPUT_PULLUP);

  // Datchiklarning DOUT va SCK oyoqlarini belgilash
  forceSensor.begin(LOADCELL_DOUT, LOADCELL_SCK);
  lungSensor.begin(LUNG_DOUT, LUNG_SCK);
  stomachSensor.begin(STOMACH_DOUT, STOMACH_SCK);

  // Tezkor Tare (Dastlabki yuklama va atmosfera bosimini 1 ta o'lchov bilan nolga tushirish)
  if (forceSensor.wait_ready_timeout(500)) {
    forceSensor.set_scale(forceCalib);
    forceSensor.tare(1); // 0.0 kg ga sozlash
  }
  if (lungSensor.wait_ready_timeout(500)) {
    lungSensor.set_scale(lungCalib);
    lungSensor.tare(1); // 0.0 kPa ga sozlash
  }
  if (stomachSensor.wait_ready_timeout(500)) {
    stomachSensor.set_scale(stomachCalib);
    stomachSensor.tare(1); // 0.0 kPa ga sozlash
  }
}

// ============================================================================
// 4. ASOSIY DASTUR TSIKLI (LOOP)
// ============================================================================

void loop() {
  // --- 1-QADAM: DATCHIKLARDAN FIZIK KO'RSATKICHLARNI O'QISH ---

  // Kuch datchigi (Load Cell)
  if (forceSensor.is_ready()) {
    float r = forceSensor.get_units(1);
    // 0.5 kg dan kichik tebranishlar shovqin hisoblanib nolga tenglashtiriladi
    curForce = (r < 0.5) ? 0.0 : r;
  }

  // O'pka bosimi (MPS20N0040D)
  if (lungSensor.is_ready()) {
    float r = lungSensor.get_units(1);
    // 0.2 kPa dan kichik shovqinlar filtrlanadi
    curLung = (r < 0.2) ? 0.0 : r;
  }

  // Oshqozon bosimi (MPS20N0040D)
  if (stomachSensor.is_ready()) {
    float r = stomachSensor.get_units(1);
    curStomach = (r < 0.2) ? 0.0 : r;
  }

  // --- 2-QADAM: RAQAMLI TUGMALAR HOLATINI ANIQLASH ---
  // Bosilgan bo'lsa (LOW) -> 1, ochiq bo'lsa (HIGH) -> 0 qiymat oladi
  int posBtn = (digitalRead(POSITION_BTN_PIN) == LOW) ? 1 : 0; // Nuqta tugmasi
  int injBtn = (digitalRead(INJECTION_BTN_PIN) == LOW) ? 1 : 0; // Ukol tugmasi

  // --- 3-QADAM: JSON PAKETINI SHAKLLANTIRISH VA UART GA UZATISH ---
  unsigned long now = millis();
  if (now - lastSendTime >= sendInterval) {
    lastSendTime = now;

    // JSON obyektini yaratish
    StaticJsonDocument<160> doc;

    // Qiymatlarni 1 xona aniqlikda yaxlitlab JSON ga joylash
    doc["force"]     = round(curForce * 10.0) / 10.0;   // Ko'krak massaji kuchi [O'lchov birligi: kg]
    doc["lung_p"]    = round(curLung * 10.0) / 10.0;    // O'pkaga kirgan havo bosimi [O'lchov birligi: kPa]
    doc["stomach_p"] = round(curStomach * 10.0) / 10.0; // Oshqozonga qochgan havo bosimi [O'lchov birligi: kPa]
    doc["pos_btn"]   = posBtn;                          // To'g'ri nuqta: 1 = qo'l to'g'ri joyda, 0 = noaniq
    doc["inj_btn"]   = injBtn;                          // Inyeksiya: 1 = tomirga igna kirdi, 0 = kiritilmadi

    // JSON ni bitta satr qilib Serial orqali uzatish
    serializeJson(doc, Serial);
    Serial.println();
  }
}
