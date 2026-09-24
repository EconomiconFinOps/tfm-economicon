# ADR-0007: Backend CORS policy

- Status: Accepted
- Date: 2026-09-23
- Related JUP/OpenSpec: JUP-085 / [jup-085-auth-session-contract](../../openspec/changes/jup-085-auth-session-contract/proposal.md)
- Trello: https://trello.com/c/Z8M443Hu
- Supersedes: none
- Superseded by: none

## Context

Frontend/API usan puertos separados, 5173/8000 por defecto. Upstream `develop`
en `3a08d60` no configura CORS; RF-087-001 y RF-095-001 siguen Open. El cliente
usa GET/POST con Authorization, Content-Type y X-Tenant-Id, sin auth por cookies.
El worktree JUP-085 ya consume HEAD `3a08d60` tras fast-forward que preservo los
15 archivos sucios previos. CORS/residual aprobados estan implementados;
codigo REVIEW_PASS; QA_BLOCKED_ENV y gate humano post-QA pendiente.

## Decision

Registro literal de aceptacion, conservado con su estado de aquel momento:

Aceptacion: Paris Arcos Martin, respuesta "aprobado" al gate concreto el
23/09/2026; registro 13:05:53 UTC en proposal.md. Se aprueban parametros,
superficies y limites descritos. Las referencias siguientes a Proposed/PENDING
conservan el contexto de presentacion; quedan resueltas por esta aceptacion.
La implementacion y QA siguen pendientes; no hay permiso de publicacion/merge.

Antecedente de presentacion anterior a la aceptacion (sin efecto de gate actual):

Direccion CHOSEN por Paris el 23/09/2026, respuesta "1": CORS en backend dentro
de la propuesta JUP-085. Proxy de mismo origen no seleccionado. Este ADR sigue
Proposed: parametros y archivos concretos requieren validacion, presentacion y
gate humano pre-code, actualmente PENDING. La seleccion no autoriza runtime.

Se propone reutilizar CORSMiddleware existente, sin dependencia nueva, con
`CORS_ALLOWED_ORIGINS` como lista JSON tipada en Settings: default `[]`, origenes
serializados exactos, sin `*`, `null`, regex ni reflection arbitraria. Configuracion
malformada falla al arrancar mediante StartupError generico sin input/secretos.
HTTPS en production; HTTP solo development/test. Ejemplos locales comentados:
`http://localhost:5173` y `http://127.0.0.1:5173`; cualquier puerto publicado
distinto exige ajustar la lista. Operador suministra origenes productivos.

GET/POST y cabeceras Authorization, Content-Type, X-Tenant-Id junto a safelisted
normales del framework; OPTIONS nativo sin JWT. `allow_credentials=false`,
`expose_headers=[]`, fetch actual sin cookies/include. CORS no sustituye JWT ni
tenant auth: una peticion simple denegada puede ejecutarse sin Allow-Origin.

El [diseno concreto](../../openspec/changes/jup-085-auth-session-contract/design.md#cors-direction-chosen-concrete-policy-pending)
preserva FastAPI app/state/overrides/lifespan/import y metricas/tracing de
peticiones reales. Propone CORS exterior a los middleware de usuario, con
Settings diferido; cubre 200/401/403/422 y 500 sanitizado por RequestIdMiddleware,
sin prometer CORS para errores generados fuera de esa capa. Preflight termina
antes de metricas/log de acceso interiores. Limites incluidos en el gate resuelto;
el contrato tecnico descrito se conserva sin cambios en esta sincronizacion.

## Consequences

Lista vacia mantiene el bloqueo cross-origin hasta configuracion explicita.
HTTP en production fallara al arrancar; el ejemplo mantiene production y `[]`
por defecto, sin cambiar entorno automaticamente. `.env` ignorado no se edita,
copia ni sobrescribe, y no se retiran secretos. No es hardening productivo completo.
JUP-097 conserva perfil/tenants paralelos y logout ante cualquier error de query
`/me`, incluso transitorio, con retries intactos. Sin ampliacion de JUP-086,
RF-087-002, seed, migraciones, CI, dependencias ni runner.

## Alternatives Considered

- Proxy de mismo origen: opcion presentada y no seleccionada por Paris.
- Wildcard/regex/reflection o desactivar seguridad del navegador: incompatibles
  con la politica explicita propuesta y la aceptacion sobre stack canonico.

## Evidence And Follow-up

Fuentes: main/config, services/api.ts, Compose, ejemplo de entorno y contratos
nativos de import/lifespan/errores de upstream. Resultados actuales comunicados
por el orquestador: 245 backend y 235 frontend PASS; 76 CORS PASS
tambien con pydantic-settings 2.3.4, sin cambiar dependencias. Este pase documental
no reejecuta producto. Los 169 tests del 10/09 siguen como resultado historico.
Ver [tareas](../../openspec/changes/jup-085-auth-session-contract/tasks.md) y
[escenarios](../../openspec/changes/jup-085-auth-session-contract/specs/demo-auth-session/spec.md).
Codigo REVIEW_PASS; RF-085-002 Open, mitigacion temporal insuficiente.
El [review actual](../../openspec/changes/jup-085-auth-session-contract/review.md)
y la [evidencia ambiental](../evidence/JUP-085-validation.md#revalidacion-qa-tras-mitigacion-2309)
registran QA_BLOCKED_ENV; ajuste persistente no autorizado ni aplicado. JWT y esta
decision siguen intactos. RF-087-001/RF-095-001 Open hasta completar QA;
gate humano post-QA pendiente, aprobaciones conservadas.

Numeracion secuencial segun README/template nativos: ambas raices y refs locales
origin JUP-014/JUP-069 contienen ADR-0001 a ADR-0006, sin 0007 en la lectura del
23/09. Reconfirmar numero y enlaces al sincronizar/fusionar en el futuro, pues
otras ramas pueden incorporar otro ADR; no sincronizar ni renumerar hoy.
