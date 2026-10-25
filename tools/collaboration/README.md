# Economicon collaboration bridge

Puente controlado para consultar el canal de Discord y el tablero de Trello del
proyecto desde `dockerserver`. No es un servicio de la aplicacion Economicon ni
necesita estar ejecutandose permanentemente: cada comando crea un contenedor
temporal y lo elimina al terminar.

## Politica de seguridad

- La lectura se habilita cuando las credenciales son validas.
- Discord es estrictamente de solo lectura: no existe comando ni metodo para
  publicar mensajes.
- Cada escritura de Trello exige `TRELLO_ALLOW_WRITES=true` y
  `--confirm-write`.
- No existe ninguna operacion de borrado.
- Los mensajes de Discord deshabilitan menciones automaticas.
- Los secretos solo se guardan en `.env` dentro de `dockerserver`, con permisos
  `600`; nunca se copian al repositorio ni a los snapshots.
- `data/` contiene conversaciones y actividad interna, esta ignorada por Git y
  debe conservar permisos restrictivos.

## Permisos minimos

### Discord

El bot se limita al servidor y canal configurados y necesita:

- View Channel;
- Read Message History;
- Message Content intent habilitado.

No necesita Send Messages, Administrator, Manage Channels, Manage Roles,
Manage Messages, Ban Members ni Kick Members. El permiso Send Messages debe
estar denegado en Discord como segunda barrera independiente del codigo.

### Trello

La API key y el token pertenecen a una cuenta miembro del tablero. El puente
expone lectura de tablero, listas, tarjetas y acciones, y solo estas escrituras:

- crear tarjetas;
- comentar tarjetas;
- mover tarjetas entre listas;
- actualizar nombre, descripcion o fecha.

## Instalacion en Dockerserver

```bash
cd /home/danteadmin/economicon-collaboration
cp .env.example .env
chmod 600 .env
# Completar los tokens fuera de Git.
docker compose build
docker compose run --rm collaboration check
docker compose run --rm collaboration sync
```

`check` valida ambos accesos. `sync` pagina hasta
`COLLAB_MAX_DISCORD_PAGES * 100` mensajes y guarda `latest.json` y `latest.md`
en `data/snapshots/`. Si Discord responde HTTP 429, el cliente respeta primero
el `retry_after` JSON y despues la cabecera `Retry-After`, con un maximo de
cuatro reintentos y 60 segundos por espera.

Los snapshots contienen el texto original del canal. Si alguien publica una
credencial en Discord, se debe revocar en el proveedor; el snapshot no convierte
una credencial expuesta en segura.

## Escrituras de Trello explicitas

```bash
docker compose run --rm collaboration trello-comment \
  --card-id CARD_ID --text "PR lista para revision" --confirm-write

docker compose run --rm collaboration trello-move \
  --card-id CARD_ID --list-id LIST_ID --confirm-write
```

Aunque `TRELLO_ALLOW_WRITES=true` este activo en el servidor, omitir
`--confirm-write` impide la operacion. Discord no admite escrituras incluso si
la antigua variable `COLLAB_ALLOW_WRITES` permanece configurada en el servidor;
por compatibilidad, esa variable antigua solo puede habilitar Trello.

## Diagnostico

- `Missing required environment variables`: falta una clave en `.env`.
- HTTP 401/403: token invalido o permisos insuficientes.
- HTTP 429 tras cuatro reintentos: limite sostenido; reducir temporalmente
  `COLLAB_MAX_DISCORD_PAGES` y volver a ejecutar mas tarde.
- El login web de Discord no afecta al bot; son sesiones independientes.

## Pruebas

```bash
python -m unittest discover -s tools/collaboration/tests -v
```
