# JUP-060 — evidencia de consolidación de arquitectura

10/10/2026 · Base revisada `c2995a118d419dfe725247bac9c6f219a3f0ea77`.
[Tarjeta](https://trello.com/c/alMIpBOQ). Rama propia
`docs/JUP-060-technical-architecture`; copia aislada `tfm-economicon-jup060`.
Esta es evidencia de la aportación técnica asistida, no la review de Lucía ni
la validación independiente de Paris. No acredita pairing humano realizado.

## Criterios de la tarjeta

### Actualización de alcance AWS incorporada el 10/10

Por petición directa «Completa el punto 1» se añaden [esquema AWS](../architecture-aws.md)
y [Terraform](../../infra/aws-reference/README.md) a la rama de PR92. Se actualizan
arquitectura §6.3, antecedente EC2, OpenSpec y continuidad para mantener alcance
exclusivamente documental. Terraform es fuente de referencia sin ejecución,
no un despliegue; PostgreSQL/Cognito/Bedrock siguen siendo brechas hipotéticas.
Los fuentes se copiaron del paquete local tras verificar su manifiesto SHA-256;
guías y enlaces se adaptaron a rutas de repositorio. No se añaden ZIP, binarios,
provider cache, tfstate ni secretos. Los resultados históricos de abajo conservan
su base y fecha: no se atribuyen al nuevo contenido pruebas de runtime antiguas.

Comprobaciones nuevas desde esta rama: Terraform fmt/validate correctos, seis
tests con proveedores mock y ocho rutas Node correctos; OpenSpec estricto 56/56,
trazabilidad JUP-060 correcta y checker de higiene correcto (1003 archivos en
ese corte). Este último requirió repetición fuera del sandbox por spawnSync git
EPERM. El proveedor se reutilizó offline con lockfile; ver su
[informe de validación](../../infra/aws-reference/VALIDACION.md).

Tres diagramas nuevos o modificados (vista AWS de architecture.md y dos del
esquema completo) renderizados e inspeccionados visualmente sin recortes. Fuentes
y PNG de evidencia en `materiales/07-evidencias/JUP-060-arquitectura-2026-10-10/aws-reference-integration/`,
fuera del repositorio; Mermaid editable dentro. El documento general mantiene
ocho diagramas y el esquema AWS añade dos. Sin plan AWS real, apply, SQL,
memoria compartida, nuevas reviews humanas o cambio de estado de aceptación.
Comprobados 88 destinos de enlaces locales en 13 Markdown afectados, sin rutas
rotas; `git diff --check` correcto. Esta comprobación no consulta URLs externas
ni valida nuevamente todos los anchors históricos.

### Matriz de entrega

| Criterio | Entrega/evidencia | Estado y pendiente |
| --- | --- | --- |
| Resultado funcional verificable | [Arquitectura](../architecture.md): ocho diagramas de componentes, secuencias, datos, despliegue y objetivo; contraste de código integrado. | Entrega documental verificable; apartado d de memoria pendiente de incorporación revisada. No nueva ejecución del producto. |
| Pruebas necesarias añadidas y en verde | Comprobación de enlaces/diagrama/especificación y controles existentes, resultados abajo. | No se añaden tests de producto para prosa; ejecución documental se registra sin sustituir QA funcional. |
| Documentación y decisiones actualizadas | Arquitectura, [change](../../openspec/changes/jup-060-technical-architecture-deliverable/proposal.md), continuidad y propuesta AWS preservada. | Implementado; no ratifica ADR Proposed ni aprovisiona recursos. |
| PR revisado y vinculado | Contribución en rama propia, [PR #92 draft](https://github.com/EconomiconFinOps/tfm-economicon/pull/92). | Vinculado; revisión Lucía y validación Paris pendientes, sin merge. |
| Validación funcional y evidencia enlazadas | Esta matriz y fuentes históricas fechadas; handoff del apartado d. | Pendiente validación humana del entregable, exportación/hash de memoria y cierre de tarjeta. |

El residual de la descripción está cubierto técnicamente: componentes (§2),
secuencias (§3), datos (§4), auth/tenant/secretos (§5), despliegue (§6), decisiones
(§7), observabilidad/CI/CD (§8), dataset y límites (§1/2/3/6). El objetivo
tools/RAG/LLM se distingue de su implementación parcial. La integración cloud
no está probada ni se presenta como realizada.

## Fuentes y método

- Registro completo del dispatch oficial y contraste Trello 10/10 mediante
  `DockerServer:/home/danteadmin/economicon-collaboration`: descripción intacta,
  P0, Backlog, última actividad `2026-10-09T18:46:52.484Z` y nota cloud
  `6ac9369c206a85872b59ec4b`. No se usa otra vía Trello.
- Clone independiente desde repositorio local y fetch de origin/develop; sin
  editar rama/archivos del checkout compartido. Sin rama/PR específica JUP-060
  encontrada en la inspección inicial; PR85 referenciaba su apartado de memoria.
- Lectura de código/configuración y dos contrastes estáticos auxiliares. Los
  agentes no representan a los responsables humanos de revisión/validación.
- Correcciones contrastadas: billing persistido; auth/tenant y citas integrados;
  chat plantilla síncrona, ingesta documental/CLI Azure separadas; tools todavía
  contrato; gateway opcional; apps con binding amplio; versiones y persistencia.
- Propuesta AWS del 09/10 copiada sin cambios desde la aportación existente:
  SHA-256 `5f5ade08941dab08edb7cd7704dc1691db364ae1920918400a6a0603c9d71855`.
  Sus precios, sizing, PR abiertas y afirmaciones operativas conservan fecha,
  no se revalidan como actuales. No hay cuenta/credenciales/provisioning/gasto.

## Cobertura del guion oficial para el apartado d

Fuente: [Guion_PJ.md](https://drive.google.com/file/d/1echdTKuzMPiZAmxqEKlHkK8kaAsImdYX/view),
localizado en [coordinación Trello](https://trello.com/c/PGC5g5V9), leído por
Google Drive el 10/10; modificado 09/10 08:24:51Z. No se copia el guion a Git.
La memoria completa y los apartados ajenos no se han leído ni editado.

| Parte del guion | Requisito aplicable | Cobertura en referencia técnica / propuesta de apartado |
| --- | --- | --- |
| Entregables, 3.d | Diagramas, justificaciones tecnológicas y componentes | Arquitectura §2–7; propuesta d, párrafos 1–7 y figura de componentes. |
| Entregables, memoria | Máximo 20 páginas de la memoria completa | Propuesta breve para revisión; [Pendiente] comprobar extensión con su responsable, sin leer/exportar otros apartados. |
| Requisitos funcionales | Arquitectura documentada: componentes, flujos, dependencias y razones | §2–7; párrafos 1–7. |
| Requisitos técnicos | IA generativa y API fundacional | §3.2/3.4 y gateway; párrafos 4/5. [Pendiente] integración generativa de chat; no se acredita MVP final. |
| Requisitos técnicos | Base vectorial para almacenamiento/recuperación | §3.1/4, párrafos 2/3. |
| Requisitos técnicos | Producto MVP funcional | Estado por flujos y límites §1/3/6/8; párrafos 3–8. [Pendiente] aceptación integral. |
| Requisitos técnicos | Automatización DevOps/CI-CD | §6/8, párrafo 8; ampliar solo en f/JUP-111. CD final no acreditado en esta base. |
| Requisitos técnicos | Monitorización, logging y trazabilidad | §8, párrafo 8; logs request_id, métricas, límites de trazado. |
| Evaluación | Diseño técnico (20% dentro del desglose de entregables) | Componentes/diagramas/alternativas; párrafos 1–7. No se transforma en calificación conseguida. |
| Evaluación | Implementación y ejecución DevOps | Referencias/limitaciones; párrafos 3–8. Evidencia detallada en tarjetas de implementación y f/h, sin reescribirlas. |

Valor de negocio y contribución individual se asignan a b/JUP-062 y c/JUP-064;
este apartado solo delimita su relación, no modifica esos textos ni atribuciones.
La propuesta de d se guarda fuera del repositorio en
`materiales/07-evidencias/JUP-060-arquitectura-2026-10-10/propuesta-apartado-d.md`.
Es un borrador para Victor, no exportación ni segunda memoria canónica.

## Comprobaciones de esta entrega

Entorno: Windows, Node v24.14.1, pnpm 9.0.0, OpenSpec 1.8.0.
Instalación fijada: `corepack pnpm install --frozen-lockfile --ignore-scripts
--offline=false`, correcta, 547 paquetes. El primer intento offline no encontró
el tarball de OpenSpec; no se cambió lockfile ni versión para resolverlo.

| Comando/control | Resultado observado |
| --- | --- |
| `node tools/jup-check.mjs --all` | 9 changes correctos, incluido JUP-060. |
| `corepack pnpm openspec:validate` | 56 passed, 0 failed; estricto y no interactivo. |
| `node --test tools/jup-check.test.mjs tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/repository-governance.test.mjs` | 89 passed, 0 failed. |
| `node --test tools/jup-cleanup-check.test.mjs` | 6 passed, 0 failed. |
| `node tools/jup-cleanup-check.mjs` | OK, 982 archivos en el corte de la ejecución. |
| Enlaces relativos de los 11 Markdown afectados | 72 destinos/anchors comprobados; 0 errores. |
| `git diff --check` | Correcto. |
| Ocho bloques Mermaid | 8/8 renderizados con Mermaid CLI 11.4.2 y Chromium headless 1228; diagrama 1 repetido correctamente tras orientar TB. Inspección visual de 1, 2, 6 y 7, sin recortes de contenido. |
| Estado externo de PR73 | Lectura 10/10: OPEN, no draft, head a75472d9e83af56e4ecc4ae1f3acc50d5178e55e, sin merge. No verifica runtime. |

Los intentos iniciales de Node test runner y del checker de higiene dentro del
sandbox fallaron por `spawn EPERM`/`spawnSync git EPERM`, antes de validar contenido;
las repeticiones autorizadas fuera del sandbox son los resultados anteriores.
Un primer comando incluyó por error el nombre inexistente jup-cleanup.test.mjs;
la suite real se ejecutó después por separado (6/6), sin contar pruebas omitidas.

El intento de render durante la instalación incompleta falló por módulo ausente;
Edge después no arrancó. Se conservaron ambos recibos y se usó Chromium de pruebas
instalado, sin perfiles personales. El render final fue correcto. Fuentes Mermaid
quedan editables en Git; PNG y recibos locales en
`materiales/07-evidencias/JUP-060-arquitectura-2026-10-10/`: document-checks.json,
mermaid-results.json, diagram-1..8.mmd/png, propuesta de d y comandos de render.

CI del primer head e8f951e: [run PR](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035168806)
con siete checks técnicos correctos (policy, OpenSpec, tres Python, frontend build
y typecheck). [JUP reviews](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035168777)
falla exclusivamente por falta de Revision JUP-060 y Validacion JUP-060 de otra
persona; no se falsea ese gate. Las actualizaciones documentales posteriores tienen
su propio run en la PR; la evidencia anterior conserva su SHA.
No se han ejecutado Compose, migraciones, ingestas, Azure real, llamadas LLM,
provisioning AWS ni operación CD. No se reutiliza evidencia histórica como nueva.

## Handoff y aceptación pendiente

PR/evidencia enlazadas y releídas en Trello mediante integración oficial:
comentario `6ac9edb77c321c49fcc1f612`, 10/10/2026 07:48:07Z. Recibo local
trello-receipt.json. Tarjeta conserva lista, prioridad, roles y fechas.

Trello: Victor Mendez liderazgo, Alejandro Aguado pairing/coautoría, Lucia Mateo
revisión, Paris Arcos Martin validación. Identidad GitHub activa: Iber1to; esta
es su contribución asistida, sin reasignar liderazgo. El PR se mantiene draft.
Victor debe revisar la propuesta e incorporar el apartado d conforme a
[las reglas de memoria](../memoria/README.md), con autorización expresa para
lectura/escritura del apartado y revisión humana previa. No hay ese recibo aquí.
Después: exportación fechada/hash y dictámenes atribuibles; archivo/promoción del
change, integración y actualización de estado por el líder. Mantener change activo
es excepción explícita hasta aceptación; no se marca JUP-060 Hecho por este informe.
