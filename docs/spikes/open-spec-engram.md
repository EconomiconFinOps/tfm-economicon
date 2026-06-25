# OpenSpec and Engram

This project uses OpenSpec for spec-driven change planning and Engram as a local-only memory tool.

Use `pnpm` for Node dependencies in this repository. Do not run `npm i` here; the workspace is configured for `pnpm@9.0.0`.

## OpenSpec

OpenSpec is installed as a project dev dependency and configured for Codex and Claude.

```powershell
pnpm openspec --version
pnpm openspec:list
pnpm openspec:validate
```

To re-run project initialization:

```powershell
pnpm openspec:init
```

The lightweight HU workflow is documented in `docs/openspec-hu-adaptation-plan.md`.

## Engram

Engram is vendored as a project-local Windows binary in `tools/engram/`.

```powershell
pnpm engram --version
pnpm engram:doctor
pnpm engram:context
```

Engram memory is local-only for this project. The `.engram/` directory is ignored so local memory exports are not committed.

If an agent needs MCP access to Engram, start the local stdio server with:

```powershell
pnpm engram:mcp
```

Do not run `engram setup codex` for this project setup; that command modifies global Codex configuration.
