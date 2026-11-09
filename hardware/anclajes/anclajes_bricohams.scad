// =====================================================================
//  ANCLAJES IMPRESOS BricoHams SDR · N0CALL  (v4)
//  Todo se sujeta con tornillería M6 inox y tuercas cautivas: sin abrazaderas
//  en U. Material: ASA o PETG (exterior), 6 perímetros, 50 % de relleno giroide.
//
//  Pieza base: CRUCETA de tres piezas para unir dos tubos perpendiculares
//    (mástil vertical ↔ brazo horizontal, brazo ↔ antena, brazo ↔ tubo corto…)
//      · «cuerpo»  centro con media caña arriba (tubo A, eje X) y abajo (tubo B, eje Y)
//      · «tapa A» y «tapa B»  las otras medias cañas, 2 tornillos M6 cada una
//    Las medias cañas son 1 mm menos profundas que el radio: al apretar, aprietan.
//
//  Exportar todo: tools/anclajes.sh   ·   Vista de montaje: PART="montaje"
// =====================================================================

PART = "montaje";
$fn = 64;
E = 0.01;
FONT = "DejaVu Sans:style=Bold";

MAST_D = 40.6;        // mástil Televés Ø40 (+0,6 de holgura)
ARM_D = 25.4;         // brazo y tubos cortos de aluminio Ø25
FIBRA_D = 26.0;       // tubo de la antena de fibra 433 en la zona de amarre (MÍDELO: 20–32)
BOOM = 20.4;          // boom cuadrado 20×20 de la quad
M6 = 6.6;  NUT6 = 11.3;  NUT6_H = 5.4;      // tuerca M6 (entre caras 10 mm)
M5 = 5.5;  M3 = 3.4;  INS_M3 = 4.0;  INS_M5 = 6.4;
APRIETE = 1.0;        // cuánto menos que el radio es cada media caña

module rotulo(t, s = 5) { linear_extrude(0.8) text(t, size = s, font = FONT, halign = "center", valign = "center"); }

// canal (media caña) a lo largo de X, de diámetro d, abierto hacia +Z; perfil en gota para imprimir hacia abajo
module canal_x(d, l, cuadrado = false) {
    if (cuadrado) translate([-l / 2, -d / 2, 0]) cube([l, d, d]);
    else rotate([0, 90, 0]) cylinder(d = d, h = l, center = true);
}

// ------------------------------- CRUCETA ------------------------------
function largo_cruceta(dA, dB) = max(dA, dB) + 44;
function prof(d, cuad = false) = d / 2 - APRIETE;                         // profundidad de cada media caña
function alto_cuerpo(dA, dB) = prof(dA) + prof(dB) + 8;                   // 8 mm de alma entre las dos cañas
function grosor_tapa(d) = prof(d) + 7;
function torn(d, L) = [[-L / 2 + 9, d / 2 + 6.5], [L / 2 - 9, -(d / 2 + 6.5)]];   // en diagonal (marco de la tapa)
function tornB(d, L) = [for (p = torn(d, L)) [p[1], -p[0]]];             // los mismos, girados -90° (tubo B)

// tubo B abajo (eje Y): en gota con la punta hacia +Z para que el techo se imprima sin soportes
module canal_b(d, L) {
    rotate([0, 0, 90]) rotate([0, 90, 0]) linear_extrude(L, center = true) union() { circle(d = d); rotate(135) square(d / 2); }
}

module cruceta_cuerpo(dA, dB, cuadA = false, cuadB = false, txt = "") {
    L = largo_cruceta(dA, dB);
    H = alto_cuerpo(dA, dB);
    difference() {
        translate([-L / 2, -L / 2, 0]) cube([L, L, H]);
        // tubo A arriba (eje X)
        if (cuadA) translate([-L / 2 - 1, -dA / 2, H - prof(dA)]) cube([L + 2, dA, dA]);
        else translate([0, 0, H + APRIETE]) canal_x(dA, L + 2);
        // tubo B abajo (eje Y)
        if (cuadB) translate([-dB / 2, -L / 2 - 1, -dB + prof(dB)]) cube([dB, L + 2, dB]);
        else translate([0, 0, -APRIETE]) canal_b(dB, L + 2);
        // tornillos de la tapa A (entran desde arriba) con tuerca cautiva cerca de abajo
        for (p = torn(dA, L)) {
            translate([p[0], p[1], -1]) cylinder(d = M6, h = H + 2);
            translate([p[0], p[1], 2.5]) rotate(30) cylinder(d = NUT6, h = NUT6_H, $fn = 6);
        }
        // tornillos de la tapa B (entran desde abajo) con tuerca cautiva cerca de arriba
        for (p = tornB(dB, L)) {
            translate([p[0], p[1], -1]) cylinder(d = M6, h = H + 2);
            translate([p[0], p[1], H - 2.5 - NUT6_H]) rotate(30) cylinder(d = NUT6, h = NUT6_H, $fn = 6);
        }
        if (txt != "") translate([0, -L / 2 + 0.6, H / 2]) rotate([90, 0, 0]) rotulo(txt, 5);
    }
}

// tapa de un tubo (eje X). Se imprime con la cara exterior en la cama y la media caña hacia arriba.
module cruceta_tapa(d, dOtro, cuadrado = false) {
    L = largo_cruceta(d, dOtro);
    t = grosor_tapa(d);
    difference() {
        translate([-L / 2, -L / 2, 0]) cube([L, L, t]);
        if (cuadrado) translate([-L / 2 - 1, -d / 2, t - prof(d)]) cube([L + 2, d, d]);
        else translate([0, 0, t + APRIETE]) canal_x(d, L + 2);
        for (p = torn(d, L)) {
            translate([p[0], p[1], -1]) cylinder(d = M6, h = t + 2);
            translate([p[0], p[1], -1]) cylinder(d = 12, h = 5);         // cabeza M6 + arandela, rehundida
        }
        // antigiro: tornillo autotaladrante inox 4,8 mm que atraviesa la tapa y muerde el tubo
        translate([L / 4, 0, -1]) cylinder(d = 5.2, h = t + 2);
    }
}

// ------------------------------ PIEZAS -------------------------------
// ADS-B: tapa inferior de la base (sustituye a adsb_tapa) con vaso para tubo Ø25 vertical
LNA = [72, 34, 20];
module adsb_tapa_tubo() {
    w = LNA[1] + 12; l = LNA[0] + 14;
    difference() {
        union() {
            translate([-w / 2, -l / 2, 0]) cube([w, l, 4]);
            translate([0, 0, -45]) cylinder(d = ARM_D + 9, h = 45 + E);
            for (a = [0, 90, 180, 270]) rotate(a) translate([0, -2, -45]) cube([(ARM_D + 9) / 2 + 6, 4, 45]);   // nervios
        }
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * (w / 2 - 4), sy * (l / 2 - 4), -1]) cylinder(d = M3, h = 6);
        translate([0, 0, -46]) cylinder(d = ARM_D, h = 42);                 // tope 4 mm bajo la tapa
        for (z = [-34, -14]) translate([0, 0, z]) rotate([0, 90, 0]) cylinder(d = M5 - 0.8, h = 40);   // prisioneros M5
        translate([0, 0, -2]) cylinder(d = 3, h = 7);                         // drenaje
    }
}

// Anemómetro y veleta RS485: brida universal sobre tubo Ø25 vertical
//  patrón A: 4 × Ø6 en círculo de Ø47,1 (brida Ø65)  ·  patrón B: 4 × Ø4,5 en Ø68 (brida Ø80)
module sensor_viento_brida() {
    D = 92;
    difference() {
        union() {
            cylinder(d = D, h = 6);
            translate([0, 0, -50]) cylinder(d = ARM_D + 9, h = 50 + E);
            for (a = [0 : 60 : 359]) rotate(a) translate([0, -2, -50]) cube([D / 2 - 2, 4, 50]);
        }
        translate([0, 0, -51]) cylinder(d = ARM_D, h = 47);
        translate([0, 0, -5]) cylinder(d = 14, h = 12);                       // paso del cable al tubo
        for (a = [45 : 90 : 359]) rotate(a) {
            translate([47.1 / 2, 0, -1]) cylinder(d = 6.4, h = 8);
            translate([47.1 / 2, 0, -8]) rotate(30) cylinder(d = 9.4, h = 8, $fn = 6);   // tuerca M5
        }
        for (a = [0 : 90 : 359]) rotate(a) {
            translate([68 / 2, 0, -1]) cylinder(d = 4.8, h = 8);
            translate([68 / 2, 0, -8]) rotate(30) cylinder(d = 8.1, h = 8, $fn = 6);    // tuerca M4
        }
        for (z = [-38, -16]) translate([0, 0, z]) rotate([0, 90, 0]) cylinder(d = M5 - 0.8, h = 40);
        translate([0, -D / 2 + 9, 6 - 0.8]) rotulo("N", 7);                    // marca del norte
    }
}

// Pluviómetro: vaso para poste Ø40 + plataforma nivelable (3 tornillos M5 + muelles)
module pluvio_vaso() {
    difference() {
        union() {
            cylinder(d = MAST_D + 10, h = 55);
            translate([0, 0, 55 - E]) cylinder(d = 100, h = 8);
            for (a = [0 : 120 : 359]) rotate(a + 60) translate([0, -2.5, 0]) cube([49, 5, 55 + E]);
        }
        translate([0, 0, -1]) cylinder(d = MAST_D, h = 52);
        for (a = [0 : 120 : 359]) rotate(a) translate([40, 0, 50]) cylinder(d = INS_M5, h = 14);   // insertos M5
        for (z = [14, 38]) translate([0, 0, z]) rotate([0, 90, 0]) cylinder(d = M5 - 0.8, h = 40);
        translate([0, 0, 50]) cylinder(d = 8, h = 20);                          // drenaje
    }
}
PLUVIO_BASE = [160, 70];        // apoyo del pluviómetro (Misol WH-SP-RG ≈ 150 × 60)
module pluvio_plataforma() {
    difference() {
        union() {
            translate([-PLUVIO_BASE[0] / 2, -PLUVIO_BASE[1] / 2, 0]) cube([PLUVIO_BASE[0], PLUVIO_BASE[1], 6]);
            cylinder(d = 100, h = 6);
        }
        for (a = [0 : 120 : 359]) rotate(a) translate([40, 0, -1]) cylinder(d = M5 + 0.6, h = 8);   // nivelación
        for (x = [-60 : 20 : 60], y = [-20, 20]) translate([x - 6, y - 1.8, -1]) cube([12, 3.6, 8]);  // ranuras M3
        translate([0, 0, -1]) cylinder(d = 10, h = 8);                          // drenaje
        translate([0, PLUVIO_BASE[1] / 2 - 6, 6 - 0.8]) rotulo("NIVELAR", 5);
    }
}

// Pico «bricohams-io» + placa perforada 50 × 70 en la rejilla de 20 mm de la caja v3
module pico_soporte() {
    W = 80; Lp = 100;
    difference() {
        union() {
            translate([-W / 2, -Lp / 2, 0]) cube([W, Lp, 3]);
            // Pico (51 × 21, agujeros 47 × 11,4, M2)
            for (sx = [-1, 1], sy = [-1, 1]) translate([sx * 23.5, 30 + sy * 5.7, 0]) cylinder(d = 5.5, h = 8);
            // placa perforada 50 × 70 (agujeros 46 × 66, M2)
            for (sx = [-1, 1], sy = [-1, 1]) translate([sx * 33, -15 + sy * 23, 0]) cylinder(d = 5.5, h = 8);
        }
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * 23.5, 30 + sy * 5.7, 2]) cylinder(d = 1.8, h = 8);
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * 33, -15 + sy * 23, 2]) cylinder(d = 1.8, h = 8);
        for (sx = [-1, 1], sy = [-2, -1, 1, 2]) translate([sx * 30, sy * 20, -1]) cylinder(d = M3, h = 5);   // rejilla 20 mm
        translate([0, 30, 3 - 0.6]) rotulo("PICO IO", 4);
    }
}

// --------------------------- VISTA DE MONTAJE ---------------------------
module tubo(d, l, eje) {   // fantasma de los tubos en la vista
    color("silver", 0.35)
        if (eje == "x") rotate([0, 90, 0]) cylinder(d = d - 0.6, h = l, center = true);
        else if (eje == "y") rotate([90, 0, 0]) cylinder(d = d - 0.6, h = l, center = true);
        else cylinder(d = d - 0.6, h = l, center = true);
}
module cruceta_montada(dA, dB, cuadA = false) {
    H = alto_cuerpo(dA, dB);
    color("orange") cruceta_cuerpo(dA, dB, cuadA);
    color("white") translate([0, 0, H + 2 * APRIETE + grosor_tapa(dA)]) mirror([0, 0, 1]) cruceta_tapa(dA, dB, cuadA);
    color("white") translate([0, 0, -2 * APRIETE - grosor_tapa(dB)]) rotate([0, 0, -90]) cruceta_tapa(dB, dA);
}
module montaje() {
    // 1) mástil (vertical, aquí el tubo B de abajo va en Y) ↔ brazo Ø25
    cruceta_montada(ARM_D, MAST_D);
    translate([0, 0, alto_cuerpo(ARM_D, MAST_D) + APRIETE]) tubo(ARM_D, 220, "x");
    translate([0, 0, -APRIETE]) tubo(MAST_D, 220, "y");
    // 2) mástil ↔ boom de la quad
    translate([170, 0, 0]) cruceta_montada(BOOM, MAST_D, true);
    // 3) brazo ↔ fibra 433
    translate([340, 0, 0]) cruceta_montada(FIBRA_D, ARM_D);
    // 4) piezas sueltas
    translate([0, 170, 50]) color("white") adsb_tapa_tubo();
    translate([150, 170, 50]) color("white") sensor_viento_brida();
    translate([290, 170, 0]) color("white") pluvio_vaso();
    translate([290, 170, 70]) color("lightgray") pluvio_plataforma();
    translate([450, 170, 0]) color("green") pico_soporte();
}

// ------------------------------ SELECTOR -------------------------------
if (PART == "montaje") montaje();
// crucetas: cuerpo + tapa A (tubo de arriba) + tapa B (tubo de abajo)
else if (PART == "cruceta_mastil_brazo_cuerpo") cruceta_cuerpo(ARM_D, MAST_D, txt = "MASTIL-BRAZO");
else if (PART == "cruceta_mastil_brazo_tapa_brazo") cruceta_tapa(ARM_D, MAST_D);
else if (PART == "cruceta_mastil_brazo_tapa_mastil") cruceta_tapa(MAST_D, ARM_D);
else if (PART == "cruceta_mastil_quad_cuerpo") cruceta_cuerpo(BOOM, MAST_D, true, txt = "QUAD");
else if (PART == "cruceta_mastil_quad_tapa_boom") cruceta_tapa(BOOM, MAST_D, true);
else if (PART == "cruceta_mastil_quad_tapa_mastil") cruceta_tapa(MAST_D, BOOM);
else if (PART == "cruceta_brazo_fibra_cuerpo") cruceta_cuerpo(FIBRA_D, ARM_D, txt = "FIBRA");
else if (PART == "cruceta_brazo_fibra_tapa_fibra") cruceta_tapa(FIBRA_D, ARM_D);
else if (PART == "cruceta_brazo_fibra_tapa_brazo") cruceta_tapa(ARM_D, FIBRA_D);
else if (PART == "cruceta_brazo_tubo_cuerpo") cruceta_cuerpo(ARM_D, ARM_D, txt = "BRAZO-TUBO");
else if (PART == "cruceta_brazo_tubo_tapa") cruceta_tapa(ARM_D, ARM_D);
else if (PART == "adsb_tapa_tubo") rotate([180, 0, 0]) adsb_tapa_tubo();   // impresa del revés: la brida en la cama
else if (PART == "sensor_viento_brida") rotate([180, 0, 0]) sensor_viento_brida();   // impresa del revés: la brida en la cama
else if (PART == "pluvio_vaso") rotate([180, 0, 0]) pluvio_vaso();   // impresa del revés: la brida en la cama
else if (PART == "pluvio_plataforma") pluvio_plataforma();
else if (PART == "pico_soporte") pico_soporte();
// vistas de documentación (solo para render del manual 52; no afectan a los STL)
else if (PART == "vista_despiece_cruceta_mastil_brazo") v_cruceta(ARM_D, MAST_D, false, V_EX, "MASTIL-BRAZO");
else if (PART == "vista_montado_cruceta_mastil_brazo") v_cruceta(ARM_D, MAST_D, false, 0, "MASTIL-BRAZO");
else if (PART == "vista_despiece_cruceta_mastil_quad") v_cruceta(BOOM, MAST_D, true, V_EX, "QUAD");
else if (PART == "vista_montado_cruceta_mastil_quad") v_cruceta(BOOM, MAST_D, true, 0, "QUAD");
else if (PART == "vista_despiece_cruceta_brazo_fibra") v_cruceta(FIBRA_D, ARM_D, false, V_EX, "FIBRA");
else if (PART == "vista_montado_cruceta_brazo_fibra") v_cruceta(FIBRA_D, ARM_D, false, 0, "FIBRA");
else if (PART == "vista_despiece_cruceta_brazo_tubo") v_cruceta(ARM_D, ARM_D, false, V_EX, "BRAZO-TUBO");
else if (PART == "vista_montado_cruceta_brazo_tubo") v_cruceta(ARM_D, ARM_D, false, 0, "BRAZO-TUBO");
else if (PART == "vista_despiece_pluviometro") v_pluvio(V_EX);
else if (PART == "vista_montado_pluviometro") v_pluvio(0);
else if (PART == "vista_despiece_viento") v_viento(V_EX);
else if (PART == "vista_montado_viento") v_viento(0);
else if (PART == "vista_despiece_pico") v_pico(V_EX);
else if (PART == "vista_montado_pico") v_pico(0);
else if (PART == "vista_despiece_adsb_tubo") v_adsb_tubo(V_EX);
else if (PART == "vista_montado_adsb_tubo") v_adsb_tubo(0);

// ---------------- VISTAS DE DOCUMENTACIÓN (solo lectura) ----------------
V_ORANGE = "#F26B1D"; V_INK = "#23272B"; V_GREY = "#59636B"; V_LIGHT = "#C9CED3";
V_EX = 50;          // separación del despiece (mm)
V_GRUB_L = 12;      // longitud orientativa del prisionero
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
module v_nut(p, d, h) { color("silver") translate(p) rotate(30) cylinder(d = d, h = h, $fn = 6); }
// tubo fantasma centrado en p con eje ax
module v_tube(p, ax, d, l) { color("silver", 0.35) translate(p) rotate(v_rot(ax)) translate([0, 0, -l / 2]) cylinder(d = d - 0.6, h = l, $fn = 48); }

module v_cruceta(dA, dB, cuadA, ex, txt) {
    H = alto_cuerpo(dA, dB); L = largo_cruceta(dA, dB);
    zA = H + 2 * APRIETE; zB = -2 * APRIETE;
    tA = grosor_tapa(dA); tB = grosor_tapa(dB);
    color(V_ORANGE, ex > 0 ? 0.7 : 1) cruceta_cuerpo(dA, dB, cuadA, false, txt);
    color(V_GREY) translate([0, 0, zA + tA + ex]) mirror([0, 0, 1]) cruceta_tapa(dA, dB, cuadA);
    color(V_LIGHT) translate([0, 0, zB - tB - ex]) rotate([0, 0, -90]) cruceta_tapa(dB, dA);
    // tubos fantasma
    if (cuadA) color("silver", 0.35) translate([-L, -dA / 2, H - prof(dA)]) cube([2 * L, dA, dA]);
    else v_tube([0, 0, H + APRIETE], "x", dA, 2 * L);
    v_tube([0, 0, -APRIETE], "y", dB, 2 * L);
    offA = ex > 0 ? zA + tA + ex + 12 - 2.5 : 0;
    offB = ex > 0 ? (H - 2.5) - (zB - tB - ex - 12) : 0;
    for (p = torn(dA, L)) {
        v_nut([p[0], p[1], 2.5], NUT6, NUT6_H);
        v_scr([p[0], p[1], 2.5], "z", zA + tA - 4 - 2.5, 6, offA);
    }
    for (p = tornB(dB, L)) {
        v_nut([p[0], p[1], H - 2.5 - NUT6_H], NUT6, NUT6_H);
        v_scr([p[0], p[1], H - 2.5], "-z", H - 2.5 - (zB - tB + 4), 6, offB);
    }
    // antigiro 4,8 × 19 de cada tapa
    v_scr([L / 4, 0, zA + tA - 19], "z", 19, 4.8, ex > 0 ? 19 + ex + 10 : 0);
    v_scr([0, -L / 4, zB - tB + 19], "-z", 19, 4.8, ex > 0 ? 19 + ex + 10 : 0);
}

module v_pluvio(ex) {
    sv = ex; sp = 2 * ex; zp = 63 + 21;   // hueco vaso-plataforma orientativo (M5 × 40 + muelle)
    v_tube([0, 0, -4.5], "z", MAST_D, 111);
    color(V_ORANGE, ex > 0 ? 0.8 : 1) translate([0, 0, sv]) pluvio_vaso();
    color(V_LIGHT) translate([0, 0, zp + sp]) pluvio_plataforma();
    if (ex > 0) v_guia([0, 0, 51], [0, 0, 51 + sv]);
    for (a = [0 : 120 : 359]) {
        px = 40 * cos(a); py = 40 * sin(a);
        color("silver", 0.5) translate([px, py, 63 + sv + 0.5 * ex]) cylinder(d = 9, h = 21, $fn = 16);   // muelle
        v_scr([px, py, 50 + sv], "z", 40, 5, ex > 0 ? (zp + sp + 6 + 15) - (50 + sv) : 0);
    }
    for (z = [14, 38]) v_scr([MAST_D / 2, 0, z + sv], "x", V_GRUB_L, 5, ex > 0 ? 25 : 0, false);
}

module v_viento(ex) {
    sb = ex; ss = 2 * ex;
    v_tube([0, 0, -60], "z", ARM_D, 112);
    color(V_ORANGE, ex > 0 ? 0.8 : 1) translate([0, 0, sb]) sensor_viento_brida();
    color(V_GREY, 0.6) translate([0, 0, 6 + ss]) cylinder(d = 65, h = 10, $fn = 48);   // sensor (esquemático)
    if (ex > 0) v_guia([0, 0, -4], [0, 0, -4 + sb]);
    for (a = [45 : 90 : 359]) {
        px = 47.1 / 2 * cos(a); py = 47.1 / 2 * sin(a);
        v_nut([px, py, -8 + sb], 9.4, 4);
        v_scr([px, py, -8 + sb], "z", 25, 5, ex > 0 ? (16 + ss + 10) - (-8 + sb) : 0);
    }
    for (z = [-38, -16]) v_scr([ARM_D / 2, 0, z + sb], "x", V_GRUB_L, 5, ex > 0 ? 25 : 0, false);
}

module v_pico(ex) {
    color(V_ORANGE) pico_soporte();
    color("darkgreen", 0.85) translate([-25.5, 30 - 10.5, 8 + ex]) cube([51, 21, 1.6]);     // Pico
    color("seagreen", 0.85) translate([-25, -50, 8 + ex]) cube([50, 70, 1.6]);              // placa perforada
    for (sx = [-1, 1], sy = [-1, 1]) {
        v_scr([sx * 23.5, 30 + sy * 5.7, 8 + 1.6 - 6], "z", 6, 2, ex > 0 ? ex + 10 + 6 : 0);
        v_scr([sx * 33, -15 + sy * 23, 8 + 1.6 - 6], "z", 6, 2, ex > 0 ? ex + 10 + 6 : 0);
    }
    for (sx = [-1, 1], sy = [-2, -1, 1, 2]) v_scr([sx * 30, sy * 20, -5], "z", 8, 3, ex > 0 ? 12 + 0.6 * ex : 0);   // a la rejilla de la caja v3
}

module v_adsb_tubo(ex) {
    w = LNA[1] + 12; l = LNA[0] + 14; sb = ex; sa = 2 * ex;
    v_tube([0, 0, -70], "z", ARM_D, 132);
    color(V_ORANGE, ex > 0 ? 0.8 : 1) translate([0, 0, sb]) adsb_tapa_tubo();
    color(V_GREY, 0.5) translate([-w / 2, -l / 2, 4 + sa]) cube([w, l, LNA[2] + 16]);   // base de la antena (esquemática)
    if (ex > 0) v_guia([0, 0, -4], [0, 0, -4 + sb]);
    for (sx = [-1, 1], sy = [-1, 1]) v_scr([sx * (w / 2 - 4), sy * (l / 2 - 4), 12 + sa], "-z", 12, 3, ex > 0 ? 22 + ex : 0);
    for (z = [-34, -14]) v_scr([ARM_D / 2, 0, z + sb], "x", V_GRUB_L, 5, ex > 0 ? 25 : 0, false);
}
