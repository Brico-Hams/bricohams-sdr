/* BricoHams RAK4631 LoRa APRS · port de LoRa APRS iGate (CA2RXU) a WisBlock
 * Copyright (C) 2026 Ricardo Guzman - CA2RXU (original) · BricoHams contributors (port nRF52)
 * GPL-3.0-or-later (ver LICENSE).
 *
 * Lógica del digipeater tomada de src/digi_utils.cpp (cleanPath, pathTokenIndex,
 * processMode3Path, buildPacket, generateDigipeatedPacket), del buffer de 25 s de
 * src/station_utils.cpp y de Utils::callsignIsValid. Cambios: una sola frecuencia
 * (sin crossFreq ni backupDigiMode) y los paquetes de terceros ("}") no se repiten.
 */
#include "configuration.h"
#include "digi_utils.h"

namespace DIGI_Utils {

    String cleanPath(const String& path) {
        String result;
        unsigned int start = 0;
        while (true) {
            int delim = path.indexOf(',', start);
            int end = (delim == -1) ? path.length() : delim;
            String token = path.substring(start, end);
            if (token != "WIDE1*" && token != "WIDE2*") {
                if (result.length() > 0) result += ",";
                result += token;
            }
            if (delim == -1) break;
            start = delim + 1;
        }
        return result;
    }

    static int pathTokenIndex(const String& path, const String& token) {
        unsigned int start = 0;
        while (start < path.length()) {
            int end = path.indexOf(",", start);
            if (end == -1) end = path.length();
            if (path.substring(start, end) == token) return start;
            start = end + 1;
        }
        return -1;
    }

    static String processMode3Path(const String& path, const String& stationCallsign) {
        unsigned int start = 0;
        bool prevTokensAllStar = true;
        int ownTokenEnd = -1;
        while (start < path.length()) {
            int delim = path.indexOf(',', start);
            if (delim == -1) delim = path.length();
            String token = path.substring(start, delim);
            bool tokenIsOwn = (token == stationCallsign) || (token == stationCallsign + "*");
            bool tokenStar = token.endsWith("*");
            if (tokenIsOwn) {
                if (tokenStar) return "";
                if (!prevTokensAllStar) return "";
                ownTokenEnd = delim;
                break;
            }
            if (!tokenStar) prevTokensAllStar = false;
            start = delim + 1;
        }
        if (ownTokenEnd == -1) return "";
        String tempPacket = cleanPath(path.substring(0, ownTokenEnd));
        return tempPacket + "*" + path.substring(ownTokenEnd);
    }

    static String buildPacket(const String& path, const String& packet) {
        const String& stationCallsign = Config.callsign;
        int suffixIndex = packet.indexOf(":");
        int digiMode = Config.digiMode;
        String tempPath = path;
        if (tempPath.indexOf("WIDE1-1") != -1 && (digiMode == 1 || digiMode == 2)) {
            if (tempPath.indexOf("*") != -1) return "";
            if (pathTokenIndex(tempPath, "WIDE1-1") != 0) return "";
            tempPath = stationCallsign + "*" + tempPath.substring(7);
        } else if (tempPath.indexOf("WIDE2-") != -1 && digiMode == 2) {
            tempPath = cleanPath(path);
            int idx = pathTokenIndex(tempPath, "WIDE2-1");
            if (idx != -1) {
                tempPath = tempPath.substring(0, idx) + stationCallsign + "*" + tempPath.substring(idx + 7);
            } else {
                idx = pathTokenIndex(tempPath, "WIDE2-2");
                if (idx == -1) return "";
                tempPath = tempPath.substring(0, idx) + stationCallsign + "*,WIDE2-1" + tempPath.substring(idx + 7);
            }
        } else if (digiMode == 3) {
            tempPath = processMode3Path(tempPath, stationCallsign);
            if (tempPath == "") return "";
        } else {
            return "";
        }
        String out = packet.substring(0, packet.indexOf(",") + 1);
        out += tempPath;
        out += packet.substring(suffixIndex);
        return out;
    }

    String generateDigipeatedPacket(const String& packet) {
        if (Config.digiMode == 0) return "";
        int colon = packet.indexOf(':');
        if (colon < 0 || packet.charAt(colon + 1) == '}') return "";        // terceros: no
        String header = packet.substring(packet.indexOf('>') + 1, colon);
        if (header.indexOf("NOGATE") >= 0 || header.indexOf("TCPIP") >= 0) return "";
        String sender = packet.substring(0, packet.indexOf('>'));
        if (sender == Config.callsign) return "";                              // lo mío no
        if (!callsignIsValid(sender)) return "";
        int commaIndex = header.indexOf(",");
        if (commaIndex <= 2) return "";                                        // sin ruta: nada que repetir
        const String path = header.substring(commaIndex + 1);
        int digiMode = Config.digiMode;
        if (digiMode == 1) {
            return path.indexOf("WIDE1-1") != -1 ? buildPacket(path, packet) : "";
        }
        if (digiMode == 2) {
            int w1 = path.indexOf("WIDE1-1"), w2 = path.indexOf("WIDE2-");
            if (w1 != -1 && w2 != -1 && w2 < w1) return "";
            return (w1 != -1 || w2 != -1) ? buildPacket(path, packet) : "";
        }
        if (digiMode == 3) {
            return path.indexOf(Config.callsign) != -1 ? buildPacket(path, packet) : "";
        }
        return "";
    }

    struct Seen { uint32_t t; uint32_t hash; };
    #define SEEN_MAX 40
    static Seen seen[SEEN_MAX];                     // buffer de 25 s (como isIn25SegHashBuffer)

    static uint32_t makeHash(const String& s) {      // FNV-1a
        uint32_t h = 2166136261u;
        for (unsigned i = 0; i < s.length(); i++) { h ^= (uint8_t)s[i]; h *= 16777619u; }
        return h;
    }

    bool isDuplicate(const String& packet) {
        uint32_t now = millis();
        int gt = packet.indexOf('>'), colon = packet.indexOf(':');
        if (gt < 0 || colon < 0) return true;
        uint32_t h = makeHash(packet.substring(0, gt) + packet.substring(colon + 1));   // origen + datos (sin ruta)
        if (h == 0) h = 1;
        int libre = 0;
        uint32_t masViejo = 0;
        for (int i = 0; i < SEEN_MAX; i++) {
            bool vivo = seen[i].hash != 0 && now - seen[i].t <= 25000;
            if (vivo && seen[i].hash == h) return true;
            uint32_t edad = vivo ? now - seen[i].t : 0xFFFFFFFF;
            if (edad >= masViejo) { masViejo = edad; libre = i; }
        }
        seen[libre].t = now;
        seen[libre].hash = h;
        return false;
    }

    bool callsignIsValid(const String& callsign) {    // versión simplificada de Utils::callsignIsValid
        int n = callsign.length();
        if (n < 4 || n > 9) return false;
        int hyphen = callsign.indexOf('-');
        int base = hyphen > 0 ? hyphen : n;
        if (base < 4 || base > 6) return false;
        if (hyphen > 0) {
            int ssidLen = n - hyphen - 1;
            if (ssidLen < 1 || ssidLen > 2) return false;
            if (ssidLen == 2 && callsign[hyphen + 1] == '0') return false;
            for (int i = hyphen + 1; i < n; i++) if (!isDigit(callsign[i])) return false;
        }
        bool hasDigit = false;
        for (int i = 0; i < base; i++) {
            char c = callsign[i];
            if (!isAlphaNumeric(c)) return false;
            if (isDigit(c)) hasDigit = true;
        }
        return hasDigit;
    }
}
