# JUP-031 — Monthly Azure spend forecasting

## Context and decisions

Reuse the normalized `azure_cost_records`/`azure_cost_ingestion_runs` contract and
the existing bearer/session/tenant membership dependency. Expose a separate
`GET /billing/forecast`, keeping forecasting independent of JUP-030 and run rate.
Parameters select 1–24 closed calendar months `[start_date,end_date)` (both day 1),
grouping subscription/service/project and horizon 1–3. End date cannot exceed the
current UTC month. Estimates start at end_date; a historical end date means a
historical as-of simulation, not a forecast from today's date.

One bounded SQL aggregation joins matching tenant, ingestion and subscription,
requires completed status, checks multiple ingestions per subscription/day and
raises the established ambiguity conflict. Project prefers typed project then
the project tag, like billing. Raw Decimal totals retain precision until display.
Currencies and dimension values remain separate; no currency conversion or global
forecast total. Rows lacking a dimension are visible but not forecast. Undated
records are counted separately and warn of partial data.

Each group needs every selected month observed, including leading and trailing
months. Absence is unknown, never zero. At least `8 + horizon` months are required:
earliest training window >=6 months, three expanding origins, full horizon in
each holdout. Last observed month is the reference; ordinary least-squares trend
is the candidate. Both use the same prefixes and future holdouts without leakage.
Mean absolute error uses exact amounts, including zero and negative net credits;
percentage error is deliberately avoided. Select trend only if MAE improves >5%;
ties keep baseline. Refit the selected method on all history.

For each horizon step, the error envelope is plus/minus the largest absolute
error of the selected method across the three holdouts. This descriptive range
is not a calibrated confidence or prediction interval. `nominal_coverage=null`.
Backtest is also used for selection: selected MAE is not independent test error.
Perfect synthetic series yield zero-width envelopes without implying certainty.

## Limits and alternatives

No seasonal model: 9–11 observations support a minimal benchmark, not annual
seasonality. No Prophet/ARIMA dependency without a representative long dataset.
The public EA sample only covers part of June 2024; it cannot validate forecast
accuracy. Synthetic tests validate behavior, never real Azure performance.
Monthly observations and completed ingestion status do not certify billing
completeness; API warnings make this limitation explicit. Late charges, pricing,
infrastructure changes, exchange rates and lifecycle changes are unmodeled.
No clamps: signed forecasts describe net pre-tax cost, including credits.

## Verification

Arithmetic fixtures, holdout-prefix spy, HTTP auth/tenant/error tests, real SQL
tests in an explicitly isolated database. See `docs/validation/JUP-031.md` for
executed commands, criteria, versions and remaining human/production checks.
