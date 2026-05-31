"""theodio — portable podcast reader enclosure (build123d).

Parametric two-shell case for Pi Zero 2 W + Whisplay HAT + 4000 mAh LiPo
+ EC11 encoder + PowerBoost. All dimensions in mm.

First-pass design from datasheets only; many positions are estimates until
the breadboard prototype confirms them. Look for ``TODO`` comments.

Usage::

    pip install -r requirements.txt
    python enclosure.py                          # both shells as STL
    python enclosure.py --part top    --out .    # top.stl
    python enclosure.py --part bottom --out .    # bottom.stl
    python enclosure.py --part assembly          # assembly.step (geometry only)

For interactive viewing, use the standard build123d viewer of your choice
(e.g. ``ocp_vscode``):

    from enclosure import full_shell, assembly
    show(assembly())
"""

from __future__ import annotations

import argparse
from pathlib import Path

from build123d import (
    Align,
    Box,
    Compound,
    Cylinder,
    Pos,
    Rot,
    export_step,
    export_stl,
)

MIN = (Align.MIN, Align.MIN, Align.MIN)

# ============================================================
# Component dimensions
# ============================================================

# Raspberry Pi Zero 2 W (datasheet)
PI_W, PI_D, PI_PCB_H = 65.0, 30.0, 1.4
PI_HOLE_D = 2.75
PI_HOLE_PITCH_W, PI_HOLE_PITCH_D = 58.0, 23.0

# PiSugar Whisplay HAT (same 65x30 PCB, stacks on the 40-pin header).
HAT_PCB_H = 1.6
HAT_COMPONENTS_H = 4.5  # TODO measure: LCD bezel + connectors
GPIO_HEADER_H = 8.5  # stacking header

# LCD visible aperture (1.69" IPS, ~30x37 mm).
# TODO confirm centre offset from the Whisplay schematic.
LCD_W, LCD_D = 30.0, 37.0
LCD_OFF_X, LCD_OFF_Y = 0.0, 0.0

# 4000 mAh LiPo cell
LIPO_W, LIPO_D, LIPO_H = 70.0, 60.0, 8.0

# Adafruit PowerBoost 1000C
PB_W, PB_D, PB_H = 36.7, 22.6, 6.4

# EC11 rotary encoder (typical Alps clone)
ENC_BODY_W, ENC_BODY_D, ENC_BODY_H = 12.5, 13.5, 7.0
ENC_THREAD_D, ENC_THREAD_H = 7.0, 7.0
ENC_SHAFT_D, ENC_SHAFT_H = 6.0, 13.0

# Misc panel-mount parts
TACT_D = 6.5  # power tactile switch panel diameter
PHONE_JACK_D = 6.5  # 3.5 mm jack panel hole
MICROSD_W, MICROSD_H = 12.5, 2.5

# ============================================================
# Case parameters
# ============================================================

WALL = 2.0
TOL = 0.3  # print/fit clearance
FOAM_PAD = 1.0  # soft pad under the LiPo
PI_RISER = 4.0  # gap between LiPo top and Pi PCB bottom

CAVITY_W = LIPO_W + 4
CAVITY_D = LIPO_D + 4

Z_LIPO = FOAM_PAD
Z_PI = Z_LIPO + LIPO_H + PI_RISER
Z_HAT = Z_PI + PI_PCB_H + GPIO_HEADER_H
Z_LCD_TOP = Z_HAT + HAT_PCB_H + HAT_COMPONENTS_H
CAVITY_H = Z_LCD_TOP + 2

CASE_W = CAVITY_W + 2 * WALL
CASE_D = CAVITY_D + 2 * WALL
CASE_H = CAVITY_H + 2 * WALL

PI_X = (CAVITY_W - PI_W) / 2
PI_Y = (CAVITY_D - PI_D) / 2
LIPO_X = (CAVITY_W - LIPO_W) / 2
LIPO_Y = (CAVITY_D - LIPO_D) / 2
PB_X = 2.0
PB_Y = CAVITY_D - PB_D - 1.0

# Encoder hangs from the top shell beside the Pi+HAT stack.
# TODO confirm clearance once the LCD aperture position is known.
ENC_COL_X = PI_X + PI_W + 3.0
ENC_COL_Y = (CAVITY_D - ENC_BODY_D) / 2
ENC_COL_Z = Z_HAT - ENC_BODY_H

# Split between the two shells: just above the Pi PCB so the GPIO header
# stays accessible from the top shell.
SPLIT_Z = Z_PI + PI_PCB_H + 1.0


# ============================================================
# Primitive helpers
# ============================================================

def _box(x: float, y: float, z: float, w: float, d: float, h: float) -> Box:
    """Axis-aligned box with its MIN corner at (x, y, z)."""
    return Pos(x, y, z) * Box(w, d, h, align=MIN)


def _cyl_z(x: float, y: float, z_bottom: float, diameter: float, height: float) -> Cylinder:
    """Cylinder along Z, bottom face centred at (x, y, z_bottom)."""
    return Pos(x, y, z_bottom + height / 2) * Cylinder(diameter / 2, height)


def _cyl_y(x: float, y_bottom: float, z: float, diameter: float, height: float) -> Cylinder:
    """Cylinder along Y, bottom face centred at (x, y_bottom, z)."""
    return Pos(x, y_bottom + height / 2, z) * Rot(X=90) * Cylinder(diameter / 2, height)


def _cyl_x(x_bottom: float, y: float, z: float, diameter: float, height: float) -> Cylinder:
    """Cylinder along X, bottom face centred at (x_bottom, y, z)."""
    return Pos(x_bottom + height / 2, y, z) * Rot(Y=90) * Cylinder(diameter / 2, height)


# ============================================================
# Case construction
# ============================================================

def _lcd_window():
    return _box(
        PI_X + (PI_W - LCD_W) / 2 + LCD_OFF_X,
        PI_Y + (PI_D - min(LCD_D, PI_D - 1)) / 2 + LCD_OFF_Y,
        CAVITY_H - 0.1,
        LCD_W,
        min(LCD_D, PI_D - 1),
        WALL + 0.2,
    )


def _encoder_hole():
    return _cyl_z(
        ENC_COL_X + ENC_BODY_W / 2,
        ENC_COL_Y + ENC_BODY_D / 2,
        CAVITY_H - 0.1,
        ENC_THREAD_D + TOL,
        WALL + 0.2,
    )


def _power_switch_hole():
    return _cyl_x(CAVITY_W - 0.1, 6.0, Z_PI + 2.0, TACT_D + TOL, WALL + 0.2)


def _headphone_jack_hole():
    # Front long edge. TODO confirm whether the HAT exposes a panel-mount
    # jack or solder pads needing a flying-lead jack.
    return _cyl_y(10.0, -WALL - 0.1, Z_HAT + 2.0, PHONE_JACK_D + TOL, WALL + 0.2)


def _microsd_slot():
    return _box(
        -WALL - 0.1,
        PI_Y + 2.5,
        Z_PI - MICROSD_H / 2,
        WALL + 0.2,
        MICROSD_W,
        MICROSD_H + 2 * TOL,
    )


def full_shell():
    outer = _box(-WALL, -WALL, -WALL, CASE_W, CASE_D, CASE_H)
    cavity = _box(0, 0, 0, CAVITY_W, CAVITY_D, CAVITY_H)
    shell = outer - cavity
    shell -= _lcd_window()
    shell -= _encoder_hole()
    shell -= _power_switch_hole()
    shell -= _headphone_jack_hole()
    shell -= _microsd_slot()
    return shell


def _half(z_min: float, z_max: float):
    """Half-space box used to slice the full shell at the split plane."""
    return _box(-WALL - 1, -WALL - 1, z_min, CASE_W + 2, CASE_D + 2, z_max - z_min)


def top_shell():
    return full_shell() & _half(SPLIT_Z, CAVITY_H + WALL + 1)


def bottom_shell():
    shell = full_shell() & _half(-WALL - 1, SPLIT_Z)
    sx0 = PI_X + (PI_W - PI_HOLE_PITCH_W) / 2
    sy0 = PI_Y + (PI_D - PI_HOLE_PITCH_D) / 2
    for x in (sx0, sx0 + PI_HOLE_PITCH_W):
        for y in (sy0, sy0 + PI_HOLE_PITCH_D):
            post = _cyl_z(x, y, 0, 5.0, Z_PI)
            pocket = _cyl_z(x, y, Z_PI - 4.5, PI_HOLE_D, 4.6)
            shell = (shell + post) - pocket
    return shell


# ============================================================
# Assembly view (for STEP export and interactive viewing)
# ============================================================

def assembly() -> Compound:
    parts = [
        full_shell(),
        _box(LIPO_X, LIPO_Y, Z_LIPO, LIPO_W, LIPO_D, LIPO_H),
        _box(PB_X, PB_Y, Z_LIPO, PB_W, PB_D, PB_H),
        _box(PI_X, PI_Y, Z_PI, PI_W, PI_D, PI_PCB_H),
        _box(PI_X, PI_Y, Z_HAT, PI_W, PI_D, HAT_PCB_H),
        _box(
            PI_X + (PI_W - LCD_W) / 2 + LCD_OFF_X,
            PI_Y + (PI_D - min(LCD_D, PI_D - 1)) / 2 + LCD_OFF_Y,
            Z_HAT + HAT_PCB_H,
            LCD_W,
            min(LCD_D, PI_D - 1),
            HAT_COMPONENTS_H,
        ),
        _box(ENC_COL_X, ENC_COL_Y, ENC_COL_Z, ENC_BODY_W, ENC_BODY_D, ENC_BODY_H),
        _cyl_z(
            ENC_COL_X + ENC_BODY_W / 2,
            ENC_COL_Y + ENC_BODY_D / 2,
            ENC_COL_Z + ENC_BODY_H,
            ENC_SHAFT_D,
            ENC_THREAD_H + ENC_SHAFT_H,
        ),
    ]
    return Compound(children=parts)


# ============================================================
# CLI
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--part",
        choices=("top", "bottom", "both", "assembly"),
        default="both",
    )
    parser.add_argument("--out", type=Path, default=Path("."))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    if args.part in ("top", "both"):
        out = args.out / "top.stl"
        export_stl(top_shell(), str(out))
        print(f"wrote {out}")
    if args.part in ("bottom", "both"):
        out = args.out / "bottom.stl"
        export_stl(bottom_shell(), str(out))
        print(f"wrote {out}")
    if args.part == "assembly":
        out = args.out / "assembly.step"
        export_step(assembly(), str(out))
        print(f"wrote {out}")

    print(
        f"envelope: {CASE_W:.0f} x {CASE_D:.0f} x {CASE_H:.0f} mm "
        f"(cavity {CAVITY_W:.0f} x {CAVITY_D:.0f} x {CAVITY_H:.0f})"
    )


if __name__ == "__main__":
    main()
