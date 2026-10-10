# JUP-037 — Verificación final con excepción de plazo MVP

10/10/2026, Europe/Paris. Responsable: Alejandro (`Iber1to`), con asistencia
de Codex. No revisión o validación independiente de Paris/Victor ni pairing Lucia.
[Autorización y atribución](../contributions/JUP-037-mvp-exception.md).

Base de pruebas: PR100 `7f63a1418fa1e573ca68f3cfeec7854c9a71b99f`, develop
`c2995a118d419dfe725247bac9c6f219a3f0ea77`; después corrección de selección del
nuevo hilo, ajuste de línea del texto y regresión frontend. No cambios backend.

## Revisión técnica asistida

**Verdict: APPROVE técnico para el alcance descrito**, confianza alta tras las
comprobaciones dirigidas; no equivale a aprobación GitHub o revisión independiente.
Se revisaron schema, autorización, agregación/procedencia, servicio, persistencia,
formulario, presentación y sus llamadas. Sin P0/P1 pendiente en el incremento.

| Hallazgo | Resultado |
| --- | --- |
| Carrera al crear hilo con conversaciones existentes: el efecto veía el listado anterior y volvía a seleccionar un hilo previo | Corregido: esperar al refresco de la colección antes de seleccionar el nuevo ID; regresión con respuesta diferida y verificación del destino de POST |
| Identificador financiero largo en texto móvil | Ajuste de línea `break-words`; evidencia estructurada ya conservaba el identificador completo |
| Desbordamiento móvil del Layout/nav compartido | RF-026-002 existente, fuera de JUP-037; observado 390/1134 px, no declarar pase visual global ni corregirlo aquí |

## Pruebas ejecutadas en este cierre

- Backend Python **3.14.4**: **209 passed / 0 failed / 0 skipped**, 109.49 s,
  coste/procedencia, billing, presupuestos, citas y retrieval. CockroachDB v24.1.2
  real en contenedor exclusivo `economicon-jup037-mvp-final`, sin volumen, puerto
  loopback remoto/local 56637, organización `processor-integration-tests`.
  El fixture verifica clúster vacío y crea/elimina su base UUID. Advertencias
  de deprecación Python/FastAPI/SQLite no se confunden con fallos.
- Frontend: **35 passed** en cinco archivos, incluida nueva regresión de hilo,
  contra HTTP simulado. Misma configuración temporal documentada en evidencia
  original (DOM 10 s, runner/hook 30 s, un worker), sin debilitar aserciones.
  Después de hacer diferida la respuesta del nuevo test: **1 passed**, diez casos
  fuera del selector; no son omisiones de integración. Componentes tras ajuste
  de línea: **11 passed**. No sumar estos pases repetidos como casos distintos.
- OpenSpec **56/56**, trazabilidad de ocho cambios activos, higiene PASS (990
  archivos antes de añadir este registro), gobernanza **82/82**.
- Lint de archivos frontend cambiados y tres configuraciones TypeScript PASS.
  Build PASS, conserva advertencia de chunk >500 kB.
- Fallo inicial de higiene/gobernanza por `spawn EPERM` dentro del sandbox:
  repetido en entorno autorizado, todo PASS; no fallo de producto.

## Navegador contra HTTP y SQL reales

Playwright/Chromium, frontend local 5187, proxy de pruebas hacia HTTP local 58737.
Harness monta rutas reales auth/tenants/assistant/billing y Database real sobre
base efímera propia. Datos sintéticos de fixtures; servicios modelo/vector/broker
no utilizados. No es el lifespan de Compose completo ni un despliegue.

Comprobaciones finales:

1. Login y creación de conversación; selección explícita application=Portal,
   EUR, junio `[2024-06-01,2024-07-01)`.
2. Cargo 100 y ajuste -20 => selección **80 EUR**, contexto **130 EUR**, sin
   dimensión **10 EUR**; ingesta de tenant ajeno no aparece en procedencia.
3. Recarga conserva respuesta, ID financiero reproducible, desglose y procedencia.
4. Cambio tenant-a → tenant-b borra formulario/draft y no muestra mensaje anterior.
5. Cero errores de página; capturas escritorio 1440 y móvil 390. Mobile mantiene
   el finding global mencionado; no afirmar responsive global PASS.

El primer pase antes de correcciones funcionó con base vacía. Al repetir con
conversaciones existentes se reprodujo la carrera; el harness inicial falló por
teardown/selector duplicado. Se añadieron esperas HTTP explícitas y cierre ordenado
de rutas, se corrigió el producto y la repetición final pasó. Los intentos fallidos
no se cuentan como validación favorable.

[Resultado reproducible](JUP-037-mvp/browser-results.json),
[escritorio](JUP-037-mvp/desktop-real-sql.png),
[móvil y límite global](JUP-037-mvp/mobile-real-sql.png).
Scripts temporales conservados fuera de Git en el workspace:
`../tmp/jup037-mvp-browser-backend.py` y `%TEMP%/playwright-test-jup037-mvp.cjs`.
El harness usa `tenant_cockroach_database`, `billing_schema`, `populated_database`
y las rutas reales; no lee tokens/credenciales de despliegue.

## Aceptación y límites del incremento

| Criterio | Resultado de cierre |
| --- | --- |
| Resultado funcional verificable | PASS para selección estructurada, costes firmados por moneda, SQL y persistencia |
| Pruebas necesarias en verde | PASS según baterías anteriores y CI final por SHA al publicar |
| Documentación y decisiones | OpenSpec archivado y spec promovida, contrato, evidencia y excepción versionados |
| PR revisada y vinculada | PR100, revisión técnica asistida; review independiente exceptuada explícitamente por usuario |
| Validación/evidencia enlazadas | Pruebas propias de cierre y navegador/SQL; dictamen Victor exceptuado, no atribuido |

Se conserva: application/owner sintéticos, sin capacidad desplegada acreditada;
sin NL libre, catálogo corporativo ni combinación PR69; sin broker/vector/modelo,
Compose completo, promoción main, despliegue o gasto. Excepción de participación
puntual por plazo, no cambio de las reglas del repositorio. Integración y cierre
se registrarán por sus fuentes después de ejecutarse.
