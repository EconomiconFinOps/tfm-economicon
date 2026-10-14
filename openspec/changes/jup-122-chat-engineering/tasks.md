# Tareas JUP-122

- [x] 1.1 Crear entregas A/B y conservar JUP-035 principal en Trello.
- [x] 1.2 Incorporar base de Paris y reconciliar develop/JUP-119.
- [x] 1.3 Extraer bloques de ingeniería sin rediseño semántico de PR121.
- [x] 1.4 Mantener chat desactivado por defecto y comprobar rechazo sin inferencia.
- [ ] 2.1 Completar regresiones aplicables y CI sobre el candidato publicado.
- [x] 2.2 Validar migraciones y carreras contra Cockroach nativo (54PASS en CI 2b55e1e2; código de producto sin cambios posteriores).
- [ ] 2.3 Validar UI en navegador sobre el candidato; identificar sus límites.
- [ ] 3.1 Publicar sustitución y cerrar #120/#121 sin merge ni borrar ramas.
- [ ] 3.2 Obtener Revision JUP-122 y Validacion JUP-122 oficiales.

La aceptación semántica y la activación pertenecen a JUP-123/B.

## Adaptacion acotada de tres mejoras
Este bloque sustituye el borrador anterior de siete puntos; no autoriza sus
otras cuatro mejoras ni cambios semanticos de JUP-123/B.

- [x] 4.1 Aprobar el alcance de tres puntos y validar estrictamente OpenSpec antes de producto/tests.
- [x] 4.2 Adaptar el descargador fijo/verificado y pruebas; sacar tokenizer de Git y ajustar Docker, CI, exclusiones y documentacion.
- [x] 4.3 Excluir .secrets de releases y contextos sin cambiar provision HMAC ni controles de symlinks.
- [x] 4.4 Hacer portable la fixture SQL del processor y esperar su tarea de limpieza real, conservando aserciones y tiempos del producto.
- [ ] 4.5 Conservar Red/Green focales y ejecutar SQL aislado sin omisiones, build offline, regresiones afectadas y controles obligatorios.
- [x] 4.6 Entregar matriz tres puntos/archivos/resultados/limites y guard; revision humana y publicacion permanecen separadas.

4.5: controles ejecutados. Las pruebas focales, imagenes offline, build y
gobernanza pasan. La tanda amplia backend conserva seis fallos de JUP-047 por
JWT creados en collection y caducados antes del caso; los ocho controles de
autorizacion pasan en ejecucion focal. No se modifica esa fixture fuera de
alcance ni se declara una unica tanda completa verde. Ver
[resultados y limites](../../../docs/evidence/JUP-122-checkpoint-improvements-20261014.md).
