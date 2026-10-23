# JUP-065 — Integración de la demo congelada con incidencias

Fecha documental: 23/10/2026. [Trello JUP-065](https://trello.com/c/SZUFo4ol).

## Decisión y alcance

El usuario autoriza expresamente: «Haz la pr y mergea como excepcion con aprobacion mia».
La excepción permite publicar e integrar los cambios existentes de la demo en
`develop`, sin nuevas rondas de ajustes ni ensayos. No acredita revisiones humanas
del equipo ni sustituye el dictamen de aceptación integral: **RC NO ACEPTADA**.
La entrega permanece clasificada como **demo con incidencias**.

Origen: chat «Levantar Jupiter en dockerDevelop»,
`01a16421-03a0-7460-b110-24738407ccb1`. La implementación y la preparación de esta
integración se han realizado con asistencia automatizada bajo autorización del
usuario; no se atribuyen pairing ni dictámenes de PR a otros miembros del equipo.
Quality User fue un agente de IA autorizado para el ensayo previo, no un revisor
humano de esta PR. La aprobación excepcional de integración es distinta de su
dictamen funcional desfavorable.

## Cambios incorporados

Base: `03e97ce670286bb55d2750be7bb466deb24548c6`, coincidente con `develop` al preparar
la rama `fix/JUP-065-frozen-demo-final10000`.

- Borrador privado conciso: objetivo de 600 tokens, con límite duro de 1.000.
- Respuesta final con límite de 10.000 tokens y reserva interna conjunta de 11.000,
  coherentes en backend, processor y contratos/manifiestos v3 y v4.
- Instrucciones ya ensayadas sobre investigación ante falta de datos, condiciones
  comerciales no documentadas, precisión y concisión. No garantizan cumplimiento.
- Lectura restringida de dos rutas de registro de LibreOffice resueltas fuera de
  `/usr`, conservando su acceso de solo lectura en el sandbox de extracción.
- Adaptaciones existentes de expectativas y contextos de pruebas al nuevo límite;
  la fixture del planificador conserva explícitamente su presión sintética anterior.

Los 26 archivos de código/pruebas coinciden con las fuentes congeladas del ensayo.
Sus huellas están en el [recibo de procedencia](JUP-065-frozen-demo-20261023.json).
El cambio de formato del manifiesto v3 a JSON compacto forma parte de esa fuente;
no representa eliminación de su contrato.

Las dependencias adicionales y el aislamiento usados por el arnés de pruebas
anterior eran ajustes del entorno de ensayo. Esta PR no añade imágenes de pruebas,
credenciales, configuración privada, datos sintéticos del despliegue ni dashboards
operativos. Tampoco cambia modelos, cuotas, autenticación, políticas o workflows.

## Evidencia anterior y límites

Ejecución previa del 23/10, cerrada a las 12:15:57 UTC:
`jup065-final10000-integral-20261023`. No se repite para esta integración.

| Área | Resultado observado |
| --- | --- |
| Backend | 2.732 PASS / 369 omitidas |
| Processor | 2.674 PASS / 150 omitidas |
| Azure cost API local | 81 PASS |
| Frontend | 1.427 PASS; lint sin errores y un aviso; tres comprobaciones TypeScript y build conformes |
| SQL aislado / UI Quality User | 36 PASS / 7 PASS |
| Cinco casos generativos | 4/5 rúbricas específicas; aceptación integral NO ACEPTADA |
| Checklist | 27 PASS, 2 FAIL y 1 NO EVALUADO |

Las 519 omisiones de backend/processor conservan sus límites; no certifican
integraciones externas. El arnés utilizó imágenes de pruebas existentes, ejecución
aislada y `pytest --forked`; no equivale a una ejecución nueva de CI sobre esta PR.
El recibo diferencia esa evidencia histórica de la comprobación actual de identidad
de archivos. No se hacen nuevas llamadas al proveedor ni pruebas de la demo.

| Incidencia vigente | Observación de la última batería |
| --- | --- |
| 003 | Solicita datos pero omite proponer investigación por servicio y recurso; FAIL de rúbrica. |
| 004 | Distinción conceptual correcta; afirmación global sobre el corpus sin soporte en los fragmentos recuperados. |
| 025 | Rechazo correcto tras tres intentos y 120,955 s; antes hubo truncado final a 10.000 tokens y EOF. No está corregida su estabilidad. |

No se compararon dos baterías completas de la misma configuración. La ejecución
independiente de Quality User no convierte ese criterio en evaluado.
Las llamadas al modelo fueron reales sobre datos de negocio simulados;
no hay un tenant real de Azure acreditado por este ensayo.

Paquete original conservado en el workspace de entrega:
`materiales/07-evidencias/cierre-integral-rc-20261023/JUP-065-cierre-integral-final10000-20261023.zip`.
SHA256: `c9e9d6cd6fc7682389f0d959d472f2a7af3dbd4a97f18633c757950ffe3b317b`.
No se publica el paquete bruto en esta PR; el resumen y la procedencia sí quedan
versionados. El archivo local no es un enlace público de evidencia accesible al equipo.

## Operación y seguimiento

DockerDevelop conserva la versión desplegada, los accesos actuales y sus sesiones
de dos horas, Grafana Viewer y el presupuesto autorizado de 10 USD sin reinicio.
Los servicios no se reconstruyen ni se despliegan por este encargo. El flujo CD
existente de `develop` puede evaluar/promover su entorno independiente de DockerServer;
su resultado no acredita un cambio ni validación de la demo congelada.

La tarjeta JUP-065 conserva la aceptación integral pendiente. El merge excepcional
no cierra esas incidencias ni cambia su estado a Hecho. Una corrección o nueva
campaña requiere un encargo posterior. No se modifican los controles del repositorio
para simular revisiones; cualquier omisión se declara en la PR y en el registro de merge.
