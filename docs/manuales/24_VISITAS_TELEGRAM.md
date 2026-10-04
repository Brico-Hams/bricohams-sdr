# 24 · Oyentes, estadísticas y avisos por Telegram

**Qué hace:**
- **Aviso por Telegram:** cada vez que alguien se conecta al SDR, el grupo de operadores recibe:
  > 🟢 **Nuevo oyente** 🇮🇹 Roma, Italia · `151.20.x.x` · 3 conectados
- **En la web:**
  - junto al nombre del receptor sale «👥 3 ahora 🇪🇸🇪🇸🇮🇹 · 1.234 visitas»;
  - al pulsarlo, un resumen por países de los últimos 30 días.

## 1. Cómo funciona (ADR-33)
1. **OpenWebRX+** publica cada conexión y desconexión, con la IP del oyente, en un **MQTT local** (mosquitto, solo 127.0.0.1). Hace falta `mqtt_enabled`, que el instalador activa con `VISITAS_ENABLE="yes"`.
2. **`bricohams-visitas`** recibe esos avisos:
   - calcula país y ciudad con una **base GeoIP local** (DB-IP City Lite, CC BY 4.0, actualizada cada mes). **La IP no se manda a ningún servicio externo.**
   - guarda en `/var/lib/bricohams/visitas.sqlite` solo la **IP truncada** (`83.45.x.x`), el país y la ciudad. **La IP completa no se escribe en disco.**
   - avisa por Telegram como mucho **una vez por IP cada 10 min**, para que no se repita en cada recarga. No avisa de las conexiones desde casa.
   - reenvía el **chat** de la web a Telegram (`VISITAS_CHAT`).
   - deja `visitas.json` para la web, **sin IPs**.
   - borra las visitas a los **90 días** (`VISITAS_DIAS`) y conserva solo los contadores diarios por país.
3. **Cron** (manual 25):
   - resumen diario a las 21:00;
   - actualización de la GeoIP el día 2 de cada mes.

## 2. Crear el bot y el grupo de Telegram
1. En Telegram, habla con **@BotFather** → `/newbot` → nombre (por ejemplo «BricoHams SDR») → copia el **token** (`123456:ABC…`).
2. Crea un **grupo privado** de operadores y añade el bot. Si es un canal, hazlo administrador.
3. Escribe cualquier cosa en el grupo y abre en el navegador `https://api.telegram.org/bot<TOKEN>/getUpdates`. Busca `"chat":{"id":-100…}`: ese número es el **chat id**.
4. Ponlos en `bricohams.env`. Ahí son secretos; no van nunca al git:
   ```
   TELEGRAM_TOKEN="123456:ABC…"
   TELEGRAM_CHAT_ID="-1001234567890"
   ```
5. Aplica y prueba:
   ```bash
   sudo bash install.sh --solo visitas,tareas
   bricohams-telegram "prueba desde la estación"
   ```

## 3. Privacidad (RGPD)
- **Por qué hay que avisar:** registrar IPs, aunque sea truncadas, y la localización es tratar datos personales. Por eso la web tiene un **aviso de privacidad** (`/bricohams/privacidad.html`, enlazado en la descripción del receptor y en el contador) que explica qué se guarda, para qué, cuánto tiempo y cómo ejercer los derechos.
- **Contacto:** el de `ADMIN_EMAIL`. Revisa el texto con tu club. Esto no es asesoramiento legal.
- **Si prefieres no guardar nada personal:** `VISITAS_ENABLE="no"`. El contador y los avisos desaparecen.

## 4. Comandos
```bash
sudo -u openwebrx bricohams-visitas --estado     # lo que ve la web (sin IPs)
sudo -u openwebrx bricohams-visitas --resumen    # manda el resumen del día
sudo -u openwebrx bricohams-visitas --geoip      # descarga la base GeoIP del mes
journalctl -u bricohams-visitas -n 50
```

## 5. Bloquear a alguien
En `https://DOMINIO/clients` (OpenWebRX+, con el usuario admin), el admin ve las IPs completas de los conectados en ese momento y puede **banear**. Esa lista es de OpenWebRX+ y no se guarda en disco.
