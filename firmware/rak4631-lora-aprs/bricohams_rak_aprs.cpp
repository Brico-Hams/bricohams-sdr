/* BricoHams RAK4631 LoRa APRS · port de LoRa APRS iGate (CA2RXU) a WisBlock
 * Copyright (C) 2026 Ricardo Guzman - CA2RXU (original) · BricoHams contributors (port nRF52)
 * GPL-3.0-or-later (ver LICENSE).
 *
 * Equivale a src/LoRa_APRS_iGate.cpp del original. Reparto del trabajo:
 *  - RAK4631 (este firmware): radio LoRa APRS 433,775 MHz, digipeater, baliza, telemetría
 *    con la temperatura de la caja, GPS y TNC KISS por el USB (como tnc.enableSerial).
 *  - Raspberry Pi (bricohams-rak-aprs): la parte de Internet que el original hace por WiFi
 *    (APRS-IS, reglas de iGate) y la configuración (el original la hace por su web).
 *
 * Protocolo por el USB (CDC, cualquier velocidad):
 *  - KISS de datos (orden 0x00): RAK -> Pi lo recibido por RF y los paquetes propios;
 *    Pi -> RAK lo que hay que transmitir (solo si tx = true).
 *  - KISS SetHardware (orden 0x06) con texto "BH:…":
 *      Pi -> RAK  BH:PING · BH:GET · BH:CONF? · BH:CFG {json} · BH:BEACON · BH:REBOOT · BH:DFU · BH:UF2
 *      RAK -> Pi  BH:PONG · BH:STATUS {json} · BH:CONF {json} · BH:CFGOK crc · BH:CFGERR motivo
 *                 BH:RX {rssi,snr,fe} (justo antes de cada paquete recibido) · BH:LOG texto
 */
#include <Arduino.h>
#include <Adafruit_TinyUSB.h>
#include <ArduinoJson.h>
#include "board_pinout.h"
#include "configuration.h"
#include "kiss_protocol.h"
#include "kiss_utils.h"
#include "lora_utils.h"
#include "digi_utils.h"
#include "aprs_utils.h"
#include "sensor_utils.h"

static bool     radioOk = false;
static uint32_t rxCount = 0, rxInterval = 0, txCount = 0, digiCount = 0, digiInterval = 0, kissIn = 0;
static int      lastRssi = 0;
static float    lastSnr = 0;
static uint32_t tBeacon = 0, tTelem = 0, tStatus = 0, tSensor = 0, tLastTx = 0, tLedOff = 0;
static uint16_t telemCycles = 0;
// cola de transmisión (anillo fijo: sin vector ni excepciones de libstdc++)
#define TXQ 10
static String txQueue[TXQ];
static uint8_t txHead = 0, txCountQ = 0;
static bool txPush(const String& p) {
    if (txCountQ >= TXQ) return false;
    txQueue[(txHead + txCountQ) % TXQ] = p;
    txCountQ++;
    return true;
}
static String txPop() {
    String p = txQueue[txHead];
    txQueue[txHead] = "";
    txHead = (txHead + 1) % TXQ;
    txCountQ--;
    return p;
}

// ------------------------------------------------------------------ USB / KISS
static void sendRaw(const String& s) {
    if (!Serial) return;                      // nadie escucha: no bloquear
    Serial.write((const uint8_t*)s.c_str(), s.length());
}
static void hw(const String& text) { sendRaw(encapsulateKISS(text, CMD_HARDWARE)); }
static void logHost(const String& text) { hw("BH:LOG " + text); }
static void toHost(const String& tnc2) { sendRaw(encodeKISS(tnc2)); }

static String statusJson() {
    JsonDocument d;
    SensorData& s = Sensor_Utils::data();
    GpsData& g = Sensor_Utils::gps();
    d["fw"] = FW_VERSION;            d["call"] = Config.callsign;   d["up"] = millis() / 1000;
    d["radio"] = radioOk ? "ok" : "error " + String(LoRa_Utils::lastState());
    d["freq"] = Config.freq;         d["tx"] = Config.txActive;     d["digi"] = Config.digiMode;
    d["rx"] = rxCount;               d["txn"] = txCount;            d["digin"] = digiCount;
    d["crcerr"] = LoRa_Utils::crcErrors;  d["kissin"] = kissIn;
    d["rssi"] = lastRssi;            d["snr"] = lastSnr;
    if (s.tempOk) d["t"] = serialized(String(s.temp, 1));
    if (medidaValida(s.hum, 0, 100)) d["h"] = serialized(String(s.hum, 0));
    if (medidaValida(s.pres, 300, 1200)) d["p"] = serialized(String(s.pres, 1));
    d["sensor"] = s.source;
    if (medidaValida(s.vbat, 0.5f, 10)) d["vbat"] = serialized(String(s.vbat, 2));
    JsonObject jg = d["gps"].to<JsonObject>();
    jg["present"] = g.present;       jg["fix"] = g.fix;             jg["sats"] = g.sats;
    if (g.fix) {
        jg["lat"] = serialized(String(g.lat, 6)); jg["lon"] = serialized(String(g.lon, 6));
        jg["alt"] = serialized(String(g.alt, 0)); jg["hdop"] = serialized(String(g.hdop, 1));
    }
    if (g.utc.length()) jg["utc"] = g.utc;
    d["crc"] = Config.checksum();
    String out;
    serializeJson(d, out);
    return out;
}

static void handleHardware(const String& t) {
    if (!t.startsWith("BH:")) return;
    if (t == "BH:PING")        { hw(String("BH:PONG ") + FW_NAME + " " + FW_VERSION); return; }
    if (t == "BH:GET")         { hw("BH:STATUS " + statusJson()); return; }
    if (t == "BH:CONF?")       { hw("BH:CONF " + Config.toJson()); return; }
    if (t == "BH:BEACON")      { tBeacon = 0; return; }
    if (t == "BH:REBOOT")      { delay(100); NVIC_SystemReset(); }
    if (t == "BH:DFU")         { delay(100); enterSerialDfu(); }
    if (t == "BH:UF2")         { delay(100); enterUf2Dfu(); }
    if (t.startsWith("BH:CFG ")) {
        uint32_t before = Config.checksum();
        String err;
        if (!Config.fromJson(t.substring(7), err)) { hw("BH:CFGERR " + err); return; }
        if (Config.checksum() != before) {
            Config.save();
            if (radioOk) radioOk = LoRa_Utils::applyConfig();
            Sensor_Utils::read();
        }
        hw("BH:CFGOK " + String(Config.checksum()));
        return;
    }
    hw("BH:CFGERR orden desconocida");
}

static void handleKissFrame(const String& frame) {
    if (frame.length() < 3) return;
    uint8_t cmd = (uint8_t)frame.charAt(1) & 0x0F;
    if (cmd == CMD_HARDWARE) {
        handleHardware(decapsulateKISS(frame));
        return;
    }
    if (cmd != CMD_DATA) return;              // TXDELAY, P, SLOTTIME…: no aplican a LoRa
    bool dataFrame = false;
    String tnc2 = decodeKISS(frame, dataFrame);
    if (!dataFrame || tnc2.indexOf(':') < 0) return;
    kissIn++;
    if (!Config.txActive) { logHost("TX desactivada: no transmito " + tnc2.substring(0, tnc2.indexOf(':'))); return; }
    txPush(tnc2);
}

static void readHost() {
    static String buf;
    static bool inFrame = false;
    while (Serial.available()) {
        uint8_t c = Serial.read();
        if (c == FEND) {
            if (inFrame && buf.length() > 0) handleKissFrame(String((char)FEND) + buf + String((char)FEND));
            buf = "";
            inFrame = true;
        } else if (inFrame) {
            if (buf.length() < 600) buf += (char)c; else { buf = ""; inFrame = false; }
        }
    }
}

// ------------------------------------------------------------------ paquetes propios
static void ownPacket(bool rf, const String& viaKiss, const String& viaRF) {
    if (Config.kissOwnPackets) toHost(viaKiss);
    if (rf && Config.txActive) txPush(viaRF);
}

static void beacons() {
    uint32_t now = millis();
    if (Config.beaconMin > 0) {
        bool due = (tBeacon == 0) ? now > 20000 : now - tBeacon >= (uint32_t)Config.beaconMin * 60000UL;   // 1.ª a los 20 s
        if (due) {
            tBeacon = now;
            ownPacket(Config.beaconRF, APRS_Utils::beacon(false), APRS_Utils::beacon(true));
            if (Config.status.length()) ownPacket(Config.beaconRF, APRS_Utils::status(false), APRS_Utils::status(true));
        }
    }
    if (Config.telemetryMin > 0 && now > 60000 && (tTelem == 0 || now - tTelem >= (uint32_t)Config.telemetryMin * 60000UL)) {
        tTelem = now;
        if (telemCycles % 12 == 0) {                                  // definiciones al arrancar y cada 12 envíos
            for (int i = 0; i < 4; i++) ownPacket(Config.telemetryRF, APRS_Utils::telemetryDefinition(false, i),
                                                  APRS_Utils::telemetryDefinition(true, i));
        }
        telemCycles++;
        ownPacket(Config.telemetryRF, APRS_Utils::telemetry(false, rxInterval, digiInterval),
                  APRS_Utils::telemetry(true, rxInterval, digiInterval));
        rxInterval = digiInterval = 0;
    }
}

// ------------------------------------------------------------------ watchdog
static void watchdogStart() {
    NRF_WDT->CONFIG = (WDT_CONFIG_SLEEP_Run << WDT_CONFIG_SLEEP_Pos) | (WDT_CONFIG_HALT_Pause << WDT_CONFIG_HALT_Pos);
    NRF_WDT->CRV = 30 * 32768;                // 30 s
    NRF_WDT->RREN = WDT_RREN_RR0_Msk;
    NRF_WDT->TASKS_START = 1;
}
static void watchdogFeed() { NRF_WDT->RR[0] = WDT_RR_RR_Reload; }

// ------------------------------------------------------------------ Arduino
void setup() {
    pinMode(INTERNAL_LED_PIN, OUTPUT);
    pinMode(TX_LED_PIN, OUTPUT);
    digitalWrite(INTERNAL_LED_PIN, HIGH);
    digitalWrite(TX_LED_PIN, HIGH);
    Serial.begin(115200);
    Config.begin();                           // sin fichero: valores por defecto (la Pi manda los suyos)
    Sensor_Utils::setup();
    randomSeed(NRF_FICR->DEVICEADDR[0] ^ micros());
    radioOk = LoRa_Utils::setup();
    delay(300);
    digitalWrite(INTERNAL_LED_PIN, LOW);
    digitalWrite(TX_LED_PIN, LOW);
    watchdogStart();
    tStatus = millis();
}

void loop() {
    watchdogFeed();
    uint32_t now = millis();
    readHost();
    Sensor_Utils::gpsLoop();

    if (radioOk) {
        LoRaRx rx;
        if (LoRa_Utils::receivePacket(rx)) {
            rxCount++; rxInterval++;
            lastRssi = rx.rssi; lastSnr = rx.snr;
            digitalWrite(INTERNAL_LED_PIN, HIGH);
            tLedOff = now + 150;
            hw("BH:RX {\"rssi\":" + String(rx.rssi) + ",\"snr\":" + String(rx.snr, 1) + ",\"fe\":" + String(rx.freqError) + "}");
            toHost(rx.packet);
            if (Config.txActive && Config.digiMode > 0 && !DIGI_Utils::isDuplicate(rx.packet)) {
                String d = DIGI_Utils::generateDigipeatedPacket(rx.packet);
                if (d.length() && txPush(d)) { digiCount++; digiInterval++; }
            }
        }
    }
    if (tLedOff && (int32_t)(now - tLedOff) >= 0) { digitalWrite(INTERNAL_LED_PIN, LOW); tLedOff = 0; }

    if (txCountQ > 0 && radioOk && now - tLastTx > 3000) {
        String p = txPop();
        if (LoRa_Utils::sendNewPacket(p)) txCount++;
        else logHost("no transmitido (canal ocupado o error " + String(LoRa_Utils::lastState()) + ")");
        tLastTx = millis();
    }

    if (now - tSensor >= 30000) { tSensor = now; Sensor_Utils::read(); }
    beacons();
    if (Config.statusSec > 0 && now - tStatus >= (uint32_t)Config.statusSec * 1000UL) {
        tStatus = now;
        hw("BH:STATUS " + statusJson());
    }
    static uint32_t tRetry = 0;
    if (!radioOk && now - tRetry > 60000) { tRetry = now; radioOk = LoRa_Utils::setup(); }   // reintento cada minuto
    delay(2);
}
