/**
 * ======================================================================================
 * MEDLIFE GD/H126 - VIBRATOR MOTORLI PULS SIMULYATORI VA VITAL MONITOR INTEGRATSIYASI
 * 
 * Pinlar:
 *   Motor (BC547 baza)   -> D4 (PWM)
 *   Touch sensor (TTP223) -> D5
 * 
 * Eslatma: Ushbu dastur kompyuterga ortiqcha matn (Serial.print) yubormaydi.
 * Shunda Vital Monitor dori deb adashtirmaydi!
 * Faqat kompyuterdan buyruqlarni qabul qiladi (NORMAL, TACH, BRAD, ASYSTOLE, VFIB, ROSC, SHOCK, BPM:xx)
 * ======================================================================================
 */

const int motorPin = 4;   // BC547 tranzistor bazasiga ulangan pin (PWM)
const int touchPin = 5;   // TTP223 Touch sensor ulangan pin

// Motorning tebranish kuchi (0 dan 255 gacha). 120-150 = yumshoq yurak zarbasi
const int motorSpeed = 140; 

int currentMode = 0; 
int customBPM = 75;

bool lastTouchState = false;
bool isWebControlled = false;
String serialBuffer = "";

void setup() {
  Serial.begin(115200);
  
  pinMode(motorPin, OUTPUT);
  pinMode(touchPin, INPUT);
  
  // Dastlabki holatda motorni o'chirish
  analogWrite(motorPin, 0);
}

void loop() {
  // 1. Vital Monitordan buyruqlarni tekshirish (115200 bod)
  tekshirSerialBuyruqlar();

  // 2. Touch sensor holati (Barmoq tekkizilganmi?)
  bool touchState = digitalRead(touchPin);

  if (touchState == HIGH) {
    // Agar kompyuter ulanmagan bo'lsa (avtonom), sensor orqali rejim almashadi
    if (!isWebControlled && lastTouchState == LOW) {
      currentMode++;
      if (currentMode > 3) currentMode = 0;
      delay(50);
    }
    
    // Yurak urishini ijro etish
    ijroEtYurakUrishi();
  } else {
    // Barmoq olinganda motor mutlaqo o'chadi
    analogWrite(motorPin, 0);
  }

  lastTouchState = touchState;
}

void ijroEtYurakUrishi() {
  switch (currentMode) {
    case 0:
      // NORMAL RITM (75 BPM) -> Tuk... tuk...
      yurakUrishi(60, 180, 650);
      break;

    case 1:
      // TAXIKARDIYA (140-180 BPM) -> Tezkor
      yurakUrishi(45, 120, 250);
      break;

    case 2:
      // BRADIKARDIYA (30 BPM) -> Sekin, og'ir zarba
      yurakUrishi(80, 280, 1600);
      break;

    case 3:
      // ARITMIYA -> Tartibsiz oraliq
      {
        int tasodifiyTanaffus = random(400, 1400);
        yurakUrishi(60, 180, tasodifiyTanaffus);
      }
      break;

    case 4:
      // ASISTOLIYA (0 BPM) -> Yurak to'xtagan, puls yo'q!
      analogWrite(motorPin, 0);
      delay(20);
      break;

    case 5:
      // VFIB (Qorinchalar fibrillyatsiyasi) -> Tezkor xaotik titrash
      analogWrite(motorPin, 120);
      pauzaBilanKutish(40);
      analogWrite(motorPin, 0);
      pauzaBilanKutish(45);
      break;

    case 6:
      // ANIQ CUSTOM BPM (Vital Monitordan)
      if (customBPM <= 0) {
        analogWrite(motorPin, 0);
        delay(20);
      } else {
        int totalMs = 60000 / customBPM;
        int zarba = (customBPM >= 120) ? 45 : (customBPM <= 45 ? 80 : 55);
        int oraliq = (customBPM >= 120) ? 120 : (customBPM <= 45 ? 260 : 170);
        int tanaffus = totalMs - (2 * zarba + oraliq);
        if (tanaffus < 50) tanaffus = 50;
        yurakUrishi(zarba, oraliq, tanaffus);
      }
      break;
  }
}

// "Lub-Dub" (Tuk-Tuk) zarba mexanizmi
void yurakUrishi(int zarbaVaqti, int oraliqPauza, int tanaffus) {
  // "Lub" - 1-zarba
  analogWrite(motorPin, motorSpeed);
  if (!pauzaBilanKutish(zarbaVaqti)) return;

  // Oraliq pauza
  analogWrite(motorPin, 0);
  if (!pauzaBilanKutish(oraliqPauza)) return;

  // "Dub" - 2-zarba
  analogWrite(motorPin, motorSpeed);
  if (!pauzaBilanKutish(zarbaVaqti)) return;

  // Tanaffus
  analogWrite(motorPin, 0);
  if (!pauzaBilanKutish(tanaffus)) return;
}

// Kechikishlarsiz (non-blocking) kutish funksiyasi
bool pauzaBilanKutish(int kutishMs) {
  unsigned long start = millis();
  while (millis() - start < (unsigned long)kutishMs) {
    // Agar barmoq olinsa, motor darhol to'xtaydi
    if (digitalRead(touchPin) == LOW) {
      analogWrite(motorPin, 0);
      return false;
    }
    // Serial buyruqlarini tekshirish
    tekshirSerialBuyruqlar();
    delayMicroseconds(500);
  }
  return true;
}

// Serial buyruqlarini o'qish (115200 bod)
void tekshirSerialBuyruqlar() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (serialBuffer.length() > 0) {
        bajarSerialBuyruq(serialBuffer);
        serialBuffer = "";
      }
    } else {
      serialBuffer += c;
    }
  }
}

void bajarSerialBuyruq(String cmd) {
  cmd.trim();
  cmd.toUpperCase();
  isWebControlled = true;

  if (cmd.startsWith("BPM:")) {
    int bpm = cmd.substring(4).toInt();
    customBPM = bpm;
    if (bpm <= 0) {
      currentMode = 4; // Asistoliya
    } else {
      currentMode = 6; // Custom BPM
    }
  }
  else if (cmd.indexOf("NORMAL") >= 0 || cmd == "1") {
    currentMode = 0;
  }
  else if (cmd.indexOf("TACH") >= 0 || cmd == "2") {
    currentMode = 1;
  }
  else if (cmd.indexOf("BRAD") >= 0 || cmd == "3") {
    currentMode = 2;
  }
  else if (cmd.indexOf("ARIT") >= 0 || cmd.indexOf("ARRHYTHMIA") >= 0) {
    currentMode = 3;
  }
  else if (cmd.indexOf("ASYSTOLE") >= 0 || cmd.indexOf("DYING") >= 0 || cmd.indexOf("STOP") >= 0) {
    currentMode = 4;
    analogWrite(motorPin, 0);
  }
  else if (cmd.indexOf("VFIB") >= 0) {
    currentMode = 5;
  }
  else if (cmd.indexOf("SHOCK") >= 0) {
    analogWrite(motorPin, 255); // Kuchli bitta zarba
    delay(280);
    analogWrite(motorPin, 0);
    delay(100);
    currentMode = 0;
  }
  else if (cmd.indexOf("ROSC") >= 0) {
    currentMode = 0;
  }
  else if (cmd.indexOf("STANDALONE") >= 0 || cmd.indexOf("AUTO") >= 0) {
    isWebControlled = false;
  }
}
