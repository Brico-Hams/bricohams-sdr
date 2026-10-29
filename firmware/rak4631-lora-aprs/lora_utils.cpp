/* BricoHams RAK4631 LoRa APRS · port de LoRa APRS iGate (CA2RXU) a WisBlock
 * Copyright (C) 2026 Ricardo Guzman - CA2RXU (original) · BricoHams contributors (port nRF52)
 * GPL-3.0-or-later (ver LICENSE).
 *
 * Adaptado de src/lora_utils.cpp del original:
 *  - SX1262 en un SPIClass propio (NRF_SPIM2, pines internos del RAK4630): el SPI por
 *    defecto del BSP de RAK es el de los slots WisBlock.
 *  - Igual que el original: cabecera LoRa APRS "<\xff\x01", CRC, ganancia RX reforzada,
 *    TCXO 1,8 V, DIO2 como conmutador de antena y CAD (DIFS + backoff) antes de transmitir.
 *  - Sin pantalla, syslog, mapa ni web (no hay WiFi): la Pi recibe todo por KISS.
 */
#include <SPI.h>
#include <RadioLib.h>
#include "board_pinout.h"
#include "configuration.h"
#include "lora_utils.h"

static SPIClass loraSPI(NRF_SPIM2, RADIO_MISO_PIN, RADIO_SCLK_PIN, RADIO_MOSI_PIN);
static SX1262 radio = new Module(RADIO_CS_PIN, RADIO_DIO1_PIN, RADIO_RST_PIN, RADIO_BUSY_PIN, loraSPI);

static volatile bool operationDone = true;
static bool transmitFlag = true;
static int  state = RADIOLIB_ERR_NONE;

#define DIFS_SLOTS      2
#define BACKOFF_MAX     4
#define CAD_MAX_WAIT_MS 10000
static unsigned long cadStartTime = 0;

namespace LoRa_Utils {

    uint32_t crcErrors = 0;

    static void setFlag(void) { operationDone = true; }

    int lastState() { return state; }

    bool applyConfig() {
        int s = 0;
        s |= radio.setFrequency((float)Config.freq / 1000000.0f);
        s |= radio.setSpreadingFactor(Config.sf);
        s |= radio.setBandwidth((float)Config.bw / 1000.0f);
        s |= radio.setCodingRate(Config.cr);
        s |= radio.setOutputPower(constrain(Config.power, -9, 22));
        radio.setCRC(true);
        radio.setCurrentLimit(140);
        radio.setRxBoostedGainMode(true);
        state = s;
        transmitFlag = true;            // vuelve a escuchar en el siguiente receivePacket()
        operationDone = true;
        return s == RADIOLIB_ERR_NONE;
    }

    bool setup() {
        pinMode(RADIO_ANT_SW_PIN, OUTPUT);
        digitalWrite(RADIO_ANT_SW_PIN, RADIO_ANT_SW_ON_STATE);
        loraSPI.begin();
        // TCXO de 1,8 V en DIO3 (del RAK4630): hay que darlo en begin(), si no el SX1262 no arranca
        state = radio.begin((float)Config.freq / 1000000.0f, (float)Config.bw / 1000.0f, Config.sf, Config.cr,
                            RADIOLIB_SX126X_SYNC_WORD_PRIVATE, constrain(Config.power, -9, 22), 8, 1.8, false);
        if (state != RADIOLIB_ERR_NONE) return false;
        radio.setDio2AsRfSwitch(true);
        radio.setDio1Action(setFlag);
        return applyConfig();
    }

    static bool doCAD() { return radio.scanChannel() != RADIOLIB_CHANNEL_FREE; }
    static bool cadTimedOut() { return millis() - cadStartTime > CAD_MAX_WAIT_MS; }
    static bool doDIFS() {
        for (uint8_t i = DIFS_SLOTS; i > 0; i--) if (doCAD()) return false;
        return true;
    }
    static void waitForDIFS() { while (!doDIFS()) { if (cadTimedOut()) return; } }
    static void doBEB() {
        int backoff = random(1, BACKOFF_MAX + 1);
        while (backoff > 0) {
            if (cadTimedOut()) return;
            if (doCAD()) waitForDIFS(); else backoff--;
        }
    }

    bool sendNewPacket(const String& newPacket) {
        if (!Config.txActive) return false;
        if (Config.cadActive) {
            cadStartTime = millis();
            waitForDIFS();
            doBEB();
            if (cadTimedOut()) { radio.startReceive(); return false; }   // canal ocupado: se descarta
        }
        digitalWrite(TX_LED_PIN, HIGH);
        String frame = String("\x3c\xff\x01") + newPacket;
        state = radio.transmit((uint8_t*)frame.c_str(), frame.length());
        digitalWrite(TX_LED_PIN, LOW);
        transmitFlag = true;
        operationDone = true;           // el siguiente receivePacket() vuelve a RX
        return state == RADIOLIB_ERR_NONE;
    }

    bool receivePacket(LoRaRx& rx) {
        if (!operationDone) return false;
        operationDone = false;
        if (transmitFlag) {
            radio.startReceive();
            transmitFlag = false;
            return false;
        }
        size_t len = radio.getPacketLength();
        uint8_t buf[256];
        if (len > sizeof(buf)) len = sizeof(buf);
        state = radio.readData(buf, len);
        radio.startReceive();
        if (state == RADIOLIB_ERR_CRC_MISMATCH) { crcErrors++; return false; }
        if (state != RADIOLIB_ERR_NONE || len < 6) return false;
        if (buf[0] != 0x3c || buf[1] != 0xff || buf[2] != 0x01) return false;   // no es LoRa APRS
        String p;
        p.reserve(len);
        for (size_t i = 3; i < len; i++) p += (char)buf[i];
        if (p.indexOf('>') < 1 || p.indexOf(':') < 3) return false;
        rx.packet = p;
        rx.rssi = (int)radio.getRSSI();
        rx.snr = radio.getSNR();
        rx.freqError = (long)radio.getFrequencyError();
        return true;
    }
}
