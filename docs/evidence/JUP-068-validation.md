# Evidencia técnica — JUP-068

Verificado el 2026-10-03. Base `origin/develop`:
`6410950315b0e3c22057d09015e11e38c5e455ab`.
Rama `feat/JUP-068-business-metrics`.
[Tarjeta](https://trello.com/c/JYaiGKKv).
Origen: chat «JUP-068 — Métricas funcionales de negocio»; identificador no disponible.

## Entregable y criterios

| Criterio mínimo Trello | Evidencia y estado |
| --- | --- |
| Resultado funcional verificable | CLI genera informe determinista de tiempo, allocation y potencial; ejemplo sintético reproducible |
| Pruebas necesarias verdes | 31 pruebas del instrumento; 257 pruebas Node de herramientas en total, todas correctas |
| Documentación y decisiones actualizadas | Protocolo, fórmula/unidades, objetivos propuestos, límites y OpenSpec versionados |
| PR revisado y vinculado | Publicación preparada; revisión Lucía pendiente |
| Validación funcional y evidencia enlazadas | Aritmética/CLI probadas; validación Paris y piloto con observaciones pendientes |

## Comprobaciones

Entorno local: Windows PowerShell, Node.js 24.14.1, pnpm 9.0.0.

| Comando | Resultado |
| --- | --- |
| `corepack pnpm install --frozen-lockfile` | Correcto; lockfile sin modificar |
| `node --test tools/business-metrics.test.mjs` | 31/31 |
| `node --test tools/*.test.mjs` | 257/257 |
| `node tools/business-metrics.mjs validate docs/validation/JUP-068-example.json` | Correcto; procedencia synthetic |
| `node tools/business-metrics.mjs report docs/validation/JUP-068-example.json` | 360000 ms / 40 % ahorro temporal; cobertura asignada 70 %, gobernada 90 %; 14000 céntimos / 14 % potencial; solo fixture |
| `node tools/jup-check.mjs --all` | Diez changes enlazados correctamente |
| `node tools/jup-cleanup-check.mjs` | Correcto |
| `node tools/assistant-corpus.mjs validate` | Correcto; corpus no modificado |
| `corepack pnpm openspec:validate` | 41 correctos, cero fallos |
| `git diff --check` | Correcto |

El conjunto de pruebas cubre pesos por coste, shared/excluded, ausencia de medición,
denominador cero, cero ahorro conocido, ahorro temporal negativo, fallos/bloqueos,
duplicados, dinero inválido/desbordamiento, solapamientos, evidencia/owner/regla
ausentes, periodos inválidos, moneda/base mezcladas y uso de CLI desde otro directorio.
CI añade validación del fixture y pruebas del instrumento al job OpenSpec.

## Límites y pendientes

La comprobación técnica no acredita ahorro ni calidad del asistente real. No se
ejecutaron respuestas de LLM, Azure real, captura de tiempos de usuarios ni optimizaciones.
No se modificó runtime, por lo que no se ejecutaron tests Python ni build frontend
como validación local de esta definición; los jobs existentes de CI se conservan.
Los porcentajes usan punto flotante (presentar con redondeo sin alterar el registro).
El verificador comprueba referencias presentes; una persona debe inspeccionar su contenido.

Liderazgo Víctor, pairing Alejandro, revisión Lucía, validación Paris, según Trello
consultado por el puente DockerServer `snapshot-20261003T210000Z.json`.
Confirmación del método/objetivos, participación efectiva, reviews y piloto pendientes.
No se declara la tarjeta terminada ni se reasignan roles.
