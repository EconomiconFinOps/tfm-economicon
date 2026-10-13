# Demo de alertas de anomalías de coste con datos de demostración

**Todos los importes de esta guía son datos sintéticos**: los genera [`scripts/demo_dataset.py`](../../../scripts/demo_dataset.py) y se cargan con [`scripts/demo_data.py`](../../../scripts/demo_data.py) por la ingesta del processor; no son facturas de Azure y no proceden del dataset público. Existen para enseñar cómo se comportan las reglas de la consulta de prueba de [JUP-030](../../api/cost-anomalies.md) y la regla diaria de negocio de los [episodios de JUP-114](../../api/anomaly-episodes.md); no demuestran que la detección acierte con gasto real ni explican causas.

Esta guía es la segunda parte de JUP-107 (la primera, [guion.md](guion.md), recorre el dashboard de costes). Los valores esperados están en [`esperados-anomalias.json`](esperados-anomalias.json) y una prueba los recalcula con aritmética exacta, sin usar el backend. El conjunto tiene un registro por servicio y día del 1 de julio al 30 de octubre de 2026: julio y agosto son una base tranquila, las cifras del 1 al 21 de septiembre son las de siempre (las dos primeras semanas son los periodos de la consulta de prueba) y del 22 de septiembre al 30 de octubre hay más variaciones. **Qué se ve depende de la fecha de referencia**: esta guía usa `COST_REFERENCE_DATE=2026-09-21` (las cifras de JUP-107) y la sección [Avanzar la fecha](#avanzar-la-fecha-de-referencia) enseña qué cambia con `2026-10-30`.

## Qué se enseña

Dos cosas con los mismos datos:

1. **La consulta de prueba** `POST /billing/anomalies/evaluate`: compara los totales de dos semanas con reglas que se mandan a mano y devuelve siete evaluaciones y dos alertas. No guarda nada y no tiene pantalla; tampoco sirve `/docs` (Swagger), porque la ruta exige la cabecera `X-Tenant-Id`, que esa página no ofrece.
2. **El panel `/anomalies`**: al pulsar «Detectar ahora» aplica la regla diaria de negocio al coste de cada día y guarda episodios; el panel los enseña priorizados por criticidad (ver [En el panel](#en-el-panel-episodios-con-la-regla-diaria)).

Son reglas distintas y dan resultados distintos: la consulta mira semanas enteras con umbrales que se eligen; el panel mira día a día con la regla fija de negocio.

## Preparación

Usa un stack aislado, con volúmenes nuevos, para no mezclar estos datos con los de otras demos. Pon `COST_REFERENCE_DATE=2026-09-21` en el `.env` y, desde la raíz del repositorio:

```sh
docker compose -p jup107b build
docker compose -p jup107b up -d --wait --wait-timeout 900
```

Si RabbitMQ sale con `eacces` o el processor aún no está sano, repite el mismo `up -d --wait`.

**Si usas PowerShell:** no existe el operador `<`. La llamada al endpoint, que lo lleva, se escribe con una tubería: `Get-Content -Raw scripts/call_anomalies_demo.py | docker compose -p jup107b exec -T backend python -`. Los comandos de carga (`demo_data.py`) y las consultas a CockroachDB no llevan `<` y valen igual.

1. Comprueba que `tenant-core` no tiene costes (debe devolver 0 filas). Si tuviera costes que no son los de la demo, el cargador se negará a cargar:
   ```sh
   docker compose -p jup107b exec -T cockroachdb ./cockroach sql --insecure -d defaultdb -e "SELECT count(*) FROM azure_cost_records WHERE tenant_id = 'tenant-core'"
   ```
2. Carga los datos y comprueba su estado (`status` debe decir `present` en `tenant-core` y en `tenant-growth`). `apply` carga el conjunto completo de la demo y es idempotente: repetirlo responde `already-present`.
   ```sh
   docker compose -p jup107b --profile demo run --rm demo-data python scripts/demo_data.py apply
   docker compose -p jup107b --profile demo run --rm demo-data python scripts/demo_data.py status
   ```

## La petición de referencia

Dos periodos consecutivos de siete días, uno por servicio y en euros, con estas reglas (la fecha de referencia debe ser el 21/09/2026 o posterior, porque la consulta de prueba solo acepta días cerrados): umbral absoluto de 2000,00, subida del 50 % frente al periodo anterior y un incremento mínimo de 100,00.

```json
{
  "start_date": "2026-09-08",
  "end_date": "2026-09-15",
  "group_by": "service",
  "currency": "EUR",
  "absolute_threshold": "2000.00",
  "deviation_threshold_percent": "50.00",
  "min_absolute_increase": "100.00"
}
```

El periodo anterior (del 1 al 7 de septiembre de 2026, ambos incluidos) lo calcula el servicio. Para ejecutarla, el script [`scripts/call_anomalies_demo.py`](../../../scripts/call_anomalies_demo.py) hace login con el usuario demo, llama al endpoint y muestra el resultado sin imprimir la contraseña ni el token:

```sh
docker compose -p jup107b exec -T backend python - < scripts/call_anomalies_demo.py
```

## Qué debe verse

Dos alertas y cinco evaluaciones sin alerta, cada una por una rama distinta de la lógica. El endpoint devuelve los grupos y las alertas ordenados alfabéticamente (Analytics antes que Compute); la tabla los ordena de más a menos llamativo:

| Servicio   | Actual  | Base      | Diferencia          | Alerta | Por qué                                                                                    |
| ---------- | ------- | --------- | ------------------- | ------ | ------------------------------------------------------------------------------------------ |
| Compute    | 2400,00 | 1000,00   | +1400,00 (140,00 %) | **Sí** | Supera el umbral (2400 ≥ 2000) y sube más de un 50 % y más de 100,00: las dos razones      |
| Analytics  | 2300,00 | 2200,00   | +100,00 (4,55 %)    | **Sí** | Solo supera el umbral; la subida es del 4,55 %, muy por debajo del 50 %                    |
| Storage    | 820,00  | 800,00    | +20,00 (2,50 %)     | No     | Estable: por debajo del umbral y sin subida relevante                                      |
| Database   | 1200,00 | 1500,00   | −300,00 (−20,00 %)  | No     | Baja: una bajada nunca dispara la regla de subida                                          |
| Tools      | 40,00   | 10,00     | +30,00 (300,00 %)   | No     | Sube un 300 %, pero solo 30,00, por debajo del incremento mínimo de 100,00                 |
| Backup     | 300,00  | 0,00      | +300,00             | No     | La base es un cero registrado: no se puede calcular un porcentaje (`baseline_nonpositive`) |
| Networking | 600,00  | sin datos | —                   | No     | Servicio nuevo sin periodo anterior (`baseline_missing`)                                   |

Además: el estado de la evaluación es `provisional` y la completitud `not_verified` (el servicio no verifica cobertura diaria ni frescura de la fuente), ambos periodos tienen estado `available` con 0 registros sin servicio, y cada alerta lleva `cause_status: not_established`. Al repetir la petición los identificadores de alerta y de evidencia no cambian.

### Dos variaciones que enseñan las reglas (opcional)

Se cambia un campo de la petición de referencia y se vuelve a llamar:

- Con `deviation_threshold_percent` en `4.55`, sin umbral absoluto y conservando `min_absolute_increase` en `100.00`, Analytics **no** salta; con `4.54` sí. El porcentaje mostrado (4,55) está redondeado: la comparación se hace antes de redondear (100,00 sobre 2200,00 es 4,5454… %).
- Con solo la regla de subida (quita `absolute_threshold`) y `min_absolute_increase` en `30.00`, Tools pasa a ser alerta: el incremento mínimo es lo que la frenaba.

## En el panel: episodios con la regla diaria

Con los datos cargados, entra en la aplicación, elige **Core Finance** y abre **Anomalías**. Antes de detectar, el panel dice «Todavía no se han buscado anomalías en este cliente» y enseña el aviso «Datos sintéticos de demostración: no son facturas reales». Pulsa **Detectar ahora**: el resultado dice que se revisó hasta el 20/09/2026 (con la referencia en el 21/09 ese es el último día con datos visibles y se considera incompleto) y que hay 3 anomalías nuevas.

| Servicio | Criticidad | Impacto acumulado | Periodo | Observación |
| --- | --- | --- | --- | --- |
| Compute | Alta (P1) | 2807.71 EUR en 12 días | 09/09 → 20/09 | Se sigue observando |
| Database | Media (P2) | 642.86 EUR en 5 días | 16/09 → 20/09 | Se sigue observando |
| Analytics | Baja (P3) | 168.86 EUR en 4 días | 10/09 → 10/09 | Ya no se observa desde 14/09 |

Por qué el resto no abre anomalía, aunque la consulta de prueba diga otra cosa:

- **Analytics** salta en la consulta de prueba por su total semanal (supera el umbral de 2000,00), pero día a día solo tiene un pico el 10 de septiembre: abre un episodio pequeño que deja de observarse a los cuatro días.
- **Tools** sube un 300 %, pero cada día solo unos céntimos sobre lo esperado: la regla exige además más de 100 al día.
- **Backup** pasa de cero a 300 un solo día: con una referencia cero no hay porcentaje, y el gasto nuevo desde cero no abre episodio.
- **Networking** aparece el 14 de septiembre sin gasto previo: mismo caso que Backup.
- **Storage** se mantiene estable.

Abre el detalle de Compute: enseña la referencia, el impacto, las reglas y «Candidata: causa no establecida». Desde ahí se puede marcar en investigación o cerrar con un motivo.

### Opcional: pedir la explicación en el asistente (JUP-038)

No forma parte de los tres minutos del [guion](guion.md) (que no cambia); es un paso aparte de unos 40 segundos para quien pregunte «¿por qué se marcó esta?».

1. En el detalle de Compute pulsa **Explicar en el asistente**. El enlace solo navega: abre `/assistant?episode=…` y no envía nada.
2. Si no hay ninguna conversación, pulsa **Nueva**. El redactor aparece con **Explicar una anomalía** activado, la anomalía de Compute ya elegida y la pregunta «¿Por qué se ha marcado esta anomalía?» propuesta. Sigue sin enviarse nada.
3. Pulsa **Enviar**. La respuesta no la redacta un modelo: es una explicación determinista con las cifras del episodio.

Con estos datos debe leerse: el 2026-09-09 el coste observado fue **377.00 EUR** frente a una referencia de **142.86 EUR** al día, subió **234.14 EUR (163.90 %)**, el impacto acumulado es **2807.71 EUR en 12 días**, criticidad **Alta (P1)**, estado «Nueva. Se sigue observando» y, al final, el aviso de datos sintéticos. Database y Analytics salen con sus cifras de la tabla de arriba. Despliega **Evidencia de la anomalía** y **Operandos exactos** para enseñar que las cifras se pueden recalcular (los operandos salen con 12 decimales, tal como los guarda la base).

Lo que hay que decir: es un candidato para investigar, **no** una causa ni un ahorro; la explicación solo cubre el día de apertura y los acumulados; no usa embeddings ni modelo, así que funciona aunque pgvector esté caído. Al cambiar el estado de la anomalía y volver a explicarla, la explicación nueva lleva otro identificador y la anterior se conserva tal cual. Ejemplo real y comprobaciones: [anomaly-explanations.md](../../api/anomaly-explanations.md#ejemplo-real) y [la evidencia de JUP-038](../../evidence/JUP-038-validation.md).

## Avanzar la fecha de referencia

Con `COST_REFERENCE_DATE=2026-10-30` (y recreado el backend) el panel enseña lo mismo que la demo de [guion.md](guion.md): al pulsar **Detectar ahora** dice «Revisado hasta el 29/10/2026» (el 30 es el último día con datos y se considera incompleto) y salen cinco anomalías. Las tres de arriba siguen ahí con sus cifras actualizadas; Compute y Database ya no se observan, y aparecen Storage (subida sostenida desde el 20/10) y Tools (un pico el 08/10):

| Servicio | Criticidad | Impacto acumulado | Periodo | Observación |
| --- | --- | --- | --- | --- |
| Compute | Alta (P1) | 5851.57 EUR en 28 días | 09/09 → 03/10 | Ya no se observa desde 07/10 |
| Storage | Media (P2) | 1230.00 EUR en 10 días | 20/10 → 29/10 | Se sigue observando |
| Database | Media (P2) | 642.86 EUR en 8 días | 16/09 → 20/09 | Ya no se observa desde 24/09 |
| Analytics | Baja (P3) | 168.86 EUR en 4 días | 10/09 → 10/09 | Ya no se observa desde 14/09 |
| Tools | Baja (P3) | 144.00 EUR en 4 días | 08/10 → 08/10 | Ya no se observa desde 12/10 |

Una sola pulsación revisa todos los días pendientes hasta el último completo. Al retroceder la fecha, las anomalías que llegan más allá de ella se ocultan y reaparecen al volver a avanzarla; para repetir la demo desde cero se retiran y se vuelven a cargar los datos.

## Limitaciones que hay que decir

- Los importes son inventados para ilustrar las reglas; no se ha medido la calidad de la detección ni se afirma que un caso real se comporte igual.
- Las alertas son candidatos a investigar, no una causa ni un ahorro demostrado.
- La consulta de prueba y el panel aplican reglas distintas (semanas con umbrales a mano frente a días con la regla de negocio): no hay que presentar sus resultados como la misma cosa.
- «Detectar ahora» guarda episodios: para repetir la demo desde cero hay que retirar y volver a cargar los datos.
- Mientras estén cargados, `tenant-core` deja de estar vacío: la demo de JUP-065 y los recorridos que lo suponen vacío no deben usarlo a la vez.

## Vuelta al estado inicial

```sh
docker compose -p jup107b --profile demo run --rm demo-data python scripts/demo_data.py remove
docker compose -p jup107b --profile demo run --rm demo-data python scripts/demo_data.py remove
docker compose -p jup107b --profile demo run --rm demo-data python scripts/demo_data.py status
docker compose -p jup107b exec -T cockroachdb ./cockroach sql --insecure -d defaultdb -e "SELECT count(*) FROM azure_cost_records WHERE tenant_id = 'tenant-core'"
docker compose -p jup107b exec -T cockroachdb ./cockroach sql --insecure -d defaultdb -e "SELECT count(*) FROM anomaly_episodes WHERE tenant_id = 'tenant-core'"
docker compose -p jup107b --profile demo down -v
```

El segundo `remove` debe retirar 0 ingestas y 0 registros (es seguro repetirlo); `status` debe decir `absent` y las dos consultas devolver 0: `remove` borra también los episodios y la marca «Revisado hasta» del cliente, porque salen de estos datos (**no** borra las conversaciones: las explicaciones pedidas en el asistente se conservan con su evidencia aunque el episodio ya no exista) (si el cliente tuviera otros costes, los conserva y lo dice). `down -v` borra el stack y sus volúmenes. El cargador solo retira las filas de las suscripciones de la demo, en los dos clientes a la vez: `remove` no acepta `--tenant` (sale con error) y `status` te dice en qué estado está cada cliente.
