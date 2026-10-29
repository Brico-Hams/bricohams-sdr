/* BricoHams RAK4631 LoRa APRS · port de LoRa APRS iGate (CA2RXU) a WisBlock
 * Copyright (C) 2026 Ricardo Guzman - CA2RXU (original) · BricoHams contributors (port nRF52)
 * GPL-3.0-or-later (ver LICENSE).
 */
#include <ArduinoJson.h>
#include <Adafruit_LittleFS.h>
#include <InternalFileSystem.h>
#include "configuration.h"

using namespace Adafruit_LittleFS_Namespace;

#define CONFIG_FILE "/bh_aprs.json"

Configuration Config;

static bool fsReady = false;

String Configuration::toJson() const {
    JsonDocument d;
    d["callsign"] = callsign;            d["comment"] = comment;
    d["symbol"] = String(symbolTable) + String(symbolCode);
    d["path"] = path;                    d["status"] = status;      d["ambiguity"] = ambiguity;
    d["lat"] = latitude;                 d["lon"] = longitude;      d["alt"] = altitude;
    d["gps"] = gpsActive;                d["gpsBeacon"] = gpsBeacon;
    d["freq"] = freq;                    d["sf"] = sf;              d["bw"] = bw;      d["cr"] = cr;
    d["power"] = power;                  d["tx"] = txActive;        d["cad"] = cadActive;
    d["digi"] = digiMode;
    d["beaconMin"] = beaconMin;          d["beaconRF"] = beaconRF;
    d["telemetryMin"] = telemetryMin;    d["telemetryRF"] = telemetryRF;
    d["tempInComment"] = tempInComment;  d["tempOffset"] = tempOffset;
    d["battery"] = batteryActive;
    d["kissOwn"] = kissOwnPackets;       d["statusSec"] = statusSec;
    String out;
    serializeJson(d, out);
    return out;
}

static bool validCallsign(const String& c) {
    if (c.length() < 3 || c.length() > 9) return false;
    for (unsigned i = 0; i < c.length(); i++) {
        char x = c[i];
        if (!(isUpperCase(x) || isDigit(x) || x == '-')) return false;
    }
    return true;
}

bool Configuration::fromJson(const String& json, String& error) {
    JsonDocument d;
    DeserializationError e = deserializeJson(d, json);
    if (e) { error = String("JSON: ") + e.c_str(); return false; }
    Configuration n = *this;             // se valida todo antes de aplicar nada
    if (d["callsign"].is<const char*>()) { n.callsign = String((const char*)d["callsign"]); n.callsign.toUpperCase(); }
    if (d["comment"].is<const char*>())  n.comment = String((const char*)d["comment"]).substring(0, 43);
    if (d["symbol"].is<const char*>()) {
        String s = d["symbol"].as<const char*>();
        if (s.length() == 2) { n.symbolTable = s[0]; n.symbolCode = s[1]; }
    }
    if (d["path"].is<const char*>())     n.path = String((const char*)d["path"]);
    if (d["status"].is<const char*>())   n.status = String((const char*)d["status"]).substring(0, 62);
    if (d["ambiguity"].is<int>())        n.ambiguity = d["ambiguity"];
    if (d["lat"].is<double>())           n.latitude = d["lat"];
    if (d["lon"].is<double>())           n.longitude = d["lon"];
    if (d["alt"].is<int>())              n.altitude = d["alt"];
    if (d["gps"].is<bool>())             n.gpsActive = d["gps"];
    if (d["gpsBeacon"].is<bool>())       n.gpsBeacon = d["gpsBeacon"];
    if (d["freq"].is<uint32_t>())        n.freq = d["freq"];
    if (d["sf"].is<int>())               n.sf = d["sf"];
    if (d["bw"].is<long>())              n.bw = d["bw"];
    if (d["cr"].is<int>())               n.cr = d["cr"];
    if (d["power"].is<int>())            n.power = d["power"];
    if (d["tx"].is<bool>())              n.txActive = d["tx"];
    if (d["cad"].is<bool>())             n.cadActive = d["cad"];
    if (d["digi"].is<int>())             n.digiMode = d["digi"];
    if (d["beaconMin"].is<int>())        n.beaconMin = d["beaconMin"];
    if (d["beaconRF"].is<bool>())        n.beaconRF = d["beaconRF"];
    if (d["telemetryMin"].is<int>())     n.telemetryMin = d["telemetryMin"];
    if (d["telemetryRF"].is<bool>())     n.telemetryRF = d["telemetryRF"];
    if (d["tempInComment"].is<bool>())   n.tempInComment = d["tempInComment"];
    if (d["tempOffset"].is<float>())     n.tempOffset = d["tempOffset"];
    if (d["battery"].is<bool>())         n.batteryActive = d["battery"];
    if (d["kissOwn"].is<bool>())         n.kissOwnPackets = d["kissOwn"];
    if (d["statusSec"].is<int>())        n.statusSec = d["statusSec"];

    if (!validCallsign(n.callsign))                     { error = "indicativo no válido"; return false; }
    if (n.latitude < -90 || n.latitude > 90 || n.longitude < -180 || n.longitude > 180) { error = "posición"; return false; }
    if (n.freq < 410000000UL || n.freq > 525000000UL)   { error = "frecuencia fuera de 410-525 MHz (RAK4631(L))"; return false; }
    if (n.sf < 7 || n.sf > 12)                          { error = "SF 7-12"; return false; }
    if (n.bw != 62500 && n.bw != 125000 && n.bw != 250000 && n.bw != 500000) { error = "BW"; return false; }
    if (n.cr < 5 || n.cr > 8)                           { error = "CR 5-8"; return false; }
    if (n.power < -9 || n.power > 22)                   { error = "potencia -9..22 dBm"; return false; }
    if (n.digiMode < 0 || n.digiMode > 3)               { error = "digi 0-3"; return false; }
    if (n.ambiguity < 0 || n.ambiguity > 4)             { error = "ambiguedad 0-4"; return false; }
    if (n.beaconMin < 0 || n.telemetryMin < 0 || n.statusSec < 5) { error = "intervalos"; return false; }
    if (n.beaconMin > 0 && n.beaconMin < 5)             n.beaconMin = 5;      // no saturar el canal
    *this = n;
    return true;
}

uint32_t Configuration::checksum() const {     // CRC32 del JSON: la Pi lo compara antes de reenviar
    String s = toJson();
    uint32_t crc = 0xFFFFFFFF;
    for (unsigned i = 0; i < s.length(); i++) {
        crc ^= (uint8_t)s[i];
        for (int k = 0; k < 8; k++) crc = (crc >> 1) ^ (0xEDB88320 & (-(int32_t)(crc & 1)));
    }
    return ~crc;
}

bool Configuration::begin() {
    fsReady = InternalFS.begin();
    if (!fsReady) return false;
    File f(InternalFS);
    if (!f.open(CONFIG_FILE, FILE_O_READ)) return false;
    String s;
    while (f.available()) s += (char)f.read();
    f.close();
    String err;
    return fromJson(s, err);
}

bool Configuration::save() {
    if (!fsReady) return false;
    InternalFS.remove(CONFIG_FILE);
    File f(InternalFS);
    if (!f.open(CONFIG_FILE, FILE_O_WRITE)) return false;
    String s = toJson();
    f.write((const uint8_t*)s.c_str(), s.length());
    f.close();
    return true;
}
