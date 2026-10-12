# Demo con datos sintéticos de coste (JUP-107)

Demo corta de la funcionalidad de costes sobre los **datos sintéticos** de [JUP-106](../../validation/JUP-106-synthetic-costs.md): varios meses de 2026, dos monedas, un mes sin datos, un cero registrado, un crédito y un registro sin fecha. **No son facturas de Azure ni proceden del dataset público**: la demo lo dice antes de enseñar ninguna cifra.

Está pensada para dos usos con los mismos pasos: respuesta con hechos en la ronda de preguntas y base de un vídeo (que se graba aparte, con la voz del equipo, y no se versiona).

| Fichero | Para qué |
| --- | --- |
| [guion.md](guion.md) | Recorrido de tres minutos (más dos pasos opcionales) con la acción, lo que decir y lo que se espera ver. |
| [preparacion.md](preparacion.md) | Levantar un stack aislado, cargar los datos, comprobarlos y deshacerlo todo. |
| [preguntas.md](preguntas.md) | Preguntas probables de un tribunal y el paso que responde cada una. |
| [esperados.json](esperados.json) | Cifras de cada paso, comprobadas por una prueba con suma exacta. |
| [receta-navegador.md](receta-navegador.md) | Script de navegador, fuera del repositorio, que recorre la demo y comprueba lo que muestra la interfaz. |
| [registro-ensayo.md](registro-ensayo.md) | Plantilla para anotar cada ensayo. |

Qué usa y qué no:

- Los costes cargados los leen el dashboard ejecutivo (`/`) y la vista heredada `/overview-legacy`; la demo usa el dashboard ejecutivo. El panel de Anomalías lee los episodios guardados del cliente y se usa en D12 con el conjunto sintético de anomalías ([anomalias.md](anomalias.md)) en Core Finance. Las pantallas de Coste detallado, Corte global y Recomendaciones usan datos fijos de la maqueta y **no se usan** como evidencia.
- La demo de JUP-065 y el recorrido de JUP-104 suponen `tenant-growth` sin costes: se prepara en un stack propio y termina con `remove`.

Comprobación automática de las cifras (sin base de datos, también en CI):

```sh
corepack pnpm synthetic-demo:test
```
