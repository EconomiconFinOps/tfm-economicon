# Evidencia de validacion JUP-081

- Fecha: 2026-08-27.
- Repositorio: `EconomiconFinOps/tfm-economicon`.
- Rama: `feat/JUP-081-collaboration-bridge` hacia `develop`.
- Pull request: https://github.com/EconomiconFinOps/tfm-economicon/pull/15.
- Tarjeta: https://trello.com/c/g91V6TXp.
- Liderazgo: Alejandro Aguado; pairing: Lucia Mateo; revision: Paris Arcos
  Martin; validacion, pruebas y documentacion: Victor Mendez.

## Diagnostico real

- El `.env` de Dockerserver existe con modo `600` y no se ha copiado.
- `check` devuelve correctamente el canal Discord y el tablero Trello.
- Un `sync` de diez paginas reprodujo HTTP 429 con `retry_after` inferior a un
  segundo.
- Un `sync` limitado a una pagina genero un snapshot de los cien mensajes mas
  recientes y todas las tarjetas sin publicar mensajes.
- La implementacion historica estaba desplegada y presente como archivos
  locales no versionados, pero ausente de `develop`.

## Implementacion

- Puente y Docker Compose reconciliados en el repositorio canonico.
- Reintentos HTTP 429 acotados con prioridad al `retry_after` JSON.
- Paginacion, reintentos, snapshots y barreras de escritura cubiertos por tests.
- Tests integrados en el check `OpenSpec` sin cambiar los seis contextos
  protegidos.
- Snapshots ignorados y credenciales limitadas al servidor.

## Validacion

- Pruebas del puente: `9 passed` con Python 3.12.
- Servicios sin regresiones: Azure Cost API `58 passed`, backend `10 passed` y
  processor `126 passed`.
- OpenSpec estricto: `17 passed, 0 failed`.
- JUP, politica de PR, CI, roadmap, repositorio, higiene, corpus y gateway en
  verde; build de frontend superado.
- Validacion temporal en Dockerserver con el codigo de la rama: `check`
  correcto y `sync` completo de 10 paginas sin HTTP 429.
- Snapshot real: 1.000 mensajes Discord, 74 tarjetas y 100 acciones Trello.
- Imagen, snapshot y directorio temporales retirados al finalizar.
- CI remota inicial: seis checks superados en
  https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/33087092287.

No se ha enviado ningun mensaje a Discord ni se han mostrado credenciales.

## Endurecimiento de solo lectura — 2026-08-28

- Eliminados `discord-post` y `DiscordClient.post_message`; la CLI y el cliente
  Discord solo exponen consultas `GET`.
- Las escrituras de Trello usan `TRELLO_ALLOW_WRITES`; la antigua
  `COLLAB_ALLOW_WRITES` se admite solo como compatibilidad para Trello y no
  puede habilitar Discord.
- Pruebas del puente: `10 passed`, incluida una regresion que verifica que la
  variable antigua no crea ningun metodo ni comando de publicacion Discord.
- OpenSpec estricto: `17 passed, 0 failed`; trazabilidad JUP e higiene en verde.
- Imagen reconstruida y desplegada en Dockerserver.
- Validacion real: `check` conserva lectura de Discord y Trello;
  `discord_post_method=False` y `discord_post_command=False` dentro del
  contenedor desplegado.
- Una invocacion de `discord-post` termina en `invalid choice` antes de cargar
  configuracion o contactar con Discord.

Como segunda barrera, la configuracion del canal debe denegar `Send Messages`
al rol del bot. El bot no dispone de la autoridad necesaria para auditar o
modificar roles del servidor mediante la API; ese ajuste requiere un
administrador de Discord.
