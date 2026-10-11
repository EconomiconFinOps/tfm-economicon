# Demo de alertas de anomalías de coste con datos sintéticos

**Todos los importes de esta guía son datos sintéticos**: los genera [`scripts/synthetic_anomalies.py`](../../../scripts/synthetic_anomalies.py), no son facturas de Azure y no proceden del dataset público. Existen para enseñar cómo se comportan las reglas de [JUP-030](../../api/cost-anomalies.md); no demuestran que la detección acierte con gasto real ni explican causas.

Esta guía es la segunda parte de JUP-107 (la primera, [guion.md](guion.md), recorre el dashboard de costes con los datos de JUP-106). Los valores esperados están en [`esperados-anomalias.json`](esperados-anomalias.json) y una prueba los recalcula con suma exacta.

## Qué se enseña

Se llama al endpoint `POST /billing/anomalies/evaluate` y se leen las siete evaluaciones y las dos alertas que devuelve. No hay pantalla para esto: el panel `/anomalies` de la aplicación sigue mostrando datos de demostración fijos (un fixture del frontend) y no lee este endpoint, así que **no refleja estas alertas**. Tampoco sirve `/docs` (Swagger): la ruta exige la cabecera `X-Tenant-Id`, que esa página no ofrece.

## Preparación

Usa un stack aislado, con volúmenes nuevos, para no mezclar estos datos con los de otras demos. Desde la raíz del repositorio:

```sh
docker compose -p jup107b build
docker compose -p jup107b up -d --wait --wait-timeout 900
```

Si RabbitMQ sale con `eacces` o el processor aún no está sano, repite el mismo `up -d --wait`.

**Si usas PowerShell:** no existe el operador `<`. Todos los comandos de esta guía que lo llevan (`apply`, `status`, `remove` y la llamada al endpoint) se escriben con una tubería: `Get-Content -Raw <fichero> | docker compose -p jup107b exec -T <servicio> python - <argumentos>`. Por ejemplo, para cargar los datos: `Get-Content -Raw scripts/synthetic_anomalies.py | docker compose -p jup107b exec -T processor python - apply`, y para la llamada: `Get-Content -Raw scripts/call_anomalies_demo.py | docker compose -p jup107b exec -T backend python -`. Las consultas a CockroachDB no llevan `<` y valen igual.

1. Comprueba que `tenant-core` no tiene costes (debe devolver 0 filas). Si tuviera la ingesta del dataset público, la herramienta se negará a cargar:
   ```sh
   docker compose -p jup107b exec -T cockroachdb ./cockroach sql --insecure -d defaultdb -e "SELECT count(*) FROM azure_cost_records WHERE tenant_id = 'tenant-core'"
   ```
2. Carga los datos y comprueba su estado (`status` debe decir `present`, 1 ingesta y 22 registros sintéticos, y 0 datos reales). `apply` es idempotente: repetirlo responde `already-present`.
   ```sh
   docker compose -p jup107b exec -T processor python - apply < scripts/synthetic_anomalies.py
   docker compose -p jup107b exec -T processor python - status < scripts/synthetic_anomalies.py
   ```

## La petición de referencia

Dos periodos consecutivos de siete días, uno por servicio y en euros, con estas reglas: umbral absoluto de 2000,00, subida del 50 % frente al periodo anterior y un incremento mínimo de 100,00.

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

| Servicio | Actual | Base | Diferencia | Alerta | Por qué |
| --- | --- | --- | --- | --- | --- |
| Compute | 2400,00 | 1000,00 | +1400,00 (140,00 %) | **Sí** | Supera el umbral (2400 ≥ 2000) y sube más de un 50 % y más de 100,00: las dos razones |
| Analytics | 2300,00 | 2200,00 | +100,00 (4,55 %) | **Sí** | Solo supera el umbral; la subida es del 4,55 %, muy por debajo del 50 % |
| Storage | 820,00 | 800,00 | +20,00 (2,50 %) | No | Estable: por debajo del umbral y sin subida relevante |
| Database | 1200,00 | 1500,00 | −300,00 (−20,00 %) | No | Baja: una bajada nunca dispara la regla de subida |
| Tools | 40,00 | 10,00 | +30,00 (300,00 %) | No | Sube un 300 %, pero solo 30,00, por debajo del incremento mínimo de 100,00 |
| Backup | 300,00 | 0,00 | +300,00 | No | La base es un cero registrado: no se puede calcular un porcentaje (`baseline_nonpositive`) |
| Networking | 600,00 | sin datos | — | No | Servicio nuevo sin periodo anterior (`baseline_missing`) |

Además: el estado de la evaluación es `provisional` y la completitud `not_verified` (el servicio no verifica cobertura diaria ni frescura de la fuente), ambos periodos tienen estado `available` con 0 registros sin servicio, y cada alerta lleva `cause_status: not_established`. Al repetir la petición los identificadores de alerta y de evidencia no cambian.

### Dos variaciones que enseñan las reglas (opcional)

Se cambia un campo de la petición de referencia y se vuelve a llamar:

- Con `deviation_threshold_percent` en `4.55`, sin umbral absoluto y conservando `min_absolute_increase` en `100.00`, Analytics **no** salta; con `4.54` sí. El porcentaje mostrado (4,55) está redondeado: la comparación se hace antes de redondear (100,00 sobre 2200,00 es 4,5454… %).
- Con solo la regla de subida (quita `absolute_threshold`) y `min_absolute_increase` en `30.00`, Tools pasa a ser alerta: el incremento mínimo es lo que la frenaba.

## Limitaciones que hay que decir

- Los importes son inventados para ilustrar las reglas; no se ha medido la calidad de la detección ni se afirma que un caso real se comporte igual.
- Las alertas son candidatos a investigar, no una causa ni un ahorro demostrado.
- El panel `/anomalies` no muestra estos datos (ver arriba); verlas ahí es un cambio posterior con su propia tarjeta.
- Mientras estén cargados, `tenant-core` deja de estar vacío: la demo de JUP-065 y los recorridos que lo suponen vacío no deben usarlo a la vez.

## Vuelta al estado inicial

```sh
docker compose -p jup107b exec -T processor python - remove < scripts/synthetic_anomalies.py
docker compose -p jup107b exec -T processor python - remove < scripts/synthetic_anomalies.py
docker compose -p jup107b exec -T processor python - status < scripts/synthetic_anomalies.py
docker compose -p jup107b exec -T cockroachdb ./cockroach sql --insecure -d defaultdb -e "SELECT count(*) FROM azure_cost_records WHERE tenant_id = 'tenant-core'"
docker compose -p jup107b down -v
```

El segundo `remove` debe retirar 0 ingestas y 0 registros (es seguro repetirlo); `status` debe decir `absent` y la consulta devolver 0. `down -v` borra el stack y sus volúmenes. La herramienta solo retira sus propias filas: los datos de JUP-106 en `tenant-growth` no se tocan. `remove` actúa sobre todos los tenants a la vez y no acepta `--tenant` (sale con error); `status` te dice en cuál estaba el conjunto.
