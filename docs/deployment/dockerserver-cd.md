# JUP-052 — CD privado hacia DockerServer

Trello: https://trello.com/c/q3TahHoj

El entorno es **desarrollo/validación con datos desechables**, CockroachDB
inseguro explícitamente permitido, IA mock y usuario demo. No es producción.
Todos los puertos publicados se fuerzan a `127.0.0.1`; acceso por túnel SSH.
Loopback impide acceso remoto directo, pero no protege de otros usuarios locales
del host: la SQL de CockroachDB es insegura y accesible sin contraseña localmente.
Solo usar datos desechables y una cuenta/host con usuarios locales de confianza;
no se acredita aislamiento entre usuarios del servidor compartido.
No ejecutar código de PR en un runner con acceso al Docker compartido.

## Flujo

1. Un push integrado a `develop` ejecuta `CD DockerServer`. También admite
   `workflow_dispatch`; sus jobs solo se ejecutan sobre `develop`. Un dispatch
   desde otra rama puede terminar verde con jobs omitidos, pero el agente exige
   también `head_branch=develop` y lo rechaza.
2. CD llama al workflow CI del mismo commit: pruebas Python, frontend,
   lint, typecheck, build y controles de gobierno/OpenSpec. `eligible` solo
   termina en verde si todos los jobs aplicables pasan.
3. Cada cinco minutos el agente Linux consulta la API pública de GitHub.
   Solo acepta la ejecución más reciente de `cd.yml`, exitosa, sobre el SHA
   actual de `develop` y del repositorio canónico. Un fallo, cancelación,
   PR, fork, SHA antiguo o cambio de rama durante el fetch no despliega.
4. Obtiene ese SHA por Git, crea una release inmutable, construye las imágenes
   en DockerServer y arranca nueve servicios con `up --wait`.
5. Verifica salud, login demo, ingesta del simulador, totales de facturación
   y job RabbitMQ completado. Solo entonces escribe `state.json` y detiene
   la release anterior. La ejecución GitHub acredita **elegibilidad**;
   `state.json` y el journal acreditan **despliegue real**.

El SHA de `develop` se comprueba después del fetch, después de preparar la fuente
y de nuevo tras build/smoke antes de promover. Si avanza, no cambia el puntero.
La consulta adicional ocurre solo con candidato; no es una transacción con
GitHub y `develop` aún podría avanzar inmediatamente después de la comprobación.

El agente no necesita credenciales GitHub/SSH en Actions: el repositorio es
público y el servidor abre las conexiones salientes. API sin autenticar:
dos consultas por ciclo sin cambios; cuatro cuando hay candidato. Un error
de red o límite de API falla cerrado y se reintenta en el siguiente ciclo.

## Instalación reproducible

Requisitos: Python >=3.12, Git, Docker Engine y Compose con `--wait` y
`config --format json`, systemd de usuario. La cuenta pertenece al grupo
Docker; esa cuenta tiene capacidad administrativa sobre el motor y debe
ser de confianza. No instalar runners públicos en ella.

Copiar `tools/cd/` de la revisión revisada a
`/home/danteadmin/economicon-cd/tools/cd/`, y las unidades `infra/cd/` a
`/home/danteadmin/.config/systemd/user/`. El agente se actualiza explícitamente
desde una revisión revisada; no se reemplaza ejecutando código recién descargado.

```sh
python3 /home/danteadmin/economicon-cd/tools/cd/deploy.py \
  --root /home/danteadmin/economicon-cd-runtime init --port-base 19252
loginctl enable-linger danteadmin
systemctl --user daemon-reload
systemctl --user enable --now economicon-cd.timer
systemctl --user start economicon-cd.service
journalctl --user -u economicon-cd.service --no-pager -n 30
systemctl --user list-timers economicon-cd.timer
```

`init` genera secretos aleatorios locales; directorio `700`, archivos `600`.
Se niega a sobrescribir configuración/secretos existentes. No copiar esos
archivos al repositorio ni imprimir `compose config` en evidencias: contiene
secretos. Antes de activar, verificar `Linger=yes` y que los puertos
19252–19262 y 19352–19362 estén libres. Otras bases se eligen en `init`.

El timer espera cinco minutos desde el fin de cada ejecución; el lock impide
despliegues concurrentes. Si CD todavía no se ha integrado, registra espera
sin desplegar. No modifica otros stacks ni usa `docker system prune`.

## Acceso y operación

El puerto de frontend/API está en `state.json`: alterna entre slots A/B.
Para el slot A:

```sh
ssh -N -L 19260:127.0.0.1:19260 -L 19257:127.0.0.1:19257 DockerServer
# Navegar a http://127.0.0.1:19260
```

Para B, sustituir por `19360` y `19357`. No hay proxy estable ni promesa de
cero interrupciones. La contraseña demo se consulta localmente en el archivo
privado; nunca se coloca en README, PR o Trello.

```sh
systemctl --user disable --now economicon-cd.timer
# No interrumpe un despliegue en curso; esperar a que termine antes de operar.
python3 /home/danteadmin/economicon-cd/tools/cd/deploy.py \
  --root /home/danteadmin/economicon-cd-runtime rollback
```

Rollback arranca la release anterior con imágenes locales y sus propios
volúmenes, pasa el smoke, cambia el puntero y detiene la actual. Pausa las
promociones automáticas mediante `manual_rollback`; `resume` elimina esa pausa.
No revierte migraciones ni recupera los datos de la nueva release: cada SHA
usa volúmenes aislados y datos demo/simulados. Ante fallo del candidato, la
release anterior permanece en marcha, y el candidato se detiene sin borrar
volúmenes. `failure.json` se escribe antes de limpiar y conserva SHA/run y tipos
de error; no valores ni mensajes potencialmente sensibles. Si también falla
`down`, conserva el fallo original y añade el tipo de error de limpieza.
`compose down` elimina contenedores y sus logs; el journal conserva la salida
del agente, y los volúmenes/fuentes se retienen, no los logs de contenedor.

Cada poll bajo lock intenta detener todas las releases inactivas de este root (incluida
`previous`, conservando sus volúmenes para rollback) y elimina copias
`<sha>.preparing` incompletas. Reintenta así una limpieza interrumpida después
de promover o hacer rollback, incluso sin nuevo SHA o con pausa manual.
Antes de reutilizar un slot exige que esa limpieza termine correctamente.
Si una release falla, continúa con las restantes y las copias incompletas;
al terminar informa de todos los SHA/tipos fallidos. El segundo reconcile
antes de fetch bloquea al candidato si persiste cualquier fallo de limpieza.
Un fallo al recuperar `current` se registra en `recovery.json`; continúa la
consulta de elegibilidad, de modo que un SHA corregido pueda reemplazarla.
Ese archivo representa fallos aún pendientes del último intento: fases,
SHA/tipos saneados y timestamp. Se elimina cuando limpieza y recuperación
terminan bien, o después de una promoción/rollback sanos y limpieza correcta.
Limpiar solo las releases no borra el fallo de una current todavía rota.

Un error de red/API en la verificación final de head detiene el candidato
sin promover ni poner en cuarentena un SHA funcionalmente sano: el siguiente
poll lo reintenta. Un head avanzado se registra como `superseded`, distinto
de `candidate-failed`. `events/*.json` conserva ambos tipos de intento y los
fallos de limpieza; no sobrescriben `failure.json`, que identifica el último
fallo funcional permanente. Tras reintento exitoso se añade `resolved_at`.

El registro de evidencia es best effort: un disco lleno o falta de permisos
emite `Evidence unavailable: TIPO`, sin mensajes privados. No impide intentar
down ni sustituye la causa original. Si no se pudo guardar failure.json,
la cuarentena no queda garantizada: detener el timer y reparar almacenamiento
antes de continuar; comprobar state.json/containers y el journal, no asumir
que ausencia de fichero significa éxito. Las escrituras de state.json siguen
siendo obligatorias, no registros opcionales.

Una promoción que ya escribió state.json sigue efectiva aunque la limpieza
posterior falle: resolved_at se intenta **antes** de reconcile; recovery.json
recoge fase cleanup y todos los SHA/tipos de CleanupError. El CLI avisa
`State already changed: current SHA; cleanup pending`; el siguiente poll
recupera current, reintenta resolved_at y limpieza incluso sin head nuevo/API.
Already deployed también reintenta resolved_at, conservando recovery pendiente
hasta que un poll compruebe la limpieza. resolved_at indica promoción verificada,
no que todos los contenedores antiguos estén detenidos.

Mientras manual_rollback está activo, repetir rollback verifica **current**
y reintenta limpiar las inactivas; no intercambia otra vez current/previous.
Si falla esa reverificación, registra current pendiente sin detenerla ni
cambiar el puntero. Para habilitar otra selección debe usarse resume después
de revisar su riesgo. Tras cleanup fallido, comprobar state antes de operar.

events registra intentos de candidato y cleanup posterior a promoción/rollback.
Los fallos de reconcile de poll van a recovery.json (último intento, no historial);
validate-source bloqueado antes de prepare informa CleanupError en el CLI,
sin asegurar histórico de ese fallo. El detalle saneado está en
CleanupError.failures; no se imprimen excepciones/entornos completos.

No hay backoff adaptativo ni reutilización de smoke: cada poll elegible tras
error de API final repite build/up/smoke, hasta 288 intentos/día con timer5min.
Se acepta por exigir comprobación funcional fresca; ante 403 persistente o
caída prolongada, el operador detiene el timer, comprueba API/causa y lo reactiva
al recuperarse. Vigilar espacio y archivar events privados según política local;
no hay retención automática. Es un límite operativo, no un backoff implementado.

Un SHA que falla no se reconstruye cada cinco minutos: `failure.json` pausa ese
SHA hasta un nuevo SHA o `resume`. `resume` habilita el reintento sin borrar la
evidencia de fallo y elimina la pausa manual,
también cuando el primer despliegue falló y aún no hay `state.json`.
Después de rollback, `resume` levanta simultáneamente la pausa manual y la
cuarentena del fallo anterior: puede volver a intentar la release que motivó
el rollback. Antes de usarlo, verificar el SHA elegible y su causa corregida;
si no, conservar la pausa y esperar otro SHA. No es una elección automática
de la versión más segura.

Los volúmenes y fuentes se conservan para investigar/rollback. Revisar espacio
periódicamente. El coste de down crece con el histórico: se acepta el barrido
completo por seguridad ante interrupciones y arranques externos. Como política
operativa, retener bajo `releases/` current, previous y el último fallo útil;
archivar el resto con el procedimiento siguiente. No hay borrado automático
de volúmenes, fuentes ni eventos; el coste real no se ha medido en esta revisión.

### Retirar una release sin bloquear CD

No borrar archivos sueltos de `releases/<sha>`: cada directorio administrado
debe conservar su `.env` y `compose.json` para poder detener su proyecto.

1. Desactivar el timer y esperar a que `economicon-cd.service` esté inactivo.
   Abrir una consola del operador bajo `flock -n ROOT/deploy.lock bash` y
   mantenerla hasta terminar; salir libera el lock. No operar si no se obtiene.
2. Leer state.json y comprobar que el SHA no es current ni previous. Identificar
   el nombre exacto de su proyecto en su compose.json congelado y confirmar
   que pertenece al root propio; no deducirlo de nombres ajenos ni usar prune.
3. Con la configuración completa, ejecutar el mismo comando compose del agente
   (`--project-directory RELEASE --env-file RELEASE/.env -f RELEASE/compose.json
   down --remove-orphans`, sin `-v`). Comprobar con `docker ps -a --filter
   label=com.docker.compose.project=PROYECTO` que no queda ningún contenedor.
4. Solo tras la comprobación, mover el directorio **completo** a `ROOT/retired/`
   (fuera de `releases/`, con permisos privados). Conservar volúmenes y evidencia;
   activar el timer al terminar. El scanner deja de intentar esa release.

Si ya faltan archivos, restaurar primero `.env`/compose.json del backup privado.
Sin backup, identificar y retirar manualmente **solo** los contenedores cuyas
etiquetas de proyecto verifiquen su pertenencia a esa release/root; conservar
volúmenes, confirmar ausencia y mover luego el directorio completo a retired.
Si no se puede acreditar el proyecto, no moverlo para eludir el guard: mantener
el bloqueo e investigar. Nunca borrar una carpeta mientras su pila siga viva.

Una release congelada que usa el slot ahora ocupado por current no se migra
automáticamente al otro slot. Si prepare lo rechaza tras una secuencia de
rollback/reintentos, conservar la pausa y usar un nuevo SHA o un root de ensayo
con otros puertos; no repetir resume ni editar la configuración inmutable.

La suite Windows tuvo un aviso externo de flake en limpieza temporal WinError145;
no se ha establecido su causa. Las regresiones Linux son el control principal
del agente; un fallo Windows no debe omitirse ni atribuirse a Docker sin evidencia.

## Ensayo aislado sin integración

```sh
python3 tools/cd/deploy.py --root /home/danteadmin/economicon-cd-validation init --port-base 19452
python3 tools/cd/deploy.py --root /home/danteadmin/economicon-cd-validation \
  validate-source --source /ruta/al/checkout/revisado --sha SHA_COMPLETO
```

`validate-source` es exclusivamente un comando de operador para ensayar código
pendiente: nunca lo llama el timer y no acredita una ejecución GitHub real.
Usar otro root y otros puertos para no mezclar ensayo y despliegue automático.
El nombre del proyecto Compose incluye un hash del root y el prefijo del SHA;
releases ya preparadas conservan sus nombres inmutables. El comando rechaza un
SHA que ya existe y un root con rollback pausado, evitando descartar `--source`
silenciosamente. **Promueve el state de ese root y detiene su release anterior**:
no es un dry-run. `--sha` es una etiqueta completa aportada por el operador,
no una prueba de relación Git con `--source`; el operador verifica el checkout.
No usar el root automático para este ensayo.

Las unidades systemd llevan las rutas de instalación y el usuario de este host;
adaptarlas antes de instalar en otro host. Cuando JUP-051 integre CI en pushes,
un push a develop ejecutará también esa CI además de la CI reutilizada por CD;
se acepta ese coste de defensa independiente por ahora.

Decisión: [ADR-0018](../adr/ADR-0018-private-dockerserver-cd.md), Proposed.

Referencias: [workflows reutilizables](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows),
[timers systemd](https://github.com/systemd/systemd/blob/main/man/systemd.timer.xml).
