# Preparación y vuelta al estado inicial

Pasos para dejar lista la demo de [guion.md](guion.md) y para deshacerla. Los datos son **de demostración**: sintéticos, o del dataset público de Microsoft con las fechas desplazadas a 2026. Los genera `scripts/demo_data.py` (el generador está en `scripts/demo_dataset.py`) y entran por el mismo camino que cualquier coste: API de Azure simulada → ingesta del processor → base de datos. Ver [la guía de datos](../../data/azure-sample-dataset.md) para qué contiene cada conjunto.

## Antes de empezar

- Usar un **stack aislado con volúmenes nuevos**, no el de otra tarea. Los ejemplos usan el proyecto `jup107`.
- `-p` aísla contenedores y volúmenes, **no los puertos del equipo**: Compose publica puertos por defecto (frontend 5173, API 8000, processor 8001, Azure simulada 8002). Parar antes cualquier otro stack que los use, o `up` fallará o chocará.
- No cambiar el puerto del frontend sin cambiar también el CORS: el backend solo acepta los orígenes de `CORS_ALLOWED_ORIGINS` (el ejemplo del README del proyecto usa `http://localhost:5173` y `http://127.0.0.1:5173`) y con otro puerto la interfaz no podrá hablar con la API.
- **Fecha de referencia:** la demo supone `COST_REFERENCE_DATE=2026-10-30` (el último día con datos). Hay que ponerla en el `.env` antes de levantar el stack; la cabecera de la aplicación dirá «Fecha simulada: 30/10/2026». Con otra fecha las cifras de los pasos no coinciden.
- Antes de la declaración del paso D1 no debe haber **cifras en pantalla**: abrir la aplicación en **Anomalías** con **Core Finance** seleccionado (sin cifras en pantalla, porque todavía no se ha detectado). El navegador recuerda el último cliente y periodo, así que tras un ensayo conviene cambiar a Core Finance o abrir una ventana privada.
- **No pulsar «Detectar ahora» antes de la demo**: D1 se hace con el panel sin revisar. Si alguien detectó durante un ensayo, retirar y volver a cargar los datos (pasos 5 y 2), que borra también sus episodios.
- La demo de JUP-065 y el recorrido de JUP-104 **suponen `tenant-growth` sin costes**. Esta demo lo carga a propósito, así que no se prepara sobre un stack donde esas demos vayan a usarse después sin retirar los datos antes.
- El archivo `.env` se completa como indica el README del proyecto; no se muestra ni se copia en ningún documento. La contraseña de demostración la conoce quien prepara la demo.
- Los datos solo traen servicio y etiqueta `Project`. La cobertura de etiquetas, los responsables por centro de coste, propietario o aplicación y el desglose por grupo de recursos no tienen datos en esta demo y no forman parte del recorrido.

## 1. Levantar el stack aislado

Desde la raíz del repositorio, con `COST_REFERENCE_DATE=2026-10-30` en el `.env`:

```sh
docker compose -p jup107 up -d --build --wait --wait-timeout 900
docker compose -p jup107 ps
```

Esperar a que backend, processor, base de datos y frontend estén sanos. La aplicación queda en `http://localhost:5173`. Este `up` **no carga datos**.

## 2. Comprobar que los clientes están vacíos y cargar los datos

El perfil `demo` de Compose levanta una segunda API simulada que sirve el CSV de demo y un cargador de un solo uso. Los comandos son los de `demo_data.py`:

```sh
docker compose -p jup107 --profile demo run --rm demo-data python scripts/demo_data.py status
docker compose -p jup107 --profile demo run --rm demo-data python scripts/demo_data.py apply
docker compose -p jup107 --profile demo run --rm demo-data python scripts/demo_data.py status
```

Esperado: el primer `status` dice `tenant-core: absent` y `tenant-growth: absent`; `apply` termina con `loaded: 7 parejas tenant/suscripcion con datos sinteticos o de fechas desplazadas, no son facturas de Azure.`; el último `status` dice `present` en los dos clientes. Si el primer `status` informa `other-data`, **parar**: el cargador se niega a cargar sobre costes que no son los suyos y no hay que saltarse esa negativa. La carga completa tarda unos 25 segundos medidos en un equipo de desarrollo.

`demo_data.py` solo carga o retira con `RUNTIME_ENVIRONMENT=development` o `test` (valor exacto, en minúsculas); con cualquier otro valor, o sin él, se niega. También trata como datos ajenos una ingesta del dataset público original de una de sus suscripciones y no la borra. En PowerShell los comandos valen igual: no usan `<`.

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
summary = call("/billing/summary?start_date=2026-07-01&end_date=2026-10-01&group_by=service",
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

Con los datos cargados la primera orden debe imprimir exactamente `data_status: partial` (por el registro sin servicio), `EUR 61580.74 370` y `USD 0.87 70`. El periodo es semiabierto: termina el 1 de octubre, así que octubre no entra. La segunda orden consulta Core Finance y debe imprimir `data_status: available` y `EUR 79337.00 569`. En la interfaz, el panel de Anomalías de Core Finance debe decir «Todavía no se han buscado anomalías en este cliente» y la cabecera, «Fecha simulada: 30/10/2026».

Después, por la interfaz: entrar en `http://localhost:5173` con la cuenta de demostración, elegir Growth Ops, poner Mes inicial 2026-07 y Mes final 2026-09 y agrupar por Servicio. Deben salir los valores del paso D3 de [guion.md](guion.md): 61580.74 EUR (370 registros) y 0.87 USD (70 registros). La [receta de navegador](receta-navegador.md) hace esta comprobación y la del resto de pasos automáticamente sobre los valores de [esperados.json](esperados.json).

## 4. Hacer la demo

Seguir [guion.md](guion.md). Si hay que repetirla, recargar la página y volver a poner el periodo; no hace falta tocar los datos. Retroceder la fecha de referencia oculta los episodios posteriores a ella; si se retrocede la fecha, las conversaciones del asistente ya guardadas siguen mostrando sus respuestas anteriores, así que se empieza una conversación nueva; para repetir D12 desde cero se retiran y se vuelven a cargar los datos.

## 5. Volver al estado inicial

```sh
docker compose -p jup107 --profile demo run --rm demo-data python scripts/demo_data.py remove
docker compose -p jup107 --profile demo run --rm demo-data python scripts/demo_data.py remove
docker compose -p jup107 --profile demo run --rm demo-data python scripts/demo_data.py status
docker compose -p jup107 exec -T backend python - < resumen.py
```

Esperado: el primer `remove` dice `Retirados 7 ingestas, 1370 registros y N episodios de anomalia derivados de ellos.` (con N episodios si se detectó; la cifra de registros es la de las siete parejas); el segundo, `Retirados 0 ingestas, 0 registros y 0 episodios de anomalia derivados de ellos.`; el `status` final, `absent` en los dos clientes; y `resumen.py` imprime solo `data_status: empty`. Con la página de la demo recargada, el dashboard de Growth Ops para 2026-07 a 2026-09 muestra «Sin datos de costes para este periodo.».

Para terminar, parar el stack y borrar sus volúmenes:

```sh
docker compose -p jup107 --profile demo down -v
```

## Si algo no coincide

- `status` dice `partial`: ejecutar `remove` y volver a cargar.
- `status` dice `other-data`: `remove` **no** retira datos ajenos a la demo, así que no basta; hay que retirar a mano esas filas o crear el stack de nuevo con volúmenes nuevos (`down -v`). Es lo que ocurre, por ejemplo, con la ingesta del dataset público original de una suscripción de la demo.
- Si el stack venía de JUP-106 o JUP-107 (scripts ya retirados), sus filas (suscripciones `synthetic-jup106-*` y `synthetic-jup107-*`) cuentan como datos ajenos: lo más simple es `down -v` y volver a levantar; si no, borrarlas con SQL en CockroachDB (`DELETE FROM azure_cost_records WHERE id LIKE 'synthetic-jup10%'`, lo mismo en `azure_cost_ingestion_runs` y, para `tenant-core`, en `anomaly_episodes` y `anomaly_detection_state`).
- Los totales de D3 no son los esperados: comprobar el periodo (la pantalla arranca con los seis últimos meses completos antes de la fecha de referencia) y que se ha elegido Growth Ops.
- La cabecera no dice «Fecha simulada: 30/10/2026»: falta `COST_REFERENCE_DATE=2026-10-30` en el `.env` del stack; corregirlo y recrear el backend.
- No lances dos `apply` a la vez sobre el mismo stack: la lógica lee el estado y después ingiere, sin cerrojo, y el resultado de la carrera no está comprobado (`RF-119-009`).
