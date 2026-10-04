// =====================================================================
//  Caja v3 BricoHams SDR · EA5KAO — DOS MÓDULOS al pie del mástil (~5 m)
//
//   MÓDULO DE ELECTRÓNICA  (VARIANTE="electronica")
//     - Rejilla universal de montaje (insertos M3 cada 20 mm + ranuras de bridas):
//       cabe cualquier SDR futuro (SDRplay, HydraSDR, otro RTL) sin reimprimir.
//     - Bandeja superior para Pi 5 + HAT y los 2 LilyGO.
//     - 14 pasamuros N hembra (2 filas de 7) + prensaestopas M25 (alimentación
//       desde el módulo de potencia), M20 (LAN) y 4 × PG7 (BME280, RS485 de viento,
//       pluviómetro y reserva) en la cara inferior.
//     - Ventilación forzada: entrada de 60 mm abajo a la izquierda y salida de
//       60 mm arriba a la derecha (flujo en diagonal), cada una con capota.
//     - Ventana opcional para la cámara WPI408 en la tapa.
//   MÓDULO DE POTENCIA  (VARIANTE="potencia")
//     - Base Schuko de superficie + cargador USB de 120 W + gatillo USB-C PD a 12 V,
//       portafusibles y regleta WAGO. Entrada de 230 V por PG9 y salida M25.
//
//  Coordenadas montada: X ancho, Y alto (0 = abajo), Z fondo (0 = espalda).
//  Exportar: openscad -D 'VARIANTE="potencia"' -D 'PART="cuerpo"' -o …  (tools/caja_v3.sh)
// =====================================================================

VARIANTE = "electronica";   // electronica | potencia
PART = "montaje";           // montaje | cuerpo | tapa | tejadillo | placa_rejilla | bandeja | poste_bandeja |
                            // capota | rejilla_ventilador | junta_tapa | pletina_pared | soporte_mastil |
                            // soporte_dongle | soporte_hub | soporte_lilygo | soporte_sdrplay | soporte_wago |
                            // tapon_n | tapon_pg | soporte_schuko | brida_cargador
CAMARA = true;              // ventana de la cámara en la tapa del módulo de electrónica
$fn = 48;
E = 0.01;
FONT = "DejaVu Sans:style=Bold";
EL = VARIANTE == "electronica";

// ------------------------------ medidas ------------------------------
W = EL ? 228 : 170;
H = EL ? 240 : 200;
D = 112;
T = 3.6;                    // pared de 9 líneas de 0,4: más rígida que la v2
R = 8;
GAP_LID = 3;  LID_T = 4.4;  RIB_H = 6;  GROOVE_W = 4.6;  GASKET_W = 4.8;  GASKET_H = 4;
EAR_L = 9;  EAR_Y = 18;  EAR_Z = 10;
EARS_Y = EL ? [24, 92, 148, 216] : [24, 100, 176];
HOLE_M3 = 3.4;  INS_M3 = 4.0;  INS_M3_L = 6;
HOLE_M4 = 4.5;  INS_M4 = 5.6;  INS_M4_L = 8.5;
HOLE_M5 = 5.5;

// rejilla interior
PL_T = 3.2;  STANDOFF = 8;
PL = EL ? [T + 3, T + 3, W - 2 * T - 6, H - 2 * T - 6] : [T + 3, T + 3, W - 2 * T - 6, H - 2 * T - 6];
PITCH = 20;
PL_BOSS = [[12, 12], [PL[2] - 12, 12], [12, PL[3] - 12], [PL[2] - 12, PL[3] - 12], [PL[2] / 2, PL[3] / 2]];

// conectores inferiores
N_HOLE = 16.2;              // pasamuros N hembra (rosca 5/8")
N_ROWS = [[26, ["SAT", "HAM", "VHF", "HF", "ADSB", "868", "GPS"]], [56, ["M433", "IG433", "DISC2", "HF2", "R1", "R2", "R3"]]];
N_PITCH = 27;
GL_Z = 88;
GLANDS_E = [["M25", 25.4, "PWR"], ["M20", 20.4, "LAN"], ["PG7", 12.7, "WX"], ["PG7", 12.7, "VIENTO"], ["PG7", 12.7, "LLUVIA"], ["PG7", 12.7, "RES"]];
GLANDS_P = [["PG9", 15.5, "230 V"], ["M25", 25.4, "A ELECTRONICA"]];

// ventiladores de 60 mm (12 V PWM de 4 hilos)
FAN = 60;  FAN_HOLE = 57;  FAN_SCREW = 50;
FAN_IN = [55, 60];          // (y, z) en la pared izquierda
FAN_OUT = [190, 60];        // (y, z) en la pared derecha

// cámara
CAM_C = [W / 2, 210];  CAM_WIN = [76, 26];  CAM_PC = [86.5, 36.5];  CAM_FRAME = 6;  CAM_FRAME_H = 5;

// tejadillo y fijación
ROOF_A = 5;  ROOF_GAP = 10;
ROOF_PILLARS = [[14, 24], [W - 14, 24], [14, D - 20], [W - 14, D - 20]];
WALL_Y = EL ? [40, 200] : [40, 160];

// --------------------------- utilidades ------------------------------
module rrect(w, h, r) { translate([r, r]) offset(r) square([w - 2 * r, h - 2 * r]); }
module outline() { rrect(W, H, R); }
module gota_y(d, l) { rotate([-90, 0, 0]) linear_extrude(l) union() { circle(d = d); rotate(225) square(d / 2); } }
module gota_x(d, l) { rotate([0, 90, 0]) linear_extrude(l) union() { circle(d = d); rotate(135) square(d / 2); } }
module rotulo_abajo(s, x, z, size) {   // legible desde delante y abajo
    translate([x, 0.6, z]) rotate([90, 0, 0]) linear_extrude(1) rotate(180) text(s, size = size, font = FONT, halign = "center", valign = "center");
}
module col(x, y, d, z0, z1) { translate([x, y, z0]) cylinder(d = d, h = z1 - z0); }

// ------------------------------ cuerpo -------------------------------
module ears() {
    zt = D + GAP_LID;
    for (xs = [-1, 1], y = EARS_Y) difference() {
        x0 = xs < 0 ? -EAR_L : W;
        hull() {
            translate([x0, y - EAR_Y / 2, zt - EAR_Z]) cube([EAR_L, EAR_Y, EAR_Z]);
            translate([xs < 0 ? -0.1 : W - 0.1, y - EAR_Y / 2, zt - EAR_Z - EAR_L]) cube([0.2, EAR_Y, 0.2]);
        }
        translate([xs < 0 ? -EAR_L / 2 - 0.5 : W + EAR_L / 2 + 0.5, y, zt - INS_M4_L]) cylinder(d = INS_M4, h = INS_M4_L + 1);
    }
}

module fan_hole(lado, y, z) {   // lado -1 izquierda, +1 derecha
    x = lado < 0 ? -1 : W - T - 1;
    translate([x, y, z]) rotate([0, 90, 0]) {
        // rejilla de lamas en vez de un hueco libre (dedos y bichos fuera)
        intersection() {
            cylinder(d = FAN_HOLE, h = T + 2);
            for (k = [-30 : 6 : 30]) translate([k - 1.6, -40, -1]) cube([3.2, 80, T + 4]);
        }
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * FAN_SCREW / 2, sy * FAN_SCREW / 2, -1]) cylinder(d = 3.6, h = T + 4);
    }
}

module cuerpo() {
    difference() {
        union() {
            difference() {
                linear_extrude(D) outline();
                translate([0, 0, T]) linear_extrude(D) offset(-T) outline();
            }
            ears();
            // nervios exteriores en la espalda (rigidez frente a la presión del viento y a la fijación)
            for (x = [W * 0.25, W * 0.75]) translate([x - 3, R, -6]) cube([6, H - 2 * R, 6 + E]);
            // pilares de la rejilla
            for (b = PL_BOSS) col(PL[0] + b[0], PL[1] + b[1], 10, T - E, T + STANDOFF);
            // pilares de las pletinas de pared / sillas de mástil (insertos M5 desde fuera)
            for (y = WALL_Y, x = [W * 0.25, W * 0.75]) col(x, y, 14, T - E, T + 10);
            // columnas del tejadillo
            for (p = ROOF_PILLARS) translate([p[0] - 5, H - T - 9, T - E]) cube([10, 9 + E, p[1] + 10 - T]);
            // marco interior de los ventiladores
            if (EL) {
                translate([T - E, FAN_IN[0] - FAN / 2 - 2, FAN_IN[1] - FAN / 2 - 2]) difference() { cube([4, FAN + 4, FAN + 4]); translate([-1, 4, 4]) cube([6, FAN - 4, FAN - 4]); }
                translate([W - T - 4 + E, FAN_OUT[0] - FAN / 2 - 2, FAN_OUT[1] - FAN / 2 - 2]) difference() { cube([4, FAN + 4, FAN + 4]); translate([-1, 4, 4]) cube([6, FAN - 4, FAN - 4]); }
            }
        }
        // insertos
        for (b = PL_BOSS) translate([PL[0] + b[0], PL[1] + b[1], T + STANDOFF - INS_M3_L]) cylinder(d = INS_M3, h = INS_M3_L + 1);
        for (y = WALL_Y, x = [W * 0.25, W * 0.75]) translate([x, y, -7]) cylinder(d = 7.0, h = 17);   // inserto M5 (agujero 7,0)
        for (p = ROOF_PILLARS) translate([p[0], H + 1, p[1]]) rotate([90, 0, 0]) cylinder(d = INS_M4, h = INS_M4_L + 1);
        // cara inferior
        if (EL) {
            for (r = N_ROWS) {
                n = len(r[1]); x0 = W / 2 - (n - 1) * N_PITCH / 2;
                for (i = [0 : n - 1]) {
                    translate([x0 + i * N_PITCH, -1, r[0]]) gota_y(N_HOLE, T + 2);
                    rotulo_abajo(r[1][i], x0 + i * N_PITCH, r[0] + 13, 3.2);
                }
            }
            glands(GLANDS_E);
            fan_hole(-1, FAN_IN[0], FAN_IN[1]);
            fan_hole(1, FAN_OUT[0], FAN_OUT[1]);
        } else {
            glands(GLANDS_P);
            for (x = [20 : 9 : W - 20]) translate([x, -1, 82]) cube([3.5, T + 2, 18]);              // rejilla de entrada
            for (x = [30 : 9 : W - 30]) translate([x, H - T - 1, 30]) cube([3.5, T + 2, 50]);       // salida bajo el tejadillo
            translate([W - 0.6, H / 2, D / 2]) rotate([90, 0, 90]) linear_extrude(1) rotate(-90)
                text("230 V · POTENCIA", size = 8, font = FONT, halign = "center", valign = "center");
        }
        if (EL) {
            for (x = [30 : 9 : W - 30]) translate([x, H - T - 1, 34]) cube([3.5, T + 2, 44]);       // salida pasiva bajo el tejadillo
            translate([W - 0.6, 110, D / 2]) rotate([90, 0, 90]) linear_extrude(1) rotate(-90)
                text("BricoHams SDR · EA5KAO", size = 8, font = FONT, halign = "center", valign = "center");
        }
    }
}

module glands(lista) {
    tot = sum_w(lista, len(lista) - 1) + 8 * (len(lista) - 1);
    for (i = [0 : len(lista) - 1]) {
        x = W / 2 - tot / 2 + sum_w(lista, i - 1) + 8 * i + lista[i][1] / 2;
        z = EL ? GL_Z : 40;
        translate([x, -1, z]) gota_y(lista[i][1], T + 2);
        rotulo_abajo(lista[i][2], x, EL ? z + lista[i][1] / 2 + 5 : z - lista[i][1] / 2 - 6, 3);
    }
}
function sum_w(l, i) = i < 0 ? 0 : l[i][1] + sum_w(l, i - 1);

// ------------------------------- tapa --------------------------------
LID_Z0 = D + GAP_LID;
module tapa() {
    fx = CAM_PC[0] + 2 * CAM_FRAME;  fy = CAM_PC[1] + 2 * CAM_FRAME;
    cam = EL && CAMARA;
    difference() {
        union() {
            translate([0, 0, LID_Z0]) linear_extrude(LID_T) union() {
                offset(2.3) outline();
                for (y = EARS_Y, xs = [-1, 1]) translate([xs < 0 ? -EAR_L - 0.5 : W, y - EAR_Y / 2]) square([EAR_L + 0.5, EAR_Y]);
            }
            translate([0, 0, LID_Z0 - RIB_H]) linear_extrude(RIB_H + E) difference() { offset(2.3) outline(); offset(-(T / 2 + GROOVE_W / 2 + 1.6)) outline(); }
            // nervios de rigidez por dentro
            for (x = [W * 0.33, W * 0.66]) translate([x - 2, 20, LID_Z0 - 5]) cube([4, H - 40, 5 + E]);
            if (cam) translate([CAM_C[0] - fx / 2, CAM_C[1] - fy / 2, LID_Z0 - CAM_FRAME_H]) cube([fx, fy, CAM_FRAME_H + E]);
        }
        translate([0, 0, LID_Z0 - RIB_H - 1]) linear_extrude(RIB_H + 1) difference() { offset(-(T / 2 - GROOVE_W / 2)) outline(); offset(-(T / 2 + GROOVE_W / 2)) outline(); }
        for (y = EARS_Y, xs = [-1, 1]) {
            translate([xs < 0 ? -EAR_L - 3 : W - 0.5, y - EAR_Y / 2 - 0.5, LID_Z0 - RIB_H - 1]) cube([EAR_L + 3.5, EAR_Y + 1, RIB_H + 1]);
            translate([xs < 0 ? -EAR_L / 2 - 0.5 : W + EAR_L / 2 + 0.5, y, LID_Z0 - 1]) cylinder(d = HOLE_M4, h = LID_T + 2);
        }
        if (cam) {
            translate([CAM_C[0] - CAM_WIN[0] / 2, CAM_C[1] - CAM_WIN[1] / 2, LID_Z0 - 10]) cube([CAM_WIN[0], CAM_WIN[1], 20]);
            translate([CAM_C[0] - CAM_PC[0] / 2, CAM_C[1] - CAM_PC[1] / 2, LID_Z0 - CAM_FRAME_H - 1]) cube([CAM_PC[0], CAM_PC[1], CAM_FRAME_H + 1 - 1.4]);
            for (s = [-1, 1]) {
                translate([CAM_C[0] + s * (CAM_PC[0] / 2 + CAM_FRAME / 2), CAM_C[1] - 8, LID_Z0 + LID_T - INS_M3_L]) cylinder(d = INS_M3, h = INS_M3_L + 1);
                translate([CAM_C[0] + s * (CAM_PC[0] / 2 + CAM_FRAME / 2), CAM_C[1] + 8, LID_Z0 - CAM_FRAME_H - 1]) cylinder(d = INS_M3, h = INS_M3_L + 1);
            }
        }
        translate([W / 2, 48, LID_Z0 + LID_T - 0.6]) linear_extrude(1)
            text(EL ? "BricoHams SDR" : "POTENCIA 230 V", size = EL ? 15 : 11, font = FONT, halign = "center", valign = "center");
        translate([W / 2, 26, LID_Z0 + LID_T - 0.6]) linear_extrude(1)
            text(EL ? "EA5KAO · Mi QTH · Región de Murcia" : "NO ABRIR CON TENSIÓN", size = 6, font = FONT, halign = "center", valign = "center");
    }
}

module junta_tapa() {
    linear_extrude(GASKET_H) difference() { offset(-(T / 2 - GASKET_W / 2)) outline(); offset(-(T / 2 + GASKET_W / 2)) outline(); }
}

// ----------------------------- tejadillo -----------------------------
ROOF_W = W + 16;  ROOF_L = D + GAP_LID + LID_T + 16;
function roof_z(y) = ROOF_GAP + (ROOF_L - y) * tan(ROOF_A);
module tejadillo() {
    difference() {
        union() {
            translate([0, ROOF_L, ROOF_GAP]) rotate([-ROOF_A, 0, 0]) translate([0, -ROOF_L / cos(ROOF_A), 0]) cube([ROOF_W, ROOF_L / cos(ROOF_A), 4]);
            translate([0, ROOF_L - 2.5, ROOF_GAP - 6]) cube([ROOF_W, 2.5, 7]);
            for (p = ROOF_PILLARS) translate([ROOF_W - 8 - p[0], p[1] + 2, 0]) cylinder(d = 11, h = roof_z(p[1] + 2) + 1);
        }
        for (p = ROOF_PILLARS) translate([ROOF_W - 8 - p[0], p[1] + 2, -1]) cylinder(d = HOLE_M4, h = 60);
    }
}

// --------------------- capota de ventilador (exterior) ---------------
module capota() {   // tapa la rejilla del ventilador por fuera; la boca mira hacia abajo
    s = FAN + 16; prof = 30;
    difference() {
        union() {
            translate([-s / 2, -s / 2, 0]) cube([s, s, 3]);
            hull() {
                translate([-s / 2, -s / 2 + 4, 0]) cube([s, s - 4, 3]);
                translate([-s / 2, -s / 2, prof - 3]) cube([s, 6, 3]);
            }
        }
        hull() {
            translate([-s / 2 + 3, -s / 2 + 7, -1]) cube([s - 6, s - 10, 1]);
            translate([-s / 2 + 3, -s / 2 + 3, prof - 6]) cube([s - 6, 3, 1]);
        }
        translate([-s / 2 + 3, -s / 2 - 1, -1]) cube([s - 6, 14, prof - 8]);        // boca hacia abajo
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * FAN_SCREW / 2, sy * FAN_SCREW / 2, -1]) cylinder(d = 3.6, h = 5);
    }
}
module rejilla_ventilador() {   // filtro: marco para malla de acero inox entre ventilador y pared
    difference() {
        translate([-FAN / 2, -FAN / 2, 0]) cube([FAN, FAN, 2.4]);
        translate([0, 0, -1]) cylinder(d = FAN - 6, h = 5);
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * FAN_SCREW / 2, sy * FAN_SCREW / 2, -1]) cylinder(d = 3.6, h = 5);
    }
}

// ------------------------ rejilla universal --------------------------
module placa_rejilla() {
    difference() {
        cube([PL[2], PL[3], PL_T]);
        for (b = PL_BOSS) translate([b[0], b[1], -1]) cylinder(d = HOLE_M3, h = 10);
        for (x = [PITCH : PITCH : PL[2] - PITCH / 2], y = [PITCH : PITCH : PL[3] - PITCH / 2]) {
            translate([x, y, -1]) cylinder(d = INS_M3, h = 10);                       // inserto M3 en cada nudo
            translate([x + PITCH / 2 - 1.4, y - 4, -1]) cube([2.8, 8, 10]);          // ranura de brida entre nudos
        }
        translate([8, 3, PL_T - 0.5]) linear_extrude(1) text(EL ? "REJILLA 20 mm · M3" : "POTENCIA", size = 4, font = FONT);
    }
}

// ----------------------- bandeja de la Pi ----------------------------
PI5 = [85, 56];  PI5_HOLES = [58, 49];  BAND = [170, 92];  BAND_H = 46;
PI_OFF = [8, 10];  BAND_Y = 118;  DONGLE_Y = 28;
module bandeja() {   // bandeja con la Pi 5 + HAT (izquierda) y 2 LilyGO (derecha)
    difference() {
        union() {
            cube([BAND[0], BAND[1], 3]);
            for (i = [0, 1], j = [0, 1]) translate([PI_OFF[0] + 3.5 + i * PI5_HOLES[0], PI_OFF[1] + 3.5 + j * PI5_HOLES[1], 0]) cylinder(d = 6.5, h = 9);
            for (k = [0, 1]) translate([108 + k * 31, 12, 0]) difference() { cube([29.4, 67.4, 7]); translate([1.2, 1.2, 5]) cube([27, 65, 5]); translate([4, 6, -1]) cube([21.4, 55.4, 10]); }
        }
        for (i = [0, 1], j = [0, 1]) translate([PI_OFF[0] + 3.5 + i * PI5_HOLES[0], PI_OFF[1] + 3.5 + j * PI5_HOLES[1], -1]) cylinder(d = 2.4, h = 20);
        for (p = [[6, 6], [BAND[0] - 6, 6], [6, BAND[1] - 6], [BAND[0] - 6, BAND[1] - 6]]) translate([p[0], p[1], -1]) cylinder(d = HOLE_M3, h = 10);
        translate([PI_OFF[0] + 16, PI_OFF[1] + 14, -1]) cube([50, 28, 10]);         // aire bajo la Pi
        for (k = [0, 1], y = [25, 60]) translate([106 + k * 31, y, -1]) cube([2.8, 3, 20]);
        translate([4, BAND[1] - 5, 2.5]) linear_extrude(1) text("Pi 5 + HAT          LilyGO ×2", size = 3.5, font = FONT);
    }
}
module poste_bandeja() {   // 4 postes: rejilla (M3 abajo) → bandeja (M3 arriba)
    difference() { cylinder(d = 10, h = BAND_H); translate([0, 0, -1]) cylinder(d = INS_M3, h = INS_M3_L + 1); translate([0, 0, BAND_H - INS_M3_L]) cylinder(d = INS_M3, h = INS_M3_L + 1); }
}

// --------------------- soportes para la rejilla ----------------------
module base_rejilla(l, w) {   // pletina con dos colisos M3 a paso de rejilla
    difference() {
        cube([l, w, 3]);
        for (x = [10, l - 10]) hull() { translate([x - 3, w / 2, -1]) cylinder(d = HOLE_M3, h = 5); translate([x + 3, w / 2, -1]) cylinder(d = HOLE_M3, h = 5); }
    }
}
module soporte_dongle(ancho = 26, largo = 90) {   // cuna para un dongle (RTL, FlightStick, HydraSDR…)
    difference() {
        union() {
            base_rejilla(largo, ancho + 16);
            for (s = [0, 1]) translate([0, s * (ancho + 2.4 + 4) + 4 - 2 - s * 0, 0]) translate([0, s ? 0 : 0, 0]) cube([largo, 2, 10]);
        }
        translate([-1, 6, 3]) cube([largo + 2, ancho + 4, 20]);
        for (x = [largo * 0.3, largo * 0.7]) translate([x, -1, 5]) cube([3, ancho + 20, 2]);
    }
}
module soporte_hub() { soporte_dongle(36, 124); }                    // regleta USB Vansuny 120 × 34 × 18
module soporte_sdrplay() { soporte_dongle(100, 100); }               // RSPdx/RSP1B (≈ 98 × 88 × 32)
module soporte_lilygo() { soporte_dongle(29, 70); }
module soporte_wago() {   // 3 WAGO 221-415 en línea (bus de 12 V y masa)
    difference() { union() { base_rejilla(70, 26); translate([5, 3, 0]) cube([60, 20, 8]); } translate([7, 5, 3]) cube([56, 16, 10]); for (x = [20, 40, 60]) translate([x - 1.4, -1, 5]) cube([2.8, 30, 2]); }
}
module tapon_n() { difference() { union() { cylinder(d = N_HOLE + 6, h = 2); cylinder(d = N_HOLE - 0.4, h = T + 4); } translate([0, 0, 2]) cylinder(d = N_HOLE - 4, h = 10); } }
module tapon_pg(d = 12.7) { difference() { union() { cylinder(d = d + 6, h = 2); cylinder(d = d - 0.4, h = T + 4); } translate([0, 0, 2]) cylinder(d = d - 4, h = 10); } }

// ------------------------- módulo de potencia ------------------------
SCHUKO = [80, 80, 42];       // base Schuko de superficie (medir la tuya)
module soporte_schuko() {   // pletina que atornilla la base Schuko a la rejilla
    difference() {
        translate([-SCHUKO[0] / 2 - 10, -SCHUKO[1] / 2 - 10, 0]) cube([SCHUKO[0] + 20, SCHUKO[1] + 20, 4]);
        for (sx = [-1, 1]) translate([sx * 30, 0, -1]) cylinder(d = HOLE_M4, h = 6);   // tornillos de la base (60 mm típicos)
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * (SCHUKO[0] / 2 + 3), sy * (SCHUKO[1] / 2 + 3), -1]) cylinder(d = HOLE_M3, h = 6);
        translate([0, 0, -1]) cylinder(d = 20, h = 6);                                   // paso del cable de red
    }
}
module brida_cargador() {   // abrazadera en U para sujetar el cargador enchufado (no se cae con vibración)
    difference() { cube([110, 16, 40]); translate([10, -1, 3]) cube([90, 18, 38]); for (x = [5, 105]) translate([x, 8, -1]) cylinder(d = HOLE_M3, h = 6); }
}

// --------------------------- fijaciones ------------------------------
module pletina_pared() {   // dos por módulo: insertos M5 de la espalda → tacos de pared
    difference() {
        hull() { cylinder(d = 26, h = 8); translate([W * 0.5, 0, 0]) cylinder(d = 26, h = 8); }
        for (x = [0, W * 0.5]) translate([x, 0, -1]) cylinder(d = HOLE_M5, h = 10);
        for (x = [-20, W * 0.5 + 20]) translate([x, 0, -1]) cylinder(d = 6, h = 10);
        for (x = [-20, W * 0.5 + 20]) translate([x, 0, 4]) cylinder(d1 = 6, d2 = 12, h = 4.1);
    }
    for (x = [-20, W * 0.5 + 20]) difference() { translate([x, 0, 0]) cylinder(d = 22, h = 8); translate([x, 0, -1]) cylinder(d = 6, h = 10); translate([x, 0, 4]) cylinder(d1 = 6, d2 = 12, h = 4.1); }
}
MAST_D = 40;
module soporte_mastil() {   // silla en V para abrazadera de 12–14 mm (poste al pie o el propio mástil)
    bw = W * 0.5 + 24; bh = 40; bz = 26; vw = MAST_D * 0.9;
    difference() {
        translate([-bw / 2, -bh / 2, 0]) cube([bw, bh, bz]);
        translate([0, -bh / 2 - 1, bz + E]) rotate([90, 0, 0]) mirror([0, 0, 1]) linear_extrude(bh + 2) polygon([[-vw / 2, 0], [vw / 2, 0], [0, -vw / 2]]);
        translate([-bw / 2 - 1, -7.5, 4]) cube([bw + 2, 15, 4]);
        for (sx = [-1, 1]) {
            translate([sx * W * 0.25, 0, -1]) cylinder(d = HOLE_M5, h = bz + 2);
            translate([sx * W * 0.25, 0, 12]) cylinder(d = 10, h = bz);
        }
    }
}

// ----------------------- cámara (visera y soporte) -------------------
CAM_SX = CAM_PC[0] / 2 + CAM_FRAME / 2;  CAM_MOD = [76, 28, 25];
module visera() {
    vw = 2 * CAM_SX + 14; vh = CAM_WIN[1] / 2 + 12; vv = 32;
    difference() {
        union() {
            translate([-vw / 2, -vh, 0]) cube([vw, 2 * vh, 3]);
            translate([-vw / 2, vh - 3, 0]) cube([vw, 3, vv]);
            for (s = [-1, 1]) translate([s * (vw / 2 - 1.5) - 1.5, 0, 0]) hull() { translate([0, vh - 3, 0]) cube([3, 3, vv]); translate([0, -vh, 0]) cube([3, 1, 3]); }
        }
        translate([-CAM_WIN[0] / 2 - 1, -CAM_WIN[1] / 2 - 1, -1]) cube([CAM_WIN[0] + 2, CAM_WIN[1] + 2, 10]);
        for (s = [-1, 1]) translate([s * CAM_SX, -8, -1]) cylinder(d = HOLE_M3, h = 10);
    }
}
module soporte_camara() {
    L = 2 * CAM_SX + 10;
    difference() {
        union() {
            translate([-L / 2, -CAM_MOD[1] / 2 - 2, 0]) cube([L, CAM_MOD[1] + 4, 3]);
            for (s = [-1, 1]) translate([s * CAM_SX, 8, 0]) cylinder(d = 8, h = 3 + CAM_MOD[2]);
            for (s = [-1, 1]) translate([s * 30 - 6, -8, 0]) cube([12, 16, 4]);
        }
        for (s = [-1, 1]) translate([s * CAM_SX, 8, -1]) cylinder(d = HOLE_M3, h = 40);
        translate([-12, -CAM_MOD[1] / 2 + 1, -1]) cube([24, CAM_MOD[1] - 2, 10]);
    }
}

// ------------------------------ montaje ------------------------------
module ghost(c) { color(c, 0.6) children(); }
module componentes() {
    pz = T + STANDOFF + PL_T;
    if (EL) {
        // fila de SDR sobre la rejilla (abajo): Mini, V3, FlightStick y la BAHÍA DE EXPANSIÓN (SDRplay o 3 dongles más)
        for (i = [0 : 2]) ghost("steelblue") translate([PL[0] + 12 + i * 34, PL[1] + DONGLE_Y, pz]) cube([26, 85, 13]);
        ghost("gold") translate([PL[0] + 114, PL[1] + DONGLE_Y, pz]) cube([100, 90, 3]);         // bahía de expansión (marcada)
        ghost("lightgoldenrodyellow") translate([PL[0] + 114, PL[1] + DONGLE_Y, pz + 3]) cube([98, 88, 32]);   // SDRplay futuro
        ghost("dimgray") translate([PL[0] + 20, PL[1] + 140, pz]) cube([124, 36, 18]);          // hub Vansuny
        ghost("silver") translate([PL[0] + 150, PL[1] + 140, pz]) cube([26, 50, 20]);           // diplexor HF/VHF
        ghost("orange") translate([PL[0] + 90, PL[1] + 186, pz]) cube([60, 26, 10]);            // WAGO 12 V
        // bandeja
        translate([PL[0] + 20, PL[1] + BAND_Y, pz + BAND_H]) {
            color("lightyellow") bandeja();
            ghost("green") translate([PI_OFF[0], PI_OFF[1], 9]) cube([PI5[0], PI5[1], 18]);
            ghost("purple") translate([PI_OFF[0], PI_OFF[1], 29]) cube([PI5[0], PI5[1], 12]);
            for (k = [0, 1]) ghost("royalblue") translate([109.2 + k * 31, 13.2, 7]) cube([27, 65, 10]);
        }
        if (CAMARA) ghost("black") translate([CAM_C[0] - CAM_MOD[0] / 2, CAM_C[1] - CAM_MOD[1] / 2, LID_Z0 - CAM_FRAME_H - CAM_MOD[2]]) cube(CAM_MOD);
        for (f = [[0, FAN_IN], [W - T - 25, FAN_OUT]]) ghost("black") translate([f[0] == 0 ? T : f[0], f[1][0] - 30, f[1][1] - 30]) cube([25, 60, 60]);
    } else {
        ghost("white") translate([W / 2 - SCHUKO[0] / 2, 30, pz]) cube(SCHUKO);
        ghost("black") translate([W / 2 - 35, 40, pz + SCHUKO[2]]) cube([70, 70, 32]);           // cargador de 120 W
        ghost("dimgray") translate([20, 140, pz]) cube([60, 20, 14]);                           // gatillo PD 12 V
        ghost("orange") translate([90, 140, pz]) cube([60, 26, 10]);                           // WAGO + fusibles
    }
}

module montaje(abierta = false) {
    color("white") cuerpo();
    color("lightyellow") translate([PL[0], PL[1], T + STANDOFF]) placa_rejilla();
    if (!abierta) color("gainsboro") tapa();
    color("orange") translate([0, 0, LID_Z0 - GASKET_H]) junta_tapa();
    color("white") translate([W + 8, H, -2]) rotate([90, 0, 180]) tejadillo();
    if (EL && CAMARA && !abierta) color("white") translate([CAM_C[0], CAM_C[1], LID_Z0 + LID_T]) visera();
    if (EL) {
        color("white") translate([-30, FAN_IN[0], FAN_IN[1]]) rotate([0, -90, 0]) rotate(90) translate([0, 0, -30]) capota();
        color("white") translate([W + 30, FAN_OUT[0], FAN_OUT[1]]) rotate([0, 90, 0]) rotate(-90) translate([0, 0, -30]) capota();
    }
    componentes();
}

if (PART == "montaje") rotate([90, 0, 0]) montaje();
else if (PART == "interior") rotate([90, 0, 0]) montaje(true);
else if (PART == "cuerpo") cuerpo();
else if (PART == "tapa") translate([0, H, LID_Z0 + LID_T]) rotate([180, 0, 0]) tapa();
else if (PART == "tejadillo") rotate([180, 0, 0]) rotate([ROOF_A, 0, 0]) tejadillo();
else if (PART == "placa_rejilla") placa_rejilla();
else if (PART == "bandeja") bandeja();
else if (PART == "poste_bandeja") poste_bandeja();
else if (PART == "capota") capota();
else if (PART == "rejilla_ventilador") rejilla_ventilador();
else if (PART == "junta_tapa") junta_tapa();
else if (PART == "pletina_pared") pletina_pared();
else if (PART == "soporte_mastil") soporte_mastil();
else if (PART == "soporte_dongle") soporte_dongle();
else if (PART == "soporte_hub") soporte_hub();
else if (PART == "soporte_lilygo") soporte_lilygo();
else if (PART == "soporte_sdrplay") soporte_sdrplay();
else if (PART == "soporte_wago") soporte_wago();
else if (PART == "tapon_n") tapon_n();
else if (PART == "tapon_pg") tapon_pg();
else if (PART == "soporte_schuko") soporte_schuko();
else if (PART == "brida_cargador") brida_cargador();
else if (PART == "visera") visera();
else if (PART == "soporte_camara") soporte_camara();
