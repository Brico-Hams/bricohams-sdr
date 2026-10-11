/* BricoHams RAK4631 LoRa APRS · EA5KAO / BricoHams · GPL-3.0-or-later (ver LICENSE).
 * Paquetes propios: baliza de posición y telemetría (temperatura de la caja).
 * Equivale a la baliza de src/utils.cpp y a src/telemetry_utils.cpp del original,
 * en formato sin comprimir para no depender de APRSPacketLib.
 */
#ifndef APRS_UTILS_H_
#define APRS_UTILS_H_

#include <Arduino.h>

namespace APRS_Utils {
    String latitude(double lat);                  // "3804.94N"
    String longitude(double lon);                 // "00115.21W"
    String header(bool viaRF);                    // "EA5KAO-10>APZBH1[,WIDE1-1]"
    String beacon(bool viaRF);
    String status(bool viaRF);                    // ">texto" o "" si no hay
    String telemetry(bool viaRF, uint32_t rxCount, uint32_t digiCount);
    String telemetryDefinition(bool viaRF, int which);   // 0 PARM · 1 UNIT · 2 EQNS · 3 BITS
}

#endif
