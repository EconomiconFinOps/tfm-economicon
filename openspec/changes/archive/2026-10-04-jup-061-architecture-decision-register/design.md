JUP: JUP-061

## Diseño

El [índice ADR](../../../../docs/adr/README.md) es el único inventario. Las justificaciones
permanecen en cada ADR o fuente existente; la evidencia de esta auditoría registra
método y comprobaciones.

ADR aplicables: [pgvector](../../../../docs/adr/ADR-0013-pgvector-retrieval-baseline.md),
[auth demo](../../../../docs/adr/ADR-0014-demo-auth-boundary.md) y
[Compose](../../../../docs/adr/ADR-0015-local-compose-deployment-boundary.md), Proposed.
Son reconstrucciones explícitas de razones del baseline; no nuevas tecnologías,
aceptaciones humanas ni justificaciones históricas atribuidas retroactivamente.

## Reglas de reconciliación

- Estado del ADR, aprobación humana e integración Git son datos independientes.
- Enlaces archivados se corrigen en la fuente que los contiene; no se copia el archivo.
- Evidencia histórica conserva fecha y límites. Precios/modelos de ADR-0002 no se
  revalidan ni se recomiendan con esta auditoría documental.
- ADR-0011/12 y fuentes JUP-021/050 ya integrados se enlazan por rutas locales.
  El corte inicial del 01/10 conserva sus referencias históricas en la evidencia.
- El inventario enlaza también las decisiones ya explicadas en corpus, guardrails,
  normalización y arquitectura. No se crean ADR duplicados para repetirlas.
- Alternativas reconstruidas se presentan como análisis actual pendiente de
  ratificación, nunca como una comparativa realizada que no consta.

## Aceptación y límites

Paris revisa la coherencia documental; Lucia valida enlaces, estados y uso en
memoria. Victor tiene pairing previsto, sin atribuirlo como hecho. Intercambio
actualizado el 03/10 según la validación de Lucia en PR #60; reemplaza los roles
del corte inicial. La ratificación corresponde a los responsables, no al autor.
ADR-0002 mantiene sus condiciones de aceptación conjunta. ADR-0005 requiere aclarar
su estado pese al merge de implementación. El despliegue productivo y la selección
comparativa original de CockroachDB no quedan acreditados por documentar el baseline.

## Verificación

OpenSpec estricto, jup:check, higiene, diff y comprobación de enlaces locales de
los documentos afectados. No se reejecutan suites de producto para un cambio
exclusivamente documental. Evidencias de ejecución citadas siguen siendo históricas.

## Sincronización del test de historial — 02/10/2026

El job Frontend build del head anterior falló en la aserción inmediata del estado
tras encontrar Sign in. Ese render no garantiza que el useEffect/navigate de
limpieza haya sido aplicado por RouterProvider. Se usa waitFor sobre la condición
observable de router.state.location.state === null antes de suscribirse y navegar
hacia atrás. Se conservan la captura completa de transiciones y la aserción que
rechaza cualquier reaparición de sessionExpired. Cambiar REPLACE por PUSH o usar
opciones vacías debe seguir fallando: la espera no sustituye esa comprobación.
Esta es una reparación del test, sin cambios en LoginPage ni nueva decisión ADR.

## Cierre documental — 04/10/2026

PR #60 integrada en develop (d61e631). Reviews de Paris y Lucía aprobadas,
enlazadas en la evidencia; la review de Victor no acredita coautoría.
El archivo promueve los dos requisitos del registro a la especificación
principal. Las ratificaciones de ADR y el pairing no acreditado mantienen
el seguimiento delimitado en tasks.md; no se conceden por archivar el cambio.
