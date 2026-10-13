# JUP-055 — evidencia local de entrega

Fecha: 06/10/2026. Rama: `feat/JUP-055-executive-azure-cost-dashboard`.
HEAD/base: `048837278bb063d6ee3abafcdb0b71c51b560f94`.
Los resultados corresponden al contenido de trabajo todavía sin commit, no a
un commit de entrega. La base remota se consultó en lectura y coincidía.

[Tarjeta oficial](https://trello.com/c/UbyhMsNF).
Proceso: CONTRIBUTING.md, versión 2026-09-30 (JUP-100).
Roles de tarjeta confirmados el 06/10: liderazgo Paris Arcos Martin,
pairing Victor Mendez, revisión Alejandro Aguado y validación Lucia Mateo.
La asignación no acredita participación realizada. Revisión técnica local y
ejecución funcional automatizada son evidencias distintas de las reviews humanas.

## Alcance comprobado

Dashboard conectado a registros almacenados mediante `/billing/summary`, con
selector inclusivo de meses, desglose del periodo inmediatamente bajo los
controles, total por moneda, evolución mensual y comparación del primer/último
mes observado con coste exacto no cero. Se mantienen ceros y huecos en toda la
serie, créditos y monedas separadas. No hay conversión de moneda ni previsión.
Se reutiliza el estilo y los componentes existentes; no se cambia backend,
contrato, dependencias de producción o migraciones.

## Revisión, pruebas y sensibilidad

Revisión técnica independiente del conjunto: REVIEW_PASS; observación de estado
documental OpenSpec reconciliada por el coordinador, conservando gates abiertos.
Red de la comparación: 28 fallos de comportamiento esperados y 50 pases sobre el
producto anterior, antes de aplicar el cambio. Dos flags de comparación de texto
se corrigieron en fase de tests separada; la sensibilidad contra el producto
anterior se repitió y mantuvo esos 28 fallos.

Green vigente: 78/78 tests enfocados, 516/516 frontend en 49 archivos; typecheck,
lint y build con exit 0. La mutación manual autorizada en copia desechable detectó
21/21 defectos introducidos en la comparación; es una muestra controlada, no una
puntuación exhaustiva de un motor de mutación. Los casos de orden del desglose
detectaron 3/3 defectos introducidos en la fase anterior.

La muestra inicial de periodo/cohortes detectó 18/19. El superviviente que
retiraba `retry: false` se clasificó equivalente para las respuestas HTTP
modeladas: los errores se convierten en resultados y la query resuelve sin
rechazar. La revisión independiente examinó esa clasificación. No se afirma
equivalencia universal ni se retiró esa protección del producto.

Warning de build: chunk JavaScript superior a 500 kB (759,81 kB; gzip 218,66 kB),
sin fallo de build; no se amplía arquitectura por este aviso.

## Ejecución funcional actual

Entorno Docker desechable con backend real y datos sintéticos v2 almacenados:
21 registros, tres ingestas completadas y dos clientes. No son facturas Azure
comerciales. Errores/demoras y 401 se provocaron mediante proxy local acotado;
las respuestas normales procedieron del backend. Capturas y trazas identifican
los escenarios. No se extrapola esta evidencia al servidor compartido.

| Escenario | Resultado y observado |
| --- | --- |
| Default 06/10/2026 | PASS: abril–septiembre UTC; 420 EUR y 9007199254741008.03 USD; comparación mayo→septiembre −90 EUR / −225%. |
| Cambio de año y zona | PASS: reloj 2027-01-01T00:30Z en UTC, Los Ángeles y Kiritimati inicia julio–diciembre 2026; 80 EUR y 9007199254741008.03 USD. |
| Febrero–agosto | PASS: siete meses, 660 EUR y 25.03 USD; febrero→agosto +50 EUR / +50%. |
| Agrupaciones | PASS: servicio, proyecto, suscripción, grupo de recursos y etiqueta modifican el desglose y conservan total/comparación. EUR por servicio 455/205; por proyecto 345/315; por suscripción 415/245. |
| Comparación anual | PASS: febrero 100→septiembre −50 EUR, −150 EUR / −150%; ceros y meses sin datos permanecen en la serie. |
| Exactitud/multimoneda | PASS: USD septiembre 9007199254740993.01 conserva céntimos; punto no representable se excluye del gráfico con aviso y permanece exacto en tabla. |
| Cero, mes único, rango vacío/invertido, sin datos | PASS: estados diferenciados, sin ceros inventados; rangos inválidos no generaron consultas. |
| 503 interior/metadatos incompatibles | PASS: mes en error y hueco; agregado y comparación observada válidos se conservan con aviso. |
| Error más allá del último coste | PASS: comparación suprimida al no poder acreditar extremo; agregado conservado. |
| 409 y recuperación | PASS: aviso de solapamiento sin resultado sustitutivo; reintento tras retirar el error recupera importes correctos. |
| Carga/aislamiento/concurrencia | PASS en carreras provocadas: montos anteriores ocultos, máximo tres peticiones por cohorte; cambio a Growth deja 2998 EUR sin datos Core. |
| Respuesta tardía | PASS: respuesta anual retenida no reemplaza el rango febrero–agosto ya completado. Abandono del cliente no certifica cancelación física del backend. |
| Sin sesión | PASS: contexto nuevo termina en login; cero consultas de perfil o costes. |
| 401 en consulta de costes | PASS de invalidación UI simulada: login y aviso de expiración; ninguna nueva consulta billing después de redirigir, consultas anteriores abandonadas. Token backend no revocado. |
| Dimensión ausente | PASS: etiqueta inexistente informa ocho registros sin dimensión, estados parciales e importes intactos. |
| Fila sin fecha | PASS: una fila NULL de 777.77 EUR excluida de importes; recuento global 1 repetido por mes sin sumarse y comparación parcial explícita. |
| Límite 9998-12 | PASS: año conservado, periodo futuro/sin datos señalado sin costes inventados. |
| Teclado/escritorio | PASS de observaciones: foco visible y controles etiquetados; a 1440×900 ancho de documento 1425/1425, sin overflow raíz. |
| Móvil 390×844 | FAIL visual heredado: ancho raíz 1026; reproducido en rutas vecinas. RF-026-002 abierto; no se declara responsive global superado. |

La fila sin fecha se retiró después de la prueba. Los snapshots completos antes
y después son idénticos byte a byte, SHA256
`8DA4620411092060F5B530F6EA3446FADBC0AB5C160EC89BA559828143720DB8`.
Los controles independientes de repositorio/Git pasaron contra referencias
originales. Detectan cambios de estado final; no certifican aislamiento técnico
ni escrituras transitorias restauradas.

## Comprobaciones generales del repositorio

Ejecutadas el 06/10/2026 sobre copia externa de las mismas 827 fuentes, sin
cambiar producto ni pruebas: veinte comandos de gobernanza, OpenSpec 46/46 y
build global nativo (cuatro tareas), todos con exit 0.

| Suite | Superadas | Omitidas | Fallos |
| --- | ---: | ---: | ---: |
| Frontend vigente, ejecución global actual | 516 | 0 | 0 |
| Azure cost API, Linux Python 3.12 | 59 | 0 | 0 |
| Backend, Linux Python 3.12 | 578 | 28 | 0 |
| Processor, Linux Python 3.12 | 448 | 57 | 0 |

Total: 1601 superadas y 85 omitidas. Los 78 tests enfocados son un subconjunto,
no se suman. `corepack pnpm test`, `corepack pnpm lint` y `corepack pnpm typecheck`
se ejecutaron después mediante Turbo nativo sin caché: exit 0 en los tres;
4/4 tareas de test, 4/4 lint y 1/1 typecheck. Frontend 516/516 volvió a ejecutarse,
igual que las tres suites Python. Un adaptador externo de ejecución enruta Python
a los contenedores Linux 3.12 ya autorizados, conserva argumentos/directorios y
propaga sus exits reales; no modifica scripts, manifests ni configuración del
repositorio. Estos resultados sustituyen la equivalencia histórica inicial.

Las omisiones conservan las condiciones nativas: servicios/URLs opcionales de
CockroachDB, pgvector y RabbitMQ y opt-in Docker LiteLLM. CI no configura esos
servicios. Siete casos omitidos de billing-summary Cockroach están relacionados
con el contrato consumido; las observaciones funcionales de dimensiones,
parcialidad, vacío y cero son independientes y no acreditan esos siete tests.
El 409 actual fue simulado por proxy, no provocado por conflicto real en DB.
Los otros 78 corresponden a integraciones fuera del frontend modificado.

Gobernanza/build: Windows Node 24/pnpm 9; CI usa Ubuntu Node 22. Suites Python:
Linux 3.12, misma familia que CI. No se declara ejecución de CI remoto.
Las comprobaciones posteriores a esta consolidación se registran aparte;
los cambios solo documentales no invalidan la evidencia de comportamiento.

## Correspondencia con criterios oficiales

| Criterio de tarjeta | Evidencia local / fase pendiente |
| --- | --- |
| Resultado funcional | Escenarios actuales de la tabla anterior; responsive global limitado por RF-026-002. |
| Pruebas | Red, Green, mutación y matriz general; 85 skips conservados como no ejecutados. |
| Documentación y decisiones | README, proposal/design/spec/tasks y esta evidencia; no nueva decisión arquitectónica. |
| PR enlazada y revisada | Pendiente de publicación autorizada y review humana de Alejandro. |
| Validación funcional enlazada | Ejecución independiente local registrada; validación humana de Lucia posterior a archive y PR. |

## Límites y decisiones pendientes

- RF-026-002: desbordamiento del Layout compartido también presente en otras
  rutas; Paris pidió registrarlo como finding, sin cambio de código. Paris aprobó
  el cierre con este límite el 06/10/2026; no es un PASS visual.
- 401 repetido de `/me` observado durante bootstrap por 5,5 segundos mantuvo
  pantalla de carga y cero billing; no demuestra un fallo permanente ni expiración
  real del token. Es distinto del escenario 401 billing que sí pasó.
- CI remota, PR y reviews humanas aún no ejecutadas en esta fase. Pairing real
  de Victor no se acredita mediante asignación ni agentes internos.
- Matriz general completada; control documental posterior registrado por separado.
- Aprobación humana postvalidación y autorización específica de archivo: concedidas por Paris el 06/10/2026 («aprobado», registro 15:33:40 Atlantic/Canary).

OpenSpec archivado el 06/10/2026 en la misma rama; no se ha publicado una PR.

## Capturas de ejecución

- [clock-los-angeles.png](jup-055/clock-los-angeles.png): escenario actual registrado, datos sintéticos.
- [billing-401.png](jup-055/billing-401.png): escenario actual registrado, datos sintéticos.
- [undated-partial.png](jup-055/undated-partial.png): escenario actual registrado, datos sintéticos.

## Decisión postvalidación

Paris aceptó expresamente el cierre local con RF-026-002 y autorizó archivar.
El finding sigue Open/Medium; los 85 skips no cambian de resultado. La decisión
no sustituye las reviews humanas ni acredita responsive global. El control
final previo al archivado y la comprobación posterior se conservan con la
revisión del cambio.

## Archivo verificado

[Revisión archivada](../../openspec/changes/archive/2026-10-06-jup-055-executive-azure-cost-dashboard/review.md).
[Especificación canónica](../../openspec/specs/executive-cost-dashboard/spec.md).
Las reviews humanas y CI remota siguen pendientes de su fase posterior.

## Corrección incremental de PR #77 — 06/10/2026

Este apartado actualiza el estado histórico anterior: la PR #77 ya existe.
Responde a la solicitud de cambios de Lucía sobre el mes observado aislado:
https://github.com/EconomiconFinOps/tfm-economicon/pull/77#pullrequestreview-5433439585.
Proceso aplicado: CONTRIBUTING.md, versión 2026-09-30 (JUP-100).

### Alcance y reproducción

Se añade un marcador visible a cada observación mensual del gráfico existente,
con el mismo color y radio del estilo actual. Se mantiene `connectNulls={false}`:
los meses sin observación no generan puntos ni uniones. Un cero registrado sí
es una observación. No cambian importes, monedas, consultas ni tablas.

Se reprodujo el fallo del mes aislado dentro de un intervalo con huecos. El
control de un único mes seleccionado ya mostraba un punto antes de la corrección;
no se presenta ese control como un fallo reproducido.

### Resultados comprobados sobre la corrección local

| Comprobación | Resultado |
|---|---|
| Regresión con Recharts real, antes de implementar | 8 fallos relevantes y 2 controles nuevos correctos; 78 pruebas anteriores correctas. |
| Regresión tras implementar | 88/88: 10 pruebas nuevas y 78 anteriores. |
| Suite completa del frontend | 526/526, sin omisiones. |
| Suite del workspace | 1611 correctas y 85 omitidas por el perfil existente; las 88 focales están incluidas, no se suman. |
| Compilación, lint y comprobación de tipos | Correctos. |
| Cuatro mutaciones manuales en copia desechable | Las cuatro fueron detectadas por las pruebas. |
| Revisión técnica local independiente | Favorable para este alcance. |
| Validación independiente | 88/88 y comprobaciones de navegador descritas a continuación. |

En navegador integrado se seleccionó mayo–agosto de 2024, con una única
observación en junio: USD 0,06 y EUR 0,00 en sus selecciones respectivas.
Ambas mostraron un punto visible, sin unir los meses vacíos y conservando
los valores de las tablas. Se comprobó también junio–junio, el cambio de
moneda y la navegación de teclado entre los selectores de meses.
Los datos fueron sintéticos, servidos localmente; no se consultó facturación real.

Los casos 503 e importe no representable se comprobaron con las pruebas
focales; no se afirma haber repetido esos errores en navegador. La comparación
sigue sin calcularse cuando no hay dos meses con coste distinto de cero.
El marcador fue visible a 1440 y 390 píxeles; esto no corrige ni acredita el
responsive global: RF-026-002 permanece con la disposición ya aprobada.
Las imágenes SVG reconstruidas durante la validación no se incorporan como
capturas originales. No se generaron nuevos PNG de esa validación.

La revisión y validación locales no modificaron el repositorio ni Git, según
los controles independientes de integridad al retorno. Estas comprobaciones
locales no sustituyen la revalidación humana de Lucía sobre el siguiente head.

### Aprobación y estado de entrega

Paris concedió la aprobación final local con «aprobado» el 06/10/2026, tras
presentarse los resultados de la revisión y validación incrementales.
OpenSpec continúa archivado en el mismo cambio; esta corrección restaura un
comportamiento ya especificado y no amplía el alcance.
En este registro la corrección aún no tiene commit ni está subida: la CI del
nuevo head y la revalidación de Lucía se comprobarán después de la actualización
autorizada de la PR. La aprobación local no autoriza por sí sola la publicación.