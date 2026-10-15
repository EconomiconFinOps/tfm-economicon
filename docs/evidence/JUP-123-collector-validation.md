# Evidencia de extracción del colector — 15/10/2026

JUP: JUP-123 · https://trello.com/c/TqtcumIN

Base: `develop/53b43bb1e79b08967cc1b9efdf66669f11e8197c`.
Rama: `feat/JUP-123-response-collector`. Extracción autorizada por el usuario;
no representa aceptación de B ni validación humana independiente.

## Comprobaciones realizadas

- 31 pruebas de biblioteca estándar pasan, sin omisiones: 9 del colector,
  6 de reconciliación RAG y 16 del adaptador 071. Incluyen servidor HTTP local,
  fallos/redacción, archivo alterado, identidad cruzada, citas ajenas,
  recuperación incompleta, salidas exclusivas y exportación estable.
- Integración con el evaluador 071 real, commit
  `81ceafc67ba400414040b1468d795a41d9d5468d`: plan87muestras,
  521GET contra servidor simulado,0POST/0llamadas al proveedor. Tres raw
  de29casos aceptados por review-sheet, score y compare; fallo técnico introducido
  conservado, reexportación de r1 idéntica byte a byte. Son fixtures de transporte,
  no respuestas de un modelo ni una tasa de robustez. No se crearon juicios.
- Regresión del evaluador existente: 110 pruebas PASS. Gobernanza: 97 pruebas
  Node PASS; trazabilidad e higiene conformes; OpenSpec estricto: 74 elementos PASS.
  Las ejecuciones de Python/Node en sandbox encontraron restricciones de ACL o
  procesos; estos resultados son de las pasadas completas con acceso normal.
- El contrato inspeccionado de develop ofrece estado, contexto, evidencia,
  resultado e historial requeridos. No se ha validado un despliegue de A.
  A ya pertenece a esa base por `cf821570` (#130); no es necesario copiar su rama.

Reproducir el conjunto portable:

```sh
python -m unittest discover -s tools -p 'test_chat_eval_collect*.py' -v
```

La primera ejecución en el sandbox Windows falló por ACL de directorios
temporales. La ejecución con acceso normal encontró una aserción del diagnóstico
de timeout: el colector interno conservaba el error pero el adaptador perdía la
clase al fallar la comprobación de identidad. Se corrigió preservando la clase
de la lectura original, sin texto sensible. La pasada final31/31 es posterior
a esa corrección. No se han borrado ni reconciliado recibos de campañas reales.

## Límites y revisión pendiente

El contrato público puede omitir RAG posterior al contexto inicial; se necesita
el payload real exacto para suplementarlo. Sin él se conserva el bloqueo. La
distancia no disponible no se reemplaza por0. La copia de071 es código local de
confianza y debe permanecer congelada durante la campaña; sus comprobaciones
de fuentes se ejecutan otra vez al exportar. Metadatos locales no atestiguan el
despliegue. La [guía](../validation/chat-collector.md) detalla comandos y salidas.

La entrega no toca apps, prompts, corpus, bancos, ledger, contadores, reservas,
claves ni límites. Gasto incremental de esta extracción:0USD. Reviews,
comprobación del despliegue de A, campaña real071 y aceptación semántica de B
siguen fuera de esta validación.
