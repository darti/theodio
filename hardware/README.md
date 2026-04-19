# Hardware — theodio

This document is the hardware spec for the portable podcast reader. It lists
goals, the proposed architecture, component options with tradeoffs, and the
open decisions that still need to be made before we order parts.

Everything here is a starting proposal — nothing is final. Sections marked
**Decision needed** are the points to resolve first.

## 1. Goals and constraints

| # | Goal                                   | Implication                                    |
|---|----------------------------------------|------------------------------------------------|
| 1 | Listen to podcasts offline             | Local storage, feed sync when online           |
| 2 | Portable, pocketable                   | Small PCB footprint, LiPo battery, enclosure   |
| 3 | All-day listening on one charge        | Power budget target: ≥ 10 h of playback        |
| 4 | Usable without a phone or screen glare | Physical controls, readable display in sun     |
| 5 | Built from off-the-shelf parts         | No custom PCB for v1; HATs + pHATs only        |
| 6 | Hackable / modifiable                  | Expose UART and one spare GPIO header          |

Non-goals for v1: streaming, wireless headphones, touchscreen UI, voice
control, a music library (it's a *podcast* player).

## 2. System block diagram

```
                      +---------------------+
   Wi-Fi  <---------- |                     |  <----  microSD (episodes, DB)
                      |   Raspberry Pi      |
   Buttons (GPIO) --> |   (compute)         |  ---->  I²C display
   Rotary enc (GPIO)->|                     |  ---->  I²S DAC --> Amp --> Speaker
                      +----------+----------+                    \--> Headphone jack
                                 |
                              5 V rail
                                 ^
                      +----------+----------+
   USB-C  ----------> |   Charger + boost   | <----- 3.7 V LiPo
                      +---------------------+
```

## 3. Component options

### 3.1 Compute — **Decision needed**

| Option          | Pros                                  | Cons                               |
|-----------------|---------------------------------------|------------------------------------|
| Pi Zero 2 W     | Tiny, low power (~0.7 W idle), cheap  | Only 512 MB RAM, slower build      |
| Pi 4 B (2 GB)   | Plenty of RAM and CPU                 | Larger, ~3 W idle, shorter battery |
| Pi 5 (2 GB)     | Fast, modern I/O                      | High idle draw, overkill           |
| Radxa Zero 3W   | Pi-Zero pin-compatible, more RAM      | Less community, different OS quirks|

**Proposal:** Pi Zero 2 W. Podcast playback is trivially light, and battery
life dominates — a Pi 4/5 would halve runtime without any user-visible gain.

### 3.2 Audio output — **Decision needed**

The Pi's built-in audio is PWM on the Zero (no 3.5 mm jack) and generally
noisy on all models. We need a real DAC.

| Option                       | Interface | Notes                                |
|------------------------------|-----------|--------------------------------------|
| Adafruit I²S 3 W amp (MAX98357A) | I²S   | Mono, drives a speaker directly      |
| PCM5102 I²S DAC + PAM8403 amp    | I²S   | Stereo, separate amp for speakers    |
| HiFiBerry MiniAmp                | I²S   | Stereo, clean, larger HAT            |
| USB DAC dongle                    | USB  | Simplest, but uses the only USB port |

**Proposal:** PCM5102 I²S DAC feeding a 3.5 mm headphone jack, with an
optional PAM8403 + small speaker hanging off the same DAC for loudspeaker
mode. Trades a bit of complexity for stereo + headphone support.

### 3.3 Display — **Decision needed**

| Option                       | Refresh     | Sunlight  | Power   | Notes                     |
|------------------------------|-------------|-----------|---------|---------------------------|
| SSD1306 128×64 OLED (I²C)    | Fast        | Poor-fair | Low     | Cheap, tiny UI area       |
| SH1106 128×64 OLED (I²C/SPI) | Fast        | Poor-fair | Low     | Slightly larger modules   |
| Waveshare 2.13" e-ink        | Seconds     | Excellent | ~0 idle | Perfect for static "now playing" |
| 2.8" SPI TFT (ST7789)        | Fast        | Fair      | Higher  | Colour, bigger UI         |

**Proposal:** Waveshare 2.13" e-ink. The UI is mostly static ("now playing",
queue, progress bar), refresh rate doesn't matter, and it's readable outdoors
with zero backlight draw. Only updates on state change.

### 3.4 Controls — **Decision needed**

Minimum set: play/pause, prev track, next track, volume -, volume +.

| Option                   | Pros                               | Cons                         |
|--------------------------|------------------------------------|------------------------------|
| 5 tactile buttons        | Simple, cheap, bulletproof         | More enclosure holes         |
| 3 buttons + rotary enc.  | Scrubbing and volume feel great    | Extra GPIO + encoder library |
| Capacitive touch pads    | No moving parts                    | Poor feel through a case     |

**Proposal:** 3 buttons (prev / play-pause / next) plus one rotary encoder
with push for volume and long-press for "mark played". Saves a button and
makes scrubbing/volume feel right.

### 3.5 Power — **Decision needed**

| Option                        | Notes                                          |
|-------------------------------|------------------------------------------------|
| PiSugar 3 (Zero form factor)  | All-in-one: LiPo + charger + RTC, magnetic     |
| Waveshare UPS HAT (B)         | 18650 cells, chunkier, long runtime            |
| Adafruit PowerBoost 1000C     | Discrete: pair with a raw LiPo, more wiring    |

**Proposal:** PiSugar 3 (1200 mAh). Cleanest mechanical fit for the Zero 2 W,
includes an RTC so the device knows the time without a network sync.

Rough power budget @ 5 V:

| Subsystem                        | Typical | Notes               |
|----------------------------------|---------|---------------------|
| Pi Zero 2 W (Wi-Fi on, decoding) | 350 mA  | Bursts higher       |
| I²S DAC + amp at low volume      |  40 mA  |                     |
| e-ink display                    |   1 mA  | During refresh only |
| Buttons / encoder                |  ~0 mA  |                     |
| **Total (playback)**             | **≈ 400 mA** | ~3 h per 1000 mAh |

1200 mAh ≈ 3 h playback. That's short of the 10 h goal — we'll need either a
larger pack (Waveshare UPS with 2× 18650 ≈ 12–15 h) or to keep Wi‑Fi off
during playback (drops to ~150 mA → ~8 h). **This is the main open
tradeoff.**

### 3.6 Storage

32 GB A1-rated microSD. No decision needed — cheap, plentiful, and enough
for hundreds of episodes.

### 3.7 Enclosure

3D-printed, two-shell design with button caps and a cutout for the e-ink
window and headphone jack. STLs live under `hardware/enclosure/` (TBD once
the component set is locked).

## 4. Proposed pinout

Subject to change based on chosen DAC HAT; I²S uses fixed pins on the Pi.

```
3V3   -> OLED/e-ink VCC
GND   -> common ground
GPIO  2 (SDA)      -> display I²C (only if I²C display chosen)
GPIO  3 (SCL)      -> display I²C
GPIO 18 (PCM_CLK)  -> I²S DAC BCK       (fixed)
GPIO 19 (PCM_FS)   -> I²S DAC LRCK      (fixed)
GPIO 21 (PCM_DOUT) -> I²S DAC DIN       (fixed)
GPIO 17            -> Prev button    (to GND, internal pull-up)
GPIO 22            -> Play/Pause     (to GND, internal pull-up)
GPIO 23            -> Next button    (to GND, internal pull-up)
GPIO  5            -> Rotary encoder A
GPIO  6            -> Rotary encoder B
GPIO 13            -> Rotary encoder push
GPIO 24, 25        -> reserved / spare header
```

If we pick the Waveshare 2.13" e-ink, it uses SPI0 + a handful of control
lines (CS=8, DC=25, RST=17, BUSY=24) — note the collision with GPIO 17/25
above, which would bump the Prev button to GPIO 27 and reclaim 25 for e-ink
DC. Will be finalised once the display is locked.

## 5. Open decisions (ordered)

1. **Compute**: Pi Zero 2 W vs something else.
2. **Target battery life**: ~3 h (small pack) vs ~10 h (Waveshare UPS with
   18650s) — drives enclosure size.
3. **Display**: e-ink (outdoor-friendly, static UI) vs OLED (cheap, small).
4. **Controls**: 5 buttons vs 3 buttons + rotary encoder.
5. **Audio**: integrated I²S amp (mono speaker) vs DAC + headphone jack
   (+ optional amp/speaker).
6. **Enclosure**: off-the-shelf case we adapt, vs fully custom print.

Once 1–5 are pinned down, we can order parts and start on the Rust software.

## 6. Bill of materials (draft)

Fill in once decisions above are made. Placeholder structure:

| Qty | Part                        | Vendor | Price | Link |
|-----|-----------------------------|--------|-------|------|
|  1  | Raspberry Pi Zero 2 W       |        |       |      |
|  1  | microSD 32 GB A1            |        |       |      |
|  1  | PiSugar 3 1200 mAh          |        |       |      |
|  1  | PCM5102 I²S DAC module      |        |       |      |
|  1  | 3.5 mm stereo jack PCB      |        |       |      |
|  1  | Waveshare 2.13" e-ink       |        |       |      |
|  3  | 6×6 mm tactile buttons      |        |       |      |
|  1  | Rotary encoder with switch  |        |       |      |
|  1  | Enclosure filament (PETG)   |        |       |      |
