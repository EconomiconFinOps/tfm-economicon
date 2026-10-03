# JUP-052 — CD privado hacia DockerServer

Trello: https://trello.com/c/q3TahHoj

El entorno es **desarrollo/validación con datos desechables**, CockroachDB
inseguro explícitamente permitido, IA mock y usuario demo. No es producción.
Todos los puertos publicados se fuerzan a `127.0.0.1`; acceso por túnel SSH.
No ejecutar código de PR en un runner con acceso al Docker compartido.

## Flujo

1. Un push integrado a `develop` ejecuta `CD DockerServer`. También admite
   `workflow_dispatch`, exclusivamente sobre `develop`.
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

El agente no necesita credenciales GitHub/SSH en Actions: el repositorio es
público y el servidor abre las conexiones salientes. API sin autenticar:
dos consultas por ciclo sin cambios; tres cuando hay candidato. Un error
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
volúmenes; `failure.json` y el journal conservan el resultado.

Los volúmenes y fuentes se conservan para investigar/rollback. Revisar espacio
periódicamente y retirar releases antiguas de forma explícita tras confirmar
que no son `current` ni `previous`; no hay borrado automático de datos.

## Ensayo aislado sin integración

```sh
python3 tools/cd/deploy.py --root /home/danteadmin/economicon-cd-validation init --port-base 19452
python3 tools/cd/deploy.py --root /home/danteadmin/economicon-cd-validation \
  validate-source --source /ruta/al/checkout/revisado --sha SHA_COMPLETO
```

`validate-source` es exclusivamente un comando de operador para ensayar código
pendiente: nunca lo llama el timer y no acredita una ejecución GitHub real.
Usar otro root y otros puertos para no mezclar ensayo y despliegue automático.

Referencias: [workflows reutilizables](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows),
[timers systemd](https://github.com/systemd/systemd/blob/main/man/systemd.timer.xml).
