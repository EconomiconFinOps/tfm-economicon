## 1. Diseno y aprobacion

- [x] 1.1 Validar propuesta, diseno, escenarios OpenSpec y trazabilidad.
- [x] 1.2 Obtener aprobacion humana explicita del diseno antes de tests/codigo.

## 2. Implementacion

- [x] 2.1 Ampliar las pruebas de topologia y configuracion; registrar Red.
- [x] 2.2 Integrar el perfil `ai`, redes, salud, secretos y volumen sin alterar
      el arranque simulado ni los aliases/pins.
- [x] 2.3 Documentar entorno, arranque/parada, claves separadas y limites.
- [x] 2.4 Ejecutar Green y mutaciones focalizadas, conservando resultados.

## 3. Verificacion y entrega

- [x] 3.1 Comprobar Compose real en proyectos aislados sin gasto: mock, perfil
      `ai`, autenticacion positiva/negativa y persistencia tras recrear.
- [x] 3.2 Ejecutar controles aplicables, revision tecnica y validacion local
      independientes, con evidencia por criterio y limites.
- [x] 3.3 Presentar resultado para aprobacion final; archivado, PR, reviews
      humanas, merge y Trello requieren autorizaciones y pasos propios.


## Consolidacion TL — 08/10/2026

- [x] Reunir evidencia final del autor (mock, salud, gateway sintetico y real), preservar primer ensayo incompleto, consumo y limites, y mapear los siete criterios oficiales transmitidos por PM. Vease `docs/evidence/JUP-108-validation.md`.
- [x] Completar 3.2 mediante Revisor independiente y luego Validador, cada uno con original/hash PM previo y retorno independiente; no atribuir independencia a las campañas previas del autor.
- [ ] Completar 3.3 tras esos dictamenes: aprobacion final humana nueva y DoD; archivo/PR/reviews humanas/integracion conservan autorizaciones y etapas propias. No hay aprobacion final ni permisos Git/publicacion por esta consolidacion.


## Reconciliacion y gates vigentes — 08/10/2026

- [x] Resolver MUT-01 con tres operadores en copia/test fijo y relectura independiente REVIEW_PASS; conservar FAIL original.
- [x] Reconciliar por MERGE autorizado develop/JUP-047 en ff2ea6be, preservando15rutas108 y respaldo/stash; checks afectados y nuevas imagenes backend/frontend preparados.
- [x] Releer solo impacto real de reconciliacion/README/evidencia bajo original PM nuevo, conservando review previa y sensibilidad por identidad.
- [x] Reanudar validacion independiente de criterios sobre base reconciliada, con original PM nuevo; checkpoint antiguo no es aceptacion final.
- [ ] Completar3.2/3.3, DoD y aprobacion final humana; archivo/PR/reviews humanas/integracion requieren pasos y permisos propios. No marcar globalmente completada la entrega por checks locales.


## Entrega local independiente — 08/10/2026

- [x] Revisión focal reconciliada REVIEW_PASS y validación local favorable criterios1–6; criterio7 parcial por etapas posteriores, sin aceptación humana inventada.
- [x] Verificar14recibos seguros del Validador y conservar originales PM nuevos/anteriores, guards propios y controles independientes PM.
- [x] Cerrar3.2 con matriz de controles documentales/equivalencias vigente y disposición de referencias históricas faltantes; no reconstruir guards ni repetir baterías válidas.
- [ ] Aprobación final humana nueva, DoD/disposición y archivo autorizado antes de PR; revisiones humanas y merge posteriores. Sin permisos de publicación/Git implícitos.


## Disposición humana de registros históricos — 09/10/2026

- [x] Paris aprueba exclusivamente para JUP-108 la excepción por ausencia de los tres guards históricos diseño/Red/Green; PM registra00:07:28Canary, fuente externa preservada. Se completa3.2 con evidencia aplicable y R/V independientes, bajo esa excepción explícita.
- [x] Conservar helperFAIL y originales, sin PASS histórico/snapshots reconstruidos/cambios de helper ni repetición funcional. Véase excepción en evidencia/review.
- [ ] Aprobación final nueva de entrega y disposición final aplicable; archivo/commit/push/PR/publicación/merge no autorizados por la excepción. Criterio7 y3.3 continúan pendientes del flujo posterior.


## Cierre final autorizado — 09/10/2026 (estado vigente)

- [x] Paris aprueba la entrega final y autoriza archivo de JUP-108 en esta misma rama; fuente PM00:08:45Canary, no hora humana inventada. Excepción histórica previamente aprobada y helperFAIL conservados.
- [x] Roles vigentes indicados por Paris con fecha08/10/2026: Paris Arcos liderazgo; Lucía Mateo pairing/coautoría; Víctor Méndez revisión de PR; Alejandro Aguado validación, pruebas y documentación. Historial preservado; no participación inferida ni lectura Trello nueva.
- [x] Ejecutar archivo autorizado, promover delta canónico, conservar DoD/disposición y reparar enlaces afectados.
- [ ] Publicación/commit/push/PR/CI/reviews humanas de Víctor y Alejandro e integración: pasos posteriores con permisos propios, no completados por el archivo.

Los pendientes de aprobación final de apartados históricos quedan sustituidos por esta decisión; no se marcan como realizados los hitos de publicación/reviews/merge.


Archivo ejecutado: `2026-10-09-jup-108-litellm-compose`, misma rama, tres requisitos canónicos añadidos/uno modificado. Se conservan resultado DoD nativo y excepción/aprobación humanas. Restan publicación y revisiones humanas/integración con autorizaciones propias; no son pasos implementados por archivar.
