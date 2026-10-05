# ADR-0016: Pin de LiteLLM 1.103.2 para validacion aislada

- Status: Proposed
- Date: 2026-10-02
- Related JUP/OpenSpec: [JUP-023 / jup-023-litellm-openrouter](../../openspec/changes/jup-023-litellm-openrouter/design.md)
- Trello: https://trello.com/c/O8elKkm9
- Supersedes: none
- Superseded by: none

## Context

La baseline historica JUP-078 usa LiteLLM 1.82.6 con digest
`sha256:7c311546c25e7bb6e8cafede9fcd3d0d622ac636b5c9418befaa32e85dfb0186`.
No se ejecutara, tampoco contra upstream simulado, por avisos aplicables:

- [GHSA-4xpc-pv4p-pm3w](https://github.com/BerriAI/litellm/security/advisories/GHSA-4xpc-pv4p-pm3w):
  bypass de Host Header en versiones < 1.84.0.
- [GHSA-r75f-5x8p-qvmc](https://github.com/BerriAI/litellm/security/advisories/GHSA-r75f-5x8p-qvmc):
  SQL injection en verificacion de API keys, >= 1.81.16 y < 1.83.7;
  relevante para PostgreSQL y claves virtuales del gateway.

Para elegir la version de destino tambien se revisaron avisos posteriores,
no aplicables a 1.82.6. Entre ellos,
[GHSA-7hp6-4w63-5g45](https://github.com/BerriAI/litellm/security/advisories/GHSA-7hp6-4w63-5g45),
critico, afecta >= 1.91 y < 1.100.4, >= 1.101 y < 1.101.3,
>= 1.102 y < 1.102.2, y >= 1.103 y < 1.103.1.

Segun la consulta del 2026-10-02 a la
[API oficial de advisories](https://api.github.com/repos/BerriAI/litellm/security-advisories?per_page=100),
ninguno de los 17 avisos listados incluye 1.103.2 en sus rangos afectados.
Esto no es una auditoria integral ni una afirmacion de ausencia de vulnerabilidades.

## Decision

Fijar la imagen oficial por version y digest reproducible:

`ghcr.io/berriai/litellm:v1.103.2@sha256:f63fb81b831b170ec16851e23c36ac5bf52ef106b271406429524a2ed730bbfd`

La [release v1.103.2](https://github.com/BerriAI/litellm/releases/tag/v1.103.2)
se publico el 2026-10-01. La subida corrige la baseline vulnerable sin usar
`latest`, prerelease ni introducir SDK o dependencias Python en el processor.

Decision operativa comunicada por Paris el 2026-10-02: aprueba 1.103.2 y
Docker local aislado con upstream simulado, sin gasto. Este ADR permanece
`Proposed` durante la revision de PR segun el flujo del repositorio.
La aprobacion no acepta ni sustituye [ADR-0002](ADR-0002-litellm-openrouter.md),
sus modelos, privacidad, presupuesto ni aprobaciones del equipo, y no autoriza
cambios en dependencias compartidas.

## Consequences

Gateway con PostgreSQL, datos y red propios; administracion solo en loopback.
No usar DockerServer ni alterar los datos o schema existentes de 8 dimensiones.
La compatibilidad Docker de config, API, autenticacion, claves virtuales,
privacidad y retries sigue pendiente: el gate de imagen esta autorizado,
pero la tarea 1.2 no se completa hasta comprobarla con upstream simulado.

Rollback solo a otra imagen corregida y aprobada o a mocks en development;
nunca a 1.82.6 ni a otra version vulnerable. No hay fallback automatico.
El uso real conserva sus gates independientes y techo agregado de 0,50 EUR.
Sin smoke real satisfactorio y evidencia no se da nuestra parte por terminada
ni se abre PR, tampoco borrador; siguen pendientes review y validacion humanas.

## Alternatives Considered

- Mantener 1.82.6: rechazado por vulnerabilidades aplicables.
- Elegir 1.84.0 como minimo: insuficiente ante avisos posteriores; requiere
  revisar todos los rangos, no solo la correccion de Host Header.
- Usar `latest`: no ofrece el pin reproducible requerido.
- Usar prerelease: innecesario existiendo la release estable seleccionada.

## Evidence And Follow-up

Comprobaciones realizadas el 2026-10-02:
inspeccion del registro y pull con digest coincidente; ejecucion de
`docker run --rm --network none --entrypoint python IMAGE -c ...`
(IMAGE es el pin anterior; el fragmento representa consulta de metadata e
import de Prisma) obtuvo `litellm 1.103.2` y `prisma 0.11.0`.
No demuestra compatibilidad de API ni de claves virtuales.
No habia cosign disponible y no se verificaron firmas; digest coincidente
no equivale a firma verificada.

Completar compatibilidad Docker y despues los gates del smoke real indicados
en [tasks.md](../../openspec/changes/jup-023-litellm-openrouter/tasks.md).
Prueba aislada del 2026-10-02: arranque, chat, embeddings, claves y retries
funcionan contra upstream simulado, pero persiste texto de errores upstream
en SpendLogs aun suprimiendo la salida de consola con `LITELLM_LOG=CRITICAL`.
Ese primer resultado bloqueo la compatibilidad de privacidad y motivo la
correccion siguiente; no acredita uso real.
Ver [evidencia JUP-023](../evidence/JUP-023-validation.md).
Seguimiento autorizado por Paris el 2026-10-02, "perfecto adelante", con el
alcance registrado en [proposal.md](../../openspec/changes/jup-023-litellm-openrouter/proposal.md):
misma imagen 1.103.2, callback publico en `infra/litellm/safe_logging.py` montado
solo lectura y registrado en config/Compose, primero Docker simulado sin gasto.
Sanear antes de SpendLogs conservando fallos y estado/modelo/request ID/tiempo/
duracion/tokens/coste disponibles; nunca `disable_error_logs` ni perdida de costes.
Resultado del mismo dia: replay Docker satisfactorio con 2 exitos y 8 fallos,
sin marcadores privados en consola ni filas completas. El mutante sin callback
falla por privacidad. El probe del inicializador confirma orden previo a DB y
aborto sin modulo antes del router; no constituye prueba HTTP de arranque.
Coste sintetico conocido y tokens se conservan en el limite del callback; no
acredita costes reales facturados ni su recuperacion en DB. La retirada del
flag de trazas no fue detectada en el replay HTTP, pero si por el helper real
de logging a nivel ERROR; son comprobaciones complementarias, no equivalentes.
Los errores de callback en runtime siguen siendo fail-open en LiteLLM; no se
ha anadido circuit breaker. Una prueba de privacidad fallida bloquea uso real.
Sin monkeypatch, parche del proveedor, SDK ni dependencias nuevas. Sigue
Proposed; no acepta ADR-0002 ni autoriza uso real. Permanecen pendientes los
limites de claves, privacidad upstream, facturacion y smoke real de JUP-023.
