# Coste de infraestructura AWS para el caso de negocio

Actualización 24/10: el límite vigente del proyecto es **30 EUR**. La ampliación
de Grafana/Atlas y los escenarios con IVA supuesto y margen se calculan en
[atlas.py](atlas.py) y [atlas-resultados.json](atlas-resultados.json). Un ciclo de
dos horas se estima en23,40EUR; tres ciclos de dos horas en39,42EUR, por encima
del límite. El corte del22Oct siguiente conserva sus hipótesis históricas; los
60EUR que menciona ya no son el presupuesto autorizado.

Estimación a 22 de octubre de 2026, dirigida a Lucía para el caso de negocio.
Mantener la arquitectura Terraform actual encendida 730 horas cuesta aproximadamente
**1.289 USD / 1.150 EUR al mes sin IVA**, con el consumo pequeño supuesto abajo.
El presupuesto de **60 EUR para ensayos y defensa** corresponde a un uso temporal;
no financia un mes de esta arquitectura. No se han desplegado aplicaciones para
obtener estas cifras ni se ha medido su capacidad.

## Alcance y método

Referencia: commit `8e879dae3f23d52f46ea2b625ca1f2eebd22cd4a`,
[Terraform de aplicación](../../../infra/aws-reference/),
[control CI/CD](../../../infra/aws-bootstrap/) y
[preparación y receta de ensayo](../../deployment/aws-defensa.md).
Aplicación en Irlanda `eu-west-1`, control en París `eu-west-3`, servicios
globales/edge con configuración en `us-east-1`; usuarios europeos.

Tarifas públicas bajo demanda, Linux x86, sin Free Tier, créditos, Savings Plans,
reservas ni descuentos privados. Mes normalizado de 730 horas. Moneda base USD;
EUR = USD / 1,1205, referencia [BCE del 22/10/2026](https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/eurofxref-graph-usd.en.html).
No es el cambio garantizado de una futura factura. Todos los importes excluyen
IVA y otros impuestos, comisiones de cambio, soporte de pago y trabajo humano.
Si se aplica un impuesto a tipo `t`, el importe correspondiente es `neto × (1+t)`;
el cálculo no determina el tratamiento fiscal de la cuenta.

[precios.json](precios.json) fija 43 tarifas con unidades, fuentes, SKU cuando
existe y fecha; [catalogos.json](catalogos.json) conserva versiones y hashes de
los catálogos descargados. Las cantidades de consumo son hipótesis editables en
[calcular.py](calcular.py). El cálculo funciona offline, sin credenciales ni SDK:

```console
python docs/planning/costes-aws/calcular.py
```

Genera [resultados.json](resultados.json) y [desglose.csv](desglose.csv).
Se acumula con Decimal sin redondear partidas; aquí se redondea sólo la presentación.
Los precios `current` pueden cambiar; el JSON fijado permite repetir este corte.

## Arquitectura y coste mensual central

| Partida | Cantidad y tarifa USD | USD/mes |
|---|---|---:|
| Fargate | 6 tareas de 0,5 vCPU y 1 GiB; 0,04048/vCPU-h + 0,004445/GiB-h | 108,12 |
| RDS PostgreSQL | 2 bases db.t4g.medium Multi-AZ × 0,138/h | 201,48 |
| RDS GP3 | 2 × 20 GB lógicos × 0,254/GB-mes Multi-AZ | 10,16 |
| RabbitMQ | Un cluster Multi-AZ mq.m5.large, 3 nodos, 0,963/h por cluster | 702,99 |
| RabbitMQ EBS | 200 GB por nodo × 3 × 0,11/GB-mes | 66,00 |
| NAT Gateway | 3 × 0,048/h | 105,12 |
| IPv4 pública | 3 IP de NAT × 0,005/h | 10,95 |
| ALB interno | 1 × 0,0252/h, sin LCU aún | 18,40 |
| Seguridad, DNS y descubrimiento | WAF 1 ACL/1 regla, 2 zonas DNS, 4 registros Cloud Map, 1 KMS, 8 secretos | 11,60 |
| **Infraestructura fija** | **Suma, aunque apenas haya usuarios** | **1.234,82** |
| S3 y ECR | 20 GB-mes S3 incluyendo versiones, 3 GB-mes imágenes | 0,76 |
| Operación variable | Logs, métricas, LCU, Cognito, consultas y reserva de control | 29,59 |
| Operaciones de ingesta | PUT/GET S3 | 0,09 |
| Red variable | CloudFront, WAF, NAT procesado y reserva de transferencia | 11,88 |
| CI/CD variable | 4 ciclos mensuales up/down | 8,80 |
| IA variable | Nova Micro y Titan V2 | 3,06 |
| **Total central** | **Sin IVA** | **1.289,00** |

No duplicar los precios de standby RDS o los tres nodos del cluster MQ: ya están
incluidos en sus tarifas de cómputo. El disco de RabbitMQ es provisionado, no sólo
los mensajes efectivamente almacenados: [precios MQ](https://aws.amazon.com/amazon-mq/pricing/),
[disco por tipo de broker](https://docs.aws.amazon.com/amazon-mq/latest/developer-guide/rmq-broker-instance-types.html).
RabbitMQ con sus discos representa cerca del 60 % del total central.
El máximo de autoscaling RDS de 100 GB por base no es almacenamiento inicial
preasignado. Los 20 GiB efímeros incluidos de cada tarea Fargate no añaden disco extra.

Las demás tarifas regionales de la tabla proceden de los catálogos oficiales
identificados por partida en `precios.json`, incluidos
[ECS Irlanda](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonECS/current/eu-west-1/index.json),
[RDS Irlanda](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRDS/current/eu-west-1/index.json),
[ALB Irlanda](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSELB/current/eu-west-1/index.json)
y [NAT](https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/natgateway.json).

## Hipótesis de consumo y sensibilidad

El central supone al mes 100 usuarios activos Cognito, 1 millón de peticiones
HTTPS/WAF/Function, 100 GB salientes de CloudFront, 10 GB procesados por NAT,
10 GB de logs ingeridos y 5 GB-mes retenidos, 60 métricas custom equivalentes,
3 alarmas estándar, 0,25 LCU promedio y 1 millón de consultas DNS. Cognito nuevo
sin tier explícito usa [Essentials por defecto](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-cognito-userpool.html),
cotizado a 0,015 USD/MAU sin deducir franquicias. No se supone SMS de MFA.

Container Insights está activado: 60 métricas equivalentes es una provisión de
coste, no un inventario medido de las dimensiones que publicará el cluster.
La reserva explícita de 2 USD/mes cubre provisionalmente DynamoDB de lease/PITR,
SNS, SQS, Scheduler y logs del control París; otra de 1 USD cubre transferencia
entre AZ/regiones. Son supuestos, no precios de un servicio ni topes de factura.
Hay que sustituirlos por consumo observado tras el primer ensayo.

La ingesta ya usa processor y RDS incluidos en el fijo. Se presupuestan 10.000
PUT/COPY/LIST y 100.000 GET, más 10 millones de tokens de embeddings, sin contratar
un OCR externo. Muchas páginas, reingestas, versiones S3 retenidas o concurrencia
podrían exigir más capacidad que la modelada.

IA utiliza los modelos de la receta AWS: EU Nova Micro bajo demanda y Titan Text
Embeddings V2. Tarifas Irlanda del [catálogo Bedrock](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/eu-west-1/index.json):
0,04 USD/millón de tokens de entrada, 0,16 USD/millón de salida y 0,026004 USD/millón
de embeddings. El central usa 50 millones de entrada + 5 millones de salida +
10 millones de embeddings: 2,00 + 0,80 + 0,26004 USD. Se cuentan los tokens de
**todas** las llamadas, contexto RAG, reformulaciones y reintentos; no se infiere
un coste por pregunta sin medirlos. No se aplican caché, batch ni throughput reservado.
Estas tarifas no se trasladan a los ensayos históricos con OpenRouter/otros modelos.

| Escenario reproducible | USD/mes | EUR/mes sin IVA |
|---|---:|---:|
| Plantilla real HA, consumos variables ×0,1 | 1.251,39 | 1.116,82 |
| Plantilla real HA, central | 1.289,00 | 1.150,38 |
| Plantilla real HA, consumos variables ×10 | 1.665,02 | 1.485,96 |
| Piloto continuo hipotético, central | 538,88 | 480,92 |

El intervalo **1.117–1.486 EUR/mes** es sensibilidad a cantidades supuestas, no
intervalo estadístico ni límite máximo. El piloto hipotético reduce a una tarea
por servicio, dos RDS Single-AZ, un NAT y un broker único m5.large con 200 GB.
Pierde redundancia y requiere cambiar IaC hardcodeada; no está implementado ni
aprobado. No representa capacidad validada para un número de clientes o un SLA.

Sobrecostes fuera del central: CPU excedentaria de RDS T4g a 0,075 USD/vCPU-h;
backups por encima de la asignación incluida o snapshots retenidos a 0,095 USD/GB-mes;
crecer ambas bases de 20 a 100 GB añade 40,64 USD/mes de disco Multi-AZ.
El tráfico grande, más logs/dimensiones, escalado, despliegues con tareas solapadas,
reintentos de CI y recursos que sobrevivan al destroy pueden superar el intervalo.
No se incluyen compra del dominio, otros entornos, Grafana externo, correo de pago,
servicios Azure reales, licencias, personal, mantenimiento ni recuperación operativa.

## Ensayos temporales y defensa

Tres ciclos (dos ensayos y defensa), conservando la topología HA original:

| Horas facturables por ciclo | Horas totales | USD total | EUR sin IVA | EUR con reserva adicional 20 % |
|---|---:|---:|---:|---:|
| 2 | 6 | 30,16 | 26,91 | 32,30 |
| 4 | 12 | 40,45 | 36,10 | 43,32 |
| 8 | 24 | 61,02 | 54,46 | 65,35 |

Cada duración incluye aprovisionamiento, espera, calentamiento, comprobaciones,
uso y retirada; no es sólo el tiempo de la presentación de diez minutos. Se
suponen horas enteras para absorber redondeos de NAT/ALB. Los recursos reales
pueden tener ventanas de facturación distintas: falta medirlas.

Se incluyen para el conjunto 540 minutos de CodeBuild (180 por ciclo up+down)
a 0,01 USD/min y 600 action-minutes V2 a 0,002 USD/min; las aprobaciones manuales
no consumen action-minutes. Estas duraciones son provisiones, no tiempos de builds
medidos: [CodeBuild](https://aws.amazon.com/codebuild/pricing/),
[CodePipeline](https://aws.amazon.com/codepipeline/pricing/).

El cálculo demo añade control persistente un mes, S3 2 GB-mes, ECR 3 GB-mes,
dos secretos de control, reserva KMS de un mes completo, una zona pública y una
privada por ciclo, 5 USD adicionales para residuos, 1 GB saliente y 5 GB NAT,
1 GB de logs, cinco MAU y 1 millón/0,1 millón/1 millón de tokens entrada/salida/embeddings.
Estos consumos son totales del conjunto, no por ciclo. La zona DNS se cobra
por mes iniciado, sin prorrateo: [Route53](https://aws.amazon.com/route53/pricing/).

El rango no descuenta el gasto ya realizado en la cuenta ni verifica saldo.
El caso de ocho horas supera 60 EUR al añadir 20 % de reserva, incluso antes de
impuestos. Por ello **esta estimación no desbloquea el ensayo ni autoriza gasto**:
`estimated_cycle_eur` y `remaining_budget_eur` siguen sin rellenarse con conjeturas.
Primero hay que fijar duración/retirada, cuota efectiva, presupuesto restante
contrastado y estimación específica del ciclo, además de revisiones y DNS.
La zona/roles/conexión preparados previamente sí proceden de autorización expresa
del usuario; este cálculo no ha añadido recursos ni solicitudes AWS.

## Mediciones futuras en el entorno definitivo

Lucía comunicó tiempos de su ordenador y propuso repetirlos en el entorno final;
Alejandro indicó que el primer despliegue espera aprobación de dos servicios.
Es una dependencia de planificación, no un resultado de rendimiento AWS.
Antes de una campaña se deben fijar RC por SHA/digests, variables Terraform y
topología efectiva, versiones de datos y banco de consultas, modelo/configuración
RAG, caché/calor inicial, concurrencia, repeticiones, métricas y criterio de éxito.
También límites de tokens/ingesta, presupuesto y condición de parada, observador,
ventana autorizada y mecanismo de apagado. No se han lanzado benchmarks ni se
promete que AWS mejore los tiempos locales. El coste mensual no demuestra
latencia, calidad, disponibilidad ni beneficio económico.

## Texto breve para Lucía

> Con la arquitectura AWS prevista y precios de Irlanda del 22/10/2026, mantener
> el servicio encendido 730 h/mes se estima en unos 1.150 EUR/mes sin IVA, sin
> depender de Free Tier. La sensibilidad de consumo modelada es de 1.117–1.486
> EUR/mes; RabbitMQ con tres nodos y sus discos concentra cerca del 60 %. La IA
> está separada: unos 3,06 USD/mes para las cantidades de tokens supuestas, que
> aún no son consumo medido. Un piloto Single-AZ reducido rondaría 481 EUR/mes,
> pero requiere una decisión de arquitectura y pierde redundancia. Los ensayos
> de defensa se presupuestan aparte por horas: tres ciclos de cuatro horas
> facturables suman unos 36 EUR sin IVA antes de reserva adicional. Son costes
> de planificación, no factura ni prueba de rendimiento; las mediciones AWS
> dependerán del despliegue autorizado, cuotas y un banco/RC congelados.

Borrador local para revisión; no enviado por Discord ni incorporado a la memoria
canónica. Encargo recibido desde HAL 9000, chat
`01a1270c-e332-7462-9c90-706d49ade92c`; petición de costes comunicada por Lucía
`1562832651935682725` y seguimiento de medidas `1562854437217771543` /
`1562861114793132206`, según traslado del coordinador. No se atribuye una nueva
consulta directa a Discord en este trabajo.
