# Pruebas unitarias e integradas — JUP-054

Verificación: 2026-10-10. Encargo: «Implementa JUP-054 — Implementar pruebas
unitarias e integradas»; chat de origen del encargo:
`01a1248a-4e9e-7963-a891-5d8cb49345a6`. ID del chat ejecutor no proporcionado.

## Confirmado y decisiones

- [Trello](https://trello.com/c/ZsxwmagI) contrastado por integración oficial
  `DockerServer:/home/danteadmin/economicon-collaboration`; mismo alcance que
  `materiales/07-evidencias/hito-mvp-2026-10-09/backlog-dispatch-source.json`
  del workspace coordinador.
- Base `origin/develop` `c2995a1`; sin rama/PR previa JUP-054 encontrada.
  Copia aislada `tfm-economicon-jup054`, rama `test/JUP-054-critical-flows`.
- Las 194 pruebas y los 49 errores de lint de agosto son históricos. Se reutiliza
  JUP-087 y la cobertura de auth/tenant/RAG ya integrada; se añaden sólo los
  límites Azure productor/consumidor, agente/pipeline y lectura JSONB/historial.
- [Matriz y comandos](../testing/critical-flows.md),
  [evidencia por criterio](../evidence/JUP-054-validation.md),
  [OpenSpec](../../openspec/changes/jup-054-test-strategy-and-critical-flows/proposal.md).
- Vitest directo en el job CI existente; no cambia nombres de checks ni reglas
  de protección. Las integraciones reales de CI siguen opt-in.
- Roles conservados: Lucia lidera, Paris pairing, Victor revisa, Alejandro
  valida. Rama de contribución propia para liderazgo; no constituye dictamen
  independiente de sus cambios ni acredita pairing humano.

## Estado y próximos pasos

[PR draft #93](https://github.com/EconomiconFinOps/tfm-economicon/pull/93) publicada: 7 pruebas nuevas, CI Linux 2041 passed / 91 skipped y recorrido real 3 passed. Windows presenta limitaciones de socketpair y tiempos, conservadas en el informe. Consultar el informe para los resultados
finales, limitaciones y enlace de PR. Completar revisión/adopción de Lucía y los
dictámenes independientes antes de integrar/cerrar. Sin movimientos de lista Trello ni
mensajes Discord. Evidencia enlazada desde la PR; adopción de liderazgo y dictámenes pendientes.
