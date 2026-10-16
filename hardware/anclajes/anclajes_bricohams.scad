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
