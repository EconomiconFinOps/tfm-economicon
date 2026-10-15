## 1. Base y contratos
- [x] 1.1 Recuperar B y activar JUP-123 en Trello.
- [x] 1.2 Admitir recibos repetidos y detectar ausencias/duplicados (15 pruebas).
- [ ] 1.3 Reconciliar A/develop y verificar las superficies afectadas.
  - Base comprobada A/28ee5b1c sobre develop/c30a7d0; no afirma una actualización posterior de esas ramas. Bloques incorporados en B; herramientas86PASS, tokenizer4PASS, CD55PASS/2SKIP, CI/topología51PASS. Candidato c7e2d561: 70 archivos, 1470 identidades únicas Linux/SQL PASS mediante procesos separados (OOM anteriores conservados); builds reales y 340 hashes de fuente más tokenizer de ambos contenedores verificados. UI001/003/014 en escritorio/móvil y recarga correcta. Aceptación/reviews de A independientes, no trasladadas a B.
  - Reabierto tras leer review oficial de Víctor18:58UTC sobre28ee5b1c: red/IP por slot del CD y UX con chat desactivado pendientes de corregir en A y reconciliar en B. Las pruebas previas no cubrían esos dos defectos; no se modifica c7 durante N3.
  - Consulta posterior: A avanza11f84334 con esos bloques y27 archivos incrementales; reviews siguen solicitando cambios y CI nueva no verificada. Falta incorporar y probar en B; no cerrar por leer el diff.
  - Completado después en B/ab66f90c:20 archivos idénticos a A y clase de capacidades adaptada conservando el esquema B.34 backend/120 frontend/58 CD Linux/40 topología PASS; tipos/lint/build y ambos loaders conformes. Compose real de ambos slots correcto; creación de redes no ejecutada por pool ajeno172.30.0.0/16. No aceptación de A ni despliegue, ni navegador final de B; esos límites siguen explícitos.
  - Reabierto al congelar la regresión: A8ea5a0c4/develop0543c5ee incorporan JUP-038. Merge local de develop con dos resoluciones y cinco adaptaciones de A;39 archivos de aplicación idénticos, semántica B intacta.550 backend PASS/141 omisiones SQL y1354 frontend PASS; tipos/lint/build conformes. Pendientes Linux/SQL del candidato conjunto antes de cerrar de nuevo1.3.
  - Candidato7be: regresión Linux1747 recogida (1689 PASS/58 SKIP,0 FAIL/ERROR), tres OOM previos conservados y resolución por procesos separados, sin cambiar aserciones. Pgvector20 PASS cubre6 omisiones del chat y añade14 contratos existentes, sin doble suma. Cockroachv4 agotó el plazo al preparar el esquema, sin JUnit; v5 terminó194 PASS/2 FAIL sobre196. Ambos fallos conservados. fba415f2 corrige sólo dos pruebas (metadatos generation y ventana de observación de deadline, con nuevas aserciones HTTP); v8 no ejecutó processor por tokenizer ausente, repuesto con SHA fijo sin versionarlo; v9 repite17 nativas PASS y8 offline (2 PASS/6 SKIP). Equivalencia de helpers/aplicación/build y todos los hashes JUnit/log verificados:1747 chat conformes con58 SKIP cubiertos nativamente,216 ejecuciones SQL/pgvector conformes. Fallos originales conservados, producto7be/pruebasfba explícitos. Buildv7 en curso; navegador/coexistencia física mantienen su alcance pendiente. Sin nuevas inferencias ni aceptación; no cerrar1.3 aún.
- [ ] 1.4 Acordar criterios obligatorios y calidad con revisores.

## 2. Medición
- [x] 2.1 Implementar colector del API, procedencia y reserva de coste.
- [x] 2.2 Verificar entorno aislado y contabilidad viva para la baseline a817382b.
- [x] 2.3 Congelar y recoger baseline N3 completa (84/84, con 7 fallos preservados).
- [ ] 2.4 Resolver incertidumbres con adjudicación independiente.
- [x] 2.5 Recoger N3 del candidato e23e495b:84/84 recibos verificados,78completed/6failed conservados; costes desconocidos con reserva íntegra, no aceptación semántica.
- [x] 2.6 Recoger y revisar localmente N3 de c7e2d561:84/84 recibos,83 completed/1 failed;70 conformes/7 inciertas/6 fallos de contenido/1 técnico. Snapshot258 hashes; no adjudicación independiente ni aceptación.

## 3. Correcciones y entrega
- [ ] 3.1 Corregir defectos medidos con lógica determinista.
  - Correcciones014/003 medidas en c7 N3:014 conforme3/3,003 completa3/3. Las1470 pruebas Linux/SQL conservan su alcance; no validan calidad por sí solas.
  - Persisten regresiones001r2/009r1/010r1/011r3/015r1/r2;021r3 falla por ecuación libre, sin candidato privado exacto. Priorizar cobertura tipada y premisas/modalidad; no relajar validadores ni reconocer sólo preguntas del banco.
  - Compilador de secciones completas integrado localmente:247 pruebas processor y2 backend PASS, cargas en frío propias y replay010r1/r2/r3 con once unidades correctos. Sin medición ni despliegue.015 aún necesita recuperar su sección; otros defectos y variantes pendientes. No cerrar3.1 por este bloque.
  - Recuperación de esa sección implementada en fb7d9ea0 y probada con46 casos Linux/pgvector sobre la misma fuente de producto (tests adicionalesddb64eb5), sin omisiones. Snapshot concurrente, tenant/proveedor y topes comprobados.17 recursos y ambos loaders pasan.015 aún sin medir con modelo; resto de defectos pendiente.
  - Cobertura tipada de011 en654298d4:226 focales processor/24 backend/6 adicionales de fragmentación PASS, replay de sus tres muestras entrega10% por coste y90% por recursos, sin cambiar juicios históricos. Diagnóstico de rechazo con índices y sin contenido privado añadido para021; ese defecto sigue pendiente de resolución, junto a001/009 y dudas004/022. Candidato sin activar ni medir con modelo; no cerrar3.1.
  - Atributos001 y decisión shared009 enb3528bcf:375 focales processor/27 backend PASS. Replay de84recibos selecciona sólo001/009 en sus tres repeticiones; conserva vista actual y pide regla/base sin cita ajena ni reparto inventado. Gramáticas completas con datos variables, no extractor universal. Regresión Linux y aceptación del proveedor se documentan en continuidad;021 y dudas004/022 siguen pendientes.
  - Etapas de ahorro021 en1afa3815:419 focales processor/30 backend PASS, incluido gateway simulado con terminal válido y rechazo de prosa aritmética. Replay de021r1/r2/r3 produce80EUR/mes y40%, sin cambiar el fallo ni reserva históricos. Nueva ruta sin activar/medir;004/022 y aceptación/regresión real siguen pendientes. No cerrar3.1 por el replay.
  - Calificadores004 y consejo022 en2c79b32d:468 focales processor/32 backend PASS; definiciones completas, modalidad literal y premisas en tres valores. Replay de sus seis muestras conforme al contrato nuevo, sin adjudicar las etiquetas históricas. Sin medición real; casillas3.1/3.2 siguen abiertas hasta validar el conjunto y sus variantes.
- [ ] 3.2 Comparar por requisito/repetición y descartar regresiones obligatorias.
  - Comparación c7/e23 registrada:438 pass→pass,7 pass→fail,7 uncertain→uncertain,6 uncertain→pass,2 fail→pass; técnicos aparte. No se cumple ausencia de regresiones; casilla abierta.
- [ ] 3.3 Confirmar N5 según alcance acordado y presupuesto.
- [ ] 3.4 Preparar candidato local con pruebas, evidencias y limitaciones.

## Evidencia de medición — 2026-10-14

Ver [continuidad](../../../docs/continuidad/chat-evaluacion-local.md) para hashes,
recibos originales y derivados, conciliación de todos los intentos y costes.
Las casillas 2.1–2.3 acreditan recogida reproducible, no aceptación semántica.
El candidato corregido todavía requiere verificación de procedencia, nueva
admisión presupuestaria y comparación; no hereda la validación del runtime anterior.
