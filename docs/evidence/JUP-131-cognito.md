# JUP-131 — adaptación Cognito, verificación local

21/10/2026. El usuario autoriza adaptar la aplicación; no se llama a AWS ni se
crean identidades reales. Esta evidencia describe el código y pruebas locales,
sin acreditar un login contra el pool AWS ni disponibilidad de DNS/TLS.

## Contrato

Backend: `AUTH_PROVIDER=cognito`, `COGNITO_ISSUER` exacto del pool y
`COGNITO_CLIENT_ID` del cliente público. En ese modo no se requiere la clave
local y `/auth/login` rechaza contraseñas con403 antes de consultar al usuario.
La configuración local anterior se conserva como default y sigue exigiendo su
clave. El seed de contraseña local está prohibido en modo Cognito.

Se valida firma RS256 mediante JWKS del issuer fijado (sin URL aportada por el
token), tiempos enteros, issuer, client_id, token_use=access y sub no vacío.
No se aceptan ID tokens para la API. El sub debe existir como `users.id`;
bootstrap creará explícitamente esa fila y sus membresías. No se vincula por
correo ni se admiten permisos de tenant desde claims. `/me` y el resto de rutas
mantienen autorización local. Fallos de firma, claims o claves se deniegan sin
incluir tokens ni errores remotos en la respuesta.

Frontend: `VITE_AUTH_PROVIDER=cognito`, `VITE_COGNITO_DOMAIN` del dominio
administrado y `VITE_COGNITO_CLIENT_ID`, todos públicos. Authorization code/PKCE
S256, state y verifier aleatorios de32bytes, almacenamiento transitorio por
pestaña, ventana10min, callback exacto `/auth/callback`, rechazo de duplicados y
consumo único. El callback retira el código del historial, intercambia sin
credenciales de cliente, consulta `/me` y conserva únicamente la sesión de
acceso verificada. No guarda ID token ni refresh token. La generación de sesión
impide que una respuesta tardía reabra una sesión abandonada. Un intercambio
en curso puede compartirse durante el doble efecto de StrictMode; un replay
posterior falla.

Las sesiones Cognito tienen caducidad explícita: se descartan antes de enviar
peticiones si ya vencieron y se invalidan cuando vencen abiertas. El logout
manual limpia sesión/datos y dirige al endpoint `/logout` del mismo cliente;
el rechazo de la API conserva el flujo de invalidación existente.

## Pruebas observadas

- Backend31PASS: firmas RSA reales, falsificación, algoritmo HMAC rechazado
  antes de consultar claves, JWKS con clave rotada y jku ignorado, issuer/client
  erróneos, ID token, tiempos/claims inválidos o ausentes, fallo de claves,
  configuración, login local desactivado e identidad local existente/ausente.
- Frontend: pruebas PKCE, callback, fallos, replay, expiración y respuesta de
  tokens inválida; batería completa95archivos/1397pruebasPASS.
- Tipado completo PASS; linter0errores/1aviso previo en ChatPresentation.tsx,
  archivo no modificado. Política Docker38PASS. OpenSpec JUP-131 estricto PASS.
- Regresión de autenticación/tenant/configuración en entorno Python aislado:
  173PASS; cuatro controles SQL de resumen pasan en repetición con tokenizer
  fijado. Ver [evidencia PostgreSQL](JUP-131-postgresql.md).

Logs ignorados en `.work/aws-application/{cognito-final,frontend-all,
frontend-typecheck-final,frontend-lint,auth-native,summary-native}.log`.
No se atribuyen estos resultados a revisión/validación humana oficial.

Fuentes de protocolo: [verificación JWT de Cognito](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html)
y [access tokens](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html).

Pendientes para ensayo: conectar outputs/receta, crear usuario y membresías por
bootstrap, comprobar login/logout reales y aislamiento contra el entorno AWS
autorizado. No se ha aceptado la aplicación AWS como desplegable.
