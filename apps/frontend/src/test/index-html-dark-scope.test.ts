// Verifica que el elemento raiz `<html>` de apps/frontend/index.html declara
// explicitamente el ambito oscuro (JUP-095, tarea 3.3, decision 4 de
// design.md).
//
// `theme.css` define los tokens de color reales (--background, --foreground,
// etc.) dentro del selector `.dark { ... }`, activado por
// `@custom-variant dark (&:is(.dark *));`. Sin la clase literal `dark` en
// algun ancestro del DOM, esos tokens oscuros nunca se aplican y los
// componentes de shadcn/ui que se copiaran en el grupo 4 (que consumen
// `bg-background`, `text-foreground`... via `@layer base`) renderizarian en
// claro sobre una aplicacion pensada para tema oscuro. La decision tomada es
// fijar `class="dark"` en `<html>` para que el ambito oscuro este siempre
// activo, sin depender de un toggle de usuario que no existe en el alcance
// de esta tarjeta.
//
// Este test NO renderiza JSX: index.html es un archivo estatico servido tal
// cual por Vite, asi que se lee directamente del disco con `node:fs` y se
// inspecciona el atributo `class` del tag `<html ...>` con una expresion
// regular que aisla ese atributo (evita el falso positivo de un
// `.includes('dark')` ingenuo, que "pasaria" con cualquier otra palabra que
// contenga la subcadena "dark", p. ej. una clase futura `darker-something`).
//
// Importamos `describe`/`it`/`expect` explicitamente porque el proyecto NO
// usa `globals: true` en la config de Vitest (ver vite.config.ts).
import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

// Ruta relativa desde este archivo (src/test/) hasta index.html, en la raiz
// de apps/frontend.
const INDEX_HTML_PATH = path.resolve(__dirname, "../../index.html");

describe("index.html - ambito oscuro declarado en <html>", () => {
  it("incluye la clase 'dark' entre las clases del atributo class de <html>", () => {
    const html = readFileSync(INDEX_HTML_PATH, "utf-8");

    // Captura el contenido del atributo class del tag <html ...>, sin
    // asumir que sea el unico atributo ni que este en una posicion fija
    // (por ejemplo, puede convivir con lang="en" en cualquier orden).
    const htmlTagMatch = html.match(/<html\b[^>]*>/i);
    expect(
      htmlTagMatch,
      "No se encontro el tag <html ...> en index.html"
    ).not.toBeNull();

    const htmlTag = htmlTagMatch![0];
    const classAttrMatch = htmlTag.match(/\bclass\s*=\s*"([^"]*)"/i);

    expect(
      classAttrMatch,
      `El tag <html> no tiene atributo class: ${htmlTag}`
    ).not.toBeNull();

    // Se parsea el valor del atributo class como conjunto de palabras
    // separadas por espacios, no como substring, para no dar falso positivo
    // con clases que meramente contengan la subcadena "dark".
    const classes = classAttrMatch![1].trim().split(/\s+/).filter(Boolean);

    expect(classes).toContain("dark");
  });
});
