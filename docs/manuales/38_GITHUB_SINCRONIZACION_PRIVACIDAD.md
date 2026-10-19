# 38 · GitHub: sincronización y repositorio sin datos personales

## Publicaciones coordinadas desde v5.4.0 · 2026-10-17

[VERSION](../../VERSION) define la versión vigente. Público y privado comparten
versión, fecha y etiqueta Git `v5.4.0`; cada `main` conserva su propio historial.
Nunca se fusiona el historial privado en el público ni se usa force-push para alinearlos.
El público recibe archivos del kit anonimizado, preservando sus recursos exclusivos.
Antes de publicar: pruebas, `tests/test_anonimato.py` y `tools/datos_personales.py`.
La nueva entrega debe incrementar VERSION y el historial y crear la misma etiqueta
en los dos repositorios. Los commits tendrán hashes diferentes.

Las secciones siguientes documentan la incidencia histórica de v5.1; no son
instrucciones para sustituir el procedimiento coordinado de publicación actual.

Este manual explica:

- por qué la carpeta del kit en Windows dejó de sincronizarse con GitHub y cómo arreglarlo;
- cómo comprobar, antes de cada `push`, que no sale nada personal ni ninguna clave;
- qué hacer con lo que ya se publicó en versiones anteriores.

Herramientas: `tools/git_sanear.sh` (diagnóstico y reparación) y `tools/datos_personales.py` (comprobación de privacidad). Pruebas: `tests/test_git_sanear.py`. Decisiones: ADR-65.

## 1. Qué pasaba (diagnóstico del 12/10/2026)

La carpeta `Documentos\GitHub\bricohams-sdr` del PC tenía cuatro problemas a la vez:

| Síntoma | Causa | Arreglo |
|---|---|---|
| `warning: ignoring ref with broken name refs/remotes/origin/HEAD (# Name clash 2026-10-11 … #)` | Un cliente de sincronización en la nube copia también la carpeta `.git`. Al chocar dos versiones de un fichero crea copias «`(# Name clash … #)`» y «`(# Edit conflict … #)`». Ese formato de nombre es el de **Proton Drive**. | Apartar esas copias (`git_sanear.sh --reparar`) y **sacar el repositorio de la carpeta sincronizada** (§3). |
| `git status` → `main...origin/main [gone]` | Faltaba `refs/remotes/origin/main` en local. El cliente de la nube borró o renombró la referencia. | `git fetch --prune origin` la vuelve a crear. |
| GitHub va 1 commit por delante: «Delete .gitignore» | Alguien borró `.gitignore` desde la web de GitHub. Si se trae tal cual, **`bricohams.env` (con las claves) quedaría sin proteger** y un `git add .` lo subiría. | La v5.1 vuelve a poner `.gitignore`, ampliado. Al traer el commit de la web, el de la v5.1 lo recupera. |
| `firmware-compilado/` sin seguimiento, 322 MB | Binarios compilados en lote (iGate y Meshtastic de muchas placas). Un commit así hace los `push` lentísimos y casi choca con el límite de GitHub. | Van en `.gitignore`, salvo `build_all.py`. Los binarios se publican como **Release** de GitHub, no en el git: los compila el workflow `.github/workflows/firmware.yml` en GitHub (a mano o con una etiqueta `fw-*`), así no llevan rutas ni nombres de usuario del PC. |

El `push` requiere una sesión autenticada de GitHub. Usa Git Credential Manager
o una clave SSH autorizada; nunca guardes tokens en los comandos ni en el repositorio.

## 2. Diagnóstico y reparación automática

Desde **Git Bash** en Windows, o en Linux, dentro de la carpeta del kit:

```bash
bash tools/git_sanear.sh             # solo mira y explica
bash tools/git_sanear.sh --reparar   # aparta copias de conflicto, refs rotas y .lock viejos; git fetch --prune
```

`--reparar` **no borra nada**. Lo que aparta queda en `.git/_conflictos_<fecha>/`; cuando todo vaya bien puedes borrar esa carpeta. Nunca hace `push` ni toca credenciales.

Comprueba:

1. copias de conflicto de la nube dentro de `.git`;
2. referencias vacías o con ceros y ficheros `.lock` de más de 10 minutos;
3. que la rama existe en GitHub y cuánto vas por delante o por detrás, y si el remoto borra `.gitignore`;
4. que `bricohams.env` no está en el índice y sí en `.gitignore`;
5. ficheros de más de 50 MB en el índice (GitHub corta en 100 MB);
6. si la carpeta está en OneDrive, Proton Drive, Dropbox, Google Drive, iCloud, Nextcloud, pCloud o MEGA.

## 3. Sacar el repositorio de la carpeta sincronizada (una vez)

git y los clientes de sincronización en la nube no se llevan bien: los dos escriben en `.git` a la vez. GitHub ya es la copia de seguridad del código. Dos opciones:

- **Recomendada:** mover el repositorio fuera de la carpeta sincronizada, p. ej. a `C:\git\bricohams-sdr`:
  1. Cierra VS Code y GitHub Desktop.
  2. Mueve la carpeta entera, con `.git`.
  3. En GitHub Desktop: *File → Add local repository* con la ruta nueva. En VS Code: *Abrir carpeta*.
  4. `bricohams.env` va dentro y sigue ignorado.
- **Alternativa:** excluir la carpeta `bricohams-sdr` (o al menos `.git`) de la sincronización, desde los ajustes de carpetas del cliente de la nube.

Copia aparte `bricohams.env` a un sitio seguro: un gestor de contraseñas o una carpeta cifrada. Es lo único que no está en GitHub.

## 4. Subir la v5.1 a GitHub (paso a paso)

El commit de la v5.1 ya está hecho en tu carpeta (`git log -1` → «v5.1 …»). Desde Git Bash, PowerShell o el terminal de VS Code:

```bash
git status -sb                      # main...origin/main [ahead N, behind 1]
bash tools/git_sanear.sh --reparar  # si aún salen avisos
git pull --rebase origin main       # trae «Delete .gitignore» de la web y pone la v5.1 encima
git ls-files .gitignore             # debe salir .gitignore
git check-ignore -v bricohams.env   # debe decir .gitignore:… bricohams.env
python tools/datos_personales.py    # ✔ limpio (usa tu bricohams.env para saber qué buscar)
git push origin main
```

Con GitHub Desktop: *Fetch origin* → *Pull origin* → *Push origin*. Si pide resolver un conflicto en `.gitignore`, quédate con el contenido de la v5.1, el que tiene más líneas.

**No borres ficheros desde la web de GitHub.** Hazlo en local y súbelo. Así `.gitignore` y el historial quedan coherentes.

## 5. Antes de cada push: nada personal ni claves

```bash
python3 tools/datos_personales.py              # árbol de trabajo
python3 tools/datos_personales.py --historial  # todo el historial, con los .zip de dentro
python3 tools/datos_personales.py --zip bricohams-sdr-v5.1.zip
```

Qué busca, **sin imprimir nunca el valor**:

- Las **huellas SHA-256** de `tools/datos_personales_huellas.txt`: la red de casa, el usuario del sistema de la Pi, las coordenadas exactas y la IP de un tercero.
  - Se guardan como huella para que la propia lista no publique lo que esconde.
  - Para añadir una: `python3 tools/datos_personales.py --huella 'dato'`.
- Con tu `bricohams.env` presente:
  - sus claves (`*PASS*`, `*KEY*`, `*TOKEN*`, `*PSK*`, `*PASSCODE*`, `*SSID*`);
  - las URL de canal de Meshtastic y sus PSK en base64 y hex;
  - `STATION_LAT/LON` con 4 decimales;
  - las palabras de `DATOS_PERSONALES="…"`.

`tests/run_tests.sh` lo pasa siempre sobre el árbol.

En el repositorio público **sí** pueden ir:

- el indicativo y el dominio de la estación, que son públicos;
- la localidad y el locator de 6 caracteres;
- las coordenadas con 2 decimales (unos 1 km).

**No** pueden ir:

- la IP de la red de casa: los ejemplos usan `192.168.1.50`;
- el usuario del sistema: se escribe `<usuario>`;
- la posición exacta;
- los SSID ni ninguna clave;
- la IP de visitantes.

## 6. Lo que ya se publicó (historial)

`tools/datos_personales.py --historial` sobre GitHub (12/10/2026):

- **No hay** contraseñas, passcodes, tokens ni PSK de Meshtastic en ningún commit ni en ningún `.zip` publicado.
- **Sí hay**, en commits viejos y en los archivos `.zip` de versiones 4.0–4.3:
  - los SSID de las WiFi;
  - la red de casa;
  - el usuario del sistema de la Pi;
  - las coordenadas exactas;
  - en un documento, la IP de un visitante.

La v5.1 lo quita del árbol actual, pero el historial sigue público. Hay dos caminos y los dos son decisión tuya:

1. **Dejarlo.** Son datos de poco riesgo, salvo la posición exacta junto a los nombres de las WiFi. Si eliges esto, cambia el nombre de las redes WiFi.
2. **Reescribir el historial.** Con [git-filter-repo](https://github.com/newren/git-filter-repo), en una copia nueva:
   ```bash
   git clone --mirror https://github.com/<cuenta>/bricohams-sdr.git limpio.git
   cd limpio.git
   git filter-repo --path "<directorio-historico>" --invert-paths --replace-text ../reemplazos.txt
   git push --force --mirror
   ```
   - Sustituye `<directorio-historico>` por la ruta exacta del directorio que contiene los archivos antiguos, comprobada en el historial. No ejecutes el ejemplo con el marcador literal.
   - `reemplazos.txt` tiene una línea por dato, `dato==>texto`. Escríbelo tú y no lo subas.
   - **Cambia todos los hashes**: cualquier otra copia (la Pi, otros PCs) tiene que volver a clonar.
   - GitHub puede tardar en olvidar las vistas en caché; para eso está su formulario de soporte.

## 7. «Despersonalizar» el remoto

El remoto `origin` apunta a `https://github.com/<cuenta>/bricohams-sdr.git`, sin usuario ni token en la URL. `git_sanear.sh` avisa si alguna vez lleva credenciales. Los commits van firmados con el nombre y el correo de BricoHams, sin el correo personal.

Para que los commits nuevos no lleven el correo de tu cuenta, usa el anónimo de GitHub (*Settings → Emails → Keep my email address private*) solo en este repositorio:

```bash
git config user.email "<id>+<cuenta>@users.noreply.github.com"
```
