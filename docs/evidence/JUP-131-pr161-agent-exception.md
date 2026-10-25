# JUP-131 — excepción de revisión y validación de PR161

Autorizada por el usuario el 24/10/2026 en «Preparar despliegue en AWS», chat
`01a15abb-d5f3-7fd3-a622-ea9e73b0db18`:

> Documenta una excepcion y lanza dos agentes para realizar la revision y la validacion

## Alcance y atribución

Excepción exclusiva de [PR161](https://github.com/EconomiconFinOps/tfm-economicon/pull/161),
`EconomiconFinOps/tfm-economicon`, JUP-131, rama `feat/JUP-131-atlas-ecs` hacia
`develop`, autor `Iber1to`. Sustituye, para este incremento, los dictámenes
humanos asignados a Lucía Mateo y Paris Arcos Martin por dos dictámenes de
agentes independientes. No acredita participación de esas personas.

Base de revisión: `ffb5d307772f697cffb8b1e73e6330250e093601`.
Candidato: `e730dc15fb3feb45a3b346fc9e48332c4608b049`.
Los cambios de documentación que registran esta excepción se identifican por
separado; cualquier cambio posterior de comportamiento requiere revalidar su delta.

- **Revision JUP-131:** agente dedicado a corrección, aislamiento, permisos,
  integridad de datos, rutas Grafana y ciclo de publicación/retirada. No modifica
  el código que revisa ni publica un dictamen atribuido a una persona.
- **Validacion JUP-131:** segundo agente dedicado a criterios observables,
  pruebas locales reproducibles y al menos un caso de error. Diferencia pruebas
  ejecutadas, evidencia anterior y comprobaciones que necesitan el ensayo AWS.

El coordinador documenta la autorización, entrega el mismo candidato a ambos,
contrasta los informes y atiende hallazgos. Los dos agentes no heredan el informe
del otro ni sustituyen un resultado negativo por una aprobación.

## Límites

La excepción autoriza los dos trabajos y su documentación; no autoriza despliegue
AWS, ejecución de modelos, cambios de permisos, acceso a secretos, ni un merge.
Las pruebas de PostgreSQL/Grafana usan exclusivamente recursos de prueba
desechables propios. Al no haber daemon local disponible, se permite el
DockerServer ya configurado, comprobado por SSH, con nombres únicos, aislamiento,
sin datos/montajes ajenos y retirada de los recursos propios por identidad.
No se modifican los servicios existentes ni se instala infraestructura compartida.

Los dictámenes se identifican como generados por agentes. No se fabrican reviews
de GitHub con identidades humanas ni se marca un check como superado sin evidencia.
Las reglas automatizadas actuales de GitHub se verifican por separado: documentar
esta excepción no equivale por sí mismo a una aprobación de plataforma.

También el 24/10 el usuario retiró el requisito operativo del presupuesto de
30 EUR para la cuenta del máster. No se consideran acreditados los supuestos
límites de Pontia. La adaptación, pendiente en aquel corte, quedó implementada
y revalidada en la reconciliación del 25/10 descrita a continuación.

## Resultados y revalidación

### Reconciliación autorizada el 25/10

El usuario exige conservar la solución aprobada de PR162 (`0edd11ef`). Se
retira el cambio mutable de `ApiError` descrito más abajo y su regresión
específica; se conserva Starlette 1.9.0. Los informes del 24/10 siguen siendo
evidencia histórica de sus propios candidatos, no aceptación de este delta.
También se adapta la guarda de presupuesto exclusivamente para `323188184300`.

La CI de política incorpora el reconocimiento específico de esta excepción:
dos informes atribuidos a `/root/pr161_code_review` y `/root/pr161_validation`,
con hashes y candidato común. Cualquier cambio de código posterior requiere
revalidación; sólo la publicación documental expresamente listada se permite.
No se sustituyen requests for changes ni se fabrican reviews humanas.

Ambos agentes entregan dictámenes independientes para el candidato
`812697387918c25e905a240fa35573091d9fdc16`: **APPROVE** de revisión y **PASS
offline** de validación. El hallazgo sobre etiquetas de roles duplicadas con
mayúsculas distintas se corrige y conserva como histórico, con evidencia
RED/GREEN. Se publican los cuatro archivos originales sin editar y un manifiesto
con sus hashes en [reconciliación PR161](JUP-131-pr161-reconciliation/README.md).
La aceptación offline del mismo árbol de aplicación se renueva con CI completa
y SQL efectivamente superadas. No acredita el funcionamiento desplegado en AWS.

### Histórico del 24/10

Ambos agentes trabajaron sobre el mismo candidato, con informes independientes.
La revisión inicial pidió corregir un P2: `/grafana/metrics` no estaba cubierta
por la denegación de métricas del ALB. Se añadió `/grafana/metrics*` a la regla
existente, manteniendo tres patrones, respuesta 404 y prioridad anterior al
reenvío de Grafana. Se conservan los dictámenes iniciales negativos y las
revalidaciones favorables del delta; no se aprueba retroactivamente e730.

El revisor comprobó ocho rutas denegadas y nueve preservadas. El validador
reprodujo RED con las reglas originales y GREEN con el delta: 14 pruebas mock,
formato y validación Terraform correctos. La ejecución del coordinador coincide.
El límite de tres comparaciones por condición se contrastó con la
[documentación ALB](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/rule-condition-types.html).

La validación independiente incluyó PostgreSQL real (carga aditiva, conflictos
sin sobrescritura y separación de permisos), Grafana con TLS, cookies y CSRF,
19 identidades/1688 resultados, tres dashboards y persistencia tras reinicio.
Se verificó la retirada por identidad de 10 contenedores, tres tags propios y
tres volúmenes anónimos en DockerServer. No hubo ejecución en AWS.

Una ejecución posterior de CI sobre e730, [40133534310](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/40133534310),
detectó 41 fallos de Azure Cost API: `ApiError` era una dataclass congelada y
rechazaba la escritura del traceback que realiza Starlette. Se reprodujo con
`contextlib`, se retiró sólo `frozen=True` y se añadió regresión. El coordinador
obtuvo 82 PASS con FastAPI 0.162.0 y Starlette 1.10.0. El revisor aprobó este
delta; el validador reprodujo siete fallos con la excepción original y obtuvo
82 PASS al aplicar únicamente la corrección. Las comprobaciones son separadas
de las del ALB y no alteran los informes anteriores.

Informes completos y evidencia publicable:
[revisión](JUP-131-pr161-agents/review/README.md) y
[validación](JUP-131-pr161-agents/validation/README.md).

Los informes identifican bytes exactos mediante SHA256. La aceptación histórica
de aplicación no se actualiza: las pruebas de Atlas y los deltas no sustituyen
la aceptación completa del ensayo. `JUP reviews` sigue verificando reviews de
cuentas GitHub; no se ha modificado el check ni fabricado una aprobación humana.
El estado remoto debe consultarse para el commit final, sin confundir la CI
técnica con ese requisito de plataforma.
