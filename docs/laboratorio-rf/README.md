# BricoHams SDR · Paquete de laboratorio RF rellenable

**Edición 2026-10-17 · Plantillas vacías: ningún componente está cualificado aún.**

- [Procedimientos y cualificación](../manuales/44_LABORATORIO_RF.md).
- [Manual NanoVNA ilustrado y calibración paso a paso](../manuales/45_NANOVNA.md).

## Uso en Excel, LibreOffice o editor CSV

1. Copiar esta carpeta a un expediente local de campaña; mantener intactas las plantillas.
2. Importar los CSV como **UTF-8, separador punto y coma `;`**, sin separador de miles.
   Usar punto decimal en datos numéricos y fecha ISO `AAAA-MM-DD`; hora con zona
   `AAAA-MM-DDThh:mm:ss+hh:mm`. Si Excel no separa columnas, usar Datos → Desde texto/CSV.
3. Mantener IDs, series y nombres de archivo como **texto**, evitando conversión a
   fechas o notación científica. No abrir archivos de origen desconocido con macros.
4. La primera fila es cabecera; la segunda es una fila vacía para rellenar.
   Duplicar filas para cada unidad/punto/repetición, no poner listas en una celda.
5. Completar IDs antes de medir. No usar cero para «no medido»; dejar vacío y
   explicar motivo. Decisión inicial: `NO_ENSAYADO`.
6. Guardar una copia de trabajo en el formato de la hoja de cálculo si se desea;
   exportar también CSV con la misma codificación/separador. **No hay fórmulas,
   cálculos ni validación automática** en las plantillas.
7. No introducir datos inventados ni rellenar incertidumbre con la resolución
   de pantalla. Adjuntar evidencias y revisión antes de decidir.
8. Para publicar, crear copia anonimizada: retirar series personales, ubicaciones,
   nombres y fotografías privadas. Las plantillas no llevan datos de la estación.

## Hojas

| Hoja | Una fila por… | Claves y uso |
|---|---|---|
| [01_componentes.csv](01_componentes.csv) | componente o revisión física | `componente_id`; padre/cadena opcional para trazabilidad |
| [02_instrumentos.csv](02_instrumentos.csv) | instrumento, referencia o accesorio | `instrumento_id`; incluir patrones, cargas, cables y protecciones |
| [03_requisitos.csv](03_requisitos.csv) | requisito verificable | `requisito_id`, componente, magnitud, banda, límite y fuente |
| [04_calibraciones.csv](04_calibraciones.csv) | sesión de corrección/verificación | `calibracion_id`, instrumento, plano, configuración y referencias |
| [05_medidas_rf.csv](05_medidas_rf.csv) | frecuencia, magnitud y repetición | `ensayo_id`, componente, requisito, calibración y evidencia |
| [06_medidas_sdr_aux.csv](06_medidas_sdr_aux.csv) | punto SDR o auxiliar DC/sensor | Configuración y magnitud explícitas; no mezclar métricas en una fila |
| [07_incertidumbre.csv](07_incertidumbre.csv) | contribución de incertidumbre | Misma magnitud/unidad; estándar/expandida diferenciadas |
| [08_decisiones.csv](08_decisiones.csv) | decisión por ensayo/requisito | Resultado, U, k, banda de guarda, revisor y limitaciones |

### Convenciones de las columnas

- `ensayo_id` puede repetirse en las medidas de un mismo ensayo; usar
  `punto_id` distinto para cada frecuencia/repetición y referenciarlo en incertidumbre.
- `calibracion_id`: corrección/verificación principal; `configuracion_archivo`
  y `montaje_archivo` relacionan todos los instrumentos/accesorios usados.
- `modelo_correccion`: OSL, OSL+THRU, corrección PC o procedimiento del instrumento;
  no escribir «SOLT completo» para un NanoVNA de una sola dirección.
- `magnitud`: por ejemplo `S11_LOG`, `ROE`, `IL`, `RECHAZO`, `GANANCIA`,
  `FRECUENCIA`, `SINAD`, `PER`, `TENSION`, `CORRIENTE`, `TEMPERATURA`.
  Especificar la unidad en su columna; no asumir dB/dBm intercambiables.
- `sentido`: normal/invertido; `puerto_tercero_carga_id` obligatorio si aplica a diplexor.
- `tipo_limite`: `MAX`, `MIN` o `INTERVALO`; rellenar solo los límites aplicables.
- `lectura_verificacion_antes/despues`: se refieren a la magnitud/unidad y
  frecuencia de verificación de esa fila. Si hacen falta más puntos, abrir
  otra fila de verificación con ID propio y documentar relación en observaciones.
- `u_estandar`: incertidumbre estándar, no tolerancia; registrar distribución,
  divisor y fuente. `U_expandida` y `k` solo con justificación.
- `resultado_tipo`: `VALOR`, `COTA_INFERIOR` o `COTA_SUPERIOR` si la medida
  está limitada por el suelo o el rango. No transformar una cota en valor exacto.
- `estado/decision`: `APTO`, `NO_APTO`, `INDETERMINADO`, `NO_ENSAYADO`.
- `evidencia_archivo`: Touchstone, datos originales o informe; `captura_archivo`
  como complemento. En `.s2p`, indicar si S12/S22 no se midieron.

## Itinerario mínimo

1. Inventario de componentes e instrumentos.
2. Requisitos y límites de seguridad del modelo real.
3. Calibración/corrección y verificación independiente.
4. Medidas y repeticiones; chequeo final.
5. Incertidumbre, decisión y revisión.

Los ejemplos numéricos de los manuales son didácticos y **no se importan como
resultados**. No hay capturas reales del banco del usuario ni medidas simuladas
presentadas como realizadas.

## Imágenes y capturas

Tres diagramas SVG BricoHams son locales y funcionan sin conexión.
Las capturas reales de referencia de NanoVNA/NanoVNA-Saver están **enlazadas a sus
fuentes externas** en el manual 45 y requieren Internet; no son capturas de tu equipo.
El manual incluye una lista de capturas reales que producir durante los ensayos.
Conservar originales sin editar y añadir branding solo en un pie que no oculte datos.
