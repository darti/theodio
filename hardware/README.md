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
| 2 | Portable (belt-clip sized)             | Pi 4 footprint + LiPo, custom enclosure        |
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

### 3.1 Compute — **Decided: Raspberry Pi 4 B (2 GB)**

| Option          | Pros                                  | Cons                               |
|-----------------|---------------------------------------|------------------------------------|
| Pi Zero 2 W     | Tiny, low power (~0.7 W idle), cheap  | Only 512 MB RAM, slower build      |
| **Pi 4 B (2 GB)** | Plenty of RAM and CPU, USB-C power, onboard 3.5 mm jack | Larger (85×56 mm), ~3 W idle      |
| Pi 5 (2 GB)     | Fast, modern I/O                      | High idle draw, overkill           |
| Radxa Zero 3W   | Pi-Zero pin-compatible, more RAM      | Less community, different OS quirks|

**Chosen:** Pi 4 B (2 GB). Trades pocketability and battery life for headroom
and easier development (USB-C power, multiple USB-A for debug, gigabit
ethernet, onboard 3.5 mm jack as a fallback before the DAC is wired up).
The build target becomes a "belt clip" form factor rather than truly
pocketable.

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

Now that the Pi 4 is locked in, the PiSugar 3 (Zero form factor) is out.
Options that fit the Pi 4 footprint:

| Option                          | Cells           | Notes                                |
|---------------------------------|-----------------|--------------------------------------|
| PiSugar 3 Plus                  | 5000 mAh LiPo   | Pi 4-sized, RTC, USB-C, magnetic     |
| Waveshare UPS HAT (B)           | 2× 18650        | Chunkier, long runtime, swappable    |
| Geekworm X728 / X1201           | 2× 18650        | Same idea, more I/O                  |
| Adafruit PowerBoost 1000C + LiPo| any LiPo        | Discrete, most wiring, most flexible |

**Proposal:** PiSugar 3 Plus (5000 mAh). Cleanest mechanical fit on the Pi 4,
RTC included so the device keeps time without a network sync, and 5000 mAh
puts us in range of the all-day-listening goal.

Rough power budget @ 5 V on a Pi 4 B:

| Subsystem                            | Typical | Notes               |
|--------------------------------------|---------|---------------------|
| Pi 4 B (Wi-Fi on, idle + decoding)   | 600 mA  | ~3 W; bursts higher |
| I²S DAC + amp at low volume          |  40 mA  |                     |
| e-ink display                        |   1 mA  | During refresh only |
| Buttons / encoder                    |  ~0 mA  |                     |
| **Total (playback)**                 | **≈ 650 mA** | ~1.5 h per 1000 mAh |

5000 mAh ≈ 7–8 h playback with Wi‑Fi on, comfortably ≥ 10 h if we keep
Wi‑Fi off during playback (drops the Pi to ~400 mA → 5000 mAh ≈ 12 h).
Strategy: sync feeds + download episodes opportunistically when Wi‑Fi is on,
then airplane-mode the radio during playback. The software (Rust) will own
this policy.

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

1. ~~**Compute**~~ — **Pi 4 B (2 GB)**.
2. **Power pack**: PiSugar 3 Plus 5000 mAh vs Waveshare UPS HAT with 2×
   18650s. Trades single-piece neatness for longer / swappable runtime.
3. **Display**: e-ink (outdoor-friendly, static UI) vs OLED (cheap, small).
4. **Controls**: 5 buttons vs 3 buttons + rotary encoder.
5. **Audio**: integrated I²S amp (mono speaker) vs DAC + headphone jack
   (+ optional amp/speaker). The Pi 4's onboard 3.5 mm jack is usable for
   bring-up before any DAC arrives.
6. **Enclosure**: off-the-shelf Pi 4 case we modify vs fully custom print.

Once 2–5 are pinned down, we can order parts and start on the Rust software.

## 6. Bill of materials (draft)

Fill in once decisions above are made. Placeholder structure:

| Qty | Part                        | Vendor | Price | Link |
|-----|-----------------------------|--------|-------|------|
|  1  | Raspberry Pi 4 B (2 GB)     |        |       |      |
|  1  | microSD 32 GB A1            |        |       |      |
|  1  | PiSugar 3 Plus 5000 mAh     |        |       |      |
|  1  | PCM5102 I²S DAC module      |        |       |      |
|  1  | 3.5 mm stereo jack PCB      |        |       |      |
|  1  | Waveshare 2.13" e-ink       |        |       |      |
|  3  | 6×6 mm tactile buttons      |        |       |      |
|  1  | Rotary encoder with switch  |        |       |      |
|  1  | Enclosure filament (PETG)   |        |       |      |
