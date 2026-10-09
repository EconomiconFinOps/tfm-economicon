JUP: JUP-108
Trello: https://trello.com/c/0MANNZZ4
Estado vigente: entrega local revisada/validada y aprobada por Paris; archivado el09/10/2026 en la misma rama. Publicación y reviews humanas posteriores pendientes.

## Why

El Compose principal configura backend y processor para hablar con `litellm`,
pero no declara el gateway ni su PostgreSQL. El entorno aislado de JUP-023 los
arranca por separado, lo que obliga a conectar proyectos manualmente para usar
proveedores reales. La tarjeta pide un arranque reproducible desde el Compose
principal sin perder el modo simulado.

## What Changes

- Incorporar LiteLLM y su PostgreSQL dedicado al Compose principal bajo un
  perfil opcional de IA real, reutilizando la definicion fijada en
  `infra/litellm/docker-compose.yml` y los mismos archivos de configuracion.
- Conectar backend y processor al gateway por la red interna, con comprobaciones
  de salud y dos claves virtuales independientes, sin exponer PostgreSQL ni la
  administracion del gateway fuera de loopback.
- Permitir que el modo simulado se configure y arranque sin claves de
  OpenRouter ni contenedores del gateway; exigir secretos validos al activar el
  perfil real.
- Conservar un volumen propio para las claves virtuales y los metadatos de
  gasto; documentar configuracion, creacion de claves, arranque y parada sin
  tocar volumenes existentes.
- Ajustar las pruebas afectadas y dejar evidencia de ambos modos, del rechazo
  de claves invalidas y de la persistencia tras recrear los contenedores.

Fuera de alcance: modelos, presupuesto o contratos de IA; funcionalidad de
negocio; DockerServer compartido; migrar o borrar bases y volumenes existentes;
llamadas pagadas sin autorizacion adicional.

## Capabilities

### New Capabilities

Ninguna: se extiende la topologia local existente.

### Modified Capabilities

- `containerized-runtime`: topologia base de nueve servicios sin perfil y
  topologia ampliada con gateway y PostgreSQL cuando se activa IA real.

## Impact

Archivos previstos: `docker-compose.yml`, `infra/litellm/docker-compose.yml`,
`infra/litellm/README.md`, `.env.example`, `README.md`,
`tools/docker-topology.test.mjs` y las pruebas Docker aisladas afectadas. El
detalle se cerrara contra el diseno validado antes de programar. No se preven
cambios en `apps/`, dependencias de produccion, API ni migraciones.

Asignación vigente por instrucción expresa de Paris, fecha de asignación08/10/2026: Paris Arcos liderazgo; Lucía Mateo pairing/coautoría; Víctor Méndez revisión de PR; Alejandro Aguado validación, pruebas y documentación. La participación efectiva se acreditará; no se presume por asignación ni autoriza publicación o gasto. La asignación anterior observada por PM en Trello se conserva como historia en la evidencia, sin afirmar actualización oficial del tablero.


## Pre-code approval — registro consolidado

Estado: **APPROVED** por Paris Arcos el08/10/2026, antes de iniciar pruebas e implementación. No se acredita el segundo exacto del mensaje humano ni se sustituye por el inicio del turno.

Fuente humana: chat `01a07c55-c454-7bb3-8053-cbf2ad70d2ec`, mensaje `01a11d20-6fb3-7743-9510-51592abce453`, turno `01a11d20-6f59-7a22-a39d-dfc52498d6ae`. Paris respondió «si, pero recuerda que nada de github ni trello ok ?» a la pregunta explícita de aprobar el diseño JUP-108 y autorizar pruebas/implementación, manteniendo fuera gasto OpenRouter, PR y cambios Trello. La aprobación no autoriza publicación ni gasto adicional.

Registro documental autorizado por Project Manager el09/10/2026 a las00:02:03Atlantic/Canary, con fuente humana ya verificada. No altera el diseño, alcance o decisión original ni constituye una nueva aprobación pre-code. La aprobación final posterior a validación permanece pendiente y separada.


## Post-validation approval — APPROVED, archivo autorizado y roles vigentes

Paris respondió «apruebo» al paso explícito de aprobación final de la entrega y autorización para archivar OpenSpec en esta misma rama, con la excepción histórica ya aprobada. PM registró la decisión el09/10/2026 a las00:08:45Atlantic/Canary; es hora de registro, no segundo exacto del mensaje humano. Fuente preservada: `jup108-final-approval-and-roles-20261009.md` del expediente PM.

Asignación vigente expresamente indicada por Paris, con fecha de asignación08/10/2026: **Paris Arcos liderazgo; Lucía Mateo pairing/coautoría; Víctor Méndez revisión de PR; Alejandro Aguado validación, pruebas y documentación**. La fuente de este cambio es la comunicación humana directa transmitida por PM, no una nueva lectura de Trello. No se presume participación realizada; se conservan atribuciones y asignaciones históricas con sus fuentes/fechas.

Revisión y validación locales favorables y controles aplicables acreditados; excepción exclusivamente JUP-108 para referencias históricas diseño/Red/Green no localizadas. Se conserva el FAIL original del helper y la aprobación de excepción separada, sin inventar PASS/guards/snapshots ni modificar el helper. El cierre final se registra bajo esa disposición humana expresa, no como DoD nativo PASS.

Se autoriza únicamente el archivo OpenSpec de JUP-108 en `feat/JUP-108-litellm-compose`, promoviendo su delta al canónico y conservando evidencia/resultado local. PR, CI y reviews humanas de Víctor/Alejandro permanecen hitos posteriores; commit/push, PR, comentarios/publicaciones y merge no están autorizados. La aprobación final/archivo no completan el criterio7 global ni atribuyen reviews humanas a los agentes.
