# Demo con datos de demostración de coste (JUP-107, rehecha con JUP-119)

Demo corta de la funcionalidad de costes sobre los **datos de demostración** de [la guía de datos](../../data/azure-sample-dataset.md): cuatro meses de 2026 (del 1 de julio al 30 de octubre), dos monedas, un mes sin datos, un cero registrado, un crédito, un registro sin servicio y un importe fuera del rango seguro de JavaScript. Son **sintéticos o del dataset público de Microsoft con las fechas desplazadas a 2026; no son facturas de Azure de 2026**: la demo lo dice antes de enseñar ninguna cifra.

Está pensada para dos usos con los mismos pasos: respuesta con hechos en la ronda de preguntas y base de un vídeo (que se graba aparte, con la voz del equipo, y no se versiona).

| Fichero | Para qué |
| --- | --- |
| [guion.md](guion.md) | Recorrido de tres minutos (más dos pasos opcionales) con la acción, lo que decir y lo que se espera ver. |
| [preparacion.md](preparacion.md) | Levantar un stack aislado, cargar los datos con `demo_data.py`, comprobarlos y deshacerlo todo. |
| [preguntas.md](preguntas.md) | Preguntas probables de un tribunal y el paso que responde cada una. |
| [esperados.json](esperados.json) | Cifras de cada paso, comprobadas por una prueba con suma exacta desde el CSV de la demo. |
| [receta-navegador.md](receta-navegador.md) | Script de navegador, fuera del repositorio, que recorre la demo y comprueba lo que muestra la interfaz. |
| [registro-ensayo.md](registro-ensayo.md) | Plantilla para anotar cada ensayo. |
| [anomalias.md](anomalias.md) | Segunda parte: la consulta de prueba de anomalías y el panel, con la fecha de referencia 21/09/2026. |

Qué usa y qué no:

- Los costes cargados los leen el dashboard ejecutivo (`/`) y la vista heredada `/overview-legacy`; la demo usa el dashboard ejecutivo. El panel de Anomalías lee los episodios guardados del cliente y se usa en D12 con el conjunto de anomalías ([anomalias.md](anomalias.md)) en Core Finance. Las pantallas de Coste detallado, Corte global y Recomendaciones ya no se publican (JUP-116).
- Los datos solo traen **servicio y etiqueta `Project`** (la API de consulta agrupa por dos campos como mucho): no hay grupo de recursos, centro de coste, propietario, aplicación ni entorno. La cobertura de etiquetas y los responsables por esas dimensiones no tienen datos en esta demo.
- La demo supone la **fecha de referencia 30/10/2026** (`COST_REFERENCE_DATE=2026-10-30`); la cabecera enseña «Fecha simulada: 30/10/2026».
- La demo de JUP-065 y el recorrido de JUP-104 suponen `tenant-growth` sin costes: se prepara en un stack propio y termina con `remove`.

Comprobación automática de las cifras (sin base de datos, también en CI):

```sh
corepack pnpm synthetic-demo:test
```
