// =====================================================================
//  Caja v3 BricoHams SDR · N0CALL — DOS MÓDULOS al pie del mástil (~5 m)
//
//   MÓDULO DE ELECTRÓNICA  (VARIANTE="electronica")
//     - Rejilla universal de montaje (insertos M3 cada 20 mm + ranuras de bridas):
//       cabe cualquier SDR futuro (SDRplay, HydraSDR, otro RTL) sin reimprimir.
//     - Bandeja intermedia de SDR (bandeja_sdr) con bahías para 3 SDR más:
//       HackRF One, RTL-SDR V4 y Airspy HF+ Discovery (lista SDR_DECK).
//     - Bandeja superior para Pi 5 + HAT, LilyGO y RAK4631 (RAK19007).
//     - Dos bandejas intermedias de SDR (3 + 8 plazas).
//     - 18 pasamuros N hembra (filas de 7 + 7 + 4) + prensaestopas M25 (alimentación
//       desde el módulo de potencia), M20 (LAN) y 4 × PG7 (BME280, RS485 de viento,
//       pluviómetro y reserva) en la cara inferior.
//     - Ventilación forzada: entrada de 60 mm abajo a la izquierda y salida de
//       60 mm arriba a la derecha (flujo en diagonal), cada una con capota.
//     - Intemperie: faldón de la tapa (alero de 9 mm sobre la pared, vuelo 1,2 mm), junta TPU
//       con compresión 25 %, 4 orificios de drenaje, cejas en las rejillas superiores, respiradero
//       con membrana (PG7 «VENT»), tapones con cabeza que tapa la punta de la gota, tejadillo con faldones.
//     - Ventana opcional en la tapa para la Raspberry Pi Camera Module 3 Wide (cristal pegado, visera sin recorte del campo de 102° × 67°).
//   MÓDULO DE POTENCIA  (VARIANTE="potencia")
//     - Base Schuko de superficie + cargador USB de 120 W + gatillo USB-C PD a 12 V,
//       portafusibles y regleta WAGO. Entrada de 230 V por PG9 y salida M25.
//   MÓDULO SAI  (VARIANTE="sai", opcional, debajo del de potencia)
//     - Reaprovecha un SAI line-interactive (placa, transformador y batería de plomo
//       12 V 7–9 Ah) con filtro EMI de red a la entrada y otro a la salida.
//     - Batería en cuna con repisa y correa; placa del SAI de canto en dos guías;
//       transformador en pletina; filtros EMI en escuadras. Lista SAI_LAYOUT.
//     - Prensaestopas PG9 «RED» y «SALIDA» (al PG9 de 230 V del módulo de potencia)
//       y PG7 «DATOS» (USB/serie del SAI a la Pi). Rejillas arriba y abajo (hidrógeno).
//
//  Coordenadas montada: X ancho, Y alto (0 = abajo), Z fondo (0 = espalda).
//  Exportar: openscad -D 'VARIANTE="potencia"' -D 'PART="cuerpo"' -o …  (tools/caja_v3.sh)
//
//  MATERIAL (clima de diseño: 47 °C a la sombra; al sol el interior llega a 55–65 °C, ver docs/manuales/17_CAJA_V3.md):
//    ASA blanco en TODAS las piezas rígidas (cuerpo, tapa, tejadillo, capotas, placa_rejilla, bandejas, postes, soportes, cunas
//    de batería, guías de placa, pletina del transformador): HDT ≈ 95 °C. PETG (HDT ≈ 70 °C) no se usa: fluye bajo carga a 60–65 °C.
//    TPU 95A solo en junta_tapa y tapones (no portan carga, trabajan por compresión y aguantan 80–100 °C).
//  LLUVIA (rachas de 100 km/h, chubascos de más de 100 mm/h): faldón de la tapa, tejadillo con faldones laterales hasta 2 mm del techo
//    (ROOF_SKIRT_Z), cejas en las rejillas superiores (ceja_techo), capotas con la boca hacia abajo, 4 drenajes y respiradero PG7 «VENT».
// =====================================================================

VARIANTE = "electronica";   // electronica | potencia | sai
PART = "montaje";           // montaje | cuerpo | tapa | tejadillo | placa_rejilla | bandeja | poste_bandeja |
                            // bandeja_sdr | poste_superior |
                            // capota | rejilla_ventilador | junta_tapa | pletina_pared | soporte_mastil |
                            // soporte_dongle | soporte_hub | soporte_lilygo | soporte_sdrplay | soporte_wago |
                            // tapon_n | tapon_pg | soporte_schuko | brida_cargador |
                            // soporte_bateria | guia_pcb | pletina_trafo | soporte_filtro
RESPIRO = false;            // true con PART="tapon_pg": tapón con orificio para la membrana del respiradero
CAMARA = true;              // ventana de la cámara en la tapa del módulo de electrónica
$fn = 48;
E = 0.01;
FONT = "DejaVu Sans:style=Bold";
EL = VARIANTE == "electronica";
SAI = VARIANTE == "sai";

// ------------------------------ medidas ------------------------------
W = EL ? 228 : SAI ? 228 : 170;
H = EL ? 240 : SAI ? 240 : 200;
D = EL ? 192 : SAI ? 140 : 112;   // electrónica: 192 de fondo para la 3.ª fila de N, las dos bandejas de SDR y la Pi (con pared de 4,8)
T = 4.8;                    // pared de 12 líneas de 0,4: más resistente a la intemperie
R = 8;
GAP_LID = 3;  LID_T = 5.2;  RIB_H = 6;  GROOVE_W = 5.8;  GASKET_W = 5.6;  GASKET_H = 4;   // junta TPU 5,6 × 4: más estrecha que la ranura para que se ensanche al comprimirse
GASKET_COMP = (GASKET_H - GAP_LID) / GASKET_H;   // compresión de la junta (objetivo 20–30 %): 4 → 3 mm = 25 %
// intemperie: faldón de la tapa que cae como un alero sobre la pared (el agua no llega a la junta)
SKIRT_H = 12;               // altura del faldón desde el plano de la tapa; solapa SKIRT_H - GAP_LID = 9 mm la pared por debajo de la junta
SKIRT_CL = 1.0;             // holgura faldón–pared (rompe la capilaridad y absorbe el alabeo del ASA)
DRIP_OUT = 1.2;             // el faldón sobresale del faldón de remate de la caja: el agua gotea sin volver hacia la junta
BELT_TOP = 11;              // el remate de la caja termina 2 mm por debajo del faldón de la tapa (hueco de escurrido)
DRAIN_D = 3.2;  DRAIN_X = 14;   // orificios de drenaje del suelo (condensación): 4 por módulo, en las esquinas
BREATH_D = 4;  BREATH_MEMB = 8; // respiradero: orificio y disco de membrana ePTFE; BREATH_MEMB es PENDIENTE de medir con la membrana que compres
RAIN_CURB_H = 3;                // ceja alrededor de las rejillas de la cara superior
EAR_L = 9;  EAR_Y = 26;  EAR_Z = 10;   // cierres laterales anchos (v5.5)
// diseño «caja rígida de transporte» (v5.5): faldón perimetral que enrasa con la tapa y aspa en X hundida
BELT_H = 16;  BELT_OUT = 2.3;           // BELT_OUT = vuelo del faldón de remate de la caja
LID_OFF = BELT_OUT + DRIP_OUT;          // vuelo de la tapa y de su faldón (= 3,5 mm; la tapa sigue ≤ 250 mm con las orejas)
LID_GR_W = 7;  LID_GR_D = 1.2;          // ancho y profundidad de las vetas de la tapa (sin voladizos al imprimir boca abajo)
EARS_Y = H == 240 ? [24, 92, 148, 216] : [24, 100, 176];
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
N_ROWS = [[26, ["SAT", "HAM", "VHF", "HF", "ADSB", "868", "GPS"]], [56, ["M433", "IG433", "DISC2", "HF2", "R1", "R2", "R3"]], [86, ["HRF", "AHF", "V4", "R4"]]];
N_PITCH = 27;
GL_Z = 116;
GLANDS_E = [["M25", 25.4, "PWR"], ["M20", 20.4, "LAN"], ["PG7", 12.7, "WX"], ["PG7", 12.7, "VIENTO"], ["PG7", 12.7, "LLUVIA"], ["PG7", 12.7, "VENT"]];   // VENT: respiradero con membrana (tapon_pg con RESPIRO=true o PG7 comercial)
GLANDS_P = [["PG9", 15.5, "230 V"], ["M25", 25.4, "A ELECTRONICA"], ["PG7", 12.7, "VENT"]];
GLANDS_S = [["PG9", 15.5, "RED"], ["PG9", 15.5, "SALIDA"], ["PG7", 12.7, "DATOS"]];

// ventiladores de 60 mm (12 V PWM de 4 hilos)
FAN = 60;  FAN_HOLE = 57;  FAN_SCREW = 50;
FAN_IN = [55, 60];          // (y, z) en la pared izquierda
FAN_OUT = [190, 68];        // (y, z) en la pared derecha; z = 68 deja el ventilador (borde inferior 38) por encima del diplexor (arriba 34,8)

// cámara
// Raspberry Pi Camera Module 3 Wide (SC0874, IMX708): placa 25 × 24, 12,4 mm de alto con el objetivo, 4 × M2 en 21 × 12,5
// (patrón oficial: confirmar con el plano del Product Brief). Campo 120° diagonal / 102° H / 67° V.
CAM_PCB = [25, 24, 12.4];
CAM_HOLES = [21, 12.5];   // patrón M2 de las cámaras oficiales (confirmar con el plano del Product Brief)
CAM_LENS_D = 8;
CAM_FOV_H = 102;
CAM_FOV_V = 67;
CAM_VID_T = 2;     // cristal de policarbonato/acrílico pegado en un rebaje de la cara exterior de la tapa
CAM_GAP = 1;       // objetivo → cara interior del cristal
CAM_D = CAM_GAP + CAM_VID_T;   // objetivo → cara exterior del cristal (d de la fórmula de la ventana)
CAM_LENS_Z = LID_T - CAM_VID_T - CAM_GAP;   // el objetivo sobresale 1,4 mm del plano interior de la tapa
// ventana ≥ 2·d·tan(FOV/2) + Ø objetivo (15,4 × 12,0 mm con d = 3); se dan 2 mm de margen por lado
CAM_WIN = [20, 16];  CAM_LAP = 4;   // CAM_LAP: solape del cristal sobre la tapa (cordón de silicona neutra/MS por todo el perímetro)
CAM_PC = [27, 26];  CAM_FRAME = 8;  CAM_FRAME_H = 5;   // cavidad de la placa y collar de insertos M3 (visera y soporte)
CAM_BOSS_H = 4;  CAM_M2_INS = false;   // postes M2: autorroscantes (Ø1,8) o con inserto M2 (Ø3,2 × 4) si CAM_M2_INS = true
CAM_C = [W / 2, 210];
CAM_GL = [CAM_WIN[0] + 2 * CAM_LAP + 0.6, CAM_WIN[1] + 2 * CAM_LAP + 0.6];   // rebaje del cristal (0,3 mm de holgura por lado)

// tejadillo y fijación
ROOF_A = 5;  ROOF_GAP = 10;
ROOF_PILLARS = [[14, 24], [W - 14, 24], [14, D - 20], [W - 14, D - 20]];
WALL_Y = H == 240 ? [40, 200] : [40, 160];

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
            // faldón de remate: sube 45° (imprime sin soportes), remata con otro 45° a SKIRT_H - GAP_LID + 2 mm de la junta
            // y queda más bajo que el faldón de la tapa, que lo cubre con vuelo DRIP_OUT
            difference() {
                hull() {
                    translate([0, 0, D - BELT_H]) linear_extrude(E) outline();
                    translate([0, 0, D - BELT_H + BELT_OUT]) linear_extrude(E) offset(BELT_OUT) outline();
                    translate([0, 0, D - BELT_TOP - BELT_OUT]) linear_extrude(E) offset(BELT_OUT) outline();
                    translate([0, 0, D - BELT_TOP]) linear_extrude(E) outline();
                }
                translate([0, 0, D - BELT_H - 1]) linear_extrude(BELT_H + 2) offset(-T) outline();
            }
            // cejas antilluvia alrededor de las rejillas de la cara superior (el agua de la tapa/pared no entra por ellas)
            if (EL) ceja_techo(34, 78); else if (SAI) ceja_techo(30, 90); else ceja_techo(30, 80);
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
        // drenaje de la condensación: 4 orificios en las esquinas del suelo (el módulo cuelga vertical; el agua baja al suelo)
        for (x = [DRAIN_X, W - DRAIN_X], z = [8, D - 12]) translate([x, -1, z]) rotate([-90, 0, 0]) cylinder(d = DRAIN_D, h = T + 2);
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
        } else if (SAI) {
            glands(GLANDS_S);
            for (x = [20 : 9 : W - 20]) translate([x, -1, 90]) cube([3.5, T + 2, 24]);              // entrada de aire abajo
            for (x = [30 : 9 : W - 30]) translate([x, H - T - 1, 30]) cube([3.5, T + 2, 60]);       // salida (hidrógeno) bajo el tejadillo
            translate([W - 0.6, H / 2, D / 2]) rotate([90, 0, 90]) linear_extrude(1) rotate(-90)
                text("SAI · BATERÍA 12 V", size = 8, font = FONT, halign = "center", valign = "center");
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
                text("BricoHams SDR · N0CALL", size = 8, font = FONT, halign = "center", valign = "center");
        }
    }
}

// ceja antilluvia: marco de 2 mm y RAIN_CURB_H de alto que rodea las rejillas de la cara superior (por fuera de las ranuras)
module ceja_techo(z0, z1) {
    x0 = 27;  x1 = W - 27;  za = z0 - 3;  zb = z1 + 3;
    translate([x0, H - E, za]) difference() {
        cube([x1 - x0, RAIN_CURB_H + E, zb - za]);
        translate([2, -1, 2]) cube([x1 - x0 - 4, RAIN_CURB_H + E + 2, zb - za - 4]);
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
// panel decorativo: entre el rótulo inferior (y≈60) y la ventana de cámara (y≈186) o el borde superior
module lid_aspa() {
    x0 = 24;  x1 = W - 24;  y0 = 72;  y1 = EL ? 176 : H - 24;
    difference() {
        translate([x0, y0]) offset(r = 6) offset(delta = -6) square([x1 - x0, y1 - y0]);
        translate([x0 + LID_GR_W, y0 + LID_GR_W]) offset(r = 4) offset(delta = -4) square([x1 - x0 - 2 * LID_GR_W, y1 - y0 - 2 * LID_GR_W]);
    }
    intersection() {
        translate([x0, y0]) square([x1 - x0, y1 - y0]);
        union() for (d = [[[x0, y0], [x1, y1]], [[x0, y1], [x1, y0]]])
            hull() { translate(d[0]) circle(d = LID_GR_W, $fn = 24); translate(d[1]) circle(d = LID_GR_W, $fn = 24); }
    }
}
module tapa() {
    fx = CAM_PC[0] + 2 * CAM_FRAME;  fy = CAM_PC[1] + 2 * CAM_FRAME;
    cam = EL && CAMARA;
    difference() {
        union() {
            translate([0, 0, LID_Z0]) linear_extrude(LID_T) union() {
                offset(LID_OFF) outline();
                for (y = EARS_Y, xs = [-1, 1]) translate([xs < 0 ? -EAR_L - 0.5 : W, y - EAR_Y / 2]) square([EAR_L + 0.5, EAR_Y]);
            }
            // labio interior (centra la tapa y encierra la junta por dentro)
            translate([0, 0, LID_Z0 - RIB_H]) linear_extrude(RIB_H + E) difference() { offset(-(T / 2 + GROOVE_W / 2)) outline(); offset(-(T / 2 + GROOVE_W / 2 + 1.6)) outline(); }
            // faldón exterior (alero): cae SKIRT_H - GAP_LID sobre la pared, con holgura SKIRT_CL
            translate([0, 0, LID_Z0 - SKIRT_H]) linear_extrude(SKIRT_H + E) difference() { offset(LID_OFF) outline(); offset(SKIRT_CL) outline(); }
            // nervios de rigidez por dentro
            for (x = [W * 0.33, W * 0.66]) translate([x - 2, 20, LID_Z0 - 5]) cube([4, H - 40, 5 + E]);
            if (cam) translate([CAM_C[0] - fx / 2, CAM_C[1] - fy / 2, LID_Z0 - CAM_FRAME_H]) cube([fx, fy, CAM_FRAME_H + E]);
        }
        for (y = EARS_Y, xs = [-1, 1]) {
            translate([xs < 0 ? -EAR_L - 3 : W - 0.5, y - EAR_Y / 2 - 0.5, LID_Z0 - SKIRT_H - 1]) cube([EAR_L + 3.5, EAR_Y + 1, SKIRT_H + 1]);
            translate([xs < 0 ? -EAR_L / 2 - 0.5 : W + EAR_L / 2 + 0.5, y, LID_Z0 - 1]) cylinder(d = HOLE_M4, h = LID_T + 2);
        }
        if (cam) {
            translate([CAM_C[0] - CAM_WIN[0] / 2, CAM_C[1] - CAM_WIN[1] / 2, LID_Z0 - 10]) cube([CAM_WIN[0], CAM_WIN[1], 20]);
            // rebaje exterior para el cristal (queda enrasado con la cara exterior; la lluvia lo apoya contra el resalte)
            translate([CAM_C[0] - CAM_GL[0] / 2, CAM_C[1] - CAM_GL[1] / 2, LID_Z0 + LID_T - CAM_VID_T]) cube([CAM_GL[0], CAM_GL[1], CAM_VID_T + 1]);
            translate([CAM_C[0] - CAM_PC[0] / 2, CAM_C[1] - CAM_PC[1] / 2, LID_Z0 - CAM_FRAME_H - 1]) cube([CAM_PC[0], CAM_PC[1], CAM_FRAME_H + 1 - 1.4]);
            for (s = [-1, 1]) {
                translate([CAM_C[0] + s * (CAM_PC[0] / 2 + CAM_FRAME / 2), CAM_C[1] - 8, LID_Z0 + LID_T - INS_M3_L]) cylinder(d = INS_M3, h = INS_M3_L + 1);
                translate([CAM_C[0] + s * (CAM_PC[0] / 2 + CAM_FRAME / 2), CAM_C[1] + 8, LID_Z0 - CAM_FRAME_H - 1]) cylinder(d = INS_M3, h = INS_M3_L + 1);
            }
        }
        // aspa en X y marco hundidos (cara exterior; sin voladizos al imprimir boca abajo)
        translate([0, 0, LID_Z0 + LID_T - LID_GR_D]) linear_extrude(LID_GR_D + 1) lid_aspa();
        translate([W / 2, 48, LID_Z0 + LID_T - 0.6]) linear_extrude(1)
            text(EL ? "BricoHams SDR" : SAI ? "SAI 230 V · Pb" : "POTENCIA 230 V", size = EL ? 15 : 11, font = FONT, halign = "center", valign = "center");
        translate([W / 2, 26, LID_Z0 + LID_T - 0.6]) linear_extrude(1)
            text(EL ? "BricoHams SDR" : SAI ? "DESENCHUFAR Y QUITAR BATERÍA" : "NO ABRIR CON TENSIÓN", size = 6, font = FONT, halign = "center", valign = "center");
    }
}

module junta_tapa() {
    linear_extrude(GASKET_H) difference() { offset(-(T / 2 - GASKET_W / 2)) outline(); offset(-(T / 2 + GASKET_W / 2)) outline(); }
}

// ----------------------------- tejadillo -----------------------------
ROOF_W = W + 16;  ROOF_FRONT = 30;   // vuelo lateral 8 mm por lado (cabe en 250 mm) y 30 mm por delante de la tapa
ROOF_L = D + GAP_LID + LID_T + ROOF_FRONT;  ROOF_SIDE_H = 8;   // refuerzo del borde del tejadillo
ROOF_SKIRT_Z = 2;  // el faldón lateral baja hasta 2 mm del techo de la caja (lluvia batida por viento de 100 km/h)
function roof_z(y) = ROOF_GAP + (ROOF_L - y) * tan(ROOF_A);
module tejadillo() {
    difference() {
        union() {
            translate([0, ROOF_L, ROOF_GAP]) rotate([-ROOF_A, 0, 0]) translate([0, -ROOF_L / cos(ROOF_A), 0]) {
                cube([ROOF_W, ROOF_L / cos(ROOF_A), 4]);
                for (x = [0, ROOF_W - 2.5]) translate([x, 0, -ROOF_SIDE_H]) cube([2.5, ROOF_L / cos(ROOF_A), ROOF_SIDE_H + 4]);   // refuerzo del borde
            }
            // faldones laterales hasta ROOF_SKIRT_Z del techo de la caja: con rachas de 100 km/h la lluvia no entra de lado por las rejillas superiores
            for (x = [0, ROOF_W - 2.5]) translate([x, 0, 0]) rotate([90, 0, 90]) linear_extrude(2.5)
                polygon([[0, ROOF_SKIRT_Z], [ROOF_L, ROOF_SKIRT_Z], [ROOF_L, roof_z(ROOF_L) + 1], [0, roof_z(0) + 1]]);
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
        translate([8, 3, PL_T - 0.5]) linear_extrude(1) text(EL ? "REJILLA 20 mm · M3" : SAI ? "SAI · BATERIA" : "POTENCIA", size = 4, font = FONT);
    }
}

// ----------------------- bandeja de la Pi ----------------------------
PI5 = [85, 56];  PI5_HOLES = [58, 49];  BAND = [170, 92];  BAND_H = 131;
RAK_O = [129, 12];  RAK_C = [32.8, 62.8];   // cuna del RAK19007 (30 × 60) con RAK4631 y el GPS en el slot A
PI_OFF = [8, 10];  BAND_Y = 118;  DONGLE_Y = 28;
BAND_POSTS = [[6, 6], [BAND[0] - 6, 6], [6, BAND[1] - 6], [BAND[0] - 6, BAND[1] - 6]];
module bandeja() {   // bandeja con la Pi 5 + HAT (izquierda) y 2 LilyGO (derecha)
    difference() {
        union() {
            cube([BAND[0], BAND[1], 3]);
            for (i = [0, 1], j = [0, 1]) translate([PI_OFF[0] + 3.5 + i * PI5_HOLES[0], PI_OFF[1] + 3.5 + j * PI5_HOLES[1], 0]) cylinder(d = 6.5, h = 9);
            translate([98, 12, 0]) difference() { cube([29.4, 67.4, 7]); translate([1.2, 1.2, 5]) cube([27, 65, 5]); translate([4, 6, -1]) cube([21.4, 55.4, 10]); }   // LilyGO
            translate([RAK_O[0], RAK_O[1], 0]) difference() { cube([RAK_C[0], RAK_C[1], 8]); translate([1.2, 1.2, 5]) cube([RAK_C[0] - 2.4, RAK_C[1] - 2.4, 5]); translate([5, 6, -1]) cube([RAK_C[0] - 10, RAK_C[1] - 12, 10]); }   // RAK19007 + RAK4631
        }
        for (i = [0, 1], j = [0, 1]) translate([PI_OFF[0] + 3.5 + i * PI5_HOLES[0], PI_OFF[1] + 3.5 + j * PI5_HOLES[1], -1]) cylinder(d = 2.4, h = 20);
        for (p = BAND_POSTS) translate([p[0], p[1], -1]) cylinder(d = HOLE_M3, h = 10);
        translate([PI_OFF[0] + 16, PI_OFF[1] + 14, -1]) cube([50, 28, 10]);         // aire bajo la Pi
        for (x = [96, 127], y = [25, 60]) translate([x, y, -1]) cube([2.8, 3, 20]);
        translate([4, BAND[1] - 5, 2.5]) linear_extrude(1) text("Pi 5 + HAT       LilyGO     RAK4631", size = 3.5, font = FONT);
    }
}
module poste(h) { difference() { cylinder(d = 10, h = h); translate([0, 0, -1]) cylinder(d = INS_M3, h = INS_M3_L + 1); translate([0, 0, h - INS_M3_L]) cylinder(d = INS_M3, h = INS_M3_L + 1); } }
module poste_bandeja() { poste(DECK_H); }                     // 6: rejilla → bandeja_sdr (4 bajo la Pi + 2 delanteros)
module poste_medio() { poste(DECK2_H - DECK_H - DECK_T); }    // 6: bandeja_sdr → bandeja_sdr2
module poste_superior() { poste(BAND_H - DECK2_H - DECK_T); } // 4: bandeja_sdr2 → bandeja de la Pi (espárrago M3 × 14)

// -------------- bandeja intermedia de SDR (3 SDR más) ----------------
// Va sobre la fila de dongles y la bahía SDRplay y bajo la bandeja de la Pi. Coordenadas absolutas
// del módulo (DECK_O = esquina) y de cada SDR relativas a la bandeja: [nombre, [x, y], [largo x, ancho y, alto]].
// Los conectores (SMA/USB) quedan en los extremos del lado largo, con ≥ 12 mm libres para el cable.
DECK_O = [31, 55];  DECK = [167, 170];  DECK_T = 3;  DECK_H = 38;  DECK2_H = 82;
SDR_DECK = [["HRF", [20, 82], [120, 75, 20]], ["V4", [12, 20], [85, 26, 13]], ["AHF", [112, 6], [45, 60, 12]]];
// segunda bandeja (v5.5): HL2 = Hermes-Lite 2 (medida a verificar con la tuya), 3 dongles tipo RTL/FlightStick (85 × 26 × 13) y 2 bahías de 52 × 30 × 15
// Los postes están en y≈73–77 y y≈157: las bahías los esquivan (assert). RSPdx va en la bahía de expansión del suelo; HackRF Pro en «HRF» y Airspy HF+ en «AHF».
SDR_DECK2 = [["HL2", [4, 85], [125, 62, 36]], ["S1", [4, 6], [85, 26, 13]], ["S2", [4, 36], [85, 26, 13]], ["S3", [100, 6], [52, 30, 15]], ["S4", [100, 38], [52, 24, 15]], ["S5", [136, 86], [26, 60, 13]]];
DECK_FRONT = [[PL[0] + 40, PL[1] + 120], [PL[0] + 100, PL[1] + 120]];   // nudos de la rejilla
function deck_posts() = concat(DECK_FRONT, [for (p = BAND_POSTS) [PL[0] + 20 + p[0], PL[1] + BAND_Y + p[1]]]);
module bahia_x(l, w) {   // carriles en los lados largos; extremos abiertos para los conectores
    for (y = [-2, w]) translate([-2, y, 0]) cube([l + 4, 2, 6]);
    for (x = [-2, l], y = [0, w - 8]) translate([x, y, 0]) cube([2, 8, 6]);
}
module bahia(l, w) { if (l >= w) bahia_x(l, w); else translate([l, 0, 0]) rotate(90) bahia_x(w, l); }
module bandeja_sdr(lista = SDR_DECK) {
    difference() {
        union() {
            cube([DECK[0], DECK[1], DECK_T]);
            for (p = deck_posts()) translate([p[0] - DECK_O[0], p[1] - DECK_O[1], 0]) cylinder(d = 12, h = DECK_T);
            for (x = [0, DECK[0] - 2]) translate([x, 0, 0]) cube([2, DECK[1], DECK_T + 4]);   // nervios de borde
            for (y = [0, DECK[1] - 2]) translate([0, y, 0]) cube([DECK[0], 2, DECK_T + 4]);
            for (s = lista) translate([s[1][0], s[1][1], DECK_T - E]) bahia(s[2][0], s[2][1]);
        }
        for (p = deck_posts()) translate([p[0] - DECK_O[0], p[1] - DECK_O[1], -1]) cylinder(d = HOLE_M3, h = 10);
        for (s = lista) {
            l = s[2][0]; w = s[2][1]; lx = l >= w;
            // rejillas de aire bajo cada SDR
            for (k = [10 : 10 : (lx ? l : w) - 10])
                translate([s[1][0], s[1][1], -1]) if (lx) translate([k - 2, 6, 0]) cube([4, w - 12, 10]); else translate([6, k - 2, 0]) cube([l - 12, 4, 10]);
            // ranuras de brida a los dos lados de los carriles
            for (f = [0.3, 0.7]) translate([s[1][0], s[1][1], -1])
                if (lx) for (y = [-6.8, w + 2.4]) translate([l * f - 1.5, y, 0]) cube([3, 4.4, 10]);
                else for (x = [-6.8, l + 2.4]) translate([x, w * f - 1.5, 0]) cube([4.4, 3, 10]);
            translate([s[1][0] + l / 2, s[1][1] + w / 2, DECK_T - 0.5]) linear_extrude(1)
                text(s[0], size = 6, font = FONT, halign = "center", valign = "center");
        }
    }
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
// Hub USB Amazon Basics de 10 puertos con adaptador de 65 W (20 V / 3,25 A), ASIN B076YRSWGW. HUB_O = esquina del hub sobre la rejilla;
// HUB_END: holgura libre en cada extremo (enchufes USB y conectores de entrada/alimentación).
HUB = [145, 44, 23];     // PENDIENTE de medir (cifras de un anuncio de terceros, modelo HU9002V1SBL)
HUB_O = [20, 136];  HUB_END = 15;
// huecos reservados de la rejilla del módulo de electrónica: [nombre, [x, y], [ancho x, alto y, alto z]]
EL_RES = [["dongles", [12, 28], [94, 85, 13]], ["bahia", [114, 28], [100, 90, 35]], ["diplexor", [182, 132], [26, 50, 20]],
          ["wago", [90, 186], [60, 26, 10]], ["reserva", [20, 186], [60, 26, 22]]];
function res(n) = [for (s = EL_RES) if (s[0] == n) s][0];
module soporte_hub() {   // cuna ajustada al hub: dos carriles largos y extremos abiertos; dos ranuras para bridas
    l = HUB[0] + 4;  w = HUB[1] + 8;
    difference() {
        union() {
            base_rejilla(l, w);
            for (y = [0, w - 2]) translate([0, y, 0]) cube([l, 2, 8]);
        }
        for (x = [l * 0.3, l * 0.7]) translate([x - 1.5, -1, 4]) cube([3, w + 2, 2]);
    }
}
module soporte_sdrplay() { soporte_dongle(100, 100); }               // RSPdx/RSP1B (≈ 98 × 88 × 32)
module soporte_lilygo() { soporte_dongle(29, 70); }
module soporte_rak() { soporte_dongle(32, 64); }                     // RAK19007 (30 × 60) con RAK4631 y GPS
module soporte_wago() {   // 3 WAGO 221-415 en línea (bus de 12 V y masa)
    difference() { union() { base_rejilla(70, 26); translate([5, 3, 0]) cube([60, 20, 8]); } translate([7, 5, 3]) cube([56, 16, 10]); for (x = [20, 40, 60]) translate([x - 1.4, -1, 5]) cube([2.8, 30, 2]); }
}
module tapon_n() {   // la cabeza cubre la punta de la gota (radio ≈ 0,71 · N_HOLE): sin ello el agua entra por la punta bajo la cabeza
    difference() { union() { cylinder(d = N_HOLE * 1.42 + 2, h = 2); cylinder(d = N_HOLE - 0.4, h = T + 4); } translate([0, 0, 2]) cylinder(d = N_HOLE - 4, h = 10); }
}
module tapon_pg(d = 12.7, resp = RESPIRO) {   // con resp = true lleva orificio BREATH_D: pega por dentro un disco de membrana ePTFE de BREATH_MEMB
    difference() {
        union() { cylinder(d = d * 1.42 + 2, h = 2); cylinder(d = d - 0.4, h = T + 4); }
        translate([0, 0, 2]) cylinder(d = d - 4, h = 10);
        if (resp) translate([0, 0, -1]) cylinder(d = BREATH_D, h = 5);
    }
}

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

// -------------------- módulo SAI (batería + placa) --------------------
// Coordenadas sobre la rejilla (0,0 = esquina inferior izquierda de placa_rejilla):
// [nombre, [x, y], [ancho x, alto y, fondo z]] = hueco reservado (pieza impresa + componente).
// Medidas por defecto de un SAI de 600 VA: batería 12 V 7–9 Ah (151 × 65 × 94 + bornes),
// placa ≈ 210 × 70 mm, transformador EI ≈ 80 × 62 × 65 y filtros EMI de chasis 85 × 50 × 30.
SAI_BAT = [151, 100, 65];          // ancho × alto con bornes × fondo (de pie, bornes arriba)
SAI_PCB = [210, 70];               // largo × alto de la placa del SAI (medir la tuya)
SAI_TRAFO = [80, 62, 65];
FILTRO = [85, 50, 30];             // filtro EMI monofásico de chasis (largo con orejas × ancho × grueso)
SAI_LAYOUT = [["BAT", [50, 4], [159, 106, 74]], ["PCB", [6, 6], [40, 216, 82]], ["TRAFO", [50, 118], [84, 70, 70]],
              ["EMI_OUT", [138, 118], [34, 86, 54]], ["EMI_IN", [176, 118], [34, 86, 54]], ["DC", [50, 194], [84, 28, 25]]];
GUIA_Y = [18, 168];                // guías de la placa del SAI (lejos de los tornillos de la rejilla)
function sai(n) = [for (s = SAI_LAYOUT) if (s[0] == n) s][0];
module nudos(o, l, w, m = 6) {     // agujeros en los nudos de la rejilla que caen dentro de la pieza
    for (x = [PITCH : PITCH : PL[2] - PITCH / 2], y = [PITCH : PITCH : PL[3] - PITCH / 2])
        if (x - o[0] > m && x - o[0] < l - m && y - o[1] > m && y - o[1] < w - m) translate([x - o[0], y - o[1], 0]) children();
}
module alivio(o) { for (b = PL_BOSS) translate([b[0] - o[0], b[1] - o[1], -1]) cylinder(d = 9, h = 3.5); }   // cabezas de la rejilla
module soporte_bateria() {   // cuna: repisa abajo, laterales con ventanas para correa de 20 mm
    s = sai("BAT"); o = s[1]; L = s[2][0]; A = s[2][1]; F = s[2][2];
    difference() {
        union() {
            cube([L, A, 3]);
            cube([L, 4, F]);                                                        // repisa (aguanta el peso)
            translate([0, 4, F - 3]) cube([L, 10, 3]);                              // labio delantero
            for (x = [0, L - 3]) cube([3, A, F]);                                   // laterales
            for (x = [L / 3, 2 * L / 3]) translate([x - 1.5, 0, 0]) cube([3, 4, F]);   // nervios bajo la repisa
        }
        for (y = [22, 66]) translate([-1, y, F - 6.5]) cube([L + 2, 22, 3.5]);     // ventanas de la correa
        nudos(o, L, A) { translate([0, 0, -1]) cylinder(d = HOLE_M3, h = 5); translate([0, 0, 1.2]) cylinder(d = 6.5, h = 3); }
        alivio(o);
        for (x = [20 : 20 : L - 20]) translate([x - 4, 20, -1]) cube([8, A - 40, 5]);   // aire y peso
        translate([L / 2, A / 2, 2.5]) linear_extrude(1) text("BATERÍA 12 V · Pb", size = 6, font = FONT, halign = "center", valign = "center");
    }
}
module guia_pcb() {   // dos por placa: la placa del SAI va de canto (cara de componentes hacia +X)
    difference() {
        union() { cube([40, 40, 3]); translate([2, 0, 0]) cube([8, 40, 14]); }
        translate([6 - 1.1, -1, 6]) cube([2.2, 42, 10]);                           // ranura de la placa (1,6 mm)
        translate([-1, 20, 10]) rotate([0, 90, 0]) cylinder(d = 2.5, h = 12);      // prisionero M3 lateral
        for (x = [14, 34]) hull() for (y = [8, 32]) translate([x, y, -1]) cylinder(d = HOLE_M3, h = 5);
    }
}
module pletina_trafo() {   // pletina con repisa; colisos M5 para las patas del transformador
    s = sai("TRAFO"); o = s[1]; L = s[2][0]; A = s[2][1];
    difference() {
        union() { cube([L, A, 5]); cube([L, 5, 40]); for (x = [0, L - 4]) translate([x, 0, 0]) cube([4, 20, 40]); }
        for (y = [12, 52]) hull() for (x = [12, L - 12]) translate([x, y, -1]) cylinder(d = HOLE_M5, h = 7);
        nudos(o, L, A) { translate([0, 0, -1]) cylinder(d = HOLE_M3, h = 7); translate([0, 0, 3]) cylinder(d = 6.5, h = 3); }
        alivio(o);
    }
}
module soporte_filtro() {   // escuadra: el filtro EMI se atornilla por sus orejas a la pared vertical
    s = sai("EMI_OUT"); L = s[2][0]; A = s[2][1]; F = s[2][2];
    difference() {
        union() { cube([L, A, 3]); translate([L - 4, 0, 0]) cube([4, A, F]); translate([L - 14, 0, 0]) cube([10, 4, 20]); translate([L - 14, A - 4, 0]) cube([10, 4, 20]); }
        for (y = [A / 2 - FILTRO[0] / 2 + 5, A / 2 + FILTRO[0] / 2 - 5]) hull() for (dy = [-4, 4]) translate([L - 5, y + dy, F / 2]) rotate([0, 90, 0]) cylinder(d = HOLE_M4, h = 6);
        for (y = [22, 42, 62, 82]) hull() for (dx = [14, 26]) translate([dx, y, -1]) cylinder(d = HOLE_M3, h = 5);   // nudos x = 20 (OUT) y 22 (IN)
    }
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
MAST_D = 50;   // Ø de la sección donde se sujeta la caja: la INFERIOR del telescópico (50 × 2 mm, PENDIENTE de medir; = TRAMOS[0] en tools/mastil.py)
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
CAM_SX = CAM_PC[0] / 2 + CAM_FRAME / 2;  CAM_MOD = CAM_PCB;
CAM_VIS_Y = CAM_WIN[1] / 2 + 11;   // cara interior del goterón superior, medida desde el eje del objetivo
CAM_VIS_V = 18;  CAM_VIS_S = 11;   // altura del goterón superior y de las mejillas laterales sobre la tapa
CAM_VIS_WIN = [CAM_WIN[0] + 8, CAM_WIN[1] + 8];   // la visera (3 mm) eleva el borde a d + 3: abertura mayor para no recortar el campo
CAM_SOP_H = 3 + CAM_BOSS_H + CAM_PCB[2] - CAM_LENS_Z - CAM_FRAME_H;   // altura del soporte: placa base + columnas hasta el collar de la tapa
module visera() {
    vw = 2 * CAM_SX + 14; vh = CAM_VIS_Y + 3;
    difference() {
        union() {
            translate([-vw / 2, -vh, 0]) cube([vw, 2 * vh, 3]);
            translate([-vw / 2, CAM_VIS_Y, 0]) cube([vw, 3, CAM_VIS_V]);   // goterón: no entra en el campo de 67°
            for (s = [-1, 1]) translate([s * (vw / 2 - 1.5) - 1.5, -vh, 0]) cube([3, 2 * vh, CAM_VIS_S]);   // mejillas: no entran en el de 102°
        }
        translate([-CAM_VIS_WIN[0] / 2, -CAM_VIS_WIN[1] / 2, -1]) cube([CAM_VIS_WIN[0], CAM_VIS_WIN[1], 10]);
        for (s = [-1, 1]) translate([s * CAM_SX, -8, -1]) cylinder(d = HOLE_M3, h = 10);
    }
}
module soporte_camara() {   // placa base + 4 postes M2 para la placa de 25 × 24 + 2 columnas M3 al collar de la tapa
    L = 2 * CAM_SX + 10;
    difference() {
        union() {
            translate([-L / 2, -CAM_PCB[1] / 2 - 2, 0]) cube([L, CAM_PCB[1] + 4, 3]);
            for (s = [-1, 1]) translate([s * CAM_SX, 8, 0]) cylinder(d = 7, h = CAM_SOP_H);
            for (sx = [-1, 1], sy = [-1, 1]) translate([sx * CAM_HOLES[0] / 2, sy * CAM_HOLES[1] / 2, 0]) cylinder(d = 6, h = 3 + CAM_BOSS_H);
        }
        for (s = [-1, 1]) translate([s * CAM_SX, 8, -1]) cylinder(d = HOLE_M3, h = CAM_SOP_H + 2);
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * CAM_HOLES[0] / 2, sy * CAM_HOLES[1] / 2, 3 + CAM_BOSS_H - 5]) cylinder(d = CAM_M2_INS ? 3.2 : 1.8, h = 6);
        translate([-6, -9, -1]) cube([12, 18, 10]);   // paso del cable plano (15 pines) y ventilación
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
        ghost("dimgray") translate([PL[0] + HUB_O[0], PL[1] + HUB_O[1], pz]) cube(HUB);         // hub USB Amazon Basics de 10 puertos
        dx = res("diplexor"); ghost("silver") translate([PL[0] + dx[1][0], PL[1] + dx[1][1], pz]) cube(dx[2]);   // diplexor HF/VHF
        wg = res("wago"); ghost("orange") translate([PL[0] + wg[1][0], PL[1] + wg[1][1], pz]) cube(wg[2]);       // WAGO 12 V
        rs = res("reserva"); ghost("firebrick") translate([PL[0] + rs[1][0], PL[1] + rs[1][1], pz]) cube(rs[2]); // reserva: fusibles ATO por carril + reductores 12→5 V y 12→20 V (opción b del hub) + 12 V del Hermes-Lite
        // bandeja intermedia con HackRF One, RTL-SDR V4 y Airspy HF+ Discovery
        for (p = deck_posts()) color("lightyellow") translate([p[0], p[1], pz]) cylinder(d = 10, h = DECK_H);
        translate([DECK_O[0], DECK_O[1], pz + DECK_H]) {
            color("lightyellow") bandeja_sdr();
            for (s = SDR_DECK) ghost(s[0] == "HRF" ? "crimson" : s[0] == "V4" ? "steelblue" : "darkorange")
                translate([s[1][0], s[1][1], DECK_T]) cube(s[2]);
        }
        // segunda bandeja con 8 plazas de SDR más
        for (p = deck_posts()) color("lightyellow") translate([p[0], p[1], pz + DECK_H + DECK_T]) cylinder(d = 10, h = DECK2_H - DECK_H - DECK_T);
        translate([DECK_O[0], DECK_O[1], pz + DECK2_H]) {
            color("lightyellow") bandeja_sdr(SDR_DECK2);
            for (s = SDR_DECK2) ghost("mediumseagreen") translate([s[1][0], s[1][1], DECK_T]) cube(s[2]);
        }
        for (p = deck_posts()) if (p[1] > PL[1] + BAND_Y) color("lightyellow") translate([p[0], p[1], pz + DECK2_H + DECK_T]) cylinder(d = 10, h = BAND_H - DECK2_H - DECK_T);
        // bandeja
        translate([PL[0] + 20, PL[1] + BAND_Y, pz + BAND_H]) {
            color("lightyellow") bandeja();
            ghost("green") translate([PI_OFF[0], PI_OFF[1], 9]) cube([PI5[0], PI5[1], 18]);
            ghost("purple") translate([PI_OFF[0], PI_OFF[1], 29]) cube([PI5[0], PI5[1], 12]);
            ghost("royalblue") translate([99.2, 13.2, 7]) cube([27, 65, 10]);                                     // LilyGO
            ghost("teal") translate([RAK_O[0] + 1.4, RAK_O[1] + 1.4, 8]) cube([30, 60, 26]);                      // RAK19007 + RAK4631 + GPS
        }
        if (CAMARA) ghost("black") translate([CAM_C[0] - CAM_MOD[0] / 2, CAM_C[1] - CAM_MOD[1] / 2, LID_Z0 + CAM_LENS_Z - CAM_MOD[2]]) cube(CAM_MOD);
        for (f = [[0, FAN_IN], [W - T - 25, FAN_OUT]]) ghost("black") translate([f[0] == 0 ? T : f[0], f[1][0] - 30, f[1][1] - 30]) cube([25, 60, 60]);
    } else if (SAI) {
        b = sai("BAT"); translate([PL[0] + b[1][0], PL[1] + b[1][1], pz]) { color("lightyellow") soporte_bateria(); ghost("dimgray") translate([4, 4, 3]) cube(SAI_BAT); }
        p = sai("PCB");
        for (gy = GUIA_Y) color("lightyellow") translate([PL[0] + p[1][0], PL[1] + gy, pz]) guia_pcb();
        ghost("darkgreen") translate([PL[0] + p[1][0] + 5.2, PL[1] + 8, pz + 6]) cube([1.6, SAI_PCB[0], SAI_PCB[1]]);
        ghost("khaki") translate([PL[0] + p[1][0] + 7, PL[1] + 8, pz + 6]) cube([30, SAI_PCB[0], SAI_PCB[1] - 4]);   // componentes
        t = sai("TRAFO"); translate([PL[0] + t[1][0], PL[1] + t[1][1], pz]) { color("lightyellow") pletina_trafo(); ghost("sienna") translate([2, 5, 5]) cube(SAI_TRAFO); }
        for (n = ["EMI_OUT", "EMI_IN"]) { f = sai(n); translate([PL[0] + f[1][0], PL[1] + f[1][1], pz]) { color("lightyellow") soporte_filtro(); ghost("silver") translate([0, 0.5, 3]) cube([FILTRO[2], FILTRO[0], FILTRO[1]]); } }
        d = sai("DC"); ghost("orange") translate([PL[0] + d[1][0], PL[1] + d[1][1], pz]) cube(d[2]);   // fusible ATO + WAGO
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
    color("orange") translate([0, 0, LID_Z0 - GAP_LID]) junta_tapa();   // sobre el canto de la pared (z = D); 4 mm libres → 3 mm comprimida
    color("white") translate([W + 8, H, -2]) rotate([90, 0, 180]) tejadillo();
    if (EL && CAMARA && !abierta) color("white") translate([CAM_C[0], CAM_C[1], LID_Z0 + LID_T]) visera();
    if (EL) {
        color("white") translate([-30, FAN_IN[0], FAN_IN[1]]) rotate([0, -90, 0]) rotate(90) translate([0, 0, -30]) capota();
        color("white") translate([W + 30, FAN_OUT[0], FAN_OUT[1]]) rotate([0, 90, 0]) rotate(-90) translate([0, 0, -30]) capota();
    }
    componentes();
}

// comprobaciones de intemperie (fallan al exportar si se cambian medidas y se pierde estanqueidad)
assert(T >= 3.2, "pared < 3,2 mm: el ASA exterior necesita ≥ 8 perímetros de 0,4");
assert(GASKET_COMP >= 0.20 && GASKET_COMP <= 0.30, "compresión de la junta fuera de 20–30 %");
assert(GASKET_W < GROOVE_W, "la junta debe ser más estrecha que la ranura para ensancharse");
assert(SKIRT_H - GAP_LID >= 8, "el faldón de la tapa solapa < 8 mm sobre la pared");
assert(DRIP_OUT >= 1, "el faldón debe sobresalir ≥ 1 mm para gotear");
assert(BELT_TOP >= SKIRT_H - GAP_LID + 1, "el remate de la caja toca el faldón de la tapa");
assert(H + 2 * LID_OFF <= 250 && W + 2 * (EAR_L + 0.5) <= 250, "la tapa no cabe en 250 mm");
assert(CAM_WIN[0] >= 2 * CAM_D * tan(CAM_FOV_H / 2) + CAM_LENS_D && CAM_WIN[1] >= 2 * CAM_D * tan(CAM_FOV_V / 2) + CAM_LENS_D, "la ventana de la cámara recorta el campo de 102° × 67°");
assert(CAM_VIS_WIN[0] >= 2 * (CAM_D + 3) * tan(CAM_FOV_H / 2) + CAM_LENS_D && CAM_VIS_WIN[1] >= 2 * (CAM_D + 3) * tan(CAM_FOV_V / 2) + CAM_LENS_D, "la abertura de la visera recorta el campo de la cámara");
assert((CAM_D + CAM_VIS_V) * tan(CAM_FOV_V / 2) <= CAM_VIS_Y - CAM_LENS_D / 2, "el goterón de la visera entra en el campo vertical de 67°");
assert((CAM_D + CAM_VIS_S) * tan(CAM_FOV_H / 2) <= CAM_SX + 7 - 3 - CAM_LENS_D / 2, "las mejillas de la visera entran en el campo horizontal de 102°");
assert(CAM_LENS_Z > 0 && abs(CAM_VID_T + CAM_GAP + CAM_LENS_Z - LID_T) < 1e-6 && CAM_SOP_H >= 3 + CAM_BOSS_H + 2, "cotas de la cámara incoherentes");
assert(CAM_PC[0] >= CAM_PCB[0] + 1 && CAM_PC[1] >= CAM_PCB[1] + 1 && CAM_GL[1] / 2 + 2 <= CAM_PC[1] / 2 + CAM_FRAME, "la cavidad de la placa o el rebaje del cristal no caben en el collar");
assert(ROOF_W <= 250 && ROOF_L / cos(ROOF_A) <= 250, "el tejadillo no cabe en 250 mm");
assert(DRAIN_D >= 3 && DRAIN_D <= 4, "orificio de drenaje fuera de 3–4 mm (menos se tapa, más deja pasar insectos)");
assert(BREATH_MEMB <= 12.7 - 4, "la membrana no cabe en el hueco del tapón PG7");
// comprobaciones de holgura (fallan al exportar si se cambian medidas y algo deja de caber)
if (EL) {
    for (s = SDR_DECK) assert(s[1][0] >= 4 && s[1][1] >= 4 && s[1][0] + s[2][0] <= DECK[0] - 4 && s[1][1] + s[2][1] <= DECK[1] - 4, str("SDR fuera de la bandeja_sdr: ", s[0]));
    assert(DECK_H + DECK_T + max([for (s = SDR_DECK) s[2][2]]) + 4 <= BAND_H, "los SDR tocan la bandeja de la Pi");
    for (s = SDR_DECK2) assert(s[1][0] >= 4 && s[1][1] >= 4 && s[1][0] + s[2][0] <= DECK[0] - 4 && s[1][1] + s[2][1] <= DECK[1] - 4, str("SDR fuera de la bandeja_sdr2: ", s[0]));
    assert(DECK_H + DECK_T + max([for (s = SDR_DECK) s[2][2]]) + 4 <= DECK2_H, "los SDR de la bandeja 1 tocan la bandeja 2");
    assert(DECK2_H + DECK_T + max([for (s = SDR_DECK2) s[2][2]]) + 4 <= BAND_H, "los SDR de la bandeja 2 tocan la bandeja de la Pi");
    for (a = SDR_DECK2, b = SDR_DECK2) if (a[0] < b[0])
        assert(max(b[1][0] - a[1][0] - a[2][0], a[1][0] - b[1][0] - b[2][0], b[1][1] - a[1][1] - a[2][1], a[1][1] - b[1][1] - b[2][1]) >= 2, str("se solapan en la bandeja 2: ", a[0], " y ", b[0]));
    for (s = SDR_DECK2, p = deck_posts()) assert(!(p[0] - DECK_O[0] + 6 > s[1][0] - 2 && p[0] - DECK_O[0] - 6 < s[1][0] + s[2][0] + 2 && p[1] - DECK_O[1] + 6 > s[1][1] - 2 && p[1] - DECK_O[1] - 6 < s[1][1] + s[2][1] + 2), str("una bahía de la bandeja 2 pisa un poste: ", s[0]));
    assert(RAK_O[0] + RAK_C[0] <= BAND[0] - 5 && RAK_O[1] + RAK_C[1] <= BAND[1] - 8, "la cuna RAK se sale de la bandeja");
    assert(T + STANDOFF + PL_T + BAND_H + 41 <= D + GAP_LID - RIB_H, "la Pi + HAT toca la tapa");
    assert(GL_Z + 25.4 / 2 + 8 <= D, "los prensaestopas no caben en la cara inferior");
    // hub USB: zona = hub + HUB_END libre en cada extremo (x) y 4 mm de cuna a cada lado (y); no pisa nada de la rejilla
    hz = [HUB_O[0] - HUB_END, HUB_O[1] - 4, HUB[0] + 2 * HUB_END, HUB[1] + 8];
    assert(HUB_END >= 15, "el hub necesita ≥ 15 mm libres en cada extremo (USB y conectores)");
    assert(hz[0] >= 2 && hz[1] >= 2 && hz[0] + hz[2] <= PL[2] - 2 && hz[1] + hz[3] <= PL[3] - 2, "el hub USB se sale de la rejilla");
    for (r = EL_RES) assert(max(r[1][0] - hz[0] - hz[2], hz[0] - r[1][0] - r[2][0], r[1][1] - hz[1] - hz[3], hz[1] - r[1][1] - r[2][1]) >= 1, str("el hub USB pisa el hueco: ", r[0]));
    for (p = deck_posts()) assert(max(p[0] - PL[0] - 6 - hz[0] - hz[2], hz[0] - (p[0] - PL[0] + 6), p[1] - PL[1] - 6 - hz[1] - hz[3], hz[1] - (p[1] - PL[1] + 6)) >= 0, "el hub USB pisa un poste de las bandejas");
    // zonas de los ventiladores sobre la rejilla (entrada x ≤ 22, y 18–78; salida x 192,8–217,8, y 153,4–213,4)
    for (f = [[-3, FAN_IN[0] - 30 - PL[1], 25, 60], [W - T - 25 - PL[0], FAN_OUT[0] - 30 - PL[1], 25, 60]])
        assert(max(f[0] - hz[0] - hz[2], hz[0] - f[0] - f[2], f[1] - hz[1] - hz[3], hz[1] - f[1] - f[3]) >= 1, "el hub USB pisa la zona de un ventilador");
    assert(T + STANDOFF + PL_T + res("diplexor")[2][2] <= FAN_OUT[1] - 30, "el diplexor toca el ventilador de salida");
    assert(DECK_H >= HUB[2] + 3 + 4, "el hub USB toca la bandeja de SDR");
}
if (SAI) {
    for (s = SAI_LAYOUT) assert(s[1][0] >= 2 && s[1][1] >= 2 && s[1][0] + s[2][0] <= PL[2] - 2 && s[1][1] + s[2][1] <= PL[3] - 2, str("fuera de la rejilla: ", s[0]));
    for (i = [0 : len(SAI_LAYOUT) - 2], j = [i + 1 : len(SAI_LAYOUT) - 1]) let(a = SAI_LAYOUT[i], b = SAI_LAYOUT[j])
        assert(max(b[1][0] - a[1][0] - a[2][0], a[1][0] - b[1][0] - b[2][0], b[1][1] - a[1][1] - a[2][1], a[1][1] - b[1][1] - b[2][1]) >= 4, str("se solapan: ", a[0], " y ", b[0]));
    assert(T + STANDOFF + PL_T + max([for (s = SAI_LAYOUT) s[2][2]]) <= D + GAP_LID - RIB_H, "el SAI toca la tapa");
    assert(SAI_BAT[0] + 8 <= sai("BAT")[2][0] && SAI_BAT[1] + 4 <= sai("BAT")[2][1] && SAI_BAT[2] + 3 <= sai("BAT")[2][2] - 6, "la batería no cabe en la cuna");
    assert(SAI_PCB[0] <= sai("PCB")[2][1] - 4 && SAI_PCB[1] + 6 <= sai("PCB")[2][2], "la placa del SAI no cabe");
    assert(SAI_TRAFO[0] + 4 <= sai("TRAFO")[2][0] && SAI_TRAFO[1] + 5 <= sai("TRAFO")[2][1] && SAI_TRAFO[2] + 5 <= sai("TRAFO")[2][2], "el transformador no cabe");
    assert(FILTRO[2] <= sai("EMI_IN")[2][0] - 4 && FILTRO[0] <= sai("EMI_IN")[2][1] && FILTRO[1] + 3 <= sai("EMI_IN")[2][2], "el filtro EMI no cabe");
}

if (PART == "montaje") rotate([90, 0, 0]) montaje();
else if (PART == "interior") rotate([90, 0, 0]) montaje(true);
else if (PART == "cuerpo") cuerpo();
else if (PART == "tapa") translate([0, H, LID_Z0 + LID_T]) rotate([180, 0, 0]) tapa();
else if (PART == "tejadillo") rotate([180, 0, 0]) rotate([ROOF_A, 0, 0]) tejadillo();
else if (PART == "placa_rejilla") placa_rejilla();
else if (PART == "bandeja") bandeja();
else if (PART == "poste_bandeja") poste_bandeja();
else if (PART == "bandeja_sdr") bandeja_sdr();
else if (PART == "bandeja_sdr2") bandeja_sdr(SDR_DECK2);
else if (PART == "poste_medio") poste_medio();
else if (PART == "soporte_rak") soporte_rak();
else if (PART == "vista_sdr2") { color("lightyellow") bandeja_sdr(SDR_DECK2); for (s = SDR_DECK2) ghost("mediumseagreen") translate([s[1][0], s[1][1], DECK_T]) cube(s[2]); }
else if (PART == "vista_sdr") { color("lightyellow") bandeja_sdr(); for (s = SDR_DECK) ghost(s[0] == "HRF" ? "crimson" : s[0] == "V4" ? "steelblue" : "darkorange") translate([s[1][0], s[1][1], DECK_T]) cube(s[2]); }
else if (PART == "poste_superior") poste_superior();
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
else if (PART == "soporte_bateria") soporte_bateria();
else if (PART == "guia_pcb") guia_pcb();
else if (PART == "pletina_trafo") pletina_trafo();
else if (PART == "soporte_filtro") soporte_filtro();
else if (PART == "visera") visera();
else if (PART == "soporte_camara") soporte_camara();
// vistas de documentación (solo para render del manual 52; no afectan a los STL)
else if (PART == "vista_despiece_v3_electronica") v3_caja(V_EX);
else if (PART == "vista_montado_v3_electronica") v3_caja(0);
else if (PART == "vista_despiece_v3_potencia") v3_potencia(V_EX);
else if (PART == "vista_montado_v3_potencia") v3_potencia(0);
else if (PART == "vista_despiece_v3_sai") v3_sai(V_EX);
else if (PART == "vista_montado_v3_sai") v3_sai(0);
else if (PART == "vista_despiece_v3_postes_bandejas") v3_postes(V_EX);
else if (PART == "vista_montado_v3_postes_bandejas") v3_postes(0);
else if (PART == "vista_despiece_v3_soportes") v3_soportes(V_EX);
else if (PART == "vista_montado_v3_soportes") v3_soportes(0);
else if (PART == "vista_despiece_v3_ventilacion") v3_ventilacion(V_EX);
else if (PART == "vista_montado_v3_ventilacion") v3_ventilacion(0);
else if (PART == "vista_despiece_v3_camara") v3_camara(V_EX);
else if (PART == "vista_montado_v3_camara") v3_camara(0);
else if (PART == "vista_despiece_v3_tapones") v3_tapones(V_EX);
else if (PART == "vista_montado_v3_tapones") v3_tapones(0);

// ---------------- VISTAS DE DOCUMENTACIÓN (solo lectura) ----------------
V_ORANGE = "#F26B1D"; V_INK = "#23272B"; V_GREY = "#59636B"; V_LIGHT = "#C9CED3";
V_EX = 50;          // separación del despiece (mm)
function v_dir(a) = a == "x" ? [1, 0, 0] : a == "-x" ? [-1, 0, 0] : a == "y" ? [0, 1, 0] : a == "-y" ? [0, -1, 0] : a == "-z" ? [0, 0, -1] : [0, 0, 1];
function v_rot(a) = a == "x" ? [0, 90, 0] : a == "-x" ? [0, -90, 0] : a == "y" ? [-90, 0, 0] : a == "-y" ? [90, 0, 0] : a == "-z" ? [180, 0, 0] : [0, 0, 0];
// línea guía fina entre dos puntos
module v_guia(a, b, d = 0.8) { color("dimgray") hull() { translate(a) sphere(d = d, $fn = 8); translate(b) sphere(d = d, $fn = 8); } }
// tornillo: la punta queda en mate + off·out; el cuerpo y la cabeza se extienden hacia «out»
module v_scr(mate, out, L, d, off = 0, head = true) {
    p = mate + v_dir(out) * off;
    color("silver") translate(p) rotate(v_rot(out)) {
        cylinder(d = d, h = L, $fn = 16);
        if (head) translate([0, 0, L]) cylinder(d = 1.75 * d, h = 0.8 * d, $fn = 24);
    }
    if (off > 0) v_guia(mate, p);
}

// cierre de la caja: cuerpo, junta, tapa, rejilla, tejadillo y pletinas de pared
module v3_caja(ex) {
    sj = 0.5 * ex; sl = ex; sp = 0.3 * ex; sr = 0.5 * ex; sg = 0.5 * ex;
    color(V_ORANGE) cuerpo();
    color(V_INK) translate([0, 0, LID_Z0 - GASKET_H + sj]) junta_tapa();
    color(V_GREY) translate([0, 0, sl]) tapa();
    color(V_LIGHT) translate([PL[0], PL[1], T + STANDOFF + sp]) placa_rejilla();
    color(V_GREY) translate([W + 8, H + sr, -2]) rotate([90, 0, 180]) tejadillo();
    // pletinas de pared: apoyan en los nervios de la espalda (6 mm) y se atornillan (M5) a sus insertos
    for (y = WALL_Y) {
        color(V_LIGHT) translate([W * 0.25, y, -14 - sg]) pletina_pared();
        if (ex > 0) for (x = [W * 0.25, W * 0.75]) v_guia([x, y, -6], [x, y, -6 - sg]);
    }
    if (ex > 0) for (q = [[W / 2, T / 2], [W / 2, H - T / 2], [T / 2, H / 2], [W - T / 2, H / 2]])
        v_guia([q[0], q[1], D], [q[0], q[1], LID_Z0 + sl - RIB_H]);   // junta <-> ranura
    // tapa: M4 a las orejetas
    for (y = EARS_Y, xs = [-1, 1]) {
        x = xs < 0 ? -EAR_L / 2 - 0.5 : W + EAR_L / 2 + 0.5;
        v_scr([x, y, LID_Z0 + LID_T - 16], "z", 16, 4, ex > 0 ? sl + 26 : 0);
    }
    // rejilla: M3 a los pilares (longitud = espesor + inserto)
    for (b = PL_BOSS)
        v_scr([PL[0] + b[0], PL[1] + b[1], T + STANDOFF - INS_M3_L], "z", PL_T + INS_M3_L, 3, ex > 0 ? PL_T + INS_M3_L + sp + 10 : 0);
    // tejadillo: M4 desde arriba (longitud derivada de la altura de cada pilar)
    for (p = ROOF_PILLARS)
        v_scr([p[0], H - INS_M4_L, p[1]], "y", roof_z(p[1] + 2) + 4 + INS_M4_L, 4, ex > 0 ? roof_z(p[1] + 2) + 4 + sr + 10 + INS_M4_L : 0);
}

// envolvente de los módulos de potencia y SAI: cuerpo opaco; junta (30), tapa (60) y tejadillo (90) hacia +Z;
// pletina de pared y silla de mástil hacia atrás (-Z) con sus M5; tapón PG del prensaestopas de reserva sobre su eje (-Y)
module v3_envolvente(ex, gl, ip) {
    sj = 0.6 * ex; sl = 1.2 * ex; sr = 1.8 * ex; sg = 0.5 * ex;
    color(V_ORANGE) cuerpo();
    color(V_INK) translate([0, 0, LID_Z0 - GASKET_H + sj]) junta_tapa();
    color(V_GREY) translate([0, 0, sl]) tapa();
    color(V_GREY) translate([W + 8, H, -2 + sr]) rotate([90, 0, 180]) tejadillo();
    if (ex > 0) for (q = [[W / 2, T / 2], [W / 2, H - T / 2], [T / 2, H / 2], [W - T / 2, H / 2]])
        v_guia([q[0], q[1], D], [q[0], q[1], LID_Z0 + sl - RIB_H]);   // junta <-> ranura
    // tapa: M4 a las orejetas (la guía va del inserto de la orejeta al agujero de la tapa)
    for (y = EARS_Y, xs = [-1, 1]) {
        x = xs < 0 ? -EAR_L / 2 - 0.5 : W + EAR_L / 2 + 0.5;
        v_scr([x, y, LID_Z0 + LID_T - 16], "z", 16, 4, ex > 0 ? sl + 26 : 0);
    }
    // tejadillo: M4 en sus agujeros, elevados con él; la guía baja hasta el inserto del pilar
    for (p = ROOF_PILLARS) {
        v_scr([p[0], H - INS_M4_L, p[1] + sr], "y", roof_z(p[1] + 2) + 4 + INS_M4_L, 4);
        if (ex > 0) v_guia([p[0], H - INS_M4_L, p[1]], [p[0], H - INS_M4_L, p[1] + sr]);
    }
    // pletina de pared (y bajo) y silla de mástil (y alto) en los insertos M5 de la espalda
    for (x = [W * 0.25, W * 0.75]) {
        v_scr([x, WALL_Y[0], 4], "-z", 18, 5, ex > 0 ? sg + 24 : 0);
        v_scr([x, WALL_Y[1], 4], "-z", 22, 5, ex > 0 ? sg + 44 : 0);
    }
    color(V_LIGHT) translate([W * 0.25, WALL_Y[0], -14 - sg]) pletina_pared();
    color(V_GREY) translate([W / 2, WALL_Y[1], -6 - sg]) rotate([180, 0, 0]) soporte_mastil();
    // tapón PG en el prensaestopas de reserva
    tot = sum_w(gl, len(gl) - 1) + 8 * (len(gl) - 1);
    gx = W / 2 - tot / 2 + sum_w(gl, ip - 1) + 8 * ip + gl[ip][1] / 2;
    color(V_INK) translate([gx, -2 - ex, 40]) rotate([-90, 0, 0]) tapon_pg(gl[ip][1]);
    if (ex > 0) v_guia([gx, -2, 40], [gx, -2 - ex, 40]);
}

// rejilla de fondo con sus M3 a los pilares del cuerpo; lp = elevación de la capa interior
module v3_rejilla_capa(ex, lp) {
    color(V_LIGHT) translate([PL[0], PL[1], T + STANDOFF + lp]) placa_rejilla();
    for (b = PL_BOSS)
        v_scr([PL[0] + b[0], PL[1] + b[1], T + STANDOFF - INS_M3_L], "z", PL_T + INS_M3_L, 3, ex > 0 ? lp + PL_T + INS_M3_L + 10 : 0);
}

// módulo de potencia: soporte Schuko con la base, brida del cargador, todo atornillado a la rejilla (M3)
module v3_potencia(ex) {
    lp = ex > 0 ? D + 1 - (T + STANDOFF) : 0;   // la capa interior sale por la boca abierta
    s1 = 0.1 * ex; s2 = 0.2 * ex; pz = T + STANDOFF + PL_T + lp;
    v3_envolvente(ex, GLANDS_P, 2);
    v3_rejilla_capa(ex, lp);
    cx = W / 2; cy = 30 + SCHUKO[1] / 2;
    color(V_ORANGE) translate([cx, cy, pz + s1]) soporte_schuko();
    color("white", 0.6) translate([cx - SCHUKO[0] / 2, 30, pz + 4 + s2]) cube(SCHUKO);
    for (sx = [-1, 1], sy = [-1, 1])
        v_scr([cx + sx * (SCHUKO[0] / 2 + 3), cy + sy * (SCHUKO[1] / 2 + 3), pz - PL_T], "z", 4 + PL_T, 3, ex > 0 ? s1 + 12 : 0);
    if (ex > 0) for (sx = [-1, 1]) v_guia([cx + sx * 30, cy, pz + 4 + s1], [cx + sx * 30, cy, pz + 4 + s2]);   // tornillos de la base Schuko
    // brida del cargador: delante de la base, fijada a la rejilla por los dos agujeros M3 de sus extremos
    bo = [W / 2 - 55, 112];
    color(V_GREY) translate([bo[0], bo[1], pz + 0.3 * ex]) brida_cargador();
    if (ex > 0) for (x = [5, 105]) v_guia([bo[0] + x, bo[1] + 8, pz], [bo[0] + x, bo[1] + 8, pz + 0.3 * ex]);
}

// módulo SAI: soportes sobre la rejilla y componentes encima (disposición y longitud de tornillos orientativas)
module v3_sai(ex) {
    lp = ex > 0 ? D + 1 - (T + STANDOFF) : 0;   // la capa interior sale por la boca abierta
    s1 = 0.1 * ex; s2 = 0.2 * ex; pz = T + STANDOFF + PL_T + lp;
    v3_envolvente(ex, GLANDS_S, 2);
    v3_rejilla_capa(ex, lp);
    b = sai("BAT");
    color(V_ORANGE) translate([PL[0] + b[1][0], PL[1] + b[1][1], pz + s1]) soporte_bateria();
    color("dimgray", 0.6) translate([PL[0] + b[1][0] + 4, PL[1] + b[1][1] + 4, pz + 3 + s2]) cube(SAI_BAT);
    translate([PL[0] + b[1][0], PL[1] + b[1][1], pz]) nudos(b[1], b[2][0], b[2][1]) v_scr([0, 0, 1.2 - 6], "z", 6, 3, ex > 0 ? s1 + 30 : 0);
    p = sai("PCB");
    for (gy = GUIA_Y) {
        color(V_GREY) translate([PL[0] + p[1][0], PL[1] + gy, pz + s1]) guia_pcb();
        for (x = [14, 34]) v_scr([PL[0] + p[1][0] + x, PL[1] + gy + 20, pz - PL_T], "z", 3 + PL_T, 3, ex > 0 ? s1 + 14 : 0);
    }
    color("darkgreen", 0.7) translate([PL[0] + p[1][0] + 5.2, PL[1] + 8, pz + 6 + s2]) cube([1.6, SAI_PCB[0], SAI_PCB[1]]);
    if (ex > 0) for (gy = GUIA_Y) v_guia([PL[0] + p[1][0] + 6, PL[1] + gy + 20, pz + 6 + s1], [PL[0] + p[1][0] + 6, PL[1] + gy + 20, pz + 6 + s2]);
    t = sai("TRAFO");
    color(V_LIGHT) translate([PL[0] + t[1][0], PL[1] + t[1][1], pz + s1]) pletina_trafo();
    color("sienna", 0.6) translate([PL[0] + t[1][0] + 2, PL[1] + t[1][1] + 5, pz + 5 + s2]) cube(SAI_TRAFO);
    translate([PL[0] + t[1][0], PL[1] + t[1][1], pz]) nudos(t[1], t[2][0], t[2][1]) v_scr([0, 0, 3 - 6], "z", 6, 3, ex > 0 ? s1 + 30 : 0);
    for (n = ["EMI_OUT", "EMI_IN"]) {
        f = sai(n);
        color(V_GREY) translate([PL[0] + f[1][0], PL[1] + f[1][1], pz + s1]) soporte_filtro();
        color("silver", 0.6) translate([PL[0] + f[1][0], PL[1] + f[1][1] + 0.5, pz + 3 + s2]) cube([FILTRO[2], FILTRO[0], FILTRO[1]]);
    }
}

// columnas de bandejas del módulo de electrónica (de la rejilla a la bandeja de la Pi)
module v3_postes(ex) {
    k = 0.45 * ex; pz = T + STANDOFF + PL_T; Ls = DECK_T + INS_M3_L; offs = ex > 0 ? DECK_T + k + 8 + INS_M3_L : 0;
    color(V_LIGHT) translate([PL[0], PL[1], T + STANDOFF]) placa_rejilla();
    for (p = deck_posts()) {
        color(V_GREY) translate([p[0], p[1], pz + k]) cylinder(d = 10, h = DECK_H);
        color(V_GREY) translate([p[0], p[1], pz + DECK_H + DECK_T + 3 * k]) cylinder(d = 10, h = DECK2_H - DECK_H - DECK_T);
        if (ex > 0) v_guia([p[0], p[1], pz], [p[0], p[1], pz + DECK2_H + 4 * k + DECK_T]);
        v_scr([p[0], p[1], pz + DECK_H - INS_M3_L + k], "z", Ls, 3, offs);
        v_scr([p[0], p[1], pz + DECK2_H - INS_M3_L + 3 * k], "z", Ls, 3, offs);
    }
    // columna superior: solo bajo la bandeja de la Pi (4 postes)
    for (p = BAND_POSTS) {
        q = [PL[0] + 20 + p[0], PL[1] + BAND_Y + p[1]];
        color(V_GREY) translate([q[0], q[1], pz + DECK2_H + DECK_T + 5 * k]) cylinder(d = 10, h = BAND_H - DECK2_H - DECK_T);
        if (ex > 0) v_guia([q[0], q[1], pz + DECK2_H + DECK_T], [q[0], q[1], pz + BAND_H + 6 * k]);
        v_scr([q[0], q[1], pz + BAND_H - INS_M3_L + 5 * k], "z", Ls, 3, offs);
    }
    color(V_ORANGE) translate([DECK_O[0], DECK_O[1], pz + DECK_H + 2 * k]) bandeja_sdr();
    color(V_ORANGE) translate([DECK_O[0], DECK_O[1], pz + DECK2_H + 4 * k]) bandeja_sdr(SDR_DECK2);
    color(V_ORANGE) translate([PL[0] + 20, PL[1] + BAND_Y, pz + BAND_H + 6 * k]) bandeja();
}

// cuna sobre la rejilla (o): dos M3 por los colisos de la base (l × w) hacia los insertos de la rejilla
module v_sop(o, l, w, ex, c) {
    pz = T + STANDOFF + PL_T;
    color(c) translate([PL[0] + o[0], PL[1] + o[1], pz + ex]) children();
    for (x = [10, l - 10]) v_scr([PL[0] + o[0] + x, PL[1] + o[1] + w / 2, pz - PL_T], "z", 3 + PL_T, 3, ex > 0 ? ex + 14 : 0);
}

// soportes de la rejilla del módulo de electrónica: dongles, hub USB y WAGO
module v3_soportes(ex) {
    color(V_ORANGE, 0.35) cuerpo();
    color(V_LIGHT) translate([PL[0], PL[1], T + STANDOFF]) placa_rejilla();
    v_sop(res("dongles")[1], 90, 42, 0.6 * ex, V_ORANGE) soporte_dongle(26, 90);
    v_sop([HUB_O[0] - 2, HUB_O[1] - 4], HUB[0] + 4, HUB[1] + 8, 0.6 * ex, V_GREY) soporte_hub();
    v_sop(res("wago")[1], 70, 26, 0.6 * ex, V_INK) soporte_wago();
}

// ventilación: capota (fuera) y filtro + ventilador (dentro) en la pared izquierda; la derecha es simétrica
module v3_ventilacion(ex) {
    color(V_ORANGE, 0.45) cuerpo();
    for (lado = [-1, 1]) {
        fy = lado < 0 ? FAN_IN[0] : FAN_OUT[0]; fz = lado < 0 ? FAN_IN[1] : FAN_OUT[1];
        translate([lado < 0 ? 0 : W, 0, 0]) scale([lado < 0 ? 1 : -1, 1, 1]) {
            color(V_GREY) translate([-30 - ex, fy, fz]) rotate([0, -90, 0]) rotate(90) translate([0, 0, -30]) capota();
            color(V_LIGHT) translate([T + 0.5 * ex, fy, fz]) rotate([0, 90, 0]) rejilla_ventilador();
            color("black", 0.6) translate([T + 2.4 + ex, fy - 30, fz - 30]) cube([25, 60, 60]);
            for (sx = [-1, 1], sy = [-1, 1])
                v_scr([T + 2.4 + 25 + ex, fy + sx * FAN_SCREW / 2, fz + sy * FAN_SCREW / 2], "-x", 3 + T + 2.4 + 25, 3, ex > 0 ? (T + 2.4 + 25 + ex) + 3 + ex + 10 : 0);
        }
    }
}

// cámara Module 3 Wide: tapa con cristal y visera (fuera); módulo y soporte (dentro)
module v3_camara(ex) {
    cx = CAM_C[0]; cy = CAM_C[1];
    zs = LID_Z0 - CAM_FRAME_H - CAM_SOP_H;            // cara inferior del soporte
    zb = LID_Z0 + CAM_LENS_Z - CAM_MOD[2];            // cara inferior de la placa de la cámara
    Ls = CAM_SOP_H + INS_M3_L - 1;
    color(V_GREY, ex > 0 ? 0.8 : 1) tapa();
    color("lightblue", 0.5) translate([cx - (CAM_WIN[0] + 2 * CAM_LAP) / 2, cy - (CAM_WIN[1] + 2 * CAM_LAP) / 2, LID_Z0 + LID_T - CAM_VID_T + 0.5 * ex])
        cube([CAM_WIN[0] + 2 * CAM_LAP, CAM_WIN[1] + 2 * CAM_LAP, CAM_VID_T]);
    color(V_INK) translate([cx, cy, LID_Z0 + LID_T + ex]) visera();
    color("black", 0.8) translate([cx - CAM_MOD[0] / 2, cy - CAM_MOD[1] / 2, zb - ex]) cube(CAM_MOD);
    color(V_LIGHT) translate([cx, cy, zs - 2 * ex]) soporte_camara();
    if (ex > 0) for (sx = [-1, 1], sy = [-1, 1])   // placa ↔ postes M2 del soporte
        v_guia([cx + sx * CAM_HOLES[0] / 2, cy + sy * CAM_HOLES[1] / 2, zb - ex], [cx + sx * CAM_HOLES[0] / 2, cy + sy * CAM_HOLES[1] / 2, zb - 2 * ex]);
    for (s = [-1, 1]) {
        v_scr([cx + s * CAM_SX, cy + 8, zs + Ls], "-z", Ls, 3, ex > 0 ? 2 * ex + 18 : 0);                       // M3 al inserto del collar
        v_scr([cx + s * CAM_SX, cy - 8, LID_Z0 + LID_T + 3 - 8], "z", 8, 3, ex > 0 ? ex + 18 : 0);            // M3 × 8 de la visera
    }
}

// tapones de la cara inferior (y = 0): tapón N en los pasamuros N libres y tapón PG en el prensaestopas de reserva
module v3_tapones(ex) {
    pe = ex > 0 ? 40 : 0;   // recorrido del tapón sobre el eje del agujero (-Y)
    color(V_ORANGE, 0.35) cuerpo();
    r = N_ROWS[1]; n = len(r[1]); x0 = W / 2 - (n - 1) * N_PITCH / 2;
    for (i = [4 : 6]) {
        color(V_INK) translate([x0 + i * N_PITCH, -2 - pe, r[0]]) rotate([-90, 0, 0]) tapon_n();
        if (ex > 0) v_guia([x0 + i * N_PITCH, -2, r[0]], [x0 + i * N_PITCH, -2 - pe, r[0]]);
    }
    tot = sum_w(GLANDS_E, len(GLANDS_E) - 1) + 8 * (len(GLANDS_E) - 1);
    i = 5; gx = W / 2 - tot / 2 + sum_w(GLANDS_E, i - 1) + 8 * i + GLANDS_E[i][1] / 2;
    color(V_INK) translate([gx, -2 - pe, GL_Z]) rotate([-90, 0, 0]) tapon_pg();
    if (ex > 0) v_guia([gx, -2, GL_Z], [gx, -2 - pe, GL_Z]);
}
