# Consulta de ownership — JUP-037

Verificación: 10/10/2026, Europe/Paris. Origen: encargo «Implementa JUP-037 —
Responder preguntas por aplicación, equipo o etiqueta», chat
`01a124a5-532d-7ca0-8b3f-70eca9c3ec8c`, delegado desde
`01a1248a-4e9e-7963-a891-5d8cb49345a6`.

## Alcance y estado

[Trello](https://trello.com/c/n4Aplko2), ID `69da405e51b0a0b605bea448`: descripción
y roles contrastados por integración oficial DockerServer el 10/10, sin cambios
desde el refinamiento del 03/10. P1. Alejandro liderazgo, Lucia pairing, Paris
revisión, Victor validación; participación humana no inferida.

Rama propia `feat/JUP-037-ownership-query` en
`../tfm-economicon-jup037-delivery`, base `origin/develop`
`c2995a118d419dfe725247bac9c6f219a3f0ea77`. Se conservaron checkout compartido,
trabajo anterior `../tfm-economicon-jup037` y rama de refinamiento 6410950.
No había PR de JUP-037 al consultar GitHub.

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
[OpenSpec](../../openspec/changes/jup-037-ownership-cost-query/proposal.md).
Pruebas backend: `test_ownership_questions.py`, `test_ownership_provenance.py`;
fixtures sintéticos explícitos, con casos SQL opt-in vía
`JUP086_COCKROACH_TEST_URL` sobre instancia efímera propia.

## Pendientes reales

Completar pruebas y entrega revisable; registrar comandos/resultados en evidencia.
Pairing Lucia, Revision Paris, Validacion Victor e integración siguen pendientes.
Application/owner se prueban con datos sintéticos; no se acredita fuente
desplegada. El mapping simulado actual solo admite CostCenter, Project, env, org.
Sin despliegue, proveedor de IA, gasto, mensajes Discord ni cierre/archivo de chat.
