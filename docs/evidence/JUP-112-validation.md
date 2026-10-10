# Evidencia de implementación — JUP-112

Fecha: 2026-10-10, Europe/Paris. [Tarjeta](https://trello.com/c/XTZU3vj3).
Base `c2995a1`, rama `feat/JUP-112-brand`. Este informe recoge comprobaciones del
candidato técnico, no una `Validacion JUP-112` humana ni aceptación de marca.

## Entrega

Paleta clara semántica de Economicon, logotipos originales del dossier, Inter y
Space Grotesk servidas localmente, acciones con contraste, foco y enlace para
saltar al contenido. Cabecera y páginas conservan sus rutas/datos; tablas anchas
tienen scroll interno y títulos/controles se adaptan a tamaños estrechos.
[Procedencia y contrato compartido](../frontend-brand.md).

## Criterios de tarjeta

| Criterio | Evidencia y estado |
| --- | --- |
| Resultado funcional verificable | Implementación frontend, build correcto y capturas con API simulada. Sin cambios en routes, hooks, services o datasets. |
| Pruebas necesarias añadidas y en verde | Nuevas pruebas de contraste/BrandMark/foco y guardianes adaptados. Suite completa y repetición acotada en curso; no se declara verde todavía. |
| Documentación y decisiones actualizadas | OpenSpec estricto 56/56, contrato de marca, ADR-0012 con evolución propuesta, README y ATTRIBUTIONS; aceptación humana del rediseño pendiente. |
| PR revisada y vinculada | Candidato draft para Paris; revisión humana Alejandro y pairing Victor pendientes, sin atribución inferida. |
| Validación funcional y evidencia enlazadas | Navegador real con mocks y evidencia propia; validación independiente Lucia/backend real pendiente. |

## Ejecución local

- Node 24.14.1, pnpm 9.0.0 por Corepack, Vite 5.4.21, Vitest 3.2.7.
- Fuentes `@fontsource-variable/inter` y `space-grotesk` 5.3.0, OFL1.1;
  avisos distribuidos también en `public/licenses/` y verificados en `dist/licenses/`.
- `corepack pnpm --filter @finops/frontend typecheck`: PASS (tres configuraciones).
- `corepack pnpm --filter @finops/frontend lint`: PASS.
- `corepack pnpm --filter @finops/frontend build`: PASS, 2486 módulos;
  JS 780.80 kB, gzip225.15 kB. Aviso de chunk mayor de500kB; no impide build.
- `corepack pnpm openspec:validate`: PASS56/56 tras conservar escenarios
  existentes en el delta MODIFIED. El intento inicial detectó su omisión y se corrigió.
- `corepack pnpm jup:check:all`: PASS.
- `node --test tools/pr-policy.test.mjs tools/ci-workflow.test.mjs tools/repository-governance.test.mjs`:
  PASS82. Primer intento sandbox falló `spawn EPERM`; repetición autorizada PASS.
- Higiene: PASS986 archivos al ejecutar con subprocess permitido; primer intento
  sandbox `spawnSync git EPERM`, sin hallazgo de repositorio.
- Suite frontend completa serial: en curso. Primeras incidencias registradas:
  tres timeouts JUP055 a5s y60 fallos en cascada JUP047/`act()`;139 pruebas de
  sesión y120 de paleta pasan. No se han modificado timeouts del repositorio.

Los controles globales vía Turbo no concluyen correctamente en este entorno:
resuelven `pnpm` al fallback11 del runtime en lugar del Corepack9 del proyecto,
intentan auto-instalar y fallan (incluido exit3221226505). Se conserva la salida;
no se corrige el lanzador global dentro de esta tarjeta. No acredita pruebas
backend/processor ni integración real. Las pruebas propias usan Corepack directo.

## Navegador y reproducción

Servidor dedicado: `corepack pnpm --filter @finops/frontend dev --host 127.0.0.1
--port 5112 --strictPort`. La revisión usa Chromium real, respuestas API simuladas
y red externa bloqueada; no usa credenciales, Azure, modelos ni inferencia real.

1. Abrir login y las nueve rutas del menú con usuario/tenant sintéticos.
2. Repetir a1440/390px y comprobar login/coste/salud/recomendaciones a320/768px.
3. Comprobar carga/error/vacío, tabulación, salto al contenido, scroll interno de
   tablas y etiquetas/tooltips. Preferencia de sistema oscura debe conservar tema claro.
4. Verificar Inter/Space Grotesk cargadas desde el propio origen, texto normal
   ≥4.5:1 y foco/campos ≥3:1. El detector de navegador excluye opacidades,
   gradientes y SVG de sus conclusiones automáticas; se inspeccionan visualmente.

En el workspace de coordinación se conservan logs y PNG en
`materiales/07-evidencias/JUP-112-brand-2026-10-10/` (`visual/main`, `visual/smoke`).
Primer smoke con import `latin.css` inválido fue corregido usando entrypoints
de los paquetes. Las capturas fallidas permanecen separadas de las nuevas.
La revisión detectó y corrigió compresión de números en tablas y recorte de
etiquetas del gráfico de recomendaciones; se recaptura después de cada arreglo.

## Pendiente

Finalizar matriz y pruebas, fijar resumen sobre el head entregado y enlazar PR.
Pairing Victor, `Revision JUP-112` Alejandro, `Validacion JUP-112` Lucia,
aceptación visual de Paris/equipo, integración y cierre Trello siguen pendientes.
La revisión automatizada de agentes no sustituye ninguno de esos actos.
