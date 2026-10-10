# Dimension vectorial desde Settings — JUP-102

Ultima verificacion: 2026-10-10. Origen: encargo «Implementa JUP-102 — Unificar la
dimension vectorial desde Settings y fichero de entorno (RF-021-001)», chat
`01a124a8-973c-75a0-b0ec-cbe4e560e0c2`.

## Alcance y decisiones

- [Tarjeta](https://trello.com/c/4OJ1OK53), registro completo contrastado mediante
  DockerServer `/home/danteadmin/economicon-collaboration`, sin cambios de roles,
  prioridad, fechas ni estado. Sin etiqueta de prioridad; descripcion conserva P1.
- Liderazgo asignado Lucia Mateo, pairing Paris Arcos Martin, revision Victor
  Mendez, validacion Alejandro Aguado. Asignacion no acredita participacion.
- Copia propia `tfm-economicon-jup102`, rama `fix/JUP-102-vector-settings`, base
  `c2995a118d419dfe725247bac9c6f219a3f0ea77` de origin/develop. Checkout compartido
  y otras ramas intactos. No existia rama/PR especifica de JUP-102 al comenzar.
- Migracion 001 recibe la dimension del PgVectorStore mediante argumentos por
  version del MigrationRunner. No relee entorno ni instancia otro Settings.
  Precedencia, guard seguro, migracion 002 y ledger existentes conservados.
- [Evidencia por criterio](../evidence/JUP-102-validation.md),
  [runbook](../runbooks/vector-database.md),
  [hallazgo](../../openspec/findings/backlog.md#rf-021-001--dimension-desde-fichero-de-entorno).

## Evidencia y limites

Reproduccion real sobre codigo original: fichero16, entorno sin dimension,
columna8, ledger001/002 y StartupError. Fix probado con PostgreSQL17.11/pgvector0.8.6
en contenedor exclusivo y bases UUID sinteticas. Regresion offline detecta el fallo
original. Tests cubren default/env/fichero/precedencia y snapshots de esquema,
ledger/indices/filas al rechazar cambios de dimension; no conversion automatica.
Suite processor: 467 passed / 53 skipped (Cockroach/LiteLLM fixture no ejecutados).
Backend vector real: 17 passed. Suite amplia Windows: 732 passed/34 skipped/166 failed;
un fallo socketpair/asyncio reproducido en develop original, resto salud/DNS/tiempos
no contrastado individualmente. No se modifica runtime backend ni se declara suite verde.
Gobernanza 95 passed; OpenSpec antes/despues de archivo 56/56 y 55/55,
trazabilidad/higiene/sintaxis correctas.

Logs de trabajo locales fuera de Git en
`../materiales/07-evidencias/JUP-102-2026-10-10/` desde la raiz de esta copia:
`repro-before.log`, `processor-suite.log`, `backend-suite.log`, `targeted-real.log`,
`governance.log`, `python-versions.txt`. No guardar credenciales en esta continuidad.
Tambien `backend-real.log` (17 pass) y `backend-baseline.log` (fallo Windows original).

## Pendientes

Entrega publicada: [PR #108 draft](https://github.com/EconomiconFinOps/tfm-economicon/pull/108),
implementacion `bfffbea4be94ad9e8a01a687fc3cd28e58fdd606`. JUP policy PASS en la
apertura; JUP reviews falla por ausencia de los dos dictamenes requeridos, no
se modifica ese control. Consultar CI sobre el head final en la PR.
Evidencia enlazada en Trello mediante comentario `6ac9f273ba91202e4a30910a`,
publicado por el puente oficial y leido de vuelta con texto identico. No cambio
de lista/roles/criterios. Contenedor sintetico y tunel propios retirados al acabar;
ningun volumen JUP-021 utilizado o eliminado.

Entrega tecnica propia para Lucia; no se atribuye liderazgo, pairing o aceptacion
por abrir una contribucion asistida. CI y dictamenes humanos deben comprobarse
sobre el head publicado; validacion independiente no puede inferirse de estos tests.
Integracion en develop y evidencia enlazada en Trello antes de Hecho. No merge,
movimiento de tarjeta ni mensajes Discord realizados.
