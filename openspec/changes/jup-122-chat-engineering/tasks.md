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

## Correcciones bloqueantes de la revision de PR130

- [x] 5.1 Asignar subred privada e IP del processor distintas por slot de CD, con regresion significativa y render real de ambos slots.
- [x] 5.2 Comprobar coexistencia de redes propias, sin tocar redes ajenas ni desplegar en DockerServer.
- [x] 5.3 Aprobar el contrato minimo de estado efectivo para ocultar el acceso del chat desactivado antes de producto/tests de UI.
- [x] 5.4 Ocultar el panel sin confirmar activacion y evitar conversaciones vacias/peticiones de generacion; comprobar modo activado mock y autenticacion.
- [x] 5.5 Entregar diff, evidencias focales, limites y respuesta a Victor sin commit/push/publicacion.

5.1: Red detecta la ausencia de las variables; Green de `test_deploy` pasa
19/19. La suite CD afectada pasa 56 casos y omite los dos controles POSIX
heredados en Windows. `init` y `prepare` reales renderizan ambos slots con
Compose, conservando HMAC, red interna, loopback y chat desactivado. Mutar
la asignacion para ignorar el slot hace fallar la nueva regresion. La
coexistencia real de 5.2 estuvo pendiente de liberar una red ajena. Tras
retirarla PM con autorizacion de Paris, las dos redes propias se crean a
la vez con los pools exactos y se retiran sin tocar otros recursos.

5.3-5.5: contrato aprobado directamente por Paris antes de producto/tests.
Backend 32/32, frontend afectado 120/120, tres typechecks y build pasan;
lint conserva un aviso previo. Navegador con backend real, SQLite y
processor controlado verifica off/on/off, sin POST ni conversaciones
vacias en off, y una sola pareja persistida en on. No acredita DockerServer
ni proveedor real. Ver [entrega y limites](../../../docs/evidence/JUP-122-review-fixes-20261014.md).
