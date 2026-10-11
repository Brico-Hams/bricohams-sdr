/* BricoHams RAK4631 LoRa APRS · EA5KAO / BricoHams · GPL-3.0-or-later (ver LICENSE). */
#include <Wire.h>
#include <TinyGPS++.h>
#include <Adafruit_BME280.h>
#include <Adafruit_BME680.h>
#include <nrf_soc.h>
#include "board_pinout.h"
#include "configuration.h"
#include "sensor_utils.h"

enum Kind { NONE, SHTC3, BME680, BME280, DIE };
static Kind kind = NONE;
static uint8_t addr = 0;
static Adafruit_BME280 bme280;
static Adafruit_BME680 bme680;
static TinyGPSPlus gpsParser;
static SensorData sd;
static GpsData gd;

static bool i2cPresent(uint8_t a) {
    Wire.beginTransmission(a);
    return Wire.endTransmission() == 0;
}

static uint8_t readChipId(uint8_t a) {
    Wire.beginTransmission(a);
    Wire.write(0xD0);
    if (Wire.endTransmission(false) != 0) return 0;
    if (Wire.requestFrom(a, (uint8_t)1) != 1) return 0;
    return Wire.read();
}

// ---- SHTC3 (RAK1901) sin librería: wake 0x3517, medir 0x7866 (T primero), sleep 0xB098
static bool shtcCmd(uint16_t c) {
    Wire.beginTransmission(0x70);
    Wire.write(c >> 8); Wire.write(c & 0xFF);
    return Wire.endTransmission() == 0;
}
static uint8_t crc8(const uint8_t* d, int n) {
    uint8_t crc = 0xFF;
    for (int i = 0; i < n; i++) {
        crc ^= d[i];
        for (int b = 0; b < 8; b++) crc = (crc & 0x80) ? (crc << 1) ^ 0x31 : (crc << 1);
    }
    return crc;
}
static bool shtcRead(float& t, float& h) {
    if (!shtcCmd(0x3517)) return false;
    delay(1);
    if (!shtcCmd(0x7866)) return false;
    delay(15);
    uint8_t b[6];
    if (Wire.requestFrom((uint8_t)0x70, (uint8_t)6) != 6) return false;
    for (int i = 0; i < 6; i++) b[i] = Wire.read();
    shtcCmd(0xB098);
    if (crc8(b, 2) != b[2] || crc8(b + 3, 2) != b[5]) return false;
    t = -45.0f + 175.0f * (float)((b[0] << 8) | b[1]) / 65536.0f;
    h = 100.0f * (float)((b[3] << 8) | b[4]) / 65536.0f;
    return true;
}

static float dieTemp() {
    uint8_t en = 0;
    sd_softdevice_is_enabled(&en);
    if (en) { int32_t t; sd_temp_get(&t); return t * 0.25f; }
    NRF_TEMP->TASKS_START = 1;
    uint32_t t0 = millis();
    while (!NRF_TEMP->EVENTS_DATARDY && millis() - t0 < 50) {}
    NRF_TEMP->EVENTS_DATARDY = 0;
    float v = (int32_t)NRF_TEMP->TEMP * 0.25f;
    NRF_TEMP->TASKS_STOP = 1;
    return v;
}

namespace Sensor_Utils {

    SensorData& data() { return sd; }
    GpsData&    gps()  { return gd; }

    void setup() {
        pinMode(VEXT_CTRL_PIN, OUTPUT);
        digitalWrite(VEXT_CTRL_PIN, VEXT_CTRL_ON_STATE);       // 3V3_S: sensores y GPS
        delay(300);
        Wire.begin();
        if (i2cPresent(0x70)) { kind = SHTC3; addr = 0x70; }
        else {
            static const uint8_t candidatos[] = {0x76, 0x77};
            for (uint8_t a : candidatos) {
                if (!i2cPresent(a)) continue;
                uint8_t id = readChipId(a);
                if (id == 0x61 && bme680.begin(a)) {
                    kind = BME680; addr = a;
                    bme680.setTemperatureOversampling(BME680_OS_8X);
                    bme680.setHumidityOversampling(BME680_OS_2X);
                    bme680.setPressureOversampling(BME680_OS_4X);
                    bme680.setGasHeater(0, 0);                  // sin calentador: no falsea la temperatura
                    break;
                }
                if (id == 0x60 && bme280.begin(a)) { kind = BME280; addr = a; break; }
            }
        }
        if (kind == NONE) kind = DIE;
        if (Config.gpsActive) {
            Serial1.begin(GPS_BAUDRATE);
        }
        if (Config.batteryActive) {
            analogReference(AR_INTERNAL_3_0);
            analogReadResolution(12);
        }
        read();
    }

    void read() {
        float t = NAN, h = NAN, p = NAN;
        bool ok = false;
        switch (kind) {
            case SHTC3:  ok = shtcRead(t, h); sd.source = "SHTC3 (RAK1901)"; break;
            case BME680: ok = bme680.performReading();
                         if (ok) { t = bme680.temperature; h = bme680.humidity; p = bme680.pressure / 100.0f; }
                         sd.source = "BME680 (RAK1906)"; break;
            case BME280: t = bme280.readTemperature(); h = bme280.readHumidity(); p = bme280.readPressure() / 100.0f;
                         ok = !isnan(t); sd.source = "BME280"; break;
            default:     t = dieTemp(); ok = true; sd.source = "nRF52840 interno"; break;
        }
        sd.tempOk = ok && t > -40 && t < 125;
        sd.temp = sd.tempOk ? t + Config.tempOffset : NAN;
        sd.hum = h; sd.pres = p;
        if (Config.batteryActive) {
            uint32_t raw = 0;
            for (int i = 0; i < 8; i++) raw += analogRead(BATTERY_PIN);
            sd.vbat = (raw / 8.0f) * 3.0f / 4096.0f * BATTERY_DIVIDER;
        }
    }

    void gpsLoop() {
        if (!Config.gpsActive) return;
        while (Serial1.available()) {
            gpsParser.encode(Serial1.read());
            gd.present = true;
        }
        gd.fix = gpsParser.location.isValid() && gpsParser.location.age() < 10000;
        if (gpsParser.location.isValid()) {
            gd.lat = gpsParser.location.lat();
            gd.lon = gpsParser.location.lng();
            gd.ageMs = gpsParser.location.age();
        }
        if (gpsParser.altitude.isValid()) gd.alt = gpsParser.altitude.meters();
        if (gpsParser.hdop.isValid()) gd.hdop = gpsParser.hdop.hdop();
        if (gpsParser.satellites.isValid()) gd.sats = gpsParser.satellites.value();
        if (gpsParser.date.isValid() && gpsParser.time.isValid() && gpsParser.date.year() > 2020) {
            char b[40];
            snprintf(b, sizeof b, "%04d-%02d-%02dT%02d:%02d:%02dZ", gpsParser.date.year(), gpsParser.date.month(),
                     gpsParser.date.day(), gpsParser.time.hour(), gpsParser.time.minute(), gpsParser.time.second());
            gd.utc = b;
        }
    }
}
