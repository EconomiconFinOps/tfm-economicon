FROM node:20-alpine@sha256:fb4cd12c85ee03686f6af5362a0b0d56d50c58a04632e6c0fb8363f609372293

WORKDIR /workspace

RUN corepack enable && corepack prepare pnpm@9.0.0 --activate

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/frontend/package.json ./apps/frontend/package.json
RUN pnpm install --frozen-lockfile --filter @finops/frontend...

COPY apps/frontend ./apps/frontend

ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN pnpm --filter @finops/frontend build

WORKDIR /workspace/apps/frontend

EXPOSE 5173

USER node

HEALTHCHECK --interval=15s --timeout=5s --retries=10 --start-period=10s \
  CMD node -e "fetch('http://localhost:5173').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"

CMD ["pnpm", "exec", "vite", "preview", "--host", "0.0.0.0", "--port", "5173"]

