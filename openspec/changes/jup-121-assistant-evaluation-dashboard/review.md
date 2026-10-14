# Revisión de jup-121-assistant-evaluation-dashboard

JUP: JUP-121 · [Trello](https://trello.com/c/aIdxwsXR) · ADR: [ADR-0022](../../../docs/adr/ADR-0022-assistant-evaluation-results-in-grafana.md)

## Resumen

Pendiente hasta cerrar la implementación.

## Excepciones doc-only

Las tareas sin código de producto no pasan por tester, coder ni mutación; se verifican con `openspec:validate` y `jup:check`.

| Tarea | Entregable | Verificación |
| --- | --- | --- |
| 1.1 | `docs/adr/ADR-0022-assistant-evaluation-results-in-grafana.md`, fila en `docs/adr/README.md` y enlace desde `design.md` | `openspec:validate` 70/70 y `jup:check` en verde |
| 1.2 | `docs/validation/evaluation-dashboard.md` (contrato `rows-v1`, manifiesto, clasificación, comparabilidad y juicio humano); `design.md` y la tarea 2.7 ajustados para incluir los recuentos `pass`/`fail` entre lo que depende de juicio humano, y la columna `selected` | `openspec:validate` y `jup:check` |
