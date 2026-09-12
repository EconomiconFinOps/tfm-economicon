import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import "./styles/index.css";

const queryClient = new QueryClient();

// `getElementById` tipa el retorno como `HTMLElement | null`. Bajo
// `strict: true` (tsconfig) hay que resolver ese `null` explicitamente antes
// de pasarlo a `createRoot`. Usamos el non-null assertion (`!`), igual que el
// patron de referencia en Economicon/frontend/src/main.tsx, en vez de un
// `as HTMLElement` o un `any`: el elemento `<div id="root">` esta garantizado
// en index.html (ver tarea 7.1) y este archivo es el propio entrypoint, asi
// que no hay un punto anterior donde comprobar su existencia en runtime de
// forma util (si faltase, el fallo inmediato al arrancar es la senal
// correcta). Relajar con `any` o silenciar con `@ts-ignore` esta prohibido
// por ADR-0003 y por la decision 9 de design.md de este cambio.
ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
);
