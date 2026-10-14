import { describe, expect, it } from "vitest";
import { isAnomalyEpisodeId } from "./contracts";

// JUP-038 tarea 6.6 (remediacion de mutantes): `isAnomalyEpisodeId`.
// Mutante que se mata aqui: `typeof value === "string" && ...` -> `true && ...`.
// `RegExp.prototype.test` convierte su argumento a texto, asi que sin la comprobacion de tipo un array de
// un solo elemento o un objeto con `toString` devolverian `true` aunque NO sean cadenas. El guardia de
// tipo (`value is string`) quedaria mintiendo al compilador: el id llegaria al backend con otra forma.

const VALID = `anomaly-${"a".repeat(64)}`;

describe("isAnomalyEpisodeId: el tipo importa, no solo el texto", () => {
  it("acepta el identificador con el formato exacto (control positivo)", () => {
    expect(isAnomalyEpisodeId(VALID)).toBe(true);
    // Hexadecimales mezclados en minuscula: tambien valido, para que el control no dependa de un solo caracter.
    expect(isAnomalyEpisodeId(`anomaly-${"0123456789abcdef".repeat(4)}`)).toBe(true);
  });

  it("rechaza un array cuyo unico elemento es un id valido (String([id]) === id)", () => {
    // Mata el mutante `true && ...`: la conversion implicita a texto dejaria pasar el array.
    expect(isAnomalyEpisodeId([VALID])).toBe(false);
  });

  it("rechaza un objeto cuyo toString devuelve un id valido", () => {
    // Mismo mecanismo con un objeto: `RegExp.test` invoca `toString`. Debe rechazarse por no ser cadena.
    const disguised = { toString: () => VALID };
    expect(isAnomalyEpisodeId(disguised)).toBe(false);
  });

  it.each([
    ["un numero", 123],
    ["null", null],
    ["undefined", undefined]
  ])("rechaza %s", (_name, value) => {
    expect(isAnomalyEpisodeId(value)).toBe(false);
  });

  it.each([
    ["mayusculas", `anomaly-${"A".repeat(64)}`],
    ["63 hexadecimales", `anomaly-${"a".repeat(63)}`],
    ["65 hexadecimales", `anomaly-${"a".repeat(65)}`],
    ["un salto de linea final", `${VALID}\n`]
  ])("rechaza una cadena con %s (el formato es exacto)", (_name, value) => {
    expect(isAnomalyEpisodeId(value)).toBe(false);
  });
});
