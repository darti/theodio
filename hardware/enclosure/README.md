# Enclosure

Parametric 3D-printable case for the theodio podcast reader. Written
with [build123d](https://build123d.readthedocs.io/) — Python on top of
the OpenCascade kernel, so the geometry is real solids (proper fillets,
chamfers, STEP export) and all dimensions live as named constants at the
top of `enclosure.py`.

## Status: v0 — envelope study

First pass from **datasheets only**. The boards haven't been breadboarded
yet, so several positions are estimates. Treat the exported STLs as
visualisations, not print-ready files. Anything tagged `TODO` inside
`enclosure.py` is a measurement to take from the actual hardware once it
arrives.

Most likely to shift after the first prototype:

- **Whisplay HAT height** above the GPIO header (`HAT_COMPONENTS_H`) —
  LCD bezel and connector heights are estimates.
- **LCD aperture position** on the Whisplay PCB (`LCD_OFF_X`, `LCD_OFF_Y`)
  — the panel may not be centred.
- **Headphone jack location** — the spec doesn't say whether the Whisplay
  exposes a panel-mount jack or solder pads needing a flying lead.
- **Encoder column position** (`ENC_COL_X/Y/Z`) — currently placed
  beside the Pi+HAT stack; may need to move once we see the real LCD
  aperture.
- **Pi standoff height** (`PI_RISER`) — needs enough clearance for the
  Pi's USB and HDMI connectors on the underside.

## Layout

```
            top shell
   +------------------------+
   |   [   LCD   ] [ enc ]  |
   |     Whisplay HAT       |
   |  ----- GPIO header --- |
   +------------------------+   <-- split plane (SPLIT_Z)
   |   Pi Zero 2 W on standoffs
   |   ---- PI_RISER ----
   |   LiPo 4000 mAh ([pb])
   +------------------------+
            bottom shell
```

External envelope at v0 parameters: roughly **75 × 65 × 42 mm**. Bigger
than the 75 × 40 × 25 mm placeholder originally in `../README.md`
because the LiPo's true ~60 × 70 × 8 mm footprint dominates.

## Building

```bash
pip install -r requirements.txt
python enclosure.py                     # writes top.stl + bottom.stl
python enclosure.py --part assembly     # writes assembly.step
python enclosure.py --part top --out /tmp/print
```

Outputs are gitignored — only `enclosure.py` and this README are tracked.

For interactive viewing during design, import the module and call
`show()` from your build123d viewer of choice (e.g. `ocp_vscode`):

```python
from enclosure import full_shell, assembly, top_shell, bottom_shell
from ocp_vscode import show
show(assembly())
```

## Printing notes (when we get there)

- Material: **PETG**. Tougher than PLA, better than ABS for a hand-held
  object that lives in a pocket.
- Layer height: 0.2 mm.
- Walls: 3 perimeters, 25 % infill (grid).
- Orientation: print both shells with the LCD/floor face down. No
  supports needed if the case stays this rectilinear.
- M2.5 brass heat-set inserts press into the standoff pockets after
  printing (`PI_HOLE_D` is sized for the insert outer diameter, not the
  screw).
