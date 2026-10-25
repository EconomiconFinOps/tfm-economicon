// Verifica que apps/frontend/index.html carga el entrypoint tipado en
// TypeScript (`/src/main.tsx`) en lugar del entrypoint historico en
// JavaScript (`/src/main.jsx`), como parte de la migracion JUP-095 (grupo 7,
// tarea 7.1: "Entrypoint e index.html").
//
// El comportamiento en tiempo de ejecucion de main.tsx no cambia respecto a
// main.jsx (ambos montan QueryClientProvider y el enrutado via App/
// RouterProvider, tarea 7.2): lo que se reconcilia aqui es exclusivamente la
// extension/tipado del archivo que Vite debe servir como modulo de entrada.
// Mientras index.html siga apuntando a main.jsx, main.tsx (una vez creado
// por el agente coder) nunca se ejecutaria, dejando la migracion a TS
// incompleta de forma silenciosa.
//
// Este test NO renderiza JSX: index.html es un archivo estatico servido tal
// cual por Vite, asi que se lee directamente del disco con `node:fs` y se
// inspecciona el atributo `src` del tag `<script type="module" ...>` con una
// expresion regular que aisla ese atributo especifico, evitando el falso
// positivo de un `.includes('main')` o `.includes('.tsx')` ingenuo (que
// "pasaria" con cualquier subcadena coincidente en otro lugar del documento,
// o incluso con una ruta parcialmente distinta como '/src/main.tsx.bak').
//
// Importamos `describe`/`it`/`expect` explicitamente porque el proyecto NO
// usa `globals: true` en la config de Vitest (ver vite.config.ts).
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

// Ruta relativa desde este archivo (src/test/) hasta index.html, en la raiz
// de apps/frontend.
const INDEX_HTML_PATH = path.resolve(__dirname, "../../index.html");

describe("index.html - entrypoint de modulo migrado a TypeScript", () => {
  it("el <script type=\"module\"> apunta exactamente a /src/main.tsx", () => {
    const html = readFileSync(INDEX_HTML_PATH, "utf-8");

    // Captura el tag <script type="module" ...> completo, sin asumir que el
    // atributo src sea el primero ni que sea el unico atributo presente.
    const scriptTagMatch = html.match(
      /<script\b[^>]*\btype\s*=\s*"module"[^>]*>/i
    );

    expect(
      scriptTagMatch,
      'No se encontro un tag <script type="module" ...> en index.html'
    ).not.toBeNull();

    const scriptTag = scriptTagMatch![0];
    const srcAttrMatch = scriptTag.match(/\bsrc\s*=\s*"([^"]*)"/i);

    expect(
      srcAttrMatch,
      `El <script type="module"> no tiene atributo src: ${scriptTag}`
    ).not.toBeNull();

    // Comparacion exacta (no substring) del valor de src: rechaza tanto el
    // entrypoint legacy '/src/main.jsx' como cualquier variante que no sea
    // exactamente la ruta esperada.
    expect(srcAttrMatch![1]).toBe("/src/main.tsx");
  });
});
