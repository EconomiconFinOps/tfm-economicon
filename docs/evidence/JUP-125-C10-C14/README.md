# JUP-125 — Paquete histórico de evidencias C10 y C14

[PR #134](https://github.com/EconomiconFinOps/tfm-economicon/pull/134) ·
[Trello](https://trello.com/c/H0RUnArf) · Entrega documental: 18/10/2026.

Este paquete recupera las evidencias históricas que faltaban en la
[validación de Alejandro](https://github.com/EconomiconFinOps/tfm-economicon/pull/134#pullrequestreview-5560333404).
Se incorpora sin modificar producto, pruebas, modelos, tokenizadores ni datos
persistidos. No acredita aceptación actual de C10/C14 ni levanta la petición de
cambios de Víctor. La corrección C13 de Lucía en `ddd3356c` se conserva.

## Navegación directa

Los 119 archivos del paquete pueden consultarse directamente en GitHub, sin
descargar el ZIP. Son copias fieles de sus miembros, sin corregir ni reescribir
contenidos históricos:

- [README original del paquete](files/README.md): procedencia, instrucciones y límites.
- [Índice original](files/INDEX.json): documentos, etapas y ausencias.
- [MANIFEST original](files/MANIFEST.json): rutas relativas, tamaños y SHA256.
- [C10](files/C10/): originales, normalizados, fixtures y recibos.
- [C14](files/C14/): corpus, etapas, inputs y vectores conservados.
- [Versiones registradas](files/versions/): locks históricos, sin acreditar versiones ejecutadas.

El MANIFEST mantiene sus bytes y resuelve sus rutas desde `files/`. Enumera los
otros 118 archivos de esa carpeta; no incluye este README exterior, el ZIP ni
el SHA256SUMS exterior. El [README dentro de files/](files/README.md) también se
conserva exactamente como estaba en el paquete.

La regla local de `.gitattributes` evita la normalización de finales de línea
sólo dentro de `files/`, para conservar los hashes originales. No desactiva
los diffs de texto ni modifica la configuración global de Git.

## Descarga ZIP e integridad

- [Descargar el ZIP](pr134-C10-C14-evidence-20261018.zip) con el botón de descarga
  del archivo en GitHub. Tamaño: **772.180 bytes**, **119 archivos**.
- [SHA256SUMS](SHA256SUMS):
  `ed9f6b06fe4d166dccbd4d044a7c680f9bfe3119aea90b5ffe174b438afb578f`.
- SHA256 de `MANIFEST.json` dentro del ZIP:
  `aab7d3a4fa74f7a3922e0d93631c2e64abad60042419e4d57e0b920bf1a7d91d`.

El ZIP se conserva byte a byte respecto a la entrega recuperada. El manifiesto
enumera los otros 118 archivos, sus tamaños y hashes; la huella permite comprobar
identidad con esta referencia, no autentica por sí sola al proveedor.

Para comprobar los archivos navegables con Python 3.10 o posterior, sin
dependencias adicionales ni red, desde la raíz del repositorio:

```text
cd docs/evidence/JUP-125-C10-C14/files
python -B verify_package.py
python -B replay_cached_cosine.py
```

El replay matemático es opcional. Como alternativa, descargar el ZIP y
descomprimirlo en una carpeta temporal nueva, fuera del checkout; ejecutar
las mismas órdenes Python desde la raíz extraída, sin el paso `cd` anterior.

El primer comando verifica archivos y correspondencias. El segundo recalcula
coseno sobre los vectores conservados y reproduce los rankings históricos de
evidencia. Sólo leen el paquete y escriben resultados en pantalla: no ejecutan
SQL, backend, OCR, tokenización ni llamadas a modelos. No se deben ejecutar los
procedimientos SQL históricos incluidos como si fueran comandos autocontenidos;
son material de inspección y sus requisitos se explican dentro del paquete.

## Contenido y alcance

| Criterio | Evidencia recuperada | Comprobación reproducible |
| --- | --- | --- |
| C10 | Nueve originales sintéticos, nueve normalizados de extracción real y nueve fixtures históricas, inventarios, métodos y recibos. | 27 hashes y cadena original → normalizado → fixture. No se repite extracción ni OCR. |
| C14 | Corpus de seis documentos y doce preguntas; 46 inputs exactos y 46 vectores reales de 1536 dimensiones de `openai/text-embedding-3-small`. | Relaciones input/caché, reconstrucción de los seis documentos registrados en final/R2 y replay matemático. |

El corpus conserva SHA256
`1db07751e61e841cfb00d6cd5d5b5aac1b5d989b9e2de7fe92840effeddd030b`.
Las etapas inicial, enriquecida, R1, final y R2 se mantienen separadas.
En esta muestra exploratoria, ambos métodos conservan Recall@1/3/5/10 de 12/12
y el número de chunks pasa de 25 a 9; no demuestra una mejora general.
El replay nuevo no reproduce filtros SQL, citas ni latencias del candidato actual.

## Límites conservados

- C10 conserva recibos resumidos del recorrido SQL/citas, no sus filas SQL/chunks
  ni los objetos completos de citas. Los booleanos históricos no son una nueva
  prueba funcional.
- Faltan recibos de las versiones ejecutadas de Tesseract/LibreOffice y el recurso
  físico del tokenizador en la ruta histórica. Los locks no prueban versiones
  instaladas. No se incorpora ningún tokenizador ni entorno generado a Git.
- La copia vacía del corpus de R1 se preserva como anomalía; el corpus canónico
  íntegro se entrega aparte. R1 no tiene SQL propio y R2 reutiliza el SQL final.
- Las cuatro preguntas PDF conservan `citation.page=null` y
  `page_provenance_matches=false` en ambos métodos: no se presentan como páginas
  validadas.
- No se recuperó la respuesta HTTP cruda del proveedor; sí los 46 vectores
  efectivos y los recibos e inventario histórico. No se realizaron nuevas
  inferencias ni gasto para esta recuperación.

El [README original](files/README.md) y el [índice](files/INDEX.json), también
incluidos en el ZIP, detallan alcance, procedencia y ausencias; el
[índice input/vector](files/C14/input-vector-index.json) enlaza cada input literal
con su archivo vectorial.
Se conservan los originales y sus limitaciones sin sustituirlos por resultados
regenerados ni atribuirlos al SHA actual de la PR.

## Siguiente comprobación

Alejandro debe verificar las evidencias C10/C14 y revalidar el delta pertinente
sobre el candidato vigente. Víctor mantiene su revisión técnica y su petición de
cambios de citas, compatibilidad con migración 003 y pruebas sensibles. Esta
entrega documental no resuelve esos cambios ni autoriza el merge.
