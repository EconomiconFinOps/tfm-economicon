JUP: JUP-085
ADR: no aplicable; formaliza el mecanismo demo existente sin convertirlo en la identidad objetivo de produccion.

## Context

El backend firma JWT propios con `AUTH_SECRET_KEY` y TTL configurable. Login
devuelve token bearer y perfil; `/me` vuelve a resolver el usuario desde el
`sub`. El frontend guarda `accessToken` y perfil en `finops.session`, y el tenant
activo por separado en `finops.activeTenant`. El logout actual es local.

## Goals / Non-Goals

**Goals:**

- Hacer explicitos request, response, claims, TTL y errores de login/perfil.
- Definir restauracion, expiracion y limpieza completa de sesion en el frontend.
- Impedir que secretos de firma o credenciales no demo se empaqueten en el cliente.
- Permitir pruebas positivas y negativas reproducibles.

**Non-Goals:**

- Integrar un IdP externo, refresh tokens, MFA o revocacion distribuida.
- Declarar la autenticacion propia adecuada para produccion publica.
- Implementar autorizacion por tenant, que pertenece a JUP-086.

## Decisions

### Contrato HTTP demo estable

`POST /auth/login` acepta email valido y password no vacio. En exito devuelve
`access_token`, `token_type: bearer` y un perfil con `id`, `email`, `full_name` y
`role`. Credenciales no validas devuelven `401` sin revelar si el email existe.

`GET /me` exige exactamente un bearer utilizable. Bearer ausente o mal formado,
firma invalida, expiracion y usuario ya inexistente devuelven `401` sin datos del
token ni del usuario.

### Token de acceso acotado

El JWT contiene al menos `sub`, `iat` y `exp`; el TTL procede de
`AUTH_TOKEN_TTL_MINUTES`. `AUTH_SECRET_KEY` se inyecta en runtime y no se expone
mediante variables `VITE_*`, respuestas HTTP, logs o artefactos versionados.

### Logout local y expiracion coherente

Mientras no exista revocacion remota, logout elimina `finops.session`,
`finops.activeTenant` y la cache de consultas. Una respuesta `401` al restaurar
o utilizar una sesion expirada debe producir la misma limpieza y volver al login.

## Risks / Trade-offs

- [JWT robado sigue valido hasta `exp`] -> TTL acotado, secreto fuera del cliente
  y documentacion explicita de que es auth de demo.
- [Estado local corrupto] -> parseo defensivo y limpieza antes de mostrar la app.
- [Mensajes filtran existencia de usuarios] -> respuesta generica para login.
- [Frontend conserva tenant tras logout] -> limpieza atomica de sesion, tenant y cache.
