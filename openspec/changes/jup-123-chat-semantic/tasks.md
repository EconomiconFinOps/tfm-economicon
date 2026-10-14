## 1. Base y contratos
- [x] 1.1 Recuperar B y activar JUP-123 en Trello.
- [x] 1.2 Admitir recibos repetidos y detectar ausencias/duplicados (15 pruebas).
- [ ] 1.3 Reconciliar A/develop y verificar las superficies afectadas.
  - Base comprobada A/28ee5b1c sobre develop/c30a7d0; no afirma una actualización posterior de esas ramas. Bloques incorporados en B; herramientas86PASS, tokenizer4PASS, CD55PASS/2SKIP, CI/topología51PASS. Candidato c7e2d561: 70 archivos, 1470 identidades únicas Linux/SQL PASS mediante procesos separados (OOM anteriores conservados); builds reales y 340 hashes de fuente más tokenizer de ambos contenedores verificados. UI001/003/014 en escritorio/móvil y recarga correcta. Aceptación/reviews de A independientes, no trasladadas a B.
  - Reabierto tras leer review oficial de Víctor18:58UTC sobre28ee5b1c: red/IP por slot del CD y UX con chat desactivado pendientes de corregir en A y reconciliar en B. Las pruebas previas no cubrían esos dos defectos; no se modifica c7 durante N3.
- [ ] 1.4 Acordar criterios obligatorios y calidad con revisores.

## 2. Medición
- [x] 2.1 Implementar colector del API, procedencia y reserva de coste.
- [x] 2.2 Verificar entorno aislado y contabilidad viva para la baseline a817382b.
- [x] 2.3 Congelar y recoger baseline N3 completa (84/84, con 7 fallos preservados).
- [ ] 2.4 Resolver incertidumbres con adjudicación independiente.
- [x] 2.5 Recoger N3 del candidato e23e495b:84/84 recibos verificados,78completed/6failed conservados; costes desconocidos con reserva íntegra, no aceptación semántica.

## 3. Correcciones y entrega
- [ ] 3.1 Corregir defectos medidos con lógica determinista.
  - Correcciones 014/003 y contratos de soporte/autoridad guardados en c7e2d561; pasan offline y SQL. Falta medirlos con proveedor real y contrastar las regresiones, sin cambiar etiquetas históricas.
  - Primera ronda c7 revisada:22conformes/3inciertas/3fallidas. Regresionesr1 frentee23:009cita ajena,010omisión de minúsculas,015omisión de investigar. Aún no decidir por una repetición ni aceptar por media; campañaN3 continúa con el mismo producto.
- [ ] 3.2 Comparar por requisito/repetición y descartar regresiones obligatorias.
- [ ] 3.3 Confirmar N5 según alcance acordado y presupuesto.
- [ ] 3.4 Preparar candidato local con pruebas, evidencias y limitaciones.

## Evidencia de medición — 2026-10-14

Ver [continuidad](../../../docs/continuidad/chat-evaluacion-local.md) para hashes,
recibos originales y derivados, conciliación de todos los intentos y costes.
Las casillas 2.1–2.3 acreditan recogida reproducible, no aceptación semántica.
El candidato corregido todavía requiere verificación de procedencia, nueva
admisión presupuestaria y comparación; no hereda la validación del runtime anterior.
