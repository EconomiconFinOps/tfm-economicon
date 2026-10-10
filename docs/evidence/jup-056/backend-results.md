# JUP-056 — comprobaciones del backend

Verificación: 2026-10-10. Copia aislada `tfm-economicon-jup056`, base `origin/develop` `c2995a1`.

## Contrato aplicado

`GET /billing/summary` mantiene v2 y admite `subscription_id`, `service_name`,
`project`, `filter_tag_key` y `filter_tag_value`. Los filtros se intersectan antes
de sumar importes. Los valores se comparan literalmente, distinguiendo mayúsculas;
el proyecto reutiliza la columna normalizada y, cuando falta, la etiqueta `project`.
La clave de etiqueta usa la canonicalización existente, independiente de la clave
seleccionada para agrupar. Clave y valor deben aparecer juntos. Vacíos, valores
compuestos solo por espacios y caracteres de control se rechazan con 422.

Las respuestas filtradas añaden `filters`, con solo las claves solicitadas y la
clave de etiqueta canónica. Las respuestas sin filtros conservan su JSON anterior.
Los importes siguen siendo `Decimal` en SQL/Python y cadenas con dos decimales;
no se suman monedas diferentes. Todos los valores de filtros son parámetros SQL.

La autorización del tenant ocurre antes de leer costes. El conflicto entre fuentes
se comprueba sobre el tenant y periodo completos: un filtro no puede esconderlo.
`missing_dimension_count` describe las filas filtradas; `excluded_undated_count`
sigue siendo global al tenant, como en el contrato previo.

## Entorno

- Windows; Python 3.14.4; pytest 9.0.3.
- FastAPI 0.115.12; Pydantic 2.12.5; SQLAlchemy 2.0.52.
- sqlalchemy-cockroachdb 2.0.4; psycopg 3.2.13.
- Docker Server 29.6.2; imagen `cockroachdb/cockroach:v24.1.11`.
- Contenedor temporal exclusivo `economicon-jup056-tests`, almacenamiento en
  memoria de 1 GiB, sin volumen persistente, puerto remoto de loopback 28556.
  Túnel SSH al mismo puerto local. Los fixtures verifican el marcador de cluster
  `processor-integration-tests` y crean/borran solo sus bases con nombre aleatorio.

## Ejecuciones

Desde `apps/backend`:

```powershell
$env:JUP086_COCKROACH_TEST_URL = '<DSN local del contenedor aislado, sin credenciales reales>'
python -m pytest tests/test_billing_filters.py tests/test_billing_summary.py -q
# Sin la variable anterior: batería unitaria y skips explícitos de integraciones.
python -m pytest tests -q --basetemp '<directorio temporal nuevo y exclusivo>'
python -m compileall -q app
```

El primer intento dentro del sandbox no llegó a ejecutar los casos: 19 errores
de preparación por `PermissionError` en el directorio temporal global de pytest,
y 11 integraciones omitidas al no configurar el DSN. No constituye evidencia de
fallo funcional ni de éxito. Se repite con ejecución autorizada y temporales propios.

Estado provisional: pruebas en ejecución; recuentos finales y limpieza pendientes.
No acredita revisión, validación ni aceptación humana de la tarjeta.
