// =====================================================================
//  Piezas impresas de las antenas y soportes BricoHams SDR · EA5KAO
//  PETG o ASA (exterior), TPU 95A (fundas y juntas). Anycubic Kobra S1.
//
//  Medidas eléctricas: hardware/antenas/sim (NEC2) y docs/manuales/11–16.
//  Exportar: openscad -D 'PART="quad_buje_2m"' -o quad_buje_2m.stl antenas_bricohams.scad
//  (tools/antenas.sh exporta todo). Las piezas salen orientadas para imprimir.
// =====================================================================

PART = "vista";
$fn = 48;
E = 0.01;
FONT = "DejaVu Sans:style=Bold";

// --------------------------- comunes ---------------------------------
HOLE_M3 = 3.4;  INS_M3 = 4.0;  NUT_M3 = 6.4;
HOLE_M4 = 4.5;  INS_M4 = 5.6;  NUT_M4 = 7.9;
HOLE_M5 = 5.5;  HOLE_M6 = 6.6;  HOLE_M8 = 8.6;
MAST_D = 40;          // mástil Televés
ARM_D = 25;           // brazo separador (tubo de aluminio Ø25)

// agujero horizontal en gota (eje Y), punta hacia +Z
module gota_y(d, l) { rotate([-90, 0, 0]) linear_extrude(l, center = true) union() { circle(d = d); rotate(225) square(d / 2); } }
module gota_x(d, l) { rotate([0, 90, 0]) linear_extrude(l, center = true) union() { circle(d = d); rotate(135) square(d / 2); } }
// brazo cilíndrico horizontal imprimible (perfil en gota) a lo largo de X
module brazo_x(d, l) { rotate([0, 90, 0]) linear_extrude(l) union() { circle(d = d); rotate(135) square(d / 2); } }
module rotulo(t, s = 4) { linear_extrude(0.8) text(t, size = s, font = FONT, halign = "center", valign = "center"); }

// =====================================================================
//  QUAD DOBLE 2 m / 70 cm (polarización vertical, cuadros en rombo)
//  Boom de aluminio cuadrado 20×20, crucetas de fibra de vidrio Ø8 (2 m) y Ø6 (70 cm)
// =====================================================================
BOOM = 20.4;
ROD8 = 8.3;  ROD6 = 6.3;
WIRE = 2.4;          // hilo de 2 mm (cobre esmaltado o aluminio)

module buje(rod, largo_brazo, h = 40, txt = "") {
    s = BOOM + 12;
    difference() {
        union() {
            translate([-s / 2, -s / 2, 0]) cube([s, s, h]);
            for (a = [0, 90, 180, 270]) rotate(a) translate([s / 2 - 2, 0, h / 2]) brazo_x(rod + 8, largo_brazo + 2);
        }
        translate([-BOOM / 2, -BOOM / 2, -1]) cube([BOOM, BOOM, h + 2]);
        // casquillos de las crucetas y prisioneros M3 (desde arriba)
        for (a = [0, 90, 180, 270]) rotate(a) {
            translate([s / 2 + 4, 0, h / 2]) rotate([0, 90, 0]) cylinder(d = rod, h = largo_brazo);
            translate([s / 2 + largo_brazo - 8, 0, h / 2]) cylinder(d = 2.8, h = 30);   // M3 autorroscante
        }
        // prisioneros M5 contra el boom
        for (z = [10, h - 10]) translate([0, s / 2 - 3, z]) gota_y(HOLE_M5 - 0.8, 12);
        if (txt != "") translate([0, -s / 2 + 0.6, h / 2]) rotate([90, 0, 0]) rotulo(txt, 4);
    }
}

module puntera(rod) {   // punta de cruceta con paso del hilo (vértice del cuadro)
    difference() {
        hull() { cylinder(d = rod + 6, h = 22); translate([0, 0, 22]) sphere(d = rod + 6); }
        translate([0, 0, -1]) cylinder(d = rod, h = 17);
        translate([0, 0, 22]) gota_y(WIRE, 30);                      // paso del hilo
        translate([0, 0, 22]) rotate([0, 0, 0]) cube([1.2, 30, 2 * WIRE], center = true);   // ranura para meter el hilo
        translate([0, 0, 9]) gota_x(2.8, 30);                        // pasador o brida
    }
}

module clip_cruceta(rod, txt = "") {   // vértice intermedio sobre una cruceta (cuadros de 70 cm en el buje de 2 m)
    difference() {
        union() {
            cylinder(d = rod + 7, h = 16);
            translate([0, 0, 8]) rotate([0, 90, 0]) cylinder(d = 9, h = (rod + 7) / 2 + 5);
        }
        translate([0, 0, -1]) cylinder(d = rod, h = 20);
        translate([(rod + 7) / 2 + 2, 0, 8]) rotate([90, 0, 0]) cylinder(d = WIRE, h = 20, center = true);   // hilo
        translate([0, 0, 8]) rotate([90, 0, 0]) cylinder(d = 2.8, h = 30, center = true);                     // prisionero M3
    }
}

module alimentacion(rod, en_punta = true) {   // vértice de alimentación: 2 bornes M3 separados 12 mm
    w = 34; d = 18; h = 16;
    difference() {
        union() {
            translate([-w / 2, -d / 2, 0]) cube([w, d, h]);
            if (en_punta) translate([0, 0, -26]) cylinder(d = rod + 6, h = 26 + E);
            else translate([0, -d / 2, h / 2]) rotate([-90, 0, 0]) cylinder(d = rod + 7, h = d);
        }
        if (en_punta) translate([0, 0, -27]) cylinder(d = rod, h = 24);
        else translate([0, -d / 2 - 1, h / 2]) rotate([-90, 0, 0]) cylinder(d = rod, h = d + 2);
        for (s = [-1, 1]) {
            translate([s * 6, 0, -1]) cylinder(d = INS_M3, h = h + 2);          // inserto M3 de latón: borne
            translate([s * 14, 0, h / 2]) rotate([90, 0, 0]) cylinder(d = WIRE, h = d + 2, center = true);   // entrada del hilo
        }
        translate([-w / 2 - 1, -1, h - 4]) cube([w + 2, 2, 5]);                  // ranura del coaxial
        for (x = [-12, 12]) translate([x, 0, 3]) gota_y(3, d + 2);               // bridas de alivio
        translate([0, d / 2 - 0.6, h / 2]) rotate([-90, 0, 0]) rotulo("+  −", 4);
    }
}

module abrazadera_cruzada(d1, d2, l = 70, t = 18, bolt1 = HOLE_M8, bolt2 = HOLE_M6, cuadrado2 = false) {
    // silla de dos ranuras perpendiculares: abajo el mástil (Ø d1, eje Y), arriba el boom o brazo (eje X)
    difference() {
        translate([-l / 2, -l / 2, 0]) cube([l, l, t]);
        translate([0, 0, -d1 / 2 + 5]) rotate([90, 0, 0]) cylinder(d = d1, h = l + 2, center = true);
        if (cuadrado2) translate([-l / 2 - 1, -d2 / 2, t - 6]) cube([l + 2, d2, 7]);
        else translate([0, 0, t + d2 / 2 - 6]) rotate([0, 90, 0]) cylinder(d = d2, h = l + 2, center = true);
        for (s = [-1, 1]) {
            translate([s * (d1 / 2 + bolt1 / 2 + 1), l / 2 - 12, -1]) cylinder(d = bolt1, h = t + 2);   // U del mástil
            translate([s * (d1 / 2 + bolt1 / 2 + 1), -l / 2 + 12, -1]) cylinder(d = bolt1, h = t + 2);
            translate([l / 2 - 10, s * (d2 / 2 + bolt2 / 2 + 1), -1]) cylinder(d = bolt2, h = t + 2);   // U del boom
            translate([-l / 2 + 10, s * (d2 / 2 + bolt2 / 2 + 1), -1]) cylinder(d = bolt2, h = t + 2);
        }
    }
}

// =====================================================================
//  DISCONE (12 + 12 varillas de aluminio Ø4 con rosca M4; bujes de aluminio)
// =====================================================================
DISC_MODELO = "grande";                // grande | compacta
HUB_D = 70;  HUB_T = 12;               // bujes de aluminio Ø70 × 12 (disco y cono)
N_VAR = 12;
SEMI = 30;                             // semiángulo del cono

module discone_aislador() {   // separador de PETG entre buje de disco (arriba) y de cono (abajo): hueco 20 mm
    h = 20;
    difference() {
        cylinder(d = 50, h = h);
        translate([0, 0, -1]) cylinder(d = 7, h = h + 2);                       // varilla de latón M4 con funda
        for (a = [0 : 120 : 359]) rotate(a + 60) {
            translate([18, 0, h - 8]) cylinder(d = INS_M4, h = 9);              // insertos arriba (disco)
            rotate(60) translate([18, 0, -1]) cylinder(d = INS_M4, h = 9);      // insertos abajo (cono)
        }
        translate([0, 0, h / 2]) rotate([90, 0, 0]) cylinder(d = 2, h = 60, center = true);   // respiradero
    }
}

module plantilla_disco() {   // guía para taladrar 12 agujeros radiales Ø3,3 (rosca M4) en el canto del buje de disco
    difference() {
        cylinder(d = HUB_D + 24, h = HUB_T + 6);
        translate([0, 0, 3]) cylinder(d = HUB_D + 0.4, h = HUB_T + 10);
        translate([0, 0, -1]) cylinder(d = 20, h = 10);
        for (k = [0 : N_VAR - 1]) rotate(k * 360 / N_VAR) translate([HUB_D / 2 - 2, 0, 3 + HUB_T / 2]) rotate([0, 90, 0]) cylinder(d = 3.4, h = 20);
        translate([0, -(HUB_D + 24) / 2 + 3, 1]) rotulo("DISCO 12x M4", 3);
    }
}

module plantilla_cono() {   // guía para 12 agujeros a 30° del eje en la cara inferior del buje de cono
    difference() {
        cylinder(d = HUB_D + 30, h = 22);
        translate([0, 0, 22 - HUB_T]) cylinder(d = HUB_D + 0.4, h = HUB_T + 1);
        for (k = [0 : N_VAR - 1]) rotate(k * 360 / N_VAR) translate([HUB_D / 2 - 8, 0, 22 - HUB_T]) rotate([0, 180 - SEMI, 0]) cylinder(d = 3.4, h = 40);
        translate([0, 0, -1]) cylinder(d = 16, h = 30);
    }
}

module discone_adaptador_mastil() {   // une el buje de cono a la punta del mástil (Ø MAST_D) y saca el coaxial
    h = 60;
    difference() {
        union() {
            cylinder(d = MAST_D + 10, h = h);
            translate([0, 0, h - E]) cylinder(d = HUB_D, h = 6);
        }
        translate([0, 0, -1]) cylinder(d = MAST_D + 0.6, h = h - 12);           // entra en el mástil por fuera
        translate([0, 0, -1]) cylinder(d = 18, h = h + 10);                     // conector N y coaxial
        for (a = [45 : 90 : 359]) rotate(a) translate([HUB_D / 2 - 7, 0, h - 10]) cylinder(d = HOLE_M4, h = 20);   // tornillos al buje
        for (z = [12, 32]) translate([0, 0, z]) rotate([90, 0, 0]) cylinder(d = HOLE_M6, h = MAST_D + 20, center = true);   // pasante al mástil
        translate([0, 0, 6]) rotate([0, 90, 0]) cylinder(d = 6, h = MAST_D, center = false);      // drenaje
    }
}

module discone_capuchon() {   // tapa de lluvia sobre el buje de disco
    difference() {
        union() { cylinder(d = HUB_D + 16, h = 3); translate([0, 0, 3]) cylinder(d1 = HUB_D + 16, d2 = 20, h = 18); }
        translate([0, 0, -1]) cylinder(d = HUB_D + 0.6, h = 3);
        for (k = [0 : N_VAR - 1]) rotate(k * 360 / N_VAR) translate([HUB_D / 2 - 4, -3, -1]) cube([20, 6, 3.5]);   // muescas de las varillas
    }
}

module tapon_varilla(d = 4.2) {   // punta roma para las varillas (seguridad) con agujero para cordino
    difference() {
        hull() { cylinder(d = d + 6, h = 14); translate([0, 0, 14]) sphere(d = d + 6); }
        translate([0, 0, -1]) cylinder(d = d, h = 12);
        translate([0, 0, 15]) gota_y(2.5, 20);
    }
}

// =====================================================================
//  ADS-B 1090 MHz: plano de tierra λ/4 (radiante 62 mm, 4 radiales de 68 mm a 45°)
//  con el LNA 1090 dentro de la base
// =====================================================================
LNA = [72, 34, 20];       // LNA con sus SMA (largo × ancho × alto); medir el tuyo
module adsb_base() {
    w = LNA[1] + 12; l = LNA[0] + 14; h = LNA[2] + 16;
    difference() {
        union() {
            translate([-w / 2, -l / 2, 0]) cube([w, l, h]);
            translate([0, 0, h - E]) cylinder(d = 36, h = 8);                    // torreta del conector
            translate([w / 2 - E, -20, 0]) cube([12, 40, h]);                   // oreja para la U del brazo
        }
        translate([-LNA[1] / 2 - 0.5, -LNA[0] / 2 - 0.5, 4]) cube([LNA[1] + 1, LNA[0] + 1, h]);   // hueco del LNA (se cierra con la tapa)
        translate([0, 0, h - 1]) cylinder(d = 6.6, h = 20);                      // SMA de panel (rosca 1/4")
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * 6.35, sy * 6.35, h + 8 - 6]) cylinder(d = 2.8, h = 7);   // brida de 4 agujeros
        translate([0, -l / 2 - 1, 10]) gota_y(GLAND_PG7_L, 12);                   // salida del coaxial (PG7)
        for (z = [8, h - 8]) translate([w / 2 + 6, 0, z]) rotate([90, 0, 0]) cylinder(d = HOLE_M6, h = 50, center = true);
        translate([0, 0, 1]) cylinder(d = 3, h = 5);                             // drenaje
    }
}
GLAND_PG7_L = 12.7;
module adsb_tapa() {   // tapa inferior de la base (con junta de TPU)
    w = LNA[1] + 12; l = LNA[0] + 14;
    difference() {
        translate([-w / 2, -l / 2, 0]) cube([w, l, 3]);
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * (w / 2 - 4), sy * (l / 2 - 4), -1]) cylinder(d = HOLE_M3, h = 5);
    }
}
module adsb_radomo() {   // cubre el radiante; se pega o atornilla sobre la torreta
    difference() {
        union() { cylinder(d = 30, h = 82); translate([0, 0, 82]) sphere(d = 30); }
        translate([0, 0, -1]) cylinder(d = 36.6, h = 8);
        translate([0, 0, 6]) cylinder(d = 26.4, h = 77);
        translate([0, 0, 82]) sphere(d = 26.4);
        for (a = [45 : 90 : 359]) rotate(a) translate([15, 0, 3]) rotate([0, 90, 0]) cylinder(d = 3, h = 10, center = true);   // salidas de los radiales
    }
}

// =====================================================================
//  GPS activa, Bigsignal 868 / 433 y fibra 433: sillas sobre brazo Ø25
// =====================================================================
FIBRA_D = 26;          // Ø del tubo de la antena de fibra en la zona de amarre (medir: 20–32)
module soporte_fibra() { abrazadera_cruzada(ARM_D, FIBRA_D, l = 64, t = 20, bolt1 = HOLE_M6, bolt2 = HOLE_M6); }
module brazo_mastil() { abrazadera_cruzada(MAST_D, ARM_D, l = 80, t = 22, bolt1 = HOLE_M8, bolt2 = HOLE_M6); }
module tapon_brazo() { difference() { union() { cylinder(d = ARM_D + 4, h = 4); cylinder(d = ARM_D - 4.6, h = 18); } translate([0, 0, 4]) cylinder(d = ARM_D - 8, h = 20); } }
module separador_coax(d = 7.5) {   // aparta el coaxial 30 mm del mástil; se sujeta con brida
    difference() {
        union() { translate([-12, 0, 0]) cube([24, 36, 10]); translate([0, 36, 0]) cylinder(d = d + 8, h = 10); }
        translate([0, 36, -1]) cylinder(d = d, h = 12);
        translate([-0.75, 36, -1]) cube([1.5, 20, 12]);
        translate([-12 - 1, 4, 3]) cube([26, 3, 4]);
        translate([0, 0, 5]) rotate([0, 0, 0]) translate([0, 0, 0]) cube([30, 2, 2], center = true);
    }
}
GPS_PUCK = [48, 40, 15];     // antena GPS activa tipo «puck» (medir)
module gps_soporte() {
    difference() {
        union() {
            translate([-35, -35, 0]) cube([70, 70, 6]);
            translate([-GPS_PUCK[0] / 2 - 3, -GPS_PUCK[1] / 2 - 3, 6 - E]) cube([GPS_PUCK[0] + 6, GPS_PUCK[1] + 6, 6]);
        }
        translate([-GPS_PUCK[0] / 2, -GPS_PUCK[1] / 2, 6]) cube([GPS_PUCK[0], GPS_PUCK[1], 10]);
        translate([-3, GPS_PUCK[1] / 2 - 2, 6]) cube([6, 10, 10]);             // cable
        for (s = [-1, 1]) for (y = [-27, 27]) translate([s * (ARM_D / 2 + 4), y, -1]) cylinder(d = HOLE_M6, h = 10);
        translate([0, 0, -1]) cylinder(d = 3, h = 10);                           // drenaje
    }
}

// =====================================================================
//  LAZO MLA-30: caja estanca para la caja amplificadora, cruz de soporte y fundas
// =====================================================================
MLA_CAJA = [90, 60, 36];     // medidas interiores para la caja del amplificador (MEDIR la tuya)
MLA_ROD = 10.3;              // varillas de fibra Ø10 para la cruz
MLA_COAX = 7;                // Ø del coaxial del lazo
module mla_caja_base() {
    t = 3; i = MLA_CAJA;
    difference() {
        translate([-i[0] / 2 - t, -i[1] / 2 - t, 0]) cube([i[0] + 2 * t, i[1] + 2 * t, i[2] / 2 + t]);
        translate([-i[0] / 2, -i[1] / 2, t]) cube([i[0], i[1], i[2]]);
        for (s = [-1, 1]) translate([s * (i[0] / 2 + t / 2), 0, t + i[2] / 2]) rotate([0, 90, 0]) cylinder(d = MLA_COAX + 1, h = t + 2, center = true);   // entradas del lazo (media caña)
        translate([0, -i[1] / 2 - t / 2, t + 8]) gota_y(GLAND_PG7_L, t + 2);        // salida SMA/coax de bajada
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * (i[0] / 2 - 4), sy * (i[1] / 2 - 4), t]) cylinder(d = 7, h = 50);
        translate([0, 0, -1]) cylinder(d = 3, h = 5);                                // drenaje
    }
    for (sx = [-1, 1], sy = [-1, 1]) translate([sx * (i[0] / 2 - 4), sy * (i[1] / 2 - 4), t]) difference() { cylinder(d = 7, h = i[2] / 2); cylinder(d = INS_M3, h = i[2]); }
}
module mla_caja_tapa() {
    t = 3; i = MLA_CAJA;
    difference() {
        translate([-i[0] / 2 - t, -i[1] / 2 - t, 0]) cube([i[0] + 2 * t, i[1] + 2 * t, i[2] / 2 + t]);
        translate([-i[0] / 2, -i[1] / 2, t]) cube([i[0], i[1], i[2]]);
        for (s = [-1, 1]) translate([s * (i[0] / 2 + t / 2), 0, t + i[2] / 2]) rotate([0, 90, 0]) cylinder(d = MLA_COAX + 1, h = t + 2, center = true);
        for (sx = [-1, 1], sy = [-1, 1]) translate([sx * (i[0] / 2 - 4), sy * (i[1] / 2 - 4), -1]) cylinder(d = HOLE_M3, h = 10);
    }
}
module mla_junta() { linear_extrude(1.6) difference() { square([MLA_CAJA[0] + 5, MLA_CAJA[1] + 5], center = true); square([MLA_CAJA[0] - 1, MLA_CAJA[1] - 1], center = true); } }
module mla_cruz() {   // une dos varillas de fibra en «+» y las amarra al mástil con una U
    h = 30; s = 34;
    difference() {
        union() {
            translate([-s / 2, -s / 2, 0]) cube([s, s, h]);
            for (a = [0, 90, 180, 270]) rotate(a) translate([s / 2 - 2, 0, h / 2]) brazo_x(MLA_ROD + 8, 40);
        }
        for (a = [0, 90, 180, 270]) rotate(a) {
            translate([s / 2 + 2, 0, h / 2]) rotate([0, 90, 0]) cylinder(d = MLA_ROD, h = 40);
            translate([s / 2 + 30, 0, h / 2]) cylinder(d = 2.8, h = 30);
        }
        for (s2 = [-1, 1]) translate([s2 * 9, 0, -1]) cylinder(d = HOLE_M6, h = h + 2);   // U al mástil o al brazo
    }
}
module mla_clip_lazo() {   // en la punta de cada varilla: sujeta el coaxial del lazo
    difference() {
        union() { cylinder(d = MLA_ROD + 6, h = 22); translate([0, 0, 22]) rotate([0, 90, 0]) cylinder(d = MLA_COAX + 7, h = 18, center = true); }
        translate([0, 0, -1]) cylinder(d = MLA_ROD, h = 18);
        translate([0, 0, 22]) rotate([0, 90, 0]) cylinder(d = MLA_COAX, h = 30, center = true);
        translate([-10, -0.8, 22]) cube([20, 1.6, 10]);
    }
}
module funda_conector(d_int = 9.5, l = 40) {   // TPU: funda para SMA/N empalmados (se ajusta con cinta autovulcanizante)
    difference() {
        cylinder(d = d_int + 3.2, h = l);
        translate([0, 0, -1]) cylinder(d = d_int, h = l + 2);
        for (z = [6 : 8 : l - 4]) translate([0, 0, z]) difference() { cylinder(d = d_int + 0.1, h = 1.2); cylinder(d = d_int - 1.2, h = 1.2); }
    }
    for (z = [6 : 8 : l - 4]) translate([0, 0, z]) difference() { cylinder(d = d_int + 0.1, h = 1.2); cylinder(d = d_int - 1.2, h = 1.2); }
}

// =====================================================================
//  Soportes dentro de la caja: filtros NMRF y bias-tee
// =====================================================================
module clip_filtro() {   // abraza el cuerpo del filtro (≈ 13×13 mm) y se fija con brida a la placa
    difference() {
        translate([-11, -10, 0]) cube([22, 20, 18]);
        translate([-6.75, -11, 3]) cube([13.5, 22, 20]);
        translate([-12, -1.5, 1]) cube([24, 3, 1.4]);
    }
}

// =====================================================================
//  VISTA
// =====================================================================
module vista() {
    color("orange") buje(ROD8, 40, txt = "2M");
    color("gold") translate([90, 0, 0]) buje(ROD6, 30, 32, "70");
    color("white") translate([170, 0, 0]) alimentacion(ROD8);
    color("white") translate([170, 60, 0]) alimentacion(ROD8, false);
    color("lightblue") translate([0, 110, 0]) discone_aislador();
    color("silver") translate([80, 110, 0]) discone_capuchon();
    color("white") translate([0, -110, 0]) adsb_base();
    color("white", 0.6) translate([70, -110, 0]) adsb_radomo();
    color("white") translate([170, -110, 0]) brazo_mastil();
    color("dimgray") translate([260, 0, 0]) mla_cruz();
}

if (PART == "vista") vista();
else if (PART == "quad_buje_2m") buje(ROD8, 40, txt = "2M");
else if (PART == "quad_buje_70") buje(ROD6, 30, 32, "70");
else if (PART == "quad_puntera_8") puntera(ROD8);
else if (PART == "quad_puntera_6") puntera(ROD6);
else if (PART == "quad_clip_70") clip_cruceta(ROD8);
else if (PART == "quad_alim_2m") alimentacion(ROD8);
else if (PART == "quad_alim_70") alimentacion(ROD8, false);
else if (PART == "quad_abrazadera") abrazadera_cruzada(MAST_D, BOOM, l = 80, t = 22, cuadrado2 = true);
else if (PART == "discone_aislador") discone_aislador();
else if (PART == "discone_plantilla_disco") plantilla_disco();
else if (PART == "discone_plantilla_cono") plantilla_cono();
else if (PART == "discone_adaptador_mastil") discone_adaptador_mastil();
else if (PART == "discone_capuchon") discone_capuchon();
else if (PART == "tapon_varilla") tapon_varilla();
else if (PART == "adsb_base") adsb_base();
else if (PART == "adsb_tapa") adsb_tapa();
else if (PART == "adsb_radomo") adsb_radomo();
else if (PART == "gps_soporte") gps_soporte();
else if (PART == "soporte_fibra") soporte_fibra();
else if (PART == "brazo_mastil") brazo_mastil();
else if (PART == "tapon_brazo") tapon_brazo();
else if (PART == "separador_coax") separador_coax();
else if (PART == "mla_caja_base") mla_caja_base();
else if (PART == "mla_caja_tapa") mla_caja_tapa();
else if (PART == "mla_junta") mla_junta();
else if (PART == "mla_cruz") mla_cruz();
else if (PART == "mla_clip_lazo") mla_clip_lazo();
else if (PART == "funda_sma") funda_conector(9.5, 40);
else if (PART == "funda_n") funda_conector(17, 50);
else if (PART == "clip_filtro") clip_filtro();
