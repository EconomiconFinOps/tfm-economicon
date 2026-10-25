# Continuidad del proyecto

25Oct, PR165: segundo intento detenido antes de aplicar Terraform por `cycle`
reservado en DynamoDB; alias corregidos y prueba real conforme. Añadidos permisos
dependientes de Cloud Map sólo por llamadas delegadas, creando zonas privadas
en Irlanda, y permisos acotados de cifrado/lectura S3 y consulta de perfiles IAM.
Plan0altas/1política/0bajas sin aplicar. Sin aplicación, bloqueo ni Scheduler
activos; bootstrap conservado.
Revisión/CI del delta e integración pendientes. Detalle en [cloud-aws.md](cloud-aws.md).

Los siguientes párrafos son cortes históricos, superados por el estado anterior.

25Oct 13:44 Europe/Paris: PR163 integrada como `6851ec7a` tras autorización
humana expresa de excepción y bypass para `f48a72e8`. CI técnica PR/push y SQL
SUCCESS, build Docker real y revisión independiente favorables; árbol integrado
idéntico al revisado. CI develop `40194488245` SUCCESS; reintento `2855d9da`
iniciado13:52:38, ventana hasta15:52:34 local. Validación y cinco imágenes SUCCESS;
plan de162 altas/0cambios/0bajas revisado y aprobado14:01, Scheduler verificado.
Apply en curso; aplicación todavía pendiente. El primer intento falló antes del plan. Véase
[cloud-aws.md](cloud-aws.md).

25Oct, primer ensayo autorizado en la cuenta del máster `323188184300`:
SSO renovada y verificada; PR161 integrada mediante el bypass puntual autorizado
como `2087855c`, sin cambiar reglas. CI push develop `40191355921` SUCCESS.
Bootstrap aplicado y estado S3 separado, cifrado/versionado, sin drift. Ensayo
`0c9fb3aa` valida correctamente y se detiene en build por el contexto Docker de
Azure; sin infraestructura de aplicación creada. Corrección de una línea con
regresión y build real conformes. PR163 publicada; revisión técnica favorable,
CI e integración nueva pendientes.
Estado y recibos en [cloud-aws.md](cloud-aws.md).

Los párrafos siguientes conservan su corte histórico.

25Oct: PR161 reconciliada con la aplicación aprobada `0edd11ef`; ApiError
intacto y Starlette 1.9.0, Atlas/Grafana/carga aditiva conservados. CI técnica
completa y SQL del árbol integrado SUCCESS; aceptación offline/digest renovados.
Excepción de agentes reconocida sólo en PR161 con informes ligados al candidato;
guardas generales conservadas. Configuración del máster regenerada sin saldo
ficticio; CI develop y ventana pendientes. Sin merge ni despliegue. Estado final
y recibos en [cloud-aws.md](cloud-aws.md).

25Oct: versión de aplicación aprobada por el usuario `0edd11ef`, PR162
integrada en `develop`. CI push `40137719699` SUCCESS; Azure instala
Starlette 1.9.0 y supera 81 pruebas, con `ApiError` idéntico a la base.
SQL de la PR también SUCCESS. Atlas/ECS sigue en PR161, abierta y con un
conflicto documental; su cambio anterior de `ApiError` debe retirarse al
reconciliarla con la versión aprobada. Configuración del ensayo aún obsoleta,
sin despliegue. Ver [cloud-aws.md](cloud-aws.md).

25Oct: por decisión expresa del usuario, el despliegue se prepara únicamente
en Economicon del máster, cuenta `323188184300`. Eliminada la automatización
de seguimiento de la cuenta original `605600557607`; ya no se requiere su
inicio de sesión ni esperar su cuota. El estado anterior queda como histórico.
Sin despliegue iniciado. Ver [cloud-aws.md](cloud-aws.md).

24Oct, actualización posterior: el usuario autoriza una excepción para PR161:
revisión y validación por dos agentes independientes, ya lanzados sobre e730dc15.
Documentada en PR, Trello y [evidencia](../evidence/JUP-131-pr161-agent-exception.md).
Retira el presupuesto30EUR como condición del ensayo en la cuenta del máster;
los límites de Pontia no están acreditados y la configuración anterior se deberá
adaptar. DNS redirigido por indicación humana a Jarvis **local**, retirado de Mother;
el chat local guardó los cuatro NS y verificó ambos autoritativos y dos
resolutores, conservando los otros 22 registros. DNS independiente a las
23:26 Europe/Paris confirma la delegación nueva. Revisión y validación favorables
para las correcciones de métricas y ApiError: Terraform 14 PASS, Azure 82 PASS,
PostgreSQL/Grafana reales y recursos propios retirados. Informes en
[evidencia PR161](../evidence/JUP-131-pr161-agents/README.md). Commit publicado
`30d4370a`: CI PR, CI push y SQL SUCCESS a las 23:47 Europe/Paris. `JUP reviews`
sigue FAILURE al exigir reviews de cuentas GitHub; la excepción tiene los
informes, pero ese mecanismo no se ha cambiado. Sin merge ni despliegue.
Ver [cloud-aws.md](cloud-aws.md).

Hito anterior24Oct23:03París: cuenta del máster Economicon323188184300 preparada parcialmente:
Fargate6/CodeBuild30, conexión GitHubAVAILABLE, boundary validada y cuatro roles
sin políticas, zona Route53 y secretos de control creados. Plan bootstrap
4importaciones/23altas/4cambios/0bajas, sin aplicar. DNS pedido a Jarvis con
autorización humana; DNS público aún antiguo. Secreto GitHub guardado por el
usuario y AWSCURRENT confirmado sólo por metadatos; contenido/autenticación no
probados. CorreoBudgets pendiente. Budget30USD creado,
sin apagado; techo humano30EUR y saldo restante por conciliar. PR161 técnica verde,
dictámenes/aceptación/integración pendientes. Paquete de ensayo bloqueado;
sin aplicación, builds ni pipelines. Monitor original separado. Ver [cloud-aws.md](cloud-aws.md).

24Oct: integración Atlas preparada en PR161: carga aditiva privada, Grafana y
Prometheus en ECS, tres dashboards y19/1688 conservados. PostgreSQL real,
Grafana con cookies/TLS/reinicio y Terraform13 PASS. Revisión asistida detectó
dos fallos corregidos y revalidó el delta0f1522e6. CI técnica y SQL finales de
e730dc15 SUCCESS; JUP reviews en rojo por los dos dictámenes humanos ausentes.
Techo30EUR; tres ciclos de2h exceden el presupuesto. Sin despliegue. Ver [cloud-aws.md](cloud-aws.md).

24Oct: sesiónAWS recuperada; Fargate Irlanda aplicada0 y sin nueva respuestaAWS.
Presupuesto creado30USD acumulados01Oct–01Dic, avisos50/80/100%; correo pendiente
de verificar, sin apagado automático. Techo local del ensayo30EUR. Ver [cloud-aws.md](cloud-aws.md).

Coste AWS actualizado el 22/10/2026: [costes-aws.md](costes-aws.md), cálculo
mensual reproducible, escenarios temporales y borrador para el caso de negocio.
Estado: estimación enviada a HAL para Lucía por autorización humana; no factura,
despliegue ni benchmark.
Acceso de evaluador22/10: fecha aclarada30Nov2026; usuario exclusivo de consola
creado, lectura/MFA y caducidad de permisos configuradas. Credenciales privadas
para entregar por el operador; primer login/MFA aún pendiente. Ver cloud-aws.
Fargate23/10 08:36París: tras login humano, consola confirma aplicada0vCPU y
solicitud6 en Caso abierto; el defaultAWS6 no es cuota asignada. Sin despliegue.
Evidencia y caso en [cloud-aws.md](cloud-aws.md).
Seguimiento23Oct12:24París enviado por web al caso179267775500075 con autorización
humana, publicación verificada. Prioridad por defensa29Oct solicitada; pendiente
respuesta/aprobación, sin upgrade, duplicados ni despliegue. Detalle en cloud-aws.
Monitor23Oct activo cada hora en este chat para respuestaAWS/cuotaFargate;
avisos sólo con cambios o intervención necesaria, sin despliegue. Requiere
equipo/app activos y sesiónAWSválida. Identificador y baseline en cloud-aws.
Antecedente Monitor24Oct13:10París (resuelto tras login): sesiónAWS caducada, primer aviso de login necesario;
cuota y respuesta actuales desconocidas. Último efectivo0 del23Oct, sin despliegue.

Resúmenes técnicos para retomar el trabajo. Trello conserva alcance, responsables
y estado operativo; GitHub conserva código y revisiones; OpenSpec conserva
requisitos y diseño. Este índice enlaza evidencia, no sustituye esas fuentes.
Leer la [convención](convencion-compartida.md) y sólo los temas pertinentes.
Las fechas indican la última actualización documental, no una nueva ejecución de pruebas.
Los párrafos de B siguientes conservan su corte histórico del 17/10. En la
reconciliación del 18/10, el PM confirma que el develop fijado `0e686f91` ya
incorpora PR140; esa incorporación no acredita esta composición de JUP-125.

B: PR140 publicada en 09b3c8bb, CI/SQL propias conformes. Reconciliación
contra 466b083a en fix/JUP-123-local-reconcile: dos conflictos resueltos,
67 backend y 92 processor PASS; publicación autorizada para desbloquear la revisión.
Checks y nuevos dictámenes del SHA integrado pendientes; sin merge remoto.
Ver [reconciliación local](pr140-reconciliacion-integracion.md).
El colector #131 está integrado; el seguimiento documental #138 es independiente.

| Tema | Resumen y estado documental | Actualizado |
| --- | --- | --- |
| [Compatibilidad Azure Cost API](azure-cost-api-compatibilidad.md) | JUP-140/PR162: contención temporal Starlette 1.9.0; ApiError congelado, resolución limpia y 81 PASS, imagen y HTTP normal/demo comprobados localmente. Otros rangos y servicios conservados. | 2026-10-24 |
| [Landing pública](landing-publica.md) | JUP-140/PR162:14marcadores sustituidos por viñetas violetas, textos/datos/JS conservados y Azure excluido. Landing36PASS(26+10), capturas nativas claro/oscuro/móvil/amplia; evaluaciones independientes y aprobación visual pendientes. | 2026-10-24 |
| [Despliegue AWS](cloud-aws.md) | PR161/163 integradas; bootstrap aplicado en el máster. Segundo intento detenido por DynamoDB antes de aplicar infraestructura; controles retirados y aplicación ausente. PR165 corrige el bloqueo y permisos dependientes de Cloud Map/S3/IAM; revisión/CI del delta e integración pendientes. | 2026-10-25 |
| [Cortes de respuesta del chat](cortes-respuesta-chat.md) | JUP-135 integrada por squash f224226d en PR153, con excepcion humana de merge; CI tecnica previa conforme. Agregados de medicion comunicados y pendientes documentales conservados; sin aceptacion generativa nueva. | 2026-10-22 |
| [Reevaluación de métricas del modelo](reevaluacion-metricas-modelo.md) | JUP-133: PR156 incorporó seis repeticiones y juez IA provisional; PR158 integrada en develop93624f77 corrige fixtures y altura. Evidencia ajena Linux1998PASS/0omisiones y OpenSpec92PASS, sin aceptación de campañas. La composición139 comprueba su delta por separado. | 2026-10-23 |
| [Composición narrativa de evaluación](dashboard-evaluacion-composicion.md) | JUP-139: entrega R8 aprobada por Paris el 24/10; revisión y validación locales favorables, 137 medidas y 19/1688 conservados. Develop idéntico a 93624f77. OpenSpec archivado 24/10 con promoción de requisitos; evaluación del delta documental y publicación pendientes. Tres dashboards intactos, publicación y etapas humanas pendientes. | 2026-10-24 |
| [Modelo único del chat](modelo-unico-chat.md) | JUP-132: Flash/DeepInfra FP8 normal y recursos v4; OpenSpec archivado. CI posterior detecta 11 fallos de fixtures, reproducidos y corregidos localmente con 19/19 controles; reevaluación del delta y nueva CI pendientes. Sin inferencias ni despliegue. | 2026-10-21 |
| [Indicadores medibles para la memoria](indicadores-memoria.md) | JUP-130: precisión, recall y retraso del detector de anomalías (5/7 eventos, 5/5 los detectables por diseño), coste de IA facturado frente a estimado (OpenRouter confirma 100/100 consultas) y reconciliación y frescura de los datos, con tres paneles en el dashboard de evaluación. Medido con datos sintéticos y el gateway local; sin publicar, revisión adversarial y aprobaciones pendientes. | 2026-10-21 |
| [Acciones y citas del panel](../demo/JUP-065/correccion-panel.md) | JUP-065: corrección separada de acciones ocultas, narrativa incompleta y visor de fuentes; pruebas y límites documentados, reviews y aceptación integrada pendientes. | 2026-10-19 |
| [Demo funcional](demo-funcional.md) | JUP-065: integración de final10000 autorizada por excepción humana23Oct; demo congelada con incidencias, RC NO ACEPTADA, accesos y10USD conservados. Evidencia histórica separada de CI. | 2026-10-23 |
| [Índices de embeddings](indices-embeddings.md) | PR139: dos bloqueantes57fe7c57 corregidos sólo local por excepción humana; política30PASS y9SQL realesPASS tras baseline6FAIL/3PASS; candidato local, sin publicación ni dictamen nuevo. | 2026-10-18 |
| [Politica de revisiones](revisiones-pr.md) | PR135: reconciliación de5f9dac36 con develop79aa76be tras PR134; excepción y entradas119 intactas, índice unido sin perder chunking. CI/SQL del nuevo candidato y revalidación incremental pendientes; aprobación previa conserva5f9. | 2026-10-18 |
| [Chunking documental](chunking-documental.md) | JUP-125 / PR #134: reconciliación publicada en f8dd03bc. CI processor detecta siete fallos por huella de política obsoleta; fix mínimo de manifiesto y pin backend preparado, con reproducción y pruebas focales favorables. Controles nuevos y evaluación independiente del fix pendientes; requisitos humanos conservados. | 2026-10-18 |
| [Ingesta documental](ingesta-documental.md) | JUP-124 / PR #133 integrada en develop 466b083a; extracción Markdown y OCR con límites/documentación propios. La reconciliación local de B preserva esa implementación sin trasladar sus dictámenes a B. | 2026-10-17 |
| [Colector reutilizable del chat](colector-chat.md) | PR131 integrada; PR138 reconciliada con develop7f38282c, limitada a tres documentos. Ejemplo/contrato run-info comprobados sin IA; CI y revisión final pendientes. JUP-123 conserva su estado cerrado y los roles originales. | 2026-10-18 |
| [Dashboard de evaluación del asistente](dashboard-evaluacion-asistente.md) | JUP-121 conserva las medidas A/B/C y su contrato PostgreSQL. PR141 añade comparativa provisional GLM/DeepSeek en panel25 separado y SQL acotado; 16 controles PG reales y limpieza acreditados sobre las seis fuentes originales. Reconciliación documental con developf444; CI y dictámenes incrementales pendientes. Grafana live no cargado ni verificado por este incremento. | 2026-10-19 |
| [Consultas de coste Azure](../evidence/JUP-036-validation.md) | PR69: reconciliación local de `1cf4087f` con develop `a3f514f7` (#129), sin cambios de producto. Corpus1.1.1 conservado; los dos casos SQL pendientes pasan en Cockroach24.1.11. Revisión/validación independientes del nuevo candidato y CI posterior pendientes. | 2026-10-15 |
| [Memoria: modelos](memoria-modelos.md) | Comparativa histórica GLM82/84 yDeepSeek77/84 con336fases trazadas, ADR0025 documental y alias0023. Revisión y validación independientes por agentes autorizadas; contenido3274 comprobado, reconciliación condevelopf444 yCI/delta pendientes. PG16PASS por identidad; Grafanalive pendiente. | 2026-10-19 |
| [Memoria: solución de IA](memoria-ia.md) | JUP-063: aporte e/g preparado para PR141 por excepción expresa del 19/10; dictámenes propios no se extienden a toda la composición. PDF nativo actual de 18 páginas y Grafana visual comprobados por PM. c/h pendientes, i parcial, d por armonizar; pairing y registros humanos no acreditados. Archivo autorizado ejecutado, sin cierre de tarjeta. | 2026-10-19 |
| [Evaluación local del chat](chat-evaluacion-local.md) | PR140: cinco correcciones publicadas en 09b3c8bb, con CI/SQL propias conformes. Archivo035/123 autorizado; aceptación y nuevos dictámenes pendientes. N5 histórica intacta. | 2026-10-17 |
| [Reconciliación de PR140](pr140-reconciliacion-integracion.md) | 09b3c8bb + develop466b083a (PR133), dos conflictos resueltos y 159 pruebas focales PASS; publicación autorizada para revisión de Víctor, CI/SQL y nuevos dictámenes pendientes. PR138 independiente. | 2026-10-17 |
| [Chat conversacional](chat-conversacional.md) | PR121: focal28 3PASS/4FAIL, JSONB7PASS. Corrección29 de soporte literal visible e interpretación separada en regresión offline; aceptación/batería real pendientes. Gasto0.957927619/2USD. | 2026-10-13 |
| [División del chat en A/B](chat-entregas-a-b.md) | División aprobada; B d9b/9e2 corregida,50/84 muestras con47PASS/3técnicas429, sin publicar ni aceptar. Ver evaluación local. Base A8ea/develop0543 y reviews/CI conservan su fecha histórica, sin nueva consulta. | 2026-10-15 |
| [Pantallas de maqueta ocultas del MVP](pantallas-ocultas-mvp.md) | JUP-116: Coste Detallado, Corte Global y Recomendaciones ya no tienen ruta ni menú (se conservan en el código y se reactivan con dos líneas) y Overview sale del menú pero conserva su ruta; una dirección desconocida lleva a `/`. 797 pruebas del frontend y 16 comprobaciones en navegador; mergeado en `develop` el 2026-10-12 (#124). | 2026-10-13 |
| [Interfaz del frontend en español](frontend-espanol.md) | JUP-117: textos de la interfaz en español con glosario y prueba de regresión; recorrido visual de las nueve pantallas en claro, oscuro y móvil. Los errores de la capa de API y los valores de la API se dejan fuera, salvo las limitaciones de los episodios de anomalía, que JUP-134 pasa a español en origen. Mergeado en `develop` el 2026-10-12 (#123) por la excepción temporal. | 2026-10-22 |
| [Datos de demo por una ruta y fecha de referencia](fecha-referencia-datos-demo.md) | JUP-119 conserva su diseño e historial. JUP-133: instantánea de los 1.370 registros etiquetados de DockerDevelop, cotejada con la fuente; publicación en PR156, sin recargar entornos ni crear importador. | 2026-10-23 |
| [Demo con datos sintéticos de coste](demo-datos-sinteticos-coste.md) | JUP-107: demo de tres minutos con los datos de JUP-106 y conjunto sintético de anomalías con herramienta, esperados y guía (30 pruebas de la parte nueva, 6 con CockroachDB real). Dos changes aprobados y archivados; desde JUP-114 el conjunto de anomalías es diario y la demo de 3 minutos incluye el panel `/anomalies` (D12); sin ensayo humano. | 2026-10-12 |
| [Reintentos de la cola de ingesta](reintentos-ingesta.md) | JUP-113: un trabajo mal formado ya no retiene la cola. La API rechaza con 422 un `source` que el processor no acepta, el rechazo del guardrail de entrada se descarta en una entrega y el fallo no clasificado se reintenta una vez; si no se puede leer o registrar el estado se reencola sin tope. `RF-086-004` y `RF-054-001` quedan `Fixed` técnico; 15 pruebas con servicios reales (11 fallan sobre la base) y recorrido con Compose. Coste asumido: ~10 s de caída de pgvector descartan jobs que hay que reenviar. OpenSpec archivado; ADR-0019 en `Proposed`. PR #118: la validación pidió cambios en el criterio 4 (cadena JSONB con aspecto de objeto), corregidos en la rama y pendientes de revalidar; `Revision JUP-113` pendiente. | 2026-10-11 |
| [Identidad de marca del frontend](identidad-marca-frontend.md) | JUP-112: marca de Economicon en tema claro y oscuro con estados y gráficas validados; implementación local sobre `develop`, 787 tests del frontend, capturas en 1280 y 390 px. PR #112 abierto y con cambios pedidos por la revisión, ya atendidos; falta confirmar en Trello la ampliación al tema oscuro. JUP-134: el conmutador de tema muestra el tema activo («Tema claro» o «Tema oscuro»). | 2026-10-22 |
| [Hitos de entrega y cierre del MVP](hitos-entrega.md) | JUP-080: fechas23/10 y29/10 confirmadas por usuario;11 vencimientos activados y verificados. Archivo OpenSpec y cierre por PR en curso. | 2026-10-11 |
| [Memoria: integración DevOps](memoria-devops.md) | JUP-111 / PR87: f incorporado y preservación verificada; PDF13p, Markdown y hashes fuera de Git; revisión delegada por excepción de plazo, integración en curso. | 2026-10-11 |
| [Arquitectura técnica](arquitectura-tecnica.md) | JUP-138: `architecture.md` al día con develop 03e97ce6 (MinIO, subida de archivos, chat generativo bajo flag, landing, AWS sin despliegue); antes JUP-060 / PR92 con a0e9a56. Estado de integración en PR/Trello. | 2026-10-22 |
| [Arquitectura documental AWS](cloud-aws.md) | Referencia Fargate y Terraform sin ejecución; antecedente EC2 operativo superado. 6 pruebas mock/8 rutas correctos, sin despliegue. | 2026-10-10 |
| [Proveedor y modelos](proveedor-modelos.md) | JUP-078 / PR113: gateway dedicado, claves9+1 USD/30d y26 controles Docker verificados; OpenSpec archivado, revision asistida aprobada, sin gasto real. | 2026-10-10 |
| [Métricas funcionales de negocio](../evidence/JUP-068-validation.md) | JUP-068 / PR68: cierre técnico por excepción MVP con subagente;113 pruebas y59 OpenSpec pasan. Piloto/beneficio real sin medir. | 2026-10-10 |
| [Cobertura de etiquetado](../evidence/JUP-017-validation.md) | JUP-017 / PR66: excepción MVP autorizada; conflicto y refresco corregidos, revisión asistida y pruebas en curso. Evidencia versionada en docs/evidence/JUP-017-validation.md. | 2026-10-10 |
| [Consulta de ownership](consulta-ownership.md) | JUP-037 / PR100: cierre preparado bajo excepción de plazo MVP; atribución real documentada, 209 backend/35 frontend y navegador HTTP/SQL pasan. Corrección de nuevo hilo; CI final/integración por verificar al publicar. | 2026-10-10 |
| [Pruebas unitarias e integradas](pruebas-unitarias-integradas.md) | JUP-054: PR93 integrada por excepción de plazo del MVP (7 tests nuevos, CI Linux 2041 pass/91 skips). Segunda pasada en rama, con flujo ordinario: cobertura del candidato `e1c2a8f` y 291 pruebas nuevas, sin cambios de producto; 5 defectos registrados sin corregir (`RF-054-001` a `005`); PR #114 abierta con CI en verde, revisión y validación pendientes. | 2026-10-10 |
| [Dimension vectorial desde Settings](dimension-vectorial-settings.md) | JUP-102 / PR #108: pruebas y CI tecnica verificadas; excepcion de entrega fuera de plazo autorizada, atribucion real bajo Alejandro y cierre por PR. Reviews humanas dispensadas, no simuladas. | 2026-10-10 |
| [Pipeline Turbo y pnpm](pipeline-turbo-pnpm.md) | JUP-105 / PR #86: residual publicado en 12841e6 desde copia propia; comentario y evidencia reconciliados. CI por SHA enlazada en PR; dictámenes Lucía/Paris y merge pendientes. | 2026-10-10 |
| [Entorno pnpm de Alejandro](pnpm-entorno-rf093001.md) | Diagnóstico Codex ff2ea6b entregado; consola normal y corrección permanente pendientes. RF-093-001 sigue Open. | 2026-10-10 |
| [Deteccion de anomalias de coste](deteccion-anomalias-coste.md) | JUP-114: episodios integrados con #122; etapa periodica fuera del MVP (JUP-115). JUP-038: explicacion determinista incorporada desde #128. JUP-120 / #129: correccion de guia reconciliada localmente con `cf821570` (#130), sin cambiar producto; calibracion real reutilizada por identidad de entradas. Control independiente incremental pendiente. Detalle e historia en el tema enlazado. | 2026-10-15 |
| [Robustez ante datos incompletos](robustez-datos-incompletos.md) | JUP-071: contribución de Alejandro (PR #90, cerrado sin integrar) recuperada sobre develop: batería de 29 casos, runner, informe con cuatro estados, bloque `run` y comando `rows` (`rows-v1`, con `prompt_sha256` del servidor) para el dashboard de JUP-121, y aceptación de evidencia sin distancia. Dos mediciones de plantilla (0 aciertos, 8 fallos, 21 sin juicio) y una prueba con el colector de JUP-123 con modelo simulado; revisadas por agentes automatizados y, para el instrumento, por Víctor (revisión) y Paris (validación) en el PR #136. Primera medición parcial con el chat real el 2026-10-20 (una repetición, una revisora, informe provisional: 7 aciertos, 17 fallos y 5 bloqueadas de 29; 0 de 55 prohibiciones incumplidas; el fallo dominante es no pedir el dato que falta) y evidencia sin distancia validada con un backend real. Faltan la segunda revisión, dos repeticiones y la atestación del modelo. Desde el 2026-10-21 las filas de la campaña incluyen 19 filas de indicadores por las cuatro familias de un RAG, con un panel mínimo en el dashboard y la campaña en el manifiesto versionado (PR #144). Instrumento integrado en develop por el PR #136; la campaña está en la rama `feat/JUP-071-campana-robustez-real`. | 2026-10-20 |
| [Presupuestos y umbrales](presupuestos-umbrales.md) | JUP-029 / PR #61: correccion documental del P2 de Paris; convencion global separada en JUP-101, nueva revision y validacion pendientes. | 2026-10-02 |
| [Convención compartida](convencion-compartida.md) | JUP-101 / PR #64: adopción para el MVP por excepción de plazo autorizada por el usuario; ejecución asistida atribuida y requisitos humanos dispensados para este cierre, sin consenso ni reviews inventados. | 2026-10-10 |
| [Citas del asistente — JUP-025](citas-asistente.md) | Evidencia histórica de implementación conservada; consultar PR #55 para el estado posterior y el cambio OpenSpec archivado. | 2026-10-10 |

La fila y el resumen de presupuestos conservan su corte histórico de 2026-10-02.
La reconciliación de JUP-101 no revalida ese trabajo; el contraste posterior de
las PR de origen está en la evidencia enlazada desde la convención.
