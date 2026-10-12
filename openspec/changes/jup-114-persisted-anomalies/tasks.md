JUP: JUP-114

## 1. Decisión y modelo de datos

- [x] 1.1 Escribir `docs/adr/ADR-0019-cost-anomaly-episodes.md` (plantilla `docs/templates/adr.md`) con la regla diaria, lo esperado y la referencia anclada, episodio y tolerancia, días evaluables, impacto acumulado y criticidad, monedas, estados y trazabilidad (MTTA y MTTR), la consulta de prueba de JUP-030 sin tocar, alternativas (regla semanal, recalcular desde cero, línea base predictiva), limitaciones y trabajo futuro (puesta al día obligatoria en la etapa 2, conversión de moneda, responsable, permisos por rol, archivado automático, histórico de cambios de estado), y añadirlo al índice de `docs/adr/README.md`.
- [x] 1.2 Migración `apps/backend/app/db/migrations/002_anomaly_episodes.py` con `anomaly_episodes` y `anomaly_detection_state`, la clave primaria determinista, el índice único parcial de episodio en seguimiento y los índices de lectura por tenant; prueba de que se aplica una sola vez sobre una base con `001`.
- [ ] 1.3 Esquemas Pydantic de episodio, respuesta de ejecución, listado y petición de cambio de estado (estados, motivo de 1 a 500 caracteres sin caracteres de control, importes como cadenas de dos decimales).

## 2. Lectura diaria y detección

- [ ] 2.1 Lectura diaria por servicio y moneda en `Database` con las mismas protecciones que billing v2 (ingestas completadas, tenant en las dos tablas, `AmbiguousCostSource`) y la lista de días observados del tenant; pruebas con CockroachDB real, incluida la de fuente solapada y la de otro tenant con los mismos servicios.
- [ ] 2.2 Servicio de detección puro (sin base de datos): días evaluables y último día completo, lo esperado (media de 7 días o referencia anclada), regla estricta con `Decimal`, apertura, continuación con tolerancia de 3 días, `no_longer_observed`, enlace al episodio anterior, impacto acumulado, criticidad y monedas no soportadas. Una prueba por escenario de la spec `cost-anomaly-episodes`, incluidas las cuatro preguntas de JUP-069 (016 a 019) como casos de regla.
- [ ] 2.3 Ejecución transaccional por tenant con la marca de agua: ventana de como máximo 7 días, `up_to_date`, rango no evaluado, 409 por fuente ambigua y por conflicto sin escrituras parciales; pruebas con CockroachDB real de pulsación repetida y de dos ejecuciones simultáneas.
- [ ] 2.4 Mutantes sobre las condiciones clave (`>` frente a `>=`, `AND` frente a `OR`, tolerancia, referencia anclada frente a media, último día completo, tramos de criticidad, filtro por tenant en SQL) y registrar cuántos sobreviven y por qué.

## 3. API y estados

- [ ] 3.1 Rutas `POST /billing/anomalies/detect`, `GET /billing/anomalies/episodes`, `GET /billing/anomalies/episodes/{id}` y `PATCH /billing/anomalies/episodes/{id}` con el tenant activo, orden del listado, `scope=open|all` y listado sin detección.
- [ ] 3.2 Cambio de estado con transiciones permitidas, motivo obligatorio al cerrar, quién y cuándo, primer cambio desde `new`, cierre, 409 para cerrado o transición inválida y actualización condicionada al estado esperado; prueba de dos cambios simultáneos con CockroachDB real.
- [ ] 3.3 Aislamiento: mismo 404 para id ajeno e inexistente en lectura y cambio de estado, denegación a no miembros antes de leer, y sin identificadores ajenos ni importes en los logs.
- [ ] 3.4 Prueba del límite exacto del 20 %: la consulta de prueba de JUP-030 lo marca como candidato y la regla de negocio no abre episodio; comprobar que las pruebas existentes de JUP-030 siguen en verde sin cambios.

## 4. Documentación y contratos

- [ ] 4.1 `docs/api/anomaly-episodes.md` con peticiones, respuestas, códigos de error, ejemplo reproducible, limitaciones y uso por JUP-038; actualizar `docs/api/cost-anomalies.md` (consulta de prueba sin guardar, `>=` frente a `>`, los episodios son la fuente de JUP-038) y `docs/architecture/finops-agent-tools.md` (lo esperado, criticidad por impacto acumulado, fuente persistida).
- [ ] 4.2 Registrar en `openspec/findings/backlog.md` los hallazgos de trabajo futuro: actualizar el corpus del asistente y regenerar las huellas de JUP-022, JUP-069 y JUP-070 con JUP-038; conversión o tabla de umbrales por moneda; línea base predictiva; responsable y permisos por rol; archivado automático; puesta al día completa en la etapa 2.
- [ ] 4.3 Nota de continuidad en `docs/continuidad/deteccion-anomalias-coste.md` y su fila en `docs/continuidad/README.md`.
- [ ] 4.4 Revisión documental completa limitada a la funcionalidad de anomalías, hecha al terminar 4.1 a 4.3: buscar en todo el repositorio cada mención de anomalías, la regla, la criticidad, los estados y los endpoints (specs `cost-anomaly-detection`, `cost-anomaly-episodes`, `anomalies-panel`, `finops-agent-tool-contract` y `synthetic-anomaly-data`; `docs/api/`, `docs/architecture/`, `docs/adr/`, `docs/continuidad/`, `docs/demo/JUP-107/`, `docs/evidence/`, READMEs, el corpus del asistente, los conjuntos de evaluación, `openspec/findings/backlog.md` y los textos del panel del frontend) y comprobar que cada cosa está donde debe, que nada describe un comportamiento distinto del implementado (drift), que no hay afirmaciones contradictorias entre documentos, que los enlaces y rutas funcionan y que nada se presenta como hecho sin estarlo. Corregir lo que sea de este change; lo que no se pueda tocar aquí (corpus y conjuntos fijados por huella, panel del change 2) se registra como hallazgo. Dejar en `review.md` la lista de ficheros revisados, lo corregido y lo registrado.

## 5. Cierre y verificación

- [ ] 5.1 Batería completa: pruebas del backend, pruebas con CockroachDB real en local (nodo desechable, `JUP086_COCKROACH_TEST_URL`), `openspec:validate`, `jup:check:all`, `jup:cleanup:check`, `corepack pnpm lint` y `git diff --check`. Registrar comandos y resultados.
- [ ] 5.2 Comprobación contra el stack real aislado (`docker compose -p jup114`, volúmenes nuevos): cargar el conjunto de JUP-107, ejecutar la detección, listar, cambiar estados, repetir la pulsación y comprobar el aislamiento con `tenant-growth`; parar el stack y borrar los volúmenes.
- [ ] 5.3 Revisión adversarial (agente `adversarial-reviewer`) hasta `accept` o aceptación explícita de Lucia, y `review.md` con la sección `## Adversarial Review`, el barrido de patrones, los riesgos y los hallazgos registrados.
- [ ] 5.4 Sección de evidencia en `docs/evidence/JUP-114-validation.md` y bloque `## Human Approval` post-review de Lucia, con la respuesta sobre la criticidad por impacto acumulado reflejada o anotada como pendiente.
- [ ] 5.5 Archivar el change en la misma rama, revisar la documentación posterior al archivo, poner la rama al día con `develop` y abrir el PR a `develop` con el bloque de excepción temporal.
