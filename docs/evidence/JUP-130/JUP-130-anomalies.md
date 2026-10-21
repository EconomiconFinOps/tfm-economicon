# Calidad del detector de anomalías (JUP-130)

Fecha de referencia: 2026-10-30 (último día evaluado: 2026-10-29). Comando: `python tools/memory-indicators.py anomalies --reference 2026-10-30`. Con `--run-at` y `--commit` se fijan la fecha y el commit del informe.

| Medida | Valor |
| --- | --- |
| Precisión (episodios con evento / episodios abiertos) | 100,0 % (5/5) |
| Recall de todos los eventos | 71,4 % (5/7) |
| Recall de los eventos detectables por diseño | 100,0 % (5/5) |
| Retraso medio hasta la detección | 0,0 días |
| Verdaderos positivos / falsos positivos / falsos negativos | 5 / 0 / 2 |

## Eventos inyectados

| Evento | Servicio | Inicio | Naturaleza | Detectable por diseño | Resultado |
| --- | --- | --- | --- | --- | --- |
| EV-01 | Compute | 2026-09-09 | sustained_step_up | sí | detectado, retraso 0 d |
| EV-02 | Analytics | 2026-09-10 | one_day_spike | sí | detectado, retraso 0 d |
| EV-03 | Backup | 2026-09-10 | one_day_spike_from_zero | no detectable por diseño | no detectado |
| EV-04 | Networking | 2026-09-14 | first_appearance | no detectable por diseño | no detectado |
| EV-05 | Database | 2026-09-16 | five_day_step_up | sí | detectado, retraso 0 d |
| EV-06 | Tools | 2026-10-08 | one_day_spike | sí | detectado, retraso 0 d |
| EV-07 | Storage | 2026-10-20 | sustained_step_up | sí | detectado, retraso 0 d |

## Episodios abiertos

| Servicio | Inicio |
| --- | --- |
| Compute | 2026-09-09 |
| Analytics | 2026-09-10 |
| Database | 2026-09-16 |
| Tools | 2026-10-08 |
| Storage | 2026-10-20 |

## Qué no demuestra

- Son 7 eventos de un conjunto de datos sintéticos: las cifras son ilustrativas y no tienen validez estadística.
- Las etiquetas las escribió quien diseñó los datos y los datos se diseñaron para esta regla, así que una precisión de 1,00 y un retraso de 0 días son en parte esperables.
- El retraso va del inicio del evento al día en que la regla diaria abre el episodio: como el episodio se abre el mismo día evaluado, vale 0 por construcción y no mide la latencia real de la detección (en producción el mínimo es de un día, porque solo se evalúan días completos).
- Un pico desde cero o la primera aparición de un servicio no se detectan por diseño: la regla exige una semana de referencia con coste positivo.
- No demuestra el comportamiento con facturas reales de Azure ni con otras reglas o umbrales.
