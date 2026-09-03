/**
 * ======================================================================================
 * APPARAT TEKSHIRUV SKETCHI: D7 (SOLINOID KLAPAN) VA D8 (PULS RELESI) DIAGNOSTIKASI
 * 
 * Ushbu skript yordamida rele va solinoid klapanning elektr zanjirini tekshirish mumkin.
 * Arduino IDE "Serial Monitor"ni oching (115200 bod):
 * 
 * Buyruqlar:
 *   '1' -> D7 solinoid klapanini Yoqish / O'chirish (Har bosganda teskarisiga o'zgaradi)
 *   '2' -> D8 puls relesini Yoqish / O'chirish
 *   'p' -> D8 tomir pulsini 75 BPM ritmida sinash
 *   '0' -> Barchasini to'xtatish (D8 o'chadi, D7 ochiladi - bosim chiqariladi)
 * ======================================================================================
 */

#define PIN_PULSE_VALVE   8   // D8: Puls klapani
#define PIN_RELIEF_VALVE  7   // D7: Solinoid ortiqcha bosim klapani
#define PIN_LED          13   // Bortdagi LED

// Rele moduli Active-LOW (Ko'pchilik modullarda LOW = Yoqilgan, HIGH = O'chirilgan)
#define RELAY_ACTIVE_LOW  true

#if RELAY_ACTIVE_LOW
  #define RELAY_ON   LOW
  #define RELAY_OFF  HIGH
#else
  #define RELAY_ON   HIGH
  #define RELAY_OFF  LOW
#endif

bool d7State = false;
bool d8State = false;
bool pulseTesting = false;
unsigned long lastBeat = 0;
bool pulseActive = false;

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println(F("\n========================================================"));
  Serial.println(F("⚡ ARDUINO RELE VA SOLINOID DIAGNOSTIKA DASTURI ⚡"));
  Serial.println(F("D7: Solinoid bosim chiqarish klapani"));
  Serial.println(F("D8: Bo'yin/bilak tomir puls relesi"));
  Serial.println(F("--------------------------------------------------------"));
  Serial.println(F("Buyruqlar:"));
  Serial.println(F("  '1' -> D7 klapanni yoqish/o'chirish"));
  Serial.println(F("  '2' -> D8 puls relesini yoqish/o'chirish"));
  Serial.println(F("  'p' -> D8 orqali 75 BPM tomir urishini boshlash"));
  Serial.println(F("  '0' -> Hammasini o'chirish / 0 ga tushirish"));
  Serial.println(F("========================================================"));

  pinMode(PIN_PULSE_VALVE, OUTPUT);
  pinMode(PIN_RELIEF_VALVE, OUTPUT);
  pinMode(PIN_LED, OUTPUT);

  // Xavfsiz holat
  digitalWrite(PIN_PULSE_VALVE, RELAY_OFF);
  digitalWrite(PIN_RELIEF_VALVE, RELAY_OFF);
  digitalWrite(PIN_LED, LOW);
}

void loop() {
  if (Serial.available() > 0) {
    char c = Serial.read();
    
    if (c == '1') {
      pulseTesting = false;
      d7State = !d7State;
      digitalWrite(PIN_RELIEF_VALVE, d7State ? RELAY_ON : RELAY_OFF);
      Serial.print(F(">>> [D7 SOLINOID]: "));
      Serial.println(d7State ? F("YOQILDI (Klapan Ochiq / Tok bor)") : F("O'CHIRILDI (Klapan Yopiq)"));
    }
    else if (c == '2') {
      pulseTesting = false;
      d8State = !d8State;
      digitalWrite(PIN_PULSE_VALVE, d8State ? RELAY_ON : RELAY_OFF);
      digitalWrite(PIN_LED, d8State ? HIGH : LOW);
      Serial.print(F(">>> [D8 PULS RELESI]: "));
      Serial.println(d8State ? F("YOQILDI (Rele yopiq / Tok bor)") : F("O'CHIRILDI (Rele ochiq)"));
    }
    else if (c == 'p' || c == 'P') {
      pulseTesting = true;
      digitalWrite(PIN_RELIEF_VALVE, RELAY_OFF); // Bosim to'planishi uchun D7 yopiladi
      Serial.println(F(">>> [75 BPM PULS TESTI BOSHLANDI]: D8 klapan har 800ms da uradi!"));
    }
    else if (c == '0') {
      pulseTesting = false;
      d7State = true;  // Bosimni chiqarish uchun D7 ochiladi
      d8State = false; // D8 puls to'xtaydi
      digitalWrite(PIN_PULSE_VALVE, RELAY_OFF);
      digitalWrite(PIN_RELIEF_VALVE, RELAY_ON);
      digitalWrite(PIN_LED, LOW);
      Serial.println(F(">>> [NOL QILINDI]: D8 to'xtadi, D7 bosimni chiqarish uchun ochildi!"));
    }
  }

  if (pulseTesting) {
    unsigned long now = millis();
    if (!pulseActive && (now - lastBeat >= 800)) {
      pulseActive = true;
      lastBeat = now;
      digitalWrite(PIN_PULSE_VALVE, RELAY_ON);
      digitalWrite(PIN_LED, HIGH);
    }
    if (pulseActive && (now - lastBeat >= 120)) {
      pulseActive = false;
      digitalWrite(PIN_PULSE_VALVE, RELAY_OFF);
      digitalWrite(PIN_LED, LOW);
    }
  }
}
