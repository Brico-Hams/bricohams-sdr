/* BricoHams RAK4631 LoRa APRS · port de LoRa APRS iGate (CA2RXU) a WisBlock
 * Copyright (C) 2026 Ricardo Guzman - CA2RXU (original) · BricoHams contributors (port nRF52)
 * GPL-3.0-or-later (ver LICENSE).
 */
#ifndef DIGI_UTILS_H_
#define DIGI_UTILS_H_

#include <Arduino.h>

namespace DIGI_Utils {
    String cleanPath(const String& path);
    String generateDigipeatedPacket(const String& packet);   // "" si no toca repetir
    bool   isDuplicate(const String& packet);                 // ya visto en los últimos 25 s
    bool   callsignIsValid(const String& callsign);
}

#endif
