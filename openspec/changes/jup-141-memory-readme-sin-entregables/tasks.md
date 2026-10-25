## 1. Editar docs/memoria/README.md (D1, D3)

- [x] 1.1 Eliminar de «Dónde vive» la viñeta de exportaciones fechadas, manifiesto SHA-256 y `materiales/06-entregables/`
- [x] 1.2 En «Para herramientas y asistentes», dejar la viñeta de la memoria como «La memoria no está en el repositorio: no se busca ni se regenera desde Git.»

## 2. Delta de spec (D2)

- [ ] 2.1 Verificar que `specs/project-memory-governance/spec.md` repite el requisito de exportaciones completo con sus dos escenarios y que solo difiere de la spec vigente en la frase «next to the other final deliverables»

## 3. Verificar el alcance (D4)

- [ ] 3.1 Comprobar que `docs/memoria/README.md` no contiene `06-entregables` y que las viñetas editadas y sus vecinas son frases completas
- [ ] 3.2 Comprobar que el diff de la rama solo toca `docs/memoria/README.md` y los artefactos de este change, sin tocar `docs/evidence/`, `docs/continuidad/` ni otros changes de OpenSpec

## 4. Validación y cierre

- [ ] 4.1 Ejecutar `corepack pnpm openspec:validate` y `corepack pnpm jup:check -- --change jup-141-memory-readme-sin-entregables`
- [ ] 4.2 Registrar en `review.md` la comprobación de la spec `project-memory-governance` y el desfase declarado en `design.md`
