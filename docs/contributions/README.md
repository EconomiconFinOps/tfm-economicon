# Contribuciones y roles rotatorios

JUP-064 · [Trello](https://trello.com/c/wluz6AGW). El proceso de los cuatro roles
se mantiene en [CONTRIBUTING](../../CONTRIBUTING.md#rotating-roles).

El [registro fechado](JUP-064-register.md) enlaza las acciones observadas de los
cuatro miembros por historia, los commits, PR, reviews, comentarios de PR,
pruebas y documentación.
El [snapshot reducido](JUP-064-snapshot.json) permite reproducir el registro sin
conexión. No contiene credenciales, emails, conversaciones ni cuerpos de reviews.
Conserva autores públicos, enlaces, SHA, fechas, estados y líneas de roles.
El informe muestra hasta doce acciones por persona e historia y tres artefactos
por tipo y PR; el snapshot conserva todos los enlaces importados.

## Actualizar

Desde la raíz del repositorio, con Python 3.10+, `gh` autenticado en GitHub y SSH
configurado para `DockerServer`:

```sh
python tools/team-contributions.py --collect --snapshot docs/contributions/JUP-064-snapshot.json --output docs/contributions/JUP-064-register.md
python -m unittest discover -s tools/tests -p 'test_team_contributions.py' -v
```

La herramienta solo lee. Toda lectura Trello pasa por la integración Economicon
desplegada en `DockerServer:/home/danteadmin/economicon-collaboration`, mediante
su cliente dentro del contenedor. No usa APIs Trello locales ni otro conector.
Las consultas GitHub paginan PR, commits, reviews, comentarios, archivos y checks. Si falla
una consulta, el comando falla sin sustituir el snapshot por un corte incompleto.
La fecha UTC indica el final de la recogida, no una lectura atómica de ambas fuentes.

Para regenerar sin acceso a las fuentes:

```sh
python tools/team-contributions.py --snapshot docs/contributions/JUP-064-snapshot.json --output docs/contributions/JUP-064-register.md
```

## Interpretación y mantenimiento

- Las asignaciones actuales vienen de Trello; las declaraciones históricas se
  muestran por PR. No se reasignan responsabilidades a partir de un commit.
- Los logins del equipo se contrastaron con autores y secciones Participacion
  de GitHub: Alejandro `Iber1to`, Víctor `Victorh1397`, Lucía `lmatsan`, Paris `ParisArcos`.
  Las identidades desconocidas quedan pendientes; no se deducen de emails.
- La columna de acciones acredita existencia, no suficiencia. Coautoría
  declarada y commits requieren contraste para acreditar pairing efectivo.
- `Revision JUP-XXX` y `Validacion JUP-XXX` deben ocupar la primera línea completa.
  Se conserva el estado y SHA; una review antigua o descartada no satisface el
  indicador de evidencia actual. Las reviews sin título también quedan enlazadas.
- Los comentarios de PR se atribuyen a su autor con enlace y fecha, para
  conservar intervenciones históricas fuera de reviews formales. Su existencia
  no acredita por sí sola revisión, pairing o validación; no se guarda el cuerpo.
- Los checks del HEAD y archivos de pruebas/documentación son evidencia común.
  La validación personal exige leer la review y comprobar criterios, comandos,
  resultados y límites; el recolector no certifica ese contenido ni permite mergear.
- El inventario incluye todas las tarjetas JUP abiertas que devuelve el puente,
  incluso sin PR, y todas las PR del repositorio que se vinculan por título/rama.
  No importa commits fuera de PR, notas de pairing Trello, documentos externos
  ni tarjetas archivadas. Un hueco significa «no importado o por enlazar».
- Si cambian los roles, el líder actualiza Trello y la PR según CONTRIBUTING,
  regenera este corte y explica la diferencia; no se borra la evidencia histórica.
- Antes de cerrar una historia, el líder contrasta los cuatro miembros y enlaza
  la evidencia desde su tarjeta. Antes de la entrega, el equipo resuelve los
  huecos con enlaces originales y resume su contribución en la memoria JUP-062.

## Evidencia manual fuera del recolector

Cuando el pairing consta en una nota Trello o una contribución no pasó por PR,
añadir una fila aquí con historia, persona, rol, fecha, acción concreta, enlace
original y quién la contrastó. No marcarla confirmada hasta contrastarla.

| Historia | Persona / rol | Fecha | Acción | Enlace original | Contraste |
| --- | --- | --- | --- | --- | --- |
| JUP-064 | Alejandro / preparación como coautor | 2026-10-04 | Recolector, matriz, specs, tests y documentación | [Commit a75bcd4](https://github.com/EconomiconFinOps/tfm-economicon/commit/a75bcd4) | Implementación publicada; no acredita sesión de pairing con Víctor |

La fila de implementación se añadió después del corte inicial de las fuentes.
La preparación de JUP-064 por Alejandro no acredita participación de Víctor, Lucía o Paris en esta
historia; liderazgo, revisión y validación permanecen pendientes.
