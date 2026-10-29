/* BricoHams RAK4631 LoRa APRS · BricoHams contributors · GPL-3.0-or-later (ver LICENSE).
 *
 * Temperatura del interior de la caja, GPS y batería.
 * Sensores (se detectan solos al arrancar, por este orden):
 *   RAK1901 SHTC3 (0x70) · RAK1906 BME680 (0x76/0x77) · BME280 (0x76/0x77)
 *   y, si no hay ninguno, el sensor interno del nRF52840 (indica la del módulo, no la del aire).
 * GPS (slot A): RAK1910 o RAK12500, NMEA a 9600 baudios por Serial1.
 */
#ifndef SENSOR_UTILS_H_
#define SENSOR_UTILS_H_

#include <Arduino.h>

struct SensorData {
    bool    tempOk      = false;
    float   temp        = NAN;      // °C (con tempOffset)
    float   hum         = NAN;      // %
    float   pres        = NAN;      // hPa
    const char* source  = "ninguno";
    float   vbat        = NAN;      // V
};

// Medida válida dentro de [lo, hi]. No usa isnan(): en el RAK real se colaba "vbat": nan en el
// JSON (v4.5, despliegue N0CALL); con NaN cualquier comparación da false, así que esto lo filtra siempre.
inline bool medidaValida(float v, float lo, float hi) { return v >= lo && v <= hi; }

struct GpsData {
    bool     present    = false;    // llegan frases NMEA
    bool     fix        = false;
    double   lat        = 0, lon = 0;
    float    alt        = 0, hdop = 99;
    uint8_t  sats       = 0;
    uint32_t ageMs      = 0;
    String   utc;                   // "2026-10-11T10:20:30Z"
};

namespace Sensor_Utils {
    void        setup();
    void        read();             // cada 30 s
    void        gpsLoop();          // alimentar el NMEA en cada vuelta
    SensorData& data();
    GpsData&    gps();
}

#endif
