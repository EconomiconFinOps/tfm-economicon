## Context

Ver [proposal.md](./proposal.md) — Why. Lo que aquí importa del estado actual:

- `services/api.ts` expone 10 operaciones sobre un único helper `fetchJson`, que ya centraliza base
  (`VITE_API_BASE_URL`), `Authorization: Bearer` y `X-Tenant-Id`. La forma es correcta; lo que nunca
  se ha hecho es **verificar que cada operación corresponde al contrato que dice consumir**.
- `POST /auth/login` devuelve `access_token` **y el `UserProfile` completo**. `GET /me` devuelve
  exactamente ese mismo `UserProfile`. Es decir: como *fuente de identidad*, `fetchProfile` es
  redundante con el login.
- `SessionGate` valida la sesión persistida en `localStorage` **solo estructuralmente** (`isSession`
  comprueba que `accessToken` sea texto y que `user` tenga los 4 campos de `UserProfile`). Nada
  confirma contra el servidor que ese token siga siendo válido ni que esa identidad sea real.
- El único punto que hoy detecta un token inválido es el fallo de `fetchTenants`, que desemboca en la
  pantalla "No se han podido cargar los tenants" con botón *Reset session*.

Restricciones que condicionan el enfoque:

- ADR-0003 (`strict: true`, sin `any` nuevo ni `@ts-ignore`) y ADR-0004 (subconjunto shadcn/ui).
- `RF-095-001`/`RF-087-001`: el backend no configura `CORSMiddleware`, así que **no se puede
  verificar en navegador real** entre `localhost:5173` y `localhost:8000`. `curl` no lo detecta.
- No se toca `apps/backend/**` (criterio de aceptación de la tarjeta).

## Goals / Non-Goals

**Goals:**

- Dejar la capa de acceso verificada contra el backend real, con la verificación registrada aunque el
  resultado sea "cero desviaciones".
- Cerrar `RF-090-003` con una decisión razonada y ejecutada, no con una nota.
- Producir un mapa de carencias por pantalla que sea a la vez **localizable desde la pantalla** y
  **enumerable desde un único sitio**, porque son dos necesidades distintas (depurar vs. priorizar).
- Dejar la capa lista para que `reconcile-auth-tenant` construya sesión encima sin rehacerla.

**Non-Goals:**

- Diseñar el flujo de sesión, el guard de rutas o la semántica de logout. Es de la tarjeta siguiente;
  aquí solo se toca `SessionGate` en el punto exacto que exige la decisión 2.
- Rediseñar `fetchJson`. Funciona y centraliza lo que debe; reescribirlo sería cambio sin causa.
- Introducir una librería de validación de esquemas en tiempo de ejecución (ver decisión 4).

## Decisions

### 1. La auditoría se verifica contra el backend levantado, no contra la documentación

Se comparan las 10 operaciones contra `apps/backend/app/api/routes/` **y** contra respuestas reales
del backend en ejecución (`docker compose up backend`), no contra `apps/frontend/README.md`. El
README es documentación derivada y puede ser justamente lo que esté desviado; tomarlo como referencia
haría que una desviación documentada se validara a sí misma. Si README y backend discrepan, manda el
backend y el README se corrige.

*Alternativa descartada:* auditar solo por lectura de código de ambos lados. Detecta desajustes de
ruta y método, pero no de **forma de respuesta**, que es donde un `response_model` de FastAPI y una
`interface` de TypeScript divergen en silencio sin que nada falle hasta que una pantalla muestra
`undefined`.

### 2. `RF-090-003`: `fetchProfile` se CONECTA, como revalidación de la sesión persistida

`GET /me` se invoca desde `SessionGate` al arrancar con una sesión recuperada de `localStorage`, y su
respuesta pasa a ser la identidad que el armazón expone por `Outlet context`.

Razones:

1. **Completa un trabajo que JUP-095 dejó a medias.** Esa tarjeta añadió `isSession` precisamente
   porque "la sesión persistida se valida antes de confiar en ella" (requisito vigente de
   `frontend-navigation-shell`). Pero una validación estructural solo descarta basura: un
   `localStorage` fabricado a mano con un token inventado y un `user` bien formado **pasa hoy el
   filtro**. El servidor es la única autoridad sobre si ese token sigue vivo y a quién pertenece.
2. **Elimina la deriva en la dirección contraria.** Retirarlo dejaría `GET /me` implementado,
   documentado y con `response_model` en el backend, sin un solo cliente. Eso no cierra la deriva:
   la mueve de lado.
3. **La identidad deja de ser un dato congelado.** Hoy el nombre y el rol que muestra el armazón son
   los del momento del login, guardados indefinidamente; si cambian en servidor, el frontend nunca se
   entera.

*Alternativa descartada:* retirarlo. Es defendible — el login ya devuelve el perfil y `fetchTenants`
ya falla con un token muerto — pero apoya la identidad en un valor de `localStorage` que el servidor
no confirma nunca, y deja un contrato del backend sin consumidor. El coste de conectarlo es una
petición al arrancar, junto al bootstrap de tenants que ya ocurre.

**Frontera con `reconcile-auth-tenant`:** aquí se conecta la llamada y se usa su respuesta como
identidad. **No** se cambia el login, ni el mecanismo de persistencia, ni el guard, ni la semántica de
logout. Si `/me` falla, se reutiliza el camino de fallo que `SessionGate` ya tiene (`handleLogout` →
`/login`), sin inventar uno nuevo.

### 3. El mapa de carencias vive en dos sitios, con papeles distintos

- **Junto a cada módulo de `src/data/demo/`**: el comentario existente "DATOS DE DEMOSTRACION
  (sustituibles)" se amplía nombrando la capacidad de backend concreta que falta. Sirve a quien llega
  desde la pantalla preguntándose por qué el dato no es real.
- **En un único documento de planificación** (`docs/planning/JUP-097-frontend-data-gap-map.md`): una
  tabla pantalla → dato → capacidad ausente → finding relacionado. Sirve a quien tiene que decidir
  qué construir primero.

No es duplicación: son las dos consultas distintas que exigen los dos escenarios del requisito "Cada
pantalla sin contrato declara la capacidad que le falta". Un comentario disperso no es enumerable; una
tabla remota no es localizable desde el código.

*Alternativa descartada:* solo el documento. Más barato de mantener, pero deja al que depura la
pantalla sin pista local, que es exactamente el problema que `RF-095-002` describe.

### 4. La forma de las respuestas se fija con pruebas, no con validación en tiempo de ejecución

La correspondencia entre `contracts.ts` y lo que el backend devuelve se protege con pruebas que
fijan la forma esperada en el límite HTTP (`fetch` sustituido), no añadiendo un validador de esquemas
en ejecución.

Añadir una librería de validación sería una dependencia nueva, una decisión duradera que ataría a
todo el frontend y, por ADR-0003, material de ADR propio. Es desproporcionado para una tarjeta cuyo
alcance es auditar. Si la auditoría demuestra que la deriva es recurrente, esa será la evidencia para
proponerlo en su propia tarjeta.

### 5. La verificación asume que el navegador real está bloqueado

`RF-095-001` impide el recorrido en navegador. La verificación de esta tarjeta se apoya en:

- **Pruebas Vitest** con `fetch` sustituido para el comportamiento observable (carga, error,
  reconsulta al cambiar de ámbito, revalidación de sesión).
- **Comprobación directa contra el backend en ejecución** para la forma real de cada respuesta, por
  fuera del navegador (donde CORS no aplica).

Se documenta explícitamente que el E2E en navegador queda pendiente de que se resuelva `RF-095-001`,
en vez de declararlo verificado por un camino que no lo prueba.

### 6. No se requiere ADR nuevo

La decisión duradera que esta tarjeta podría haber necesitado —"una sola capa API centralizada"— ya
está tomada como decisión 4 del spike de migración y materializada desde JUP-095. Conectar `/me` es
una decisión acotada y reversible dentro de esa arquitectura, no un cambio de ella. Se citan ADR-0003
y ADR-0004 como marco vigente; no se propone ADR-0005.

## Risks / Trade-offs

- **La auditoría encuentra deriva que solo el backend puede corregir** → Se registra como finding y
  la corrección va en tarjeta de backend. Esta tarjeta no se bloquea por ello: su entregable es la
  auditoría, y un desajuste documentado es un resultado válido, no un fallo.
- **Conectar `/me` invade territorio de `reconcile-auth-tenant`** → Mitigado por la frontera explícita
  de la decisión 2: se toca el punto mínimo de `SessionGate` y se reutiliza su camino de fallo
  existente. Si al implementar resulta que no se puede conectar sin rediseñar la sesión, se para y se
  reconsidera con Victor antes de seguir, en vez de arrastrar el rediseño.
- **Una petición más en el arranque** → Es el coste aceptado de la decisión 2. Se emite junto al
  bootstrap de tenants que ya ocurría, no en serie después de él.
- **El mapa de carencias envejece** → Vive junto al código que describe (comentarios) y en un
  documento fechado con su tarjeta. Cuando una capacidad se construya, la tarjeta que la construya
  retira su fila; queda enunciado así en el propio documento.
- **Sin E2E en navegador, algo podría romperse solo allí** → Riesgo real y asumido, consecuencia de
  `RF-095-001`. Se declara en la revisión en vez de disimularse; es además el argumento de peso para
  priorizar la tarjeta de CORS.

## Migration Plan

No hay migración de datos ni despliegue por fases. El cambio es interno al frontend y reversible por
`git revert`: la capa de acceso conserva su forma actual y las correcciones son puntuales. El único
cambio observable para el usuario es que una sesión persistida con token muerto pasa a expulsar al
acceso en el arranque en vez de fallar más tarde en el bootstrap de tenants — comportamiento mejor,
pero que conviene mencionar en la revisión por si alguien lo lee como regresión.
