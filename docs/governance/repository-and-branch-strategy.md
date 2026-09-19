# Estrategia de repositorio y ramas

Estado: vigente desde JUP-048.

- Trello: https://trello.com/c/l7mloFNe
- Repositorio canonico: `EconomiconFinOps/tfm-economicon`.
- Rama estable y predeterminada: `main`.
- Rama comun de integracion: `develop`.

## Responsabilidades de cada sistema

- Trello contiene alcance, prioridad, responsables, estado y calendario.
- OpenSpec conserva requisitos, diseño y escenarios tecnicos versionados.
- GitHub conserva codigo, documentacion, CI, revisiones y evidencia de merge.
- Discord sirve para conversar; una decision duradera debe registrarse en
  Trello, OpenSpec, un ADR o esta documentacion, segun corresponda.

No se crea una numeracion paralela: el mismo `JUP-XXX` se reutiliza en tarjeta,
rama, OpenSpec, titulo y cuerpo del pull request.

## Flujo aprobado

```text
tipo/JUP-XXX-descripcion -> develop -> main
```

1. Los cuatro integrantes refinan la tarjeta y asignan los roles rotatorios.
2. La rama de tarea parte del `develop` remoto actualizado.
3. La rama usa uno de estos prefijos: `feat`, `fix`, `docs`, `test`, `chore`,
   `refactor`, `ci` o `build`.
4. El pull request de tarea apunta a `develop` y supera revision y CI.
5. Se usa squash por defecto. Rebase se reserva para una serie pequena de
   commits que aporte valor de revision. Los merge commits estan desactivados.
6. GitHub elimina automaticamente la rama remota tras el merge.
7. Solo `develop` puede abrir un pull request hacia `main`.

## Politica de worktrees

- El clon principal permanece en `develop` y se actualiza con
  `git merge --ff-only origin/develop`.
- Se mantienen como maximo dos worktrees de tarea simultaneos, siempre creados
  desde `origin/develop` y asociados a una rama publicada `tipo/JUP-XXX-*`.
- Un worktree no almacena trabajo unico: antes de retirarlo, su estado debe estar
  limpio y todos sus commits deben existir en una rama local respaldada o remota.
- Tras mezclar o cerrar el pull request se ejecutan `git worktree remove <ruta>`
  y `git worktree prune`; la rama se elimina solo si ya esta integrada y no
  existe un pull request abierto.
- `tmp/` puede alojar worktrees efimeros, pero nunca artefactos que deban
  conservarse ni una segunda copia permanente del repositorio.

`main` y `develop` rechazan pushes directos, force pushes y eliminaciones. Los
detalles de revisiones y comprobaciones obligatorias se mantienen en
`github-branch-protection.md` y en `.github/rulesets/`.

## Releases y hotfixes

La promocion ordinaria se realiza mediante un pull request `develop` -> `main`,
con dos aprobaciones, CI completo e historial lineal. El merge estable se
etiqueta cuando exista una version demostrable.

Una reparacion urgente usa una rama `fix/JUP-XXX-descripcion` desde `develop` y
sigue el mismo recorrido protegido antes de promocionarse a `main`. Asi se
mantiene una unica ruta verificable y se evita que ambas ramas permanentes
diverjan.

## Inventario de ramas heredadas

El 26 de agosto de 2026 se verifico con
`git merge-base --is-ancestor <rama> origin/develop` que las ramas de JUP-019,
JUP-072 a JUP-079, JUP-082 y JUP-083, `chore/migrate-frontend` y
`setup/open-spec` ya estan contenidas en `develop`. Son candidatas a limpieza
remota coordinada; no hace falta reutilizarlas para trabajo nuevo.

`setup/sdd` no es ancestro de `develop`. No se elimina ni se integra en bloque:
requiere una tarjeta de revision separada si el equipo quiere recuperar algun
cambio. JUP-048 no borra ramas historicas sin esa decision conjunta.

## Accesos

Visualizar el repositorio publico no demuestra permiso de escritura. El acceso
se verifica individualmente mediante GitHub antes de contar una aprobacion o
cerrar una responsabilidad. A fecha de la auditoria, `Iber1to`, `ParisArcos` y
`Victorh1397` tienen permiso efectivo de administrador. Falta confirmar el
usuario de GitHub y el permiso efectivo de Lucia.

La recomendacion organizativa es mantener al menos dos owners de la
organizacion. El administrador actual del repositorio no dispone del alcance
`admin:org`, por lo que JUP-048 documenta pero no puede verificar ni cambiar los
owners de la organizacion.

## Configuracion reproducible

`.github/repository-settings.json` versiona los ajustes esperados del
repositorio. `tools/repository-governance.test.mjs` comprueba su coherencia con
las reglas de ramas y esta guia. Las consultas a la API de GitHub constituyen la
evidencia del estado remoto; los archivos por si solos no prueban activacion.

`.gitattributes` fija LF para los archivos de texto compartidos entre Windows,
Docker y CI, y excluye los binarios habituales de cualquier normalizacion. Los
colaboradores no deben cambiar finales de linea de forma manual ni ejecutar una
renormalizacion masiva fuera de un pull request dedicado y revisable.
