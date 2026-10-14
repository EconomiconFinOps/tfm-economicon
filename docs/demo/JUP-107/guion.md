# Guion de la demo con datos de demostración de coste

**Duración total: 180 s** (tres minutos) más dos pasos opcionales de 20 s (D7) y 30 s (D11). Los pasos tienen identificador estable (`D1`...`D12`; D12 va justo después de D9) para poder enseñar uno solo cuando se responde a una pregunta (ver [preguntas.md](preguntas.md)).

Los datos de esta demo son de **demostración**: sintéticos, generados por nosotros, o del dataset público de Microsoft con las fechas desplazadas a 2026. No son facturas de Azure de 2026 y no deben presentarse como tales. La demo supone la **fecha de referencia 30/10/2026** (`COST_REFERENCE_DATE=2026-10-30`): el último día con datos. La cabecera lo dice con «Fecha simulada: 30/10/2026». Se enseñan dos pantallas: el dashboard ejecutivo (`/`, Coste Global) con el cliente Growth Ops y, en D12, el panel de Anomalías con el cliente Core Finance (ver [anomalias.md](anomalias.md)). Las cifras de cada paso están en [esperados.json](esperados.json) y una prueba las recalcula con suma exacta desde el CSV de la demo.

Los datos solo traen **servicio y etiqueta Project**: no hay grupo de recursos, centro de coste, propietario, aplicación ni entorno, porque la API de consulta agrupa por dos campos como mucho.

Antes de empezar, seguir [preparacion.md](preparacion.md) hasta tener los datos cargados y la sesión abierta en el panel de Anomalías.

### D1 · Declarar que los datos son de demostración

- **Duración:** 15 s
- **Acción:** Con la aplicación abierta en Anomalías con Core Finance seleccionado (sin cifras en pantalla: todavía no se ha detectado), sin tocar nada todavía.
- **Qué decir:** «Todo lo que vais a ver son datos de demostración: sintéticos, generados por nosotros para probar la aplicación, o del dataset público de Microsoft con las fechas desplazadas a 2026. No son facturas de Azure de 2026, aunque los rótulos de la pantalla digan Azure.»
- **Resultado esperado:** En pantalla, el aviso «Datos sintéticos de demostración: no son facturas reales», la etiqueta «Fecha simulada: 30/10/2026» en la cabecera y ninguna cifra; el público oye la declaración antes de ver ninguna cifra.

### D2 · Elegir el cliente y el periodo

- **Duración:** 15 s
- **Acción:** Ir a Coste Global y elegir Growth Ops en el selector de cliente. Poner Mes inicial 2026-07 y Mes final 2026-09; el periodo por defecto depende de la fecha de referencia, así que se fija siempre antes de leer ninguna cifra.
- **Qué decir:** «Elegimos el cliente Growth Ops y de julio a septiembre de 2026. Los dos meses extremos están incluidos.»
- **Resultado esperado:** Aparece «julio de 2026 – septiembre de 2026 (UTC)» y los totales EUR y USD del periodo.

### D3 · Desglose por servicio y totales por moneda

- **Duración:** 25 s
- **Acción:** Agrupar por Servicio.
- **Qué decir:** «Hay dos monedas y no se mezclan: 61580,74 euros en 370 registros y 0,87 dólares en 70. El desglose reparte los euros entre Compute, Database, Storage y Networking, con un crédito aparte y un grupo sin servicio.»
- **Resultado esperado:** Total EUR 61580.74 (370 registros) y total USD 0.87 (70 registros). Filas EUR: Compute 28099.20, Database 16859.52, Storage 11239.68, Networking 5619.84, Credits -250.00 y Sin dimensión 12.50.

### D4 · Un mes sin datos frente a un mes con cero

- **Duración:** 25 s
- **Acción:** Cambiar la moneda a USD y señalar el gráfico y la tabla de costes mensuales.
- **Qué decir:** «En dólares, julio no tiene ningún dato y agosto tiene un cero registrado: la aplicación no los confunde. El gráfico deja un hueco en julio en vez de dibujar un cero inventado.»
- **Resultado esperado:** Julio con «—» y «Sin datos de esta moneda.»; agosto 0.00 con 31 registros; septiembre 0.87 con 39 registros.

### D5 · Un crédito y la comparación en euros

- **Duración:** 20 s
- **Acción:** Cambiar la moneda a EUR y señalar la fila Credits del desglose y la comparación de meses.
- **Qué decir:** «Agosto incluye un crédito de 250 euros negativos, en el grupo Credits. La comparación usa el primer y el último mes con coste: de julio a septiembre suben 2351,54 euros, un 12,12 por ciento.»
- **Resultado esperado:** Credits -250.00 (1 registro). «Comparación: septiembre de 2026 frente a julio de 2026 · EUR» con variación absoluta +2351.54 EUR y porcentual +12.12 %.

### D6 · Cuando no hay comparación posible

- **Duración:** 20 s
- **Acción:** Cambiar la moneda a USD y señalar la comparación de meses.
- **Qué decir:** «En dólares no hay comparación posible: agosto es un cero registrado, que no cuenta como extremo, y julio no tiene datos; solo septiembre tiene coste.»
- **Resultado esperado:** «Comparación no disponible: Solo hay un mes con coste para comparar».

### D7 · Opcional: desglose por etiqueta

- **Duración:** 20 s (opcional, no cuenta en el total)
- **Acción:** Agrupar por Etiqueta y escribir la clave project.
- **Qué decir:** «Podemos repartir el coste por etiqueta: Alpha, Beta, y lo que no tiene etiqueta queda aparte en vez de perderse.»
- **Resultado esperado:** Etiqueta consultada: project. EUR: Alpha 44971.22 (185), Beta 15935.60 (172) y Sin dimensión 673.92 (13); USD: Alpha 0.00, Foo 0.43 y Sin dimensión 0.44.

### D8 · Lo que queda sin clasificar: un registro sin servicio

- **Duración:** 10 s
- **Acción:** Con el desglose por servicio, señalar el aviso amarillo de datos parciales y la fila Sin dimensión.
- **Qué decir:** «Hay un registro sin servicio. La aplicación no lo reparte ni lo esconde: lo avisa y lo deja en su propio grupo.»
- **Resultado esperado:** Aviso «Datos parciales: 1 registros sin dimensión; 0 registros sin fecha excluidos.» y fila Sin dimensión 12.50 EUR (1 registro).

### D9 · Aislamiento entre clientes

- **Duración:** 15 s
- **Acción:** Cambiar el selector de cliente a Core Finance.
- **Qué decir:** «Core Finance tiene sus propios costes: al cambiar de cliente aparecen otras cifras y no se mezclan con las de Growth Ops.»
- **Resultado esperado:** Con Core Finance y el mismo periodo, total EUR 79337.00 (569 registros) y ningún total USD. Esto muestra la separación visual entre clientes; no sustituye una prueba de autorización. Se sigue con Core Finance en el paso siguiente.

### D12 · Anomalías detectadas en Core Finance

- **Duración:** 30 s
- **Acción:** Abrir Anomalías en el menú, con Core Finance seleccionado, pulsar «Detectar ahora» y abrir el detalle de la primera fila.
- **Qué decir:** «En Core Finance hay otro conjunto de demostración, pensado para anomalías. Al detectar, la aplicación revisa el coste de cada día con la regla de negocio y prioriza por el impacto acumulado. Compute sale primero, con criticidad alta: es una candidata para investigar, no una causa confirmada.»
- **Resultado esperado:** Aviso «Datos sintéticos de demostración: no son facturas reales» y «Revisado hasta el 29/10/2026». Primera fila Compute «Alta (P1)» con 5851.57 EUR en 28 días; después Storage y Database «Media (P2)», y Analytics y Tools «Baja (P3)». El detalle de Compute dice «Candidata: causa no establecida».

### D10 · Límites de lo que hemos enseñado

- **Duración:** 5 s
- **Acción:** Sin tocar la pantalla.
- **Qué decir:** «Para ser claros con los límites: son datos de demostración, solo traen servicio y proyecto, y el ahorro potencial no está disponible.»
- **Resultado esperado:** Nada que comprobar en pantalla. La cobertura de etiquetas y los responsables por centro de coste, propietario o aplicación no tienen datos en esta demo, y Coste Detallado, Corte Global y Recomendaciones (`/operational`, `/cuts`, `/recommendations`) ya no se publican: no abrirlas.

### D11 · Opcional: un importe fuera del rango seguro

- **Duración:** 30 s (opcional, no cuenta en el total)
- **Acción:** Volver a Coste Global, elegir Growth Ops, poner Mes inicial y Mes final en 2026-10 y la moneda USD; señalar el aviso, la tabla y, con el desglose por servicio, la fila Archive.
- **Qué decir:** «Octubre tiene un importe por encima de lo que un número de JavaScript representa sin perder dígitos. La aplicación no lo dibuja, avisa y conserva el valor exacto en la tabla.»
- **Resultado esperado:** Aviso «Algunos importes superan el límite de representación gráfica. Sus valores exactos permanecen en la tabla.» y octubre 9007199254741837.50 (31 registros); con el desglose por servicio, Archive 9007199254740993.00 (1 registro). No comparar octubre con septiembre: el porcentaje resultante no es presentable.

## Si algo falla

- Si los totales de D2 o D3 no coinciden con los esperados, detener el recorrido, no improvisar cifras y comprobar con `status` que los datos están cargados (ver preparación).
- Si el periodo por defecto sigue activo, volver a poner Mes inicial 2026-07 y Mes final 2026-09 antes de leer ninguna cifra.
- Si en D12 el panel ya muestra anomalías antes de pulsar, alguien detectó antes de la demo: el resultado de la pulsación dirá «Ya estaba al día» y las cifras son las mismas; no hace falta repetir la preparación.
- Si la cabecera no dice «Fecha simulada: 30/10/2026», el backend no tiene `COST_REFERENCE_DATE=2026-10-30`: las cifras de octubre y de D12 no serán las esperadas.
- No presentar capturas anteriores como resultado actual ni abrir pantallas que no leen estos datos para rellenar el tiempo.
