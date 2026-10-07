# Datos sintéticos de coste (JUP-106)

Conjunto de datos de coste de varios meses de 2026 para validar en la interfaz la funcionalidad de costes que el dataset público no cubre. **Son datos sintéticos: no son facturas de Azure, no proceden del dataset público versionado y no deben usarse en una demo como si lo fueran.** Los registros y las ingestas llevan el prefijo reservado `synthetic-jup106-`, cada ingesta guarda `{"synthetic": true}` en su petición y el simulador y su fixture no se tocan.

## Para qué sirve

El dataset público cubre del 1 al 19 de junio de 2024 y una sola moneda (USD). Con este conjunto se pueden recorrer meses con huecos, un cero registrado, un crédito, dos monedas con meses distintos, un importe fuera del rango seguro de `Number`, dimensiones ausentes, grupos de recursos que solo difieren en mayúsculas y un registro sin fecha. No ejercita la ingesta (se inserta directamente en las tablas de costes, que ya cubren JUP-076 y JUP-077) ni el simulador.

## Cargar, consultar y retirar

Los comandos se ejecutan desde la raíz del repositorio con el stack levantado y se pasan por la entrada estándar al contenedor del processor, que ya tiene `DATABASE_URL`. El tenant por defecto es `tenant-growth` (el único tenant demo sin costes); se cambia con `--tenant`.

```sh
docker compose exec -T processor python - apply < scripts/synthetic_costs.py
docker compose exec -T processor python - status < scripts/synthetic_costs.py
docker compose exec -T processor python - remove < scripts/synthetic_costs.py
```

En PowerShell no existe `<`: `Get-Content -Raw scripts/synthetic_costs.py | docker compose exec -T processor python - apply`. El fichero es solo ASCII para que la codificación de la tubería no lo altere. Con un proyecto Compose aislado, añade `-p <proyecto>` tras `docker compose`.

- `apply` es idempotente: la segunda vez informa `already-present` y no escribe nada. Se niega (salida 2) si el tenant ya tiene datos de coste que no son sintéticos o si hay un estado parcial o en otro tenant; en esos casos hay que ejecutar `remove` primero. La comprobación de datos reales se repite dentro de la transacción de escritura, de modo que una ingesta real que llegue justo antes de escribir también aborta la carga sin dejar nada.
- `status` informa del estado (`absent`, `present`, `partial` o `other-tenant`) y de las filas reales del tenant.
- `remove` borra solo las filas sintéticas, también cuando el tenant tiene datos reales, y es seguro repetirlo. Se niega (salida 2) y no borra nada si hay registros reales colgando de una ingesta sintética, porque la clave foránea impediría borrar la ingesta; hay que resolverlo a mano.

Mientras los datos estén cargados, `tenant-growth` deja de estar vacío (algunos recorridos, como JUP-104, lo suponen vacío de costes): retíralos al terminar. Para probar el recorrido de un tenant sin datos usa `remove`.

## Valores esperados

Tenant `tenant-growth`, dos suscripciones sintéticas (`synthetic-jup106-sub-a` en EUR y `synthetic-jup106-sub-b` en USD) y dos ingestas completadas con diez registros. Los periodos de la API son semiabiertos: el fin es exclusivo.

| Mes (2026) | EUR | USD | Qué ejercita |
| --- | --- | --- | --- |
| Enero | 100,00 (2 registros) | sin datos | grupo de recursos `Web` y `web` que se fusionan en uno |
| Febrero | 0,00 (1 registro) | 10,50 | cero registrado frente a hueco, dos monedas |
| Marzo | sin datos | sin datos | mes sin ningún registro |
| Abril | 40,00 (2 registros) | sin datos | un registro sin servicio, grupo de recursos, proyecto ni etiquetas |
| Mayo | -50,00 (1 registro) | sin datos | crédito (importe negativo) |
| Junio | sin datos | 25,25 | moneda con meses distintos |
| Julio | sin datos | 9007199254740993,01 | importe por encima de `Number.MAX_SAFE_INTEGER` |
| Sin fecha | 7,77 (1 registro) | | recuento de registros sin fecha |

Del 1 de enero al 1 de agosto de 2026: total 90,00 EUR (6 registros) y 9007199254741028,76 USD (3 registros), con un registro sin fecha excluido y estado `partial`. De enero a junio (fin 1 de julio) el total en USD es 35,75 (2 registros). Otros tenants no cambian.

Desglose del mismo periodo, por moneda (el registro sin fecha no entra):

| Agrupación | EUR | USD |
| --- | --- | --- |
| Suscripción | `sub-a` 90,00 (6) | `sub-b` 9007199254741028,76 (3) |
| Servicio | Compute 100,00 (2), Storage 30,00 (2), Credits -50,00 (1), sin servicio 10,00 (1) | Compute 10,50 (1), Storage 9007199254741018,26 (2) |
| Grupo de recursos | Web 100,00 (2), Data -20,00 (3), sin grupo 10,00 (1) | Analytics 9007199254741028,76 (3) |
| Proyecto | Alpha 100,00 (2), Beta -20,00 (3), sin proyecto 10,00 (1) | Alpha 10,50 (1), Beta 9007199254741018,26 (2) |
| Etiqueta `cost_center` | finance 100,00 (2), ops -20,00 (3), sin etiqueta 10,00 (1) | finance 10,50 (1), ops 9007199254741018,26 (2) |

Con agrupación distinta de la suscripción, el recuento de registros sin dimensión es 1.

Comparación entre meses (para quien valide JUP-055 u otra pantalla con comparación). Se toman el primer y el último mes con coste distinto de cero de cada moneda dentro del periodo, y un mes con cero registrado no cuenta como extremo:

| Moneda y periodo | Extremos | Diferencia | Porcentaje |
| --- | --- | --- | --- |
| EUR, enero a mayo | enero (100,00) y mayo (-50,00) | -150,00 | -150,00 % |
| USD, enero a junio | febrero (10,50) y junio (25,25) | +14,75 | +140,48 % |
| USD, enero a julio | febrero (10,50) y julio (9007199254740993,01) | +9007199254740982,51 | importe fuera del rango seguro para dibujar |

Con la pantalla actual de develop (fechas de inicio y fin exclusivo y agrupación), el recorrido con estos datos se comprobó con el mismo resultado que la API: totales por moneda, desglose por cada agrupación, marzo sin datos y febrero con 0,00 EUR y 10,50 USD.

## Cómo se comprobaron estos valores

Se comparan con una suma exacta con `Decimal` sobre los registros del conjunto, escrita a mano en las pruebas, y no con el código de la herramienta ni con la agregación del backend. Después se consulta `/billing/summary` de un stack real y se comparan los totales de cada mes, del periodo completo, de cada agrupación y el recuento de registros sin fecha.

## Límites

- Los datos se insertan en las tablas de costes: una migración que cambie sus columnas puede romper la herramienta. Lo detecta la prueba contra CockroachDB real (`JUP086_COCKROACH_TEST_URL`), que no corre en CI.
- `status` y `apply` deciden `present` solo por los identificadores de las ingestas y los registros: si se cambia a mano un importe u otro campo, siguen diciendo `present` y `already-present`. Para comprobar el contenido, usa `/billing/summary` frente a los valores de arriba o retira y vuelve a cargar.
- `remove` acepta `--tenant` pero lo ignora: retira el conjunto sintético de todos los tenants. Usa `status` para ver en cuál estaba.
- Dos `apply` simultáneos no duplican nada, pero el que pierde la carrera ve un error genérico en lugar de `already-present`; se repite el comando y se informa del estado.
- No hay valores sintéticos para la fecha de ingesta ni se simulan errores del origen; para eso están los escenarios del simulador.
- Las comparaciones del cuadro dependen de cómo cada pantalla elija los extremos; el cuadro es la referencia de la tarjeta JUP-106, no una especificación de JUP-055.
- Una tercera moneda u otros casos pueden añadirse al conjunto sin cambiar el contrato de la herramienta.

## Pruebas

```sh
corepack pnpm synthetic-costs:test
```

Son 46 pruebas. Con `sqlalchemy` instalado pasan 38 y se omiten 8 (las de CockroachDB); en el job de CI, que usa Python 3.12 sin instalar paquetes, pasan 37 y se omiten 9 porque `SqlStoreTests` tampoco corre. **La CI no ejecuta ninguna sentencia de `SqlStore`**: solo comprueba el conjunto de datos, los totales, las guardas y la línea de comandos con un almacén simulado.

Para probar el SQL hace falta una CockroachDB desechable con `JUP086_COCKROACH_TEST_URL=cockroachdb+psycopg://root@127.0.0.1:<puerto>/defaultdb?sslmode=disable` (puerto distinto de 26257 y 5432) y la marca `SET CLUSTER SETTING cluster.organization = 'processor-integration-tests'`. La prueba rechaza cualquier otra URL o un nodo sin la marca, crea su propia base de datos, migra en ella el esquema del processor y la borra al terminar, de modo que no toca `defaultdb` ni deja tablas para las suites del backend y del processor. Con ella pasan las 46.
