// =====================================================================
//  Caja de intemperie BricoHams SDR · BricoHams SDR
//  Para mástil Televés. PETG (estructura) + TPU 95A (juntas), impresa en
//  una Anycubic Kobra S1 (volumen 250 × 250 × 250 mm).
//
//  Qué aloja:
//   - Zona de electrónica: Raspberry Pi 5 + HAT HackerGadgets, Mini RTL-SDR,
//     RTL-SDR Blog V3, FlightStick RadarBox, diplexor HF/VHF y cámara WPI408
//     (tras una ventana de policarbonato en la tapa).
//   - Compartimento de potencia aparte (tabique + tapa interior): cargador
//     USB multitoma de 45 W y regleta/hub USB alimentado. Los 230 V entran
//     solo aquí, por su prensaestopas PG9.
//   - Los dos LilyGO T3 V1.6.1 van sobre la tapa interior de potencia.
//   - 9 conectores SMA pasamuros, prensaestopas y rejillas de entrada en la
//     cara inferior (no entra el agua). Rejillas de salida arriba, bajo un
//     tejadillo inclinado.
//   - Garita de platos para el BME280, con su propio brazo al mástil.
//
//  Coordenadas con la caja montada: X = ancho, Y = alto (0 = abajo),
//  Z = fondo (0 = espalda contra el mástil, D = borde donde cierra la tapa).
//
//  Exportar una pieza:
//      openscad -D 'PART="cuerpo"' -o cuerpo.stl caja_bricohams.scad
//  Las piezas salen ya orientadas para imprimir sin soportes.
//  (tools/caja.sh exporta todas y genera las vistas PNG)
// =====================================================================

PART = "montaje";   // montaje | interior | despiece | cuerpo | tapa | tapa_potencia | placa_electronica |
                    // placa_potencia | tejadillo | visera | soporte_camara | soporte_mastil |
                    // junta_tapa | junta_ventana | separador_ir | pasamuros_usb |
                    // garita_base | garita_plato | garita_tapa
$fn = 48;
E = 0.01;
FONT = "DejaVu Sans:style=Bold";

// ---------------------------------------------------------------------
//  Medidas generales (mm)
// ---------------------------------------------------------------------
W = 224;            // ancho exterior del cuerpo (X)
H = 232;            // alto exterior (Y)
D = 90;             // fondo exterior del cuerpo (Z)
T = 3.2;            // paredes y fondo (8 líneas de 0,4)
R = 6;              // radio de las esquinas
PWR_W = 70;         // ancho interior del compartimento de potencia
TP = 3.2;           // espesor del tabique
XP = T + PWR_W;     // cara izquierda del tabique  (73,2)
XE = XP + TP;       // inicio de la zona de electrónica (76,4)

// cierre estanco: el borde de la pared entra en una ranura de la tapa con junta TPU
GAP_LID = 3;        // la tapa apoya en las orejetas 3 mm por encima del borde
LID_T = 4;          // espesor de la tapa
RIB_H = 6;          // altura de los nervios que forman la ranura
GROOVE_W = 4.2;     // ancho de la ranura
GASKET_W = 4.4;     // junta TPU de 4,4 × 4: entra a presión en la ranura y se comprime 1 mm (25 %)
GASKET_H = 4.0;
EAR_L = 9;          // orejetas de cierre, fuera de la junta
EAR_Y = 18;
EAR_Z = 10;
EARS_Y = [22, 84, 148, 210];

// tornillería e insertos roscados de latón (se ponen con el soldador)
HOLE_M3 = 3.4;  INS_M3 = 4.0;  INS_M3_L = 6;      // insertos M3 × 5,7 (tipo ruthex)
HOLE_M4 = 4.5;  INS_M4 = 5.6;  INS_M4_L = 8.5;    // insertos M4 × 8,1

// placas de montaje, atornilladas a pilares del fondo
STANDOFF = 10;  PLATE_T = 3;
PE = [XE + 3.2, 6, 138, 210];        // placa de electrónica: x, y, ancho, alto
PP = [T + 6, 6, 58, 210];            // placa de potencia
PE_BOSS = [[30, 6], [110, 6], [30, 204], [110, 204]];      // coordenadas sobre la placa
PP_BOSS = [[8, 6], [50, 6], [8, 204], [50, 204]];

// tapa interior del compartimento de potencia
CP_Z = D - 34;                       // cara trasera de la tapa interior (z = 56)
CP_T = 3;
CP_BOSS_Y = [30, 200];
CP_BOSS_W = 8;

// paso de cables USB en el tabique (por debajo de la tapa interior) y muesca
// superior para los coaxiales de los LilyGO (por encima)
GROM = [18, 34];  GROM_Y = 176;  GROM_Z = 16;
NOTCH_Y = 140;  NOTCH_W = 18;  NOTCH_Z = 64;

// soporte de mástil: dos sillas en V con abrazadera metálica (Televés Ø25–50)
MAST_D = 40;
MAST_Y = [45, 187];                  // centro de cada silla
MAST_SCREW_DX = 30;  MAST_SCREW_DY = 19;
BRK_Z = 26;                          // grosor de la silla
V_W = MAST_D * 0.9;  V_D = V_W / 2;  // V a 90°
MAST_OFF = MAST_D / 2 * sqrt(2) - V_D;   // eje del mástil respecto a la cara de la silla

// tejadillo
ROOF_PILLARS = [[12, 20], [212, 20], [12, 70], [212, 70]];   // (x, z) en la caja
ROOF_GAP = 10;      // hueco delante (aire de salida)
ROOF_A = 5;         // inclinación hacia delante (º)
ROOF_W = W + 16;
ROOF_L = D + GAP_LID + LID_T + 16;

// cara inferior de la zona de electrónica: SMA hembra pasamuros
SMA_HOLE = 6.6;
SMA_LABELS = ["SAT", "HAM", "VHF", "HF", "ADSB", "868", "GPS", "M433", "IG433"];
SMA_PITCH = 15;
SMA_Z = 26;
SMA_X0 = XE + (W - T - XE) / 2 - (len(SMA_LABELS) - 1) * SMA_PITCH / 2;
GLAND_PG7 = 12.7;    // cable del BME280
GLAND_M20 = 20.4;    // Ethernet (prensaestopas M20 de junta partida)
GLAND_PG9 = 15.5;    // 230 V (solo en el compartimento de potencia)

// cámara Whadda/Velleman WPI408 (OV5647 + 2 LED IR)
CAM_C = [160, 196];                  // centro de la ventana (x, y)
CAM_WIN = [76, 26];                  // hueco libre de la ventana
CAM_PC = [86.5, 36.5];               // cajeado: policarbonato de 86 × 36 × 2 mm + junta de 1,5 mm
CAM_FRAME = 8;                       // marco interior alrededor del cajeado
CAM_FRAME_H = 5;                     // lo que sobresale el marco por dentro
CAM_MOD = [76, 28, 25];              // módulo con las dos placas IR
CAM_SX = CAM_PC[0] / 2 + CAM_FRAME / 2;  // x de los insertos del marco
VIS_Y = -8;                          // insertos de la visera (desde fuera)
BRK_Y = 8;                           // insertos del soporte de la cámara (desde dentro)

// componentes (vista de montaje y posición de las bridas)
PI5 = [85, 56];  PI5_HOLES = [58, 49];  PI5_POS = [42, 141];   // sobre la placa de electrónica
DONGLES = [["Mini RTL-SDR", 26, 54, 3], ["RTL-SDR V3", 26, 85, 33], ["FlightStick", 26, 85, 63]];
DONGLE_Y = 16;
DIPLEXER = [26, 50, 93, 16];         // ancho, alto, x, y sobre la placa
CHARGER = [65, 95, 30];              // cargador USB 45 W (referencia; se sujeta con bridas)
HUB = [40, 100, 22];                 // regleta / hub USB alimentado
LILYGO = [27, 65];                   // LilyGO T3 V1.6.1

VENT_W = 3;  VENT_L = 22;

// ---------------------------------------------------------------------
//  Utilidades
// ---------------------------------------------------------------------
module rrect(w, h, r) { translate([r, r]) offset(r) square([w - 2 * r, h - 2 * r]); }
module outline() { rrect(W, H, R); }

// agujero en gota con eje Y; la punta va hacia +Z (arriba durante la impresión)
module teardrop_y(d, l) {
    rotate([-90, 0, 0]) linear_extrude(l) union() {
        circle(d = d);
        rotate(225) square(d / 2);
    }
}

// texto grabado en la cara inferior (y = 0), legible desde delante y abajo
module label_bottom(s, x, z, size) {
    translate([x, 0.6, z]) rotate([90, 0, 0]) linear_extrude(1) rotate(180)
        text(s, size = size, font = FONT, halign = "center", valign = "center");
}

module zip_slots(x, y, w, h) {   // ranuras de brida a ambos lados de una pieza
    for (yy = [y + h * 0.25, y + h * 0.75], xx = [x - 4, x + w + 1.2])
        translate([xx, yy - 1.5, -1]) cube([2.8, 3, 20]);
}

// ---------------------------------------------------------------------
//  CUERPO (se imprime con la espalda sobre la cama)
// ---------------------------------------------------------------------
module ears(xs) {   // xs = -1 izquierda, +1 derecha
    x0 = xs < 0 ? -EAR_L : W;
    zt = D + GAP_LID;
    for (y = EARS_Y) difference() {
        hull() {
            translate([x0, y - EAR_Y / 2, zt - EAR_Z]) cube([EAR_L, EAR_Y, EAR_Z]);
            // refuerzo a 45°: imprime sin soporte
            translate([xs < 0 ? -0.1 : W - 0.1, y - EAR_Y / 2, zt - EAR_Z - EAR_L]) cube([0.2, EAR_Y, 0.2]);
        }
        translate([xs < 0 ? -EAR_L / 2 - 0.5 : W + EAR_L / 2 + 0.5, y, zt - INS_M4_L]) cylinder(d = INS_M4, h = INS_M4_L + 1);
    }
}

module column(x, y, d, z0, z1) { translate([x, y, z0]) cylinder(d = d, h = z1 - z0); }

module cuerpo() {
    difference() {
        union() {
            difference() {
                linear_extrude(D) outline();
                translate([0, 0, T]) linear_extrude(D) offset(-T) outline();
            }
            ears(-1); ears(1);
            // tabique entre potencia y electrónica
            translate([XP, T - E, T - E]) cube([TP, H - 2 * T + 2 * E, D - T]);
            // pilares de las placas (insertos M3)
            for (b = PE_BOSS) column(PE[0] + b[0], PE[1] + b[1], 9, T - E, T + STANDOFF);
            for (b = PP_BOSS) column(PP[0] + b[0], PP[1] + b[1], 9, T - E, T + STANDOFF);
            // pilares del soporte de mástil (insertos M4 desde fuera)
            for (yc = MAST_Y, sx = [-1, 1], sy = [-1, 1])
                column(W / 2 + sx * MAST_SCREW_DX, yc + sy * MAST_SCREW_DY, 12, T - E, T + 8);
            // pilares de la tapa interior de potencia (pegados a pared y tabique)
            for (y = CP_BOSS_Y) {
                translate([T - E, y - 5, T - E]) cube([CP_BOSS_W, 10, CP_Z - T]);
                translate([XP - CP_BOSS_W + E, y - 5, T - E]) cube([CP_BOSS_W, 10, CP_Z - T]);
            }
            // columnas bajo el techo para los insertos del tejadillo
            for (p = ROOF_PILLARS) translate([p[0] - 5, H - T - 9, T - E]) cube([10, 9 + E, D - T - 8]);
            // marco del paso de cables del tabique
            translate([XP - 1.5, GROM_Y - 3, GROM_Z - 3]) cube([TP + 3, GROM[0] + 6, GROM[1] + 6]);
        }
        // --- insertos ---
        for (b = PE_BOSS) translate([PE[0] + b[0], PE[1] + b[1], T + STANDOFF - INS_M3_L]) cylinder(d = INS_M3, h = INS_M3_L + 1);
        for (b = PP_BOSS) translate([PP[0] + b[0], PP[1] + b[1], T + STANDOFF - INS_M3_L]) cylinder(d = INS_M3, h = INS_M3_L + 1);
        for (yc = MAST_Y, sx = [-1, 1], sy = [-1, 1])
            translate([W / 2 + sx * MAST_SCREW_DX, yc + sy * MAST_SCREW_DY, -1]) cylinder(d = INS_M4, h = INS_M4_L + 1);
        for (y = CP_BOSS_Y) {
            translate([T + CP_BOSS_W / 2, y, CP_Z - INS_M3_L]) cylinder(d = INS_M3, h = INS_M3_L + 1);
            translate([XP - CP_BOSS_W / 2, y, CP_Z - INS_M3_L]) cylinder(d = INS_M3, h = INS_M3_L + 1);
        }
        for (p = ROOF_PILLARS) translate([p[0], H + 1, p[1]]) rotate([90, 0, 0]) cylinder(d = INS_M4, h = INS_M4_L + 1);

        // --- cara inferior: SMA, prensaestopas y rejillas de entrada ---
        for (i = [0 : len(SMA_LABELS) - 1]) {
            translate([SMA_X0 + i * SMA_PITCH, -1, SMA_Z]) teardrop_y(SMA_HOLE, T + 2);
            label_bottom(SMA_LABELS[i], SMA_X0 + i * SMA_PITCH, SMA_Z + 9.5, 2.9);
        }
        translate([XE + 24, -1, 64]) teardrop_y(GLAND_PG7, T + 2);
        label_bottom("WX", XE + 24, 78, 3.5);
        translate([XE + 56, -1, 64]) teardrop_y(GLAND_M20, T + 2);
        label_bottom("LAN", XE + 56, 81, 3.5);
        for (x = [XE + 80 : 7 : W - T - 12]) translate([x, -1, 52]) cube([VENT_W, T + 2, VENT_L]);
        translate([T + PWR_W / 2, -1, 36]) teardrop_y(GLAND_PG9, T + 2);
        label_bottom("230 V", T + PWR_W / 2, 52, 4.5);
        for (x = [T + 8, T + PWR_W - 12]) translate([x, -1, 30]) cube([VENT_W, T + 2, VENT_L]);
        // --- techo: rejillas de salida (quedan bajo el tejadillo) ---
        for (x = concat([for (x = [T + 18 : 7 : XP - 8]) x], [for (x = [XE + 10 : 7 : W - T - 22]) x]))
            translate([x, H - T - 1, 30]) cube([VENT_W, T + 2, 34]);
        // --- tabique: paso de cables USB (con pasamuros de TPU) y muesca de los coaxiales ---
        translate([XP - 2, GROM_Y, GROM_Z]) cube([TP + 4, GROM[0], GROM[1]]);
        translate([XP - 1, NOTCH_Y, NOTCH_Z]) cube([TP + 2, NOTCH_W, D]);
        // --- rótulo en el lateral derecho ---
        translate([W - 0.6, H / 2, D / 2]) rotate([90, 0, 90]) linear_extrude(1) rotate(-90)
            text("BricoHams · N0CALL", size = 8, font = FONT, halign = "center", valign = "center");
    }
}

// ---------------------------------------------------------------------
//  TAPA (modelada cerrada; para imprimir se gira con la cara exterior abajo)
// ---------------------------------------------------------------------
LID_Z0 = D + GAP_LID;                // cara interior de la tapa
module lid_plate_2d() {
    union() {
        offset(2.1) outline();
        for (y = EARS_Y, xs = [-1, 1])
            translate([xs < 0 ? -EAR_L - 0.5 : W, y - EAR_Y / 2]) square([EAR_L + 0.5, EAR_Y]);
    }
}
module tapa() {
    fx = CAM_PC[0] + 2 * CAM_FRAME;  fy = CAM_PC[1] + 2 * CAM_FRAME;
    difference() {
        union() {
            translate([0, 0, LID_Z0]) linear_extrude(LID_T) lid_plate_2d();
            // nervios a ambos lados de la ranura (el borde de la pared entra en ella)
            translate([0, 0, LID_Z0 - RIB_H]) linear_extrude(RIB_H + E) difference() {
                offset(2.1) outline();
                offset(-(T / 2 + GROOVE_W / 2 + 1.6)) outline();
            }
            // marco interior de la ventana de la cámara
            translate([CAM_C[0] - fx / 2, CAM_C[1] - fy / 2, LID_Z0 - CAM_FRAME_H]) cube([fx, fy, CAM_FRAME_H + E]);
        }
        // ranura de la junta, centrada sobre la pared
        translate([0, 0, LID_Z0 - RIB_H - 1]) linear_extrude(RIB_H + 1) difference() {
            offset(-(T / 2 - GROOVE_W / 2)) outline();
            offset(-(T / 2 + GROOVE_W / 2)) outline();
        }
        // paso de las orejetas del cuerpo por el faldón
        for (y = EARS_Y, xs = [-1, 1])
            translate([xs < 0 ? -EAR_L - 3 : W - 0.5, y - EAR_Y / 2 - 0.5, LID_Z0 - RIB_H - 1]) cube([EAR_L + 3.5, EAR_Y + 1, RIB_H + 1]);
        for (y = EARS_Y, xs = [-1, 1]) translate([xs < 0 ? -EAR_L / 2 - 0.5 : W + EAR_L / 2 + 0.5, y, LID_Z0 - 1]) cylinder(d = HOLE_M4, h = LID_T + 2);
        // ventana y cajeado (policarbonato + junta); queda un labio de 5,4 mm
        translate([CAM_C[0] - CAM_WIN[0] / 2, CAM_C[1] - CAM_WIN[1] / 2, LID_Z0 - 10]) cube([CAM_WIN[0], CAM_WIN[1], 20]);
        translate([CAM_C[0] - CAM_PC[0] / 2, CAM_C[1] - CAM_PC[1] / 2, LID_Z0 - CAM_FRAME_H - 1]) cube([CAM_PC[0], CAM_PC[1], CAM_FRAME_H + 1 - 1.4]);
        // insertos M3: visera (desde fuera) y soporte de la cámara (desde dentro)
        for (s = [-1, 1]) {
            translate([CAM_C[0] + s * CAM_SX, CAM_C[1] + VIS_Y, LID_Z0 + LID_T - INS_M3_L]) cylinder(d = INS_M3, h = INS_M3_L + 1);
            translate([CAM_C[0] + s * CAM_SX, CAM_C[1] + BRK_Y, LID_Z0 - CAM_FRAME_H - 1]) cylinder(d = INS_M3, h = INS_M3_L + 1);
        }
        // rótulos en la cara exterior
        translate([W / 2, 52, LID_Z0 + LID_T - 0.6]) linear_extrude(1)
            text("BricoHams SDR", size = 14, font = FONT, halign = "center", valign = "center");
        translate([W / 2, 30, LID_Z0 + LID_T - 0.6]) linear_extrude(1)
            text("BricoHams SDR", size = 6.5, font = FONT, halign = "center", valign = "center");
        translate([T + PWR_W / 2, 140, LID_Z0 + LID_T - 0.6]) linear_extrude(1) rotate(90)
            text("230 V", size = 10, font = FONT, halign = "center", valign = "center");
    }
}

// ---------------------------------------------------------------------
//  PLACAS DE MONTAJE
// ---------------------------------------------------------------------
module placa_electronica() {
    difference() {
        union() {
            cube([PE[2], PE[3], PLATE_T]);
            // separadores de la Raspberry Pi 5 (tornillo M2.5 autorroscante)
            for (i = [0, 1], j = [0, 1])
                translate([PI5_POS[0] + 3.5 + i * PI5_HOLES[0], PI5_POS[1] + 3.5 + j * PI5_HOLES[1], 0]) cylinder(d = 6.5, h = PLATE_T + 6);
            // guías de los dongles
            for (d = DONGLES) for (s = [0, 1])
                translate([d[3] - 2 + s * (d[1] + 2.6), DONGLE_Y, 0]) cube([2, d[2], PLATE_T + 3]);
        }
        for (b = PE_BOSS) translate([b[0], b[1], -1]) cylinder(d = HOLE_M3, h = 10);
        for (i = [0, 1], j = [0, 1])
            translate([PI5_POS[0] + 3.5 + i * PI5_HOLES[0], PI5_POS[1] + 3.5 + j * PI5_HOLES[1], -1]) cylinder(d = 2.3, h = 20);
        for (d = DONGLES) zip_slots(d[3] - 2, DONGLE_Y, d[1] + 4.6, d[2]);
        zip_slots(DIPLEXER[2], DIPLEXER[3], DIPLEXER[0], DIPLEXER[1]);
        for (x = [10 : 16 : PE[2] - 10]) translate([x, 118, -1]) cube([3, 2.8, 10]);   // bridas de cables
        translate([PI5_POS[0] + 15, PI5_POS[1] + 12, -1]) cube([PI5[0] - 30, PI5[1] - 24, 10]);   // aire bajo la Pi
        translate([6, 1.5, PLATE_T - 0.5]) linear_extrude(1) text("ELECTRONICA", size = 3.5, font = FONT);
    }
}

module placa_potencia() {
    difference() {
        cube([PP[2], PP[3], PLATE_T]);
        for (b = PP_BOSS) translate([b[0], b[1], -1]) cylinder(d = HOLE_M3, h = 10);
        // rejilla de ranuras para bridas: vale para cualquier cargador y hub
        for (y = [20 : 15 : PP[3] - 15], x = [4, PP[2] - 7]) translate([x, y, -1]) cube([2.8, 3, 10]);
        for (y = [30 : 30 : PP[3] - 30]) translate([PP[2] / 2 - 1.5, y, -1]) cube([3, 2.8, 10]);
        translate([16, 1.5, PLATE_T - 0.5]) linear_extrude(1) text("POTENCIA", size = 3.5, font = FONT);
    }
}

// ---------------------------------------------------------------------
//  TAPA INTERIOR DE POTENCIA (con los dos LilyGO en su cara delantera)
// ---------------------------------------------------------------------
CPW = PWR_W - 1;
CPH = H - 2 * T - 1;
LILY_Y = 118;                        // y de las cunas sobre la tapa interior
module tapa_potencia() {
    difference() {
        union() {
            cube([CPW, CPH, CP_T]);
            // cunas de los LilyGO (placa de 27 × 65 sobre resaltes de 4 mm)
            for (i = [0, 1]) translate([5 + i * (LILYGO[0] + 6), LILY_Y, 0]) difference() {
                cube([LILYGO[0] + 2.4, LILYGO[1] + 2.4, CP_T + 4]);
                translate([1.2, 1.2, CP_T + 2]) cube([LILYGO[0], LILYGO[1], 10]);
                translate([4, 6, CP_T - 1]) cube([LILYGO[0] - 5.6, LILYGO[1] - 9.6, 10]);
            }
        }
        // tornillos a los pilares
        for (y = CP_BOSS_Y) for (x = [CP_BOSS_W / 2 - 0.5, CPW - CP_BOSS_W / 2 + 0.5]) translate([x, y - T - 0.5, -1]) cylinder(d = HOLE_M3, h = 10);
        // bridas de los LilyGO
        for (i = [0, 1], yy = [LILY_Y + 15, LILY_Y + 50]) {
            translate([2 + i * (LILYGO[0] + 6) - 0.5, yy, -1]) cube([2.8, 3, 20]);
            translate([5 + i * (LILYGO[0] + 6) + LILYGO[0] + 3.2, yy, -1]) cube([2.8, 3, 20]);
        }
        // paso de los cables USB de los LilyGO hacia el hub (abajo)
        translate([CPW / 2 - 10, CPH - 9, -1]) cube([20, 10, 10]);
        // hueco para la columna del tejadillo (esquina superior izquierda)
        translate([-1, CPH - 13, -1]) cube([15, 14, 10]);
        // aviso grabado
        translate([CPW / 2, 58, CP_T - 0.6]) linear_extrude(1) rotate(90)
            text("230 V - NO ABRIR CON TENSION", size = 4.6, font = FONT, halign = "center", valign = "center");
    }
}

// ---------------------------------------------------------------------
//  TEJADILLO (protege las rejillas de salida; cae hacia delante)
//  Modelado en posición: x = ancho, y = fondo de la caja (+2 mm), z = altura sobre el techo
// ---------------------------------------------------------------------
function roof_z(y) = ROOF_GAP + (ROOF_L - y) * tan(ROOF_A);    // cara inferior de la placa
module tejadillo() {
    difference() {
        union() {
            translate([0, ROOF_L, ROOF_GAP]) rotate([-ROOF_A, 0, 0]) translate([0, -ROOF_L / cos(ROOF_A), 0])
                cube([ROOF_W, ROOF_L / cos(ROOF_A), 4]);
            // goterón delantero
            translate([0, ROOF_L - 2.5, ROOF_GAP - 6]) cube([ROOF_W, 2.5, 7]);
            // pilares
            for (p = ROOF_PILLARS) translate([ROOF_W - 8 - p[0], p[1] + 2, 0]) cylinder(d = 11, h = roof_z(p[1] + 2) + 1);
        }
        for (p = ROOF_PILLARS) translate([ROOF_W - 8 - p[0], p[1] + 2, -1]) cylinder(d = HOLE_M4, h = 60);
    }
}

// ---------------------------------------------------------------------
//  VISERA DE LA CÁMARA (x = ancho, y = alto, z = vuelo hacia fuera)
// ---------------------------------------------------------------------
VIS_W = 2 * CAM_SX + 14;  VIS_H = CAM_WIN[1] / 2 + 12;  VIS_V = 32;
module visera() {
    difference() {
        union() {
            translate([-VIS_W / 2, -VIS_H, 0]) cube([VIS_W, 2 * VIS_H, 3]);           // pletina
            translate([-VIS_W / 2, VIS_H - 3, 0]) cube([VIS_W, 3, VIS_V]);            // techo
            for (s = [-1, 1]) translate([s * (VIS_W / 2 - 1.5) - 1.5, 0, 0]) hull() {   // laterales
                translate([0, VIS_H - 3, 0]) cube([3, 3, VIS_V]);
                translate([0, -VIS_H, 0]) cube([3, 1, 3]);
            }
        }
        translate([-CAM_WIN[0] / 2 - 1, -CAM_WIN[1] / 2 - 1, -1]) cube([CAM_WIN[0] + 2, CAM_WIN[1] + 2, 10]);
        for (s = [-1, 1]) translate([s * CAM_SX, VIS_Y, -1]) cylinder(d = HOLE_M3, h = 10);
    }
}

// soporte de la cámara: pletina con dos patas que aprieta el módulo contra el policarbonato
module soporte_camara() {
    L = 2 * CAM_SX + 10;
    difference() {
        union() {
            translate([-L / 2, -CAM_MOD[1] / 2 - 2, 0]) cube([L, CAM_MOD[1] + 4, 3]);
            for (s = [-1, 1]) translate([s * CAM_SX, BRK_Y, 0]) cylinder(d = 8, h = 3 + CAM_MOD[2]);
            // topes que aprietan la parte trasera de las placas IR (con 1 mm de espuma)
            for (s = [-1, 1]) translate([s * 30 - 6, -8, 0]) cube([12, 16, 4]);
        }
        for (s = [-1, 1]) translate([s * CAM_SX, BRK_Y, -1]) cylinder(d = HOLE_M3, h = 40);
        translate([-12, -CAM_MOD[1] / 2 + 1, -1]) cube([24, CAM_MOD[1] - 2, 10]);   // paso del cable CSI
    }
}

// ---------------------------------------------------------------------
//  SOPORTE DE MÁSTIL (silla en V + abrazadera metálica de 12–14 mm)
//  x = ancho, y = alto, z = desde la espalda de la caja hacia el mástil
// ---------------------------------------------------------------------
module soporte_mastil() {
    bw = 2 * MAST_SCREW_DX + 20; bh = 2 * MAST_SCREW_DY + 12;
    difference() {
        translate([-bw / 2, -bh / 2, 0]) cube([bw, bh, BRK_Z]);
        translate([0, -bh / 2 - 1, BRK_Z + E]) rotate([90, 0, 0]) mirror([0, 0, 1]) linear_extrude(bh + 2)
            polygon([[-V_W / 2, 0], [V_W / 2, 0], [0, -V_D]]);
        translate([-bw / 2 - 1, -7.5, 4]) cube([bw + 2, 15, 4]);   // ranura de la abrazadera
        for (sx = [-1, 1], sy = [-1, 1]) {
            translate([sx * MAST_SCREW_DX, sy * MAST_SCREW_DY, -1]) cylinder(d = HOLE_M4, h = BRK_Z + 2);
            translate([sx * MAST_SCREW_DX, sy * MAST_SCREW_DY, 12]) cylinder(d = 8.5, h = BRK_Z);
        }
    }
}

// ---------------------------------------------------------------------
//  PIEZAS DE TPU
// ---------------------------------------------------------------------
module junta_tapa() {
    linear_extrude(GASKET_H) difference() {
        offset(-(T / 2 - GASKET_W / 2)) outline();
        offset(-(T / 2 + GASKET_W / 2)) outline();
    }
}
module junta_ventana() {
    linear_extrude(1.5) difference() {
        square([CAM_PC[0] - 0.5, CAM_PC[1] - 0.5], center = true);
        square([CAM_WIN[0], CAM_WIN[1]], center = true);
    }
}
module separador_ir() {   // aro alrededor del objetivo: la luz IR no rebota en el policarbonato
    difference() { cylinder(d = 19, h = 6); translate([0, 0, -1]) cylinder(d = 14.5, h = 8); }
}
module pasamuros_usb() {   // tapón partido para el paso de cables del tabique
    difference() {
        union() {
            translate([-(GROM[0] + 6) / 2, -(GROM[1] + 6) / 2, 0]) cube([GROM[0] + 6, GROM[1] + 6, 1.6]);
            translate([-(GROM[0] - 0.4) / 2, -(GROM[1] - 0.4) / 2, 0]) cube([GROM[0] - 0.4, GROM[1] - 0.4, 1.6 + TP + 3]);
        }
        translate([-0.4, -GROM[1], -1]) cube([0.8, 2 * GROM[1], 20]);   // corte para meter los cables
        for (y = [-13.5, -6.75, 0, 6.75, 13.5]) translate([0, y, -1]) cylinder(d = 5, h = 20);   // 5 cables
    }
}

// ---------------------------------------------------------------------
//  GARITA DEL BME280 (pantalla de radiación de platos, PETG blanco)
// ---------------------------------------------------------------------
G_D = 120; G_HOLE = 50; G_ROD_R = 52; G_STEP = 14;
module g_posts(h) { for (a = [0, 120, 240]) rotate(a) translate([G_ROD_R, 0, 0]) cylinder(d = 10, h = h); }
module g_rods()   { for (a = [0, 120, 240]) rotate(a) translate([G_ROD_R, 0, -1]) cylinder(d = 4.5, h = 60); }
module garita_plato() {   // base plana, cara superior en cono (escurre el agua)
    difference() {
        union() {
            rotate_extrude($fn = 96) polygon([[G_HOLE / 2, 0], [G_D / 2, 0], [G_D / 2, 1.6], [G_HOLE / 2, 6]]);
            g_posts(G_STEP);
        }
        g_rods();
    }
}
module garita_tapa() {
    difference() {
        rotate_extrude($fn = 96) polygon([[0, 0], [G_D / 2 + 4, 0], [G_D / 2 + 4, 2.4], [0, 14]]);
        g_rods();
    }
}
module garita_base() {   // plato inferior abierto + cuna del sensor + brazo al mástil
    arm = 110;
    difference() {
        union() {
            difference() { cylinder(d = G_D, h = 3, $fn = 96); translate([0, 0, -1]) cylinder(d = G_HOLE - 6, h = 5); }
            g_posts(G_STEP);
            translate([-G_HOLE / 2 + 2, -2.5, 0]) cube([G_HOLE - 4, 5, 3]);     // travesaño
            translate([-11, -9, 0]) cube([22, 18, 3]);                           // cuna del sensor GYBMEP
            translate([G_D / 2 - 6, -10, 0]) cube([arm, 20, 8]);                 // brazo
            translate([G_D / 2 + arm - 16, -20, 0]) cube([16, 40, 26]);          // silla del mástil
        }
        g_rods();
        translate([-8, -6.5, -1]) cube([16, 13, 10]);                            // aire bajo el sensor
        for (s = [-1, 1]) translate([s * 9, 6, -1]) cylinder(d = 2.2, h = 10);   // tornillos M2 del sensor
        translate([G_D / 2 + arm, -21, 13]) rotate([-90, 0, 0]) linear_extrude(42)
            polygon([[E, -12], [E, 12], [-9, 0]]);                               // V del mástil
        translate([G_D / 2 + arm - 13, -22, 4]) cube([4, 44, 18]);               // abrazadera
        translate([G_D / 2 + 4, -2, 4.5]) cube([arm - 24, 4, 10]);               // canal del cable
    }
}

// ---------------------------------------------------------------------
//  VISTA DE MONTAJE (componentes en semitransparente)
// ---------------------------------------------------------------------
module ghost(c) { color(c, 0.6) children(); }
module componentes() {
    pz = T + STANDOFF + PLATE_T;
    ghost("green")  translate([PE[0] + PI5_POS[0], PE[1] + PI5_POS[1], pz + 6]) cube([PI5[0], PI5[1], 18]);
    ghost("purple") translate([PE[0] + PI5_POS[0], PE[1] + PI5_POS[1], pz + 26]) cube([PI5[0], PI5[1], 12]);
    for (d = DONGLES) ghost("steelblue") translate([PE[0] + d[3], PE[1] + DONGLE_Y, pz]) cube([d[1], d[2], 13]);
    ghost("silver") translate([PE[0] + DIPLEXER[2], PE[1] + DIPLEXER[3], pz]) cube([DIPLEXER[0], DIPLEXER[1], 20]);
    ghost("white")   translate([T + 2.5, PP[1] + 4, pz]) cube(CHARGER);
    ghost("dimgray") translate([T + (PWR_W - HUB[0]) / 2, PP[1] + CHARGER[1] + 10, pz]) cube(HUB);
    for (i = [0, 1]) ghost("royalblue")
        translate([T + 0.5 + 5 + i * (LILYGO[0] + 6) + 1.2, T + 0.5 + LILY_Y + 1.2, CP_Z + CP_T + 2]) cube([LILYGO[0], LILYGO[1], 12]);
    ghost("black") translate([CAM_C[0] - CAM_MOD[0] / 2, CAM_C[1] - CAM_MOD[1] / 2, LID_Z0 - CAM_FRAME_H - CAM_MOD[2]]) cube(CAM_MOD);
    for (i = [0 : len(SMA_LABELS) - 1]) ghost("gold")
        translate([SMA_X0 + i * SMA_PITCH, -10, SMA_Z]) rotate([-90, 0, 0]) cylinder(d = 6.2, h = 24);
}

module montaje(ex = 0, abierta = false) {
    color("white") cuerpo();
    if (!abierta) {
        color("gainsboro") translate([0, 0, ex]) tapa();
        color("white") translate([CAM_C[0], CAM_C[1], LID_Z0 + LID_T + ex * 1.3]) visera();
    }
    color("orange") translate([0, 0, LID_Z0 - GASKET_H + ex * 0.6]) junta_tapa();
    color("lightyellow") translate([PE[0], PE[1], T + STANDOFF - ex * 0.2]) placa_electronica();
    color("lightyellow") translate([PP[0], PP[1], T + STANDOFF - ex * 0.2]) placa_potencia();
    color("lightgray") translate([T + 0.5, T + 0.5, CP_Z + ex * 0.4]) tapa_potencia();
    color("white") translate([W + 8, H + ex * 0.5, -2]) rotate([90, 0, 180]) tejadillo();
    color("white") translate([CAM_C[0], CAM_C[1], LID_Z0 - CAM_FRAME_H - CAM_MOD[2] - 3 + ex * 0.8]) soporte_camara();
    for (yc = MAST_Y) color("white") translate([W / 2, yc, -ex * 0.5]) mirror([0, 0, 1]) soporte_mastil();
    color("silver", 0.5) translate([W / 2, -60, -BRK_Z - MAST_OFF - ex * 0.5]) rotate([-90, 0, 0]) cylinder(d = MAST_D, h = H + 160);
    if (ex == 0) componentes();
}

// las vistas se giran para que el alto de la caja (Y) salga vertical en pantalla
module vista() { rotate([90, 0, 0]) children(); }

// ---------------------------------------------------------------------
//  Selección de pieza (ya orientadas para imprimir)
// ---------------------------------------------------------------------
if (PART == "montaje") vista() montaje(0);
else if (PART == "interior") vista() montaje(0, true);
else if (PART == "despiece") vista() montaje(70);
else if (PART == "cuerpo") cuerpo();                                                    // espalda sobre la cama
else if (PART == "tapa") translate([0, H, LID_Z0 + LID_T]) rotate([180, 0, 0]) tapa();  // cara exterior sobre la cama
else if (PART == "tapa_potencia") tapa_potencia();
else if (PART == "placa_electronica") placa_electronica();
else if (PART == "placa_potencia") placa_potencia();
else if (PART == "tejadillo") rotate([180, 0, 0]) rotate([ROOF_A, 0, 0]) tejadillo();     // cara superior sobre la cama
else if (PART == "visera") visera();
else if (PART == "soporte_camara") soporte_camara();
else if (PART == "soporte_mastil") soporte_mastil();
else if (PART == "junta_tapa") junta_tapa();
else if (PART == "junta_ventana") junta_ventana();
else if (PART == "separador_ir") separador_ir();
else if (PART == "pasamuros_usb") pasamuros_usb();
else if (PART == "garita_base") garita_base();
else if (PART == "garita_plato") garita_plato();
else if (PART == "garita_tapa") garita_tapa();
