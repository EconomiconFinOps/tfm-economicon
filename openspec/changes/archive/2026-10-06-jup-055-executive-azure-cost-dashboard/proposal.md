JUP: JUP-055
Trello: https://trello.com/c/UbyhMsNF

## Why

El panel ejecutivo de `/` combina el resumen almacenado de JUP-026 con
tarjetas, tendencias y exportación de demostración. JUP-055 debe presentar
gasto, desglose y variación observados para el ámbito activo con un intervalo
mensual comprensible, conservando el aspecto de la aplicación.

Fuente de alcance: contexto verificado por el Coordinador el 06/10/2026.
Base local: `048837278bb063d6ee3abafcdb0b71c51b560f94`.
Rama: `feat/JUP-055-executive-azure-cost-dashboard`.
Proceso: `CONTRIBUTING.md#review-and-validation-flow`, versión 2026-09-30 (JUP-100).

## What Changes

- Sustituir el contenido de demostración del panel ejecutivo por totales por
  moneda, desglose de todo el intervalo, serie mensual y comparación entre
  el **primer y último mes del intervalo con coste registrado no cero de cada moneda**.
- Seleccionar inicio y fin como meses inclusivos, con cualquier intervalo
  válido; el valor inicial son los últimos seis meses completos en UTC.
- Reutilizar `GET /billing/summary` v2: una consulta de todo el intervalo para
  totales/desglose y una por mes para tendencia/comparación, sin sumar meses
  redondeados como total autoritativo.
- Mantener cantidades exactas, monedas separadas, créditos y cero observado;
  distinguir ausencia, error, parcialidad y datos de una selección anterior.
- Conservar Layout, tarjetas, controles, tokens y gráficos existentes, con
  comportamiento accesible en escritorio y móvil.
- Actualizar solamente la documentación del recorrido ejecutivo y sus
  instrucciones de validación.

No se incluyen cambios de backend, contratos, ingesta, autenticación,
dependencias de producción, migraciones, paletas, forecast, presupuestos,
facturas, cálculo de ahorro ni filtros de cuenta/suscripción inexistentes.
No se implementa una exportación real: se retira la exportación de demostración
del panel junto con su inventario ficticio. Las otras pantallas y
`/overview-legacy` conservan su alcance.

## Capabilities

### New Capabilities

- `executive-cost-dashboard`: selección mensual inclusiva, presentación
  observada por moneda, tendencia mensual, comparación de meses con coste no cero y estados
  honestos bajo la sesión y el ámbito activos.

### Modified Capabilities

Ninguna. Se consumen los contratos vigentes de JUP-026 y el armazón existente;
no se modifica la política de separación de demostración de otras pantallas.

## Impact

Producto previsto: `apps/frontend/src/pages/ExecutiveCostDashboard.tsx`,
un hook de consulta ejecutivo y utilidades pequeñas de meses/importes en el
frontend. La ubicación definitiva se confirma en Red/Green con un encargo de
rutas concreto. Se reutilizan los servicios y contratos de facturación,
React Query y Recharts ya presentes. Tests de página/hook/utilidades y
regresiones afectadas; `apps/frontend/README.md` para la documentación mínima.

El README contiene información antigua y el paquete identifica posibles
trabajos concurrentes JUP-104/JUP-105. El Coordinador debe reconciliar la
edición mínima antes de Green; este cambio no presume el contenido de JUP-105.

## Gates

Las aprobaciones inicial y de disposición/datos se conservan más abajo. El criterio nuevo de comparación fue aprobado; esta revisión técnica requiere su gate antes de nuevos cambios de tests/producto.
Los escenarios, tareas y evidencia prevista se detallan en
[design.md](design.md), [tasks.md](tasks.md) y
[spec](specs/executive-cost-dashboard/spec.md).

Tras las comprobaciones documentales, el Coordinador solicitará a Paris
aprobación explícita del alcance y diseño. Después: Red, Green y mutación en
encargos separados; revisión técnica y validación funcional independientes;
evidencia y aprobación humana postvalidación. El archivado requiere
autorización explícita y se hace en la misma rama antes de solicitar las dos
reviews de GitHub, conforme a CONTRIBUTING. Las reviews humanas y el merge
siguen pendientes entonces y requieren sus permisos propios.


## Refinamiento solicitado por Paris — 06/10/2026

Situar «Desglose del periodo» como primer resultado inmediatamente debajo de
los controles de meses/agrupación y avisos aplicables, antes de totales,
comparación y tendencia. El orden visual coincide con la lectura accesible.
«Agrupar por» sigue agrupando solo el desglose; no filtra las finanzas globales
ni añade controles o cálculos.

Preparar, en fase posterior autorizada y fuera del repositorio, datos sintéticos
de la DB local desechable con dos suscripciones, servicios, proyectos y grupos
de recursos EUR. Repartir los mismos costes mensuales para mostrar diferencias
reales entre agrupaciones; conservar moneda, tenant, cero/créditos y caso de
precisión USD. El diseño incluye filas y esperados independientes, versionado
de referencia y plan de revalidación; ninguna escritura de datos se realiza
en analysis-design.

El refinamiento de disposición y datos obtuvo la aprobación histórica registrada a continuación. Layout/proxy y límites del informe de validación anterior siguen pendientes fuera de ese alcance.


## Comparación por meses con coste no cero — criterio de 06/10/2026

Paris aprobó expresamente el nuevo criterio transmitido por el Coordinador
el 06/10/2026 a las 10:54:35. Esta revisión sustituye operativamente los extremos
seleccionados y la base cero de la versión inicial: elegir, para cada moneda,
primer y último mes del intervalo con coste registrado distinto de cero,
incluyendo negativos, y mostrar inequívocamente los meses efectivos.

Cero y ausencia se omiten únicamente para elegir la comparación. Totales y
desglose siguen cubriendo todo el intervalo; tendencia/tabla retienen todos
los meses (año completo: doce), ceros observados y huecos sin conectar.
Uno/ninguno elegible se explican sin cifras comparativas; errores y metadata
inválida no se convierten en ausencia. El diseño detalla errores interiores
frente a errores que impiden determinar extremos y los avisos partial.

No se modifica producto, tests, README o DB en este encargo. Diseño técnico,
mapa de sustitución de tests, plan documental y referencias de comparación v2
requieren su gate y despachos secuenciales. Las dos aprobaciones históricas
conservadas a continuación no se borran ni se editan para aparentar aprobación
de esta revisión. El criterio está aprobado; el Coordinador presentará el
diseño validado antes del siguiente gate de código.


## Aprobación humana pre-código — 06/10/2026

Paris Arcos ha aprobado explícitamente este diseño en el chat Coordinador, después de confirmar que incluye el selector de mes inicial y final: «apruebo entonces».
Registrado por el Coordinador el 06/10/2026 a las 01:28 Atlantic/Canary. La aprobación cubre el alcance y escenarios de esta versión; autoriza pruebas e implementación secuenciales bajo controles Red/Green/mutación. No autoriza publicaciones, archivo, merge ni cambios en Trello oficial.

## Aprobación humana del refinamiento pre-código — 06/10/2026

Paris Arcos aprobó expresamente el diseño validado y el plan de datos v2 en este chat Coordinador: «aprobado».
Registrado por el Coordinador el 06/10/2026 a las 10:37:17 Atlantic/Canary.
Cubre una única instancia del desglose inmediatamente después del selector/avisos, antes de totales/comparación/tendencia, sin cambiar cálculos ni semántica de agrupación; y datos sintéticos EUR v2 en la DB desechable exclusiva, con dos suscripciones, servicios, proyectos y grupos de recursos, preservando totales mensuales, monedas, tenants y evidencia v1.
Autoriza las fases secuenciales acotadas de pruebas, implementación y preparación de datos con sus controles y revalidación afectada. No autoriza reparación del Layout compartido, proxy de latencia, publicaciones, archivado, merge ni cambios en Trello oficial. Las limitaciones de validación anteriores siguen pendientes.


## Aprobación humana de comparación pre-código — 06/10/2026

Paris Arcos aprobó expresamente el diseño validado presentado en el chat Coordinador: «aprobado».
Registrado por el Coordinador el 06/10/2026 a las 11:19:11 Atlantic/Canary.
Cubre primer y último mes con coste observado distinto de cero por moneda, incluidos negativos, precisión exacta y meses efectivos; conservación del rango completo en totales, tablas y gráficas; mensajes de uno/ninguno; errores que impiden extremos sin comparación numérica y errores interiores con aviso explícito, así como avisos de parcialidad.
Autoriza pruebas e implementación secuenciales Red/Green/mutación y documentación afectada del diseño comparison-design-1; conserva el plan de datos v2 y aprobaciones anteriores. No autoriza reparación del Layout compartido, proxy, publicaciones, archivado, merge ni cambios en Trello oficial.

## Registro pre-code aprobado

Resumen de autorizaciones históricas, sin nuevas aprobaciones: Paris aprobó el
diseño inicial («apruebo entonces», registrado el 06/10/2026 a las 01:28
Atlantic/Canary), disposición/datos («aprobado», 10:37:17) y comparación
(«aprobado», 11:19:11). Se conservan arriba sus bloques originales y límites.
No otorgan autorización de publicación, archivado ni aprobación postvalidación.
Proxy y entornos de prueba se autorizaron posteriormente para validación local;
el Layout compartido conserva el finding RF-026-002 sin reparación autorizada.
