#include <Arduino.h>
#include <HX711.h>
#include <ArduinoJson.h>

// --- PINLAR ---
const int LOADCELL_DOUT     = 14;
const int LOADCELL_SCK      = 27;
const int POSITION_BTN_PIN  = 13;
const int LUNG_DOUT         = 32;
const int LUNG_SCK          = 33;
const int STOMACH_DOUT      = 25;
const int STOMACH_SCK       = 26;
const int INJECTION_BTN_PIN = 4;

HX711 forceSensor;
HX711 lungSensor;
HX711 stomachSensor;

// Kalibratsiya koeffitsientlari
float forceCalib   = 23000.0;
float lungCalib    = 4200.0;
float stomachCalib = 4200.0;

// O'zgaruvchilar
float curForce   = 0.0;
float curLung    = 0.0;
float curStomach = 0.0;

unsigned long lastSendTime = 0;
const unsigned long sendInterval = 50; // Har 50 ms da (20 Hz) uzatish

void setup() {
  Serial.begin(115200);

  // Tugmalar (INPUT_PULLUP)
  pinMode(POSITION_BTN_PIN, INPUT_PULLUP);
  pinMode(INJECTION_BTN_PIN, INPUT_PULLUP);

  // Datchiklarni ishga tushirish
  forceSensor.begin(LOADCELL_DOUT, LOADCELL_SCK);
  lungSensor.begin(LUNG_DOUT, LUNG_SCK);
  stomachSensor.begin(STOMACH_DOUT, STOMACH_SCK);

  // Tezkor Tare
  if (forceSensor.wait_ready_timeout(500)) {
    forceSensor.set_scale(forceCalib);
    forceSensor.tare(1);
  }
  if (lungSensor.wait_ready_timeout(500)) {
    lungSensor.set_scale(lungCalib);
    lungSensor.tare(1);
  }
  if (stomachSensor.wait_ready_timeout(500)) {
    stomachSensor.set_scale(stomachCalib);
    stomachSensor.tare(1);
  }
}

void loop() {
  // 1. Datchiklardan qiymatlarni o'qish
  if (forceSensor.is_ready()) {
    float r = forceSensor.get_units(1);
    curForce = (r < 0.5) ? 0.0 : r;
  }
  if (lungSensor.is_ready()) {
    float r = lungSensor.get_units(1);
    curLung = (r < 0.5) ? 0.0 : r;
  }
  if (stomachSensor.is_ready()) {
    float r = stomachSensor.get_units(1);
    curStomach = (r < 0.5) ? 0.0 : r;
  }

  // 2. Tugmalar holati (1 = bosilgan, 0 = ochiq)
  int posBtn = (digitalRead(POSITION_BTN_PIN) == LOW) ? 1 : 0;
  int injBtn = (digitalRead(INJECTION_BTN_PIN) == LOW) ? 1 : 0;

  // 3. JSON paketini uzatish (har 50 ms da bitta qator)
  unsigned long now = millis();
  if (now - lastSendTime >= sendInterval) {
    lastSendTime = now;

    StaticJsonDocument<150> doc;
    doc["force"]     = round(curForce * 10.0) / 10.0;    // Massaj kuchi (kg)
    doc["lung_p"]    = round(curLung * 10.0) / 10.0;     // O'pka bosimi
    doc["stomach_p"] = round(curStomach * 10.0) / 10.0;  // Oshqozon bosimi
    doc["pos_btn"]   = posBtn;                           // To'g'ri nuqta tugmasi (1 yoki 0)
    doc["inj_btn"]   = injBtn;                           // Ukol/Tomir tugmasi (1 yoki 0)

    serializeJson(doc, Serial);
    Serial.println();
  }
}
