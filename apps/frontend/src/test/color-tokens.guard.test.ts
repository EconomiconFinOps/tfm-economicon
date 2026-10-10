// Guardián estático de colores literales (JUP-099, tarea 3.1, decisión 5 de
// design.md y requisito "Los colores de la interfaz proceden solo de los
// tokens del tema").
//
// Regla que protege: ninguna pantalla, armazón, componente ni dato demo
// escribe un color literal (hexadecimal o utilidad de la paleta genérica de
// Tailwind); todo color sale de un token de `theme.css`. Si alguien
// reintroduce `bg-[#1a1f2e]`, `text-slate-400` o `stroke="#94a3b8"`, este test
// falla señalando archivo, línea y valor, en lugar de depender de la revisión
// humana.
//
// Metodología (igual que index-html-dark-scope.test.ts): NO renderiza nada;
// lee los fuentes con `node:fs` y los inspecciona con expresiones regulares.
// Es determinista y rápido (lectura síncrona, sin red ni reloj).
//
// Estructura:
//   1. Un caso `it` POR ARCHIVO escaneado, para que cada grupo de migración
//      ponga en verde sus archivos y el fallo diga exactamente cuáles quedan.
//   2. Un caso por excepción declarada: una excepción obsoleta (el valor ya no
//      está en el archivo) hace fallar el test, para que la lista no acumule
//      permisos muertos.
//   3. Casos autocontenidos del detector (cadenas en memoria, sin disco) que
//      fijan sus bordes: sin ellos una regex degradada dejaría de detectar y
//      todos los casos por archivo pasarían en silencio (falso verde).
//
// Importamos `describe`/`it`/`expect` explícitamente porque el proyecto NO usa
// `globals: true` en la config de Vitest (ver vite.config.ts).
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

// src/test/ -> src/ ; y una más arriba, la raíz de apps/frontend.
const SRC_DIR = path.resolve(__dirname, "..");
const FRONTEND_DIR = path.resolve(SRC_DIR, "..");

// ---------------------------------------------------------------------------
// Excepciones declaradas: color literal que se conserva porque el tema no
// puede alcanzarlo. Un valor solo se admite si coincide archivo + valor.
// ---------------------------------------------------------------------------
interface ColorException {
  // Ruta relativa a apps/frontend, con separador "/".
  file: string;
  // Valor exacto tal como lo devuelve el detector (sin variantes delante).
  value: string;
  reason: string;
}

const EXCEPTIONS: ColorException[] = [
  {
    file: "src/components/ExportButton.tsx",
    value: "#2b2359",
    reason:
      "El <style> del documento HTML autónomo que se abre en otra ventana para imprimir a PDF no carga theme.css, así que no puede resolver tokens ni var(--...). Usa el índigo de marca.",
  },
  {
    file: "src/components/ExportButton.tsx",
    value: "#fafafc",
    reason:
      "Mismo motivo: texto de la cabecera de la tabla del documento de exportación (blanco roto de marca).",
  },
  {
    file: "src/components/ExportButton.tsx",
    value: "#d9d5f2",
    reason:
      "Mismo motivo: color de borde dentro del <style> del documento de exportación, que vive fuera de la aplicación y de theme.css.",
  },
  {
    file: "src/components/ui/dialog.tsx",
    value: "bg-black/50",
    reason:
      "Primitivo de shadcn/ui copiado tal cual lo publica el proyecto (ADR-0004; decisión 2 de design.md): los primitivos se copian, no se reescriben.",
  },
];

// ---------------------------------------------------------------------------
// Detector de colores literales
// ---------------------------------------------------------------------------

// Prefijos de utilidad de Tailwind que aceptan un color. `ring-offset` va
// antes que `ring` y `border` admite lado (`border-t-`, `border-x-`...).
const UTILITY_PREFIXES =
  "bg|text|border(?:-[xytblrse])?|ring-offset|ring|fill|stroke|from|to|via|shadow|divide|outline|decoration|accent|caret|placeholder";

// Colores de la paleta genérica que llevan escala de tono (`-400`, `-500`...).
const SCALED_COLORS =
  "slate|gray|zinc|neutral|stone|red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose";

// Decisión de diseño de este test: la escala de tono es OBLIGATORIA salvo para
// `white` y `black`, que no la tienen. Motivo: design.md define un token
// semántico llamado `neutral`; `text-neutral` es entonces una utilidad del
// tema y NO un color de paleta, mientras que `text-neutral-500` sí lo es. Con
// el tono opcional el guardián marcaría por error el token legítimo.
const PALETTE_UTILITY = new RegExp(
  // - `(?<![\w-])` evita falsos positivos por prefijo (`whitespace-...`,
  //   `--color-x`): la utilidad debe empezar en una frontera.
  // - `(?![\w-])` evita que `text-white-space` o `text-whitespace-x` cuenten
  //   como `text-white`.
  // - La opacidad `/NN` (o `/[..]`) es opcional y forma parte del valor.
  `(?<![\\w-])(?:${UTILITY_PREFIXES})-(?:(?:${SCALED_COLORS})-\\d{2,3}|white|black)(?![\\w-])(?:\\/(?:\\d{1,3}|\\[[^\\]]*\\]))?`,
  "g",
);

// Hexadecimal de color (#fff, #1e40af, #00000080). El `(?<![&\w])` evita las
// entidades HTML (`&#160;`) y los identificadores con almohadilla pegada.
const HEX_COLOR = /(?<![&\w])#[0-9a-fA-F]{3,8}\b/g;

interface ColorMatch {
  line: number;
  value: string;
}

// Devuelve cada color literal con su número de línea (base 1). Las variantes
// delante de la utilidad (`hover:`, `dark:`, `data-[state=open]:`) no forman
// parte del valor: `dark:bg-black/50` se reporta como `bg-black/50`.
function findColorLiterals(source: string): ColorMatch[] {
  const matches: ColorMatch[] = [];
  source.split(/\r?\n/).forEach((text, index) => {
    for (const regex of [HEX_COLOR, PALETTE_UTILITY]) {
      for (const found of text.matchAll(regex)) {
        matches.push({ line: index + 1, value: found[0] });
      }
    }
  });
  return matches.sort((a, b) => a.line - b.line);
}

function isAllowed(file: string, value: string): boolean {
  return EXCEPTIONS.some(
    (exception) =>
      exception.file === file &&
      exception.value.toLowerCase() === value.toLowerCase(),
  );
}

// ---------------------------------------------------------------------------
// Descubrimiento de archivos
// ---------------------------------------------------------------------------

function toRelative(absolutePath: string): string {
  return path.relative(FRONTEND_DIR, absolutePath).split(path.sep).join("/");
}

// Ámbito: todos los `*.tsx` bajo src/ y los `*.ts` bajo src/data/. Se excluyen
// los tests (`*.test.ts(x)`) y el directorio src/test/, que son ayudas de
// prueba y contienen colores a propósito (por ejemplo, los casos de este
// mismo archivo).
function listScannedFiles(): string[] {
  const testHelpersDir = path.join(SRC_DIR, "test");
  const dataDir = path.join(SRC_DIR, "data");
  const found: string[] = [];

  const walk = (directory: string): void => {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      const absolute = path.join(directory, entry.name);
      if (entry.isDirectory()) {
        if (absolute === testHelpersDir || entry.name === "node_modules") {
          continue;
        }
        walk(absolute);
        continue;
      }
      if (/\.test\.tsx?$/.test(entry.name)) continue;
      const isTsx = entry.name.endsWith(".tsx");
      const isDataTs =
        entry.name.endsWith(".ts") && absolute.startsWith(dataDir + path.sep);
      if (isTsx || isDataTs) found.push(toRelative(absolute));
    }
  };

  walk(SRC_DIR);
  return found.sort();
}

function readSource(relativeFile: string): string {
  return readFileSync(path.join(FRONTEND_DIR, relativeFile), "utf-8");
}

const SCANNED_FILES = listScannedFiles();

// ---------------------------------------------------------------------------
// Casos
// ---------------------------------------------------------------------------

describe("guardián de colores - descubrimiento de archivos", () => {
  // Sin esto, un recorrido roto devolvería una lista vacía y `it.each([])`
  // no generaría ningún caso: el guardián estaría muerto y en verde.
  it("escanea pantallas, armazón, componentes y datos demo, y excluye los tests", () => {
    expect(SCANNED_FILES).toEqual(
      expect.arrayContaining([
        "src/pages/DashboardPage.tsx",
        "src/layouts/Layout.tsx",
        "src/components/MetricCard.tsx",
        "src/components/ui/dialog.tsx",
        "src/data/demo/executiveCostDashboard.ts",
      ]),
    );
    expect(SCANNED_FILES.some((file) => /\.test\.tsx?$/.test(file))).toBe(
      false,
    );
    expect(SCANNED_FILES.some((file) => file.startsWith("src/test/"))).toBe(
      false,
    );
    // Los `.ts` fuera de src/data/ (servicios, hooks) no son parte del ámbito.
    expect(
      SCANNED_FILES.some(
        (file) => file.endsWith(".ts") && !file.startsWith("src/data/"),
      ),
    ).toBe(false);
  });
});

describe("guardián de colores - un caso por archivo", () => {
  // Cada archivo debe quedar sin color literal salvo excepciones declaradas.
  // El mensaje lista `archivo:línea valor` de cada ofensor.
  it.each(SCANNED_FILES)("%s no contiene colores literales", (file) => {
    const offenders = findColorLiterals(readSource(file))
      .filter((match) => !isAllowed(file, match.value))
      .map((match) => `${file}:${match.line}  ${match.value}`);

    expect(
      offenders,
      `${file} escribe colores literales; usa un token del tema (bg-card, text-muted-foreground, var(--chart-1)...) o declara una excepción con motivo`,
    ).toEqual([]);
  });
});

describe("guardián de colores - excepciones declaradas", () => {
  // Una excepción cuyo valor ya no aparece en su archivo es un permiso
  // muerto: podría amparar un color literal reintroducido más adelante.
  it.each(EXCEPTIONS)(
    "la excepción $value en $file sigue vigente",
    ({ file, value, reason }) => {
      expect(
        SCANNED_FILES,
        `La excepción apunta a ${file}, que no está en el ámbito escaneado`,
      ).toContain(file);
      expect(reason.trim().length, "Toda excepción lleva motivo").toBeGreaterThan(
        0,
      );

      const values = findColorLiterals(readSource(file)).map((match) =>
        match.value.toLowerCase(),
      );
      expect(
        values,
        `La excepción ${value} ya no aparece en ${file}; elimínala de la lista`,
      ).toContain(value.toLowerCase());
    },
  );
});

describe("guardián de colores - bordes del detector (en memoria)", () => {
  // Casos que DEBEN marcarse, con el valor exacto que se reporta.
  const MUST_FLAG: Array<[string, string[]]> = [
    // Clase arbitraria con hexadecimal.
    ['className="bg-[#1a1f2e]"', ["#1a1f2e"]],
    // Hexadecimal dentro de un degradado con opacidad.
    ['className="from-[#0078d4]/20"', ["#0078d4"]],
    // Atributo de Recharts.
    ['<XAxis stroke="#94a3b8" />', ["#94a3b8"]],
    // Objeto de estilo en línea con hexadecimal corto.
    ["contentStyle={{ color: '#fff' }}", ["#fff"]],
    // Hexadecimal con canal alfa (8 dígitos).
    ['const veil = "#00000080";', ["#00000080"]],
    // Variante delante + opacidad: la variante no forma parte del valor.
    ['className="hover:bg-red-500/20"', ["bg-red-500/20"]],
    ['className="text-slate-400"', ["text-slate-400"]],
    // white/black no llevan escala de tono.
    ['className="text-white"', ["text-white"]],
    ['className="shadow-blue-500/30"', ["shadow-blue-500/30"]],
    ['className="dark:bg-black/50"', ["bg-black/50"]],
    // Variante con corchetes y dos puntos.
    ['className="data-[state=open]:text-emerald-400"', ["text-emerald-400"]],
    // Prefijos compuestos: ring-offset y borde por lado.
    ['className="ring-offset-white"', ["ring-offset-white"]],
    ['className="border-t-slate-700"', ["border-t-slate-700"]],
    // Varias utilidades en la misma cadena.
    [
      'className="bg-red-500/20 text-red-300 border-red-500/30"',
      ["bg-red-500/20", "text-red-300", "border-red-500/30"],
    ],
  ];

  it.each(MUST_FLAG)("marca el color literal en: %s", (source, expected) => {
    const values = findColorLiterals(source).map((match) => match.value);
    expect(values.sort()).toEqual([...expected].sort());
  });

  // Casos que NO deben marcarse: tokens del tema y falsos positivos por
  // prefijo. Si el detector se vuelve demasiado agresivo, bloquearía
  // migraciones correctas.
  const MUST_NOT_FLAG: string[] = [
    'className="bg-card"',
    'className="text-muted-foreground"',
    'className="border-border"',
    'className="from-card to-accent"',
    '<XAxis stroke="var(--chart-axis)" />',
    'className="bg-primary/10"',
    // Prefijo engañoso: `text-whitespace` no es `text-white`.
    'className="text-whitespace"',
    'className="text-whitespace-x"',
    'className="text-white-space"',
    // `neutral` sin tono es el token semántico del tema, no la paleta.
    'className="text-neutral bg-neutral/50"',
    // Utilidades de ancho/tamaño que comparten prefijo con las de color.
    'className="border border-b text-sm shadow-lg ring-2 bg-gradient-to-br"',
    // Entidad HTML numérica: no es un color aunque parezca `#160`.
    "const nbsp = '&#160;';",
    // Almohadilla de identificador que no es hexadecimal.
    'const anchor = "#main-content";',
  ];

  it.each(MUST_NOT_FLAG)("no marca: %s", (source) => {
    expect(findColorLiterals(source)).toEqual([]);
  });

  it("reporta el número de línea (base 1) de cada ofensor", () => {
    const source = ["const a = 1;", 'const b = "#fff";', "", "text-slate-400"].join(
      "\n",
    );
    expect(findColorLiterals(source)).toEqual([
      { line: 2, value: "#fff" },
      { line: 4, value: "text-slate-400" },
    ]);
  });

  it("solo admite una excepción cuando coinciden archivo y valor", () => {
    // Mismo valor en otro archivo NO se admite; otro valor en el archivo
    // exceptuado tampoco. Evita que una excepción se convierta en un permiso
    // general.
    expect(isAllowed("src/components/ui/dialog.tsx", "bg-black/50")).toBe(true);
    expect(isAllowed("src/pages/DashboardPage.tsx", "bg-black/50")).toBe(false);
    expect(isAllowed("src/components/ui/dialog.tsx", "bg-black/60")).toBe(
      false,
    );
    expect(isAllowed("src/components/ExportButton.tsx", "#D9D5F2")).toBe(true);
    expect(isAllowed("src/components/ExportButton.tsx", "#fff")).toBe(false);
  });
});
