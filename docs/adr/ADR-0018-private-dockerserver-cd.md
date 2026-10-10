# ADR-0018 — CD privado mediante agente de lectura en DockerServer

Status: Proposed
Date: 2026-10-03
JUP: JUP-052
Trello: https://trello.com/c/q3TahHoj
OpenSpec: [jup-052-dockerserver-cd](../../openspec/changes/archive/2026-10-04-jup-052-dockerserver-cd/design.md)

DockerServer es compartido y su SSH está en red privada; no hay runner GitHub
registrado. El entorno solicitado es de desarrollo/validación desechable.

GitHub valida el SHA integrado de `develop` reutilizando CI. Un agente systemd
de usuario consulta desde DockerServer únicamente ejecuciones CD del repositorio
canónico. Construye el SHA validado y prueba un slot distinto antes de cambiar
el estado vigente. No recibe webhooks, claves de despliegue ni tareas de PR.

Se fuerzan puertos loopback y se generan secretos locales fuera de Git. Cada
SHA conserva fuentes, imágenes y volúmenes propios. El rollback recupera el
entorno previo y pausa la promoción automática, sin pretender rollback de datos.

Costes: latencia de hasta cinco minutos más build/smoke; mantenimiento explícito
del agente y limpieza de releases; acceso por túneles con puertos alternantes.
GitHub verde indica elegibilidad, no confirma por sí solo runtime saludable.
La confianza operativa sigue recayendo en quienes integran código en `develop`
y en la cuenta Linux que administra el motor Docker compartido.
