# ADR-0006: Runtime secret boundaries

- Status: Accepted
- Date: 2026-09-09
- Related JUP/OpenSpec: JUP-053, [jup-053-secure-runtime-secrets](../../openspec/changes/jup-053-secure-runtime-secrets/proposal.md)
- Trello: https://trello.com/c/2UCJTDhi/41-jup-053-gestionar-secretos-y-credenciales-de-forma-segura
- Supersedes: none
- Superseded by: none

## Context

Backend y processor comparten defaults inseguros y limites de diagnostico.
CockroachDB local usa --insecure; Grafana conserva password admin por defecto.
El seed demo sobrescribe el hash existente. Corregir estos limites afecta a
politicas duraderas de seguridad, aunque no requiera nuevas dependencias.
TLS/provisioning, secret manager y despliegue de proveedores estan fuera de alcance.

## Decision

Decision con aprobacion parcial de Paris Arcos, registrada el 2026-09-09
a las 14:12 UTC. Aprobadas la excepcion CockroachDB local y la inclusion de
Grafana con password conservada en `.env`; aun no implementadas.
Paris Arcos completo la aprobacion tras la explicacion del cambio demo;
registro del 2026-09-09 a las 14:24 UTC. ADR y gate previo: APPROVED.
La aprobacion no acredita implementacion, QA ni autorizacion de publicacion.

- Reutilizar Pydantic Settings, SecretStr y structlog por servicio; exigir
  secretos externos, fixtures de test explicitas y diagnosticos saneados.
- Redactar campos sensibles y valores configurados conocidos, sin prometer
  deteccion de secretos arbitrarios. Excluir secretos de bundles y builds.
- Permitir CockroachDB sin autenticacion solo en demo local desechable/test
  aislado, con entorno, destino y opt-in explicitos y confirmacion del operador.
  Nunca compartido/produccion. Excepcion local: APPROVED; no activa el opt-in.
- Conservar la password de Grafana en `.env` local, fuera de Git y contextos
  Docker, usando `GRAFANA_ADMIN_PASSWORD`; `.env.example` deja el campo vacio.
  Quitar el fallback versionado, no la password ni la autenticacion. No rotar
  ni regenerar el valor existente. Alcance Grafana: APPROVED con esa condicion.
  No se incluye hardening general ni cambios de dashboards.
- Seed opt-in sin sobrescrito, password sin prefill y rotacion de cuenta
  existente por accion explicita. Rechazar password demo insegura conocida
  con indicacion de rotacion manual. Cambio demo: APPROVED.

## Consequences

Arrancar requerira preparar configuracion; copiar el ejemplo no sera suficiente.
Un opt-in o una URL loopback no prueban aislamiento ni autorizan la excepcion.
Cambiar variables no rota passwords persistidas en DB/Grafana o cuentas demo.
Mover la password a `.env` no convierte un valor debil en uno robusto; no se
certifica fortaleza ni se aplica una rotacion como parte de este traslado.
No se cambian contratos de sesion/tenant ni se introducen migraciones.

## Alternatives Considered

- Sin excepcion local: alternativa no elegida; configurar un stack seguro
  con TLS/provisioning requeriria otro alcance y decision arquitectonica.
- Password Grafana en `.env`: elegida, conservando el valor y la autenticacion.
- Excluir Grafana: alternativa no elegida; su inclusion ha sido aprobada.
- Secret manager central: requiere otro alcance, aprobacion y ADR; no elegido.

## Evidence And Follow-up

Base de inspeccion: 7d76fc376e0eca1aac6401304977575a2f92ceb5; fuentes de alcance:
plan aprobado de 2026-09-07 y export Trello leido el 2026-09-09, sin acceso vivo.
Al registrar el gate previo todavia no habia resultados funcionales ni scan.
La evidencia posterior de Green3, mutation y QA esta en
[JUP-053-validation.md](../evidence/JUP-053-validation.md).
El gate previo esta aprobado y OpenSpec revalidado. QA confirma el alcance
acotado, pero RF-053-004 mantiene pendiente la aceptacion completa y humana;
no hay CI remoto ni aprobacion final. La implementacion posterior traslado
la fuente Grafana al .env ignorado conservando el valor, sin rotacion.
El acto documental de aprobacion no leyo ni modifico ese fichero.
ADR-0002 y sus aprobaciones no se modifican; este ADR no lo sustituye.
