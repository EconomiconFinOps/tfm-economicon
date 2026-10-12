# Demo con datos sintéticos de coste — JUP-107

Verificación: 2026-10-11. [Tarjeta](https://trello.com/c/ADFz3fpR). Dos changes de OpenSpec en una sola rama (`feat/JUP-107-synthetic-cost-demo`) y un solo pull request.

## Qué contiene

- **Parte 1, `jup-107-synthetic-cost-demo` (aprobada el 2026-10-08):** demo de tres minutos del dashboard ejecutivo con los datos sintéticos de JUP-106 (varios meses, dos monedas, huecos, ceros, créditos). Paquete en `docs/demo/JUP-107/`: guion, preparación, preguntas, valores esperados, receta de navegador y registro de ensayo. Spec: `synthetic-cost-demo`.
- **Parte 2, `jup-107-anomaly-demo-data` (aprobada el 2026-10-11):** conjunto sintético de 22 registros en euros en `tenant-core` (dos periodos de siete días, siete servicios) para enseñar las alertas de JUP-030. Herramienta `scripts/synthetic_anomalies.py` (`apply`, `status`, `remove`), valores esperados `docs/demo/JUP-107/esperados-anomalias.json`, guía `docs/demo/JUP-107/anomalias.md` y llamada al endpoint con `scripts/call_anomalies_demo.py`. Spec: `synthetic-anomaly-data`. Con umbral 2000,00, subida 50 % e incremento mínimo 100,00 salen dos alertas (Compute y Analytics) y cinco evaluaciones sin alerta.

## Estado y límites

- Los datos son sintéticos: no son facturas de Azure ni vienen del dataset público. Las alertas ilustran las reglas; no demuestran calidad de detección ni causas.
- El panel `/anomalies` sigue con datos de demostración fijos y no lee el endpoint de JUP-030: conectarlo es un cambio aparte, con su propia tarjeta y su propia segunda opción de diseño.
- Las pruebas con CockroachDB real (6 en la parte 2) no las ejecuta la CI; se lanzan a mano con un nodo desechable (`RF-107-002`). La suite de `synthetic_costs.py` podría tener los mismos huecos que se cerraron en la nueva (`RF-107-003`).
- La receta de navegador de la parte 1 se ejecutó el 2026-10-08 y se repitió el 2026-10-12 contra la interfaz con la identidad de marca (JUP-112): 11 pasos `pass` y control positivo válido. Es una ejecución automatizada; no hay ensayo humano.
- No hay ensayo humano de ninguna de las dos guías.
- Excepción temporal del 2026-10-11: sin revisión ni validación humanas de otras personas en GitHub; revisión adversarial independiente, evidencia y aprobación de Lucia. Evidencia en [docs/evidence/JUP-107-validation.md](../evidence/JUP-107-validation.md).
- Los datos viven en `tenant-core` (parte 2) y en `tenant-growth` (parte 1): mientras estén cargados esos tenants dejan de estar vacíos y la demo de JUP-065 no debe usarlos. Retirar con `remove` al terminar.

## Cómo retomar

1. Leer la guía de la parte que se vaya a enseñar (`docs/demo/JUP-107/guion.md` o `anomalias.md`).
2. Levantar un stack aislado (`docker compose -p jup107b ...`), cargar, enseñar, retirar con `remove` dos veces y `down -v`.
3. En PowerShell, los comandos con `<` se escriben con `Get-Content -Raw <fichero> | docker compose ...`.
