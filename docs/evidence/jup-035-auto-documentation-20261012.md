# JUP-035 / PR120 — parche de decisión automática

Verificado el 12/10/2026. Origen: «Implementa # Orden de trabajo — JUP-035 / PR120»,
chat `01a1302b-c7a5-7c71-ba85-4d2391f8ff33`. Preparación técnica local; no revisión
ni validación humanas, publicación, merge, despliegue o cierre de JUP-035.

## Entrega y alcance

- PR de Paris: https://github.com/EconomiconFinOps/tfm-economicon/pull/120
- Base de este aporte: `f63c15031b65c99f1da149e867675ff771d3c1dd`, sobre develop
  `8035a3de08fcf8c4c5f825aeba0a07e7e8c4311f`. Consultados HEAD, diff, conversación,
  reviews y comentarios inline; siguen sin comentarios/reviews al segundo corte.
- Rama propia: `fix/JUP-035-auto-documentation`, checkout `tfm-economicon-jup035-auto`.
- Commit de código y pruebas: `5dd15972e53afa1668d80ba5d75c07c821d7a61b`.
  La entrega añade después únicamente documentación; el README del paquete fija
  el SHA de entrega y hashes de los parches. No se empuja a la rama original.
- [Paquete reproducible del espacio](../../../materiales/07-evidencias/JUP-035-PR120-auto-20261012/README.md)
  conserva logs, contraste de base y parches. En un clon independiente este enlace
  externo puede no existir: los requisitos y pruebas permanecen en el repositorio.

## Diagnóstico demostrado y límites

La reproducción sobre f63c150 da **4 fallos funcionales y 3 rechazos correctos**:
llamada nativa auto y decisión sin herramienta son rechazadas, y los dos recorridos
no ejecutan la finalización prevista. El parser admite native_seen solo en required;
fuera de esa rama espera JSON final. Además el coordinador y ChatOperations
codificaban búsqueda obligatoria. Son causas propias demostradas con SSE controlado,
no prueba de incapacidad de GLM/DeepInfra ni de transformación por LiteLLM/OpenRouter.
La influencia del esquema estricto sobre la decisión real sigue siendo hipótesis.

## Diseño implementado

`auto-documentation-v2` separa una decisión privada `auto`, sin response_format,
de la respuesta `none` con esquema FinOps estricto. Siempre hay como máximo dos
peticiones de generación y cero/una búsqueda. Sin búsqueda se reutiliza únicamente
el contexto original autorizado; el texto de decisión se descarta, no se muestra,
no se persiste y no entra como contexto de la segunda petición. Con búsqueda se
conservan envelope nativo validado, tool_call_id y resultado HMAC del backend.

El prompt exige buscar hechos documentales sin sustento previo; si auto no busca,
la aplicación exige abstención/aclaración no accionable cuando falte evidencia.
No hay búsqueda forzada ni tercera llamada oculta. La validación estructural rechaza
citas inventadas, provenance alterada y métricas no contrastadas por billing; no
certifica por sí sola la verdad semántica de answer. Esa evaluación sigue pendiente.

Se mantienen proveedor deepinfra/fp4 sin fallbacks, modelo alias economicon-chat,
límites de tokens/herramientas, deadline común, cancelación, intento vigente,
autoridad financiera y suma de uso real de ambas llamadas. Ni usuario ni corpus
conceden autoridad a métricas. Contadores/costes incompletos no se estiman.

Ambos servicios, descriptor, contexto, operaciones, prompt, hashes y OpenSpec
negocian el contrato nuevo. El bundle conserva nombre v3 con hash nuevo; un peer
antiguo falla cerrado. Mock continúa por su gateway y contrato independientes.
El archivo OpenSpec anterior queda intacto y la evolución está en el cambio activo
[jup-035-auto-documentation](../../openspec/changes/jup-035-auto-documentation/proposal.md).

## Verificación

Windows, CPython 3.12.13 y tokenizers 0.22.1; dependencias de prueba aisladas,
versiones exactas en el paquete. No se instalaron dependencias globales.

| Comprobación | Resultado y alcance |
| --- | --- |
| Reproducción sobre f63c150 | 4 FAIL / 3 PASS; errores del protocolo, no imports/fixtures |
| Backend focal final | 62 PASS / 15 SKIP; SKIP requiere CockroachDB exclusivo |
| Processor focal final | 130 PASS; gateway, privado, recursos, contexto y nuevos casos auto |
| Frontend | 882 PASS / 72 archivos |
| API de costes | 81 PASS |
| Build raíz | 4/4 PASS |
| OpenSpec estricto | 67/67 PASS |
| PR policy / CI / gobernanza | 57 / 12 / 13 PASS |
| Trazabilidad / higiene | PASS |
| Campaña amplia durante desarrollo: backend | 1480 PASS, 148 FAIL, 82 SKIP |
| Campaña amplia durante desarrollo: processor | 980 PASS, 13 FAIL, 71 SKIP, 4 ERROR |

No sumar focales con suites solapadas ni presentar la campaña amplia como una
batería final verde. Los nuevos casos cubren: búsqueda y continuación, cero herramientas,
respuesta directa con billing, saludo/aclaración, búsqueda vacía, citas inventadas,
cifras sin autoridad, herramienta desconocida, argumentos inválidos, segunda llamada,
correlación errónea, SSE fragmentado, EOF, final inválido, 429 en ambas fases,
cancelación en decisión/búsqueda/final, deadline sin reinicio y uso combinado.
El endpoint privado se ejercita con ChatGateway real y HTTP sintético; se rechazan
tenant/usuario ajenos, claim caducado, falta de HMAC, resultado repetido y manipulado.
Historial/par único/reapertura se ejercitan offline con SQLite, no como JSONB real.

**Fallos de base contrastados:** los 13 FAIL y 4 ERROR del processor se reproducen
sobre f63c150 (solo fixture LF normalizada para que el hash sea válido en Windows).
Incluyen cancelación de resumen, privilegio de symlinks y procesos hijos sin
uvicorn/dependencias. De los 148 FAIL backend, 147 se reproducen idénticamente:
symlinks y doubles de red JUP-047 que interceptan el socketpair del loop Windows.
El restante era una carrera de fixture: esperaba waiting tras 30ms y encontraba el
intento anterior. Se corrige esperando también attempt_count, sin relajar presupuesto,
reintentos ni aserciones. La suite focal conjunta posterior pasa 62/62 ejecutadas.

Dos ajustes de entorno se registran sin ocultar sus fallos iniciales: el lanzador
virtual Windows cambia el PID del resolver, por eso se ejecuta el intérprete real
con dependencias en PYTHONPATH; el fixture hash usa bytes UTF-8 en vez de traducción
CRLF. Turbo escogía pnpm de fallback; un wrapper temporal usa corepack/pnpm 9.0.0.
El build pasa después. Los tests de frontend/API pasan con env-mode=loose para
transmitir el PYTHONPATH local. No se modifican límites o configuración de producción.

## Ampliación Linux autorizada — 12/10/2026

El usuario autorizó expresamente copiar el checkout y ejecutar pruebas aisladas
en DockerServer, sin despliegue. Se probó `9829d82c799487e8223a91be4259605335d59a2f`
(mismo código `5dd1597`), mediante git archive verificado por SHA256:
`9a5c882d7472c0ae534b4162fc308281f1f6bf87dd928c2f787ec21d7e73ae27`.
Fuente de solo lectura, Python 3.12.13, tokenizers 0.22.1, pytest 9.1.1,
CockroachDB 24.1.11 y pgvector pg17. Contenedores sin puertos publicados,
red aislada, datos sintéticos y ninguna credencial ni inferencia externa.
Receta, identificadores de imágenes y logs están en `linux/` del paquete externo.

| Ejecución Linux | Resultado |
| --- | --- |
| Processor completo | 1002 PASS / 71 SKIP; 420.73 s |
| Backend completo | 1654 PASS / 47 SKIP / 8 FAIL / 3 ERROR; 434.61 s |
| Backend focal final | 77 PASS, sin SKIP; 29.42 s; incluye 15 casos CockroachDB |
| CockroachDB + aislamiento/contratos pgvector focales | 31 PASS / 1 FAIL |
| Metadata de chat + salud, repetición focal | 51 PASS; también 51 PASS sobre f63c150 |

No sumar ejecuciones solapadas. El fallo pgvector de citas se reproduce sobre
f63c150: `test_filtered_ranked_context_resolves_only_its_document_citation_in_the_route`
espera `retrieved_context` sobre un `Response`. Los otros siete FAIL de la campaña
amplia (metadata mismatch y seis casos de autenticación de salud) no se repiten
en sus módulos aislados; causa aún no establecida. No se declara suite amplia verde.

Se conservan los intentos fallidos: instalación inicial con hashes, arranque SQL
y campaña amplia. CockroachDB temporal se detuvo durante esta última, con causa
no confirmada; fue recreado y las 15 pruebas del chat pasan. Los tres ERROR de
summary SQL proceden de conexión rechazada; además ese módulo exige una base y
conversación de smoke específicas que este entorno no provisiona. Esos probes
siguen pendientes, al igual que las integraciones omitidas que los logs enumeran.
Las pruebas focales posteriores no cambian código ni debilitan aserciones.
Contenedores e imagen temporal retirados y ausencia de contenedores de esta
campaña comprobada. Archivos en `/tmp/economicon-jup035-auto-01a1302b` conservados
como evidencia; logs copiados al paquete local. No hubo despliegue.

## Matriz real y aceptación pendiente

| Ruta / parámetros | Estado | finish_reason / herramientas / latencia / uso / coste |
| --- | --- | --- |
| LiteLLM, auto sin response_format | NOT_RUN | No medidos |
| LiteLLM, auto con esquema estricto | NOT_RUN | No medidos |
| LiteLLM, required como control | NOT_RUN | No medidos |
| OpenRouter directo equivalente | NOT_RUN | No medidos; ruta no autorizada |

No se usaron claves ni presupuestos históricos; no hay saldo/caducidad vigente
verificados para este encargo. **Cero inferencias externas realizadas.** El modelo
GLM-5.2 es una referencia de configuración del repositorio, no la configuración
efectiva del entorno verificada aquí. La simulación usa respuestas controladas;
no mide decisiones, costes ni latencias reales del proveedor.

Pendientes: autorización de entorno/presupuesto y límite total, configuración
efectiva/versiones del gateway, matriz comparable, probes SQL de summary/navegador
y batería JUP-069 completa de 28 preguntas sobre un único SHA final. No hay 28/28.
El bloqueo inicial de copia por revisión automática quedó resuelto con la
autorización explícita del usuario. La ampliación Linux anterior acredita el
alcance SQL indicado; no acredita aceptación del proveedor, navegador o full28.

Paris conserva liderazgo, Víctor pairing, Alejandro revisión y Lucía validación.
Este aporte no acredita sus dictámenes ni los sustituye; tampoco se envía a Discord,
Trello o GitHub. Paris debe revisar/integrar el parche y coordinar aceptación antes
de cualquier publicación o despliegue.
