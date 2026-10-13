# Preparación y vuelta al estado inicial

Pasos para dejar lista la demo de [guion.md](guion.md) y para deshacerla. Los datos son **sintéticos**: los costes de JUP-106 en Growth Ops y el conjunto de anomalías de JUP-107 en Core Finance, cada uno con su herramienta; ver [la guía de JUP-106](../../validation/JUP-106-synthetic-costs.md) para qué contiene cada caso.

## Antes de empezar

- Usar un **stack aislado con volúmenes nuevos**, no el de otra tarea. Los ejemplos usan el proyecto `jup107`.
- `-p` aísla contenedores y volúmenes, **no los puertos del equipo**: Compose publica puertos por defecto (frontend 5173, API 8000, processor 8001, Azure simulada 8002). Parar antes cualquier otro stack que los use, o `up` fallará o chocará.
- No cambiar el puerto del frontend sin cambiar también el CORS: el backend solo acepta los orígenes de `CORS_ALLOWED_ORIGINS` (el ejemplo del README del proyecto usa `http://localhost:5173` y `http://127.0.0.1:5173`) y con otro puerto la interfaz no podrá hablar con la API.
- Antes de la declaración del paso D1 no debe haber **cifras en pantalla**: abrir la aplicación en **Anomalías** con **Core Finance** seleccionado (sin cifras en pantalla, porque todavía no se ha detectado). El navegador recuerda el último cliente y periodo, así que tras un ensayo conviene cambiar a Core Finance o abrir una ventana privada. D9 supone además que Core Finance no tiene costes entre enero y junio de 2026 (sus datos de anomalías son de septiembre): se comprueba en el paso 3.
- **No pulsar «Detectar ahora» antes de la demo**: D1 se hace con el panel sin revisar. Si alguien detectó durante un ensayo, retirar y volver a cargar el conjunto de anomalías (paso 5 y paso 2), que borra también sus episodios.
- La demo de JUP-065 y el recorrido de JUP-104 **suponen `tenant-growth` sin costes**. Esta demo lo carga a propósito, así que no se prepara sobre un stack donde esas demos vayan a usarse después sin retirar los datos antes.
- El archivo `.env` se completa como indica el README del proyecto; no se muestra ni se copia en ningún documento. La contraseña de demostración la conoce quien prepara la demo.

## 1. Levantar el stack aislado

Desde la raíz del repositorio:

```sh
docker compose -p jup107 up -d --build --wait --wait-timeout 900
docker compose -p jup107 ps
```

Esperar a que backend, processor, base de datos y frontend estén sanos. La aplicación queda en `http://localhost:5173`.

## 2. Comprobar que el cliente está vacío y cargar los datos

```sh
docker compose -p jup107 exec -T processor python - status < scripts/synthetic_costs.py
docker compose -p jup107 exec -T processor python - apply < scripts/synthetic_costs.py
docker compose -p jup107 exec -T processor python - status < scripts/synthetic_costs.py
```

Esperado: el primer `status` dice `absent` y 0 registros; `apply` dice `loaded: 2 ingestas y 10 registros en tenant-growth`; el último `status` dice `present`. Si el primer `status` informa de datos reales, **parar**: la herramienta se niega a cargar sobre datos que no son sintéticos y no hay que saltarse esa negativa.

En PowerShell no existe `<`: usar `Get-Content -Raw scripts/synthetic_costs.py | docker compose -p jup107 exec -T processor python - apply`.

Después, el conjunto de anomalías en Core Finance (ver [anomalias.md](anomalias.md)):

```sh
docker compose -p jup107 exec -T processor python - apply < scripts/synthetic_anomalies.py
docker compose -p jup107 exec -T processor python - status < scripts/synthetic_anomalies.py
```

Esperado: `loaded: 1 ingestas y 134 registros sinteticos en tenant-core` y después `estado present` con `0 episodios de anomalia`.

## 3. Comprobar los valores antes de la demo

Primero por la API, sin la interfaz. Guardar este fragmento como `resumen.py` **fuera del repositorio** y ejecutarlo dentro del contenedor del backend, que ya tiene la contraseña de demostración en su entorno (el fragmento no la imprime):

```python
import json
import os
import urllib.request

BASE = "http://localhost:8000"
TENANT = os.environ.get("TENANT", "tenant-growth")


def call(path, data=None, headers=None):
    body = json.dumps(data).encode() if data is not None else None
    request = urllib.request.Request(BASE + path, data=body, headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


access = call("/auth/login", {"email": "operator@example.com", "password": os.environ["DEMO_PASSWORD"]})["access_token"]
summary = call("/billing/summary?start_date=2026-01-01&end_date=2026-07-01&group_by=service",
               headers={"Authorization": "Bearer " + access, "X-Tenant-Id": TENANT})
print("data_status:", summary["data_status"])
for total in summary["totals"]:
    print(total["currency"], total["cost"], total["record_count"])
```

```sh
docker compose -p jup107 exec -T backend python - < resumen.py
docker compose -p jup107 exec -T -e TENANT=tenant-core backend python - < resumen.py
```

En PowerShell: `Get-Content -Raw resumen.py | docker compose -p jup107 exec -T backend python -` (y la misma línea con `-e TENANT=tenant-core` antes de `backend`).

Con los datos cargados debe imprimir exactamente `data_status: partial` (por el registro sin fecha y el que no tiene dimensión), `EUR 90.00 6` y `USD 35.75 2`. El periodo es semiabierto: termina el 1 de julio, así que julio no entra. La segunda orden consulta Core Finance entre enero y junio y debe imprimir solo `data_status: empty`; si no, hay costes en Core Finance en ese periodo y D9 no vale (se corrige el stack, no el guion). En la interfaz, el panel de Anomalías de Core Finance debe decir «Todavía no se han buscado anomalías en este cliente».

Después, por la interfaz: entrar en `http://localhost:5173` con la cuenta de demostración, elegir Growth Ops, poner Mes inicial 2026-01 y Mes final 2026-06 y agrupar por Servicio. Deben salir los valores del paso D3 de [guion.md](guion.md): 90.00 EUR (6 registros) y 35.75 USD (2 registros). La [receta de navegador](receta-navegador.md) hace esta comprobación y la del resto de pasos automáticamente sobre los valores de [esperados.json](esperados.json).

## 4. Hacer la demo

Seguir [guion.md](guion.md). Si hay que repetirla, recargar la página y volver a poner el periodo; no hace falta tocar los datos.

## 5. Volver al estado inicial

```sh
docker compose -p jup107 exec -T processor python - remove < scripts/synthetic_anomalies.py
docker compose -p jup107 exec -T processor python - remove < scripts/synthetic_costs.py
docker compose -p jup107 exec -T processor python - remove < scripts/synthetic_costs.py
docker compose -p jup107 exec -T processor python - status < scripts/synthetic_costs.py
docker compose -p jup107 exec -T backend python - < resumen.py
```

Esperado: el `remove` de anomalías retira su ingesta, sus registros y los episodios de Core Finance; el primer `remove` de costes dice `Retiradas 2 ingestas y 10 registros sinteticos.`; el segundo, `Retiradas 0 ingestas y 0 registros sinteticos.`; el `status` final, `absent` y 0 registros; y `resumen.py` imprime solo `data_status: empty`. Con la página de la demo recargada, el dashboard de Growth Ops para 2026-01 a 2026-06 muestra «Sin datos de costes para este periodo.».

Para terminar, parar el stack y borrar sus volúmenes:

```sh
docker compose -p jup107 down -v
```

## Si algo no coincide

- `status` dice `partial` u `other-tenant`: ejecutar `remove` y volver a cargar.
- Los totales de D3 no son los esperados: comprobar el periodo (la pantalla arranca con los seis últimos meses completos) y que se ha elegido Growth Ops.
- Un `apply` simultáneo de otra persona sobre el mismo stack no duplica datos, pero el que pierde la carrera ve un error genérico; repetir el comando.
