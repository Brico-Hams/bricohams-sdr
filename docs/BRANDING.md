# Identidad visual BricoHams (resumen operativo)

Resumen del **Manual de color BricoHams v1.1 (03-11-2026)**. El documento oficial es
`BricoHams_Guia_Colores_Web_Pantone_Claro_Oscuro_con_Prompt_IA.pdf` (no se incluye en el repositorio).
Ante cualquier duda manda el PDF.

## Alcance

Se aplica a las interfaces propias del kit: `files/web/*.html`, `files/web/index.html.tmpl`,
`files/htdocs/plugins/receiver/**`, `files/htdocs/plugins/map/**` y las páginas generadas por
`files/bin/bricohams-mesh-admin`, `bricohams-owrx-botones` y `bricohams-google-auth`.
La interfaz base de OpenWebRX+ y los plugins de terceros (`uikit`, `rig_skin`, `doppler`, `notify`…) son
de origen externo y **no** se reestilizan.

## Tokens

| Token | Claro | Oscuro |
|---|---|---|
| `--brand-ink` / `--on-accent` | `#23272B` | `#23272B` |
| `--brand-orange` | `#F26B1D` | `#F26B1D` |
| `--bg` | `#FFFFFF` | `#111518` |
| `--surface` | `#F6F7F8` | `#1C2329` |
| `--text` | `#23272B` | `#F6F8FA` |
| `--text-muted` | `#59636B` | `#BAC4CC` |
| `--border` | `#DCE1E5` | `#38434C` |
| `--link` | `#AA410B` | `#FFA06A` |
| `--focus` | `#F26B1D` | `#FFC18F` |
| `--ok` | `#1B5E20` | `#7BD88F` |
| `--warn` | `#7A4F00` | `#FFC857` |
| `--err` | `#B3261E` | `#FF8A80` |

Los colores de estado (`--ok`, `--warn`, `--err`) son funcionales. Sus valores se eligieron para cumplir
WCAG AA, pero **la razón de contraste está pendiente de medir** con una herramienta antes de darla por buena.

## Reglas

- **Botón primario**: fondo naranja `--brand-orange` con texto grafito `--on-accent`, en ambos temas. Nunca texto blanco sobre naranja.
- **Enlaces**: `#AA410B` en claro y `#FFA06A` en oscuro (`--link`).
- **Foco**: `:focus-visible { outline: 3px solid var(--focus); outline-offset: 3px }`.
- **Tema**: claro / oscuro / sistema. Se guarda en `localStorage` (`bh_theme`), se aplica como `data-theme` en `<html>` y, en las páginas del portal, mediante un script en `<head>` para evitar parpadeo. En OpenWebRX+ lo aplica `marca.js` (`window.BricoHamsTheme`) y el botón `#bricohams-theme` lo alterna.
- **Logotipo**: solo el PNG original (`receiver/marca/bricohams-logo.png`), sin filtros ni inversión. En modo oscuro va sobre una placa blanca discreta.
- **Tipografía**: Inter para la interfaz y Montserrat 700–800 para titulares grandes, con alternativas del sistema. No se cargan fuentes remotas: las páginas deben funcionar sin conexión.
- **Pantone**: solo para impresión; en pantalla se usan los valores hexadecimales de la tabla.
- Los colores no listados en el manual no se usan. Los datos de mapa y los diagramas pueden usar colores funcionales propios.

## Contraste (valores esperados, sin medir)

| Pareja | Uso | Objetivo |
|---|---|---|
| `#23272B` sobre `#F26B1D` | botón primario | AA texto normal |
| `#AA410B` sobre `#FFFFFF` | enlace claro | AA texto normal |
| `#FFA06A` sobre `#111518` | enlace oscuro | AA texto normal |
| `#23272B` sobre `#FFFFFF` | texto claro | AAA |
| `#F6F8FA` sobre `#111518` | texto oscuro | AAA |
| `#59636B` sobre `#FFFFFF` | texto secundario claro | AA |
| `#BAC4CC` sobre `#111518` | texto secundario oscuro | AA |
| `#FFC18F` sobre `#111518` | foco oscuro | ≥ 3:1 |

## Pruebas

`tests/test_branding_colores.py` comprueba que los tokens existen y que la paleta antigua
(`#f7941d`, `#F26B21`, `#a64b00`, `#0b1418`, `#0e1420`, `#111d22`, `#172131`, `#89b9ff`, `#205da8`, `#ff6b00`, `#0a2540`)
no aparece en las interfaces propias.
