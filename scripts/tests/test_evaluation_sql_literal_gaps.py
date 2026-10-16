"""Huecos de `sql_literal` tras el QA de la tarea 3.1 (JUP-121): subclases hostiles y paridad de barras en el NUL.

Dos hallazgos LOW que dejaban mutantes vivos:

1. `sql_literal` compara tipos exactos (`kind is int`, `kind is float`). Un mutante que lo cambie por
   `isinstance(value, int)` dejaría pasar una subclase con `__repr__`/`__str__` hostiles, y su texto llegaría al
   script SQL (inyección). Aquí se definen subclases hostiles y se exige `SqlError`. `bool` (subclase de `int`)
   sigue siendo `TRUE`/`FALSE`: va antes que `int` precisamente por eso.
2. `_JSON_NUL_RE` busca el NUL escapado (`\\u0000`) en el JSON ya serializado. La regla correcta es la paridad de
   barras: el texto literal `\\u0000` (barra, `u`, cuatro ceros) se serializa con la barra duplicada y NO es un
   NUL; un NUL real precedido de barras reales sí lo es. Un mutante sin el lookbehind, o la versión ingenua
   `\\u0000`, darían un falso positivo con el texto y romperían un dato legítimo.

La ruta de la herramienta se puede sustituir con `EVALUATION_DASHBOARD_TOOL` para apuntar a una copia mutada.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_sql_literal_gaps", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

HOSTIL = "1); DROP SCHEMA evaluation; --"


# --- Subclases hostiles: su representación textual es una inyección si llega al SQL ---------------------------


class HostileInt(int):
    def __repr__(self) -> str:
        return HOSTIL

    def __str__(self) -> str:
        return HOSTIL


class HostileFloat(float):
    def __repr__(self) -> str:
        return HOSTIL

    def __str__(self) -> str:
        return HOSTIL


class HostileStr(str):
    def __repr__(self) -> str:
        return HOSTIL

    def __str__(self) -> str:
        return HOSTIL

    def __format__(self, spec: str) -> str:
        return HOSTIL


class HostileList(list):
    def __repr__(self) -> str:
        return HOSTIL

    def __str__(self) -> str:
        return HOSTIL


class HostileDict(dict):
    def __repr__(self) -> str:
        return HOSTIL

    def __str__(self) -> str:
        return HOSTIL


class HostileSubclassTest(unittest.TestCase):
    def assert_rejected(self, value) -> None:
        # Una subclase no es el tipo exacto: se rechaza, y el mensaje nunca contiene el texto hostil.
        with self.assertRaises(tool.SqlError) as caught:
            tool.sql_literal(value)
        self.assertNotIn("DROP", str(caught.exception))

    def test_subclase_de_int_se_rechaza(self) -> None:
        # Mata `kind is int` -> `isinstance(value, int)`: con isinstance devolvería `str(value)` = texto hostil.
        self.assert_rejected(HostileInt(5))

    def test_subclase_de_float_se_rechaza(self) -> None:
        # Mata `kind is float` -> `isinstance(value, float)`: devolvería `repr(value)` = texto hostil.
        self.assert_rejected(HostileFloat(1.5))

    def test_subclase_de_float_no_finita_se_rechaza_igual(self) -> None:
        self.assert_rejected(HostileFloat("nan"))

    def test_subclase_de_str_se_rechaza(self) -> None:
        self.assert_rejected(HostileStr("hola"))

    def test_subclase_de_list_se_rechaza(self) -> None:
        self.assert_rejected(HostileList(["a"]))

    def test_subclase_de_dict_se_rechaza(self) -> None:
        self.assert_rejected(HostileDict(a=1))

    def test_bool_sigue_siendo_true_y_false_y_la_subclase_de_int_no(self) -> None:
        # `bool` es subclase de `int` pero va antes: TRUE/FALSE. Una subclase hostil de int con valor 1 o 0 no.
        self.assertEqual(tool.sql_literal(True), "TRUE")
        self.assertEqual(tool.sql_literal(False), "FALSE")
        self.assert_rejected(HostileInt(1))
        self.assert_rejected(HostileInt(0))
        # El int exacto sigue funcionando: el rechazo no es una prohibición general de enteros.
        self.assertEqual(tool.sql_literal(5), "5")
        self.assertEqual(tool.sql_literal(1.5), "1.5")

    def test_subclases_dentro_de_una_lista_se_rechazan(self) -> None:
        # Los elementos de una lista deben ser `str` exactos: ninguna subclase (ni de str ni de otros tipos).
        for item in (HostileStr("a"), HostileInt(1), HostileFloat(1.0), HostileList(), 5, None):
            with self.subTest(item=type(item).__name__):
                self.assert_rejected(["ok", item])

    def test_subclase_de_list_dentro_de_una_lista_se_rechaza(self) -> None:
        self.assert_rejected([HostileList(["a"])])

    def test_subclases_numericas_dentro_de_un_dict_no_filtran_el_texto_hostil(self) -> None:
        # `json.dumps` serializa las subclases de int/float con la representación del tipo base, no con su
        # `__repr__`: el literal es seguro y nunca contiene el texto hostil. Se fija para que un cambio de
        # serializador que sí use `repr`/`str` salte aquí.
        literal = tool.sql_literal({"a": HostileInt(5), "b": HostileFloat(1.5), "c": [HostileInt(2)]})
        self.assertNotIn("DROP", literal)
        self.assertEqual(literal, "'" + json.dumps({"a": 5, "b": 1.5, "c": [2]}, sort_keys=True,
                                                    separators=(",", ":")) + "'::jsonb")

    def test_subclase_de_str_dentro_de_un_dict_usa_su_contenido_no_su_repr(self) -> None:
        # Valor y clave: se serializa el contenido real de la cadena, nunca `__repr__`/`__str__`/`__format__`.
        literal = tool.sql_literal({HostileStr("k"): HostileStr("v")})
        self.assertNotIn("DROP", literal)
        self.assertEqual(literal, """'{"k":"v"}'::jsonb""")


# --- NUL en jsonb: regla de paridad de barras ------------------------------------------------------------------


class JsonNulParityTest(unittest.TestCase):
    def test_texto_literal_barra_u0000_en_un_valor_no_es_un_nul(self) -> None:
        # Dato: barra + "u0000" (6 caracteres). El JSON lo escribe `\\u0000` (barra duplicada): no es un NUL.
        # Mata la versión ingenua `\\u0000` (falso positivo) y la regex sin el lookbehind.
        literal = tool.sql_literal({"a": "\\u0000"})
        self.assertEqual(literal, "'" + '{"a":"\\\\u0000"}' + "'::jsonb")
        # Ida y vuelta: el JSON del literal devuelve exactamente el texto original, no un NUL.
        self.assertEqual(json.loads(literal[1:-len("'::jsonb")])["a"], "\\u0000")

    def test_texto_literal_barra_u0000_en_una_clave_no_es_un_nul(self) -> None:
        literal = tool.sql_literal({"\\u0000": 1})
        self.assertEqual(literal, "'" + '{"\\\\u0000":1}' + "'::jsonb")

    def test_texto_literal_anidado_y_en_lista_no_es_un_nul(self) -> None:
        literal = tool.sql_literal({"a": {"b": ["x", "\\u0000"]}})
        self.assertEqual(literal, "'" + '{"a":{"b":["x","\\\\u0000"]}}' + "'::jsonb")

    def test_u0000_sin_barra_no_es_un_nul(self) -> None:
        # Sin barra previa en el dato, `u0000` es texto corriente.
        self.assertEqual(tool.sql_literal({"a": "u0000"}), """'{"a":"u0000"}'::jsonb""")

    def test_paridad_texto_con_cero_a_cuatro_barras_antes_de_u0000_es_dato_valido(self) -> None:
        # n barras reales + "u0000" como texto: el JSON lleva 2n barras (par) y por tanto no hay escape de NUL.
        for barras in range(0, 5):
            with self.subTest(barras=barras):
                texto = "\\" * barras + "u0000"
                literal = tool.sql_literal({"a": texto})
                self.assertEqual(json.loads(literal[1:-len("'::jsonb")].replace("''", "'"))["a"], texto)

    def test_paridad_nul_real_precedido_de_cero_a_cuatro_barras_es_error(self) -> None:
        # n barras reales + NUL real: el JSON lleva 2n+1 barras antes de `u0000` (impar): es un NUL escapado.
        # Mata un lookbehind/paridad mal planteados que dejen pasar el NUL tras barras reales.
        for barras in range(0, 5):
            with self.subTest(barras=barras):
                texto = "\\" * barras + "\x00"
                with self.assertRaises(tool.SqlError):
                    tool.sql_literal({"a": texto})

    def test_nul_real_en_valor_clave_anidado_o_lista_es_error(self) -> None:
        casos = {
            "valor": {"a": "\x00"},
            "clave": {"\x00": 1},
            "valor anidado": {"a": {"b": "x\x00y"}},
            "lista": {"a": ["ok", "\x00"]},
            "clave anidada": {"a": {"\x00": 1}},
            "lista de dicts": {"a": [{"b": "\x00"}]},
        }
        for nombre, dato in casos.items():
            with self.subTest(caso=nombre):
                with self.assertRaises(tool.SqlError) as caught:
                    tool.sql_literal(dato)
                self.assertIn("NUL", str(caught.exception))

    def test_texto_barra_u0000_y_nul_real_en_el_mismo_objeto_sigue_siendo_error(self) -> None:
        # El dato legítimo no enmascara al NUL real: basta un NUL escapado en cualquier punto del JSON.
        with self.assertRaises(tool.SqlError):
            tool.sql_literal({"a": "\\u0000", "b": "\x00"})
        with self.assertRaises(tool.SqlError):
            tool.sql_literal({"a": "\\\\u0000", "b": "\\\x00"})


if __name__ == "__main__":
    unittest.main()
