// Prueba en el PC de la lógica del firmware (sin radio): la compila y la llama tests/test_rak_aprs.py.
//   host_test kiss  "TNC2"      -> trama KISS en hexadecimal
//   host_test unkiss HEX        -> TNC2
//   host_test digi MODO "TNC2"  -> paquete a repetir ("" si no toca)
//   host_test beacon LAT LON    -> baliza propia
//   host_test telem             -> telemetría
//   host_test dup "TNC2" "TNC2" -> 0/1 (segundo es duplicado)
#include <iostream>
#include "Arduino.h"
#include "../configuration.h"
#include "../kiss_utils.h"
#include "../digi_utils.h"
#include "../aprs_utils.h"
#include "../sensor_utils.h"

unsigned long fake_millis = 100000;
Configuration Config;
static SensorData sd;
static GpsData gd;
namespace Sensor_Utils {
    SensorData& data() { return sd; }
    GpsData& gps() { return gd; }
}
uint32_t Configuration::checksum() const { return 0; }

static std::string hex(const String& s) {
    static const char* h = "0123456789abcdef";
    std::string o;
    for (unsigned i = 0; i < s.length(); i++) { uint8_t c = s[i]; o += h[c >> 4]; o += h[c & 15]; }
    return o;
}
static String unhex(const std::string& x) {
    String o;
    for (size_t i = 0; i + 1 < x.size(); i += 2) o += (char)strtol(x.substr(i, 2).c_str(), nullptr, 16);
    return o;
}

int main(int argc, char** argv) {
    if (argc < 2) return 2;
    std::string c = argv[1];
    Config.callsign = "N0CALL-10";
    if (c == "kiss") { std::cout << hex(encodeKISS(String(argv[2]))) << "\n"; return 0; }
    if (c == "unkiss") { bool d = false; std::cout << decodeKISS(unhex(argv[2]), d).c_str() << "\n"; return d ? 0 : 1; }
    if (c == "digi") { Config.digiMode = atoi(argv[2]); std::cout << DIGI_Utils::generateDigipeatedPacket(String(argv[3])).c_str() << "\n"; return 0; }
    if (c == "dup") { DIGI_Utils::isDuplicate(String(argv[2])); fake_millis += 1000; std::cout << DIGI_Utils::isDuplicate(String(argv[3])) << "\n";
                      fake_millis += 30000; std::cout << DIGI_Utils::isDuplicate(String(argv[3])) << "\n"; return 0; }
    if (c == "beacon") {
        Config.latitude = atof(argv[2]); Config.longitude = atof(argv[3]); Config.altitude = 230;
        sd.tempOk = true; sd.temp = 23.44f;
        std::cout << APRS_Utils::beacon(false).c_str() << "\n" << APRS_Utils::beacon(true).c_str() << "\n";
        Config.ambiguity = 1; Config.status = "N0CALL-SDR BricoHams"; Config.path = "WIDE1-1,WIDE2-1";
        std::cout << APRS_Utils::beacon(true).c_str() << "\n" << APRS_Utils::status(false).c_str() << "\n";
        Config.ambiguity = 3;
        std::cout << APRS_Utils::latitude(37.983815).c_str() << "|" << APRS_Utils::longitude(-1.128013).c_str() << "\n";
        return 0;
    }
    if (c == "telem") {
        sd.tempOk = true; sd.temp = 31.5f; sd.hum = 40.2f; sd.vbat = 4.1f; gd.fix = true;
        std::cout << APRS_Utils::telemetry(false, 7, 2).c_str() << "\n";
        for (int i = 0; i < 4; i++) std::cout << APRS_Utils::telemetryDefinition(false, i).c_str() << "\n";
        return 0;
    }
    return 2;
}
