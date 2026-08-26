# Evidencia de validacion JUP-048

- Fecha: 2026-08-26.
- Trello: https://trello.com/c/l7mloFNe
- Repositorio: `EconomiconFinOps/tfm-economicon`.
- Rama: `chore/JUP-048-consolidate-repository`.
- Base auditada: `develop` en `e3889cc`.

## Estado remoto comprobado

- La organizacion y el repositorio canonico estan confirmados.
- `main` es la rama predeterminada y `develop` la rama de integracion.
- Los rulesets `21475971` y `21475972` protegen respectivamente `develop` y
  `main`; ambos aparecen como ramas protegidas.
- `Iber1to`, `ParisArcos` y `Victorh1397` devuelven permiso efectivo `admin` en
  el repositorio. La lista general de colaboradores no refleja correctamente
  todos los permisos heredados de la organizacion, por lo que cada cuenta se
  comprobo individualmente.
- No se conoce todavia el usuario de GitHub de Lucia y no se atribuye acceso ni
  aprobacion sin verificarlo.
- El token actual puede administrar el repositorio, pero GitHub rechaza la
  consulta de owners/invitaciones de la organizacion por falta de `admin:org`.

## Inventario de ramas

La comprobacion de ancestros confirma que todas las ramas JUP publicadas,
`chore/migrate-frontend` y `setup/open-spec` estan incluidas en `develop`.
`setup/sdd` (`588eb16`) es la unica rama remota heredada que no es ancestro de
`develop`; se conserva sin integrar ni borrar.

No se eliminan ramas historicas en esta tarea: su limpieza remota afecta al
trabajo local de los demas miembros y requiere coordinacion. La eliminacion
automatica se aplica a futuros PR fusionados.

## Configuracion propuesta y validacion

- Los merge commits quedan desactivados; squash y rebase permanecen disponibles.
- Las ramas de PR se eliminan automaticamente despues del merge.
- Ambos rulesets aceptan exclusivamente squash o rebase.
- La politica queda versionada en `.github/repository-settings.json`.
- El nuevo test de gobernanza cruza ajustes, rulesets, estrategia y guia de
  contribucion; se ejecuta dentro del check obligatorio `OpenSpec`.

Los resultados finales de CI, la activacion remota y el pull request se
anadiran a esta evidencia antes de integrar JUP-048.

## Participacion y pendiente de cierre

- Liderazgo asignado en Trello: Victor Mendez.
- Pairing/coautoria y ejecucion de la reconciliacion: Alejandro Aguado.
- Revision de PR asignada: Lucia Mateo.
- Validacion, pruebas y documentacion asignada: Paris Arcos Martin.

La asignacion de un rol no equivale a participacion realizada. La revision de
Lucia y la validacion de Paris se registraran solo cuando existan evidencias
reales en GitHub/Trello.
