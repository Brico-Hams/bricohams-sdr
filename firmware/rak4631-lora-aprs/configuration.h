/* BricoHams RAK4631 LoRa APRS · port de LoRa APRS iGate (CA2RXU) a WisBlock
 * Copyright (C) 2026 Ricardo Guzman - CA2RXU (original) · BricoHams contributors (port nRF52)
 * GPL-3.0-or-later (ver LICENSE).
 *
 * Configuración. El original guarda /igate_conf.json en SPIFFS y la edita por su web (WiFi).
 * El nRF52840 no tiene WiFi: aquí se guarda /bh_aprs.json en la flash interna (LittleFS)
 * y la escribe la Raspberry por el USB con la orden KISS 0x06 «BH:CFG {json}».
 */
#ifndef CONFIGURATION_H_
#define CONFIGURATION_H_

#include <Arduino.h>

#define FW_NAME     "BricoHams-RAK-APRS"
#define FW_VERSION  "1.0.0"
#define APRS_TOCALL "APZBH1"            // APZ = experimental (hasta registrar uno propio)

class Configuration {
public:
    // identidad
    String  callsign        = "N0CALL-10";
    String  comment         = "SDR BricoHams LoRa APRS";
    char    symbolTable     = 'L';      // L& = pasarela LoRa
    char    symbolCode      = '&';
    String  path            = "WIDE1-1"; // solo para lo que sale por RF
    String  status          = "";       // paquete de estado (">texto") tras cada baliza; vacío = no
    int     ambiguity       = 0;        // ambigüedad de posición APRS 0-4 (1 = ~185 m)
    // posición fija (se usa si no hay GPS o si gpsBeacon = false)
    double  latitude        = 0.0;
    double  longitude       = 0.0;
    int     altitude        = 0;        // m
    bool    gpsActive       = true;
    bool    gpsBeacon       = false;    // true: la baliza usa la posición del GPS cuando hay fix
    // radio (LoRa APRS Europa: 433,775 MHz, SF12, BW 125 kHz, CR 4/5)
    uint32_t freq           = 433775000;
    int     sf              = 12;
    long    bw              = 125000;
    int     cr              = 5;
    int     power           = 20;       // dBm (SX1262: -9..22)
    bool    txActive        = false;    // false = solo escucha (no molesta a los SDR de la caja)
    bool    cadActive       = true;     // escuchar antes de hablar
    // digipeater: 0 apagado · 1 WIDE1-1 (fill-in) · 2 WIDE1-1 + WIDE2-n · 3 solo si va a mi indicativo
    int     digiMode        = 0;
    // balizas y telemetría
    int     beaconMin       = 15;
    bool    beaconRF        = false;    // además de entregarla a la Pi (APRS-IS)
    int     telemetryMin    = 10;
    bool    telemetryRF     = false;
    bool    tempInComment   = true;     // «Caja 23.4C» al final del comentario
    float   tempOffset      = 0.0;      // °C, corrección del sensor de la caja
    bool    batteryActive   = false;    // con batería en la base
    // enlace con la Pi
    bool    kissOwnPackets  = true;     // baliza y telemetría también por KISS (la Pi las sube a APRS-IS)
    int     statusSec       = 60;

    bool begin();                       // monta la flash y lee el fichero (o deja los valores por defecto)
    bool save();
    bool fromJson(const String& json, String& error);   // mezcla las claves recibidas
    String toJson() const;
    uint32_t checksum() const;
};

extern Configuration Config;

#endif
