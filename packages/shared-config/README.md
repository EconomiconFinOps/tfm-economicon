# Shared Config

## Descripcion

`packages/shared-config` es un paquete compartido del monorepo.

No es un servicio que se ejecute por si solo. Su funcion es centralizar configuraciones, constantes y pequenos contratos reutilizables para la parte JavaScript del workspace.

Ahora mismo expone metadata basica del monorepo, pero esta preparado para crecer con:

- constantes compartidas
- tokens de diseno
- wrappers de configuracion
- contratos JS comunes

## Stack

- `JavaScript`
- `ES Modules`
- `pnpm workspace`

## Estructura

```text
packages/shared-config
|-- index.js
|-- package.json
`-- README.md
```

## Como usarlo

### Con Docker Compose

No tiene ejecucion propia ni puerto.

Se usa indirectamente cuando otros modulos del monorepo lo importan.

### Con Turborepo

Desde la raiz del repo:

```powershell
pnpm dev
```

Turborepo no levanta este paquete como servicio visible, pero lo incluye en el workspace y puede ser usado por las apps.

Puerto visible:

- no aplica

### Individualmente

Este paquete no se "corre" como una aplicacion.

Se consume desde otros paquetes o apps del monorepo mediante imports.

Puerto visible:

- no aplica

## Notas

- Es un paquete de soporte, no una API ni una interfaz web.
- Si en el futuro compartis navegacion, tema o contratos JS, este es el sitio natural para ponerlos.
