import js from "@eslint/js";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import tseslint from "typescript-eslint";
import globals from "globals";

// `tseslint.configs.recommended` llega trocado en varios objetos (registro de
// parser/plugin + reglas repartidas en distintas entradas). Se fusionan todas
// las `rules` en un unico objeto para no depender de cuantas entradas ni en
// que orden las publique la libreria (mas robusto que indexar el array).
const tsRecommendedRules = Object.assign(
  {},
  ...tseslint.configs.recommended.map((config) => config.rules ?? {})
);

export default [
  js.configs.recommended,
  {
    files: ["src/**/*.{js,jsx}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parserOptions: {
        ecmaFeatures: {
          jsx: true
        }
      },
      globals: {
        ...globals.browser
      }
    },
    plugins: {
      react,
      "react-hooks": reactHooks
    },
    settings: {
      react: {
        version: "detect"
      }
    },
    rules: {
      ...react.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      "react/react-in-jsx-scope": "off"
    }
  },
  {
    // Bloque TypeScript, con ambito exclusivo a src/**/*.{ts,tsx}. El bloque
    // {js,jsx} de arriba queda intacto a proposito: RF-082-002 (49 violaciones
    // de react/prop-types en 9 .jsx) sigue abierto hasta que F3 los migre a
    // .tsx, asi que esos archivos deben seguir bajo esa regla (ADR-0003,
    // decision 3, corregido en la revision de PR de JUP-092).
    files: ["src/**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parser: tseslint.parser,
      parserOptions: {
        ecmaFeatures: {
          jsx: true
        }
      },
      globals: {
        ...globals.browser
      }
    },
    plugins: {
      "@typescript-eslint": tseslint.plugin,
      react,
      "react-hooks": reactHooks
    },
    settings: {
      react: {
        version: "detect"
      }
    },
    rules: {
      ...tsRecommendedRules,
      ...react.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      "react/react-in-jsx-scope": "off",
      // TypeScript ya valida las props en tiempo de compilacion; esta regla
      // de runtime queda redundante SOLO donde hay tipos reales (ADR-0003,
      // decision 3). Los .jsx sin tipar la conservan en el bloque de arriba.
      "react/prop-types": "off"
    }
  }
];
