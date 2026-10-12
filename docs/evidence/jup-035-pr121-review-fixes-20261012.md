# PR121 — correcciones de revisión, 12/10/2026

Implementación asistida de Alejandro en su PR propia; no review de Víctor ni
validación atribuida a Lucía. Encargo: corregir los pendientes de PR121 mediante
un subagente. Fuente: [review de Víctor](https://github.com/EconomiconFinOps/tfm-economicon/pull/121#pullrequestreview-5494349151).

Código funcional `551fb81`; actualización con develop `3c6517b` en `1d082fb`;
pruebas/documentación adicionales `85e1dc9`. El árbol de producto de `1d082fb`
y `85e1dc9` es idéntico. No se fusiona la PR ni se publican mensajes a Discord.

**Entrega parcial, aceptación global NO PASS.** Los cinco puntos de ingeniería
de la review tienen correcciones y evidencia; la multiplicidad y la calidad de
contenido siguen impidiendo la integración. La campaña completa no confirma
la estabilidad del éxito observado en los cuatro focales.

## Matriz de correcciones

| Pendiente | Causa y cambio | Comprobación | Estado |
| --- | --- | --- | --- |
| Stream inicial waiting/paused | SQL podía confirmar antes de publicar RAM; ahora se entrega el estado confirmado antes del cierre. | 24 combinaciones de cuatro estados, tres órdenes SQL/RAM y dos entregas; SQLite y Cockroach reales. | Corregido en código. |
| Observador con lectura active anterior al cierre publicado | El observador no recibía el cierre previo a su cola. Captura atómica del último evento al suscribirse. | Las seis regresiones que fallan sobre3719f8c pasan con el parche; sin cierres duplicados ni pérdida del par. | Corregido en código. |
| Decisión truncada | length caía en422 invalid_response. Se devuelve502 incomplete sin emitir/reutilizar texto de decisión ni nueva generación dentro del intento. | Registro exacto, diagnóstico sin contenido y transición backend waiting/retry_scheduled sin par. Regresión falla en baseline. | Corregido. |
| Emoji mojibake | Fixture perdió U+1F600. Restaurado carácter y prueba adicional con UTF-8 real partido byte a byte. | Comprueba bytes f09f9880, answer y deltas; mutación al fixture anterior detectada. | Corregido. |
| Conflicto develop | Conflicto real en índice de continuidad. Fusionada base3c6517b, conservada fila JUP113. Historia extensa movida a tema enlazado. | GitHubMERGEABLE; workflow pull_request vuelve a ejecutarse y JUP policySUCCESS. | Corregido; reviews siguen pendientes. |
| CD/HMAC | init/prepare no suministraban CHAT_HMAC_FILE. Se crea una clave estable, reutilizada entre releases, fuera de source/build. | init/prepare reales, docker compose config, ambos secrets, lectura UID10001 y montaje ro. Directorio0700/archivo0444; suiteCDLinux55PASS. | Corregido en herramienta; sin desplegar CD compartido. |
| 010/011 | Omisión de reglas y adición de reglas sin fuente. Bundle diferencia completitud solicitada, convención interna y fragmento que respalda cada regla. | Focales reales conformes; full28 confirma010, pero011 omite distinguir90% por recursos. | Parcial; no garantía semántica universal. |
| 021 | Se mezclaban diferencias/denominadores. Bundle exige operandos, unidades y coherencia entre todos los campos. | Focal y full28:70EUR/mes y40%, sin93.33. Full28 añade citas no pertinentes. | Aritmética observada coherente; citas pendientes. |
| 018 | Citas accesorias no pertinentes. Se conservan selección exacta y reglas de pertinencia. | Focal cita sólo fragmento7; full28 vuelve a añadir fragmento6 ajeno al umbral. | No resuelto de forma estable. |
| Llamadas múltiples | El proveedor nativo puede devolver varios IDs; no hay control compatible demostrado en este endpoint. | Rechazo de varias llamadas completas/fragmentadas antes de ejecutar búsquedas; no truncamiento ni retries ocultos. | Pendiente de decisión de protocolo/proveedor. |

## Pruebas

- Backend metadata/operaciones:68PASS. Primer pase66PASS/1FAIL por un sleep de
 30ms en el fixture de Stop; sincronizado con reserva SQL/claim observable,
 conservando las aserciones. No se presenta ese primer pase como verde.
- Processor auto/gateway/recursos:87PASS antes de la prueba UTF-8 adicional;
 auto final29PASS. Se solapan: no sumar ambos totales.
- Cockroach24.1.11:43PASS, cero omisiones, incluidos24 cruces nuevos y los19
 probes anteriores de transacciones/summary. Base sintética nueva retenida.
- CDLinux:55PASS, cero omisiones. Un primer pase mixto Windows processor/CD
 dio118PASS/2SKIP; no se suma a los anteriores.
- Frontend streaming/recuperación/solicitudes/captura:42PASS.
- Gobernanza/CD workflow:85PASS. Primer intento sandboxEPERM conservado;
 OpenSpec estricto67/67PASS.
- Build real backend/processorPASS;75/69 archivos Python verificados SHA256
 contra source congelada. No se usan mounts de código sobre las imágenes.
- Pruebas contra3719f8c: stream6FAIL/18PASS; truncación1FAIL; Unicode1FAIL;
 CD1FAIL. Los archivos nuevos se restauraron en finally antes de continuar.

Comandos: CPython3.12 con PYTHONPATH del servicio, pytest -B -q -p
no:cacheprovider; Cockroach con JUP035_REQUIRE_NATIVE_SQL=true. CD:
`python -B -m unittest discover -s tools/cd -p 'test_*.py' -v`.
OpenSpec: `node node_modules/@fission-ai/openspec/bin/openspec.js validate --all --strict --no-interactive`.
Los recibos operativos y scripts reproducibles se conservan fuera del repositorio
en `materiales/07-evidencias/PR121-herramientas-evidencia-20261012/pending-*`.
Las respuestas sintéticas y evaluaciones finales están versionadas junto a este informe.

## Aceptación real focal

Runtime aislado `/tmp/economicon-pr121-20261012`, imágenes `:pending`.
OpenRouter GLM5.2, deepinfra/fp4, sin fallback ni cambio de límites. Cuatro
escenarios sintéticos010/011/018/021 completados, un intento, final y un par
persistido por caso. Respuestas y citas completas en el recibo versionado.
La comprobación usa el contenido completo de los chunks, no sólo los140
caracteres del excerpt. En011, finops:chunk10 respalda ponderación por coste
y rules:chunk5 la fórmula; en021, rules:chunk5 define Savings Realization.
No confundir una referencia permitida por el esquema con sustento semántico.

## Campaña completa final y gasto

**28/28 ejecutados: 21 completed / 7 failed**, un intento por caso. Los fallos
005,006,007,012,016,022 y027 son `native_multiple_calls`, sin búsqueda parcial
ni mensajes persistidos. Los21 completados emiten exactamente un final y
persisten un único par user/assistant. No HTTP400. Banco sin modificaciones,
SHA256 `0bd8a31792d68ff82c2bb222d42593f139d9596e2d24ad37f77c08d648a9f2e7`.

Defectos observados entre los completados, conservados sin repetir para elegir
una muestra favorable:

- **011:**10% por coste correcto, pero falta distinguir explícitamente90% por
 número de recursos. Las citas sí respaldan las afirmaciones presentes.
- **017:** afirma que100EUR/día cumple `>100` y activa la regla; debe excluir
 la igualdad. Es un fallo de contenido observado en esta muestra, sin atribuir
 causalidad estadística al cambio de prompt.
- **018:** mantiene el cálculo correcto, pero incluye rules:chunk6 sobre
 budget/forecast, sin sustento específico para el umbral de anomalía respondido.
- **021:** desaparece la contradicción70/93.33, pero cita finops:chunk15 sobre
 recomendaciones y finops:chunk5 sobre conceptos/budget; no respaldan la
 definición de realization respondida. El cálculo del usuario no exige esas citas.
- **024:** mantiene monedas separadas y solicita destino/tipo/fecha, pero añade
 tasas ficticias0.90EUR/USD y1.10USD/EUR, contrarias al forbidden del banco.

El saludo posterior completa en un intento, sin fuentes y con un par persistido;
su status es `unsupported`. Se registra el resultado exacto, sin presentarlo
como validación de UX ni de clasificación semántica del saludo.

Resultados completos, contraste manual por caso, expected del banco, fragmentos
citados y contadores: [recibo JSON](jup-035-pr121-review-fixes-20261012.json).
Incremento observado en claves de esta tanda: **0.0760432175USD**. Acumulado
autorizado desde baseline: **0.1895518525USD de0.50USD**. El contador compartido
OpenRouter aumentó0.080593807USD; no se atribuye exclusivamente a esta tanda.
No se renovaron claves ni aumentaron límites/RPM/TPM/concurrencia. Caducidad
existente19:28:33UTC. Runtime detenido con exit0; volúmenes, corpus, base SQL
de pruebas y recibos retenidos. No se activó el CD compartido.

CI sobre85e1dc9: seis checks técnicos verdes en push y pull_request; JUP policy
del evento pull_requestSUCCESS. [Ejecución PR](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38295392821).
JUP reviewsFAIL porque siguen faltando las reviews requeridas y persiste el
CHANGES_REQUESTED de Víctor; este trabajo no lo levanta ni lo omite.

## Decisión necesaria sobre multiplicidad

Recomendación: **decisión estructurada explícita**, si el producto permite
sustituir el protocolo nativo. Primera generación sin herramientas con objeto
estricto `{action: none|search, query: string|null}` y validación local de ambas
ramas. El backend admitiría una única solicitud documental autenticada; la
finalización recibiría su contexto como datos no confiables. Debe versionarse
el contrato privado/descriptor/manifiesto/OpenSpec, sin fabricar IDs ni mensajes
tool nativos. Conserva dos generaciones, una búsqueda ejecutada, HMAC, tenant,
deadline y firewall. Requiere pruebas del esquema real, cancelación, presupuesto
y aceptación completa. No implementado sin decisión explícita.

Alternativa: endpoint/ruta específica de chat que admita control real de
cardinalidad (`parallel_tool_calls=false` u otro equivalente documentado),
manteniendo el protocolo nativo. Requiere autorización del destino, comparación
de coste/calidad y nueva campaña; no se propone cambiar el proveedor global.
El endpoint actual no anuncia ese parámetro y el ensayo previo devolvió404.

Ambas opciones tienen coste de implementación y requieren gasto de aceptación;
la primera conserva el número máximo actual de generaciones, pero no se promete
idéntico precio por tokens. Mantener el rechazo actual es seguro, pero conserva
fallos funcionales. No escoger una llamada arbitraria, concatenar consultas o
asignar resultados inventados para hacer pasar el banco.

## Límites de la entrega

No hay una calculadora determinista ni un verificador semántico universal. Los
prompts son mitigaciones y la nueva batería conserva todos sus fallos. Las
reviews humanas pendientes no se sustituyen por estas pruebas. El recorrido
en navegador de esta revisión no está acreditado: la sesión CUA del subagente
no tiene la pestaña autenticada anterior y localhost28660 rechazó conexión.
Las pruebas HTTP/SQL y frontend no se presentan como un ensayo de navegador.
