# Compatibilidad temporal de Azure Cost API

JUP-140 · PR #162 · 2026-10-24.

Se añade únicamente `starlette==1.9.0` a los requisitos de esta API. `ApiError` mantiene `frozen=True`; código, contratos, autenticación, FastAPI y demás rangos permanecen iguales. Es una contención temporal, no una corrección de `ApiError` ni un bloqueo reproducible de todo Python.

Comprobación local Linux/Python 3.12.13: resolución limpia de `requirements-dev.txt`, FastAPI 0.162.0/Starlette 1.9.0, `pip check` conforme y suite existente **81 PASS, 0 FAIL, 0 SKIP**. Imagen construida sin caché con el Dockerfile vigente; requisitos de ejecución también conformes. Se conserva un aviso de deprecación de TestClient/httpx.

Por HTTP real entre contenedores propios: normal con paginación, 401/403, 429 y `Retry-After`, 500, retardo y escenarios del smoke nativo; demo con health, OpenAPI idéntico, consulta de fecha presente en su CSV y errores 401/429. Ambos healthchecks conformes, usuario sin privilegios y raíz de solo lectura. No se contactó Azure ni otros proveedores.

Normal y demo usan el mismo Dockerfile y requisitos; demo cambia sólo el CSV configurado. Los contenedores existentes necesitan reconstrucción para incorporar el pin y no fueron modificados. Landing, backend, processor, Grafana, CI y Compose conservados; no se repitieron sus suites. Estos resultados locales no acreditan CI remota, despliegue ni ausencia universal de regresiones.
