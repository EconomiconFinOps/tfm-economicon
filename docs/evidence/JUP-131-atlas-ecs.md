# JUP-131 — Atlas y monitorización para ECS

Preparación autorizada 24/10/2026, sin despliegue AWS. Base Atlas
`ffb5d307772f697cffb8b1e73e6330250e093601` (PR159/160); continuación de PR146,
ya integrada. Los resultados siguientes son locales; no acreditan funcionamiento
en AWS, aprobación de cuota ni aceptación de modelos.

## Artefacto y datos

`apps/backend/app/aws_atlas_data/evaluations.sql` conserva exactamente el SQL
entregado, SHA256 `b61d9ffcc04e02d8a3df9847a7b4ffe21397d44afc5dd1d7384b7c30981a6f09`.
El manifiesto coteja aquí los 19 informes canónicos con sus hashes originales.
Bootstrap privado ejecuta fase `monitoring` después de esquemas y fixtures,
antes de servicios. No usa `evaluation-dashboard.py load` ni ejecuta modelos.

PostgreSQL16 real, contenedores desechables sin red exterior ni puertos publicados:
6 comprobaciones PASS: 19/1688 iniciales; repetición y adicional20/1689; conflicto
con rollback; huella alterada rechazada; lector SELECT sin DML/DDL/TEMP y rechazo
de rol privilegiado; metadatos separados persistentes tras repetir preparación.
Comando: `python -m unittest tools.aws_demo.test_atlas_postgresql -v`, con URL
de prueba opt-in. La prueba de manifiesto adicional pasa sin PostgreSQL.

## Runtime preparado

Grafana11.3.0 + Prometheus2.55.1, bases fijadas por digest, una tarea privada
0.5vCPU/1GiB. Evaluaciones y metadatos usan el RDS vectorial ya previsto:
`embeddings.evaluation` con lector y DB `grafana` con propietario propio.
Cuatro valores aleatorios separados en Secrets Manager; ninguno en Terraform.
TLS `verify-full` con CA regional fijada; sin acceso anónimo ni registro abierto.

CloudFront conserva `/grafana` y `/grafana/*`, sin caché ni reescritura `/api`;
ALB privado3000. Tres dashboards y UID `economicon-assistant-evidence` intactos.
Prometheus accede por loopback desde Grafana y descubre backend/processor con
Cloud Map; sin puerto público. Métricas limitadas a24h/256MB efímeros: se reinician
con la tarea; evaluaciones y metadatos se conservan en RDS durante el ciclo.
La landing y el vídeo permanecen en el flujo Pages, fuera de ECS.

`python tools/aws_demo/monitoring_smoke.py`: construye únicamente las imágenes
de monitorización y prueba PostgreSQL TLS con una CA sintética local. Comprueba
rechazo401 anónimo, tres dashboards, salud de ambos datasources, consulta de las
19 identidades/hashes/conteos y reinicio de Grafana. Añade login con cookie segura,
consulta real con Host de origen distinto del Origin público y rechazo403 de
otro dominio, sin alterar preferencias. Raíces de contenedor de sólo
lectura y discos temporales vacíos; todos los contenedores propios se retiran.
No prueba el DNS Cloud Map ni CloudFront real; esos controles quedan para el ensayo.

Terraform:13 pruebas mock PASS, incluida red privada, rutas, secretos referenciados,
dos contenedores y capacidad. Se mantienen dos réplicas de cada aplicación;
rolling150% =4.5vCPU; monitorización rolling200% =1vCPU: máximo agregado5.5vCPU.
La cuota efectiva exigida sigue siendo6; no basta el valor predeterminado AWS.

## Revisión de la preparación

Revisión asistida independiente de `ffb5d307..a7341d79`: dos hallazgos reproducidos
y corregidos. La cookie de navegador obtenía403 al consultar tras CloudFront;
Grafana11.3 espera el hostname en `csrf_trusted_origins`, por lo que se limita a
`frontend_domain`. Prueba aislada posterior PASS, incluido origen ajeno403 y
preferencia persistida tras reiniciar. La recuperación no retiraba definiciones
`backend-monitoring` huérfanas; ahora las reconoce con las mismas comprobaciones
de cuenta/ciclo/SHA/etiquetas. Rechaza componentes, fases y propietarios ajenos.
Regresión RED→GREEN y87 controles offline OK (7 opt-in, PostgreSQL probado aparte).

[PR161](https://github.com/EconomiconFinOps/tfm-economicon/pull/161) conserva los
resultados remotos por SHA y el estado de revisión. Los dictámenes humanos
`Revision JUP-131` y `Validacion JUP-131` siguen pendientes; la revisión asistida
no los sustituye. Sin merge ni despliegue.

## Coste y límites

Control rechaza presupuesto>30EUR, estimación>saldo verificado o saldo desconocido.
Se mantiene el nombre heredado `available_credit_eur`, pero significa fondos
restantes del proyecto: no existe crédito promocional acreditado.
Caducidad y aprobación siguen activas; este control no es un corte de facturación.
`python docs/planning/costes-aws/atlas.py` reproduce hipótesis y margen con el
catálogo22Oct: un ciclo2h23.40EUR; uno4h27.91EUR; tres1h32.65EUR; tres2h39.42EUR,
incluyendo IVA supuesto21% y margen20%. Gastos ya contabilizados, ventanas de
retirada y reservas deben reconciliarse antes de rellenar la configuración.

CI técnica, revisión independiente y evidencias del SHA definitivo se registran
en la PR de esta ampliación. La evidencia histórica PostgreSQL/Cognito/Bedrock y
demo se conserva con su fecha; no se renueva aceptación de toda la aplicación
por añadir estos tests. La receta mantiene su bloqueo de digest histórico hasta
una aceptación del candidato completo. Primer ensayo sigue pendiente de cuota,
saldo/ventana, bootstrap de control, fuente integrada y autorización de despliegue.
