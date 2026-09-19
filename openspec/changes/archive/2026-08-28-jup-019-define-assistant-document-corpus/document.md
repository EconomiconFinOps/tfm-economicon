# FinOps básico aplicado a Azure Cost Management
## Guía práctica para el MVP de Economicon

**Fecha de revisión:** 12 de agosto de 2026  
**Ámbito:** FinOps general, Microsoft Azure Cost Management y diseño de reglas MVP para Economicon  
**Tipo de escenario:** Simulado. Las cifras, umbrales internos y ahorros de Economicon son ejemplos de diseño, no recomendaciones oficiales de Microsoft ni de FinOps Foundation.

---

## 0. Qué deberías ser capaz de explicar al terminar

Después de estudiar esta guía deberías poder responder con soltura a tres bloques:

1. **FinOps básico aplicado a Azure Cost Management en un entorno simulado.**
2. **Reglas MVP de Economicon:** tagging, coste no asignado, KPIs, anomalías y recomendaciones.
3. **Glosario práctico:** tenant, subscription, resource group, tag, showback, forecast, anomaly, commitment y rightsizing.

Además, deberías ser capaz de defender decisiones como:

- por qué no basta con mirar la factura mensual;
- cómo pasar de gasto cloud a responsabilidad por equipo o producto;
- qué diferencia existe entre budget, forecast y coste real;
- cómo tratar costes compartidos y costes sin propietario;
- por qué una recomendación de ahorro no debe aplicarse automáticamente;
- cuándo tiene sentido rightsizing y cuándo tiene sentido un commitment;
- por qué el tagging es una herramienta FinOps pero también una disciplina de gobierno.

---

# 1. FinOps: la idea fundamental

FinOps es una práctica operativa y cultural para maximizar el valor empresarial de la tecnología mediante colaboración entre ingeniería, finanzas, producto y negocio.

No significa simplemente "gastar menos". Una organización puede aumentar su gasto cloud y, aun así, mejorar su eficiencia si ese incremento genera más valor, más usuarios, más transacciones o mejores resultados de negocio.

La pregunta FinOps no es únicamente:

> ¿Cuánto estamos gastando?

Sino:

> ¿Qué estamos obteniendo a cambio, quién genera ese gasto, es esperado, está optimizado y quién puede actuar sobre él?

## 1.1 El ciclo Inform - Optimize - Operate

FinOps Foundation organiza el trabajo de manera iterativa en tres fases:

### Inform

Crear visibilidad y contexto:

- cuánto gastamos;
- dónde gastamos;
- quién es responsable;
- cómo evoluciona el gasto;
- si estamos dentro del presupuesto;
- qué parte del coste está correctamente asignada.

En Azure, esta fase se apoya especialmente en Cost Analysis, exports, tags, jerarquía de recursos, presupuestos y reporting.

### Optimize

Encontrar oportunidades para mejorar eficiencia:

- rightsizing;
- apagado de recursos ociosos;
- eliminación de recursos huérfanos;
- optimización de almacenamiento;
- optimización de logs;
- Reservations;
- Savings Plans;
- Azure Hybrid Benefit;
- cambios arquitectónicos.

### Operate

Convertir el análisis en comportamiento repetible:

- responsables claros;
- políticas;
- alertas;
- revisiones periódicas;
- tickets o workflows;
- seguimiento del ahorro realizado;
- automatización segura.

El ciclo se repite. No es un proyecto que se hace una vez.

---

# 2. Conceptos que no debes confundir

## 2.1 Coste, valor y eficiencia

**Coste** es lo que pagamos por la tecnología.  
**Valor** es lo que esa tecnología permite conseguir.  
**Eficiencia** relaciona ambos conceptos.

Ejemplo:

- Aplicación A cuesta 2.000 EUR/mes y procesa 2 millones de pedidos.
- Aplicación B cuesta 1.000 EUR/mes y procesa 100.000 pedidos.

Mirando solo el coste, B parece mejor. Mirando coste por pedido:

- A: 0,001 EUR/pedido.
- B: 0,01 EUR/pedido.

A es diez veces más eficiente en esa unidad de negocio simulada.

Esto introduce el concepto de **unit economics**: asociar el coste tecnológico a una unidad que tenga sentido para el negocio.

## 2.2 Budget

Un **budget** es un objetivo o límite de control financiero para un periodo.

Ejemplo:

- Presupuesto mensual de Azure: 10.000 EUR.

En Azure Cost Management un budget puede generar alertas, pero **no es por sí mismo un hard cap**. Alcanzar el 100 % no significa que Azure vaya a apagar automáticamente los recursos.

## 2.3 Forecast

El **forecast** es una estimación de cuánto esperamos gastar en el futuro.

Ejemplo:

- Budget: 10.000 EUR.
- Coste acumulado a día 22: 8.300 EUR.
- Forecast de cierre: 11.350 EUR.

El problema no es que hoy hayamos superado 10.000 EUR. El problema es que la tendencia indica que probablemente terminaremos por encima.

**Forecast variance vs budget:**

`(Forecast - Budget) / Budget * 100`

Ejemplo:

`(11.350 - 10.000) / 10.000 * 100 = 13,5 %`

## 2.4 Actual cost vs amortized cost

Esta diferencia es especialmente importante con Reservations y Savings Plans.

### Actual cost

Representa los cargos de manera cercana a cómo aparecen en facturación.

Si una reserva anual de 1.200 EUR se paga por adelantado, el actual cost puede reflejar la compra completa cuando se produce.

### Amortized cost

Distribuye el coste del compromiso a lo largo de su periodo y atribuye el beneficio a los recursos que lo consumen.

Para análisis FinOps y showback, el coste amortizado suele ser útil porque representa mejor el coste económico del consumo durante el tiempo.

No significa que uno sea "correcto" y el otro "incorrecto". Responden a preguntas distintas.

---

# 3. Jerarquía de Azure que debes entender

Una forma simplificada de pensar Azure es:

`Tenant -> Management Groups -> Subscriptions -> Resource Groups -> Resources`

La secuencia anterior es la representación canónica utilizada por este corpus;
no depende de un recurso gráfico externo.

## 3.1 Tenant

Un **tenant** de Microsoft Entra ID representa una instancia de identidad y directorio de una organización.

En términos prácticos, contiene identidades, aplicaciones, grupos y relaciones de acceso. Una organización puede tener uno o varios tenants, aunque muchos entornos corporativos intentan mantener una estrategia controlada para evitar fragmentación.

FinOps se relaciona con el tenant porque el gobierno, los accesos y la jerarquía global condicionan quién puede ver y administrar costes.

## 3.2 Management Group

Los **management groups** permiten agrupar subscriptions y otros management groups.

Son útiles para:

- aplicar Azure Policy a múltiples subscriptions;
- aplicar RBAC a gran escala;
- organizar entornos por unidad de negocio, geografía o función;
- analizar y gobernar costes en estructuras grandes.

Ejemplo:

```text
Tenant
|
+-- Management Group: Production
|   +-- Subscription: Ecommerce-Prod
|   +-- Subscription: Data-Prod
|
+-- Management Group: NonProduction
    +-- Subscription: Dev-Test
```

## 3.3 Subscription

Una **subscription** es un contenedor administrativo y de facturación para recursos Azure.

Es una frontera importante para:

- acceso;
- cuotas;
- políticas;
- facturación y reporting;
- separación de entornos o unidades organizativas.

FinOps no debería asumir que una subscription equivale siempre a un único producto o equipo. Depende del diseño organizativo.

## 3.4 Resource Group

Un **resource group** es un contenedor lógico de recursos que normalmente comparten ciclo de vida, aplicación, entorno o responsabilidad operativa.

Un recurso pertenece a un resource group en un momento determinado.

Desde FinOps es muy útil porque permite agrupar costes antes incluso de aplicar tags.

## 3.5 Resource

Es la instancia concreta consumida: una VM, un Storage Account, una base de datos, un App Service, un Key Vault, etc.

La granularidad de coste real disponible depende del servicio y del modelo de facturación.

---

# 4. Scopes y acceso a Cost Management

Azure Cost Management trabaja con **scopes**. Un scope define el conjunto de costes que estamos consultando o administrando.

Ejemplos típicos:

- management group;
- subscription;
- resource group;
- ciertos scopes de billing según el tipo de cuenta.

La pregunta correcta al analizar un informe es siempre:

> ¿Qué scope estoy mirando?

Dos usuarios pueden obtener cifras distintas simplemente porque están viendo scopes diferentes.

## 4.1 RBAC y costes

Para usar Cost Management se necesita acceso suficiente al scope correspondiente. Microsoft indica que el acceso de lectura es necesario para utilizar Cost Management en scopes de recursos.

En una organización madura conviene aplicar **least privilege**:

- un equipo puede necesitar leer los costes de su subscription o resource group;
- FinOps puede necesitar visibilidad transversal;
- finanzas puede necesitar scopes de billing;
- no todos necesitan permisos para modificar infraestructura.

La visibilidad de coste y la capacidad de cambiar recursos son preocupaciones relacionadas, pero no idénticas.

---

# 5. Azure Cost Management: capacidades relevantes

Microsoft Cost Management es el conjunto de herramientas FinOps nativas para analizar, monitorizar, asignar y optimizar costes Microsoft Cloud.

Para un MVP como Economicon, las capacidades más relevantes son:

1. Cost Analysis.
2. Budgets y alertas.
3. Anomaly detection / anomaly alerts.
4. Tags y tag inheritance.
5. Cost Allocation para costes compartidos.
6. Exports.
7. Azure Advisor.
8. Reservations y Savings Plans.

---

# 6. Cost Analysis

**Cost Analysis** debería ser el primer lugar para investigar una variación de gasto.

Permite analizar costes con vistas y dimensiones distintas.

Preguntas típicas:

- ¿Qué servicio cuesta más?
- ¿Qué resource group ha crecido este mes?
- ¿Qué subscription explica la desviación?
- ¿Qué tag `application` está generando el gasto?
- ¿Qué recursos concretos son los top contributors?
- ¿Cómo cambia el resultado si observo actual cost o amortized cost?

## 6.1 Método básico de investigación

Ante un aumento inesperado:

1. Seleccionar el scope correcto.
2. Comparar periodo actual vs periodo anterior.
3. Agrupar por Service name.
4. Bajar a Resource group.
5. Bajar a Resource.
6. Revisar tags de ownership/application.
7. Correlacionar con despliegues, crecimiento de tráfico o cambios de configuración.
8. Decidir si el coste es esperado, optimizable o anómalo.

No todo aumento de coste es un problema. Puede ser consecuencia de crecimiento de negocio.

---

# 7. Tagging como base de allocation

Los **tags** son pares clave-valor asociados a recursos Azure compatibles.

Ejemplo:

```text
costcenter = CC-1020
owner = web-team
application = storefront
environment = prod
businessunit = ecommerce
```

El tagging permite añadir contexto que la jerarquía por sí sola no contiene.

## 7.1 Qué problema resuelve

Supongamos una subscription compartida por tres aplicaciones. La subscription nos indica dónde está el gasto, pero no necesariamente quién lo genera.

Si cada recurso tiene `application` y `owner`, podemos crear un showback por aplicación y equipo.

## 7.2 Lo que NO debes asumir sobre tags

No todos los servicios o registros de coste se comportan exactamente igual con tags.

Además:

- un tag aplicado a un resource group no debe asumirse automáticamente como tag físico heredado por todos los recursos;
- Azure Policy puede utilizarse para requerir o modificar tags;
- Cost Management dispone de **tag inheritance**, que puede aplicar información heredada a los **registros de coste**, sin que eso implique escribir físicamente el tag en el recurso;
- existen costes que pueden no quedar asignables mediante tagging simple.

Esta distinción es muy importante en una entrevista.

## 7.3 Propuesta MVP para Economicon

Economicon puede definir cinco tags mínimos:

| Tag | Ejemplo | Objetivo |
|---|---|---|
| `costcenter` | `CC-1020` | Imputación financiera |
| `owner` | `web-team` | Responsable operativo |
| `application` | `storefront` | Producto/aplicación |
| `environment` | `prod` | prod/dev/test |
| `businessunit` | `ecommerce` | Unidad de negocio |

Reglas MVP propuestas:

- claves normalizadas en minúsculas;
- catálogo controlado para `environment`;
- `owner` debe corresponder a un equipo, no a una persona concreta cuando sea posible;
- evitar PII o información sensible en tags;
- validar tags en despliegue mediante IaC y/o Azure Policy;
- medir cumplimiento por **coste**, no solo por número de recursos.

### Por qué medir cumplimiento por coste

Supongamos:

- 100 recursos correctamente etiquetados cuestan 1 EUR cada uno;
- 1 recurso sin tags cuesta 5.000 EUR.

Cumplimiento por recursos: 100/101 = 99 %.  
Cumplimiento por coste: 100/5.100 = 1,96 %.

El primer KPI sería engañoso para FinOps.

---

# 8. Allocation, showback y chargeback

## 8.1 Allocation

**Allocation** es la práctica de asignar costes y uso a los grupos responsables o beneficiarios.

Puede apoyarse en:

- subscriptions;
- resource groups;
- tags;
- nombres;
- cuentas de billing;
- reglas derivadas;
- reglas de costes compartidos.

## 8.2 Showback

**Showback** significa mostrar a cada equipo o unidad el coste que genera o se le asigna, sin necesariamente hacer una transferencia contable real.

Ejemplo:

```text
Web Team: 4.300 EUR
Data Team: 3.100 EUR
Platform: 2.100 EUR
Unallocated: 500 EUR
```

El objetivo inicial es crear transparencia y accountability.

## 8.3 Chargeback

**Chargeback** va un paso más allá: el coste se repercute formalmente a la unidad responsable mediante procesos financieros internos.

Un MVP puede empezar por showback. Es más sencillo y permite corregir problemas de calidad de allocation antes de utilizar los datos para imputación financiera estricta.

---

# 9. Coste no asignado

El **unallocated cost** es coste que no puede asociarse de manera suficiente a un owner, aplicación, cost center u otra unidad definida por la organización.

No debe confundirse automáticamente con **shared cost**.

## 9.1 Cuatro estados recomendados en Economicon

Economicon podría clasificar cada línea de coste como:

- `allocated`: responsable conocido;
- `shared`: coste compartido conocido y pendiente o sujeto a regla de reparto;
- `unallocated`: no existe información suficiente para asignarlo;
- `excluded`: coste excluido explícitamente del modelo por una regla documentada.

Esto evita convertir todo lo difícil de asignar en "unallocated".

## 9.2 KPI de coste no asignado

`Unallocated Cost % = Unallocated Cost / Total Eligible Cost * 100`

Ejemplo:

- Coste total: 10.000 EUR.
- Coste unallocated: 500 EUR.

`500 / 10.000 * 100 = 5 %`

## 9.3 Umbrales MVP propuestos

Estos umbrales son **decisiones de diseño de Economicon**, no estándares oficiales:

- Verde: <= 5 %.
- Amarillo: > 5 % y <= 10 %.
- Rojo: > 10 %.

La meta debería endurecerse con la madurez.

---

# 10. Shared cost

Algunos costes son legítimamente compartidos:

- plataforma común;
- observabilidad;
- red central;
- seguridad;
- tooling;
- CI/CD;
- Kubernetes compartido.

Hay varias formas de distribuirlos:

1. **Equal split:** mismo porcentaje para cada consumidor.
2. **Proportional to direct spend:** proporcional al gasto directo.
3. **Usage based:** basado en uso real, si existe telemetría útil.
4. **Business metric:** usuarios, pedidos, transacciones, etc.

La regla debe ser:

- transparente;
- consistente;
- explicable;
- revisable;
- preferiblemente estable durante el periodo reportado.

No conviene buscar una precisión falsa si obtenerla cuesta más que el valor de la decisión.

---

# 11. Budgets y alertas

Los budgets sirven para establecer expectativas y disparar avisos.

Ejemplo MVP:

```text
Budget mensual: 10.000 EUR
50 %: informativo
80 %: warning
90 %: crítico
100 %: excedido
```

Una mejor implementación también utiliza **forecast alerts**, porque detectar un exceso previsto antes de alcanzarlo permite actuar.

### Importante

Un budget **no apaga recursos por defecto**. Puede integrarse con acciones o automatización, pero el diseño de esa automatización debe ser explícito y seguro.

Apagar producción automáticamente solo porque se supera un budget suele ser una mala política.

---

# 12. Anomalías

FinOps Foundation define Anomaly Management como la capacidad de detectar, identificar, alertar, investigar y gestionar eventos de coste inesperados o no previstos.

## 12.1 Qué es una anomalía

Una anomalía no es simplemente "un coste alto".

Ejemplo:

- Un clúster cuesta 5.000 EUR todos los meses. Puede ser caro, pero no anómalo.
- Log Analytics pasa de 15 EUR/día a 80 EUR/día después de un despliegue. Eso sí puede ser anómalo.

La anomalía depende de lo **esperado**.

## 12.2 Azure

Microsoft Cost Management dispone de detección y alertas de anomalías. Microsoft indica que su modelo identifica anomalías diariamente sobre uso normalizado.

Para Economicon, la señal nativa de Azure puede combinarse con reglas propias.

## 12.3 Regla determinista MVP de Economicon

Ejemplo simple:

Crear anomalía candidata cuando:

- desviación diaria > 20 % respecto al baseline, **y**
- impacto absoluto > 100 EUR/día.

Estos valores son solo un ejemplo MVP.

La doble condición evita ruido:

- +200 % sobre 1 EUR = impacto bajo;
- +5 % sobre 100.000 EUR = impacto económico alto pero podría requerir otro detector.

Un sistema más maduro usaría modelos por servicio, estacionalidad, día de semana y forecast.

## 12.4 Severidad propuesta

Ejemplo Economicon:

- **P1:** riesgo > 2.000 EUR/mes o impacto crítico.
- **P2:** 500-2.000 EUR/mes.
- **P3:** < 500 EUR/mes.

De nuevo: política interna, no estándar Azure.

## 12.5 Workflow de anomalía

1. Detectar.
2. Identificar scope y dimensión responsable.
3. Encontrar owner.
4. Confirmar si el cambio era esperado.
5. Investigar causa técnica o de negocio.
6. Estimar impacto.
7. Tomar acción.
8. Documentar resolución.
9. Marcar falso positivo si corresponde.
10. Ajustar baseline o regla si es necesario.

### KPIs útiles

- anomalías abiertas;
- impacto potencial;
- false positive rate;
- MTTA: mean time to acknowledge;
- MTTR: mean time to resolve.

---

# 13. Recomendaciones de optimización

Una recomendación FinOps no debería ser simplemente:

> Apaga esta VM.

Debería contener:

- recurso afectado;
- hallazgo;
- evidencia;
- acción propuesta;
- ahorro estimado;
- riesgo;
- owner;
- prioridad;
- estado;
- ahorro realizado después de ejecutar.

## 13.1 Taxonomía MVP para Economicon

### Rightsizing

Cambiar un recurso a una capacidad más adecuada.

Ejemplo:

- VM D8 utilizada al 8 % de CPU durante semanas.
- Propuesta: validar memoria/IO y migrar a D4.

### Scheduling / shutdown

Apagar recursos cuando no hacen falta.

Ejemplo:

- VM de desarrollo encendida 24/7.
- Uso real: lunes-viernes, 08:00-19:00.

### Orphan cleanup

Eliminar recursos huérfanos:

- discos sin adjuntar;
- IPs sin utilizar;
- snapshots antiguos;
- recursos temporales olvidados.

Siempre con validación y periodo de seguridad.

### Storage optimization

- lifecycle policies;
- mover datos a cool/cold/archive según acceso;
- revisar redundancia;
- eliminar datos sin utilidad.

### Observability optimization

- volumen de logs;
- retención;
- sampling;
- duplicados;
- tablas o categorías innecesarias.

### Rate optimization

- Reservations;
- Savings Plans;
- Azure Hybrid Benefit;
- otros descuentos aplicables.

---

# 14. Azure Advisor y rightsizing

Azure Advisor genera recomendaciones basadas en telemetría y patrones de uso, incluidas recomendaciones de coste sobre recursos infrautilizados.

Debe ser una **fuente de recomendaciones**, no una orden automática.

Antes de aplicar rightsizing conviene comprobar:

- CPU;
- memoria;
- IOPS;
- throughput;
- picos;
- estacionalidad;
- HA;
- SLA;
- crecimiento esperado;
- requisitos de licencia;
- dependencia con otros componentes.

## 14.1 Qué significa rightsizing

**Rightsizing** significa ajustar la capacidad del recurso a las necesidades reales del workload.

Puede ser:

- reducir tamaño;
- aumentar tamaño;
- cambiar familia/SKU;
- cambiar arquitectura;
- eliminar;
- consolidar.

FinOps no es "downsizing". Si un recurso está infradimensionado y degrada negocio, rightsizing puede significar aumentarlo.

---

# 15. Commitments: Reservations y Savings Plans

Un **commitment** es un compromiso financiero asumido a cambio de una tarifa inferior.

## 15.1 Reservations

Azure Reservations ofrecen descuentos al comprometerse normalmente durante uno o tres años para determinados productos/recursos elegibles.

El descuento se aplica al uso que coincida con las condiciones de la reserva.

Ventaja:

- descuento alto para uso estable y predecible.

Riesgo:

- comprometer capacidad que después no se utiliza.

## 15.2 Savings Plans for Compute

Savings Plans son compromisos de gasto horario para compute elegible, con mayor flexibilidad que una reserva específica en ciertos escenarios.

Ventaja:

- flexibilidad entre recursos elegibles.

Riesgo:

- pagar compromiso no aprovechado si cae el uso.

## 15.3 Orden recomendado de análisis

Una regla FinOps muy útil:

1. limpiar desperdicio obvio;
2. rightsizing;
3. estabilizar baseline;
4. analizar commitments;
5. comprar únicamente la parte suficientemente estable.

Si compras compromiso antes de rightsizing, puedes comprometerte a pagar por un patrón de consumo inflado.

## 15.4 KPIs de commitments

**Utilization:** qué porcentaje del compromiso comprado se usa.  
**Coverage:** qué porcentaje del uso elegible está cubierto por compromisos.

No deben maximizarse ciegamente ambos al 100 %. Se busca equilibrio entre descuento y flexibilidad.

---

# 16. Exports y datos para Economicon

Para un MVP externo a Azure Portal, Economicon necesita ingerir datos de coste.

Cost Management permite programar **Exports** a Azure Storage. Microsoft soporta datasets de coste y uso y ofrece formatos como CSV y, según configuración/dataset, opciones como Parquet. También existe soporte para datos alineados con **FOCUS**.

FOCUS es una especificación abierta para normalizar datos de coste y uso cloud y facilitar análisis consistentes entre proveedores y herramientas.

## 16.1 Pipeline conceptual MVP

```text
Azure Cost Management Export
        |
        v
Azure Storage
        |
        v
Economicon ingestion
        |
        +--> Normalización
        +--> Allocation / tagging
        +--> KPIs
        +--> Detección de anomalías
        +--> Recomendaciones
        +--> Dashboard / API
```

## 16.2 Qué guardar

Como mínimo:

- fecha;
- subscription;
- resource group;
- resource ID;
- service/product/meter relevantes;
- coste;
- moneda;
- pricing/charge type cuando proceda;
- tags;
- benefit/commitment information cuando proceda;
- identificadores de invoice/billing si el modelo los requiere.

No conviene diseñar el modelo interno copiando ciegamente cada columna del proveedor. Es preferible crear una capa normalizada.

---

# 17. FOCUS en pocas palabras

FOCUS significa **FinOps Open Cost and Usage Specification**.

Su objetivo es proporcionar un esquema común y abierto para datos de coste y uso.

Para Economicon tiene interés porque reduce acoplamiento a un único proveedor:

```text
Azure ----\
AWS ------- > Modelo FOCUS/normalizado -> Economicon
GCP ------/
```

No significa que todos los proveedores sean idénticos. Siempre existirán conceptos específicos, pero se reduce la cantidad de lógica exclusiva por proveedor.

Para un MVP solo Azure no es obligatorio implementar todo FOCUS, pero diseñar pensando en normalización evita deuda técnica.

---

# 18. KPIs mínimos de Economicon

Un MVP no necesita decenas de métricas. Necesita pocas métricas accionables.

## KPI 1. Monthly Cost

Coste del mes actual.

## KPI 2. Budget Variance

`(Actual - Budget) / Budget * 100`

Para periodos incompletos debe interpretarse con cuidado.

## KPI 3. Forecast vs Budget

`(Forecast - Budget) / Budget * 100`

Permite anticipar overspend.

## KPI 4. Forecast Error

Una fórmula sencilla al cierre:

`abs(Forecast - Actual) / Actual * 100`

Permite saber si nuestro forecast mejora con el tiempo.

## KPI 5. Unallocated Cost %

`Unallocated / Eligible Cost * 100`

## KPI 6. Tagging Compliance by Cost

`Correctly Tagged Cost / Taggable Eligible Cost * 100`

## KPI 7. Savings Realization

Diferencia entre ahorro **identificado** y ahorro **realmente verificado**.

Ejemplo:

- recomendaciones aceptadas: 1.000 EUR/mes;
- ahorro verificado: 620 EUR/mes.

Savings realization = 62 %.

## KPI 8. Anomaly MTTA / MTTR

Tiempo medio hasta reconocimiento y resolución.

## KPI 9 opcional. Commitment Utilization

Especialmente útil cuando la empresa ya compra reservas o Savings Plans.

## KPI 10 opcional. Unit Cost

Ejemplos:

- EUR/pedido;
- EUR/cliente activo;
- EUR/1.000 API calls;
- EUR/transacción.

Este KPI acerca FinOps al valor de negocio.

---

# 19. Caso práctico completo: Contoso Retail + Economicon

## 19.1 Contexto

Empresa ficticia: **Contoso Retail**.

Azure contiene:

- `Ecommerce-Prod`;
- `Data-Prod`;
- `Dev-Test`.

Budget mensual total: **10.000 EUR**.

Distribución inicial:

La tabla siguiente es la fuente canónica de la distribución simulada.

| Servicio | Coste mensual | Peso |
|---|---:|---:|
| Virtual Machines | 4.200 EUR | 42,0 % |
| Azure SQL Database | 2.100 EUR | 21,0 % |
| App Service | 1.300 EUR | 13,0 % |
| Storage Accounts | 900 EUR | 9,0 % |
| Log Analytics | 850 EUR | 8,5 % |
| Backup, red y otros | 650 EUR | 6,5 % |
| **Total** | **10.000 EUR** | **100 %** |

## 19.2 Inform

Economicon ingiere el export y calcula:

- coste total: 10.000 EUR;
- allocated: 8.900 EUR;
- shared: 600 EUR;
- unallocated: 500 EUR;
- unallocated rate: 5 %;
- tagging compliance by cost: 91 %.

Showback:

| Allocation target | Coste |
|---|---:|
| Ecommerce | 4.300 EUR |
| Data | 3.100 EUR |
| Platform/shared | 2.100 EUR |
| Unallocated | 500 EUR |

Economicon detecta que parte de los 500 EUR sin asignar corresponde a recursos sin `owner` y `application`.

## 19.3 Forecast

A día 22:

- coste acumulado: 8.300 EUR;
- forecast: 11.350 EUR;
- budget: 10.000 EUR;
- forecast variance: +13,5 %.

La situación requiere investigación antes de asumir que hay desperdicio.

## 19.4 Anomaly

El gasto diario de Log Analytics aumenta de unos 17 EUR/día a 45 EUR/día tras una release.

Investigación:

1. Cost Analysis muestra el crecimiento en Log Analytics.
2. Resource group apunta a `rg-storefront-prod`.
3. `owner=web-team`.
4. El equipo confirma un cambio de logging a nivel DEBUG en producción.
5. Se estima impacto de +300 EUR/mes.

Clasificación:

- anomalía válida;
- owner: Web Team;
- acción: volver a nivel INFO y revisar retención;
- ahorro potencial: 300 EUR/mes.

## 19.5 Optimize

Economicon consolida recomendaciones:

| Hallazgo | Acción | Ahorro estimado/mes |
|---|---|---:|
| VM sobredimensionada | Rightsizing | 220 EUR |
| VM desarrollo 24/7 | Apagado programado | 150 EUR |
| Discos sin adjuntar | Eliminar tras validación | 120 EUR |
| Exceso de Log Analytics | Reducir ingestión/retención | 300 EUR |
| Storage antiguo en Hot | Lifecycle/tiering | 100 EUR |
| **Total** |  | **890 EUR/mes** |

Forecast después de optimización inmediata:

La comparación canónica se expresa con los importes de las tablas y la ecuación
siguiente, sin depender de una imagen externa.

`11.350 - 890 = 10.460 EUR`

Todavía está 460 EUR sobre budget, pero el problema se ha reducido notablemente.

## 19.6 Commitments

Se descubre una carga compute estable de unos 2.000 EUR/mes.

Antes de comprar un commitment:

1. se aplica rightsizing;
2. se esperan varias semanas para confirmar baseline;
3. se calcula cobertura deseada;
4. se compara Reservation vs Savings Plan;
5. se evita comprometer el 100 % si existe incertidumbre.

## 19.7 Operate

Se implantan reglas:

- tags obligatorios;
- Azure Policy para compliance;
- revisión semanal de anomalías;
- revisión mensual de recommendations;
- budget + forecast alerts;
- dashboard de KPIs;
- owner obligatorio en recomendaciones;
- verificación posterior del ahorro.

Ahora Economicon no solo muestra gasto. Crea un ciclo operativo FinOps.

---

# 20. Reglas MVP de Economicon resumidas

## 20.1 Tagging

Obligatorios:

- `costcenter`;
- `owner`;
- `application`;
- `environment`;
- `businessunit`.

Validación:

- catálogo controlado;
- Policy/IaC;
- compliance por coste;
- reportar recursos y coste incumplidor.

## 20.2 Coste no asignado

Estados:

- allocated;
- shared;
- unallocated;
- excluded.

KPI:

`Unallocated Cost / Eligible Cost`.

Meta inicial sugerida: <= 5 %.

## 20.3 KPIs

MVP:

1. Monthly Cost.
2. Budget Variance.
3. Forecast vs Budget.
4. Forecast Error.
5. Unallocated Cost %.
6. Tagging Compliance by Cost.
7. Savings Realization.
8. Anomaly MTTA/MTTR.

## 20.4 Anomalías

MVP:

- señal Azure + regla propia;
- baseline diario;
- umbral absoluto y relativo;
- owner;
- severidad;
- estado;
- causa y resolución;
- false positive tracking.

## 20.5 Recomendaciones

Campos mínimos:

- resource/scope;
- category;
- evidence;
- recommended action;
- estimated saving;
- confidence;
- risk;
- owner;
- status;
- realized saving.

Estados sugeridos:

`new -> reviewed -> accepted/rejected -> implemented -> verified`

---

# 21. Modelo de datos conceptual de Economicon

Un modelo MVP podría tener:

## CostRecord

```text
id
date
provider
subscription_id
resource_group
resource_id
service
cost
currency
tags
allocation_status
allocation_target
```

## Budget

```text
scope
period
amount
currency
thresholds
```

## Anomaly

```text
id
scope
metric_date
expected_cost
observed_cost
absolute_delta
relative_delta
severity
owner
status
root_cause
```

## Recommendation

```text
id
resource_id
category
current_cost
estimated_saving
confidence
risk
owner
status
realized_saving
```

El MVP debería separar los datos originales del proveedor de los datos derivados por Economicon.

---

# 22. Errores comunes que deberías evitar al explicar FinOps

## Error 1: "FinOps es reducir la factura"

Incompleto. FinOps busca maximizar valor y responsabilidad económica.

## Error 2: "Budget de Azure detiene el gasto"

Falso por defecto. Un budget alerta; no actúa como hard cap automático.

## Error 3: "Una recomendación de Advisor debe aplicarse"

Falso. Es una señal que debe validarse contra requisitos del workload.

## Error 4: "Si un recurso no tiene tag, siempre es unallocated"

No necesariamente. Puede asignarse mediante jerarquía, regla derivada o clasificación shared.

## Error 5: "Todo shared cost es unallocated"

Falso. Shared significa que conocemos su naturaleza compartida; unallocated significa que carecemos de información suficiente para asignarlo.

## Error 6: "Rightsizing significa hacer todo más pequeño"

Falso. Significa ajustar al tamaño correcto.

## Error 7: "Una Reservation reduce el consumo"

Falso. Es un descuento de facturación sobre uso coincidente; no cambia el runtime por sí misma.

## Error 8: "Forecast y budget son lo mismo"

Falso. Budget expresa una expectativa/objetivo; forecast predice el resultado probable.

---

# 23. Glosario esencial

## Tenant

Instancia de Microsoft Entra ID que representa el directorio de identidades de una organización y actúa como raíz de contexto organizativo para muchos elementos de Azure.

**Forma de recordarlo:** identidad y organización.

## Subscription

Contenedor administrativo y de facturación que agrupa recursos y actúa como scope importante de acceso, cuotas, políticas y costes.

**Forma de recordarlo:** frontera operativa y de coste.

## Resource Group

Contenedor lógico de recursos Azure, normalmente agrupados por ciclo de vida, aplicación o entorno.

**Forma de recordarlo:** agrupación operativa.

## Tag

Par clave-valor utilizado para añadir metadatos a recursos compatibles y facilitar gobierno, filtrado y allocation.

**Forma de recordarlo:** contexto que la jerarquía no expresa.

## Showback

Mostrar a equipos o unidades los costes que generan o se les asignan, sin repercusión contable obligatoria.

**Forma de recordarlo:** "te enseño tu factura interna".

## Forecast

Estimación del coste futuro basada en comportamiento histórico, tendencias, cambios previstos y otros factores.

**Forma de recordarlo:** "a este ritmo, terminaremos en...".

## Anomaly

Coste o uso inesperado respecto al comportamiento normal o esperado.

**Forma de recordarlo:** desviación significativa, no simplemente coste alto.

## Commitment

Compromiso financiero de consumo o gasto a cambio de un precio reducido, como Reservations o Savings Plans.

**Forma de recordarlo:** descuento a cambio de comprometerse.

## Rightsizing

Ajuste de la capacidad/configuración de un recurso para adecuarla a la necesidad real del workload.

**Forma de recordarlo:** tamaño correcto, no tamaño mínimo.

---

# 24. Preguntas de evaluación con respuesta modelo

## 1. ¿Qué es FinOps?

**Respuesta modelo:**  
FinOps es una práctica operativa y cultural que busca maximizar el valor empresarial de la tecnología mediante responsabilidad compartida entre ingeniería, finanzas, producto y negocio. Se apoya en visibilidad del coste y uso, optimización y procesos operativos continuos.

## 2. ¿Cómo aplicarías FinOps básico en Azure?

**Respuesta modelo:**  
Empezaría definiendo scopes y ownership, utilizaría Cost Analysis para entender gasto, implementaría una estrategia de allocation basada en jerarquía y tags, configuraría budgets y alertas, crearía forecast, investigaría anomalías, consumiría recomendaciones de Advisor y mediría el ahorro realizado. Después convertiría estas actividades en un ciclo periódico Inform-Optimize-Operate.

## 3. ¿Por qué es importante tagging?

**Respuesta modelo:**  
Porque permite asociar coste a dimensiones de negocio que la jerarquía de Azure no expresa por sí sola, como aplicación, owner o cost center. Sin embargo, tags no son la única estrategia de allocation y hay que considerar servicios no taggeables, tag inheritance y costes compartidos.

## 4. ¿Qué harías con el coste no asignado?

**Respuesta modelo:**  
Lo mediría como porcentaje del coste elegible, identificaría sus principales contributors y crearía acciones para reducirlo. Separaría unallocated de shared y excluded. En un MVP podría fijar una meta inicial del 5 %, sabiendo que el umbral es una decisión interna.

## 5. ¿Qué diferencia hay entre showback y chargeback?

**Respuesta modelo:**  
Showback ofrece visibilidad del coste a los responsables sin necesidad de realizar una imputación financiera formal. Chargeback repercute ese coste de manera contable o presupuestaria a la unidad responsable.

## 6. ¿Qué diferencia hay entre budget y forecast?

**Respuesta modelo:**  
Budget es la cantidad objetivo o planificada; forecast es la predicción de cuánto se espera terminar gastando. Un forecast por encima del budget permite actuar antes de que se produzca el overspend.

## 7. ¿Un budget de Azure detiene recursos al alcanzar el 100 %?

**Respuesta modelo:**  
No por defecto. Azure Cost Management budgets generan seguimiento y alertas. Cualquier automatización que modifique recursos debe diseñarse explícitamente y con controles adecuados.

## 8. ¿Qué es una anomalía de coste?

**Respuesta modelo:**  
Es un nivel de coste o uso que se desvía de lo esperado. Un coste muy alto puede no ser anómalo si es normal para ese workload. Para gestionarla hacen falta detección, owner, investigación, resolución y aprendizaje del falso positivo.

## 9. ¿Aplicarías automáticamente una recomendación de Azure Advisor?

**Respuesta modelo:**  
No. Advisor aporta evidencia y posibles optimizaciones, pero hay que validar rendimiento, memoria, I/O, picos, SLA, crecimiento esperado y restricciones de negocio antes de aplicar el cambio.

## 10. ¿Qué es rightsizing?

**Respuesta modelo:**  
Es ajustar el recurso a la capacidad adecuada para el workload. Puede implicar reducir, aumentar, cambiar SKU, consolidar o incluso eliminar un recurso. No equivale siempre a downsizing.

## 11. ¿Qué es un commitment?

**Respuesta modelo:**  
Es un compromiso financiero a cambio de una tarifa reducida. En Azure los ejemplos principales son Reservations y Savings Plans. Deben comprarse sobre una base de uso suficientemente estable para evitar compromiso desaprovechado.

## 12. ¿Por qué harías rightsizing antes de comprar commitments?

**Respuesta modelo:**  
Porque si compro un compromiso sobre consumo sobredimensionado, puedo fijar financieramente un nivel de gasto que después quiero eliminar. Primero optimizo uso, luego comprometo la parte estable restante.

## 13. ¿Qué KPIs escogerías para un MVP?

**Respuesta modelo:**  
Coste mensual, budget variance, forecast vs budget, forecast error, unallocated cost %, tagging compliance por coste, savings realization y MTTA/MTTR de anomalías. Si ya existen commitments, añadiría utilization y coverage.

## 14. ¿Cómo investigarías un aumento de costes en Azure?

**Respuesta modelo:**  
Verificaría el scope y periodo, compararía contra baseline, agruparía por servicio, resource group y recurso, usaría tags para encontrar owner y aplicación, correlacionaría el aumento con despliegues o demanda y decidiría si es crecimiento esperado, anomalía o desperdicio.

## 15. ¿Qué valor aporta Economicon si Azure ya tiene Cost Management?

**Respuesta modelo:**  
Economicon puede crear una capa organizativa propia sobre los datos: reglas homogéneas de allocation, KPIs internos, workflow de anomalías, priorización de recomendaciones, histórico de decisiones y savings realization. Cost Management seguiría siendo una fuente nativa clave, no un competidor que deba replicarse por completo.

---

# 25. Respuesta corta a los tres bloques del enunciado

## 1. FinOps básico aplicado a Azure Cost Management simulado

En un entorno simulado empezaría creando visibilidad del gasto con Cost Analysis, establecería scopes y ownership, usaría jerarquía y tags para allocation, configuraría budgets y forecast, detectaría anomalías y analizaría optimizaciones con Advisor. Después convertiría los hallazgos en acciones operativas y mediría el ahorro realizado. El proceso seguiría el ciclo Inform-Optimize-Operate.

## 2. Reglas MVP de Economicon

**Tagging:** cinco tags mínimos (`costcenter`, `owner`, `application`, `environment`, `businessunit`) y compliance medido por coste.  
**Coste no asignado:** separar allocated/shared/unallocated/excluded y controlar `Unallocated Cost %`.  
**KPIs:** coste, budget variance, forecast, forecast error, unallocated %, tagging compliance, savings realization y MTTA/MTTR.  
**Anomalías:** combinar señal nativa con umbrales internos, owner, severidad y workflow de investigación.  
**Recomendaciones:** rightsizing, scheduling, cleanup, storage, observability y commitments, siempre con ahorro estimado, riesgo, owner, estado y ahorro verificado.

## 3. Glosario

- **Tenant:** contexto de identidad/organización de Entra ID.
- **Subscription:** contenedor administrativo y de facturación.
- **Resource group:** agrupación lógica de recursos.
- **Tag:** metadato clave-valor para contexto y allocation.
- **Showback:** mostrar internamente el coste asignado.
- **Forecast:** predicción del gasto futuro.
- **Anomaly:** desviación inesperada de coste/uso.
- **Commitment:** compromiso financiero por descuento.
- **Rightsizing:** ajustar capacidad al tamaño correcto.

---

# 26. Checklist de diseño de un MVP FinOps razonable

Antes de considerar Economicon "usable", comprobaría:

- [ ] Existe un scope de datos claramente definido.
- [ ] El coste total cuadra razonablemente con la fuente Azure seleccionada.
- [ ] Se diferencia actual cost de amortized cost cuando aplica.
- [ ] Existe estrategia de allocation documentada.
- [ ] Shared no se mezcla con unallocated.
- [ ] Los tags mínimos tienen ownership.
- [ ] Compliance se mide también por coste.
- [ ] Existe budget y forecast.
- [ ] Las anomalías tienen owner y workflow.
- [ ] Las recomendaciones tienen evidencia, riesgo y ahorro estimado.
- [ ] El ahorro se verifica después de la implementación.
- [ ] Rightsizing se analiza antes de commitments.
- [ ] Existen controles de acceso y least privilege.
- [ ] Las reglas internas se diferencian de requisitos oficiales.
- [ ] Los datos simulados se etiquetan explícitamente como simulados.

---

# 27. Referencias oficiales prioritarias

## Microsoft Learn

1. **What is Microsoft Cost Management**  
   https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/overview-cost-management

2. **Cost Management documentation**  
   https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/

3. **Quickstart - Start using Cost Analysis**  
   https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/quick-acm-cost-analysis

4. **Understand Cost Management data**  
   https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/understand-cost-mgt-data

5. **Introduction to cost allocation**  
   https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/cost-allocation-introduction

6. **View amortized benefit costs**  
   https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/view-amortized-costs

7. **Azure Reservations**  
   https://learn.microsoft.com/en-us/azure/cost-management-billing/reservations/save-compute-costs-reservations

8. **Plan to manage Azure costs**  
   https://learn.microsoft.com/en-us/azure/cost-management-billing/understand/plan-manage-costs

9. **Protect your resource hierarchy**  
   https://learn.microsoft.com/en-us/azure/governance/management-groups/how-to/protect-resource-hierarchy

## FinOps Foundation

10. **FinOps Framework**  
    https://www.finops.org/framework/

11. **FinOps Phases**  
    https://www.finops.org/framework/phases/

12. **Allocation capability**  
    https://www.finops.org/framework/capabilities/allocation/

13. **Anomaly Management capability**  
    https://www.finops.org/framework/capabilities/anomaly-management/

14. **Forecasting capability**  
    https://www.finops.org/framework/capabilities/forecasting/

15. **FinOps Terminology**  
    https://framework.finops.org/assets/terminology/

---

# 28. Nota sobre las reglas de Economicon

Las siguientes reglas de este documento son propuestas para un **MVP**, no estándares externos:

- cinco tags obligatorios concretos;
- objetivo inicial de unallocated <= 5 %;
- regla de anomalía de +20 % y +100 EUR/día;
- niveles P1/P2/P3;
- workflow y estados de recommendations;
- conjunto mínimo de KPIs.

La implementación real debería calibrarse con:

- volumen de gasto;
- número de subscriptions;
- estructura organizativa;
- granularidad del dato;
- criticidad de workloads;
- madurez FinOps;
- tolerancia al ruido;
- objetivos de negocio.

La idea correcta no es copiar umbrales. Es construir un sistema explicable que convierta coste en accountability y acciones verificables.
