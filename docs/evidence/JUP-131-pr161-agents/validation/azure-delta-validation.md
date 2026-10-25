Validacion JUP-131

Revalidación Azure por el agente independiente `/root/pr161_validation`, 24/10/2026. Es un dictamen de agente y no se atribuye a Paris Arcos Martin. Complementa [el informe inicial](validation.md) y [el delta ALB](delta-validation.md), cuyos alcances y dictámenes se mantienen separados.

**Veredicto: PASS para el delta Azure de dos archivos identificado abajo.** En una copia propia del candidato original, siete escenarios reproducen `FrozenInstanceError` al modificar `__traceback__`. Tras aplicar únicamente la corrección de `errors.py`, pasan las 82 pruebas Azure, incluida la nueva regresión. Esto no acredita aceptación completa de la aplicación ni CI del commit posterior.

El coordinador comunicó 41 fallos Azure en la ejecución CI `40133534310` del SHA e730 y solicitó esta ampliación. Este agente no consultó esa CI, el informe del revisor ni los logs de pruebas del coordinador: los resultados siguientes son ejecuciones propias. El defecto se comprobó después del informe inicial de Atlas y no se presenta como un descubrimiento original de aquel alcance.

Snapshot: `2026-10-24T21:36:37.040195Z`, sobre el archivo de fuente exacta `e730dc15fb3feb45a3b346fc9e48332c4608b049`. Se copiaron la app, fixtures públicos y contratos desde la extracción original a `.work/pr161-validation/azure-source/`; se incorporaron sólo los dos archivos del delta. La copia no contiene `.env`.

| Archivo | SHA256 exacto de los bytes probados |
| --- | --- |
| `apps/azure-cost-api/app/errors.py` | `389e2a7c72185d34122c89028c2147e64a0db904ac38190839e3b4844e4a4a48` |
| `apps/azure-cost-api/tests/test_errors.py` | `0cbc76998fdddd661c54c5d2bdc61542507ddcf992dbfebf582a2c0683886678` |

El archivo original `errors.py` tiene SHA256 `2f6612520f6001475ce63e49819c8492e61afd05beb67c9f905d438e0c6ba1a5`; el nuevo test no existe en e730. [Manifiesto del delta](azure-delta-manifest.json).

| Comprobación fresca | Resultado y evidencia |
| --- | --- |
| Regresión `contextlib` con `@dataclass(frozen=True)` original | Falla al restaurar `exc.__traceback__`; queda reproducida la incompatibilidad de la excepción congelada con el manejo de excepciones. |
| Errores HTTP con fuente original | Fallan las seis expectativas 400, 401, 403, 404, 429 y 500 porque Starlette intenta asignar `exc.__traceback__ = None`. Junto a la regresión: **7 FAIL, exit 1**. [RED propio](azure-red-original-errors.log). |
| Suite completa tras incorporar `@dataclass` | **82 PASS, exit 0**, incluida la conservación de la misma instancia `ApiError`, código, mensaje y cabeceras, y los casos de autenticación, paginación, contratos, filtros y resiliencia. [GREEN propio](azure-green-all-tests.log). |

La corrección elimina `frozen=True` y documenta por qué la excepción debe permitir cambios en su traceback. Los campos de respuesta siguen conservándose: el test nuevo comprueba la misma instancia, estado 429 y `Retry-After`; los tests HTTP existentes comprueban los códigos y cuerpos contractuales, `WWW-Authenticate` y `Retry-After`.

Runtime ya instalado por el coordinador y reutilizado sin instalar paquetes: Windows, Python 3.14.4, FastAPI 0.162.0, Starlette 1.10.0, pytest 9.1.1, httpx 0.28.1, Pydantic 2.14.1 y pydantic-settings 2.16.1. Versiones verificadas por este agente en [azure-runtime.log](azure-runtime.log). Se mantiene una advertencia de deprecación de TestClient/httpx; no es un fallo de la suite.

Comandos ejecutados con argumentos separados mediante `azure_delta_validation.py`, desde `.work/pr161-validation/azure-source/apps/azure-cost-api/`:

```text
<runtime>/python.exe -m pytest 
  tests/test_errors.py
  tests/test_resilience.py::test_missing_token_returns_401_with_challenge
  tests/test_resilience.py::test_forbidden_identity_returns_403
  tests/test_resilience.py::test_rate_limit_scenario_returns_retry_after
  tests/test_resilience.py::test_server_error_scenario_returns_500
  tests/test_query_api.py::test_unknown_subscription_uses_azure_error_shape
  tests/test_query_api.py::test_unsupported_api_version_is_a_bad_request
  -q -p no:cacheprovider --basetemp=<carpeta propia>/azure-tmp/red
# 7 failed, 1 warning in 3.06s; exit 1.

<runtime>/python.exe -m pytest tests -q -p no:cacheprovider
  --basetemp=<carpeta propia>/azure-tmp/green
# 82 passed, 1 warning in 1.34s; exit 0.
```

Ejecución fuera del sandbox para evitar el bloqueo de temporales ya observado; `TEMP`, `TMP` y basetemp propios, autoload de plugins desactivado, caché pytest y bytecode desactivados, entorno mínimo sin credenciales. Todas las peticiones son de TestClient dentro del proceso, con datos y tokens sintéticos de fixtures. No hubo Azure/AWS real, red externa, Docker adicional ni repetición SQL/Grafana. Los metadatos completos de comandos, cwd, tiempos y salidas permanecen en `.work/pr161-validation/`.

**Límites:** no se ejecutó esta suite con Python 3.12 ni se consultó CI nueva. La regresión y el resultado completo corresponden exclusivamente a los hashes y dependencias anteriores. Debe comprobarse la CI del commit que integre los cuatro archivos técnicos ALB/Azure; estos dos dictámenes no autorizan despliegue/merge ni actualizan la aceptación general de la receta.
