# Revision tecnica JUP-087

- Fecha: 2026-09-08.
- Base revisada: `origin/develop` en `ae538aadbf8012c144d540644691a9d80a5a4508`.
- Evidencia: [validacion JUP-087](../../../../docs/evidence/JUP-087-validation.md).

## Contratos y regresion

Se contrastaron los contratos TypeScript con los schemas de auth, tenant,
billing, health, jobs y assistant del backend. El acceso HTTP conserva los
endpoints y cabeceras de autenticacion/tenant. Los metadatos abiertos se tipan
como `unknown`; no se añaden supresiones para forzar el compilador a aceptar
contratos incompletos.

Se revisaron el aislamiento de las pruebas, la regla JSX para contratos de
props y el encadenamiento de lint y pruebas dentro de `Frontend build`.
La revision identifico un fallo heredado de estado al cambiar de tenant,
cubierto ahora mediante remonte de las paginas y regresiones de respuestas
tardias. La evidencia de validacion describe el resto de correcciones y limites.

## Participacion pendiente al 08/09

Trello asigna liderazgo a Victor Mendez, pairing a Alejandro Aguado,
revision de PR a Lucia Mateo y validacion/pruebas/documentacion a Paris
Arcos Martin. Este informe registra una revision automatizada; no sustituye
la aprobacion humana ni acredita participacion de esas personas. El change
permanece activo hasta completar la revision y el cierre operativo.

## Cierre acotado y participacion — 2026-09-14

Lucia aprobo la PR #29 el 12/09 sobre `746fd5d` y la fusiono en `develop`
mediante `1de7b16`. La evidencia enlaza la revision y el CI correspondientes.
El usuario autoriza ahora ejecutar la validacion operativa en esta tarea para
cerrar el baseline, conservando el rol y la auditoria de Paris. La ejecucion
es automatizada bajo esa autorizacion, no una validacion personal de Paris;
no se acredita pairing ni se cambian los cuatro roles previstos.

Se revalidan lint, 28 pruebas frontend, tipos, build y herramientas sobre
`cfc6668`. El ensayo Chromium con servicios reales confirma login, tenants,
dashboard, ingesta hasta persistencia y manejo de errores. Un proxy de prueba
permite continuar tras detectar el preflight 405; el historial real devuelve
500 por metadata JSONB ya deserializada. RF-087-001/JUP-085 y
RF-087-002/JUP-035 permanecen abiertos y limitan el resultado integrado.
Providers de embedding/asistente y cifras de billing siguen siendo mock.

El archivo acredita exclusivamente los requisitos de calidad frontend.
La auditoria personal de Paris sigue pendiente por la excepcion operativa
expresa del usuario; no sustituye la aprobacion propia de la PR documental.
