## 1. Protocolo
- [x] 1.1 Reproducir fallos observables en baseline con SSE controlado.
- [x] 1.2 Implementar decision auto y finalizacion none, cero/una busqueda.
- [x] 1.3 Coordinar contexto, endpoint, operaciones, prompt y hashes.
- [x] 1.4 Ejecutar suites afectadas y controles; registrar fallos de base, omisiones y correcciones de fixtures.

## 2. Evidencia y entrega
- [x] 2.1 Entregar parche separado y evidencia con SHA exacto.
- [ ] 2.2 Verificar matriz real con presupuesto vigente autorizado.
- [ ] 2.3 Repetir bateria JUP-069 completa sobre un SHA final y recorrido real.
- [x] 2.4 Realizar revisión técnica propia y validación asistida focal por autorización explícita del usuario (12/10); sin atribuir dictámenes a terceros ni aceptación del proveedor.

## 3. Corrección de la suite backend
- [x] 3.1 Reproducir y corregir ambas carreras entre estado SQL y evento final en RAM.
- [x] 3.2 Corregir fixtures de JWT caducados en colección y respuesta HTTP pgvector.
- [x] 3.3 Provisionar datos SQL sintéticos propios para los tres probes de summary y conservar sus aserciones.
- [x] 3.4 Ejecutar la suite backend completa en contenedores aislados: 1671 PASS/47 SKIP, cero fallos/errores, exit 0 sobre 8294c48; evidencia y omisiones documentadas.
