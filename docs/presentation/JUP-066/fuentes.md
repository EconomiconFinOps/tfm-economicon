# Fuentes y límites del guion — JUP-066

Consulta documental: 10/10/2026, Europe/Paris. Base de esta contribución: `c2995a118d419dfe725247bac9c6f219a3f0ea77` (`origin/develop`). [Guion](guion.md) · [Evidencia por criterio](../../evidence/JUP-066-preparacion.md).

## Fuentes contrastadas

| Fuente | Versión / localización | Uso y límite |
| --- | --- | --- |
| PDF oficial del Proyecto Júpiter | Workspace, fuera del clon: `materiales/01-requisitos/Guion-proyecto-Jupiter.pdf`; SHA-256 `53908876a615a2efc1c7c1ede739f40af23cea555a9f0deaabc18e580ea152b0` | Página física 4, impresa 5: 10–20 min, todos los miembros, criterios de exposición y preguntas. Texto y página contrastados visualmente; sin calendario. No se copia el PDF a Git. |
| `Guion_PJ.md` en Drive | Localizado por enlace exacto en [PROYECTO — Enlaces y coordinación](https://trello.com/c/PGC5g5V9); modificado 09/10/2026 08:24:51.390Z | Lectura completa del texto; confirma duración y participación de la sección Evaluación. No se copia la transcripción a Git. |
| `Memoria_Economicon` compartida | Enlace en esa misma tarjeta; modificación 09/10/2026 18:04:25.675Z; revisión `AHj4eMSHtOtYa-X0IrJWEm3v7znan3phVnfNzF1i2lWnKscY4wDlwglNtjjIQJsbixrfQr_yhl0GwEuChdgj8OPgc7BtVtEdnIboPEbmwZ4` | Leída para este encargo, sin editarla ni copiarla al repositorio. Problema, audiencia y propuesta sirven de contexto; no se aceptan como prueba sus afirmaciones de ejecución. |
| [Demo JUP-065 / PR63](https://github.com/EconomiconFinOps/tfm-economicon/pull/63) | Head consultado `48ee74250714c6fe50946906824b80dc9ffd59fa`, abierta; preparación fijada al dataset `de0d62e7c0028f35a81c5087f531d19031a90e81` | Guion, preflight, README, datos y plantilla de ensayo. Referencia mensual vigente y límites; no se incorpora su rama ni se ejecuta el MVP. |
| [Informe JUP-070](../../evidence/JUP-070-run-1-report.md) y [datos](../../evidence/JUP-070-run-1-results.json) | Ejecución 08/10/2026 20:13:54Z, commit `b12b3c80d0954a1f1a7bd12fae31456f269cff52`; proveedor/alias mock, plantilla sin modelo | 0/20 answer y 28 fail totales son históricos y provisionales; casos críticos con juicio de una sola persona. No calidad ni latencia de un modelo real. No se reejecuta esa evaluación. |
| [Arquitectura](../../architecture.md), [ADR Azure](../../adr/ADR-0001-azure-cost-api-simulation.md), [ADR vectorial](../../adr/ADR-0013-pgvector-retrieval-baseline.md), [gateway](../../adr/ADR-0002-litellm-openrouter.md) | Versiones de la base `c2995a1` | Soporte del discurso técnico y sus compromisos. No equivalen a un despliegue real verificado por JUP-066. |
| [Gobernanza de memoria](../../memoria/README.md), [contribuciones](../../contributions/JUP-064-register.md) y [hitos](../../planning/JUP-080-milestones.json) | Base `c2995a1`; contribuciones corte 04/10; calendario provisional | Fuente editable externa, propiedad de apartados, distinción asignación/acción y fechas pendientes. No se duplican los apartados de memoria. |

El borrador local `materiales/06-entregables/Memoria_Economicon-borrador-2026-08-28.md` fue un antecedente consultado, superado para este contraste por la lectura del documento compartido. La carpeta local `demo-funcional-jup065` también conserva una preparación inicial: manda la PR fijada arriba. Ninguno se presenta como memoria o demo finales.

## Dependencias y divergencias que condicionan el uso final

- **JUP-065:** el ensayo integrado conserva `not_run`. Preparar el guion completo no acredita sus dependencias ni cierra esa tarjeta. La revisión favorable de Paris sobre `48ee742` se limita a preparación; no se atribuye a este trabajo ni sustituye la validación del ensayo.
- **Memoria:** c–i siguen reservados en la revisión leída. Usamos a–b como contexto y documentación técnica para el discurso; no redactamos los apartados de JUP-060/062/063/064/109/110/111. La tabla vigente de propiedad está en `docs/memoria/README.md`; algunas reservas de la memoria todavía remiten a asignaciones antiguas.
- **Divergencia de viabilidad técnica:** memoria, tab `t.0`, párrafo de inicio 6812, afirma comprobación de extremo a extremo. La demo consultada declara ensayo pendiente. El guion no reproduce la afirmación como resultado acreditado: falta asociarla a ejecución, commit, modo y alcance válidos. Resolver por JUP-062/JUP-065 antes de la defensa.
- **Evaluación:** las frases de impacto de la memoria no convierten umbrales en resultados. El informe JUP-070 distingue 20 answer dentro de 28 casos y modo mock; mantener ese denominador. La evaluación del modelo y la evaluación funcional de usuarios corresponden a sus tarjetas, no a esta preparación oral.
- **Modelo/costes:** no se trasladan precios, gastos acumulados ni modelo elegido a afirmaciones de ejecución actual. Registrar el proveedor realmente utilizado en el ensayo. No se efectúan llamadas de pago desde JUP-066.
- **Generación aún no integrada en la base:** `docs/architecture.md`, sección «Estado actual del asistente», y `apps/backend/app/services/assistant.py` conservan construcción determinista de la respuesta, sin invocación LLM generativa. No es únicamente falta de ensayo. La flecha discontinua del esquema representa esa integración futura; el gateway de embeddings no acredita generación. Reconciliar con JUP-035/JUP-065 antes de activar el modo en vivo.
- **Calendario:** 23/10 entrega, 27/10 ensayo y 29/10 defensa son provisionales en JUP-080. La continuidad local de demo del 09/10 recoge además propuesta de ensayo el 28/10, mensaje de Paris `1555998340037214209`, sin acuerdo institucional acreditado. Es una referencia histórica local, no una nueva lectura de Discord ni una convocatoria.

## Cobertura del requisito de presentación

| Requisito oficial / tarjeta | Dónde se prepara | Qué falta comprobar |
| --- | --- | --- |
| Problema, solución, demo, arquitectura, resultados y futuro | Guion, bloques 1–6 | Claridad con audiencia y soportes reales |
| 10–20 min y todos los miembros activos | Cronograma 18 min y recorte 15 min | Cronometraje humano y acuerdo de reparto |
| Argumentar decisiones y dominio del conjunto | Bloque 4 y preguntas previstas | Respuestas de las cuatro personas |
| Justificar aportación individual | Intervenciones y ficha con cuatro filas | Aportación concreta confirmada por cada persona |
| Valor de negocio: impacto, viabilidad, diferenciación | Bloques 1, 2, 5 y 6 | Validación con usuarios, economía de despliegue y resultados efectivos |
| IA generativa, base vectorial, API/modelo, CI/CD, monitorización | Bloques 2–4 y referencias técnicas | Ejecución integrada correspondiente; describir diseño no acredita funcionalidad |
| Coherencia con memoria y evaluación | Tabla de evidencia y divergencias | Incorporación humana de los apartados pendientes y reconciliación final |

## Condiciones de entrega

Esta rama es una contribución documental separada para Lucia Mateo, liderazgo registrado. Paris conserva pairing, Víctor revisión y Alejandro validación/documentación. Las asignaciones se verificaron mediante el cliente de la integración en `DockerServer:/home/danteadmin/economicon-collaboration` el 10/10/2026, consulta 07:10:53Z; JUP-066 estaba en Backlog, sin fecha, rama ni PR enlazados. GitHub no devolvió PR ni rama remota JUP-066 en el contraste inicial.

La preparación asistida no acredita pairing, aceptación, revisión de Víctor ni validación independiente de Alejandro. Para preservar el papel de validación, se entrega copia/rama propia y parche a liderazgo, sin empujar una rama ajena ni abrir una PR atribuyendo liderazgo falso. Lucía podrá adoptar el contenido en su PR contra develop. La memoria sigue su gobernanza externa y no se modifica en esta entrega.
