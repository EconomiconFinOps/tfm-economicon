JUP: JUP-107
Trello: https://trello.com/c/ADFz3fpR

## Why

La demo de JUP-065 recorre una muestra pública de un mes y una sola moneda (0,06 USD) y deja `tenant-growth` vacío a propósito, así que no enseña lo que la funcionalidad de costes sí sabe hacer con series de varios meses, dos monedas, huecos, ceros y créditos. JUP-106 dejó esos datos como conjunto sintético, determinista y con valores esperados comprobados, pero no una demo que los use. La defensa es el 29/10 (10 a 20 minutos entre los cuatro integrantes) y el candidato de entrega con la demo ensayada desde cero es el 20/10, así que lo útil es una pieza corta, ensayable y repetible por otra persona, que sirva para responder con hechos en la ronda de preguntas y como base del vídeo opcional.

## What Changes

- Un paquete de demo en `docs/demo/JUP-107/`: un guion cronometrado de unos tres minutos sobre el dashboard ejecutivo con `tenant-growth`, con lo que se dice y lo que se espera ver en cada paso, y una guía de preparación y de vuelta al estado inicial con los comandos de JUP-106 (`apply`, `status`, `remove`).
- Una tabla de preguntas probables de un tribunal (varias monedas, hueco frente a cero, crédito, importes muy grandes, aislamiento entre clientes, etiquetas) y el paso del guion que responde cada una.
- Una declaración visible, en el guion y en el material de apoyo, de que los datos son sintéticos y no proceden de Azure ni del dataset público, y de qué pantallas de la aplicación no leen estos datos.
- Un fichero de valores esperados por paso, derivado del conjunto de JUP-106, y una prueba que lo recalcula con suma exacta y falla si el conjunto o el guion se desalinean; esa prueba corre en CI sin base de datos.
- Una receta de navegador, ejecutable fuera del repositorio como la de JUP-104, que recorre el guion, comprueba los valores esperados y guarda capturas y un vídeo mudo de apoyo fuera del repositorio.
- Una plantilla de registro de ensayo para anotar qué persona lo ensayó, con qué commit y qué resultado.

Fuera de alcance: modificar los datos sintéticos, la herramienta de JUP-106, el dataset público o los artefactos de JUP-065; cambiar el código de `apps/`, el esquema o el contrato de `/billing/summary`; datos de un tenant real; grabar el vídeo final, que se hace con la voz del equipo y no se versiona; corregir fallos que se encuentren al ensayar (cada uno, su tarjeta); y presentar como derivadas de estos datos las pantallas que hoy usan datos fijos del frontend.

## Capabilities

### New Capabilities

- `synthetic-cost-demo`: paquete de demo reproducible sobre los datos sintéticos de coste, con su declaración de origen, valores esperados verificados, preparación y limpieza, y registro de ensayo.

### Modified Capabilities

Ninguna. No cambia ningún requisito de `synthetic-cost-data` ni de las capacidades de costes.

## Impact

- Nuevo: `docs/demo/JUP-107/` (guion, preparación, preguntas, valores esperados, receta de navegador y plantilla de ensayo), una prueba en `scripts/tests/` y `docs/evidence/JUP-107-validation.md`.
- Cambios de configuración de CI y de scripts: `package.json`, `.github/workflows/ci.yml` y `tools/ci-workflow.test.mjs`, como hizo JUP-106.
- Sin cambios en `apps/`, en migraciones, en `scripts/synthetic_costs.py` ni en `docs/demo/JUP-065/`.
- Afecta a quien ensaye: mientras los datos estén cargados, `tenant-growth` deja de estar vacío y la demo de JUP-065 exige lo contrario, así que la preparación usa una instancia aislada y la guía termina con `remove`.
