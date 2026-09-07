# JUP-062 - Auditoria del borrador de memoria de negocio

- Trello: https://trello.com/c/5sBSKurr
- Pull request: https://github.com/EconomiconFinOps/tfm-economicon/pull/20
- Fuente editable: `Memoria_Economicon` en Google Docs, enlazada en Trello
- Fecha de corte: 2026-08-28
- Rol que prepara la evidencia: validacion, pruebas y documentacion
- Estado: baseline reproducible; contenido pendiente de coautoria y revision

## Evidencia reproducible

La fuente editable sigue siendo Google Docs. Para este corte se guardaron dos
copias inmutables fuera de Git, junto al resto de entregables finales:

- `materiales/06-entregables/Memoria_Economicon-borrador-2026-08-28.pdf`
- `materiales/06-entregables/Memoria_Economicon-borrador-2026-08-28.md`

La exportacion PDF tiene 6 paginas. Cumple el maximo oficial de 20 paginas y
deja margen para completar las secciones tecnicas, de evaluacion y cierre.

| Archivo | SHA-256 |
|---|---|
| Markdown | `3E0C6EB207CD8AE98434FFE7F2F81B3D44EA0A8A863676B15AB52CFA38D000EF` |
| PDF | `6545B9E11F2873649C3FD55F7771ABF9D6AA49024959761FFE54A1381BA7E4C4` |

## Revalidacion de Alejandro - 2026-08-28 20:11 CEST

Alejandro Aguado reexporto la fuente canonica enlazada en Trello en Markdown y
PDF y la comparo con el snapshot anterior. Ambos archivos son identicos byte a
byte y conservan los hashes registrados arriba. El PDF mantiene 6 paginas A4,
213052 bytes y un render legible, sin texto cortado, solapamientos ni elementos
fuera de pagina.

Esta comprobacion acredita la reexportacion y la validacion tecnica del snapshot
actual, pero no una validacion final del contenido: el documento sigue sin
incorporar viabilidad, impacto medible, costes y riesgos, y conserva apartados
posteriores como pendientes de redaccion. Por tanto, las tareas 2.1-2.6 y las
confirmaciones 3.1-3.4 permanecen abiertas, y JUP-062 debe continuar en
`30 - En curso` hasta que exista una version revisable nueva.

## Contraste con el guion oficial

El guion oficial dedica el 10% de la evaluacion de entregables a la descripcion
del caso de negocio. Exige una oportunidad identificada, analisis de mercado,
justificacion de la solucion y una explicacion clara de impacto, viabilidad y
diferenciacion. La memoria completa no puede superar 20 paginas.

## Cobertura del borrador

| Criterio | Estado | Evidencia o brecha |
|---|---|---|
| Oportunidad/problema | Parcial | Problema claro, pero falta acotar la evidencia al segmento elegido. |
| Usuarios objetivo | Parcial | Enumera startups, independientes y equipos pequenos; falta validacion o declararlo hipotesis. |
| Analisis de mercado | Parcial | Gartner esta correctamente identificado; las cifras de Flexera y otras afirmaciones deben precisarse. |
| Propuesta de valor | Cubierto | Traduce datos de coste a indicadores, alertas y respuestas con fuentes. |
| Diferenciacion | Parcial | El agente conversacional es claro; falta comparar alternativas concretas o limitar la afirmacion. |
| Viabilidad | Ausente | Falta separar viabilidad tecnica, operativa y economica. |
| Impacto | Ausente | Falta definir resultados esperados y como se mediran. |
| Costes | Ausente | Falta registrar categorias, supuestos, fecha y fuente de cada estimacion. |
| Riesgos | Ausente | Falta matriz priorizada con mitigacion y responsable. |
| Coherencia con el MVP | Parcial | El alcance Azure simulado esta acotado; no todas las capacidades resumidas tienen todavia evidencia final. |
| Limite de paginas | Cubierto ahora | 6/20 paginas en el corte del 2026-08-28. |

## Correcciones de fuentes

Las dos fuentes existentes son pertinentes, con estos ajustes:

1. Gartner proyecto un gasto mundial de `723.400 millones USD` en servicios de
   nube publica para 2025, frente a `595.700 millones USD` en 2024. La fuente es
   la nota de prensa de Gartner del 19 de noviembre de 2024.
2. Flexera 2025 encuesto a 759 profesionales y responsables cloud. El `84%`
   situo la gestion del gasto cloud entre los principales retos y estimo un
   `27%` de gasto IaaS/PaaS desperdiciado. Es evidencia de un problema general,
   no prueba por si sola que el segmento de pequenas organizaciones este
   desatendido.

Fuentes primarias:

- Gartner, 2024: https://www.gartner.com/en/newsroom/press-releases/2024-11-19-gartner-forecasts-worldwide-public-cloud-end-user-spending-to-total-723-billion-dollars-in-2025
- Flexera, 2025: https://info.flexera.com/CM-REPORT-State-of-the-Cloud-AWS

## Texto propuesto para completar la memoria

Este texto es una propuesta de revision; no sustituye la fuente editable ni
afirma resultados que todavia no existen.

### Hipotesis de segmento y alternativa actual

Economicon parte de la hipotesis de que startups, profesionales independientes
y equipos pequenos necesitan interpretar su gasto Azure sin mantener una
funcion FinOps dedicada. Las cifras de Gartner y Flexera demuestran que el gasto
y su gestion son un problema relevante, pero no validan por si solas este
segmento. Durante el MVP se contrastara la hipotesis mediante tareas guiadas y
feedback de usuarios; hasta entonces, la alternativa de referencia es combinar
las vistas nativas de Azure Cost Management con analisis manual y documentacion
FinOps.

### Viabilidad

La viabilidad tecnica se apoya en un alcance deliberadamente acotado: un unico
proveedor cloud, un dataset publico y una API de Azure Cost Management simulada.
Esto permite demostrar de forma reproducible el circuito de ingesta, analitica
y asistencia sin solicitar credenciales ni datos reales de clientes. La
arquitectura versionada y los contenedores reducen el coste de reproduccion; el
RAG, la evaluacion y la observabilidad deben completarse antes de afirmar que el
MVP esta listo.

La viabilidad operativa depende del roadmap del equipo de cuatro personas, del
limite de dos implementaciones y una linea documental en curso, del freeze de
codigo del 9 de octubre y del freeze de memoria del 16 de octubre. La viabilidad
economica del prototipo se medira con costes reales de inferencia, hosting y
dominio. Hasta elegir modelos y alojamiento de produccion no se publicara una
cifra total como si fuera un presupuesto cerrado.

### Impacto esperado y medicion

El impacto esperado es reducir el esfuerzo necesario para responder preguntas
sobre coste y convertirlas en acciones comprensibles. La evaluacion comparara
exactitud de calculos, cobertura de preguntas, citas correctas, tiempo para
completar tareas y claridad/accionabilidad percibida. Estos son objetivos de
medicion; los resultados se incorporaran unicamente cuando JUP-067 a JUP-071
produzcan evidencia reproducible.

### Costes y riesgos

El coste del prototipo se registrara por categoria: inferencia del modelo,
embeddings, hosting, almacenamiento, observabilidad y dominio. Cada importe
indicara proveedor, unidad, supuesto de uso, moneda y fecha. El software local
y los componentes open source no eliminan el coste de operacion, por lo que no
se presentaran como coste cero.

| Riesgo | Mitigacion | Evidencia/owner pendiente |
|---|---|---|
| El dataset publico no representa un tenant real | Limitar conclusiones al MVP simulado y documentar la validez externa. | JUP-072/JUP-077 |
| El modelo genera explicaciones no soportadas | Calculo determinista, RAG con fuentes y evaluacion de fidelidad. | JUP-067 a JUP-071 |
| El RAG o la observabilidad no llegan al freeze | Proteger P0 y retirar alcance P1/P2 antes de mover las fechas. | JUP-080 |
| El coste por consulta supera el presupuesto | Medir tokens/coste, limitar modelos y fijar alertas. | Propietario por asignar |
| La memoria supera 20 paginas | Presupuesto de cuatro paginas para introduccion/caso de negocio y control semanal. | JUP-062 |
| Falta evidencia individual | Enlazar commits, PR, revisiones y validaciones por miembro. | JUP-064 |

## Puerta de salida

JUP-062 puede volver a `40 - En revision` cuando el Google Doc incorpore el
contenido acordado, exista una nueva exportacion con hashes y el bloque conserve
el presupuesto de paginas. No debe cerrarse hasta registrar la contribucion de
Lucia, Paris, Victor y Alejandro conforme a los roles de la tarjeta.

La PR usa la plantilla de gobernanza JUP e identifica de forma explicita la
tarjeta, Trello y las cuatro responsabilidades rotatorias para que la politica
remota pueda comprobar la trazabilidad sin atribuir revisiones ya realizadas.
