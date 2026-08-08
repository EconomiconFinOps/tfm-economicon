# Evidencia de validación JUP-077

Fecha: 2026-08-08  
Rama local: `test/JUP-077-azure-cost-e2e`  
Commit desplegado y validado: `e81b898`  
Publicación remota: no realizada

## Alcance validado

- dataset público de ejemplo → Azure Cost fake API;
- recorrido de las tres páginas por el cliente de JUP-076;
- normalización de coste, moneda, fecha y dimensiones;
- migraciones y persistencia en CockroachDB;
- repetición idempotente de la misma ejecución;
- estado fallido y ausencia de filas parciales ante un `401` controlado;
- logs estructurados sin token Bearer.

## Pruebas locales

```text
scripts/tests:       8 passed
apps/azure-cost-api: 34 passed, 1 warning de deprecación de TestClient
apps/processor:      34 passed
apps/backend:        7 passed, 2 warnings de longitud de clave en fixture de test
git diff --check:    sin errores
```

La suite del backend requirió reemplazar el dominio reservado `.local` del dato
de prueba por `example.com`. No se cambió el comportamiento de autenticación.

## Despliegue aislado

Host: `dockerserver`  
Directorio: `/home/danteadmin/economicon-deployments/jup-077-e81b898`  
Proyecto Compose: `economicon-jup077`

Servicios:

```text
economicon-jup077-azure-cost-api-1  healthy  0.0.0.0:18004->8002
economicon-jup077-cockroachdb-1     healthy  0.0.0.0:26257->26257
```

El build del processor usó un contexto de 70,60 kB y terminó correctamente.
Se ajustó Compose para que la pila sea autocontenida sin exigir un `.env`
ignorado, use almacenamiento persistente y permita conectividad SQL en la red
interna. La conexión utiliza `sqlalchemy-cockroachdb` con psycopg 3.

## Recorrido correcto e idempotencia

La misma orden se ejecutó dos veces:

```text
python -m app.run_azure_cost_ingestion \
  --tenant-id tenant-e2e \
  --subscription-id 64e355d7-997c-491d-b0c1-8414dccfcf42
```

Ambas devolvieron el mismo identificador y el mismo resumen:

```json
{
  "page_count": 3,
  "persisted_row_count": 30,
  "retry_count": 0,
  "row_count": 30,
  "run_id": "cdbc4aad-c920-5918-9ffb-1fefecb2ff25",
  "status": "completed",
  "tenant_id": "tenant-e2e"
}
```

Tras la segunda ejecución CockroachDB conserva exactamente 30 filas, no 60.
Las fechas persistidas abarcan del `2024-06-02` al `2024-06-19`.

## Error controlado

Se repitió el recorrido con otro tenant y un Bearer inválido. El proceso terminó
con código `1` y salida segura:

```json
{"error_code": "AzureCostHttpError", "status": "failed"}
```

Estado final consultado directamente en CockroachDB:

```text
tenant-e2e        completed  pages=3  rows=30  error=NULL
tenant-e2e-error  failed     pages=0  rows=0   error=AzureCostHttpError
```

La ejecución fallida tiene cero filas asociadas. Los logs contienen evento,
tenant, ruta, página, métricas e identificador de ejecución, pero no el Bearer.

## Incidencias descubiertas durante la prueba

1. La entrada Docker de CockroachDB `v24.1.11` rechaza un `--listen-addr`
   personalizado para `start-single-node`. Compose usa directamente el binario,
   una dirección anunciada resoluble en la red y el volumen persistente.
2. El dialecto PostgreSQL genérico de SQLAlchemy no reconoce la cadena de
   versión de CockroachDB. Se añadió el adaptador específico y se cambiaron los
   valores por defecto a `cockroachdb+psycopg://`.

## Pendiente antes de integrar

- confirmación del repositorio remoto oficial;
- acuerdo y creación de `origin/develop`;
- revisión humana según los roles de JUP-076/JUP-077;
- publicación de una rama integradora y draft PR, solo después de lo anterior.
