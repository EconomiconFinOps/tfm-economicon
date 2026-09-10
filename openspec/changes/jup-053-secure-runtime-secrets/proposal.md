JUP: JUP-053
Trello: https://trello.com/c/2UCJTDhi/41-jup-053-gestionar-secretos-y-credenciales-de-forma-segura

## Why

JWT, conexiones y seed demo contienen defaults inseguros; errores y contextos
Docker pueden exponer credenciales. El objetivo es configuracion externa,
arranque verificable y diagnosticos sin secretos, antes de JUP-085 y JUP-023.

Fuentes: seccion JUP-053 del `plan.txt` aprobado de 2026-09-07 y tarjeta oficial
del export `CawMVPoy - economicon (09-09).json`, leido el 2026-09-09. No se pudo
consultar Trello en vivo. La tarjeta privada fue contrastada en preparacion;
no sustituye a Trello oficial ni acredita aprobacion de este diseno.

## What Changes

- Inventariar JWT, OpenRouter/LiteLLM, DB, RabbitMQ y demo; exigir configuracion
  externa para secretos reales y conservar fixtures explicitas de prueba.
- Reutilizar Pydantic Settings, SecretStr y structlog para validar antes de
  conectar, ocultar errores sensibles y documentar configuracion y rotacion.
- Eliminar password demo del formulario y el sobrescrito automatico del seed;
  conservar cuenta, email, roles y contratos HTTP actuales, sin migraciones.
- Completar `.env.example`, exclusiones de Git/Docker y pruebas con sentinelas
  sinteticas. La revision no promete detectar cualquier secreto arbitrario.
- Externalizar la password admin de Grafana mediante un `.env` local no
  versionado, conservando su valor y la autenticacion. La inclusion de Grafana
  esta aprobada; no eliminar ni rotar automaticamente la password existente.

## Capabilities

### New Capabilities

- `secure-runtime-secrets`: configuracion, rechazo de defaults, diagnosticos,
  empaquetado y operacion verificables con limites explicitos.

### Modified Capabilities

- `demo-auth-credentials`: mantiene el email coherente; la password se introduce
  manualmente y el seed no invalida una rotacion del usuario existente.

## Impact

Las superficies exactas propuestas figuran en `design.md`. Se conservan las
dependencias y frameworks actuales. No incluye session/login de JUP-085,
autorizacion tenant de JUP-086, despliegue de proveedores/JUP-023, secret manager,
TLS/provisioning, migraciones, rediseno de CI ni renovacion del frontend.
Las fixtures Azure simuladas no son credenciales de Azure; no se cambia su API.

Se acepta [ADR-0006](../../../docs/adr/ADR-0006-runtime-secret-boundaries.md)
para los limites duraderos de secretos y la excepcion local, en estado Accepted,
con aprobacion completa registrada abajo. Introducir secret manager o TLS requiere nueva aprobacion
de alcance y decision arquitectonica. ADR-0002/JUP-078 permanece intacto.

## Prepublication Reconciliation (2026-09-10)

El fetch comunicado situa origin/develop en cb27009, tres commits despues de
la base local 7d76fc3; al redactar esta nota no se ha realizado merge.
Se explicita RABBITMQ_ERLANG_COOKIE dentro del alcance ya aprobado de secretos
RabbitMQ/Compose: entrada externa requerida, sin fallback publicado ni rotacion.
La reconciliacion conserva tracing JUP-044, sus cinco tests y archivos/findings
importados. RF-044-002/JUP-096 no se da por corregido; RF-053-004 se deriva a
JUP-020 sin resolverlo aqui. No cambian los 17 escenarios globales, arquitectura,
dependencias o migraciones. Las aprobaciones y estados historicos de abajo se
conservan; esta nota no acredita el cierre ni el resultado de QA integrado.

## Pre-code Approval: APPROVED

- Aprobacion parcial: Paris Arcos, registrada el 2026-09-09 a las 14:12 UTC.
  Acepta CockroachDB local y Grafana, indicando conservar la password en `.env`.
- Grafana: APPROVED con esa condicion. Compose leera `GRAFANA_ADMIN_PASSWORD`
  de un `.env` local excluido de Git y de contextos Docker; `.env.example`
  mantendra el campo vacio. Conservar la password existente: no eliminarla,
  regenerarla, rotarla ni deshabilitar autenticacion. Quitar solo el fallback
  del archivo versionado. No hacer hardening general ni cambiar dashboards.
  Mover una password debil a `.env` no la fortalece; no afirmar lo contrario.
- CockroachDB: APPROVED. Permitir `--insecure` solo para demo
  local desechable o test aislado, mediante opt-in explicito y comprobable.
  Nunca en entornos compartidos/produccion. Loopback por si solo no acredita
  aislamiento. Esta aprobacion no activa el opt-in ni autoriza operaciones
  sobre un entorno compartido o productivo.
- Demo: APPROVED. Password externa, formulario sin password precargada,
  creacion solo por opt-in y rotacion explicita de cuentas existentes.
  Incluye rechazar el arranque al detectar la password demo insegura conocida,
  indicando rotacion explicita sin cambiarla automaticamente.
- Aprobacion completa: Paris Arcos; registrada el 2026-09-09 a las 14:24 UTC.
  Decision: "correcto aprobado", tras explicar el cambio demo y solicitar
  autorizacion para comenzar pruebas. Se conservan las condiciones anteriores
  de CockroachDB y Grafana. Los 17 escenarios y el diseno quedan aprobados.
  OpenSpec y trazabilidad superados antes de la aprobacion; revalidar despues
  de registrar este estado. Autorizadas pruebas e implementacion del alcance,
  no PR, tracker, commit/push, merge, archivo ni operaciones compartidas.

## Post-QA Approval: PENDING

En el gate previo de las 14:24 UTC todavia no habia resultados de pruebas
ni escaneo. Posteriormente se ejecutaron Green3, mutation y QA; consultar
[review.md](review.md) y [evidencia](../../../docs/evidence/JUP-053-validation.md).
QA confirma los controles acotados, pero la aceptacion completa permanece
NEEDS_HUMAN por RF-053-004. No hay aprobacion final ni CI remoto.
