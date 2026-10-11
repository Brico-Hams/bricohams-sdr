/* BricoHams RAK4631 LoRa APRS · EA5KAO / BricoHams · GPL-3.0-or-later (ver LICENSE). */
#include "configuration.h"
#include "sensor_utils.h"
#include "aprs_utils.h"

namespace APRS_Utils {

    static uint16_t telemetrySeq = 0;

    static String degMin(double v, int degDigits, char pos, char neg) {
        char h = v >= 0 ? pos : neg;
        v = fabs(v);
        int d = (int)v;
        double m = (v - d) * 60.0;
        if (m >= 59.995) { d++; m = 0; }
        char b[16];
        if (degDigits == 2) snprintf(b, sizeof b, "%02d%05.2f%c", d, m, h);
        else                snprintf(b, sizeof b, "%03d%05.2f%c", d, m, h);
        // ambigüedad APRS: espacios desde las centésimas de minuto hacia la izquierda (sin tocar el punto)
        int len = strlen(b), quitar = constrain(Config.ambiguity, 0, 4);
        for (int i = len - 2, q = 0; i >= 0 && q < quitar; i--) {
            if (b[i] == '.') continue;
            b[i] = ' ';
            q++;
        }
        return String(b);
    }

    String latitude(double lat)  { return degMin(lat, 2, 'N', 'S'); }
    String longitude(double lon) { return degMin(lon, 3, 'E', 'W'); }

    String header(bool viaRF) {
        String h = Config.callsign + ">" + APRS_TOCALL;
        if (viaRF && Config.path.length()) h += "," + Config.path;
        return h;
    }

    String beacon(bool viaRF) {
        GpsData& g = Sensor_Utils::gps();
        bool useGps = Config.gpsBeacon && g.fix;
        double lat = useGps ? g.lat : Config.latitude;
        double lon = useGps ? g.lon : Config.longitude;
        int alt = useGps ? (int)g.alt : Config.altitude;
        String p = header(viaRF) + ":!" + latitude(lat) + Config.symbolTable + longitude(lon) + Config.symbolCode;
        if (alt > 0) {
            char a[12];
            snprintf(a, sizeof a, "/A=%06ld", lround(alt * 3.28084));
            p += a;
        }
        p += " " + Config.comment;
        SensorData& s = Sensor_Utils::data();
        if (Config.tempInComment && s.tempOk) p += " Caja " + String(s.temp, 1) + "C";
        return p;
    }

    String status(bool viaRF) {
        return Config.status.length() ? header(viaRF) + ":>" + Config.status : String("");
    }

    static String addressee() {       // "::EA5KAO-10:" (mensaje a uno mismo, destinatario relleno a 9)
        String a = Config.callsign;
        while (a.length() < 9) a += ' ';
        return "::" + a + ":";
    }

    String telemetry(bool viaRF, uint32_t rxCount, uint32_t digiCount) {
        SensorData& s = Sensor_Utils::data();
        GpsData& g = Sensor_Utils::gps();
        auto clamp8 = [](long v) { return v < 0 ? 0L : (v > 255 ? 255L : v); };
        long a1 = s.tempOk ? clamp8(lround((s.temp + 40.0f) * 2.0f)) : 0;      // EQNS 0,0.5,-40
        long a2 = medidaValida(s.hum, 0, 100) ? clamp8(lround(s.hum)) : 0;           // EQNS 0,1,0
        long a3 = medidaValida(s.vbat, 0.5f, 10) ? clamp8(lround(s.vbat * 50.0f)) : 0; // EQNS 0,0.02,0
        long a4 = clamp8(rxCount);
        long a5 = clamp8(digiCount);
        char b[64];
        telemetrySeq = (telemetrySeq + 1) % 1000;
        snprintf(b, sizeof b, ":T#%03u,%ld,%ld,%ld,%ld,%ld,%d%d%d00000", telemetrySeq, a1, a2, a3, a4, a5,
                 g.fix ? 1 : 0, Config.txActive ? 1 : 0, Config.digiMode > 0 ? 1 : 0);
        return header(viaRF) + b;
    }

    String telemetryDefinition(bool viaRF, int which) {
        String p = header(viaRF) + addressee();
        switch (which) {
            case 0: p += "PARM.TempCaja,HumCaja,Bateria,RxLoRa,Digi,GPS,TX,Digi"; break;
            case 1: p += "UNIT.degC,%,V,paq,paq,fix,on,on"; break;
            case 2: p += "EQNS.0,0.5,-40,0,1,0,0,0.02,0,0,1,0,0,1,0"; break;
            default: p += "BITS.11100000,SDR BricoHams RAK4631"; break;
        }
        return p;
    }
}
