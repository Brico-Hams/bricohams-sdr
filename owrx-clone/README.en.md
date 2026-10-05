# owrx-clone · move your OpenWebRX+ to another machine

*Español: [README.md](README.md)*

**owrx-clone** saves everything that makes your **OpenWebRX+** station unique into a single file and applies it on another machine with one command. That includes:

- receivers and profiles, bookmarks, users and header images;
- web plugins and `/etc/openwebrx`;
- udev rules, SDR packages and hand-made code tweaks.

Use it to:

- **migrate** from one Raspberry Pi to another, or to a PC;
- keep a **complete backup** that is ready to restore;
- **share** a setup with other hams, with passwords removed (`--publico`).

It is a single Python 3 file that uses only the standard library (plus `openssl` to encrypt).
- **Systems:** Debian 11/12/13, Ubuntu 22.04/24.04 and Raspberry Pi OS.
- **Architectures:** amd64, arm64 and armhf.
- **Licence:** MIT.

The tool speaks Spanish, but every command has an English alias: `export`, `show`, `import`, `undo`, `check`, `help`.

## Install

```bash
cd owrx-clone && sudo ./instalar.sh           # → /usr/local/bin/owrx-clone and man page
```

## Five commands

```bash
sudo owrx-clone export --cifrar                          # old machine → owrx-perfil-HOST-DATE.owrx.tar.gz.enc
owrx-clone show owrx-perfil-*.owrx.tar.gz.enc            # what is inside
sudo owrx-clone import profile.owrx.tar.gz.enc --simular # new machine: dry run
sudo owrx-clone import profile.owrx.tar.gz.enc --todo    # do it (all levels)
sudo owrx-clone check                                    # health check
```

To roll back, run `sudo owrx-clone undo`.

## Levels

| Level | Contents | Imported by default |
|---|---|---|
| `config` | `settings.json`, `users.json`, `bookmarks.json`, header images and the rest of `/var/lib/openwebrx` (caches excluded) | yes |
| `etc` | all of `/etc/openwebrx` | yes |
| `web` | files **added** to htdocs (not shipped by the package): `init.js`, plugins, themes | yes |
| `paquetes` | SDR/decoder packages installed by hand, reinstalled with apt | yes |
| `sistema` | udev rules, rtl/dvb modprobe files, `openwebrx.service.d`, `/etc/codecserver` | `--niveles` / `--todo` |
| `parches` | openwebrx **package** files edited by hand, applied only on the **same** openwebrx version | `--niveles` / `--todo` |
| `extra` | anything added with `export --incluir PATH` | only with `--niveles extra` (not with `--todo`) |

## On import

1. Every file's **SHA-256** is verified, and the paths are checked.
2. If OpenWebRX+ is missing, the matching luarvique repository is added and the profile's packages are installed.
3. Every file that will be overwritten is backed up to `/var/backups/owrx-clone`.
4. The files are copied with their permissions, the service is restarted and `/status.json` is polled.
5. You are warned about any SDR serial number from the profile that is not plugged in.

**Different SDRs on the new machine:** use `--mapear "serial=OLD=>serial=NEW"`.

## OpenWebRX+ in Docker (1.1)

Put `--docker CONTAINER` before the command (or set `OWRX_CLONE_DOCKER=CONTAINER`):

```bash
sudo owrx-clone --docker owrx-mbe export -o from-docker.owrx.tar.gz
sudo owrx-clone --docker owrx-mbe import profile.owrx.tar.gz --simular
```

- **Where it writes:** `docker inspect` finds the host folders mounted on `/var/lib/openwebrx` (config), `/etc/openwebrx` (etc) and `/usr/lib/python3/dist-packages/htdocs/plugins` (web). Without the first two it stops: anything inside the container is lost when it is recreated.
- **What it skips:** no apt packages (OpenWebRX+ and the SDR drivers come with the image, which is recorded in the profile) and no `parches`. `sistema` (udev, modprobe) still applies, as it belongs to the host.
- **Native ⇄ Docker:** a native profile can be imported into a container and the other way round. Web files outside `plugins/` do not fit in Docker and are reported.
- **Service:** the container is stopped and started (`docker stop/start`); `undo` knows it was a container.

## Security

- **Passwords are included by default:** a normal profile holds admin password hashes and API keys. Treat the file like a password, or use `--cifrar` (AES-256 with PBKDF2).
- **Sharing:** `--publico` drops `users.json` and blanks every key whose name contains pass, passcode, key, token or secret.
- **Code runs from the profile:** plugins are JavaScript that runs in your listeners' browsers, and `sistema`/`parches` run as root. Import profiles from trusted people only.
- **Restricted paths:** each level writes only to its own directories, never to `/etc/shadow`, `/etc/sudoers`, `/root`, `/boot`, cron, systemd, PAM, `ld.so` or `~/.ssh` (not even `extra`). A profile may only use this machine's data directory or a new `/var/lib/openwebrx…` / `/srv/openwebrx…` owned by the `openwebrx` user; anything else is rejected. `--todo` includes `sistema` and `parches`, which run code as root: use it only with your own or trusted profiles.
- **No symlinks:** nothing is ever written through a symlink, either on import or on undo. An interrupted import records what it wrote and restarts OpenWebRX+, so `undo` can clean up.

More: `owrx-clone help {niveles,seguridad,dispositivos,migrar,docker,problemas}` and `man owrx-clone`.

*EA5KAO · BricoHams · 2026*
