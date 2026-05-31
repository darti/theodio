# Enclosure

Parametric 3D-printable case for the theodio podcast reader. Written in
[OpenSCAD](https://openscad.org/) so dimensions live as named variables at
the top of the file, every change is git-diffable, and there's no binary
project file to corrupt.

## Status: v0 — envelope study

This is a first pass from **datasheets only**. The boards haven't been
breadboarded yet, so several dimensions and component positions are
estimates. Treat the rendered STLs as visualisations, not print-ready
files. Anything tagged `TODO` inside `enclosure.scad` is something to
verify against the actual hardware once it arrives.

Most likely to shift after the first prototype:

- **Whisplay HAT height** above the GPIO header (`hat_components_h`) — the
  LCD bezel and connector heights are estimates.
- **LCD aperture position** on the Whisplay PCB (`lcd_off_x`, `lcd_off_y`)
  — the panel may not be centred.
- **Headphone jack location** — the spec doesn't say whether the Whisplay
  exposes a panel-mount jack or solder pads needing a flying lead.
- **Encoder column position** — currently placed beside the Pi+HAT stack;
  may need to move once we see what the real LCD aperture looks like.
- **Pi standoff height** (`pi_riser`) — needs enough clearance for the
  Pi's USB and HDMI connectors on the underside.

## Layout

```
            top shell
   +------------------------+
   |   [   LCD   ] [ enc ]  |
   |     Whisplay HAT       |
   |  ----- GPIO header --- |
   +------------------------+   <-- split plane (~split_z)
   |   Pi Zero 2 W on standoffs
   |   ---- pi_riser ----
   |   LiPo 4000 mAh ([pb])
   +------------------------+
            bottom shell
```

External envelope (current parameters): roughly **75 × 65 × 42 mm**.
Larger than the 75 × 40 × 25 mm placeholder in `../README.md` because
the LiPo's true ~60 × 70 × 8 mm footprint dominates the case. The
hardware README will get the corrected envelope once the design settles.

## Rendering

OpenSCAD ≥ 2021.01.

```bash
# Visualise component fit inside a transparent shell (default in GUI)
openscad enclosure.scad

# Export an STL
openscad -o assembly.stl -D 'part="assembly"' enclosure.scad
openscad -o bottom.stl   -D 'part="bottom"'   enclosure.scad
openscad -o top.stl      -D 'part="top"'      enclosure.scad
openscad -o both.stl     -D 'part="both"'     enclosure.scad   # side by side
```

Rendered STLs are gitignored — only the source `.scad` is tracked.

## Printing notes (when we get there)

- Material: **PETG**. Tougher than PLA, better than ABS for a hand-held
  object that will live in a pocket.
- Layer height: 0.2 mm.
- Walls: 3 perimeters, 25 % infill (grid).
- Orientation: print both shells with the LCD/floor face down. No
  supports needed if the case stays this rectilinear.
- M2.5 brass heat-set inserts go in the standoffs after printing.
