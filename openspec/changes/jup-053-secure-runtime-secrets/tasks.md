## 1. Gate previo

- [x] 1.1 Registrar aprobacion humana completa de Grafana, excepcion CockroachDB, cambio demo y ADR-0006, conservando sus limites y condiciones.
- [x] 1.2 Validar OpenSpec estricto, trazabilidad JUP-053 y limites del diff; registrar aprobacion humana antes de pruebas o codigo de implementacion.

## 2. Tester: Red

- [x] 2.1 Crear pruebas de configuracion ausente/presente/default, fixtures explicitas y matriz de entorno/opt-in; conservar las pruebas condicionales de IA existentes.
- [x] 2.2 Cubrir import sin configuracion y cada entrypoint: fallo seguro antes de conexiones, threads o servidor; aislar entorno/cache sin leer .env real.
- [x] 2.3 Cubrir logs, stderr, HTTP 422/500 y fallo persistido con sentinelas, excepciones encadenadas y campos anidados; conservar correlacion y metadata util.
- [x] 2.4 Cubrir seed nuevo/existente, password heredada, reinicio tras rotacion, formulario sin prefill y exclusiones de contextos Docker; demostrar Red por comportamiento ausente, no por import/setup roto.

## 3. Coder: Green

- [x] 3.1 Implementar Settings/loader y construccion tardia de recursos sobre las superficies aprobadas; adaptar consumidores SecretStr sin cambiar contratos JWT/tenant.
- [x] 3.2 Implementar redaccion final y diagnosticos HTTP/worker/CLI seguros sin persistir excepciones crudas ni perder el formato JSON existente.
- [x] 3.3 Aplicar seed opt-in sin sobrescrito y password manual; actualizar documentacion de rotacion de cuenta existente sin migraciones.
- [x] 3.4 Tras el gate completo, externalizar secretos de Compose y completar ejemplos/exclusiones Git-Docker; trasladar la password Grafana existente a .env ignorado sin eliminarla, generarla, rotarla ni resetear cuenta/volumen, conservando autenticacion; mantener el opt-in local aprobado desactivado por defecto.
- [x] 3.5 Documentar arranque local/nativo/test, procedencia y rotacion de cada credencial; ejecutar pruebas focales y regresiones de las superficies tocadas hasta Green.

## 4. Tester: Mutation

- [x] 4.1 Preparar copias aisladas desechables fuera del repositorio del producto; aplicar alli, una a una y sin dependencias nuevas, mutaciones que acepten placeholder JWT, permitan bypass fuera de local, omitan saneado final o sobrescriban hash existente. El tester nunca modifica producto en el worktree activo, ni temporalmente.
- [x] 4.2 Ejecutar pytest focal por mutante en cada copia; registrar mutacion/test/resultado, comprobar identidad con la fuente antes de mutar y verificar mediante hashes que la fuente permanece intacta al terminar. Escalar supervivientes; si la ejecucion compatible no cumple el contrato de roles, detener y solicitar aprobacion explicita de mutation-exception, sin exencion silenciosa ni nuevas dependencias.

## 5. Reviewer, evidencia y QA

- [x] 5.1 Revisar alcance, decisiones pendientes, compatibilidad demo, rutas de fuga y preservacion de validadores; resolver hallazgos bloqueantes y consolidar review/evidencia con resultados observados.
- [x] 5.2 QA contrasta los 17 escenarios, repite checks afectados, verifica scan acotado y arranque aislado; registra limitaciones y los siete checks de CI sin atribuir exito a comandos no ejecutados.
- [x] 5.3 Presentar aprobacion humana post-QA. PR, tracker, commit/push, merge y archivo requieren su autorizacion correspondiente y no forman parte de esta planificacion.

Estado historico tras review 2 (2026-09-09): 552 pruebas distintas aprobadas,
192 nuevas; 11 mutantes dirigidos detectados. RF-053-001/002/003 Fixed.
Actualizacion 2026-09-10: Paris Arcos acordo corregir RF-053-004 en JUP-020
y referenciar el finding en su tarjeta privada; no se inicia esa JUP.
Referencia añadida y verificada en JUP-020 privada; replica al TFM pendiente.
Posteriormente solicita cierre acotado y PR. Integracion cb040366 sobre
develop cb27009: revision PASS, 454 casos reejecutados mas 104 reutilizados,
558 distintos y 193 nuevos de JUP-053; cinco pruebas importadas de JUP-044.
Dos mutantes dirigidos detectados y diez comprobaciones de RabbitMQ PASS.
5.2/5.3 completadas: QA_PASS_WITH_APPROVED_EXCEPTIONS y autorizacion de Paris
para cierre acotado y PR registradas. CI remoto pendiente de la publicacion;
no se confunde este cierre tecnico con pairing/revision/validacion del equipo.
El smoke integral historico sigue FAIL; no hay cierre operativo ni merge.
Detalles en
[review.md](review.md) y [evidencia](../../../docs/evidence/JUP-053-validation.md).

## 6. Reconciliacion previa a publicacion (2026-09-10)

- [x] 6.1 Tester: cubrir cookie externo ausente/vacio/presente con valores sinteticos y fixture request_id dentro del job; conservar los cinco tests de tracing upstream sin depender del contexto ambiente.
- [x] 6.2 Coder: reconciliar cb27009 conservando tracing, archivos y findings importados; exigir RABBITMQ_ERLANG_COOKIE externo sin fallback, con ejemplo vacio y procedimiento del operador que preserve el valor existente sin imprimirlo. No generar, resetear ni rotar cookies, tocar .env/volumenes reales o cambiar la password Grafana.
- [x] 6.3 Revisar y revalidar el resultado integrado antes de sintetizar cierre/QA; mantener RF-053-004 en JUP-020 y RF-044-002 en JUP-096 sin declararlos corregidos. Escalar cambios de cookie, clustering/persistencia o nuevas excepciones; no ampliar criterios de aceptacion.
