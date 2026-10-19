# Corrección del panel — JUP-065

Verificado: 19/10/2026. Origen: chat `01a12c49-7488-72f0-9077-1137c5c4f2a6`,
JUP-065/PR63 y ensayo RC. [Tarjeta](https://trello.com/c/SZUFo4ol).
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
documental. Después pasan 92 pruebas de componentes/colores, 47 del backend de
metadatos y 105 del procesador (render/stream/contrato). Typecheck, build y lint
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
Suite completa final en curso al registrar este corte. Python global 3.14 carecía
de dependencias y tenía tokenizer 0.23.1: venv propio preparado con 0.22.1 y recurso
de embeddings fijado. No presentar errores de aquel entorno como aceptación.
La CI usa Linux/Python3.12; resultados/enlaces del SHA publicado se registran en
la sección Validacion de la nueva PR.

## Pendientes

Alejandro lidera, Lucía pairing, Paris revisión y Víctor validación según Trello:
son responsabilidades, no participación realizada. Ninguna excepción anterior
de merge/pairing/agentes se extiende a esta PR. Faltan CI final, pairing y dos
dictámenes propios; después de integración autorizada, repetir ensayo generativo
y narrado para comprobar aclaraciones visibles y citas pertinentes.
No consumo de modelos, cierre de tarjeta, Discord, otras PR ni merge.
