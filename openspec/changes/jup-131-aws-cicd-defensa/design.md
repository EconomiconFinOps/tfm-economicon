# Diseño JUP-131

JUP: JUP-131
Trello: https://trello.com/c/NtiH8R4Z

Aplicar [plan](../../../docs/planning/aws-cicd-defensa.md) y
[ADR-0027](../../../docs/adr/ADR-0027-aws-defense-lifecycle.md).
Bootstrap separado; dos pipelines manuales sin trigger de cambios, un runner
serializado y lease de dominio sin TTL. Terraform mantiene la arquitectura de
JUP-060 y exige una boundary de roles ECS al ejecutar por CI/CD.

Config fuera de Git direccionada por SHA256, source COMMIT_ID y CI SUCCESS exacta.
Planes binarios y binding privados. Teardown acepta únicamente IDs/addresses del
state propio y detiene escritores antes del vaciado. Recuperación usa el mismo
state; un plan down invalida el up anterior. Caducidad funciona con sourcebundle
del mismo SHA y lockfiles. Secretos en entorno/Secrets Manager, fuera de logs.

La preparación local es libre de APIs AWS y produce readiness negativo cuando
faltan cuenta/DNS/motores/CI/aceptación. El runtime real no se habilita sin receta
y evidencias de adaptación asociadas al hash de aplicación. El runbook distingue
pruebas offline, campos pendientes y futuras acciones con coste.

El 21/10 el usuario amplía la implementación a las adaptaciones de aplicación y
scripts, conservando la prohibición de desplegar. Se aplica el
[plan de adaptación](../../../docs/planning/aws-application-adaptations.md).
PostgreSQL usa tipos TEXT comunes, catálogo nativo validado y DSN explícito;
se conserva Cockroach. Cognito vincula el sub firmado al id del usuario local
creado por bootstrap, nunca por coincidencia de correo ni por claims de tenant.
Las membresías y permisos siguen siendo autoridad de la base operativa.

El22/10 el usuario autoriza Irlanda como región de aplicación y las solicitudes
de Fargate6vCPU Irlanda/CodeBuild Medium1 París, sin despliegue. La política
y receta fijan Irlanda; TLS RDS y perfiles regionales se sustituyen con nuevos
hashes/evidencia. Nova UE desde Irlanda solo admite cuatro destinos revisados.
El preflight exige cuotas efectivas antes de lease/planes/alta demo; solicitudes
pendientes no equivalen a recursos habilitados. Plan aws-ireland-transition.md.

En el ensayo3 del25/10, los dos processors tienen boot_id independientes y
Cloud Map puede resolver una IP diferente en cada conexión. El backend vincula
el boot_id del descriptor firmado a la IP real del socket, manteniendo el puerto
configurado. Chat, tool-result, cancelación y resúmenes usan ese vínculo sin
cambiar el host global. Un backend sin caché busca el boot mediante GET firmados
a un máximo de16 candidatos DNS; nunca reenvía una inferencia a otra réplica.
La caché se limita a256 entradas durante300 segundos y rechaza reasociaciones
de boot. La resolución participa en el deadline; cancelar impide sondas tardías
cuando termina un DNS bloqueado. El sistema operativo puede mantener ese hilo
DNS hasta resolver, pero el llamante no espera fuera de plazo. La búsqueda
secuencial puede agotar los2 segundos de control antes de un segundo candidato
sano; se conserva el resultado incierto y la recuperación existente.
