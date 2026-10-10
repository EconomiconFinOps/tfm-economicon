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

La ejecución dirigida con Cockroach terminó con **26 passed y 4 errores de
preparación** en 689,99 s. Los cuatro comparten un único timeout de 60 s al
arrancar las migraciones del processor para el módulo nuevo; no ejecutaron sus
aserciones. Los 11 casos nuevos de frontera HTTP y los 15 casos originales
(incluidos sus siete casos SQL reales) pasaron.

Se repitieron exclusivamente los cuatro casos SQL nuevos con `-k cockroach -x
--tb=short` y un directorio temporal nuevo: **4 passed, 11 deselected** en 145,58 s.
Un wrapper efímero dentro del proceso amplió de 60 a 300 s únicamente la llamada
`subprocess.run` del fixture cuyo `cwd` termina en `processor`; las migraciones,
aserciones y fuentes versionadas permanecieron iguales. Comando reproducible,
con el DSN de pruebas establecido como arriba:

```powershell
python -c "import subprocess, sys, pytest; original_run = subprocess.run; subprocess.run = lambda *args, **kwargs: original_run(*args, **{**kwargs, **({'timeout': 300} if kwargs.get('timeout') == 60 and str(kwargs.get('cwd', '')).endswith('processor') else {})}); raise SystemExit(pytest.main(['tests/test_billing_filters.py', '-k', 'cockroach', '-q', '-x', '--tb=short', '--basetemp', sys.argv[1]]))" '<directorio temporal nuevo>'
```

Los casos SQL acreditan filtros AND, ausencia de coincidencias, valores con
metacaracteres SQL, separación de tenants con igual suscripción, proyecto de
fallback, claves distintas al agrupar y filtrar etiquetas, importes mayores que
el límite entero seguro de JavaScript, reembolso `-1.01`, cero redondeado y suma
`10.004 + 2.004 = 12.01` antes de redondear. También comprueban que el filtro no
oculta el 409 por solapamiento.

La batería completa local se interrumpió por indicación de coordinación tras
confirmar el éxito completo de CI Linux; no se atribuye un recuento final al intento
interrumpido. Se diagnosticó un fallo independiente
en el fixture sin red de JUP-047: parchea `socket.socket.connect`, y el event loop
de Windows/Python 3.14 utiliza ese método para crear su `socketpair` interno antes
de despachar la petición ASGI. Reproducción aislada: `python -m pytest
tests/test_health_provider_admission_jup047.py -q -x --tb=short --basetemp
'<directorio temporal nuevo>'`: **1 failed** en 6,86 s, con `Only controlled gateway
doubles are permitted in Red`. Los archivos `test_health_provider_admission_jup047.py`
y `test_secret_boundaries.py` no tienen cambios respecto a `c2995a1`; no se modifican
en esta tarjeta. Esto no equivale a ejecutar toda la suite sobre la base original.

Limpieza comprobada: `SHOW DATABASES` solo mostró `defaultdb`, `postgres` y
`system` tras los fixtures. Se retiraron el contenedor exclusivo y el túnel SSH;
ningún volumen ni servicio compartido se modificó. Se retiraron también los dos
directorios `pytest-cache-files-*` creados por el intento fallido, verificando sus
rutas absolutas dentro de esta copia antes del borrado.

## Control completo en CI

El [job backend de PR #99](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035433148/job/114164767451)
terminó con `success` para `f1e0dd6f5231276b19e685203fda2c3a8c3b2f4a` el
2026-10-10 a las 09:47:32 Europe/Paris. El log y metadatos se leyeron mediante
`gh api repos/EconomiconFinOps/tfm-economicon/actions/jobs/114164767451/logs`
y el endpoint del job.

- Runner `ubuntu-latest`, Python 3.12.15, pytest 9.1.1.
- FastAPI 0.143.0, Pydantic 2.14.0, SQLAlchemy 2.0.54, psycopg 3.3.6,
  sqlalchemy-cockroachdb 2.0.4.
- `python -m compileall -q app`: PASS.
- `python -m pytest tests -q`: **909 passed, 38 skipped**, 2364 warnings,
  106,75 s. Las integraciones omitidas no se presentan como probadas por CI;
  los once casos SQL de facturación se verificaron por separado como se detalla arriba.
- Compilación local `python -m compileall -q app`: PASS, salida 0.

Limitaciones: no despliegue compartido, ingesta Azure real, llamada a proveedor LLM
ni validación humana. La incompatibilidad del fixture de red JUP-047 con el
socketpair de Windows queda fuera de este delta; la suite completa verde corresponde
al entorno Linux de CI, no al intento Windows interrumpido.

No acredita revisión, validación ni aceptación humana de la tarjeta.
