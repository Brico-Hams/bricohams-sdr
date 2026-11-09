// =====================================================================
//  Piezas impresas de las antenas y soportes BricoHams SDR · N0CALL
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
// vistas de documentación (solo para render del manual 52; no afectan a los STL)
else if (PART == "vista_despiece_quad_buje") v_quad_buje(V_EX);
else if (PART == "vista_montado_quad_buje") v_quad_buje(0);
else if (PART == "vista_despiece_quad_alimentacion") v_quad_alim(V_EX);
else if (PART == "vista_montado_quad_alimentacion") v_quad_alim(0);
else if (PART == "vista_despiece_quad_abrazadera") v_abraz(MAST_D, BOOM, 80, 22, HOLE_M8, HOLE_M6, true, V_EX);
else if (PART == "vista_montado_quad_abrazadera") v_abraz(MAST_D, BOOM, 80, 22, HOLE_M8, HOLE_M6, true, 0);
else if (PART == "vista_despiece_brazo_mastil") v_abraz(MAST_D, ARM_D, 80, 22, HOLE_M8, HOLE_M6, false, V_EX, true);
else if (PART == "vista_montado_brazo_mastil") v_abraz(MAST_D, ARM_D, 80, 22, HOLE_M8, HOLE_M6, false, 0, true);
else if (PART == "vista_despiece_soporte_fibra") v_abraz(ARM_D, FIBRA_D, 64, 20, HOLE_M6, HOLE_M6, false, V_EX);
else if (PART == "vista_montado_soporte_fibra") v_abraz(ARM_D, FIBRA_D, 64, 20, HOLE_M6, HOLE_M6, false, 0);
else if (PART == "vista_despiece_discone") v_discone(V_EX);
else if (PART == "vista_montado_discone") v_discone(0);
else if (PART == "vista_despiece_discone_plantillas") v_plantillas(V_EX);
else if (PART == "vista_montado_discone_plantillas") v_plantillas(0);
else if (PART == "vista_despiece_adsb") v_adsb(V_EX);
else if (PART == "vista_montado_adsb") v_adsb(0);
else if (PART == "vista_despiece_mla") v_mla(V_EX);
else if (PART == "vista_montado_mla") v_mla(0);
else if (PART == "vista_despiece_mla_cruz") v_mla_cruz(V_EX);
else if (PART == "vista_montado_mla_cruz") v_mla_cruz(0);
else if (PART == "vista_despiece_gps") v_gps(V_EX);
else if (PART == "vista_montado_gps") v_gps(0);
else if (PART == "vista_despiece_fundas_tapones") v_fundas(V_EX);
else if (PART == "vista_montado_fundas_tapones") v_fundas(0);

// ---------------- VISTAS DE DOCUMENTACIÓN (solo lectura) ----------------
V_ORANGE = "#F26B1D"; V_INK = "#23272B"; V_GREY = "#59636B"; V_LIGHT = "#C9CED3";
V_EX = 50;          // separación del despiece (mm)
V_GRUB_L = 12;      // longitud orientativa de prisioneros y autorroscantes
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
// U de varilla roscada: dos patas verticales en p1 y p2 unidas por un travesaño a la altura zbar; las patas acaban en zleg
module v_ubolt(p1, p2, db, zbar, zleg) {
    color("silver") {
        for (p = [p1, p2]) translate([p[0], p[1], min(zbar, zleg)]) cylinder(d = db, h = abs(zleg - zbar), $fn = 16);
        hull() { for (p = [p1, p2]) translate([p[0], p[1], zbar]) sphere(d = db, $fn = 12); }
    }
}

// buje de boom con sus cuatro crucetas de fibra (fantasma), punteras, clips y tornillos
module v_buje_set(rod, largo, h, txt, z0, ex, clips) {
    s = BOOM + 12; xr = s / 2 + 4;
    color(V_ORANGE, ex > 0 ? 0.85 : 1) translate([0, 0, z0]) buje(rod, largo, h, txt);
    for (a = [0, 90, 180, 270]) rotate(a) {
        color("silver", 0.35) translate([xr + 0.6 * ex, 0, z0 + h / 2]) rotate([0, 90, 0]) cylinder(d = rod - 0.3, h = largo + 60, $fn = 24);
        color(V_GREY) translate([xr + largo + 60 - 17 + 1.4 * ex, 0, z0 + h / 2]) rotate([0, 90, 0]) puntera(rod);
        if (clips) color(V_LIGHT) translate([xr + largo + 25 + ex, 0, z0 + h / 2]) rotate([0, 90, 0]) clip_cruceta(rod);
        v_scr([s / 2 + largo - 8, 0, z0 + h / 2], "z", V_GRUB_L, 3, ex > 0 ? 25 : 0);
    }
    for (z = [10, h - 10]) v_scr([0, BOOM / 2, z0 + z], "y", V_GRUB_L, 5, ex > 0 ? 25 : 0, false);
}
module v_quad_buje(ex) {
    color("silver", 0.35) translate([-BOOM / 2, -BOOM / 2, -140]) cube([BOOM, BOOM, 360]);   // boom
    v_buje_set(ROD8, 40, 40, "2M", -0.4 * ex, ex, true);
    v_buje_set(ROD6, 30, 32, "70", 80 + 0.4 * ex, ex, false);   // separación entre bujes orientativa
}

module v_quad_alim(ex) {
    h = 16; d = 18;
    for (s = [-1, 1]) v_scr([s * 6, 0, 0], "z", h, 3, ex > 0 ? ex : 0);
    color(V_ORANGE) alimentacion(ROD8);
    v_tube([0, 0, -3 - 0.8 * ex - 45], "z", ROD8, 90);          // cruceta entra por abajo
    translate([80, 0, 0]) {
        color(V_ORANGE) alimentacion(ROD8, false);
        v_tube([0, -1.2 * ex, h / 2], "y", ROD8, 90);           // cruceta atraviesa el bloque
        for (s = [-1, 1]) v_scr([s * 6, 0, 0], "z", h, 3, ex > 0 ? ex : 0);
    }
}

// abrazadera cruzada con sus dos U de varilla roscada (mástil abajo, boom/brazo arriba)
module v_abraz(d1, d2, l, t, b1, b2, cuad, ex, tapon = false) {
    db1 = b1 - 0.6; db2 = b2 - 0.6; zm = -d1 / 2 + 5; zc = t + d2 / 2 - 6;
    color(V_ORANGE, ex > 0 ? 0.8 : 1) abrazadera_cruzada(d1, d2, l, t, b1, b2, cuad);
    v_tube([0, 0, zm], "y", d1, l + 80);
    if (cuad) color("silver", 0.35) translate([-(l + 80) / 2, -d2 / 2, t - 6]) cube([l + 80, d2, d2]);
    else v_tube([0, 0, zc], "x", d2, l + 80);
    xl = d1 / 2 + b1 / 2 + 1; zt1 = t + 0.8 * db1 + 3;
    for (yy = [-1, 1]) {
        y = yy * (l / 2 - 12);
        translate([0, 0, -ex]) v_ubolt([-xl, y], [xl, y], db1, zm - d1 / 2 - db1 / 2, zt1);
        for (sx = [-1, 1]) {
            v_nut([sx * xl, y, t + ex], 1.9 * db1, 0.8 * db1);
            if (ex > 0) v_guia([sx * xl, y, zt1 - ex], [sx * xl, y, t + ex]);
        }
    }
    yl = d2 / 2 + b2 / 2 + 1; zb2 = -(0.8 * db2 + 3);
    for (xx = [-1, 1]) {
        x = xx * (l / 2 - 10);
        translate([0, 0, ex]) v_ubolt([x, -yl], [x, yl], db2, zc + d2 / 2 + db2 / 2, zb2);
        for (sy = [-1, 1]) {
            v_nut([x, sy * yl, -0.8 * db2 - ex], 1.9 * db2, 0.8 * db2);
            if (ex > 0) v_guia([x, sy * yl, zb2 + ex], [x, sy * yl, -ex]);
        }
    }
    if (tapon) {
        color(V_LIGHT) translate([l / 2 + 40 + 4 + ex, 0, zc]) rotate([0, -90, 0]) tapon_brazo();
        if (ex > 0) v_guia([l / 2 + 40, 0, zc], [l / 2 + 40 + ex, 0, zc]);
    }
}

// discone: mástil → adaptador → buje de cono → aislador → buje de disco → capuchón (los bujes de aluminio son fantasmas)
module v_discone(ex) {
    k = 0.5 * ex;
    v_tube([0, 0, -52], "z", MAST_D, 200);
    color(V_ORANGE) translate([0, 0, k]) discone_adaptador_mastil();
    color("silver", 0.6) translate([0, 0, 66 + 2 * k]) cylinder(d = HUB_D, h = HUB_T, $fn = 64);   // buje de cono (Ø70 × 12)
    color(V_LIGHT) translate([0, 0, 78 + 3 * k]) discone_aislador();
    color("silver", 0.6) translate([0, 0, 98 + 4 * k]) cylinder(d = HUB_D, h = HUB_T, $fn = 64);   // buje de disco (Ø70 × 12)
    color(V_INK) translate([0, 0, 108 + 5 * k]) discone_capuchon();
    for (z = [12, 32]) v_scr([0, -(MAST_D + 10) / 2, z + k], "y", MAST_D + 10, 6, ex > 0 ? 0.9 * ex : 0);   // pasante M6 al mástil
    if (ex > 0) {
        for (a = [45 : 90 : 359]) v_guia([(HUB_D / 2 - 7) * cos(a), (HUB_D / 2 - 7) * sin(a), 66 + k], [(HUB_D / 2 - 7) * cos(a), (HUB_D / 2 - 7) * sin(a), 66 + 2 * k]);
        for (a = [0, 120, 240]) {
            v_guia([18 * cos(a), 18 * sin(a), 78 + 2 * k], [18 * cos(a), 18 * sin(a), 78 + 3 * k]);                 // M4 buje de cono ↔ aislador
            v_guia([18 * cos(a + 60), 18 * sin(a + 60), 98 + 3 * k], [18 * cos(a + 60), 18 * sin(a + 60), 98 + 4 * k]);   // M4 aislador ↔ buje de disco
        }
    }
}
module v_plantillas(ex) {
    translate([-60, 0, 0]) { color(V_ORANGE) plantilla_disco(); color("silver", 0.6) translate([0, 0, 3 + ex]) cylinder(d = HUB_D, h = HUB_T, $fn = 64); }
    translate([60, 0, 0]) { color(V_ORANGE) plantilla_cono(); color("silver", 0.6) translate([0, 0, 22 - HUB_T + ex]) cylinder(d = HUB_D, h = HUB_T, $fn = 64); }
}

// ADS-B: tapa bajo la base, radomo sobre la torreta, elemento de latón y 4 radiales (disposición orientativa)
module v_adsb(ex) {
    w = LNA[1] + 12; l = LNA[0] + 14; h = LNA[2] + 16;
    sa = ex; sr = 1.4 * ex; se = 0.6 * ex;
    color(V_ORANGE) adsb_base();
    color(V_GREY) translate([0, 0, -3 - sa]) adsb_tapa();
    color(V_LIGHT, 0.8) translate([0, 0, h + 1 + sr]) adsb_radomo();
    color("goldenrod") translate([0, 0, h + 8 + se]) cylinder(d = 2, h = 62, $fn = 12);
    for (a = [45 : 90 : 359]) rotate(a) color("goldenrod") translate([0.8 * ex, 0, h + 4]) rotate([0, 90, 0]) cylinder(d = 2, h = 68, $fn = 12);
    for (sx = [-1, 1], sy = [-1, 1]) v_scr([sx * (w / 2 - 4), sy * (l / 2 - 4), 3], "-z", 6, 3, ex > 0 ? 16 + sa : 0);
}

// caja del lazo MLA: base, junta, tapa girada 180° y 4 × M3 (longitud orientativa)
module v_mla(ex) {
    i = MLA_CAJA; zm = i[2] / 2 + 3;
    color(V_ORANGE) mla_caja_base();
    color(V_INK) translate([0, 0, zm - 0.8 + 0.5 * ex]) mla_junta();
    color(V_GREY) translate([0, 0, 2 * zm + ex]) rotate([180, 0, 0]) mla_caja_tapa();
    for (sx = [-1, 1], sy = [-1, 1]) v_scr([sx * (i[0] / 2 - 4), sy * (i[1] / 2 - 4), 2 * zm - 25], "z", 25, 3, ex > 0 ? ex + 35 : 0);
}
// cruz del lazo MLA: 4 varillas de fibra (fantasma), clips de lazo y autorroscantes
module v_mla_cruz(ex) {
    h = 30; s = 34;
    color(V_ORANGE) mla_cruz();
    for (a = [0, 90, 180, 270]) rotate(a) {
        color("silver", 0.35) translate([s / 2 + 2 + 0.6 * ex, 0, h / 2]) rotate([0, 90, 0]) cylinder(d = MLA_ROD - 0.3, h = 100, $fn = 24);
        color(V_GREY) translate([s / 2 + 2 + 100 - 17 + 1.4 * ex, 0, h / 2]) rotate([0, 90, 0]) mla_clip_lazo();
        v_scr([s / 2 + 30, 0, h / 2], "z", V_GRUB_L, 3, ex > 0 ? 25 : 0);
    }
    if (ex > 0) for (s2 = [-1, 1]) v_guia([s2 * 9, 0, 0], [s2 * 9, 0, -ex]);   // U M6 al mástil o al brazo
}

// GPS: soporte sobre el brazo Ø25 con dos U M6 y el puck encajado desde arriba
module v_gps(ex) {
    zt = -ARM_D / 2; db = HOLE_M6 - 0.6; xl = ARM_D / 2 + 4; ztop = 6 + 0.8 * db + 3;
    v_tube([0, 0, zt], "y", ARM_D, 120);
    color(V_ORANGE) translate([0, 0, ex]) gps_soporte();
    color(V_GREY, 0.8) translate([-GPS_PUCK[0] / 2, -GPS_PUCK[1] / 2, 6 + 2 * ex]) cube(GPS_PUCK);
    for (y = [-27, 27]) {
        v_ubolt([-xl, y], [xl, y], db, zt - ARM_D / 2 - db / 2, ztop);
        for (sx = [-1, 1]) {
            v_nut([sx * xl, y, 6 + 1.5 * ex], 1.9 * db, 0.8 * db);
            if (ex > 0) v_guia([sx * xl, y, ztop], [sx * xl, y, 6 + 1.5 * ex]);
        }
    }
}

// accesorios: fundas de TPU sobre cable, clip de filtro, separador de coaxial y tapón de varilla
module v_fundas(ex) {
    translate([-90, 0, 0]) { v_tube([0, 0, 20], "z", 7, 120); color(V_INK) translate([0, 0, ex]) funda_conector(9.5, 40); }
    translate([-45, 0, 0]) { v_tube([0, 0, 20], "z", 12, 120); color(V_INK) translate([0, 0, ex]) funda_conector(17, 50); }
    translate([0, 0, 0]) {
        color(V_ORANGE) clip_filtro();
        color("silver", 0.5) translate([-6.5, -30, 3 + ex]) cube([13, 60, 13]);   // filtro (≈ 13 × 13; largo esquemático)
        if (ex > 0) v_guia([0, 0, 3], [0, 0, 3 + ex]);
    }
    translate([60, 0, 0]) {
        color(V_ORANGE) separador_coax();
        color("black", 0.7) translate([0, 36 + ex, -10]) cylinder(d = 7, h = 30, $fn = 24);   // coaxial: entra por la ranura (-Y)
        if (ex > 0) v_guia([0, 36, 5], [0, 36 + ex, 5]);
    }
    translate([110, 0, 0]) {
        v_tube([0, 0, -45], "z", 4.2, 112);
        color(V_LIGHT) translate([0, 0, ex]) tapon_varilla();
    }
}
