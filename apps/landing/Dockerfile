FROM node:22-alpine@sha256:fe4f6d74e20370acb04ad889077d14d0f64a9c8ea6a42bc60cddf1e844699914 AS build
WORKDIR /landing
COPY apps/landing/src ./src
COPY apps/landing/scripts ./scripts
ARG SITE_ORIGIN=""
RUN SITE_ORIGIN="$SITE_ORIGIN" node scripts/build.mjs

FROM node:22-alpine@sha256:fe4f6d74e20370acb04ad889077d14d0f64a9c8ea6a42bc60cddf1e844699914
ENV NODE_ENV=production
WORKDIR /landing
COPY --from=build --chown=node:node /landing/dist ./dist
COPY --from=build --chown=node:node /landing/scripts ./scripts
USER node
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 CMD node -e "fetch('http://127.0.0.1:8080/healthz').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"
CMD ["node", "scripts/start.mjs"]
