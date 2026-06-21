# SDD Harness

Paquete TypeScript que valida contratos y manifiestos del harness SDD.

## Comandos

```powershell
pnpm --filter @finops/sdd-harness lint
pnpm --filter @finops/sdd-harness test
pnpm --filter @finops/sdd-harness build
pnpm sdd:validate-manifest -- SPEC/examples/HU-000-fixture/manifest.yaml
pnpm sdd -- status --story HU-001
pnpm sdd -- contract validate --schema skill/verifier/input@1.0.0 --input .sdd/fixtures/contracts/common-input.valid.yaml
```

El validador devuelve JSON determinista y usa estos exit codes:

- `0`: manifiesto válido.
- `1`: errores estructurales o semánticos.
- `2`: error de lectura, configuración o versión no soportada.

## CLI determinista

El entrypoint público es `pnpm sdd -- <command>`. Implementa `init`, `validate`, `status`, `approve`, `revise`, `artifact register`, `evidence record`, `next`, `run`, `review`, `story`, `recover` y `contract validate`.

- JSON es el formato por defecto; `--format text` ofrece una vista humana.
- Las aprobaciones usan `--identity` o la identidad configurada en Git.
- `run` registra intentos y resultados suministrados; nunca ejecuta agentes, skills ni comandos externos.
- Los snapshots se conservan bajo `SPEC/HU-NNN/history/`.
- El journal está encadenado por hash y el manifest conserva su head.
- El manifest soportado es exclusivamente `2.0.0`; cada artefacto referencia un contrato versionado.
- `contract validate` valida payloads JSON o YAML contra el catálogo `.sdd/schemas/catalog.yaml` sin modificar estado.
- El preflight valida front matter, secciones Markdown, referencias documentales y hashes antes de cualquier commit.
