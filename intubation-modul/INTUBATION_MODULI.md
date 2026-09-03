# Intubatsiya maniken moduli — to'liq texnik spetsifikatsiya

> Bu fayl modulni boshqa loyihada noldan qayta qurish uchun yetarli bo'lgan hamma narsani o'z ichiga oladi:
> umumiy tushuncha, apparat ulanishi, ma'lumot formatlari, tashhis qoidalari, UI/animatsiya, ovoz va to'liq kod.
> Yonidagi `assets/` papkasida modul ishlatadigan media fayllar bor.

## 1. Modul nima qiladi

Intubatsiya (traxeya trubkasini qo'yish) ko'nikmasini o'rgatuvchi maniken ichida **3 ta sensor** bor:

| Sensor | Joyi | Ma'nosi |
|---|---|---|
| `teeth` | Tish/lab | Laringoskop yoki trubka tishga tayandi — jarohat xavfi (ogohlantirish) |
| `esophagus` | Qizilo'ngach (oshqazon yo'li) | Trubka **noto'g'ri** yo'lga kirdi — xato |
| `trachea` | Traxeya (o'pka yo'li) | Trubka **to'g'ri** joylashdi |

Sensorlar Arduino'ga ulanadi, Arduino esa USB serial port orqali matn qatorlari yuboradi.
Brauzer **Web Serial API** bilan bu portni to'g'ridan-to'g'ri o'qiydi (server kerak emas) va:

1. qatorni tahlil qiladi (`parseSerialLine` / `parseTextLine`),
2. har bir sensor uchun faol/jim holatni hisoblaydi (`isActive`),
3. holatlar kombinatsiyasidan **tashhis** chiqaradi (`diagnose`),
4. anatomiya rasmida mos nuqtani yondiradi (pulsatsiya + porlash),
5. tashhisga qarab ovoz chalinadi (xato — takroriy signal, to'g'ri — fanfara),
6. trubka **2 soniya** to'g'ri holatda turgach konfetti bilan nishonlaydi,
7. barcha o'zgarishlarni hodisalar jurnaliga yozadi.

## 2. Apparat va ulanish

```
Maniken sensorlari ──> Arduino (D2/D3/D4 yoki A0/A1/A2) ──USB──> Kompyuter
                                                                    │
                                                      Chrome/Edge (Web Serial API)
                                                                    │
                                                       React sahifa: /intubation
```

**Talablar**
- Desktop **Chrome yoki Edge** (Firefox/Safari Web Serial'ni qo'llamaydi). Sahifa `https://` yoki `localhost` bo'lishi shart.
- Port faqat **foydalanuvchi bosgan tugma** ichida so'raladi: `navigator.serial.requestPort()`.
- Baud rate UI'dan tanlanadi: 9600 / 19200 / 38400 / 57600 / 115200 (Arduino'dagi `Serial.begin()` bilan bir xil bo'lishi kerak).
- Arduino IDE'ning Serial Monitor'i **yopiq** bo'lishi kerak — aks holda port band bo'ladi.

**Arduino tomonidan yuboriladigan formatlar (istalgan biri):**

| Format | Misol |
|---|---|
| kalit:qiymat | `T:1 E:0 L:0` yoki `tish=1;oshqazon=0;opka=1` |
| JSON | `{"teeth":1,"eso":0,"lung":0}` |
| CSV (3 son, tartib: tish, oshqazon, o'pka) | `512,0,800` |
| matnli xabar | `button-tishga tegdi`, `Oshqazonga tegdi`, `Tomoqqa tegdi` |

Qiymat `0/1` bo'lsa raqamli signal sifatida, `1` dan katta bo'lsa **analog** (0–1023) sifatida
UI'dagi "Analog chegara" (default **300**) bilan solishtiriladi.

**Muhim xatti-harakat:** ko'p Arduino eskizlari faqat "tegdi" xabarini yuboradi, "qo'yib yubordi" xabari yo'q.
Shu sababli hook har **250 ms**da tekshiradi va sensor bo'yicha **500 ms** ichida yangi xabar kelmasa uni avtomatik `0` (jim) qiladi.

**Minimal Arduino eskizi (raqamli tugmalar bilan):**

```cpp
const int PIN_TEETH = 2, PIN_ESO = 3, PIN_TRACHEA = 4;

void setup() {
  Serial.begin(9600);
  pinMode(PIN_TEETH, INPUT_PULLUP);
  pinMode(PIN_ESO, INPUT_PULLUP);
  pinMode(PIN_TRACHEA, INPUT_PULLUP);
}

void loop() {
  int t = digitalRead(PIN_TEETH)   == LOW ? 1 : 0;
  int e = digitalRead(PIN_ESO)     == LOW ? 1 : 0;
  int l = digitalRead(PIN_TRACHEA) == LOW ? 1 : 0;
  Serial.print("T:"); Serial.print(t);
  Serial.print(" E:"); Serial.print(e);
  Serial.print(" L:"); Serial.println(l);
  delay(100); // 10 Hz yetarli
}
```

Analog (FSR/fotorezistor) variantda: `Serial.println(String(analogRead(A0)) + "," + analogRead(A1) + "," + analogRead(A2));`

## 3. Tashhis qoidalari (ustuvorlik tartibida)

| Shart | Daraja | Xulosa |
|---|---|---|
| `esophagus` faol | `danger` | Trubka qizilo'ngachga kirdi — darhol chiqarib qayta urinish |
| `trachea` faol **va** `teeth` faol | `warn` | Traxeyaga kirdi, lekin tishga tegdi |
| `trachea` faol, `teeth` jim | `ok` | To'g'ri joylashuv |
| faqat `teeth` faol | `warn` | Tishga tayanish qayd etildi |
| hech biri | `idle` | Signal kutilmoqda |

Ranglar: `ok` — emerald, `warn` — amber, `danger` — destructive/qizil, `idle` — kulrang.

## 4. Vizual qism

- **Anatomiya rasmi** (`assets/tibbiy_sensor_anatomy.svg`) o'zgarmagan holda `<img>` sifatida ko'rsatiladi,
  ustiga HTML/CSS overlay qilinadi. Nuqtalar foizli koordinatalarda joylashgan:
  - tish — `x: 33.9%`, `y: 29.2%`, rang `#ff3b4e`
  - o'pka yo'li (traxeya) — `x: 38.6%`, `y: 53.4%`, rang `#2fa8ff`
  - oshqozon yo'li — `x: 43.3%`, `y: 86.0%`, rang `#ffb020`
  - konteyner `aspect-ratio: 1536 / 1024`.
- Faol sensor: `mk-ping` keyframe bilan pulsatsiya + `blur` porlash + oq to'ldirilgan nuqta.
- O'ng yuqori burchakda 3 sensorning `FAOL / jim` legendasi.
- **Konfetti**: 140 bo'lak, 6–7 s davomiylik, markazda yashil "salyut" porlashi. Faqat tashhis `ok` bo'lib
  **2 soniya** turgandan keyin ishga tushadi va **7 soniya**dan keyin o'chib, ovozni ham to'xtatadi.
- Sahifada namuna video ham bor (`assets/intubation_sample.mp4`) — imtihondan oldin to'g'ri texnikani ko'rish uchun.

## 5. Ovoz

| Holat | Fayl | Rejim |
|---|---|---|
| `danger` (qizilo'ngach) | `assets/esophagus.mp3` | `loop` — xato tuzatilmaguncha |
| `warn` | `assets/failed.mp3` | `loop` |
| `ok` | `assets/success.mp3` | bir marta (fanfara) |

`Audio` elementlari URL bo'yicha keshlanadi, `stopAllSounds()` hamma narsani to'xtatadi.
UI'da "Ovoz yoniq / o'chiq" tugmasi bor (brauzer autoplay siyosati uchun birinchi ovoz foydalanuvchi bosishidan keyin chalinadi).

## 6. Fayl tuzilishi (qayta qurish uchun)

```
src/lib/manikin-serial.ts        # parser, isActive, diagnose, useManikinSerial hook
src/lib/manikin-sound.ts         # ovoz boshqaruvi + useDiagnosisSound
src/components/ManikinAnatomy.tsx# anatomiya + jonli overlay
src/components/Confetti.tsx      # muvaffaqiyat animatsiyasi
src/routes/.../intubation.tsx    # sahifa UI (route)
assets/                          # svg, 3 mp3, namuna mp4
```

Tashqi bog'liqliklar: React 19, Tailwind (yoki oddiy CSS), `lucide-react` ikonkalari,
shadcn/ui `Card / Button / Badge / Input / Label / Select`. Backend, DB yoki API **kerak emas** —
modul to'liq brauzer ichida ishlaydi. Kodda `@/assets/*.asset.json` importlari bor —
yangi loyihada ularni oddiy fayl importlari bilan almashtiring (masalan `import anatomy from "./assets/tibbiy_sensor_anatomy.svg"`).

## 7. Sinov (apparat bo'lmasa)

UI'dagi **Demo** tugmasi 1.6 s oraliqda ssenariy o'ynatadi: bo'sh → tish → qizilo'ngach → bo'sh → traxeya → traxeya,
ya'ni barcha 4 tashhis holatini, ovozni va konfettini apparatsiz tekshirib ko'rish mumkin.

## 8. To'liq kod

### `src/lib/manikin-serial.ts`

Serial parser + `useManikinSerial` hook + tashhis mantiqi

```ts
import { useCallback, useEffect, useRef, useState } from "react";

export type SensorKey = "teeth" | "esophagus" | "trachea";

export type SensorReading = {
  teeth: number;
  esophagus: number;
  trachea: number;
};

export type ManikinEvent = {
  id: string;
  at: number;
  sensor: SensorKey;
  kind: "start" | "end";
  raw?: string;
};

export const SENSOR_LABEL: Record<SensorKey, string> = {
  teeth: "Tish sensori",
  esophagus: "Qizilo'ngach (oshqazon yo'li)",
  trachea: "Traxeya (o'pka yo'li)",
};

const ALIASES: Record<string, SensorKey> = {
  t: "teeth",
  teeth: "teeth",
  tish: "teeth",
  tooth: "teeth",
  e: "esophagus",
  eso: "esophagus",
  esophagus: "esophagus",
  oshqazon: "esophagus",
  qizilongach: "esophagus",
  stomach: "esophagus",
  l: "trachea",
  lung: "trachea",
  opka: "trachea",
  trachea: "trachea",
  tracheal: "trachea",
  airway: "trachea",
};

/**
 * Matnli xabarlardan sensorni aniqlaydi, masalan:
 *  - "button-tishga tegdi"      -> teeth
 *  - "Oshqazonga tegdi"         -> esophagus
 *  - "Tomoqqa tegdi"            -> trachea
 */
export function parseTextLine(line: string): SensorKey | null {
  const t = line.toLowerCase();
  if (t.includes("tizim")) return null;
  if (t.includes("tish") || t.includes("button")) return "teeth";
  if (t.includes("oshqazon") || t.includes("qizil")) return "esophagus";
  if (t.includes("tomoq") || t.includes("traxe") || t.includes("o'pka") || t.includes("opka"))
    return "trachea";
  return null;
}

/**
 * Arduino serial monitordan kelgan qatorni tahlil qiladi.
 * Qabul qiladigan formatlar:
 *  - JSON:            {"teeth":1,"eso":0,"lung":1}
 *  - kalit:qiymat:    T:512, E:0, L:800   yoki   tish=1;oshqazon=0;opka=1
 *  - 3 ta son (CSV):  512,0,800   (tartib: tish, oshqazon, o'pka)
 *  - matnli xabar:    "button-tishga tegdi", "Tomoqqa tegdi"
 */
export function parseSerialLine(line: string): Partial<SensorReading> | null {

  const text = line.trim();
  if (!text) return null;

  if (text.startsWith("{")) {
    try {
      const obj = JSON.parse(text) as Record<string, unknown>;
      const out: Partial<SensorReading> = {};
      for (const [k, v] of Object.entries(obj)) {
        const key = ALIASES[k.toLowerCase().replace(/[^a-z]/g, "")];
        if (!key) continue;
        out[key] = typeof v === "boolean" ? (v ? 1 : 0) : Number(v) || 0;
      }
      return Object.keys(out).length ? out : null;
    } catch {
      return null;
    }
  }

  const pairs = [...text.matchAll(/([a-zA-Z_\u0400-\u04FF']+)\s*[:=]\s*(-?\d+(?:\.\d+)?)/g)];
  if (pairs.length) {
    const out: Partial<SensorReading> = {};
    for (const m of pairs) {
      const key = ALIASES[(m[1] ?? "").toLowerCase().replace(/[^a-z]/g, "")];
      if (!key) continue;
      out[key] = Number(m[2]);
    }
    return Object.keys(out).length ? out : null;
  }

  const nums = text.split(/[,;\s]+/).map(Number);
  if (nums.length >= 3 && nums.slice(0, 3).every((n) => Number.isFinite(n))) {
    return { teeth: nums[0]!, esophagus: nums[1]!, trachea: nums[2]! };
  }
  return null;
}

export function isActive(value: number, threshold: number) {
  // 0/1 raqamli signal ham, analog (0-1023) signal ham qo'llab-quvvatlanadi
  if (value <= 1) return value >= 1;
  return value >= threshold;
}

export type Diagnosis = {
  level: "ok" | "warn" | "danger" | "idle";
  title: string;
  detail: string;
};

export function diagnose(active: Record<SensorKey, boolean>): Diagnosis {
  if (active.esophagus) {
    return {
      level: "danger",
      title: "Trubka qizilo'ngachga (oshqazon yo'liga) kirdi",
      detail:
        "Oshqazon yo'li sensori faollashdi. Bu noto'g'ri joylashuv — trubkani darhol chiqarib, boshni qayta joylab urinish kerak.",
    };
  }
  if (active.trachea) {
    return {
      level: active.teeth ? "warn" : "ok",
      title: active.teeth
        ? "Traxeyaga kirdi, lekin tishga tegdi"
        : "Trubka traxeyaga (o'pka yo'liga) to'g'ri kirdi",
      detail: active.teeth
        ? "O'pka yo'li sensori faol — joylashuv to'g'ri, ammo tish sensori ham ishga tushdi (tish/lab jarohati xavfi)."
        : "O'pka yo'li sensori faollashdi va oshqazon yo'li sensori jim — joylashuv to'g'ri deb qayd etildi.",
    };
  }
  if (active.teeth) {
    return {
      level: "warn",
      title: "Tishga tegish qayd etildi",
      detail: "Laringoskop yoki trubka tishga tayanmoqda. Tayanch nuqtasini o'zgartirish kerak.",
    };
  }
  return { level: "idle", title: "Signal kutilmoqda", detail: "Hozircha hech bir sensor faol emas." };
}

export type SerialStatus = "unsupported" | "disconnected" | "connecting" | "connected" | "demo";

export function useManikinSerial(threshold: number) {
  const [status, setStatus] = useState<SerialStatus>("disconnected");
  const [reading, setReading] = useState<SensorReading>({ teeth: 0, esophagus: 0, trachea: 0 });
  const [lines, setLines] = useState<string[]>([]);
  const [events, setEvents] = useState<ManikinEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  const portRef = useRef<any>(null);
  const readerRef = useRef<any>(null);
  const stopRef = useRef(false);
  const prevActive = useRef<Record<SensorKey, boolean>>({
    teeth: false,
    esophagus: false,
    trachea: false,
  });
  const demoTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastSeen = useRef<Record<SensorKey, number>>({ teeth: 0, esophagus: 0, trachea: 0 });

  useEffect(() => {
    if (typeof navigator !== "undefined" && !("serial" in navigator)) setStatus("unsupported");
  }, []);

  const pushReading = useCallback(
    (partial: Partial<SensorReading>, raw?: string) => {
      setReading((prev) => {
        const next = { ...prev, ...partial };
        const active: Record<SensorKey, boolean> = {
          teeth: isActive(next.teeth, threshold),
          esophagus: isActive(next.esophagus, threshold),
          trachea: isActive(next.trachea, threshold),
        };
        (Object.keys(active) as SensorKey[]).forEach((k) => {
          if (active[k] !== prevActive.current[k]) {
            const ev: ManikinEvent = {
              id: `${Date.now()}-${k}-${active[k] ? "s" : "e"}-${Math.random().toString(36).slice(2, 6)}`,
              at: Date.now(),
              sensor: k,
              kind: active[k] ? "start" : "end",
              ...(raw ? { raw } : {}),
            };
            setEvents((e) => [ev, ...e].slice(0, 200));
          }
        });
        prevActive.current = active;
        return next;
      });
    },
    [threshold],
  );

  const handleLine = useCallback(
    (line: string) => {
      setLines((l) => [line, ...l].slice(0, 80));
      const parsed = parseSerialLine(line);
      if (parsed) {
        (Object.keys(parsed) as SensorKey[]).forEach((k) => {
          lastSeen.current[k] = Date.now();
        });
        pushReading(parsed, line);
        return;
      }
      const sensor = parseTextLine(line);
      if (sensor) {
        lastSeen.current[sensor] = Date.now();
        pushReading({ [sensor]: 1 } as Partial<SensorReading>, line);
      }
    },
    [pushReading],
  );

  // Arduino faqat "tegdi" xabarini yuboradi ("qo'yib yubordi" yo'q),
  // shuning uchun xabar kelmasa sensor avtomatik o'chadi.
  useEffect(() => {
    const id = setInterval(() => {
      const now = Date.now();
      const off: Partial<SensorReading> = {};
      (["teeth", "esophagus", "trachea"] as SensorKey[]).forEach((k) => {
        const seen = lastSeen.current[k];
        if (seen && now - seen > 500) {
          off[k] = 0;
          lastSeen.current[k] = 0;
        }
      });
      if (Object.keys(off).length) pushReading(off);
    }, 250);
    return () => clearInterval(id);
  }, [pushReading]);


  const disconnect = useCallback(async () => {
    stopRef.current = true;
    if (demoTimer.current) {
      clearInterval(demoTimer.current);
      demoTimer.current = null;
    }
    try {
      await readerRef.current?.cancel();
    } catch {
      /* ignore */
    }
    try {
      readerRef.current?.releaseLock?.();
    } catch {
      /* ignore */
    }
    try {
      await portRef.current?.close();
    } catch {
      /* ignore */
    }
    readerRef.current = null;
    portRef.current = null;
    setStatus("disconnected");
    setReading({ teeth: 0, esophagus: 0, trachea: 0 });
    prevActive.current = { teeth: false, esophagus: false, trachea: false };
  }, []);

  const connect = useCallback(
    async (baudRate: number) => {
      setError(null);
      const nav = navigator as unknown as { serial?: any };
      if (!nav.serial) {
        setStatus("unsupported");
        setError("Bu brauzer Web Serial API'ni qo'llab-quvvatlamaydi. Chrome/Edge (desktop) ishlating.");
        return;
      }
      try {
        setStatus("connecting");
        const port = await nav.serial.requestPort();
        await port.open({ baudRate });
        portRef.current = port;
        stopRef.current = false;
        setStatus("connected");

        const decoder = new TextDecoderStream();
        port.readable.pipeTo(decoder.writable).catch(() => undefined);
        const reader = decoder.readable.getReader();
        readerRef.current = reader;

        let buffer = "";
        while (!stopRef.current) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += value ?? "";
          const parts = buffer.split(/\r?\n/);
          buffer = parts.pop() ?? "";
          for (const p of parts) if (p.trim()) handleLine(p);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Portga ulanib bo'lmadi");
        setStatus("disconnected");
      }
    },
    [handleLine],
  );

  const startDemo = useCallback(() => {
    if (demoTimer.current) return;
    setStatus("demo");
    const script: SensorReading[] = [
      { teeth: 0, esophagus: 0, trachea: 0 },
      { teeth: 1, esophagus: 0, trachea: 0 },
      { teeth: 0, esophagus: 1, trachea: 0 },
      { teeth: 0, esophagus: 0, trachea: 0 },
      { teeth: 0, esophagus: 0, trachea: 1 },
      { teeth: 0, esophagus: 0, trachea: 1 },
    ];
    let i = 0;
    demoTimer.current = setInterval(() => {
      const s = script[i % script.length]!;
      handleLine(`T:${s.teeth} E:${s.esophagus} L:${s.trachea}`);
      i += 1;
    }, 1600);
  }, [handleLine]);

  useEffect(() => () => void disconnect(), [disconnect]);

  const active: Record<SensorKey, boolean> = {
    teeth: isActive(reading.teeth, threshold),
    esophagus: isActive(reading.esophagus, threshold),
    trachea: isActive(reading.trachea, threshold),
  };

  return {
    status,
    reading,
    active,
    lines,
    events,
    error,
    connect,
    disconnect,
    startDemo,
    clearEvents: () => setEvents([]),
  };
}
```

### `src/lib/manikin-sound.ts`

Ovoz boshqaruvi (xato/ogohlantirish/muvaffaqiyat)

```ts
import { useEffect, useRef } from "react";
import type { Diagnosis } from "./manikin-serial";
import failedAsset from "@/assets/failed.mp3.asset.json";
import successAsset from "@/assets/success.mp3.asset.json";
import esophagusAsset from "@/assets/esophagus.mp3.asset.json";

const cache = new Map<string, HTMLAudioElement>();

function el(url: string, loop: boolean): HTMLAudioElement | null {
  if (typeof window === "undefined") return null;
  const key = `${url}|${loop}`;
  let a = cache.get(key);
  if (!a) {
    a = new Audio(url);
    a.loop = loop;
    a.volume = 1;
    a.preload = "auto";
    cache.set(key, a);
  }
  return a;
}

function play(url: string, loop = false) {
  const a = el(url, loop);
  if (!a) return;
  try {
    a.currentTime = 0;
  } catch {
    /* ignore */
  }
  void a.play().catch(() => undefined);
}

function stop(url: string, loop = false) {
  const a = el(url, loop);
  if (!a) return;
  a.pause();
  try {
    a.currentTime = 0;
  } catch {
    /* ignore */
  }
}

/** Xato: yuklangan xato ovozi (uzluksiz takrorlanadi) */
export function playErrorSound() {
  play(failedAsset.url, true);
}

/** Ogohlantirish: xato ovozi (takrorlanadi) */
export function playWarnSound() {
  play(failedAsset.url, true);
}

/** Muvaffaqiyat: g'alaba fanfarasi */
export function playSuccessSound() {
  stopAlarmLoop();
  play(successAsset.url);
}

/** Xato tuzatilmaguncha ogohlantirish signalini takrorlab turadi */
export function startAlarmLoop(kind: "danger" | "warn") {
  if (kind === "danger") {
    stop(failedAsset.url, true);
    play(esophagusAsset.url, true);
    return;
  }
  stop(esophagusAsset.url, true);
  play(failedAsset.url, true);
}

export function stopAlarmLoop() {
  stop(failedAsset.url, true);
  stop(esophagusAsset.url, true);
}

/** Barcha ovozlarni (jumladan muvaffaqiyat kuyi) to'xtatadi */
export function stopAllSounds() {
  stopAlarmLoop();
  stop(successAsset.url);
}

/** Tashhis darajasiga qarab ovozni boshqaradi (xato bartaraf bo'lguncha chalinadi) */
export function useDiagnosisSound(dx: Diagnosis, enabled: boolean) {
  const prev = useRef<Diagnosis["level"] | null>(null);
  useEffect(() => {
    const last = prev.current;
    prev.current = dx.level;
    if (!enabled) {
      stopAllSounds();
      return;
    }
    if (dx.level === "danger" || dx.level === "warn") {
      if (last !== dx.level) startAlarmLoop(dx.level);
      return;
    }
    stopAlarmLoop();
    if (dx.level === "ok" && last !== "ok") playSuccessSound();
  }, [dx.level, enabled]);

  useEffect(() => () => stopAllSounds(), []);
}
```

### `src/components/ManikinAnatomy.tsx`

Anatomiya rasmi ustidagi jonli sensor overlay

```tsx
import anatomyAsset from "@/assets/tibbiy_sensor_anatomy.svg.asset.json";
import type { SensorKey } from "@/lib/manikin-serial";

/**
 * Anatomiya rasmi o'zgarmagan holda (asl SVG asset) ko'rsatiladi,
 * ustiga faqat jonli sensor indikatorlari HTML/CSS overlay qilib qo'yiladi.
 */
type Point = {
  key: SensorKey;
  label: string;
  /** rasm ichidagi foizli koordinatalar */
  x: number;
  y: number;
  color: string;
};

const POINTS: Point[] = [
  { key: "teeth", label: "Tish sensori", x: 33.9, y: 29.2, color: "#ff3b4e" },
  { key: "trachea", label: "O'pka yo'li sensori", x: 38.6, y: 53.4, color: "#2fa8ff" },
  { key: "esophagus", label: "Oshqozon yo'li sensori", x: 43.3, y: 86.0, color: "#ffb020" },
];

export function ManikinAnatomy({ active }: { active: Record<SensorKey, boolean> }) {
  return (
    <div className="relative w-full overflow-hidden rounded-lg" style={{ aspectRatio: "1536 / 1024" }}>
      <img
        src={anatomyAsset.url}
        alt="Maniken anatomiyasi: tish, o'pka yo'li va oshqozon yo'li sensorlari"
        className="absolute inset-0 h-full w-full object-contain"
        draggable={false}
      />

      {POINTS.map((p) => {
        const on = active[p.key];
        return (
          <div
            key={p.key}
            className="absolute -translate-x-1/2 -translate-y-1/2"
            style={{ left: `${p.x}%`, top: `${p.y}%` }}
          >
            {on ? (
              <>
                <span
                  className="absolute left-1/2 top-1/2 size-6 -translate-x-1/2 -translate-y-1/2 rounded-full"
                  style={{ backgroundColor: p.color, opacity: 0.35, animation: "mk-ping 1.2s ease-out infinite" }}
                />
                <span
                  className="absolute left-1/2 top-1/2 size-10 -translate-x-1/2 -translate-y-1/2 rounded-full blur-md"
                  style={{ backgroundColor: p.color, opacity: 0.55 }}
                />
              </>
            ) : null}
            <span
              className="relative block size-4 rounded-full border-2"
              style={{
                borderColor: p.color,
                backgroundColor: on ? "#ffffff" : "transparent",
                opacity: on ? 1 : 0.55,
                boxShadow: on ? `0 0 12px ${p.color}` : "none",
              }}
            />
          </div>
        );
      })}

      {/* holat yozuvlari */}
      <div className="absolute right-2 top-2 flex flex-col gap-1.5 rounded-md bg-black/35 p-2 backdrop-blur-sm sm:right-4 sm:top-4">
        {POINTS.map((p) => {
          const on = active[p.key];
          return (
            <div key={p.key} className="flex items-center gap-2 text-[11px] font-semibold sm:text-xs">
              <span
                className="size-2.5 rounded-full"
                style={{
                  backgroundColor: p.color,
                  opacity: on ? 1 : 0.35,
                  boxShadow: on ? `0 0 10px ${p.color}` : "none",
                }}
              />
              <span style={{ color: p.color, opacity: on ? 1 : 0.6 }}>{p.label}</span>
              <span className="tabular-nums" style={{ color: p.color, opacity: on ? 1 : 0.45 }}>
                {on ? "FAOL" : "jim"}
              </span>
            </div>
          );
        })}
      </div>

      <style>{`@keyframes mk-ping{0%{transform:translate(-50%,-50%) scale(.6);opacity:.5}100%{transform:translate(-50%,-50%) scale(3);opacity:0}}`}</style>
    </div>
  );
}
```

### `src/components/Confetti.tsx`

Muvaffaqiyat konfetti animatsiyasi (6-7 s)

```tsx
import { useEffect, useMemo, useState } from "react";

const COLORS = ["#22c55e", "#38bdf8", "#facc15", "#f472b6", "#a78bfa", "#fb923c"];

type Piece = {
  id: number;
  left: number;
  delay: number;
  duration: number;
  color: string;
  size: number;
  rotate: number;
  drift: number;
};

/** Muvaffaqiyat uchun salyutga o'xshash konfetti animatsiyasi */
export function Confetti({ show, pieces = 140 }: { show: boolean; pieces?: number }) {
  const [seed, setSeed] = useState(0);

  useEffect(() => {
    if (show) setSeed((s) => s + 1);
  }, [show]);

  const items = useMemo<Piece[]>(
    () =>
      Array.from({ length: pieces }, (_, i) => ({
        id: i,
        left: Math.random() * 100,
        delay: Math.random() * 1.5,
        duration: 6.0 + Math.random() * 1.0,
        color: COLORS[i % COLORS.length]!,
        size: 6 + Math.random() * 10,
        rotate: Math.random() * 360,
        drift: (Math.random() - 0.5) * 180,
      })),
    [pieces, seed],
  );

  if (!show) return null;

  return (
    <div className="pointer-events-none absolute inset-0 z-20 overflow-hidden">
      {items.map((p) => (
        <span
          key={`${seed}-${p.id}`}
          className="absolute top-0 block rounded-[2px]"
          style={{
            left: `${p.left}%`,
            width: p.size,
            height: p.size * 1.8,
            backgroundColor: p.color,
            ["--drift" as string]: `${p.drift}px`,
            ["--rot" as string]: `${p.rotate}deg`,
            animation: `mk-confetti ${p.duration}s cubic-bezier(.2,.6,.4,1) ${p.delay}s forwards`,
          }}
        />
      ))}

      {/* salyut porlashi */}
      <span
        className="absolute left-1/2 top-1/3 size-32 -translate-x-1/2 -translate-y-1/2 rounded-full blur-2xl"
        style={{ backgroundColor: "#22c55e", animation: "mk-burst 3.5s ease-out forwards" }}
      />

      <style>{`
        @keyframes mk-confetti {
          0% { transform: translate3d(0,-10%,0) rotate(var(--rot)); opacity: 1; }
          100% { transform: translate3d(var(--drift), 115vh, 0) rotate(calc(var(--rot) + 1080deg)); opacity: .9; }
        }
        @keyframes mk-burst {
          0% { transform: translate(-50%,-50%) scale(.2); opacity: .95; }
          60% { opacity: .4; }
          100% { transform: translate(-50%,-50%) scale(5); opacity: 0; }
        }
      `}</style>
    </div>
  );
}
```

### `src/routes/_authenticated/intubation.tsx`

Sahifa (UI): ulanish paneli, animatsiya, jurnal, serial monitor

```tsx
import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { ManikinAnatomy } from "@/components/ManikinAnatomy";
import { Confetti } from "@/components/Confetti";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SENSOR_LABEL, diagnose, useManikinSerial, type SensorKey } from "@/lib/manikin-serial";
import { Activity, Plug, PlugZap, PlayCircle, Trash2, Volume2, VolumeX } from "lucide-react";
import { useDiagnosisSound, playErrorSound, playSuccessSound, stopAllSounds } from "@/lib/manikin-sound";
import intubationSample from "@/assets/intubation_sample.mp4.asset.json";


export const Route = createFileRoute("/_authenticated/intubation")({
  head: () => ({
    meta: [
      { title: "Maniken sensorlari — Navoiy filiali AI baholash" },
      {
        name: "description",
        content:
          "Arduino serial ma'lumotlari asosida maniken tish, qizilo'ngach va traxeya sensorlarini real vaqtda kuzatish va tashhis.",
      },
      { property: "og:title", content: "Maniken sensorlari — Navoiy filiali AI baholash" },
      {
        property: "og:description",
        content: "Intubatsiya manikenidagi 3 sensor signalini animatsiya va tashhis bilan kuzatish.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: IntubationPage,
});

const LEVEL_STYLE: Record<string, string> = {
  ok: "border-emerald-500/40 bg-emerald-500/10 text-emerald-500",
  warn: "border-amber-500/40 bg-amber-500/10 text-amber-500",
  danger: "border-destructive/40 bg-destructive/10 text-destructive",
  idle: "border-border bg-muted/40 text-muted-foreground",
};

function IntubationPage() {
  const [baud, setBaud] = useState("9600");
  const [threshold, setThreshold] = useState(300);
  const serial = useManikinSerial(threshold);
  const dx = diagnose(serial.active);
  const [soundOn, setSoundOn] = useState(true);
  useDiagnosisSound(dx, soundOn);
  const [celebrate, setCelebrate] = useState(false);
  const sampleVideoRef = useRef<HTMLVideoElement>(null);
  const [sampleCollapsed, setSampleCollapsed] = useState(false);
  useEffect(() => {
    if (dx.level !== "ok") {
      setCelebrate(false);
      return;
    }
    // Trubka to'g'ri joylashtirilganda 2 soniya kutib, keyin muvaffaqiyat effekti ishga tushadi
    const t = setTimeout(() => setCelebrate(true), 2000);
    return () => clearTimeout(t);
  }, [dx.level]);
  useEffect(() => {
    if (!celebrate) return;
    const t = setTimeout(() => {
      setCelebrate(false);
      stopAllSounds();
    }, 7000);
    return () => clearTimeout(t);
  }, [celebrate]);
  const keys: SensorKey[] = ["teeth", "esophagus", "trachea"];


  const connected = serial.status === "connected" || serial.status === "demo";

  return (
    <AppShell
      title="Maniken sensorlari (intubatsiya)"
      subtitle="Arduino serial ma'lumotlari asosida maniken tish, qizilo'ngach va traxeya sensorlarini real vaqtda kuzatish va tashhis"
    >
      <div className="grid gap-4 lg:grid-cols-[1.15fr_1fr]">
        <div className="space-y-4">
          <Card>
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle className="text-base">Namuna: to'g'ri intubatsiya</CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setSampleCollapsed((s) => !s)}>
                {sampleCollapsed ? "Ko'rsatish" : "Yashirish"}
              </Button>
            </CardHeader>
            {!sampleCollapsed ? (
              <CardContent className="space-y-3">
                <div className="overflow-hidden rounded-lg border border-border bg-black">
                  <video
                    ref={sampleVideoRef}
                    src={intubationSample.url}
                    controls
                    className="w-full"
                    style={{ aspectRatio: "16 / 9" }}
                    preload="metadata"
                    aria-label="To'g'ri intubatsiya namuna videosi"
                  />
                </div>
                <p className="text-xs text-muted-foreground">
                  Imtihonni boshlashdan oldin to'g'ri trubka joylashtirish texnikasini ko'rib chiqing.
                </p>
              </CardContent>
            ) : null}
          </Card>

          <Card>
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle className="text-base">Jonli animatsiya</CardTitle>
              <Badge variant="outline" className="gap-1">
                <Activity className="size-3" />
                {serial.status === "connected"
                  ? "Ulangan"
                  : serial.status === "demo"
                    ? "Demo rejim"
                    : serial.status === "connecting"
                      ? "Ulanmoqda…"
                      : serial.status === "unsupported"
                        ? "Brauzer qo'llamaydi"
                        : "Ulanmagan"}
              </Badge>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="relative overflow-hidden rounded-lg border border-border bg-card/50 p-2">
                <ManikinAnatomy active={serial.active} />
                <Confetti show={celebrate} />
              </div>


            <div className={`rounded-lg border p-3 ${LEVEL_STYLE[dx.level]}`}>
              <p className="text-sm font-semibold">{dx.title}</p>
              <p className="mt-1 text-xs opacity-90">{dx.detail}</p>
            </div>

            <div className="grid gap-2 sm:grid-cols-3">
              {keys.map((k) => (
                <div
                  key={k}
                  className={`rounded-md border p-3 ${
                    serial.active[k]
                      ? k === "trachea"
                        ? "border-emerald-500/40 bg-emerald-500/10"
                        : "border-destructive/40 bg-destructive/10"
                      : "border-border"
                  }`}
                >
                  <p className="text-[11px] text-muted-foreground">{SENSOR_LABEL[k]}</p>
                  <p className="text-lg font-semibold tabular-nums">{serial.reading[k]}</p>
                  <p className="text-[11px]">{serial.active[k] ? "FAOL" : "jim"}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        </div>

        <div className="space-y-4">

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Ulanish</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label>Baud rate</Label>
                  <Select value={baud} onValueChange={setBaud}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {["9600", "19200", "38400", "57600", "115200"].map((b) => (
                        <SelectItem key={b} value={b}>
                          {b}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label>Analog chegara</Label>
                  <Input
                    type="number"
                    value={threshold}
                    onChange={(e) => setThreshold(Number(e.target.value) || 0)}
                  />
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                {connected ? (
                  <Button variant="destructive" size="sm" onClick={() => void serial.disconnect()}>
                    <Plug className="size-4" /> Uzish
                  </Button>
                ) : (
                  <Button size="sm" onClick={() => void serial.connect(Number(baud))}>
                    <PlugZap className="size-4" /> Portga ulanish
                  </Button>
                )}
                <Button variant="outline" size="sm" onClick={serial.startDemo} disabled={connected}>
                  <PlayCircle className="size-4" /> Demo
                </Button>
                <Button variant="ghost" size="sm" onClick={serial.clearEvents}>
                  <Trash2 className="size-4" /> Jurnalni tozalash
                </Button>
                <Button
                  variant={soundOn ? "secondary" : "outline"}
                  size="sm"
                  onClick={() => {
                    const next = !soundOn;
                    setSoundOn(next);
                    if (next) playSuccessSound();
                    else stopAllSounds();
                  }}
                >
                  {soundOn ? <Volume2 className="size-4" /> : <VolumeX className="size-4" />}
                  {soundOn ? "Ovoz yoniq" : "Ovoz o'chiq"}
                </Button>
                <Button variant="outline" size="sm" onClick={playErrorSound}>
                  Xato ovozi
                </Button>
                <Button variant="outline" size="sm" onClick={playSuccessSound}>
                  Muvaffaqiyat kuyi
                </Button>
              </div>

              {serial.error ? <p className="text-xs text-destructive">{serial.error}</p> : null}

              <p className="text-[11px] leading-relaxed text-muted-foreground">
                Chrome/Edge (desktop) kerak. Arduino quyidagi formatlardan birida yozsa yetarli:
                <code className="mx-1 rounded bg-muted px-1">T:1 E:0 L:0</code>,
                <code className="mx-1 rounded bg-muted px-1">{"{\"teeth\":1,\"eso\":0,\"lung\":0}"}</code> yoki
                <code className="mx-1 rounded bg-muted px-1">512,0,800</code> (tartib: tish, oshqazon, o'pka).
                0/1 signal to'g'ridan-to'g'ri, analog qiymatlar esa chegara bo'yicha hisoblanadi.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Hodisalar jurnali</CardTitle>
            </CardHeader>
            <CardContent className="max-h-64 space-y-1.5 overflow-y-auto">
              {serial.events.length === 0 ? (
                <p className="text-xs text-muted-foreground">Hodisa yo'q.</p>
              ) : (
                serial.events.map((ev) => (
                  <div key={ev.id} className="flex items-center justify-between rounded-md border border-border px-2 py-1.5 text-xs">
                    <span>
                      {SENSOR_LABEL[ev.sensor]} — {ev.kind === "start" ? "faollashdi" : "to'xtadi"}
                    </span>
                    <span className="tabular-nums text-muted-foreground">
                      {new Date(ev.at).toLocaleTimeString("uz-UZ")}
                    </span>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Serial monitor (xom)</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="max-h-40 overflow-y-auto rounded-md bg-muted/40 p-2 text-[11px] leading-relaxed">
                {serial.lines.length ? serial.lines.join("\n") : "—"}
              </pre>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
```
