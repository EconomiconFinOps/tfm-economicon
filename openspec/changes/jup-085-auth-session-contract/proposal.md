JUP: JUP-085
Trello: https://trello.com/c/Z8M443Hu

## Why

Economicon ya dispone de login, perfil autenticado, JWT propio y persistencia de
sesion en el frontend, pero ese comportamiento heredado no tiene un contrato
completo. Sin requisitos versionados no se pueden distinguir la autenticacion
demo aceptada, los secretos de runtime y los escenarios de expiracion o logout.

## What Changes

- Definir los contratos HTTP de `POST /auth/login` y `GET /me`.
- Fijar el contenido minimo del token, su TTL configurable y los errores de
  credenciales, bearer ausente, token invalido, token expirado y usuario ausente.
- Definir la persistencia y limpieza de la sesion demo en el frontend.
- Separar credenciales sembradas de desarrollo, secreto de firma y cualquier
  configuracion destinada a un despliegue no local.
- Mantener un IdP externo fuera del MVP.

## Capabilities

### New Capabilities

- `demo-auth-session`: contrato verificable del ciclo de autenticacion y sesion
  propia utilizado exclusivamente por la demo del MVP.

### Modified Capabilities

- None. La coherencia de credenciales demo ya promovida sigue vigente y este
  cambio amplía el contrato hacia el ciclo completo de sesion.

## Impact

- Afecta a las rutas de auth, seguridad JWT, configuracion, seed local,
  almacenamiento frontend y pruebas backend/frontend.
- No introduce OAuth/OIDC, refresh tokens, revocacion remota ni un IdP externo.
- JUP-086 consume la identidad autenticada para resolver autorizacion por tenant.
