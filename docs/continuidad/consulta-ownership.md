# Consulta de ownership — JUP-037

Verificación: 10/10/2026, Europe/Paris. Origen: encargo «Implementa JUP-037 —
Responder preguntas por aplicación, equipo o etiqueta», delegado desde el chat
`01a1248a-4e9e-7963-a891-5d8cb49345a6`; identificador receptor no confirmado.

## Alcance y estado

[Trello](https://trello.com/c/n4Aplko2), ID `69da405e51b0a0b605bea448`: descripción
y roles contrastados por integración oficial DockerServer el 10/10, sin cambios
desde el refinamiento del 03/10. P1. Alejandro liderazgo, Lucia pairing, Paris
revisión, Victor validación; participación humana no inferida.

Rama propia `feat/JUP-037-ownership-query` en
`../tfm-economicon-jup037-delivery`, base `origin/develop`
`c2995a118d419dfe725247bac9c6f219a3f0ea77`. Se conservaron checkout compartido,
trabajo anterior `../tfm-economicon-jup037` y rama de refinamiento 6410950.
No había PR de JUP-037 al consultar GitHub. Entrega publicada posteriormente como
[PR #100](https://github.com/EconomiconFinOps/tfm-economicon/pull/100), draft,
commit inicial `b85b51b`. [Evidencia por criterio](../evidence/JUP-037-ownership-queries.md).

La instrucción actual autoriza código y supera la restricción histórica de no
iniciar. Se reutilizó aquel refinamiento, actualizando alcance al título/cuerpo
de tarjeta: proyecto, aplicación, equipo/owner, centro de coste y etiqueta.

## Decisiones actuales

- Selección explícita `ownership_query` en conversación; no parser de texto libre.
- Billing v2 exacto por tenant/periodo UTC, valores literales y monedas separadas.
- Proyecto y aplicación son distintos; organization/org no equivale a owner.
- Contexto total, selección y coste sin dimensión se conservan por separado.
- Ausencia completa de etiqueta es `insufficient_data`, no cero ni unsupported.
- Evidencia persistida `cost_evidence` 1.0 + adaptador ownership-1.0; procedencia
  en misma consulta SQL/transacción, sin citas del corpus para importes.
- JUP-036 PR #69 draft aee2571 no integrada: contrato reutilizado, código ajeno
  no incorporado. Pendiente prueba conjunta y exclusión de consultas simultáneas
  al integrar `cost_query`. JUP-015 conserva catálogo/taxonomía; no se inventan
  valores válidos ni alias nuevos. Alias Project→application del documento
  histórico JUP-084 no se aplica por contradecir la semántica solicitada.

[Contrato y límites](../api/ownership-questions.md).
[OpenSpec archivado técnicamente](../../openspec/changes/archive/2026-10-10-jup-037-ownership-cost-query/proposal.md),
sin implicar aceptación de la tarjeta o merge.
Pruebas backend: `test_ownership_questions.py`, `test_ownership_provenance.py`;
fixtures sintéticos explícitos, con casos SQL opt-in vía
`JUP086_COCKROACH_TEST_URL` sobre instancia efímera propia.

## Pendientes reales

Entrega comprobada: 209 tests backend con SQL real aislado (sin omisiones),
35 frontend (HTTP simulado), tipos/lint/build PASS, OpenSpec 56/56 y gobernanza
82/82. El frontend requirió esperas DOM 10 s/runner 30 s y un worker en un
override temporal ignorado, sin modificar aserciones. Dos correcciones de revisión
automatizada: escapar controles de etiquetas ingeridas y exponer grupos más allá
del resumen de 20. No equivalen al dictamen de Paris.

CI consultada sobre b85b51b: policy/OpenSpec/tipos/build y Python backend,
processor y azure-cost-api verdes; `JUP reviews` falla exclusivamente por ausencia
de `Revision JUP-037` y `Validacion JUP-037`, confirmado en sus logs.
Actualizar el resultado final al retomar; no interpretar estos checks parciales
como CI completa del commit documental posterior (sin cambios de runtime).

Trello actualizado por integración oficial y descripción releída: rama, PR100 e
informe enlazados; tarjeta en **30 — En curso**. Roles, miembros, fechas y criterios
preservados. [Registro de entrega](https://trello.com/c/n4Aplko2#comment-6ac9ede7d532f7533a85b38d).
La base efímera `economicon-jup037-test` y su túnel se retiraron al terminar;
listado remoto filtrado al nombre exacto vacío. No se modificaron servicios ajenos.

Pairing Lucia, Revision Paris, Validacion Victor e integración siguen pendientes.
Application/owner se prueban con datos sintéticos; no se acredita fuente
desplegada. El mapping simulado actual solo admite CostCenter, Project, env, org.
Sin despliegue, proveedor de IA, gasto, mensajes Discord ni cierre/archivo de chat.
