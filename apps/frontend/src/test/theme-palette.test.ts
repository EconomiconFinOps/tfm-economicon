// Contrato del tema (JUP-099, tarea 3.2, decisiones 2, 3 y 5 de design.md y
// requisitos "El tema define una única paleta activa" y "Un cambio de token
// se propaga a toda la interfaz"). Sustituye a index-html-dark-scope.test.ts.
//
// Qué protege:
//   a. `theme.css` no tiene bloque `.dark` ni una variante `dark:` atada a un
//      ancestro `.dark`: la paleta clara vive en `:root` y `dark:` no aplica
//      (`@custom-variant dark (&:not(*));`, JUP-112).
//   b. Cada propiedad personalizada se declara UNA sola vez (sin paleta
//      paralela con los mismos nombres repetidos en `:root` y `.dark`).
//   c. Cada `var(--x)` de `@theme inline` apunta a un token realmente
//      declarado (un alias roto compilaría sin avisar y la utilidad no
//      pintaría nada).
//   d. Cada `--color-*` expuesto en `@theme inline` tiene al menos un
//      consumidor en `src/` (decisión 3: los tokens sin uso se retiran).
//   e. El `<html>` de index.html no depende de una clase de tema.
//
// Metodología (igual que index-html-dark-scope.test.ts): NO renderiza; lee
// theme.css, index.html y los fuentes con `node:fs`. Determinista y rápido.
// Las funciones de análisis (parser de CSS, búsqueda de consumidores,
// extracción de clases de <html>) tienen casos autocontenidos en memoria que
// fijan sus bordes, para que una regex degradada no deje pasar el contrato en
// silencio.
//
// Importamos `describe`/`it`/`expect` explícitamente porque el proyecto NO usa
// `globals: true` en la config de Vitest (ver vite.config.ts).
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

const SRC_DIR = path.resolve(__dirname, "..");
const FRONTEND_DIR = path.resolve(SRC_DIR, "..");
const THEME_CSS_PATH = path.join(SRC_DIR, "styles", "theme.css");
const INDEX_HTML_PATH = path.join(FRONTEND_DIR, "index.html");

// ---------------------------------------------------------------------------
// Parser mínimo de CSS (suficiente para theme.css: bloques anidados,
// declaraciones y sentencias `@...;`). No pretende ser un parser completo.
// ---------------------------------------------------------------------------

interface CssNode {
  // Cabecera del bloque (`:root`, `@theme inline`, `.dark`...); "" en la raíz.
  header: string;
  // Sentencias directas terminadas en `;` (declaraciones `--x: v`, `@apply`,
  // `@custom-variant ...`), sin las de bloques hijos.
  statements: string[];
  children: CssNode[];
  // Texto original del bloque completo (`cabecera { cuerpo }`).
  raw: string;
}

function stripComments(css: string): string {
  return css.replace(/\/\*[\s\S]*?\*\//g, "");
}

function parseCss(css: string, header = "", raw = ""): CssNode {
  const node: CssNode = { header, statements: [], children: [], raw };
  let buffer = "";
  let index = 0;
  while (index < css.length) {
    const char = css[index];
    if (char === ";") {
      if (buffer.trim()) node.statements.push(buffer.trim());
      buffer = "";
      index += 1;
    } else if (char === "{") {
      // Busca la llave de cierre emparejada.
      let depth = 1;
      let end = index + 1;
      while (end < css.length && depth > 0) {
        if (css[end] === "{") depth += 1;
        if (css[end] === "}") depth -= 1;
        end += 1;
      }
      const blockHeader = buffer.trim();
      const inner = css.slice(index + 1, end - 1);
      node.children.push(
        parseCss(inner, blockHeader, `${blockHeader} {${inner}}`),
      );
      buffer = "";
      index = end;
    } else {
      buffer += char;
      index += 1;
    }
  }
  // Última declaración sin `;` final.
  if (buffer.trim()) node.statements.push(buffer.trim());
  return node;
}

function flatten(node: CssNode): CssNode[] {
  return [node, ...node.children.flatMap(flatten)];
}

const isThemeBlock = (node: CssNode): boolean => /^@theme\b/.test(node.header);

// Nombres (`--x`) de las declaraciones directas de un nodo.
function declaredNames(node: CssNode): string[] {
  return node.statements
    .map((statement) => statement.match(/^(--[\w-]+)\s*:/)?.[1])
    .filter((name): name is string => Boolean(name));
}

// Declaraciones `nombre -> valor` de un nodo.
function declarations(node: CssNode): Array<[string, string]> {
  return node.statements.flatMap((statement) => {
    const match = statement.match(/^(--[\w-]+)\s*:\s*([\s\S]*)$/);
    return match ? [[match[1], match[2].trim()] as [string, string]] : [];
  });
}

const parseThemeFile = (css: string): CssNode => parseCss(stripComments(css));

// ---------------------------------------------------------------------------
// Búsqueda de consumidores de un token
// ---------------------------------------------------------------------------

// Prefijos de utilidad de Tailwind que aceptan un color. Los prefijos
// compuestos (`ring-offset`, `border-t`...) también se reconocen.
const UTILITY_PREFIXES =
  "bg|text|border(?:-[xytblrse])?|ring-offset|ring|fill|stroke|from|to|via|shadow|divide|outline|decoration|accent|caret|placeholder";

function escapeRegex(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// ¿Consume `source` el token `name` (sin el prefijo `--color-`)?
// Un consumidor es:
//   - una utilidad `prefijo-nombre`, con variantes delante y `/opacidad`
//     opcionales (`hover:bg-primary/80`, `data-[state=open]:bg-accent`);
//   - `var(--nombre)` o `var(--color-nombre)`.
// Fronteras que se fijan:
//   - `(?<![\w-])` delante: `prefijo-nombre` debe empezar en una frontera, no
//     como parte de otro identificador (`--color-border` no es `border-border`).
//   - `(?![\w-])` detrás: `bg-primary-foreground` NO consume `primary`
//     (`-foreground` continúa el nombre), pero sí `primary-foreground`.
//   - La clase de ancho `border` o `border-b` no consume el token `border`:
//     hace falta `border-border`.
function hasConsumer(source: string, name: string): boolean {
  const escaped = escapeRegex(name);
  const utility = new RegExp(
    `(?<![\\w-])(?:${UTILITY_PREFIXES})-${escaped}(?![\\w-])`,
  );
  const variable = new RegExp(`var\\(\\s*--(?:color-)?${escaped}\\s*[,)]`);
  return utility.test(source) || variable.test(source);
}

// Para theme.css solo cuentan los usos FUERA de `:root` (donde un alias
// `--input: var(--border)` no es un consumidor real) y de `@theme` (donde
// `--color-x: var(--x)` es la propia definición del token).
function themeConsumerText(css: string): string {
  return parseThemeFile(css)
    .children.filter(
      (block) => block.header !== ":root" && !isThemeBlock(block),
    )
    .map((block) => block.raw)
    .join("\n");
}

// ---------------------------------------------------------------------------
// Descubrimiento de fuentes de `src/`
// ---------------------------------------------------------------------------

// Fuentes `.ts/.tsx/.css` de src/, excluyendo los tests (`*.test.ts(x)`) y
// src/test/: sus cadenas de ejemplo (`bg-primary`...) no son consumidores
// reales y falsearían el resultado.
function listConsumerSources(): string[] {
  const testHelpersDir = path.join(SRC_DIR, "test");
  const found: string[] = [];
  const walk = (directory: string): void => {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const absolute = path.join(directory, entry.name);
      if (entry.isDirectory()) {
        if (absolute !== testHelpersDir && entry.name !== "node_modules") {
          walk(absolute);
        }
        continue;
      }
      if (/\.test\.tsx?$/.test(entry.name)) continue;
      if (/\.(tsx?|css)$/.test(entry.name)) found.push(absolute);
    }
  };
  walk(SRC_DIR);
  return found.sort();
}

// Texto agregado que consumen los tokens: todos los fuentes de src/, salvo
// theme.css, del que solo cuenta lo que no sea `:root` ni `@theme`.
function loadConsumerText(): string {
  return listConsumerSources()
    .map((file) => {
      const content = readFileSync(file, "utf-8");
      return file === THEME_CSS_PATH ? themeConsumerText(content) : content;
    })
    .join("\n");
}

// ---------------------------------------------------------------------------
// Extracción de las clases de <html>
// ---------------------------------------------------------------------------

// Devuelve el conjunto de clases del atributo `class` del tag `<html ...>`, o
// `null` si no hay tag `<html>`. Si no hay atributo `class`, el conjunto es
// vacío. Se parsea como palabras separadas por espacios, no como substring,
// para no dar falso positivo con clases que meramente contengan "dark"
// (`darker-something`).
function htmlRootClasses(html: string): string[] | null {
  const tag = html.match(/<html\b[^>]*>/i);
  if (!tag) return null;
  const attribute = tag[0].match(/\sclass\s*=\s*(?:"([^"]*)"|'([^']*)')/i);
  if (!attribute) return [];
  const value = attribute[1] ?? attribute[2] ?? "";
  return value.trim().split(/\s+/).filter(Boolean);
}

// ---------------------------------------------------------------------------
// Datos reales cargados una vez (lectura síncrona)
// ---------------------------------------------------------------------------

const THEME_CSS = readFileSync(THEME_CSS_PATH, "utf-8");
const THEME_TREE = parseThemeFile(THEME_CSS);
const THEME_BLOCKS = flatten(THEME_TREE);
const THEME_INLINE_BLOCKS = THEME_BLOCKS.filter(isThemeBlock);

// Todas las declaraciones `--x: valor` de `@theme inline`.
const THEME_INLINE_DECLARATIONS = THEME_INLINE_BLOCKS.flatMap(declarations);

// Nombres declarados fuera de `@theme` (los tokens reales, en `:root`).
const ROOT_DECLARED_NAMES = THEME_BLOCKS.filter(
  (node) => !isThemeBlock(node),
).flatMap(declaredNames);

// Tokens de color expuestos como utilidades: `--color-card` -> `card`.
const EXPOSED_COLOR_TOKENS = THEME_INLINE_DECLARATIONS.map(([name]) => name)
  .filter((name) => name.startsWith("--color-"))
  .map((name) => name.slice("--color-".length));

const CONSUMER_TEXT = loadConsumerText();

// ---------------------------------------------------------------------------
// Casos
// ---------------------------------------------------------------------------

describe("theme.css - lectura del archivo real", () => {
  // Guarda contra un parser degradado: si no lee nada, los casos por token
  // no generarían ningún test y el contrato estaría vacío pero en verde.
  it("el parser encuentra `:root`, `@theme inline` y tokens de color expuestos", () => {
    expect(ROOT_DECLARED_NAMES).toEqual(
      expect.arrayContaining(["--background", "--foreground", "--radius"]),
    );
    expect(THEME_INLINE_BLOCKS.length).toBeGreaterThan(0);
    expect(EXPOSED_COLOR_TOKENS).toEqual(
      expect.arrayContaining(["background", "foreground", "border"]),
    );
  });
});

describe("theme.css - paleta única activa sin ámbito .dark (a)", () => {
  it("no contiene ningún selector ni bloque `.dark { ... }`", () => {
    // Se revisa la cabecera de todos los bloques, a cualquier profundidad,
    // para cubrir también un `.dark` anidado en `@layer` o combinado
    // (`.dark, .foo`, `html.dark`).
    const darkHeaders = THEME_BLOCKS.map((node) => node.header).filter(
      (header) => /\.dark(?![\w-])/.test(header),
    );
    expect(
      darkHeaders,
      "theme.css no debe tener una segunda paleta bajo `.dark`: los tokens viven una sola vez en :root",
    ).toEqual([]);
  });

  // Sentencia `@custom-variant dark ...;` del archivo (sin comentarios).
  const customVariant = THEME_BLOCKS.flatMap((node) => node.statements).find(
    (statement) => /^@custom-variant\s+dark\b/.test(statement),
  );

  it("la declaración `@custom-variant dark` no depende de un ancestro `.dark`", () => {
    expect(
      customVariant,
      "Debe seguir existiendo `@custom-variant dark`: sin ella Tailwind v4 interpreta `dark:` como prefers-color-scheme y el select cambiaría según el sistema operativo",
    ).toBeDefined();
    expect(customVariant).not.toMatch(/\.dark(?![\w-])/);
  });

  it("JUP-112 desactiva dark: con un selector imposible, independientemente del sistema operativo", () => {
    // JUP-112 cambia la paleta a clara sin reescribir los primitivos shadcn.
    // :not(*) nunca coincide: tampoco depende de una preferencia del SO.
    const argument = customVariant?.match(/^@custom-variant\s+dark\s*\(([\s\S]*)\)\s*$/)?.[1];
    expect(argument?.trim()).toBe("&:not(*)");
    expect(stripComments(THEME_CSS)).toMatch(/color-scheme:\s*light\s*;/);
  });
});

describe("theme.css - cada propiedad personalizada se declara una sola vez (b)", () => {
  it("ninguna propiedad personalizada (fuera de @theme inline) aparece declarada más de una vez", () => {
    const counts = new Map<string, number>();
    for (const name of ROOT_DECLARED_NAMES) {
      counts.set(name, (counts.get(name) ?? 0) + 1);
    }
    const duplicated = [...counts.entries()]
      .filter(([, count]) => count > 1)
      .map(([name, count]) => `${name} (x${count})`);

    expect(
      duplicated,
      "Cada token debe tener una sola definición: una paleta paralela repite los mismos nombres en otro bloque",
    ).toEqual([]);
  });
});

describe("theme.css - los alias de @theme inline apuntan a tokens declarados (c)", () => {
  // Un caso por par `--color-x: var(--x)`: el fallo dice qué alias está roto.
  const aliases = THEME_INLINE_DECLARATIONS.flatMap(([name, value]) =>
    [...value.matchAll(/var\(\s*(--[\w-]+)/g)].map(
      (found) => [name, found[1]] as [string, string],
    ),
  );

  it("existe al menos un alias que comprobar", () => {
    expect(aliases.length).toBeGreaterThan(0);
  });

  const allDeclared = new Set(
    THEME_BLOCKS.flatMap((node) => declaredNames(node)),
  );

  it.each(aliases)("%s -> var(%s) apunta a un token declarado", (_name, target) => {
    expect(
      allDeclared.has(target),
      `${target} se usa en @theme inline pero no está declarado en theme.css`,
    ).toBe(true);
  });
});

describe("theme.css - cada token de color expuesto tiene consumidor (d)", () => {
  // Un caso por token: el fallo dice qué token sobra (decisión 3 de
  // design.md). Consumidor = utilidad Tailwind con ese nombre o `var(--...)`
  // en cualquier `.ts/.tsx/.css` de src/ no de test (en theme.css, solo fuera
  // de `:root` y `@theme inline`).
  it.each(EXPOSED_COLOR_TOKENS)("--color-%s tiene al menos un consumidor en src/", (token) => {
    expect(
      hasConsumer(CONSUMER_TEXT, token),
      `El token --color-${token} está expuesto en @theme inline pero ninguna utilidad ni var(--${token}) lo consume en src/; retíralo del tema`,
    ).toBe(true);
  });
});

describe("búsqueda de consumidores - bordes (en memoria)", () => {
  it("`bg-primary-foreground` no consume `primary` pero sí `primary-foreground`", () => {
    const source = 'className="bg-primary-foreground"';
    expect(hasConsumer(source, "primary")).toBe(false);
    expect(hasConsumer(source, "primary-foreground")).toBe(true);
  });

  it("`text-muted-foreground` no consume `muted`", () => {
    expect(hasConsumer('className="text-muted-foreground"', "muted")).toBe(
      false,
    );
    expect(
      hasConsumer('className="text-muted-foreground"', "muted-foreground"),
    ).toBe(true);
  });

  it("`bg-primary/10` y `hover:bg-primary/80` consumen `primary` (opacidad y variantes)", () => {
    expect(hasConsumer('className="bg-primary/10"', "primary")).toBe(true);
    expect(hasConsumer('className="hover:bg-primary/80"', "primary")).toBe(
      true,
    );
    expect(
      hasConsumer('className="data-[state=open]:bg-accent"', "accent"),
    ).toBe(true);
  });

  it("`var(--chart-1)` y `var(--color-chart-1)` consumen `chart-1`", () => {
    expect(hasConsumer('stroke="var(--chart-1)"', "chart-1")).toBe(true);
    expect(hasConsumer("color: var(--color-chart-1);", "chart-1")).toBe(true);
    // Con fallback tras la coma también cuenta.
    expect(hasConsumer("color: var(--chart-1, red);", "chart-1")).toBe(true);
  });

  it("`var(--chart-10)` no consume `chart-1` (el nombre no se corta a medias)", () => {
    expect(hasConsumer('stroke="var(--chart-10)"', "chart-1")).toBe(false);
    expect(hasConsumer('className="bg-chart-10"', "chart-1")).toBe(false);
  });

  it("`border-border` consume `border`, pero la clase de ancho `border` o `border-b` no", () => {
    expect(hasConsumer('className="border-border"', "border")).toBe(true);
    expect(hasConsumer('className="border border-b rounded-lg"', "border")).toBe(
      false,
    );
  });

  it("los prefijos compuestos consumen el token (`ring-offset-background`, `border-t-border`, `outline-ring/50`)", () => {
    expect(hasConsumer('className="ring-offset-background"', "background")).toBe(
      true,
    );
    expect(hasConsumer('className="border-t-border"', "border")).toBe(true);
    expect(hasConsumer("@apply border-border outline-ring/50;", "ring")).toBe(
      true,
    );
  });

  it("la definición `--color-x` o `--x: ...` no cuenta como consumo por sí sola", () => {
    // `--color-border: var(--border);` contiene el nombre pero no es una
    // utilidad ni un `var(--color-border)`; la única referencia es `var(--border)`,
    // por eso `themeConsumerText` descarta `@theme` y `:root` antes de buscar.
    expect(hasConsumer("--color-primary: #0078d4;", "primary")).toBe(false);
    expect(hasConsumer("--border: #2d3748;", "border")).toBe(false);
  });

  it("un token sin ninguna referencia no tiene consumidor", () => {
    expect(hasConsumer('className="bg-card text-foreground"', "sidebar")).toBe(
      false,
    );
  });
});

describe("theme.css - qué texto cuenta como consumidor (en memoria)", () => {
  const css = `
    :root { --card: #1a1f2e; --input: var(--border); --border: #2d3748; }
    @theme inline { --color-card: var(--card); --color-border: var(--border); }
    @layer base {
      * { @apply border-border; }
      body { @apply bg-background text-foreground; }
    }
  `;

  it("descarta :root y @theme inline y conserva @layer base", () => {
    const text = themeConsumerText(css);
    // Aparecen solo por definición/alias: no deben contar.
    expect(hasConsumer(text, "card")).toBe(false);
    // El alias `--input: var(--border)` en :root tampoco cuenta para `border`
    // por sí solo; el consumo real viene de `@apply border-border`.
    expect(hasConsumer(text, "border")).toBe(true);
    expect(hasConsumer(text, "background")).toBe(true);
    expect(hasConsumer(text, "foreground")).toBe(true);
    expect(hasConsumer(text, "input")).toBe(false);
  });
});

describe("parser de theme.css - bordes (en memoria)", () => {
  it("separa bloques anidados y detecta `.dark` a cualquier profundidad", () => {
    const tree = parseThemeFile(
      "/* comentario */ :root { --a: 1; } @layer base { .dark { --a: 2; } }",
    );
    const headers = flatten(tree).map((node) => node.header);
    expect(headers).toEqual(expect.arrayContaining([":root", "@layer base", ".dark"]));
  });

  it("cuenta como duplicada una propiedad repetida en dos bloques", () => {
    const tree = parseThemeFile(":root { --a: 1; --b: 2 } .dark { --a: 3; }");
    const names = flatten(tree).flatMap(declaredNames);
    expect(names.filter((name) => name === "--a")).toHaveLength(2);
    // La última declaración sin `;` final también se lee.
    expect(names).toContain("--b");
  });

  it("no cuenta como duplicadas las declaraciones de @theme inline", () => {
    const tree = parseThemeFile(
      ":root { --a: 1; } @theme inline { --a: var(--a); }",
    );
    const outside = flatten(tree)
      .filter((node) => !isThemeBlock(node))
      .flatMap(declaredNames);
    expect(outside).toEqual(["--a"]);
  });

  it("lee la declaración de `@custom-variant dark` como sentencia", () => {
    const tree = parseThemeFile("@custom-variant dark (&:is(.dark *));\n:root { --a: 1; }");
    expect(tree.statements).toEqual(["@custom-variant dark (&:is(.dark *))"]);
  });
});

describe("index.html - el <html> no depende de una clase de tema (e)", () => {
  it("el tag <html> no lleva la clase `dark`", () => {
    const html = readFileSync(INDEX_HTML_PATH, "utf-8");
    const classes = htmlRootClasses(html);

    expect(classes, "No se encontró el tag <html ...> en index.html").not.toBeNull();
    // Se compara el conjunto de palabras, no un substring. El atributo
    // `class` puede no existir (conjunto vacío) y el caso es válido.
    expect(
      classes,
      "La paleta ya no depende de un ancestro `.dark`: retira class=\"dark\" del <html>",
    ).not.toContain("dark");
  });

  it("extrae las clases como conjunto de palabras (en memoria)", () => {
    expect(htmlRootClasses('<html lang="en" class="dark">')).toEqual(["dark"]);
    expect(htmlRootClasses('<html class="a  dark b" lang="en">')).toEqual([
      "a",
      "dark",
      "b",
    ]);
    expect(htmlRootClasses("<html class='dark'>")).toEqual(["dark"]);
    // Sin atributo class: conjunto vacío, no error.
    expect(htmlRootClasses('<html lang="en">')).toEqual([]);
    // Una clase que solo contiene la subcadena "dark" no es `dark`.
    expect(htmlRootClasses('<html class="darker-theme">')).not.toContain("dark");
    // Un atributo `data-class` no es el atributo `class`.
    expect(htmlRootClasses('<html data-class="dark">')).toEqual([]);
    // Sin tag <html>.
    expect(htmlRootClasses("<div class=\"dark\"></div>")).toBeNull();
  });
});
