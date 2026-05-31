# Hardware — theodio

This document is the hardware spec for the portable podcast reader. It lists
goals, the proposed architecture, component options with tradeoffs, and the
open decisions that still need to be made before we order parts.

Items marked **Decided** are settled. Items marked **Decision needed** are
the points to resolve before ordering.

## 1. Goals and constraints

| # | Goal                                   | Implication                                    |
|---|----------------------------------------|------------------------------------------------|
| 1 | Listen to podcasts offline             | Local storage, feed sync when online           |
| 2 | Portable, pocketable                   | Pi Zero footprint, LiPo battery, tight case    |
| 3 | All-day listening on one charge        | Power budget target: ≥ 10 h of playback        |
| 4 | Usable without a phone or screen glare | Physical controls, readable display indoors    |
| 5 | Built from off-the-shelf parts         | No custom PCB for v1; HATs / pHATs only        |
| 6 | Hackable / modifiable                  | Expose UART and any spare GPIO                 |

Non-goals for v1: streaming, wireless headphones, touchscreen UI, voice
control, a music library (it's a *podcast* player).

## 2. System block diagram

```
                              +-------------------+
                              |  microSD          |
                              |  (episodes, DB)   |
                              +---------+---------+
                                        |
                              +---------v---------+
   Wi-Fi (built-in)  <------> |  Raspberry Pi     |
                              |  Zero 2 W         |
                              +---------+---------+
                                        | 40-pin header
                              +---------v---------+
                              |  Whisplay HAT     |
                              |                   | --> 1.69" LCD
                              |  ST7789 + WM8960  | --> 1 W speaker
                              |  buttons + RGB    | --> headphone out
                              +---------+---------+
                                        |
                              +---------v---------+
   USB micro <---------------- |  PowerBoost 1000C |
                              |  + 4000 mAh LiPo  |
                              +-------------------+
```

## 3. Components

### 3.1 Compute — **Decided: Raspberry Pi Zero 2 W**

| Option            | Pros                                              | Cons                                          |
|-------------------|---------------------------------------------------|-----------------------------------------------|
| **Pi Zero 2 W**   | Quad-core A53 (64-bit), Zero form factor, ~0.7 W  | 512 MB RAM (fine for this workload)           |
| Pi Zero W (orig.) | Slightly lower idle, same footprint               | Single-core ARMv6, 32-bit only, Rust tier-2   |
| Pi 4 B (2 GB)     | Lots of headroom, USB-C power                     | 85×56 mm breaks the Zero form, ~3 W idle      |
| Pi 5              | Fast, modern                                      | Overkill, high idle draw                      |

**Chosen:** Pi Zero 2 W. Pivoted back from the Pi 4 once the Whisplay HAT
was on the table — the HAT is built for the Zero footprint, so a Pi 4 would
have it overhanging the carrier board with no real software benefit.
Quad A53 + 64-bit Rust toolchain give plenty of headroom for podcast
decoding plus UI rendering, with ~0.7 W idle.

### 3.2 Display + audio + buttons — **Decided: PiSugar Whisplay HAT**

The Whisplay HAT collapses what was previously three open decisions
(display, DAC + amp, basic controls) into a single ~50 USD board with the
same 65×30 mm footprint as the Pi Zero.

| Subsystem    | What the HAT provides                                |
|--------------|------------------------------------------------------|
| Display      | 1.69" IPS, 240×280, **ST7789** over SPI0 (CS0)       |
|              | Default control pins: DC=27, RST=4, BL=22            |
| Audio codec  | **WM8960** over I²S + I²C — mainline ALSA driver     |
| Speaker      | Onboard 8 Ω / 1 W mono                               |
| Headphone    | Speaker/headphone output (3.5 mm or wire-out)        |
| Microphones  | Dual MEMS (unused for v1, kept for future projects)  |
| Controls     | Onboard buttons (gestures: click / long / 4×rapid) + RGB LEDs |

This also locks the Rust software choices:

- Display: `mipidsi` (ST7789 driver) + `embedded-graphics` for the UI.
- Audio: ALSA via `alsa-rs` or `cpal` — WM8960 is supported by the
  mainline kernel driver, exposed as a standard ALSA sound card.

Caveat: if we ever pair the Whisplay with a PiSugar **S Plus** battery
HAT, the AUTO switch must be off, otherwise the WM8960 isn't detected
(I²C bus contention — per PiSugar docs).

### 3.3 Power — **Decided: 4000 mAh LiPo + Adafruit PowerBoost 1000C**

Options considered, with realistic runtime (LiPo → 5 V boost at ~85 %
efficiency, on the consumption profile in the table below):

| Option                          | Cells       | HP, Wi-Fi off | Notes                                |
|---------------------------------|-------------|---------------|--------------------------------------|
| PiSugar 3                       | 1200 mAh    | ~3.5 h        | Clean Zero form fit, RTC, magnetic   |
| PiSugar 3 Plus                  | 5000 mAh    | ~14 h         | Pi 4 footprint — overhangs the Zero  |
| **PowerBoost 1000C + 4000 mAh LiPo** | 4000 mAh | **~12 h**  | Keeps Zero footprint, more wiring    |
| Waveshare UPS HAT (B/C) or 2×18650 | ~6800 mAh | ~20 h         | Bulky, breaks pocketability          |

**Chosen:** Adafruit PowerBoost 1000C feeding off a ~60 × 70 × 8 mm flat
LiPo (4000 mAh, single cell with built-in PCM, JST-PH 2.0). Hits the ≥ 10 h
playback goal, and the build is fully under our control (charger, boost,
load switch). The cell sits next to the Pi rather than directly under it,
which pushes the case envelope to ~75 × 40 × 25 mm — still pocketable.

We lose the PiSugar's built-in RTC and power button polish: RTC is
replaced by an NTP sync at boot, and a discrete momentary tactile switch
handles power on/off. A 1 A polyfuse in series with the LiPo + acts as a
second-line protection on top of the cell's PCM.

Realistic power budget @ 5 V on a Pi Zero 2 W + Whisplay HAT:

| Subsystem                                   | Typical  | Notes               |
|---------------------------------------------|----------|---------------------|
| Pi Zero 2 W (Wi-Fi on, decoding audio)      | 250 mA   | Bursts higher       |
| Pi Zero 2 W (Wi-Fi off, decoding audio)     | 150 mA   |                     |
| WM8960 codec + 1 W speaker at low volume    |  80 mA   | ~30 mA on headphones |
| ST7789 LCD with backlight                   |  40 mA   |                     |
| RGB LEDs (status only, dimmed)              |   5 mA   |                     |
| **Total (playback, speaker, Wi-Fi on)**     | **≈ 375 mA → 1.9 W** | ~6.5 h on 4000 mAh |
| **Total (playback, headphones, Wi-Fi off)** | **≈ 225 mA → 1.1 W** | **~12 h on 4000 mAh** |

To hit the all-day target reliably the software (Rust) will keep Wi‑Fi off
during playback and sync feeds opportunistically — this is the realistic
mode of use anyway (commute, walks, etc.).

### 3.4 Storage

32 GB A1-rated microSD. No decision needed.

### 3.5 Enclosure

3D-printed two-shell design wrapping Pi Zero 2 W + Whisplay HAT + 4000 mAh
LiPo (cell sits beside the Pi rather than under it). Approximate envelope:
**~75 × 40 × 25 mm** + button caps and LCD window — still pocketable.
STLs land under `hardware/enclosure/` once the controls decision is locked.

## 4. Pinout

The Whisplay HAT consumes (subject to final confirmation against the HAT
schematic / device tree overlay):

| Bus / pin             | Use                                |
|-----------------------|------------------------------------|
| SPI0 (GPIO 9/10/11, CS = GPIO 8) | LCD data                |
| I²S (GPIO 18/19/20/21)           | Audio data              |
| I²C1 (GPIO 2/3)                  | WM8960 control          |
| GPIO 4                           | LCD RST                 |
| GPIO 22                          | LCD backlight enable    |
| GPIO 27                          | LCD DC                  |
| Remaining GPIO                   | Onboard buttons + RGB LEDs |

Spare GPIO available on the bottom header pins (to confirm):
GPIO 5, 6, 12, 13, 16, 17, 23, 24, 25, 26. That's enough for a rotary
encoder (A/B + push = 3 pins) if we choose to supplement the HAT's buttons.

## 5. Open decisions (ordered)

1. ~~**Compute**~~ — **Pi Zero 2 W**.
2. ~~**Display**~~ — **Whisplay HAT (1.69" ST7789)**.
3. ~~**Audio**~~ — **Whisplay HAT (WM8960 + 1 W speaker)**.
4. ~~**Power pack**~~ — **4000 mAh LiPo + Adafruit PowerBoost 1000C**.
5. **Controls supplement**: rely on Whisplay's onboard buttons + gestures
   (single click / long press / 4 rapid clicks → cycle / select / exit),
   or add a rotary encoder on the spare GPIO for proper scrubbing + volume.
6. **Enclosure**: print fully custom STLs.

Once 5 is pinned down, we can order parts and start on the Rust software.

## 6. Bill of materials (draft)

| Qty | Part                              | Vendor | Price  | Link |
|-----|-----------------------------------|--------|--------|------|
|  1  | Raspberry Pi Zero 2 W             |        |        |      |
|  1  | PiSugar Whisplay HAT              |        | ~50 €  |      |
|  1  | microSD 32 GB A1                  |        |        |      |
|  1  | LiPo 4000 mAh (≈ 60×70×8 mm, 3.7 V, PCM, JST-PH) |  | ~25 €  |      |
|  1  | Adafruit PowerBoost 1000C         |        | ~20 €  |      |
|  1  | Polyfuse 1 A (PTC, MF-R)          |        |  ~1 €  |      |
|  1  | Momentary tactile switch (power)  |        |        |      |
|  1  | Rotary encoder w/ switch (optional)|       |        |      |
|  1  | Enclosure filament (PETG)         |        |        |      |
