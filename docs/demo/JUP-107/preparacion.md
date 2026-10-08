# Preparación y vuelta al estado inicial

Pasos para dejar lista la demo de [guion.md](guion.md) y para deshacerla. Los datos son **sintéticos** (JUP-106) y se cargan con su herramienta; ver [la guía de JUP-106](../../validation/JUP-106-synthetic-costs.md) para qué contiene cada caso.

## Antes de empezar

- Usar un **stack aislado con volúmenes nuevos**, no el de otra tarea. Los ejemplos usan el proyecto `jup107`.
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

## 3. Comprobar los valores antes de la demo

Entrar en `http://localhost:5173` con la cuenta de demostración, elegir Growth Ops, poner Mes inicial 2026-01 y Mes final 2026-06 y agrupar por Servicio. Deben salir los valores del paso D3 de [guion.md](guion.md): 90.00 EUR (6 registros) y 35.75 USD (2 registros). La [receta de navegador](receta-navegador.md) hace esta comprobación y la del resto de pasos automáticamente sobre los valores de [esperados.json](esperados.json).

## 4. Hacer la demo

Seguir [guion.md](guion.md). Si hay que repetirla, recargar la página y volver a poner el periodo; no hace falta tocar los datos.

## 5. Volver al estado inicial

```sh
docker compose -p jup107 exec -T processor python - remove < scripts/synthetic_costs.py
docker compose -p jup107 exec -T processor python - remove < scripts/synthetic_costs.py
docker compose -p jup107 exec -T processor python - status < scripts/synthetic_costs.py
```

Esperado: el primer `remove` dice `Retiradas 2 ingestas y 10 registros sinteticos.`; el segundo, `Retiradas 0 ingestas y 0 registros sinteticos.`; el `status` final, `absent` y 0 registros. Con la página de la demo recargada, el dashboard de Growth Ops para 2026-01 a 2026-06 muestra «Sin datos de costes para este periodo.».

Para terminar, parar el stack y borrar sus volúmenes:

```sh
docker compose -p jup107 down -v
```

## Si algo no coincide

- `status` dice `partial` u `other-tenant`: ejecutar `remove` y volver a cargar.
- Los totales de D3 no son los esperados: comprobar el periodo (la pantalla arranca con los seis últimos meses completos) y que se ha elegido Growth Ops.
- Un `apply` simultáneo de otra persona sobre el mismo stack no duplica datos, pero el que pierde la carrera ve un error genérico; repetir el comando.
