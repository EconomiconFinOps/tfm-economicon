JUP-054 — Cobertura del candidato final (segunda pasada). Carril `standard`.

## Context

Motivación y alcance en `proposal.md`; requisitos en `specs/critical-flow-testing/spec.md`. Aquí solo
el estado que condiciona el enfoque, leído en el repositorio el 2026-10-10 sobre `develop` en
`e1c2a8f`. Nada de esta sección se ha ejecutado todavía.

**Lo que dejó la primera pasada.** La matriz de `docs/testing/critical-flows.md` asigna siete áreas
de riesgo (auth, tenant, Azure, RAG, agente, frontend y Docker/runtime) a suites concretas, con
auditoría sobre `c2995a1`. La evidencia recoge 2041 pruebas aprobadas y 91 omitidas en CI Linux
sobre la base inicial; el comentario de cierre de la tarjeta da 2048 aprobadas y 99 omitidas en el
CI final de la PR #93 (ejecución `38040988154`). Las omitidas son las suites opt-in que necesitan
CockroachDB, pgvector o RabbitMQ.

**No hay medición de cobertura.** Ningún `requirements-dev.txt` incluye una herramienta de
cobertura, `apps/frontend/package.json` no tiene proveedor de cobertura para Vitest y
`.github/workflows/ci.yml` ejecuta `pytest tests -q` y `vitest run` sin instrumentar. `.gitignore`
ya ignora `coverage/`.

**El candidato ha cambiado.** El diff `1f57f91..e1c2a8f` sobre `apps/` añade, entre otros:

| Zona | Archivos nuevos o ampliados | Pruebas que llegaron con ellos |
| --- | --- | --- |
| Backend, preguntas de ownership | `app/services/ownership_questions.py`, `app/schemas/ownership.py`, `app/api/routes/assistant.py` | `tests/test_ownership_questions.py`, `tests/test_ownership_provenance.py` |
| Backend, cobertura de etiquetado | `app/core/tag_policy.py`, `app/schemas/tag_coverage.py`, `app/api/routes/billing.py`, `app/db/database.py` (+114 líneas) | `tests/test_tag_coverage.py` |
| Frontend, conversaciones | `src/components/MessageComposer.tsx` (sin archivo de prueba propio), `src/components/CostEvidence.tsx`, `src/pages/ConversationsPage.tsx`, `src/services/contracts.ts` | `src/components/CostEvidence.test.tsx`, `tests/ownership-conversations.test.tsx` |
| Frontend, panel de etiquetado | `src/components/TagCoveragePanel.tsx`, `src/pages/ExecutiveCostDashboard.tsx` | `src/components/TagCoveragePanel.test.tsx` |

La atribución de cada archivo a su tarjeta se confirma en el grupo 3 de `tasks.md`; aquí se infiere
de los nombres. JUP-068 solo toca `tools/`, y JUP-105 y JUP-064 son documentales.

**La máquina de trabajo no es comparable con CI.** CI usa Python 3.12 y Node 22 en Linux. La máquina
de trabajo es Windows 11 con Python 3.13 y 3.11 y Node 24. La evidencia de la primera pasada
documenta 169 fallos del backend en Windows (145 por una colisión entre los fixtures de JUP-047 y el
`socketpair` de asyncio) que no ocurren en CI Linux. Docker 29.8.1 está disponible.

**Hallazgos abiertos relacionados.** `RF-096-004` (las suites con servicios reales se omiten en CI)
y `RF-103-005` (pruebas con plazos de tiempo que fallan bajo carga, sin causa confirmada).

## Goals / Non-Goals

**Goals:**

- Una cifra de cobertura por servicio atribuible a un SHA exacto y repetible por otra persona.
- Una lista cerrada de huecos en flujos críticos, cada uno con su destino.
- Pruebas nuevas que detectan la rotura del comportamiento que cubren.

**Non-Goals:**

- Alcanzar un porcentaje, o comparar la cifra con un objetivo.
- Medir en CI o cambiar cualquier job, paso o nombre de check.
- Cubrir código que solo ejercitan las suites opt-in con servicios reales.
- Corregir defectos de producto o la colisión de fixtures en Windows.
- Medir `tools/**`.

## Decisions

**1. La herramienta de cobertura no entra en el repositorio.** Se instala solo dentro del contenedor
de medición, con versión fijada y anotada en la evidencia: `pytest-cov` para los tres servicios
Python y el proveedor `v8` de Vitest, en la misma versión que el Vitest resuelto, para el frontend.
El candidato auditado es un SHA de `develop` que por definición no contiene esa herramienta, así que
la medición tiene que aportarla desde fuera en cualquier caso.
*Alternativa descartada:* añadirla a `requirements-dev.txt` y a `devDependencies`. Cambia
`pnpm-lock.yaml` y lo que instala CI para un diagnóstico puntual, y no estaría en el SHA medido. Si
el equipo quiere medir de forma recurrente, es una tarjeta propia.

**2. Se mide en contenedores Linux desechables equivalentes a CI.** `python:3.12` para los tres
servicios y `node:22` para el frontend. El código entra en el contenedor con `git archive <SHA>`, de
modo que se mide exactamente el árbol versionado, sin archivos locales ni `.env`. Sin volúmenes
compartidos con el repositorio y sin publicar puertos.
*Alternativa descartada:* medir en Windows. Python y Node no coinciden con CI y hay fallos
documentados de la suite que no son del producto; una cobertura medida con pruebas caídas no
describe al candidato.
*Alternativa descartada:* un job de CI. Obliga a tocar el workflow y sus pruebas de política para
una medición que no debe ser un requisito.

**3. El candidato es un SHA de `develop`, con regla de repetición.** Se parte de `e1c2a8f`. Antes de
cerrar se compara con `origin/develop`: si hay commits nuevos que tocan `apps/**`, se repite la
medición de los servicios afectados y se extiende la matriz; si no se repite, la evidencia dice qué
commits quedan fuera. La promoción a `main` no pertenece a esta tarjeta: la cifra corresponde al SHA
auditado y no a lo que se promueva después.

**4. La medición solo vale si reproduce la ejecución de referencia.** La referencia es la ejecución
de CI del SHA auditado. Si la ejecución instrumentada no da las mismas pruebas aprobadas, fallidas y
omitidas, se anota la diferencia y esa cifra no se presenta como cobertura del candidato. No se
relajan plazos ni guards para que cuadre; la instrumentación ralentiza las pruebas y puede disparar
las de `RF-103-005`, en cuyo caso se repite el servicio aislado antes de concluir nada.

**5. Criterio de hueco crítico, sin porcentaje.** Un hueco es crítico si es código de un flujo de la
matriz, o añadido después de la PR #93, que ninguna prueba ejecuta y que decide una de estas cosas:
autorización o pertenencia a un tenant, validación de entrada en una ruta pública, tratamiento de
errores con efecto visible (código de respuesta, estado persistido, mensaje al operador) o
escritura en base de datos o cola. El resto recibe uno de dos destinos:

- *Aceptado*, con motivo: código defensivo inalcanzable, ramas de arranque o configuración ya
  cubiertas por las pruebas de `tools/`, o líneas ejecutadas solo en un subproceso que la
  herramienta no observa.
- *Diferido*, como hallazgo `RF-054-NNN`: hueco real que no es crítico o que necesita algo fuera de
  alcance.

El código que solo ejercitan las suites opt-in se lista aparte, cruzando la medición con las pruebas
omitidas. No es un hueco de esta pasada ni queda acreditado por ella.

**6. Parada de aprobación entre auditar y escribir pruebas.** La lista de huecos con su
clasificación se presenta antes de escribir ninguna prueba. El número de pruebas no se conoce hasta
medir, y decidir qué es crítico es una decisión de alcance. Las tareas del grupo 5 se desglosan
entonces por hueco aprobado.

**7. Cada prueba nueva se comprueba rompiendo el producto.** Como el código ya existe, una prueba
nueva pasa a la primera y eso no demuestra que detecte nada. Para cada una se introduce a mano un
cambio en el comportamiento cubierto, se comprueba que la prueba falla y se revierte; el cambio no
se versiona y la evidencia anota qué se rompió y qué falló. Si una prueba nueva falla contra el
candidato sin modificar, es un defecto: se para, se registra como hallazgo con su reproducción y se
decide si la prueba se entrega marcada como fallo esperado estricto o se deja fuera. No se debilita
la aserción.
*Alternativa descartada:* mutación automática sobre todo el servicio. No está configurada para
Python y su coste no corresponde a una pasada de cierre.

**8. No aplica ADR.** No se añade dependencia, no cambia la arquitectura ni el contrato de CI. La
decisión de no versionar la herramienta es reversible y queda en este documento.

**9. La evidencia se añade, no se reescribe.** Sección nueva con fecha en
`docs/evidence/JUP-054-validation.md`, después de las de la primera pasada, que quedan intactas con
su atribución. Los informes de cobertura generados no se versionan; la evidencia recoge la tabla por
servicio, la lista de huecos con su destino y los comandos.

## Risks / Trade-offs

- [La medición fuera del repositorio es menos cómoda de repetir] → Los comandos completos y las
  versiones fijadas van en `docs/testing/critical-flows.md`; quien repita solo necesita Docker.
- [Instalar el proveedor de cobertura en la copia del frontend puede alterar el árbol de
  dependencias] → Se instala primero con el lockfile congelado y después se añade el proveedor en la
  misma versión que Vitest; la evidencia anota la versión resuelta de Vitest antes y después.
- [Las pruebas que lanzan subprocesos no aportan cobertura del proceso hijo] → Esas líneas se
  contrastan a mano antes de llamarlas hueco y se clasifican como aceptadas con ese motivo.
- [La auditoría puede sacar más huecos de los que caben] → El criterio de la decisión 5 limita lo
  crítico y la parada de la decisión 6 permite recortar; lo demás va al backlog.
- [`develop` puede avanzar varias veces antes de entregar] → Regla de la decisión 3; "Update branch"
  que traiga cambios de aplicación obliga a repetir lo afectado.
- [Una cifra de cobertura invita a leerla como calidad] → La evidencia la presenta junto a la lista
  de huecos y repite que no hay umbral.
- [El contenedor no tiene los servicios reales] → Las suites opt-in se omiten igual que en CI; es el
  comportamiento de referencia y se declara.

## Open Questions

- Quién revisa y quién valida esta pasada. Quien lidera no puede firmar ninguna de las dos reviews;
  la asignación se registra en Trello y no cambia las tareas.
- Qué SHA se promoverá finalmente a `main`. No cambia el enfoque: la evidencia declara el SHA
  auditado.
