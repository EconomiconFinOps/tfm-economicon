# Fecha de referencia

JUP-119 ([ADR-0021](../adr/ADR-0021-demo-cost-data-single-path-and-reference-date.md)). El backend decide qué día es
«hoy» para los costes, la detección de anomalías y el asistente en un solo sitio: el ajuste `COST_REFERENCE_DATE`.

## Configuración

| Valor | Efecto |
| --- | --- |
| vacío o ausente | La fecha de referencia es el día UTC real y avanza sola con el reloj. |
| `AAAA-MM-DD` | Fecha fija (por ejemplo `2026-10-30`). Cualquier otro valor (fecha y hora, espacios, un día que no existe, un año de dos cifras) detiene el arranque con un mensaje que nombra `cost_reference_date` y no muestra el valor. |

## Qué cambia

- Ninguna lectura de costes (`GET /billing/summary`, `GET /billing/tag-coverage`, `POST /billing/budget/evaluate`,
  `POST /billing/anomalies/evaluate`, la lectura diaria de la detección y la pregunta de responsables) incluye un
  registro posterior al día de referencia. El día de referencia entra; el siguiente no. Un periodo entero posterior
  responde como un periodo sin datos. Los registros sin fecha conservan su tratamiento.
- El periodo por defecto es el mes que contiene la fecha de referencia. La consulta de prueba de anomalías sigue
  aceptando solo días cerrados: su fin no puede pasar de la fecha de referencia.
- La detección usa la fecha de referencia como «hoy»: el último día completo es el anterior al menor entre la fecha de
  referencia y el último día con datos visibles (el último día con datos nunca se da por completo).
- Los episodios guardados solo se ven si el último día de su impacto es anterior a la fecha de referencia; al retroceder
  la fecha se ocultan con el mismo 404 que un identificador desconocido y reaparecen al avanzarla. La «última evaluación»
  del listado no pasa del día anterior a la fecha de referencia.
- La respuesta de responsables incluye `reference_date` en la evidencia y la línea «Fecha de referencia».

Los datos posteriores existen en la base de datos aunque no se lean: no es un control de acceso.

## `GET /billing/reference-date`

Requiere sesión (`Authorization: Bearer ...`); no depende del cliente activo y devuelve lo mismo a cualquier usuario.

```json
{ "reference_date": "2026-10-30", "simulated": true }
```

`simulated` es verdadero exactamente cuando `COST_REFERENCE_DATE` está fijado. Sin sesión responde 401 y no devuelve la
fecha. El frontend lee esta ruta para el periodo por defecto del dashboard ejecutivo, el compositor del asistente y la
cabecera, que muestra «Fecha simulada: dd/mm/aaaa» cuando `simulated` es verdadero; si la ruta falla, la interfaz
muestra un error y no calcula nada con el reloj del navegador.
