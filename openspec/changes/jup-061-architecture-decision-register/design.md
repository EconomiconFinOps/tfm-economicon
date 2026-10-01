JUP: JUP-061

## Diseño

El [índice ADR](../../../docs/adr/README.md) es el único inventario. Las justificaciones
permanecen en cada ADR o fuente existente; la evidencia de esta auditoría registra
método y comprobaciones, y continuidad solo enlaza esos documentos.

ADR aplicables: [pgvector](../../../docs/adr/ADR-0013-pgvector-retrieval-baseline.md),
[auth demo](../../../docs/adr/ADR-0014-demo-auth-boundary.md) y
[Compose](../../../docs/adr/ADR-0015-local-compose-deployment-boundary.md), Proposed.
Son reconstrucciones explícitas de razones del baseline; no nuevas tecnologías,
aceptaciones humanas ni justificaciones históricas atribuidas retroactivamente.

## Reglas de reconciliación

- Estado del ADR, aprobación humana e integración Git son datos independientes.
- Enlaces archivados se corrigen en la fuente que los contiene; no se copia el archivo.
- Evidencia histórica conserva fecha y límites. Precios/modelos de ADR-0002 no se
  revalidan ni se recomiendan con esta auditoría documental.
- Números 0011 y 0012 están usados en PR abiertas; se enlazan por commit.
- El inventario enlaza también las decisiones ya explicadas en corpus, guardrails,
  normalización y arquitectura. No se crean ADR duplicados para repetirlas.
- Alternativas reconstruidas se presentan como análisis actual pendiente de
  ratificación, nunca como una comparativa realizada que no consta.

## Aceptación y límites

Paris revisa la coherencia y ratificación documental; Victor valida enlaces,
estados y uso en memoria. Lucia conserva pairing previsto sin atribuirlo como hecho.
ADR-0002 mantiene sus condiciones de aceptación conjunta. ADR-0005 requiere aclarar
su estado pese al merge de implementación. El despliegue productivo y la selección
comparativa original de CockroachDB no quedan acreditados por documentar el baseline.

## Verificación

OpenSpec estricto, jup:check, higiene, diff y comprobación de enlaces locales de
los documentos afectados. No se reejecutan suites de producto para un cambio
exclusivamente documental. Evidencias de ejecución citadas siguen siendo históricas.
