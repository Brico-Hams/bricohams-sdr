/* BricoHams RAK4631 LoRa APRS · port de LoRa APRS iGate (CA2RXU) a WisBlock
 * Copyright (C) 2026 Ricardo Guzman - CA2RXU (original) · BricoHams contributors (port nRF52)
 * GPL-3.0-or-later (ver LICENSE).
 */
#ifndef LORA_UTILS_H_
#define LORA_UTILS_H_

#include <Arduino.h>

struct LoRaRx {
    String  packet;     // TNC2 sin la cabecera "<\xff\x01"
    int     rssi;
    float   snr;
    long    freqError;
};

namespace LoRa_Utils {
    bool    setup();                        // false si el SX1262 no responde
    bool    applyConfig();                  // frecuencia, SF, BW, CR, potencia
    bool    receivePacket(LoRaRx& rx);      // true si hay un paquete LoRa APRS válido
    bool    sendNewPacket(const String& packet);
    int     lastState();
    extern uint32_t crcErrors;
}

#endif
