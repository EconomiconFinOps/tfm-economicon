## 1. Codigo vecino y barrido previo

- [x] 1.1 Barrer los usos de `jobs` y de `Database.initialize()` en `apps/processor` (codigo, tests, scripts) y en `docker-compose.yml`; listar lo que asume que el processor crea `jobs`.
- [x] 1.2 Revisar las migraciones del backend y del processor y confirmar que `jobs` es el unico objeto de esquema creado por ambos servicios, y que las tablas del processor no las toca el backend.

## 2. Fase RED

- [x] 2.1 Añadir una prueba de integracion opt-in (CockroachDB real desechable) que aplique a la vez, sobre una base vacia, las migraciones reales del backend y del processor en procesos separados, al menos 5 veces y con desfase 0 s y 0,5 s; verificar que falla en `develop` con `SerializationFailure` en al menos una ejecucion.
- [x] 2.2 Añadir pruebas de propiedad del esquema: tras migrar solo el processor sobre una base vacia no existe ninguna tabla del backend (incluida `jobs`), y tras migrar solo el backend no existe ninguna tabla del processor; verificar que la del processor falla en `develop`.
- [x] 2.3 Añadir pruebas de compatibilidad con bases existentes: base migrada por ambos servicios con filas en `jobs` (sin cambios ni versiones nuevas) y base migrada solo por el processor antiguo con filas en `jobs` seguida del backend (sin error, filas conservadas).

## 3. Implementacion

- [x] 3.1 Dejar la migracion `001` del processor sin operaciones de esquema, conservando fichero y version, con un comentario que remita a la propiedad del backend.
- [x] 3.2 Añadir en `docker-compose.yml` la dependencia del processor sobre `backend` con `condition: service_healthy`.
- [x] 3.3 Adaptar los tests del processor que asumian que su migracion crea `jobs` (al menos `_assert_schema` en `tests/test_azure_cost_cockroach_integration.py`), creando el esquema del backend cuando lo necesiten.
- [x] 3.4 Ejecutar las pruebas del grupo 2 y confirmar que pasan.
- [x] 3.5 Hacer que `/health` del processor responda 200 `degraded` con `jobs` nulo solo cuando falta `jobs`, sin ocultar otros errores (revision adversarial ADV-1, ADV-6, ADV-12, ADV-13).
- [x] 3.6 Añadir una guarda estatica que se ejecute en CI sin base de datos y compruebe que cada servicio solo toca sus tablas en sus migraciones (ADV-2, ADV-7, ADV-11, ADV-16, ADV-17); es heuristica, la prueba completa es la opt-in con CockroachDB real.
- [x] 3.7 Exigir la tabla de versiones explicita en el `MigrationRunner` del processor (ADV-10).

## 4. Verificacion con Docker real

- [x] 4.1 Arranque en frio del stack completo en un proyecto Compose aislado con volumenes nuevos, al menos 3 veces: backend y processor sanos, el processor creado despues de que el backend este sano, sin `SerializationFailure` en los logs.
- [x] 4.2 Camino de error: con el backend sin llegar a estar sano, Compose no arranca el processor e informa de la dependencia no cumplida.
- [x] 4.3 Control positivo: con la migracion `001` original del processor, la prueba de 2.1 vuelve a fallar.

## 5. Findings

- [x] 5.1 Actualizar RF-044-002 en `openspec/findings/backlog.md` a `Fixed` con referencia a JUP-096 y la evidencia.
- [x] 5.2 Registrar RF-096-001 (RabbitMQ `eacces` al leer `.erlang.cookie` en un arranque en frio, una vez de seis, arranca al reintentar) como `Open`, fuera de alcance, candidato para JUP-050.
- [x] 5.3 Registrar RF-096-002 (lectura de pgvector por el backend, riesgo aceptado por Lucia), RF-096-003 (migracion concurrente dentro del processor) y RF-096-004 (CI no ejecuta los tests con base de datos real).

## 6. Cierre y verificacion

- [x] 6.1 Bateria completa: tests de backend y processor, `corepack pnpm openspec:validate`, `corepack pnpm jup:check -- --change jup-096-coordinate-migrations` y `corepack pnpm jup:cleanup:check`; registrar comandos y resultados.
- [x] 6.2 Revision adversarial con el agente `adversarial-reviewer` hasta `accept`; corregir o probar cada finding.
- [x] 6.3 Redactar `review.md` (resumen, decisiones, validacion, `## Adversarial Review`, barrido del patron, riesgos, findings y aplicabilidad de ADR) y `docs/evidence/JUP-096-validation.md`.
- [x] 6.4 Añadir `## Human Approval` al final de `review.md` tras la aprobacion explicita de Lucia.
- [x] 6.5 Archivar el change en la misma rama tras 6.4.
- [ ] 6.6 Abrir el PR hacia `develop`.
