# Review JUP-022

## Resumen

El backend embebe la pregunta del chat con el mismo modelo que la ingesta (alias `economicon-embedding`, 1536 dimensiones) a traves del gateway LiteLLM y con una clave virtual propia, y la recuperacion tiene un contrato explicito: `top_k`, distancia maxima, orden por distancia y despues por identificador, resultado vacio sin relleno, filtro de tenant y de proveedor en la misma consulta, fallos como 503 con cuerpo fijo y una traza por recuperacion sin la pregunta ni el contenido. Los valores por defecto salen de una calibracion reproducible con el banco JUP-069 y etiquetas por seccion.

## Decisiones

- Clave virtual propia del backend (`BACKEND_LITELLM_API_KEY` en Compose) y cliente propio en la biblioteca estandar, con una prueba de paridad con el processor. Registrado como [ADR-0017](../../../../docs/adr/ADR-0017-backend-query-embedding-own-key.md) (Proposed).
- `mock` solo en `development` y `test`; `litellm` exige clave y dimension 1536.
- Umbral por defecto segun proveedor: 0.6 con `litellm` (regla escrita en el informe) y ninguno con `mock`; `none` u `off` lo desactivan.
- Los casos `clarify` y `abstain` se miden aparte y no fijan el umbral.
- El orden entre guardar el mensaje del usuario y recuperar no se modifica (decision 5 del diseno).
- No se cambia el troceado de la ingesta: se mide y se deja como finding.

## Validacion

Comandos y resultados completos en [docs/evidence/JUP-022-validation.md](../../../../docs/evidence/JUP-022-validation.md): backend 552 passed con pgvector real y 540 como la CI, processor 414, utilidades Python 59, herramientas 242 de 243 (el fallo es del doctor de JUP-050 por puertos ocupados en la maquina de validacion), OpenSpec 40/40, 32 mutantes aplicados y 32 detectados tras reforzar las pruebas de los que sobrevivieron al principio, y calibracion real con 80 llamadas.

## Adversarial Review

### Pass 1 - accept

Agente `adversarial-reviewer` independiente. Sin BLOCKING ni HIGH; 14 hallazgos de severidad MEDIUM o LOW, contrastados con el codigo antes de decidir.

| ID | Sev | Disposicion |
| --- | --- | --- |
| ADV-1 | MEDIUM | Aceptado y documentado. El SQL real solo se ejecuta en los tests opt-in (`JUP086_VECTOR_TEST_URL`); se ejecutaron contra pgvector real (552 passed) y quedan fuera de la CI, el mismo patron que RF-096-004. |
| ADV-2 | MEDIUM | Aceptado con dependencia. La paridad de categorias se salta mientras el cliente de #65 no este en `develop`; se comprobo a mano contra el fichero de #65 (9 categorias iguales) y dejara de saltarse al integrarse. |
| ADV-3 | MEDIUM | Aceptado como precondicion. `EMBEDDING_PROVIDER` es una unica variable de Compose para backend y processor a proposito (misma configuracion en ingesta y consulta); activar `litellm` exige #65. Documentado en el README del backend. |
| ADV-4 | MEDIUM | Aceptado: es la decision 5 del diseno (el mensaje se guarda antes de recuperar, necesario para el id del evento), igual que RF-025-001. |
| ADV-5 | MEDIUM | Registrado como RF-022-003 (la pregunta no tiene tope de longitud); cambiar el contrato del API no es de este cambio. |
| ADV-6 | LOW | Corregido: la clave de `litellm` rechaza los placeholders conocidos fuera de `test`. |
| ADV-7 | LOW | Corregido: `top_k` solo admite enteros ASCII; se rechazan booleanos, decimales y digitos unicode. |
| ADV-8 | LOW | Corregido: la distancia maxima solo admite decimales ASCII; se rechazan exponentes y digitos unicode. |
| ADV-9 | LOW | Corregido: un vector sin direccion (todo ceros o menor que 5e-7) se rechaza como `invalid_response` antes de buscar. |
| ADV-10 | LOW | Corregido en el backend (el opener ignora los proxies del entorno, con test); el cliente del processor tiene el mismo patron, registrado en RF-022-004. |
| ADV-11 | LOW | Aceptado: `provider` es opcional en `search_chunks` para herramientas como `scripts/validate_vector_database.py`; la unica llamada de produccion lo pasa siempre y un test lo fija. |
| ADV-12 | LOW | Corregido: el validador de etiquetas rechaza `expect` que no sea una lista. |
| ADV-13 | LOW | Corregido: error controlado ante `EMBEDDING_DIMENSION` no numerico y ante fallos del proveedor a mitad de ejecucion (sin su texto); el informe advierte de que los reintentos pueden multiplicar el gasto real. |
| ADV-14 | LOW | Parcial: comentario en `.env.example`; la regla del doctor se registra en RF-022-004. |

Todas las correcciones se hicieron con test que falla sin ellas (comprobado quitando cada arreglo) y la bateria completa pasa despues.

## Barrido del patron

- Vectores de norma cero: la ruta del chat lo rechaza ahora; `tools/retrieval-calibration.py` ya lo hacia.
- Valores numericos de configuracion: `top_k` y la distancia maxima eran los unicos que usaban la conversion laxa de pydantic o de `float`.
- Secretos: la clave del backend sigue las reglas de `SecretStr`, redaccion, repr y logs; los placeholders ya no son solo cosa de los DSN.
- Llamadas a `search_chunks` y a `embed` en produccion: solo la ruta del asistente.

## Riesgos aceptados por Lucia

Pendientes de su decision en la aprobacion: ADV-1, ADV-2, ADV-3, ADV-4, ADV-5 (RF-022-003) y ADV-11, y el limite del troceado actual (RF-022-002).

## Findings

- RF-022-001: un cambio de modelo con la misma dimension no se detecta.
- RF-022-002: el troceado por ventanas de caracteres limita el acierto por seccion; evaluar 500/100 y el troceado por encabezados.
- RF-022-003: la pregunta del chat no tiene tope de longitud (coste y errores `request` perpetuos).
- RF-022-004: el cliente LiteLLM del processor toma proxies del entorno y el doctor no valida `RUNTIME_ENVIRONMENT=production` con `EMBEDDING_PROVIDER=mock`.

## ADR

[ADR-0017](../../../../docs/adr/ADR-0017-backend-query-embedding-own-key.md), Proposed. El numero 0017 sigue a los ADR-0013 a 0016 de los PR #60 y #65 y se renumera si cambian antes de integrarse. No sustituye ni cierra ADR-0002.

## Human Approval

- Change: jup-022-semantic-retrieval
- Approval type: post-review
- Decision: approved
- Approver: Lucia
- Date: 2026-10-03
- Adversarial review: accept (pass 1) | accepted findings: ADV-1, ADV-2, ADV-3, ADV-4, ADV-5 (RF-022-003), ADV-11, limite del troceado (RF-022-002)
- Archive decision: archive
- Notes: revisados el codigo, las specs, el diseno, la evidencia y la revision adversarial. Pendiente: abrir el PR hacia develop y la revision y validacion de las personas asignadas en Trello; la paridad de categorias con el processor se activa al integrarse #65.
