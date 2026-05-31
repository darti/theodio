// theodio — portable podcast reader enclosure
//
// Parametric two-shell case for Pi Zero 2 W + Whisplay HAT + 4000 mAh LiPo.
// All dimensions in mm.
//
// First-pass design from datasheets only — many positions are estimates
// until the breadboard prototype confirms them. Look for `TODO` comments.
//
// Render:
//   openscad -o assembly.stl -D 'part="assembly"' enclosure.scad
//   openscad -o top.stl      -D 'part="top"'      enclosure.scad
//   openscad -o bottom.stl   -D 'part="bottom"'   enclosure.scad
//
// Open in the GUI with the default (`assembly`) to visualise component fit
// with the shell rendered transparent.

part = "assembly";  // "top" | "bottom" | "both" | "assembly"
$fn = 48;

// ============================================================
// Component dimensions
// ============================================================

// --- Raspberry Pi Zero 2 W (datasheet) ---
pi_w        = 65;
pi_d        = 30;
pi_pcb_h    = 1.4;
pi_hole_d   = 2.75;
pi_hole_pitch_w = 58;     // 3.5 mm in from each long edge
pi_hole_pitch_d = 23;     // 3.5 mm in from each short edge

// --- PiSugar Whisplay HAT ---
// Same 65×30 PCB footprint, stacks on the 40-pin header.
hat_pcb_h         = 1.6;
hat_components_h  = 4.5;    // TODO measure: LCD bezel + connectors
gpio_header_h     = 8.5;    // stacking header
// LCD visible aperture (1.69" IPS, ~30×37 mm).
// TODO confirm centre offset on the PCB from the Whisplay schematic.
lcd_w        = 30;
lcd_d        = 37;
lcd_off_x    = 0;           // shift from HAT centre, +x toward microSD side
lcd_off_y    = 0;

// --- 4000 mAh LiPo cell ---
lipo_w = 70;
lipo_d = 60;
lipo_h = 8;

// --- Adafruit PowerBoost 1000C ---
pb_w = 36.7;
pb_d = 22.6;
pb_h = 6.4;

// --- EC11 rotary encoder (typical alps-clone) ---
enc_body_w   = 12.5;
enc_body_d   = 13.5;
enc_body_h   = 7.0;
enc_thread_d = 7.0;         // panel-mount thread
enc_thread_h = 7.0;
enc_shaft_d  = 6.0;
enc_shaft_h  = 13.0;

// --- Misc ---
tact_d       = 6.5;         // power tactile switch panel diameter
phone_jack_d = 6.5;         // 3.5 mm jack panel hole
microsd_w    = 12.5;
microsd_h    = 2.5;

// ============================================================
// Case parameters
// ============================================================

wall       = 2.0;
tol        = 0.3;           // print/fit clearance
foam_pad   = 1.0;           // soft pad under the LiPo
pi_riser   = 4.0;           // standoff between LiPo top and Pi PCB bottom

// Internal cavity origin = inside bottom-back-left corner of the case.
// All component positions below are inside this cavity frame.
cavity_w = lipo_w + 4;                     // ~74
cavity_d = lipo_d + 4;                     // ~64
inner_stack_h = foam_pad + lipo_h + pi_riser
              + pi_pcb_h + gpio_header_h
              + hat_pcb_h + hat_components_h + 2;
cavity_h = inner_stack_h;                  // ~38
echo("Internal cavity:", cavity_w, cavity_d, cavity_h);

// Z layout (heights above the cavity floor)
z_lipo  = foam_pad;
z_pi    = z_lipo + lipo_h + pi_riser;
z_hat   = z_pi + pi_pcb_h + gpio_header_h;
z_lcd_top = z_hat + hat_pcb_h + hat_components_h;

// Pi XY position inside the cavity (centred)
pi_x = (cavity_w - pi_w) / 2;
pi_y = (cavity_d - pi_d) / 2;

// LiPo centred on the floor
lipo_x = (cavity_w - lipo_w) / 2;
lipo_y = (cavity_d - lipo_d) / 2;

// PowerBoost sits flat next to the LiPo, against the back wall
pb_x = 2;
pb_y = cavity_d - pb_d - 1;

// Encoder column: between the Pi+HAT stack and the case's short edge.
// TODO confirm there's actually room here once the LCD aperture is set.
enc_col_x = pi_x + pi_w + 3;
enc_col_y = (cavity_d - enc_body_d) / 2;
enc_col_z = z_hat - enc_body_h;            // hangs from the top shell

// Split plane between top and bottom shells.
// Bottom holds the LiPo, PowerBoost, and Pi. Top holds the HAT, LCD, and
// encoder. The split runs just above the Pi PCB so the GPIO header
// remains accessible from the top shell.
split_z = z_pi + pi_pcb_h + 1;

// ============================================================
// Component proxies (for the assembly view)
// ============================================================

module pi_zero() {
    color("MediumSeaGreen") cube([pi_w, pi_d, pi_pcb_h]);
}

module whisplay_hat() {
    color("Black") cube([pi_w, pi_d, hat_pcb_h]);
    translate([(pi_w - lcd_w)/2 + lcd_off_x,
               (pi_d - lcd_d)/2 + lcd_off_y,
               hat_pcb_h])
        color("White") cube([lcd_w, min(lcd_d, pi_d - 1), hat_components_h]);
}

module lipo() { color("Silver") cube([lipo_w, lipo_d, lipo_h]); }

module powerboost() { color("Magenta") cube([pb_w, pb_d, pb_h]); }

module encoder() {
    color("DimGray") {
        cube([enc_body_w, enc_body_d, enc_body_h]);
        translate([enc_body_w/2, enc_body_d/2, enc_body_h]) {
            cylinder(h=enc_thread_h, d=enc_thread_d);
            translate([0, 0, enc_thread_h])
                cylinder(h=enc_shaft_h, d=enc_shaft_d);
        }
    }
}

// ============================================================
// Case construction
// ============================================================

module case_outer() {
    translate([-wall, -wall, -wall])
        cube([cavity_w + 2*wall, cavity_d + 2*wall, cavity_h + 2*wall]);
}

module case_cavity() {
    cube([cavity_w, cavity_d, cavity_h]);
}

module pi_standoffs() {
    sx0 = pi_x + (pi_w - pi_hole_pitch_w)/2;
    sy0 = pi_y + (pi_d - pi_hole_pitch_d)/2;
    for (x = [sx0, sx0 + pi_hole_pitch_w])
        for (y = [sy0, sy0 + pi_hole_pitch_d])
            translate([x, y, 0])
                difference() {
                    cylinder(h=z_pi, d=5);
                    translate([0, 0, z_pi - 4.5])
                        cylinder(h=4.6, d=pi_hole_d);
                }
}

// --- Panel cutouts ---

module lcd_window() {
    // Through the top wall, above the HAT's LCD bezel.
    translate([pi_x + (pi_w - lcd_w)/2 + lcd_off_x,
               pi_y + (pi_d - lcd_d)/2 + lcd_off_y,
               cavity_h - 0.1])
        cube([lcd_w, min(lcd_d, pi_d - 1), wall + 0.2]);
}

module encoder_hole() {
    // Encoder thread pokes through the top, knob sits above the case.
    translate([enc_col_x + enc_body_w/2,
               enc_col_y + enc_body_d/2,
               cavity_h - 0.1])
        cylinder(h=wall + 0.2, d=enc_thread_d + tol);
}

module power_switch_hole() {
    // Right short edge, at mid-height of the HAT stack.
    translate([cavity_w + 0.1, 6, z_pi + 2])
        rotate([0, -90, 0])
        cylinder(h=wall + 0.2, d=tact_d + tol);
}

module headphone_jack_hole() {
    // Front long edge, where the Whisplay's audio output sits.
    // TODO: confirm position once we know whether the HAT exposes a
    // panel-mount jack or pads + flying-lead jack.
    translate([10, -0.1, z_hat + 2])
        rotate([-90, 0, 0])
        cylinder(h=wall + 0.2, d=phone_jack_d + tol);
}

module microsd_slot() {
    // Left short edge, aligned with the Pi's microSD card.
    translate([-wall - 0.1, pi_y + 2.5, z_pi - microsd_h/2])
        cube([wall + 0.2, microsd_w, microsd_h + 2*tol]);
}

// --- Shells ---

module full_shell() {
    difference() {
        case_outer();
        case_cavity();
        lcd_window();
        encoder_hole();
        power_switch_hole();
        headphone_jack_hole();
        microsd_slot();
    }
}

module bottom_shell() {
    difference() {
        full_shell();
        translate([-wall - 1, -wall - 1, split_z])
            cube([cavity_w + 2*wall + 2,
                  cavity_d + 2*wall + 2,
                  cavity_h + 2*wall + 2]);
    }
    pi_standoffs();
}

module top_shell() {
    difference() {
        full_shell();
        translate([-wall - 1, -wall - 1, -wall - 1])
            cube([cavity_w + 2*wall + 2,
                  cavity_d + 2*wall + 2,
                  split_z + wall + 1]);
    }
}

module assembly() {
    %full_shell();   // transparent shell
    translate([lipo_x, lipo_y, z_lipo]) lipo();
    translate([pb_x,   pb_y,   z_lipo]) powerboost();
    translate([pi_x,   pi_y,   z_pi])   pi_zero();
    translate([pi_x,   pi_y,   z_hat])  whisplay_hat();
    translate([enc_col_x, enc_col_y, enc_col_z]) encoder();
}

// ============================================================
// Render dispatch
// ============================================================
if      (part == "assembly") assembly();
else if (part == "top")      top_shell();
else if (part == "bottom")   bottom_shell();
else if (part == "both") {
    bottom_shell();
    translate([cavity_w + 2*wall + 20, 0, 0]) top_shell();
}
