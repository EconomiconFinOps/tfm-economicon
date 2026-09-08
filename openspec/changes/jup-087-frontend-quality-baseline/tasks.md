## 1. Baseline y contrato

- [x] 1.1 JUP-087 registrar los 49 errores heredados, nueve archivos y ausencia de tests reales.
- [x] 1.2 JUP-087 definir la matriz minima de recorridos positivos y de error.
- [x] 1.3 JUP-087 enlazar RF-082-002 con este cambio y RF-083-002 con su residual funcional.

## 2. Implementacion

- [x] 2.1 JUP-087 resolver contratos de props sin desactivar globalmente la regla.
- [x] 2.2 JUP-087 configurar runner, entorno DOM, utilidades y script frontend de pruebas.
- [x] 2.3 JUP-087 cubrir login/sesion, tenant, dashboard, ingesta y conversacion.

## 3. Verificacion

- [x] 3.1 JUP-087 demostrar `pnpm lint` sin errores y `pnpm test` con pruebas frontend reales.
- [x] 3.2 JUP-087 ejecutar build, OpenSpec, trazabilidad y checks de CI.
- [x] 3.3 JUP-087 publicar PR y evidencia de regresion.

Evidencia: [validacion JUP-087](../../../docs/evidence/JUP-087-validation.md),
[PR #29](https://github.com/EconomiconFinOps/tfm-economicon/pull/29).
La implementacion y la verificacion automatizada estan completas; la revision
humana, la validacion atribuible y el cierre operativo siguen pendientes.
