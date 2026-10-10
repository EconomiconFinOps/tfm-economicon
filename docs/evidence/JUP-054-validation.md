# Evidencia técnica — JUP-054

Fecha: 2026-10-10. [Trello](https://trello.com/c/ZsxwmagI).
[PR draft #93](https://github.com/EconomiconFinOps/tfm-economicon/pull/93), rama
`test/JUP-054-critical-flows`. Base: `c2995a118d419dfe725247bac9c6f219a3f0ea77`.

## Entrega y atribución

Siete casos nuevos conectan componentes que antes se probaban por separado:
API Azure local HTTP → cliente → normalizador → SQL SQLite (4); AgentRuntime →
LangGraph → IngestTask → SQL SQLite (3). Se amplía el recorrido real existente
CockroachDB/RabbitMQ/pgvector con GET del historial, igualdad de mensajes/citas,
JSONB y denegación entre tenants. No se reimplementa producto ni se repite JUP-087.
Vitest se invoca directamente dentro de su job CI, sin caché Turbo.

[Matriz, límites y reproducción](../testing/critical-flows.md).
OpenSpec: `jup-054-test-strategy-and-critical-flows`.

Contribución preparada en copia aislada
`C:/Users/DanteInferno/Documents/Economicon/tfm-economicon-jup054`; el checkout
compartido y las ramas ajenas permanecen intactos. Roles confirmados por la
integración oficial de DockerServer el 10/10: Lucia Mateo, liderazgo; Paris
Arcos Martin, pairing; Victor Mendez, revisión; Alejandro Aguado,
validación/pruebas/documentación. Esta es una rama de aportación propia para su
adopción por Lucía, no un dictamen independiente de los propios cambios.
No acredita pairing ni aceptación humana ni reasigna roles.

## Resultados aprobados

[CI push 38035094870](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035094870)
y [CI PR 38035169344](https://github.com/EconomiconFinOps/tfm-economicon/actions/runs/38035169344)
aprobados sobre `69b9e7fb91a3ab1c7f5578aa46b4c29a494a0df5`. Los logs del primero
conservan estos conteos. Los checks del head vigente se consultan en la PR.

| Verificación | Resultado observado |
| --- | --- |
| Backend completo, CI Linux | 898 passed, 34 skipped |
| Processor completo, CI Linux | 455 passed, 57 skipped, incluidos los 7 casos nuevos |
| Azure Cost API completo, CI Linux y Windows | 59 passed |
| Frontend completo, CI Linux | 629 passed en 53 archivos |
| Frontend lint, tipos y build | Exit 0 en Windows y CI Linux; aviso existente de bundle grande |
| Nueva integración agente, Windows aislada | 3 passed |
| Repetición final de los 7 casos juntos, Windows | 7 passed, 24.53 s, con timeout de contrato final de 10 s |
| Nuevo contrato Azure, Windows aislado | 4 passed |
| Recorrido real tenant/historial, Linux aislado | 3 passed, 14.23 s; sin skips |
| Checks locales CI/política/gobernanza | 82 passed |
| Trazabilidad / OpenSpec | Exit 0 / 56 passed, 0 failed |

Son **2041 pruebas de aplicación aprobadas en CI**, más los tres escenarios
reales externos a CI. Los 91 skips de servicios no prueban sus integraciones.
`JUP reviews` queda pendiente de dictámenes humanos; no se presenta como verde.

## Intentos Windows y contraste

Los intentos que fallaron se conservan, no se borran de la evidencia:

- Backend completo: 729 passed / 169 failed / 34 skipped. En 145 fallos, los
  fixtures de JUP-047 interceptan `socket.connect` usado por el `socketpair`
  interno de asyncio Proactor en Windows, antes de invocar el endpoint. Los
  otros 24 afectan a observaciones con plazos breves de DNS, publisher,
  embeddings y concurrencia. Backend no tiene cambios respecto a la base.
- Processor completo: 448 passed / 7 failed / 57 skipped. Cuatro plazos de
  streaming existentes, dos subprocessos existentes a 30 s y una lectura HTTP
  del nuevo contrato a 2 s. Las siete nuevas pruebas pasaron por separado.
- Frontend Windows: se observaron timeouts a 5 s y errores de expectativas bajo
  carga; se interrumpió el intento tras completar las 629 pruebas en CI Linux.
  No se atribuye un conteo final de éxito al intento interrumpido.
- Integración real Windows: 3 fallos (subprocess a 30 s y publicación 503).
  Misma suite y aserciones en Linux: 3 passed. No se relajan sus plazos ni guards.

Todos los tests completos afectados pasan en CI Linux. La carga es una
explicación compatible para los plazos; no prueba por sí sola su causa. La
colisión socketpair/guard en Windows sí está confirmada por la traza.
El fixture nuevo de contrato usa finalmente 60 s de readiness y 10 s de lectura:
no evalúa latencia, que ya tiene su suite específica. No se modifica ningún
límite temporal del producto ni de pruebas existentes.

## Entorno, artefactos y ciclo de vida

Windows: Node 24.14.1, pnpm 9.0.0, Vitest 3.2.7, Python 3.12.13. Entorno virtual
nuevo con requirements-dev de los tres servicios; CI usa Node 22 y entornos
Python separados. Linux aislado: Python 3.12.13, FastAPI 0.143.0, SQLAlchemy
2.0.54, psycopg 3.3.6, pytest 9.1.1, LangGraph 1.2.14, httpx 0.28.1.
Dependencias Python resueltas completas: `.artifacts/jup054/*python-dependencies.txt`.

Comandos completos y límites de fixtures están en la matriz. Se usaron pytest
por servicio y Vitest directo; ningún resultado deriva de un hit de Turbo.
Los nuevos tests finales se ejecutan juntos con:

```sh
# Desde apps/processor, con el entorno Python activado:
python -m pytest tests/test_azure_api_contract_integration.py tests/test_agent_ingestion_integration.py -q -ra
```

Para el recorrido real se crearon exclusivamente `economicon-jup054-crdb`,
`economicon-jup054-vector`, `economicon-jup054-rabbit` y `economicon-jup054-runner`,
con límites de recursos y sin volúmenes compartidos. DockerServer recibió sólo
130 archivos fuente/fixtures revisados (550528 bytes), sin dotenv, repositorio
Git, entornos ni archivos personales. El runner usó red puente privada,
`--cap-drop ALL` y `no-new-privileges`; proxies propios proporcionaron loopback
para respetar los guards existentes. La alternativa inicial de copiar el proyecto
completo con red del host fue rechazada por la revisión automática y no se ejecutó.

Imágenes del recorrido real (IDs Docker):

- Cockroach `v24.1.11`: `sha256:89bda255c52b25f463c7a9373ffedef122a4d9f1b432aa34b897970fe864a66c`.
- pgvector `pg17`: `sha256:cf134a767f474095eeba57e0117be8e568e011a63f33fbf252f14c9b760f8e6f`.
- RabbitMQ `3.13-management`: `sha256:e582c0bc7766f3342496d8485efb5a1df782b5ce3886ad017e2eaae442311f69`.

Artefactos locales en `.artifacts/jup054/`, excluidos de Git:

| Archivo | SHA-256 |
| --- | --- |
| `linux-reviewed-source.tar.gz` | `C916D51A5733247B1D338C215552F5AA593ED5DF71DA7D238DD140C8C0D0BF59` |
| `linux-real-integration.xml` | `9CDC6F84E7341BE67D9B00FC636AABF0C253B32195A7C9879A427BFBB4626F22` |
| `ci-38035094870.log` | `8F557C6BF99F41587EF0EA3330F359D6CA5F08050384711F191C5EC094703519` |

XML, logs y comandos de la ejecución real quedan conservados. Se retiran los
contenedores/red/túnel propios tras comprobar sus etiquetas de propiedad;
recibo local `cleanup.txt`. No se toca ningún servicio compartido.

## Criterios y pendientes

| Criterio de Trello | Evidencia / situación |
| --- | --- |
| Resultado funcional verificable | Contratos, persistencia y errores comprobados en las suites nuevas y reales |
| Pruebas necesarias añadidas y en verde | 7 casos nuevos, suite CI completa y recorrido real aprobados; limitaciones Windows arriba |
| Documentación y decisiones actualizadas | Matriz, OpenSpec, este informe y continuidad |
| Pull request revisado y vinculado | PR #93 draft enlazada; revisión humana pendiente |
| Validación funcional y evidencia enlazadas | Evidencia técnica por criterio; aceptación independiente pendiente |

Pendiente de Lucía: adoptar la contribución y coordinar pairing/revisión/validación
independientes; después, integración y cierre según CONTRIBUTING.md. No se mueve
ni se cierra la tarjeta. Sin mensajes Discord. La evidencia no acredita Azure
cloud, LLM externo, gateway LiteLLM real, reinicio RabbitMQ, todas las migraciones,
Compose completo ni navegador real. RF-096-004 (infraestructura en CI) sigue separado.
