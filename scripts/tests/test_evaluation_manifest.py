"""Pruebas de la lectura y validación de manifiestos de `tools/evaluation-dashboard.py` (JUP-121, tarea 2.1).

Cubren solo el contrato de los manifiestos (`read_manifest`, `merge_manifests`,
`FORMATS`, `IDENTIFIER_RE`, `ManifestError`). El resto de la herramienta (adaptadores,
carga en la base) se prueba en ficheros propios de tareas posteriores.

La ruta de la herramienta se puede sustituir con la variable de entorno
`EVALUATION_DASHBOARD_TOOL` para apuntar estas mismas pruebas a una copia mutada
durante la fase de mutación.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_manifest", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)

REAL_MANIFEST = ROOT / "docs" / "validation" / "evaluation-runs.json"
EXPECTED_FORMATS = (
    "jup-070-report-v1",
    "jup-078-benchmark-v1",
    "jup-022-calibration-v1",
    "jup-068-input-v1",
    "rows-v1",
)
ENTRY_KEYS = {"path", "format", "milestone", "run_id", "manifest"}


class ManifestTestCase(unittest.TestCase):
    """Base con un directorio temporal aislado por prueba (no se toca el repositorio)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        # resolve() evita falsos negativos por alias de rutas cortas en Windows o /tmp -> /private/tmp.
        self.dir = Path(self._tmp.name).resolve()

    def report(self, relative: str = "informe.json") -> Path:
        """Crea un informe ficticio (la lectura de manifiestos solo exige que exista)."""
        path = self.dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf8")
        return path

    def manifest(self, content, name: str = "manifiesto.json") -> Path:
        """Escribe un manifiesto; si `content` es str se escribe tal cual (JSON inválido incluido)."""
        path = self.dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        text = content if isinstance(content, str) else json.dumps(content)
        path.write_text(text, encoding="utf8")
        return path

    def entry(self, **overrides) -> dict:
        """Entrada válida mínima; `overrides` con valor `...` elimina la clave."""
        base = {"path": "informe.json", "format": "rows-v1", "milestone": False}
        for key, value in overrides.items():
            if value is ...:
                base.pop(key, None)
            else:
                base[key] = value
        return base

    def assertRejected(self, manifest_path: Path, *fragments: str, root: Path | None = None) -> str:
        """El manifiesto debe lanzar ManifestError y el mensaje nombrar el fichero y cada fragmento."""
        with self.assertRaises(tool.ManifestError) as caught:
            tool.read_manifest(manifest_path, root=root or self.dir)
        message = str(caught.exception)
        self.assertIn(manifest_path.name, message, "el error debe nombrar el fichero del manifiesto")
        for fragment in fragments:
            self.assertIn(fragment, message, f"el error debe nombrar el campo {fragment!r}")
        return message


class ContractSurfaceTests(unittest.TestCase):
    def test_formats_son_los_cinco_del_contrato_en_orden(self) -> None:
        # El contrato fija exactamente estos cinco formatos; añadir o quitar uno cambia el contrato.
        self.assertEqual(tuple(tool.FORMATS), EXPECTED_FORMATS)

    def test_manifest_error_es_value_error(self) -> None:
        # Los llamadores pueden capturar ValueError de forma genérica.
        self.assertTrue(issubclass(tool.ManifestError, ValueError))

    def test_identifier_re_es_la_regex_del_contrato(self) -> None:
        # Se fija el patrón literal para que una mutación del límite (80) o del alfabeto no pase inadvertida.
        self.assertIsInstance(tool.IDENTIFIER_RE, re.Pattern)
        self.assertEqual(tool.IDENTIFIER_RE.pattern, r"^[A-Za-z0-9][A-Za-z0-9._:=,/+@-]{0,79}$")

    def test_identifier_re_acepta_identificadores_validos(self) -> None:
        # Identificador de caso, alias de modelo y punto del barrido de calibración (lleva '=' y ',').
        for value in ("JUP-069-024", "plantilla-sin-modelo", "top_k=4,max_distance=0.6", "a", "0abc", "x" * 80):
            with self.subTest(value=value):
                self.assertIsNotNone(tool.IDENTIFIER_RE.match(value))

    def test_identifier_re_rechaza_texto_libre_y_formas_invalidas(self) -> None:
        # Regla 3 del contrato: sin texto libre. Un enunciado, espacios, empezar por símbolo o pasar de 80 se rechaza.
        for value in ("", "con espacios", "-empieza-por-guion", ".punto", "x" * 81, "¿Cuánto cuesta?", "salto\nlinea"):
            with self.subTest(value=value):
                self.assertIsNone(tool.IDENTIFIER_RE.match(value))


class RealManifestTests(unittest.TestCase):
    def test_manifiesto_versionado_se_lee_completo(self) -> None:
        # El manifiesto real de hitos: ocho informes existentes, todos de hito, sin run_id declarado.
        entries = tool.read_manifest(REAL_MANIFEST)
        self.assertEqual(len(entries), 8)
        self.assertEqual(
            [entry["format"] for entry in entries],
            [
                "jup-070-report-v1",
                "jup-070-report-v1",
                "jup-078-benchmark-v1",
                "jup-022-calibration-v1",
                "jup-068-input-v1",
                "rows-v1",
                "rows-v1",
                "rows-v1",
            ],
        )
        for entry in entries:
            with self.subTest(path=str(entry["path"])):
                self.assertEqual(set(entry), ENTRY_KEYS)
                self.assertIsInstance(entry["path"], Path)
                self.assertTrue(entry["path"].is_absolute())
                self.assertTrue(entry["path"].is_file())
                self.assertIs(entry["milestone"], True)
                self.assertIsNone(entry["run_id"])
                self.assertEqual(Path(entry["manifest"]).resolve(), REAL_MANIFEST.resolve())
        # Las rutas relativas se resuelven desde la raíz del repositorio.
        self.assertEqual(entries[0]["path"], (ROOT / "docs/evidence/JUP-070-run-1-report.json").resolve())

    def test_formatos_del_manifiesto_real_pertenecen_a_formats(self) -> None:
        # Coherencia entre el manifiesto versionado y el contrato de formatos.
        for entry in tool.read_manifest(REAL_MANIFEST):
            self.assertIn(entry["format"], tool.FORMATS)


class ReadManifestValidTests(ManifestTestCase):
    def test_ruta_absoluta_milestone_false_y_run_id_explicito(self) -> None:
        # Manifiesto local típico: ruta absoluta, no es de hito, run_id declarado.
        report = self.report()
        path = self.manifest(
            {
                "manifest_version": 1,
                "runs": [{"path": str(report), "format": "jup-068-input-v1", "milestone": False, "run_id": "JUP-069-024"}],
            }
        )
        entries = tool.read_manifest(path, root=self.dir / "otra-raiz")
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(set(entry), ENTRY_KEYS)
        self.assertEqual(entry["path"], report)
        self.assertIsInstance(entry["path"], Path)
        self.assertEqual(entry["format"], "jup-068-input-v1")
        self.assertIs(entry["milestone"], False)
        self.assertEqual(entry["run_id"], "JUP-069-024")
        self.assertEqual(Path(entry["manifest"]).resolve(), path.resolve())

    def test_ruta_relativa_se_resuelve_contra_root_y_no_contra_el_manifiesto_ni_el_cwd(self) -> None:
        # El `root` pasado como argumento manda: el informe vive en otra raíz distinta del directorio del manifiesto.
        root = self.dir / "raiz"
        report = self.report("raiz/sub/informe.json")
        path = self.manifest(
            {"manifest_version": 1, "runs": [self.entry(path="sub/informe.json")]},
            name="fuera/manifiesto.json",
        )
        entries = tool.read_manifest(path, root=root)
        self.assertEqual(entries[0]["path"], report)
        self.assertTrue(entries[0]["path"].is_absolute())
        self.assertIsNone(entries[0]["run_id"])

    def test_ruta_relativa_con_rodeos_se_normaliza(self) -> None:
        # La ruta resuelta es canónica (sin `..`), necesario para detectar duplicados después.
        report = self.report("a/informe.json")
        (self.dir / "b").mkdir()
        path = self.manifest({"manifest_version": 1, "runs": [self.entry(path="b/../a/informe.json")]})
        self.assertEqual(tool.read_manifest(path, root=self.dir)[0]["path"], report)

    def test_runs_vacio_es_valido(self) -> None:
        # Un manifiesto local sin ejecuciones es legítimo y no aporta entradas.
        path = self.manifest({"manifest_version": 1, "runs": []})
        self.assertEqual(tool.read_manifest(path, root=self.dir), [])

    def test_conserva_el_orden_y_todos_los_formatos(self) -> None:
        # Cada formato del contrato es aceptado y el orden del fichero se conserva.
        runs = []
        for index, fmt in enumerate(EXPECTED_FORMATS):
            self.report(f"r{index}.json")
            runs.append(self.entry(path=f"r{index}.json", format=fmt, milestone=index % 2 == 0))
        path = self.manifest({"manifest_version": 1, "runs": runs})
        entries = tool.read_manifest(path, root=self.dir)
        self.assertEqual([entry["format"] for entry in entries], list(EXPECTED_FORMATS))
        self.assertEqual([entry["milestone"] for entry in entries], [True, False, True, False, True])

    def test_run_id_en_el_limite_de_80_caracteres(self) -> None:
        # Límite exacto de la regex: 80 caracteres se aceptan.
        self.report()
        path = self.manifest({"manifest_version": 1, "runs": [self.entry(run_id="x" * 80)]})
        self.assertEqual(tool.read_manifest(path, root=self.dir)[0]["run_id"], "x" * 80)

    def test_read_manifest_acepta_ruta_como_str(self) -> None:
        # Los llamadores de línea de comandos pasan cadenas, no Path.
        self.report()
        path = self.manifest({"manifest_version": 1, "runs": [self.entry()]})
        self.assertEqual(len(tool.read_manifest(str(path), root=str(self.dir))), 1)


class ReadManifestRejectionTests(ManifestTestCase):
    def doc(self, **root_overrides) -> dict:
        self.report()
        data = {"manifest_version": 1, "runs": [self.entry()]}
        for key, value in root_overrides.items():
            if value is ...:
                data.pop(key, None)
            else:
                data[key] = value
        return data

    # --- manifest_version -------------------------------------------------------------------

    def test_manifest_version_distinta_de_1_se_rechaza(self) -> None:
        # Solo existe la versión 1; 0, 2, "1" (cadena), True (bool es int en Python) y ausente deben fallar.
        for label, value in (("cero", 0), ("dos", 2), ("cadena", "1"), ("bool", True), ("nulo", None), ("ausente", ...)):
            with self.subTest(caso=label):
                path = self.manifest(self.doc(manifest_version=value))
                self.assertRejected(path, "manifest_version")

    # --- runs y raíz ------------------------------------------------------------------------

    def test_runs_ausente_o_no_lista_se_rechaza(self) -> None:
        for label, value in (("ausente", ...), ("objeto", {}), ("cadena", "x"), ("nulo", None), ("numero", 3)):
            with self.subTest(caso=label):
                path = self.manifest(self.doc(runs=value))
                self.assertRejected(path, "runs")

    def test_clave_desconocida_en_la_raiz_se_rechaza(self) -> None:
        # Una errata como `run` en lugar de `runs` no debe pasar en silencio.
        path = self.manifest(self.doc(extra=1))
        self.assertRejected(path, "extra")

    def test_raiz_que_no_es_objeto_se_rechaza(self) -> None:
        for label, text in (("lista", "[]"), ("numero", "1"), ("cadena", '"x"'), ("nulo", "null")):
            with self.subTest(caso=label):
                self.assertRejected(self.manifest(text))

    # --- entradas ---------------------------------------------------------------------------

    def test_entrada_que_no_es_objeto_se_rechaza(self) -> None:
        for label, value in (("cadena", "docs/x.json"), ("lista", []), ("nulo", None), ("numero", 1)):
            with self.subTest(caso=label):
                path = self.manifest(self.doc(runs=[self.entry(), value]))
                self.assertRejected(path, "runs[1]")

    def test_clave_desconocida_en_una_entrada_se_rechaza(self) -> None:
        path = self.manifest(self.doc(runs=[self.entry(), self.entry(kind="x")]))
        self.assertRejected(path, "runs[1]", "kind")

    def test_path_invalido_se_rechaza(self) -> None:
        # Vacío, ausente o de tipo no cadena no identifican ningún informe.
        for label, value in (("vacio", ""), ("ausente", ...), ("numero", 3), ("nulo", None), ("lista", ["a"])):
            with self.subTest(caso=label):
                path = self.manifest(self.doc(runs=[self.entry(path=value)]))
                self.assertRejected(path, "runs[0].path")

    def test_format_invalido_se_rechaza(self) -> None:
        for label, value in (("desconocido", "jup-999-v1"), ("ausente", ...), ("mayusculas", "ROWS-V1"), ("numero", 1), ("nulo", None)):
            with self.subTest(caso=label):
                path = self.manifest(self.doc(runs=[self.entry(), self.entry(format=value)]))
                self.assertRejected(path, "runs[1].format")

    def test_milestone_debe_ser_bool_estricto(self) -> None:
        # "true" y 1 son falsos amigos: el contrato exige un booleano JSON.
        for label, value in (("cadena", "true"), ("entero_1", 1), ("entero_0", 0), ("nulo", None), ("ausente", ...)):
            with self.subTest(caso=label):
                path = self.manifest(self.doc(runs=[self.entry(milestone=value)]))
                self.assertRejected(path, "runs[0].milestone")

    def test_run_id_invalido_se_rechaza(self) -> None:
        # Espacios, vacío, 81 caracteres, empezar por símbolo, pregunta libre y tipos no str.
        valores = (
            ("espacios", "con espacios"),
            ("vacio", ""),
            ("81_caracteres", "x" * 81),
            ("empieza_por_guion", "-malo"),
            ("pregunta", "¿Cuánto cuesta?"),
            ("numero", 7),
            ("nulo", None),
            ("lista", ["a"]),
        )
        for label, value in valores:
            with self.subTest(caso=label):
                path = self.manifest(self.doc(runs=[self.entry(run_id=value)]))
                self.assertRejected(path, "runs[0].run_id")

    def test_el_indice_del_error_apunta_a_la_entrada_defectuosa(self) -> None:
        # Con varias entradas, el mensaje debe localizar la segunda y no la primera.
        self.report("b.json")
        data = {"manifest_version": 1, "runs": [self.entry(), self.entry(path="b.json", format="nope")]}
        message = self.assertRejected(self.manifest(data), "runs[1].format")
        self.assertNotIn("runs[0]", message)

    # --- ficheros ---------------------------------------------------------------------------

    def test_informe_inexistente_nombra_la_ruta(self) -> None:
        path = self.manifest({"manifest_version": 1, "runs": [self.entry(path="no/existe/informe.json")]})
        self.assertRejected(path, "runs[0].path", "informe.json")

    def test_ruta_absoluta_inexistente_se_rechaza(self) -> None:
        missing = self.dir / "ausente.json"
        path = self.manifest({"manifest_version": 1, "runs": [self.entry(path=str(missing))]})
        self.assertRejected(path, "runs[0].path", "ausente.json")

    def test_json_invalido_se_rechaza(self) -> None:
        for label, text in (("truncado", '{"manifest_version": 1, "runs": ['), ("vacio", ""), ("texto", "no es json")):
            with self.subTest(caso=label):
                self.assertRejected(self.manifest(text))

    def test_manifiesto_inexistente_se_rechaza(self) -> None:
        missing = self.dir / "no-existe.json"
        self.assertRejected(missing)

    def test_error_no_es_una_excepcion_del_sistema_de_ficheros(self) -> None:
        # El contrato exige ManifestError también para el manifiesto inexistente (no FileNotFoundError ni JSONDecodeError).
        with self.assertRaises(tool.ManifestError):
            tool.read_manifest(self.dir / "no-existe.json", root=self.dir)
        with self.assertRaises(tool.ManifestError):
            tool.read_manifest(self.manifest("{"), root=self.dir)


class MergeManifestsTests(ManifestTestCase):
    def test_sin_manifiestos_devuelve_lista_vacia(self) -> None:
        self.assertEqual(tool.merge_manifests([], root=self.dir), [])

    def test_concatena_en_el_orden_de_los_manifiestos(self) -> None:
        # El orden de entrada determina el orden de las ejecuciones; no se reordena ni se deduplica.
        self.report("a.json")
        self.report("b.json")
        self.report("c.json")
        first = self.manifest(
            {"manifest_version": 1, "runs": [self.entry(path="a.json", run_id="run-a"), self.entry(path="b.json", format="jup-078-benchmark-v1")]},
            name="uno.json",
        )
        second = self.manifest({"manifest_version": 1, "runs": [self.entry(path="c.json", milestone=True, run_id="run-c")]}, name="dos.json")
        merged = tool.merge_manifests([first, second], root=self.dir)
        self.assertEqual([entry["path"].name for entry in merged], ["a.json", "b.json", "c.json"])
        self.assertEqual([entry["run_id"] for entry in merged], ["run-a", None, "run-c"])
        self.assertEqual([Path(entry["manifest"]).name for entry in merged], ["uno.json", "uno.json", "dos.json"])
        self.assertTrue(all(set(entry) == ENTRY_KEYS for entry in merged))
        # Invertir el orden de los manifiestos invierte el de las entradas.
        reversed_merge = tool.merge_manifests([second, first], root=self.dir)
        self.assertEqual([entry["path"].name for entry in reversed_merge], ["c.json", "a.json", "b.json"])

    def test_manifiesto_vacio_entre_otros_no_aporta_entradas(self) -> None:
        self.report("a.json")
        empty = self.manifest({"manifest_version": 1, "runs": []}, name="vacio.json")
        full = self.manifest({"manifest_version": 1, "runs": [self.entry(path="a.json")]}, name="lleno.json")
        self.assertEqual(len(tool.merge_manifests([empty, full, empty], root=self.dir)), 1)

    def test_mismo_fichero_en_dos_manifiestos_se_rechaza(self) -> None:
        # Cargar dos veces el mismo informe duplicaría sus filas.
        self.report("x.json")
        one = self.manifest({"manifest_version": 1, "runs": [self.entry(path="x.json")]}, name="uno.json")
        two = self.manifest({"manifest_version": 1, "runs": [self.entry(path="x.json")]}, name="dos.json")
        with self.assertRaises(tool.ManifestError) as caught:
            tool.merge_manifests([one, two], root=self.dir)
        message = str(caught.exception)
        self.assertIn("x.json", message)
        self.assertIn("path", message)
        self.assertIn("dos.json", message)

    def test_mismo_fichero_con_otro_rodeo_de_ruta_se_rechaza(self) -> None:
        # Se comparan rutas resueltas: `sub/../x.json` y `x.json` son el mismo fichero.
        self.report("x.json")
        (self.dir / "sub").mkdir()
        one = self.manifest({"manifest_version": 1, "runs": [self.entry(path="x.json")]}, name="uno.json")
        two = self.manifest({"manifest_version": 1, "runs": [self.entry(path="sub/../x.json")]}, name="dos.json")
        with self.assertRaises(tool.ManifestError):
            tool.merge_manifests([one, two], root=self.dir)

    def test_ruta_absoluta_y_relativa_al_mismo_fichero_se_rechaza(self) -> None:
        report = self.report("x.json")
        one = self.manifest({"manifest_version": 1, "runs": [self.entry(path="x.json")]}, name="uno.json")
        two = self.manifest({"manifest_version": 1, "runs": [self.entry(path=str(report))]}, name="dos.json")
        with self.assertRaises(tool.ManifestError):
            tool.merge_manifests([one, two], root=self.dir)

    def test_mismo_fichero_dos_veces_en_un_manifiesto_se_rechaza(self) -> None:
        self.report("x.json")
        path = self.manifest({"manifest_version": 1, "runs": [self.entry(path="x.json"), self.entry(path="x.json", milestone=True)]})
        with self.assertRaises(tool.ManifestError) as caught:
            tool.merge_manifests([path], root=self.dir)
        self.assertIn("x.json", str(caught.exception))

    def test_run_id_explicito_repetido_se_rechaza(self) -> None:
        # Dos ejecuciones distintas no pueden compartir identificador: chocarían en la base.
        self.report("a.json")
        self.report("b.json")
        one = self.manifest({"manifest_version": 1, "runs": [self.entry(path="a.json", run_id="mismo-id")]}, name="uno.json")
        two = self.manifest({"manifest_version": 1, "runs": [self.entry(path="b.json", run_id="mismo-id")]}, name="dos.json")
        with self.assertRaises(tool.ManifestError) as caught:
            tool.merge_manifests([one, two], root=self.dir)
        message = str(caught.exception)
        self.assertIn("run_id", message)
        self.assertIn("mismo-id", message)
        self.assertIn("dos.json", message)

    def test_run_id_explicito_repetido_dentro_de_un_manifiesto_se_rechaza(self) -> None:
        self.report("a.json")
        self.report("b.json")
        path = self.manifest(
            {"manifest_version": 1, "runs": [self.entry(path="a.json", run_id="dup"), self.entry(path="b.json", run_id="dup")]}
        )
        with self.assertRaises(tool.ManifestError) as caught:
            tool.merge_manifests([path], root=self.dir)
        self.assertIn("run_id", str(caught.exception))

    def test_run_id_none_repetido_no_es_conflicto(self) -> None:
        # Sin run_id declarado se derivará del informe más adelante: varios None son normales.
        self.report("a.json")
        self.report("b.json")
        one = self.manifest({"manifest_version": 1, "runs": [self.entry(path="a.json")]}, name="uno.json")
        two = self.manifest({"manifest_version": 1, "runs": [self.entry(path="b.json")]}, name="dos.json")
        merged = tool.merge_manifests([one, two], root=self.dir)
        self.assertEqual([entry["run_id"] for entry in merged], [None, None])

    def test_run_id_distinto_con_ficheros_distintos_es_valido(self) -> None:
        self.report("a.json")
        self.report("b.json")
        path = self.manifest(
            {"manifest_version": 1, "runs": [self.entry(path="a.json", run_id="id-1"), self.entry(path="b.json", run_id="id-2")]}
        )
        self.assertEqual(len(tool.merge_manifests([path], root=self.dir)), 2)

    def test_error_en_el_segundo_manifiesto_no_devuelve_resultados_parciales(self) -> None:
        # Regeneración atómica: si cualquier manifiesto falla no se devuelve nada del primero.
        self.report("a.json")
        good = self.manifest({"manifest_version": 1, "runs": [self.entry(path="a.json")]}, name="bueno.json")
        bad = self.manifest({"manifest_version": 2, "runs": []}, name="malo.json")
        with self.assertRaises(tool.ManifestError) as caught:
            tool.merge_manifests([good, bad], root=self.dir)
        message = str(caught.exception)
        self.assertIn("malo.json", message)
        self.assertIn("manifest_version", message)

    def test_manifiesto_inexistente_en_la_lista_se_rechaza(self) -> None:
        self.report("a.json")
        good = self.manifest({"manifest_version": 1, "runs": [self.entry(path="a.json")]}, name="bueno.json")
        with self.assertRaises(tool.ManifestError) as caught:
            tool.merge_manifests([good, self.dir / "falta.json"], root=self.dir)
        self.assertIn("falta.json", str(caught.exception))

    def test_combina_manifiesto_real_con_uno_local(self) -> None:
        # Caso de uso documentado: manifiesto versionado + local con una ejecución que no es de hito.
        local_report = self.report("local.json")
        local = self.manifest(
            {"manifest_version": 1, "runs": [{"path": str(local_report), "format": "rows-v1", "milestone": False}]},
            name="local.json.manifest.json",
        )
        merged = tool.merge_manifests([REAL_MANIFEST, local], root=ROOT)
        self.assertEqual(len(merged), 9)
        self.assertEqual([entry["milestone"] for entry in merged], [True] * 8 + [False])
        self.assertEqual(merged[-1]["path"], local_report)


if __name__ == "__main__":
    unittest.main()
