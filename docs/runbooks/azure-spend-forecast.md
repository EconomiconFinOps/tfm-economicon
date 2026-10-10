# Forecasting de gasto Azure — JUP-031

[Tarjeta](https://trello.com/c/uV9ywMry) ·
[Diseño y decisiones](../../openspec/changes/jup-031-azure-spend-forecast/design.md) ·
[Evidencias](../validation/JUP-031.md)

Con el backend levantado según su README, iniciar sesión y usar el bearer de la
sesión y `X-Tenant-Id` de una pertenencia autorizada. Petición de ejemplo:

```http
GET /billing/forecast?start_date=2024-01-01&end_date=2025-01-01&group_by=subscription&horizon_months=3
Authorization: Bearer <token-de-la-sesion>
X-Tenant-Id: <tenant-autorizado>
```

También admite `group_by=service` y `group_by=project`. El proyecto prefiere la
columna normalizada y usa el tag `project` si falta. La consulta incluye todos
los grupos del tenant; cada combinación de valor y moneda tiene una serie.
No convierte monedas ni suma previsiones de EUR y USD. No hace peticiones a Azure
ni al proveedor LLM y no necesita migraciones ni nuevas variables de entorno.

`start_date` y `end_date` son primeros de mes, UTC, con final exclusivo; máximo
24 meses de historia. Deben estar cerrados en el calendario: no admite el mes
actual. La previsión empieza en `end_date`, incluso si se eligió un corte histórico.
`horizon_months` admite 1–3, por defecto 1. Selecciones inválidas dan 422;
ingestas completadas solapadas para una misma suscripción/día dan 409 con
`ambiguous_cost_source`. Se mantienen los controles de autenticación y pertenencia.

Cada serie informa:

- `history`: meses observados, importe y número de filas.
- `status`: `forecast`, `insufficient_data` o `invalid_data`.
- `reason`: `short_history`, `missing_months`, `missing_dimension` o `non_finite_cost`.
- `missing_months`: huecos explícitos, incluidos extremos, sin imputación de ceros.
- `method`: `last_month` o `linear_trend`; null cuando no se puede prever.
- `backtest`: tres orígenes temporales, MAE de ambas opciones y de la seleccionada.
- `points`: estimación, referencia del último mes y límites descriptivos por mes.

Se requieren **9 meses para horizonte 1, 10 para 2 y 11 para 3**, todos observados
en la ventana seleccionada. Tres cortes evalúan horizontes completos con al menos
seis meses previos de entrenamiento. Una tendencia lineal sustituye la referencia
sólo si mejora su MAE más del 5 %. El modelo elegido se ajusta con toda la historia.

Los límites inferior/superior suman y restan el mayor error absoluto observado en
los tres cortes para ese horizonte. **No son un intervalo calibrado**:
`nominal_coverage=null`; tres cortes no acreditan cobertura probabilística.
La selección usa esos mismos cortes y su MAE no es una evaluación independiente.
Una serie sintética perfecta puede producir rango de anchura cero. Ceros reales
y créditos se conservan; valores y límites negativos representan coste neto antes
de impuestos y no se recortan. Los importes JSON son cadenas decimales exactas,
redondeadas a dos decimales sólo al presentar.

`data_status=empty` significa ausencia de datos utilizables, nunca gasto cero;
`partial` señala series insuficientes, dimensiones faltantes o filas sin fecha.
Aunque todos los meses tengan observaciones, la fuente no acredita cobertura
completa de facturación/ingesta. Las advertencias de la respuesta lo explicitan.
No se modelan estacionalidad anual, cambios de precios/infraestructura o divisas.
No sustituye la previsión nativa de Azure, una factura ni un compromiso presupuestario.

La muestra pública disponible sólo tiene parte de junio de 2024 y debe dar
`insufficient_data`. No cargar datos ficticios en un tenant operativo para conseguir
una previsión. Los tests versionados construyen series sintéticas aisladas y
prueban el contrato; no acreditan exactitud real ni la integración de anomalías
JUP-030. Tampoco se cambia el run rate de las herramientas del asistente.

Pruebas focales desde `apps/backend`:

```powershell
python -m pytest tests/test_forecast_service.py tests/test_forecast_api.py tests/test_forecast_repository.py -q
```

Las pruebas SQL se omiten si falta `JUP086_COCKROACH_TEST_URL`. La fixture exige
Cockroach desechable en loopback y puerto no estándar, usuario root sin contraseña,
`defaultdb?sslmode=disable`, sin tablas de usuario y organización
`processor-integration-tests`; crea y elimina su propia base. Nunca apuntar esta
suite a una base del usuario. Los dobles HTTP sustituyen sólo el lector de costes,
manteniendo autenticación y membership reales de la fixture SQLite.
