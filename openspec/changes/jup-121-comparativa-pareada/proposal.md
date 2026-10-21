JUP: JUP-121
Trello: https://trello.com/c/aIdxwsXR

## Why

La autorización humana del 18/10 permite publicar la comparación GLM/DeepSeek
de JUP-063 e incorporarla a Grafana. El formato pareado real no encaja en el
benchmark JUP-078 y sus juicios locales provisionales no son aceptación humana
ni checks automáticos de calidad. Una carga global borraría otras ejecuciones.

## What Changes

- Adaptador aditivo `jup-063-paired-v1`, 18 filas de una ejecución agregada.
- Nulo de juicio estrictamente acotado a tres contadores locales provisionales;
  sin migración del CHECK PostgreSQL existente.
- Manifiesto suplementario y panel A separado con límites explícitos.
- SQL transaccional opt-in acotado a identidad/huella, sin vaciado global,
  modificación de roles ni DDL.
- Regresiones y prueba PostgreSQL aislada reproducible, sin nuevas inferencias.

## Impact

Herramienta de carga, contrato de filas, dashboard y documentación de JUP-121.
No modifica PR63, modelos, recuperación, corpus, proveedor ni gasto. Publicar
soporte no equivale a haberlo aplicado y observado en un Grafana activo.
