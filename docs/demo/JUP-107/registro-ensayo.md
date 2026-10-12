# Registro de ensayo

Plantilla para anotar cada ensayo de [guion.md](guion.md). Un ensayo solo existe cuando hay un registro relleno aquí o en la evidencia de la tarjeta: ningún documento debe afirmar que «se ensayó» sin él. Copiar la tabla por cada ensayo.

| Campo | Valor |
| --- | --- |
| Persona | |
| Fecha y hora | |
| Commit de la aplicación | |
| Commit del paquete de demo | |
| Modo | automatizada (receta de navegador) o ensayo humano |
| Duración total medida | |
| Stack | proyecto Compose, puertos y si los volúmenes eran nuevos |

## Resultado por paso

Usar `pass`, `fail`, `blocked` o `not_run`. Un paso que depende de otro que falló queda como `not_run`.

| Paso | Resultado | Duración (s) | Observaciones |
| --- | --- | --- | --- |
| D1 | | | |
| D2 | | | |
| D3 | | | |
| D4 | | | |
| D5 | | | |
| D6 | | | |
| D7 | | | |
| D8 | | | |
| D9 | | | |
| D10 | | | |
| D11 (opcional) | | | |

## Observaciones generales

- Una ejecución **automatizada** comprueba valores y etiquetas de la interfaz; no dice nada del cronometraje con una persona presentando.
- Fallos encontrados: cada uno se registra como hallazgo o tarjeta propia, sin corregirlos en el ensayo.
- Estado final: confirmar que se retiraron los datos (`remove`) y el stack se paró con `down -v`.
