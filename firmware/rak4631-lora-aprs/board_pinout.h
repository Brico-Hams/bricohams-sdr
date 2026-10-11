/* BricoHams RAK4631 LoRa APRS · port de LoRa APRS iGate (CA2RXU) a WisBlock
 * Copyright (C) 2026 Ricardo Guzman - CA2RXU (original) · EA5KAO / BricoHams (port nRF52)
 * GPL-3.0-or-later (ver LICENSE).
 *
 * Pines del núcleo RAK4631 (nRF52840 + SX1262 con TCXO) en una base WisBlock
 * (RAK19007 / RAK19003 / RAK5005-O). Mismo formato que variants/<placa>/board_pinout.h
 * del firmware original. Numeración Arduino del BSP de RAK: P1.xx = 32 + xx.
 */
#ifndef BOARD_PINOUT_H_
#define BOARD_PINOUT_H_

    //  LoRa: SX1262 interno del RAK4630/RAK4631 (bus SPI propio, no el de los slots)
    #define HAS_SX1262
    #define HAS_TCXO                    // TCXO a 1,8 V por DIO3 y conmutador de antena por DIO2
    #define RADIO_SCLK_PIN      43      // P1.11
    #define RADIO_MISO_PIN      45      // P1.13
    #define RADIO_MOSI_PIN      44      // P1.12
    #define RADIO_CS_PIN        42      // P1.10
    #define RADIO_RST_PIN       38      // P1.06
    #define RADIO_DIO1_PIN      47      // P1.15
    #define RADIO_BUSY_PIN      46      // P1.14
    #define RADIO_ANT_SW_PIN    37      // P1.05: alimenta el conmutador de antena (como RAK3312 en el original)
    #define RADIO_ANT_SW_ON_STATE HIGH

    //  Alimentación de la base: WB_IO2 enciende 3V3_S (sensores y GPS de los slots)
    #define VEXT_CTRL_PIN       34      // P1.02 = WB_IO2
    #define VEXT_CTRL_ON_STATE  HIGH

    //  GPS en el slot A: RAK1910 (Quectel L76B) o RAK12500 (u-blox ZOE-M8Q), NMEA por UART1
    #define HAS_GPS
    #define GPS_BAUDRATE        9600
    #define GPS_RX              15      // P0.15 (Serial1 RX)
    #define GPS_TX              16      // P0.16 (Serial1 TX)

    //  I2C de los slots (Wire): RAK1901 SHTC3 0x70 · RAK1906 BME680 0x76 · BME280 0x76/0x77
    #define SENSOR_SDA          13
    #define SENSOR_SCL          14

    //  LED y batería
    #define INTERNAL_LED_PIN    35      // verde (P1.03): recepción
    #define TX_LED_PIN          36      // azul  (P1.04): transmisión / PC conectado
    #define BATTERY_PIN         5       // P0.05 / AIN3, divisor de la base (x1,73)
    #define BATTERY_DIVIDER     1.73f

#endif
