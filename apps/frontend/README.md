# Frontend

Dashboard React para la operación del asistente FinOps.

## Stack

- `React`
- `Vite`
- JavaScript

## Función En La Arquitectura

Este servicio representa la capa de interacción para:

- overview operativo
- visibilidad de tenants
- resumen de billing
- estado general de salud del backend

Consume el backend exclusivamente por HTTP REST.

## Estructura

```text
apps/frontend
|-- src/
|   |-- components/
|   |-- hooks/
|   |-- layouts/
|   |-- pages/
|   |-- services/
|   `-- styles/
|-- Dockerfile
|-- index.html
|-- package.json
`-- vite.config.js
```

## Variables De Entorno

- `VITE_API_BASE_URL`: URL base del backend. En local: `http://localhost:8000`

## Instalación

```powershell
pnpm install
```

## Ejecución Local

```powershell
pnpm dev
```

## Build

```powershell
pnpm build
```

## Docker

```powershell
docker build -t finops-frontend .
docker run --rm -p 5173:5173 --env VITE_API_BASE_URL=http://localhost:8000 finops-frontend
```

## Contratos Esperados Del Backend

- `GET /health`
- `POST /auth/login`
- `GET /me`
- `GET /tenants`
- `GET /billing/summary`

## Arquitectura

- `services/api.js` centraliza acceso HTTP.
- `hooks/useDashboardData.js` agrega la carga inicial del dashboard.
- `layouts/AppShell.jsx` define navegación y estructura principal.
- `pages/` encapsula las vistas del panel.

