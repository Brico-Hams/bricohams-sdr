# owrx-clone · lleva tu OpenWebRX+ a otro equipo

*English: [README.en.md](README.en.md)*

**owrx-clone** guarda en un solo fichero todo lo que hace única a tu estación **OpenWebRX+** (receptores y perfiles, marcadores, usuarios, imágenes, plugins de la web, `/etc/openwebrx`, reglas udev, paquetes de SDR, retoques del código…) y lo aplica en otro equipo con una orden. Así se puede:

- **migrar** de una Raspberry Pi a otra, o a un PC;
- tener una **copia completa** de la estación lista para restaurar;
- **compartir** una configuración con otros radioaficionados (sin contraseñas, con `--publico`).

Un solo fichero Python 3, sin dependencias: solo la biblioteca estándar (y `openssl` para cifrar). Funciona en **Debian 11/12/13, Ubuntu 22.04/24.04 y Raspberry Pi OS**, en amd64, arm64 y armhf. Licencia MIT.

## Instalar

```bash
git clone <este-repositorio> && cd bricohams-sdr/owrx-clone      # o copia la carpeta owrx-clone
sudo ./instalar.sh                                               # /usr/local/bin/owrx-clone + man owrx-clone
```

## En 5 órdenes

```bash
sudo owrx-clone exportar --cifrar                        # 1. en el equipo viejo → owrx-perfil-EQUIPO-FECHA.owrx.tar.gz.enc
owrx-clone ver owrx-perfil-*.owrx.tar.gz.enc             # 2. qué lleva (en cualquier equipo)
sudo owrx-clone importar perfil.owrx.tar.gz.enc --simular   # 3. en el nuevo: qué haría
sudo owrx-clone importar perfil.owrx.tar.gz.enc --todo      # 4. hacerlo
sudo owrx-clone comprobar                                # 5. ¿todo bien?
```

Si algo no te gusta: `sudo owrx-clone deshacer`.

## Qué se copia (niveles)

| Nivel | Qué | Se importa por defecto |
|---|---|---|
| `config` | `settings.json` (receptores, perfiles, ajustes), `users.json`, `bookmarks.json`, imágenes de cabecera y el resto de `/var/lib/openwebrx` (sin cachés) | sí |
| `etc` | `/etc/openwebrx` entero: `openwebrx.conf`, `openwebrx.conf.d`, `bands*.json`, `bookmarks.d`, `markers.d` | sí |
| `web` | lo **añadido** a la web (no viene en el paquete): `plugins/receiver/init.js`, plugins, temas | sí |
| `paquetes` | paquetes de SDR y decodificadores instalados a mano (`soapysdr-module-*`, `rtl-sdr`, `codecserver`, `wsjtx`…); se reinstalan con apt | sí |
| `sistema` | reglas udev, `/etc/modprobe.d` de rtl/dvb/sdr, `openwebrx.service.d`, `/etc/codecserver` | con `--niveles` o `--todo` |
| `parches` | ficheros **del paquete** openwebrx retocados a mano. Solo con la **misma versión** de openwebrx | con `--niveles` o `--todo` |
| `extra` | lo que añadas con `exportar --incluir RUTA` | solo con `--niveles extra` (no entra con `--todo`) |

Las cachés que OpenWebRX+ descarga solo (`eibi.json`, `receivers.json`, `repeaters.json`, `meshtastic.json`), los `*.pyc` y las copias `*.antes-*` no se copian.

## Qué hace al importar

1. Comprueba el perfil: **SHA-256 de cada fichero** y que ninguna entrada se salga de su sitio.
2. Si falta OpenWebRX+, pone el **repositorio de luarvique** que toca a tu sistema (bookworm, trixie, noble, jammy, bullseye) e instala los paquetes del perfil. Los que no existan en tu sistema se avisan y se saltan.
3. Guarda en `/var/backups/owrx-clone/copia-FECHA.tar.gz` **todo lo que va a sobrescribir** y apunta lo que crea.
4. Para OpenWebRX+, copia cada fichero con sus permisos (`users.json` 600, datos del usuario `openwebrx`), recarga udev/systemd si hace falta.
5. Lo arranca y espera a que `/status.json` responda.
6. Avisa de los SDR del perfil que no ve conectados.

`sudo owrx-clone deshacer` devuelve los ficheros a como estaban y borra los nuevos (los paquetes instalados se quedan).

## Otros SDR en el equipo nuevo

OpenWebRX+ elige cada SDR por su número de serie (`"device": "serial=00000101"`). Si en el nuevo equipo son otros:

```bash
SoapySDRUtil --find                                  # series conectadas (o rtl_test -t)
sudo owrx-clone importar perfil.owrx.tar.gz --mapear "serial=00000101=>serial=12345678"
```

O graba en el RTL-SDR nuevo la serie antigua: `rtl_eeprom -d 0 -s 00000101`.

## Seguridad

- Un perfil **normal lleva contraseñas**: el hash de las cuentas de administración y las claves de `settings.json`. Trátalo como una contraseña o usa `--cifrar` (AES-256, openssl, PBKDF2). La contraseña se pide o se toma de `OWRX_CLONE_CLAVE`.
- Para **compartir**: `--publico` quita `users.json` y deja en blanco cualquier clave cuyo nombre tenga `pass`, `passcode`, `key`, `token` o `secret`. `owrx-clone ver` dice cuáles.
- Cada nivel solo puede escribir en sus carpetas. Nunca en `/etc/shadow`, `/etc/sudoers`, `/root`, `/boot`, `/bin`, cron, systemd, PAM, `/etc/profile.d`, `ld.so` ni `~/.ssh`, ni siquiera con `extra`. El directorio de datos del perfil solo se acepta si es el de este equipo o uno nuevo `/var/lib/openwebrx…` o `/srv/openwebrx…` del usuario `openwebrx`; si no, la importación se para. `--todo` incluye `sistema` y `parches`, que ejecutan código como root: úsalo solo con perfiles tuyos o de confianza.
- Nunca escribe a través de un enlace simbólico, ni al importar ni al deshacer. Si se corta a medias, apunta lo que llevaba y vuelve a arrancar OpenWebRX+; `deshacer` lo deja como antes.
- Los plugins (`web`) son JavaScript que corre en el navegador de tus oyentes, y `sistema` y `parches` corren como root: **importa solo perfiles de confianza** y míralos antes con `ver`.

## Formato del perfil

Un `tar.gz` (o ese mismo `tar.gz` cifrado con `openssl enc -aes-256-cbc -pbkdf2 -iter 200000`) con:

```
manifiesto.json          versión del formato, origen (equipo, sistema, arquitectura, versión de OpenWebRX+),
                         niveles, receptores, paquetes, repositorios, avisos y, por cada fichero:
                         nivel, ruta, sha256, tamaño, modo, dueño
LEEME.txt                resumen para humanos
archivos/<nivel>/…       los ficheros. {DATA} = directorio de datos y {HTDOCS} = web de OpenWebRX+,
                         que pueden estar en otro sitio en el destino
```

## Ayuda

```bash
owrx-clone --help
owrx-clone ayuda niveles | seguridad | dispositivos | migrar | problemas
man owrx-clone
```

Las órdenes también existen en inglés: `export`, `show`, `import`, `undo`, `check`, `help`.

## Dentro del kit BricoHams

En el kit BricoHams SDR, `install.sh` lo usa:

- `sudo bash install.sh --exportar [fichero]`: igual que `owrx-clone exportar`.
- `sudo bash install.sh --importar perfil.owrx.tar.gz`: instala la estación BricoHams y al final aplica el perfil. Desde ese momento el instalador **respeta** la configuración importada.
- La copia diaria guarda además un perfil de OpenWebRX+ (los 7 últimos).

Detalle en [docs/manuales/31_CLONAR_OPENWEBRX.md](../docs/manuales/31_CLONAR_OPENWEBRX.md).

*EA5KAO · BricoHams · Mi QTH (Región de Murcia) · 2026*
