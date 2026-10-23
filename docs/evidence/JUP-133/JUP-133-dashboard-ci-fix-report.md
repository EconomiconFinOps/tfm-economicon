# JUP-133 — Corrección de la suite del dashboard tras PR156

Verificación: 23/10/2026. Base `develop` `db8f69ab5e2d4a42931cd6dc7412b99e855f0148`.
Rama `fix/JUP-133-dashboard-ci`. Autorización: «Adelante con el siguiente paso»,
para corregir los bloqueos diagnosticados y comprobar la integración.

## Cambio y causa

Las seis repeticiones añadidas por PR156 elevaron el manifiesto a 18 ejecuciones
y 1670 resultados. Las pruebas seguían suponiendo 12/647 y algunas insertaban
una campaña de octubre como «última», aunque las nuevas eran posteriores.
El [diagnóstico previo](JUP-133-develop-ci-report.md) conserva el fallo de CI:
110 fallos y 30 errores; no eran defectos independientes del modelo.

- Las pruebas de manifiesto, normalización, SQL, carga, permisos, atomicidad y
  vistas comprueban el conjunto actual, sus seis ejecuciones sin hito y dos
  series de tres repeticiones. Se mantienen los rechazos, ACL, concurrencia y
  rollback. Los montajes comprueban ahora también el número exacto de resultados.
- Los escenarios históricos de consulta y legibilidad usan un manifiesto
  explícito de doce informes, `scripts/tests/fixtures/evaluation-before-infra.json`.
  Sólo referencia las fuentes existentes. El manifiesto de producto no cambia.
- Ocho pruebas nuevas concilian las seis fuentes rows-v1 con PostgreSQL real,
  incluyendo nulos, juicios y clasificación provisional. Ejecutan los 18 targets
  SQL de paneles y la anotación con el rol de lectura y el manifiesto completo;
  contrastan metadatos/casos, las 1076 filas de robustez y la selección de la
  repetición JUP-071 r3 con sus 19 indicadores. No sustituyen juicios humanos.
- La matriz completa tiene 55 filas. Su altura pasa de 52 a 61 unidades y los
  paneles inferiores se desplazan nueve, sin solapes. Antes de corregirla, la
  prueba con el manifiesto completo fallaba explícitamente por necesitar 61.
- El inventario vincula los seis informes nuevos a las categorías dependientes
  del modelo ya existentes; no cambia su estado ni sus valores.

## Validación ejecutada

| Comprobación | Resultado |
| --- | --- |
| `python3 -m unittest discover -s scripts/tests -p 'test_evaluation_*.py' -v` | **1998 pruebas PASS, 0 fallos, 0 errores, 0 omitidas; 111.227 s** |
| `corepack pnpm openspec:validate` | 92 elementos PASS, modo estricto |
| `corepack pnpm ci:check:test` | 19 PASS |
| `corepack pnpm cd:test` | 3 pruebas Node PASS; Python 60 PASS / 3 omitidas por requerir entorno explícito |
| `corepack pnpm jup:cleanup:check` y `git diff --check` | PASS |
| Imports de módulos individuales | PASS |

La suite completa se ejecutó en un directorio temporal de DockerDevelop, con
Python 3.12.3, Node 22.23.4, pnpm 9.0.0 y contenedores PostgreSQL/Prometheus
desechables. Árbol Git probado: `38c43415042bc1e438a8d7b5f6961fac0982a511`.
Los cambios posteriores al árbol probado son documentación de esta verificación.
Los contenedores de prueba terminaron retirados; ninguna prueba cargó bases
compartidas. No se instalaron herramientas en el sistema ni se reinició la demo.

La primera ejecución en Windows detectó expectativas residuales y montajes
incompatibles con Docker remoto. La primera pasada Linux falló sólo en cuatro
comandos por faltar Corepack. La ejecución final completa anterior incluye esa
dependencia y no omite esos controles. No se presentan los ensayos intermedios
como una validación aprobada.

Revisión técnica independiente por agente: detectó imports individuales,
expectativas residuales y una anotación omitida en la nueva prueba; corregidos.
Se reforzó también la conciliación de paneles. Esa revisión no equivale a las
reviews humanas requeridas para el PR ni a aceptación de las campañas.

## Límites y siguiente paso

En este corte previo a publicación, CI remota y revisión del PR quedan pendientes.
Los resultados de Actions deben leerse sobre el SHA publicado. CD DockerServer
sólo valida `develop`: requiere integrar el parche y completar su CI; el control
offline del workflow no acredita una promoción ni el estado del servidor.

Resultados, manifiesto de ejecuciones, dataset Azure, cargador SQL, accesos,
cuotas y límite global de 10 USD permanecen intactos. No hay nuevas consultas al
modelo, cargas de la demo, despliegues ni prueba visual del Grafana en vivo.
La definición de altura corregida queda preparada en Git para su despliegue.
La entrega sigue como **demo con incidencias**, sin aceptación integral nueva:
003/004/025, operaciones bloqueadas y métricas no medidas se conservan.

Logs privados: `materiales/07-evidencias/JUP-133-campanas-infra-20261023/agent-review/ci-fix-*`
del workspace. No se incorporan crudos, respuestas, juicios ni credenciales.
Origen: «Levantar Jupiter en dockerDevelop», `01a16421-03a0-7460-b110-24738407ccb1`.
