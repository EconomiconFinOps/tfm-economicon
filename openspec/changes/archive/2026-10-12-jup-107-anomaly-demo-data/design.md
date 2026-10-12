JUP: JUP-107
Trello: https://trello.com/c/ADFz3fpR

## Context

Ver `proposal.md` (por qué y qué cambia) y `specs/synthetic-anomaly-data/spec.md` (requisitos).

Estado de partida, comprobado en `develop` (`536fb4b`):

- `POST /billing/anomalies/evaluate` (JUP-030) compara `[start, end)` con el periodo anterior de igual duración. Con `group_by: service` los grupos llevan `subscription_id: null`. Estados de desviación: `disabled`, `below`, `triggered`, `baseline_missing` y `baseline_nonpositive`. Las alertas de una evaluación llevan `cause_status: not_established`.
- Los datos de JUP-106 (`scripts/synthetic_costs.py`) se cargan en `tenant-growth` con el prefijo `synthetic-jup106-` y la herramienta trata como reales las filas de ese tenant que no lleven el prefijo.
- El script se pasa por la entrada estándar al contenedor del processor (`python - apply < script`), así que no puede importar otros módulos del repositorio: debe ser autocontenido y solo ASCII.
- El dataset público (ingesta de Azure) deja datos de 2024 en el tenant donde se ingiere; en un stack recién levantado `tenant-core` no tiene costes.

## Goals / Non-Goals

**Goals:**

- Un conjunto que produzca, con reglas fijadas, exactamente dos alertas (una por umbral y subida, otra solo por umbral) y cinco evaluaciones sin alerta que ejercitan cada rama de la lógica.
- Cifras verificables a mano: importes enteros, periodos de siete días y porcentajes exactos.
- Que cargarlo y retirarlo sea explícito, repetible y no interfiera con JUP-106, JUP-065 ni el dataset público.

**Non-Goals:**

- Conectar el panel `/anomalies`, añadir pantallas o cambiar `apps/`.
- Medir la calidad de la detección o presentar los importes como reales.
- Sustituir ni reutilizar el conjunto de JUP-106.

## Decisions

1. **Tenant `tenant-core` y prefijo propio `synthetic-jup107-`.** JUP-106 trata como real todo lo de su tenant que no lleve su prefijo; cargar este conjunto en `tenant-growth` haría que `synthetic_costs.py apply` se negara. Con otro tenant y otro prefijo cada herramienta ve el tenant del otro como ajeno. Alternativa descartada: añadir filas al conjunto de JUP-106, porque la tarjeta lo excluye y lo cambiaría para sus propias pruebas.
2. **Herramienta autocontenida y duplicación asumida.** La entrada estándar impide importar `synthetic_costs.py`. Se copia el patrón (modelos de fila, `status`, `apply`, `remove`, `SqlStore`) con el prefijo y los datos propios. El coste es código duplicado; el beneficio es no tocar la herramienta de JUP-106 ni acoplar los dos conjuntos. La prueba comprueba que ambas herramientas se ignoran entre sí.
3. **Dos periodos de siete días y siete servicios, en EUR, una suscripción.** Base `[2026-09-01, 2026-09-08)` y actual `[2026-09-08, 2026-09-15)`, con `group_by: service`. Importes enteros para que la aritmética sea visible: Compute 1000,00 a 2400,00 (+1400,00; 140,00 %), Analytics 2200,00 a 2300,00 (+100,00; 4,55 %), Storage 800,00 a 820,00, Database 1500,00 a 1200,00, Tools 10,00 a 40,00 (+30,00; 300,00 %), Backup 0,00 (cero registrado) a 300,00 y Networking sin base y 600,00 actual. Reglas de la demo: umbral `2000.00`, subida `50.00` e incremento mínimo `100.00`. Salen dos alertas: Compute (umbral y subida) y Analytics (solo umbral); Tools queda por debajo del incremento mínimo pese a subir un 300 %, Backup en `baseline_nonpositive` y Networking en `baseline_missing`.
4. **Varias filas por servicio y periodo, todas con servicio.** Para que el recuento de registros sea realista y `missing_dimension_count` sea 0 (estado `available`). El recuento por grupo forma parte de los esperados.
5. **Valores esperados en un fichero propio, `esperados-anomalias.json`, y una prueba que los recalcula sin base de datos.** Sigue el patrón de la primera parte de JUP-107: la prueba suma con `Decimal` desde las filas del conjunto, sin usar el servicio de anomalías, y compara con el fichero; un control negativo altera un importe y exige que falle nombrando la cifra. Los identificadores `id` y `evidence_id` no se fijan en el fichero: se comprueban en la validación contra el endpoint real (estables al repetir), porque dependen del cálculo del backend.
6. **La demostración llama al endpoint; no hay pantalla.** `anomalias.md` ofrece dos vías: Swagger (`/docs`, solo si se comprueba que está disponible en el stack aislado) y un script por la entrada estándar del contenedor del backend que hace login con el usuario demo leyendo la contraseña del entorno del contenedor sin imprimirla. Se declara que el panel `/anomalies` sigue con su fixture y no refleja estos datos.
7. **Fecha de los datos fija en septiembre de 2026.** `end_date` no puede superar el día UTC actual; los datos están en el pasado respecto a la defensa, así que la petición es válida mientras la fecha del sistema sea posterior al 15/09/2026. La prueba lo comprueba contra la fecha del día y falla con mensaje claro si el reloj fuera anterior.

ADR: no aplicable. Es un conjunto de datos de demostración y su documentación; no introduce una decisión de arquitectura duradera ni transversal.

## Risks / Trade-offs

- **Código duplicado** con `synthetic_costs.py`: un cambio de esquema de las tablas de costes obliga a tocar las dos herramientas. Mitigación: la prueba con CockroachDB real (`JUP086_COCKROACH_TEST_URL`) ejercita la inserción y la retirada.
- **Los importes parecen reales:** se declara el origen sintético en la guía, en la herramienta y en `status`, y se limita a "ilustra las reglas".
- **Interferencia con la demo de JUP-065 o la ingesta pública** en `tenant-core`: la herramienta se niega si hay costes ajenos y la guía exige comprobar el tenant vacío y retirar al terminar.
- **Dependencia del reloj** (decisión 7): riesgo bajo; la prueba lo vigila.

## Migration Plan

Sin migraciones ni cambios de producto. Retirar el conjunto con `remove` deja el tenant como estaba. El paso de CI se añade con su comprobación; revertirlo no afecta a ninguna otra suite.

## Open Questions

- ¿Se publica la ruta `/docs` en el stack de demostración? Se comprueba al implementar; si no, la guía usa solo el script.
