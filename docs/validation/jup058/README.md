# Evidencia de implementación JUP-058

Fecha: 2026-10-10. Tarjeta: https://trello.com/c/kU8swHK1.
Base: `c2995a118d419dfe725247bac9c6f219a3f0ea77` (`origin/develop`).
Esta evidencia es propia de implementación; no constituye las reviews
`Revision JUP-058` y `Validacion JUP-058` exigidas por CONTRIBUTING.

## Resultado por criterio de la tarjeta

| Criterio original | Evidencia y estado |
| --- | --- |
| Resultado funcional verificable | Panel en `/recommendations`: filtros combinados, orden, mensual/anual, detalle, evidencia y CSV. Demo explícita; consulta del cliente con contrato propuesto JUP-033 y estados carga/error/reintento/vacío. Ver capturas y pruebas. Backend desplegado no comprobado. |
| Pruebas necesarias añadidas y en verde | 16 pruebas focales superadas; contratos Python 9/9; typecheck y lint correctos. Resultado de suite completa registrado abajo. |
| Documentación y decisiones actualizadas | OpenSpec `jup-058-recommendations-panel`, [arquitectura](../../architecture/recommendations-panel.md), README frontend, mapa JUP-097 y [continuidad](../../continuidad/panel-recomendaciones.md). |
| Pull request revisado y vinculado | PR de entrega preparada para `develop`; revisión humana pendiente. La evaluación interna asistida no cubre este criterio. |
| Validación funcional y evidencia enlazadas | Interacciones comprobadas con Chromium y dobles HTTP; [contraste Python](contract-check.json) reproducible. Validación formal independiente pendiente; Alejandro sigue asignado en Trello, pero no puede validar esta contribución preparada desde su cuenta. No se declara aceptado el criterio global. |

## Pruebas y comandos

Desde la raíz de la copia:

```powershell
corepack pnpm install --frozen-lockfile
corepack pnpm --filter @finops/frontend typecheck
corepack pnpm --filter @finops/frontend lint
corepack pnpm --filter @finops/frontend exec vitest run --maxWorkers=1 --no-file-parallelism --testTimeout=60000
corepack pnpm --filter @finops/frontend build
node --test tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/repository-governance.test.mjs
node tools/jup-check.mjs --all
node tools/jup-cleanup-check.mjs
corepack pnpm openspec:validate
```

- Typecheck: correcto en código, configuración Node y tests.
- Lint: correcto tras corregir una expresión con caracteres de control en CSV.
- Suite frontend completa: **644/644 pruebas, 55/55 archivos**, 519,30 s,
  con un worker y timeout CLI de 60 s; incluye las 16 focales del panel.
- Pruebas nuevas: modelo 5, componente 6, cliente HTTP 5. Comprueban filtros,
  orden preciso con valores mayores que `MAX_SAFE_INTEGER`, desconocido/cero,
  monedas, CSV, evidencia, estados HTTP, mes y cambio de tenant con respuesta tardía.
- Build frontend: correcto; aviso de bundle compartido mayor de 500 kB.
- Gobernanza: 82/82. OpenSpec: 56/56 antes y después del archivo técnico del cambio.
- La primera ejecución de algunas pruebas excedió 5 s por saturación del host;
  se repitieron con un worker y timeout CLI de 60 s. No se cambió la configuración
  de tiempos del repositorio ni se ocultaron aserciones fallidas.
- `corepack pnpm build` (Turbo global) falló inicialmente por
  `ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY`: sus subprocesos eligieron el shim
  pnpm del runtime en lugar de pnpm 9. Se repitió con un shim temporal que llama
  a Corepack/pnpm 9 en el PATH de ese único proceso: **4/4 tareas correctas**.
  No se cambió configuración global ni del repositorio. Turbo advierte de que
  los builds Python no generan los outputs dist/build declarados; los comandos
  compileall sí terminaron correctamente.

Entorno: Node 24.14.1, pnpm 9.0.0, TypeScript 5.9.3, Vite 5.4.21,
Python 3.14.4, Pydantic 2.12.5. Dependencias instaladas con lockfile congelado.

## Compatibilidad con dependencias

```powershell
python docs/validation/jup058/check-contracts.py --frontend . --jup033 ../tfm-economicon-jup033 --jup034 ../tfm-economicon-jup034
```

El script importa en modo lectura los esquemas y el evaluador reales de las
copias indicadas, sin crear bytecode ni escribir en ellas. Tras integrar ambas
dependencias se pueden pasar las tres rutas como `.`. Requiere Node, TypeScript
instalado en el frontend y Pydantic 2 en Python.

[Resultado 9/9](contract-check.json): los dos dobles se validan y conservan su
serialización, se rechazan evidencia rota/aprobación falsa/costes desparejados,
y los importes, inclusiones y exclusiones coinciden con JUP-034. Detectó y
corrigió inicialmente la exclusión errónea de un escenario de ahorro cero.
Los hashes de esquemas/servicio/fixtures identifican las versiones exactas
contrastadas; no se afirma que estén integradas o desplegadas.
Después se observaron publicadas como PR [#97 (JUP-033)](https://github.com/EconomiconFinOps/tfm-economicon/pull/97)
y [#96 (JUP-034)](https://github.com/EconomiconFinOps/tfm-economicon/pull/96),
con las mismas fuentes de contrato comprobadas; siguen siendo dependencias pendientes de integración.

## Navegador y capturas

Chromium sobre el frontend real: sesiones, perfil y tenants sintéticos,
con respuestas HTTP interceptadas. Evaluación independiente asistida PASS en
1440/768/375 px, filtros combinados, vacío, reset, orden, detalle mediante Enter
y estado HTTP 503. Sin errores JavaScript. No hay otro proveedor de modelos
disponible: fue un agente independiente del mismo proveedor, no una revisión humana.

El build compilado también se comprobó en `http://127.0.0.1:5859/recommendations`:
cinco filas demo sin consulta al endpoint, descarga CSV real de una sola fila
filtrada conservando `0.00`, periodo y condiciones, exportación deshabilitada
con cero filas, solicitud con cabecera tenant y reintento 503 sin fallback demo.

- [Escritorio](desktop.png)
- [Móvil](mobile.png)
- [Resultado automatizado sobre build](browser-smoke.json)
- [Error de cliente explícito](client-error.png)

El panel cabe en el ancho móvil y su detalle abierto no desborda. **La navegación
global heredada sigue ampliando el documento a 1134 px** en viewport 375/390;
el shell no cambia en esta tarjeta (limitación ya registrada como RF-026-002).
La captura completa la muestra sin recortarla para aparentar un resultado global correcto.
Se mejoró el contraste del selector de mes con `color-scheme: dark`, local al input.

## Pendientes y límites

- Integrar versiones definitivas JUP-033/034 y repetir contrato/HTTP con backend
  autenticado y datos del despliegue. No se ha probado Azure real, persistencia
  de informes, generación de recomendaciones ni aplicación de mejoras.
- El ahorro de la demo es un escenario hipotético; el modo cliente v1 muestra
  ahorro no estimado. No se suman alternativas, no hay conversión de moneda,
  cálculo de anualización en UI ni afirmación de ahorro conseguido.
- CSV comprobado como descarga y contenido; no abierto en Excel/LibreOffice.
  No se ofrece PDF mediante el interpolador HTML compartido.
- Pairing real, revisión de Víctor, validación independiente y aceptación de
  Lucía pendientes. Los roles proceden de Trello; no son acciones acreditadas.
  La cuenta publicadora `Iber1to` y el autor Git configurado corresponden a
  Alejandro, asignado a validación. Se entrega una **contribución en rama propia
  para Lucía**, no un dictamen ni una reasignación de liderazgo. Esta cuenta no
  puede validar su propio cambio; el liderazgo debe resolver autoría/roles antes
  de solicitar la aceptación formal, manteniendo la independencia exigida.

Logs y script de navegador de la sesión conservados en el workspace:
`materiales/07-evidencias/JUP-058-implementacion-2026-10-10/`. Los resultados
esenciales, hashes, comprobador de contratos y capturas se versionan aquí.
