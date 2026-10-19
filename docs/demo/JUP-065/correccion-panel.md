# Corrección del panel — JUP-065

Verificado: 19/10/2026. Origen: chat `01a12c49-7488-72f0-9077-1137c5c4f2a6`,
JUP-065/PR63 y ensayo RC. [Tarjeta](https://trello.com/c/SZUFo4ol).
[PR143](https://github.com/EconomiconFinOps/tfm-economicon/pull/143) abierta.
Base `f444ba11e38203b6cfd645a098fd9946d55955e3`; rama independiente
`fix/JUP-065-panel-actions-citations`, destino develop, sin merge.

## Problema y corrección

El ensayo real del RC encontró next_actions de 003/023 ocultas en UI, fuentes
sin apertura y prosa incompleta ya persistida en 003/dashboard. Ese último caso
tenía contexto de facturación contrario a la precondición de la rúbrica, pero
el defecto de texto era real; no se atribuye a fragmentación HTTP.

- AnswerEvidence muestra las acciones persistidas en panel e historial.
- Cada fuente abre un diálogo accesible del fragmento recuperado, página/sección
  si existen y texto inerte. El backend congela contenido sólo de citas seleccionadas
  del contexto autorizado; no consulta corpus vivo ni abre URLs del modelo.
- Mensajes históricos sin contenido conservan el extracto con aviso. El visor no
  contiene el documento entero ni prueba por sí mismo pertinencia semántica.
- Renderer y cierre de stream rechazan conectores de continuación sin prosa ni
  cantidad/cálculo tipado posterior. No rellenan cifras. Prompt y contrato cambian
  de fingerprint. Los deltas siguen siendo provisionales; no se reescribe historia.

El control sintáctico de narrativa sólo cubre patrones españoles/ingleses
detectables, no todos los errores de lenguaje. Una respuesta inválida usa el flujo
de error existente; no se garantiza respuesta correcta de un modelo. El recurso
histórico `/evidence` no se reconstruye: el visor usa la cita persistida.

## Pruebas y reproducción

Antes de implementar fallaron 3 regresiones UI, 4 de narrativa y 1 de contenido
documental. Después pasan 92 pruebas de componentes/colores, 69 del backend de
metadatos/operaciones y 107 del procesador (render/stream/contrato). Typecheck, build y lint
frontend ejecutados; quedan avisos preexistentes en ChatPresentation y tamaño
del bundle. OpenSpec 82/82, trazabilidad e higiene conformes.

Chromium escritorio/móvil: 6 pasos con HTTP **sintético**, acciones, apertura,
Escape, recarga y cierre explícito; no validación generativa. El primer instrumento
omitió reference-date; corregido y repetido sin peticiones inesperadas. Evidencia
local: `materiales/07-evidencias/JUP-065-panel-fix-20261019/` del workspace Economicon.

```text
corepack pnpm --filter @finops/frontend test -- --maxWorkers=2
corepack pnpm --filter @finops/frontend typecheck
corepack pnpm --filter @finops/frontend lint
corepack pnpm --filter @finops/frontend build
python apps/processor/build_tokenizer.py
python apps/processor/build_tokenizer.py --embedding-only
# Desde apps/backend y apps/processor, con sus requirements-dev:
python -m pytest tests -q
corepack pnpm openspec:validate
corepack pnpm jup:check -- --change jup-065-panel-actions-citations
corepack pnpm jup:cleanup:check
```

La primera suite frontend bajo alta concurrencia falló 5 pruebas; limitando
concurrencia quedaron Escape propagado y color literal, corregidos y verificados.
Suite frontend final: **1380/1380 en 92 archivos**. Python global 3.14 carecía
de dependencias y tenía tokenizer 0.23.1: venv propio preparado con 0.22.1 y recurso
de embeddings fijado. No presentar errores de aquel entorno como aceptación.
La primera suite backend con Python global no fijado terminó con 2263 pass,
367 skip, 209 fail y 102 errores (recursos/contrato y dependencias); no se acepta
ese corte. Las 69 pruebas afectadas se repitieron conformes en venv fijado.
La CI usa Linux/Python3.12; resultados/enlaces del SHA publicado se registran en
la sección Validacion de la nueva PR.

## Pendientes

Alejandro lidera, Lucía pairing, Paris revisión y Víctor validación según Trello:
son responsabilidades, no participación realizada. Ninguna excepción anterior
de merge/pairing/agentes se extiende a esta PR. Faltan CI final, pairing y dos
dictámenes propios; después de integración autorizada, repetir ensayo generativo
y narrado para comprobar aclaraciones visibles y citas pertinentes.
No consumo de modelos, cierre de tarjeta, Discord, otras PR ni merge.


## Regresiones del ensayo real de PR143 (19/10/2026)

El ensayo f64a26be completó cinco generaciones y comprobó acciones/citas/historial,
pero dejó «anómalo.Para» (003), «historia.Puedo» (025), «En cambio,» y una introducción
acabada en dos puntos antes de cita (004). Evidencia externa:
materiales/07-evidencias/JUP-065-ensayo-PR143-20261019/README.md.

Se inserta un espacio sólo entre segmentos de prosa con puntuación final .?! y
mayúscula inicial. Se preservan espacios/saltos existentes, palabras partidas,
citas literales y cantidades tipadas. Se valida también la concatenación original
para no debilitar controles de ecuaciones/slots. Backend, processor y streaming
usan el mismo ensamblado; los espacios cuentan dentro del límite final.

Una coma, punto y coma o dos puntos al final de prosa requieren continuación de
prosa o cantidad tipada; una cita no la completa. El prompt exige afirmaciones
completas antes de sus pasajes de apoyo. Contrato:
`bounded-prose-completion-and-sentence-spacing-v2`. El candidato incompleto se
rechaza por el flujo existente; no se reescriben afirmaciones, citas o historial.
Es un control sintáctico acotado, no garantía universal de calidad semántica.

`regresiones-narrativa.json` guarda reproducciones mínimas de las fronteras del
ensayo, no payloads crudos del proveedor. Cinco regresiones fallaron antes del
arreglo. Después:197 pruebas processor y73 backend afectadas PASS, incluidas
fragmentación del stream1/7/todo, literalidad, longitud y cálculos. Un fixture nuevo
usó inicialmente un dict en lugar del catálogo tipado: corregido antes de la pasada
verde, sin confundir ese fallo de instrumento con un defecto de producto.

Sin consumo nuevo de modelos. La próxima aceptación generativa debe fijar este
nuevo SHA/prompt, sin transferir la evidencia anterior. Pairing Lucía, revisión
Paris y validación Víctor siguen pendientes; ninguna excepción heredada. CI del
nuevo SHA se registra con enlaces al publicar. Sin merge ni otras PR.
