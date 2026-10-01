# JUP-065 — Validación de la preparación de demo

Fecha: 2026-10-01. [Trello](https://trello.com/c/SZUFo4ol).
Rama: `docs/JUP-065-functional-demo`, sobre develop
`de0d62e7c0028f35a81c5087f531d19031a90e81`.
[Paquete](../demo/JUP-065/README.md) y
[alcance OpenSpec](../../openspec/changes/jup-065-functional-demo/proposal.md).

## Resultados locales

| Comprobación | Resultado nuevo |
| --- | --- |
| `python docs/demo/JUP-065/verificar.py --repo .` | PASS; quince archivos idénticos a la regeneración desde Git fijado |
| `python -O docs/demo/JUP-065/verificar.py --repo .` | PASS; guardas explícitas activas sin depender de assert |
| `python -m unittest discover -s docs/demo/JUP-065 -p 'test_*.py' -v` | 2 tests PASS, cuatro controles negativos: coste alterado, rúbrica inyectada, archivo faltante y archivo extra rechazados |
| `node docs/demo/JUP-065/generado/sources/tools/validation-questions.mjs validate` | 28 consultas, siete categorías y fuentes/rúbricas verificadas |
| `node tools/jup-check.mjs --change jup-065-functional-demo` | Trazabilidad PASS |
| `node tools/jup-cleanup-check.mjs` | Higiene PASS |
| `openspec validate --all --strict --no-interactive` | 36/36 PASS |
| Gobernanza: CI workflow, JUP check, higiene y política de PR | 32/32 tests PASS; nueve changes trazables |
| `git diff --check` | PASS |

Las pruebas negativas operan en copias temporales y no modifican la referencia
versionada. [Recibo de integridad](JUP-065-offline-results.json) conserva hashes.
Python estándar y Node; ninguna dependencia añadida al proyecto. CI obtiene
historial completo solo en gobernanza y ejecuta verificador, controles negativos
y validador de fuentes, conservando los siete contextos obligatorios.

## Referencias y limitaciones

La referencia se calcula independientemente con CSV y Decimal: 40 filas públicas,
38 registros recurso/grupo/día/moneda, ocho grupos (case-insensitive para resource
group) y coste 0,06 USD. La suma exacta CSV 0.060113199075769 no es una lectura
de CockroachDB. Se compara la salida de billing a dos decimales en el ensayo
posterior; no se afirma persistencia ni igualdad bit a bit del importe interno.
JUP-069-001 utiliza 1.000 EUR sintéticos suministrados como contexto separado.

**Runtime/LLM/ensayo integrado: not_run.** No se ejecutaron bases de datos,
proveedores externos, ingestas ni navegador. No se afirma calidad de respuestas,
despliegue, demo completa, ahorro obtenido ni cierre de tarjeta. La revisión de
Paris, validación de Victor y pairing de Lucia permanecen pendientes de evidencia
humana; el usuario autorizó publicar y solicitar, no aprobar en su nombre.

## Reproducción solicitada al validador

1. Obtener la rama y el SHA exacto publicado, con el commit de referencia disponible.
2. Ejecutar los comandos anteriores desde la raíz, empezando por el verificador
   sin regenerar los ficheros: una regeneración previa podría ocultar una alteración.
3. Contrastar números, fechas, ausencia de filtración de rúbricas y casos límite.
4. Leer guion/preflight/plantilla y confirmar que límites y dependencias son claros.
5. Publicar resultado de preparación con SHA, comandos, incidencias y conclusión.
   No marcar como realizado el ensayo integrado ni cerrar JUP-065 por estas pruebas.
