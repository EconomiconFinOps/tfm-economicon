## Context

El simulador de Azure sirve el fixture público `EA-Cost-Actual.sample.csv` (junio de 2024, USD) y la ingesta lo persiste en `azure_cost_ingestion_runs` y `azure_cost_records` (migraciones del processor 002 a 004). `/billing/summary` agrega esas tablas por tenant, periodo semiabierto, moneda y dimensión, y solo cuenta ingestas `completed`. Los usuarios demo pertenecen a `tenant-core` (con los datos de junio de 2024) y `tenant-growth` (sin costes). La proposal de JUP-106 explica el motivo.

Existe precedente de insertar costes directamente para pruebas (`apps/backend/tests/billing_support.py`) y de scripts de verificación en `scripts/` con pruebas en `scripts/tests/` (JUP-067, retrieval-calibration). Los contenedores tienen el sistema de ficheros de solo lectura, por lo que un script puntual se pasa por la entrada estándar (`docker compose exec -T processor python - <args>`).

## Goals / Non-Goals

**Goals:**

- Que quien valida pueda cargar con un comando un conjunto conocido de datos de varios meses y retirarlo con otro, sobre un stack limpio, sin dejar restos.
- Que cada caso límite de los costes tenga un valor esperado escrito y comprobable de forma independiente.
- Que los datos sean inequívocamente sintéticos y nunca se mezclen con el dataset público.

**Non-Goals:**

- Probar la ingesta ni el simulador (cubiertos por JUP-076 y JUP-077) ni cambiar su contrato.
- Producir datos realistas o de volumen; el objetivo es cobertura de casos, no verosimilitud.
- Automatizar el recorrido de navegador ni versionar herramientas de navegador.

## Decisions

**D1. Inserción directa en las tablas de costes, no ampliar el simulador.** Alternativa descartada: añadir un fixture y una suscripción sintéticos al simulador para que los datos entren por la ingesta real. Daría fidelidad de extremo a extremo, pero el simulador y su fixture existen para servir los valores publicados por Microsoft y sus pruebas fijan el checksum y la procedencia; mezclar datos inventados los contaminaría. Además la ingesta no produce filas sin fecha ni importes arbitrarios, que son justo los casos que faltan. La limitación se documenta: esta carga no ejercita la ingesta.

**D2. Tenant `tenant-growth`, con guarda.** Es el único tenant demo sin costes y el usuario demo ya tiene acceso. Un tenant nuevo no sería visible desde la interfaz. Para no ensuciar un tenant que sí tenga datos reales, la herramienta se niega a cargar si el tenant tiene registros no sintéticos, y la retirada borra solo filas sintéticas. Se acepta el riesgo de que `tenant-growth` deje de estar vacío mientras los datos estén cargados; el documento lo avisa.

**D3. Marcado por prefijo reservado.** Los identificadores de ingesta y de registro y los de suscripción llevan el prefijo `synthetic-jup106-`, y el `request` de cada ingesta lleva `{"synthetic": true, "change": "jup-106-synthetic-cost-data"}`. La retirada borra por ese prefijo y comprueba el tenant y el origen, de modo que no depende de fechas ni de importes.

**D4. Un único fichero de herramienta, `scripts/synthetic_costs.py`.** Biblioteca estándar más SQLAlchemy (ya en el processor), subcomandos `apply`, `status` y `remove`, la URL de base de datos tomada de `DATABASE_URL` del entorno y el tenant por argumento con `tenant-growth` por defecto. El conjunto de datos es una constante Python (determinista, sin reloj ni azar) y el documento lo describe con una tabla. Alternativa descartada: un fichero JSON o SQL aparte; añade un segundo sitio donde mantener los valores sin ventaja.

**D5. Conjunto de datos (2026, tenant `tenant-growth`).** Dos suscripciones sintéticas (`-sub-a`, `-sub-b`) y dos ingestas completadas.

| Mes | EUR | USD | Qué ejercita |
| --- | --- | --- | --- |
| Enero | 100,00 en dos registros, grupo de recursos `Web` y `web` | sin datos | un mes con coste y fusión de mayúsculas del grupo de recursos |
| Febrero | 0,00 (cero registrado) | 10,50 | cero registrado frente a hueco; dos monedas |
| Marzo | sin datos | sin datos | hueco en todas las monedas |
| Abril | 40,00 en dos registros, uno sin servicio, grupo de recursos ni etiquetas | sin datos | dimensiones ausentes |
| Mayo | -50,00 (crédito) | sin datos | importe negativo |
| Junio | sin datos | 25,25 | moneda con meses distintos |
| Julio | sin datos | 9007199254740993,01 | importe por encima de `Number.MAX_SAFE_INTEGER` |
| Sin fecha | 7,77 (un registro sin fecha de uso) | | recuento de registros sin fecha |

Valores derivados: comparación del primer y último mes con coste distinto de cero en EUR (enero y mayo, febrero queda fuera por ser cero): -150,00 EUR y -150,00 %; en USD de enero a junio (febrero y junio): +14,75 USD y +140,48 %; total de enero a julio en EUR 90,00 y en USD 9007199254741028,76 (suma exacta de 10,50, 25,25 y 9007199254740993,01). El registro sin fecha no entra en los importes ni en la comparación y se cuenta como excluido. Las etiquetas (`cost_center`, `project`) y los servicios se reparten para que cada agrupación tenga más de un grupo.

**D6. Valores esperados independientes.** El documento y las pruebas llevan los totales escritos a mano y la prueba los compara con una suma exacta con `Decimal` sobre los registros del conjunto; nunca con la agregación del backend ni con el código de la herramienta. La prueba de extremo a extremo compara después `/billing/summary` con esos valores.

**D7. Pruebas en capas.** Pruebas sin base de datos (conjunto, totales, prefijos, guardas, idempotencia con una conexión simulada) que corren en CI con la biblioteca estándar, y una prueba contra una CockroachDB real y desechable (`JUP086_COCKROACH_TEST_URL`, como las de billing) que carga, consulta y retira. Esta última no corre en CI, igual que las demás con servicios reales; se ejecuta en local y se dice en la evidencia.

## Risks / Trade-offs

- **Confundir datos sintéticos con reales.** Mitigado con el prefijo, el marcado de la ingesta, el aviso del documento y la guarda de la herramienta; no se puede eliminar del todo si alguien pega la salida en una demo.
- **Dependencia del esquema.** La herramienta inserta en columnas de las migraciones 002 a 004; un cambio de esquema la rompería. La prueba contra Cockroach real lo detecta al ejecutarla, no en CI; se anota como límite.
- **`tenant-growth` deja de estar vacío.** Algún recorrido (JUP-104) asume que Growth Ops no tiene costes; se avisa y la retirada lo deja como estaba.
- **Cobertura fuera de la interfaz.** Los casos solo son útiles si alguien los recorre; esta tarjeta deja los datos y los valores esperados, y el recorrido de navegador de JUP-055 se hace en su propio PR.

## Open Questions

Ninguna que cambie lo que se construye. Cualquier caso adicional (por ejemplo una tercera moneda) se puede añadir al conjunto sin cambiar el contrato.
