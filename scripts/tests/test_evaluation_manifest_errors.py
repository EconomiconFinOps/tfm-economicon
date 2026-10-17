"""Formato exacto de los mensajes de `ManifestError` de `tools/evaluation-dashboard.py` (JUP-121, tarea 2.1, mutación).

Contrato del mensaje:

    "<ruta del manifiesto>: <campo>: <problema>"        errores de un campo concreto
    "<ruta del manifiesto>: <problema>"                 errores del fichero entero

Las pruebas de `test_evaluation_manifest.py` solo comprueban que el mensaje «contiene el
nombre del fichero y el campo». Eso deja vivos los mutantes que alteran el índice `runs[i]`,
el separador `: ` o el prefijo. Aquí se fija la cadena `"<manifiesto>: <campo>: "` completa
(con la ruta tal como se pasó) y el índice exacto de la entrada defectuosa, siempre con
entradas válidas delante para que el índice sea mayor que 0 y no se confunda con un literal 0.

La ruta de la herramienta se puede sustituir con la variable de entorno
`EVALUATION_DASHBOARD_TOOL` para apuntar estas pruebas a una copia mutada.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = Path(os.environ.get("EVALUATION_DASHBOARD_TOOL") or ROOT / "tools" / "evaluation-dashboard.py")
SPEC = importlib.util.spec_from_file_location("economicon_evaluation_dashboard_manifest_errors", TOOL_PATH)
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = tool
SPEC.loader.exec_module(tool)


class ErrorFormatTestCase(unittest.TestCase):
    """Base con un directorio temporal aislado y ayudas para construir manifiestos."""

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

    def entry(self, relative: str = "informe.json", **overrides) -> dict:
        """Entrada válida; crea el informe al que apunta. `overrides` sustituye claves."""
        self.report(relative)
        base = {"path": relative, "format": "rows-v1", "milestone": False}
        base.update(overrides)
        return base

    def doc(self, runs, **extra) -> dict:
        return {"manifest_version": 1, "runs": runs, **extra}

    def read_error(self, manifest: Path) -> tool.ManifestError:
        with self.assertRaises(tool.ManifestError) as caught:
            tool.read_manifest(manifest, root=self.dir)
        return caught.exception

    def assert_error(self, exc: Exception, manifest: Path, field: str) -> None:
        """El mensaje debe empezar por `<manifiesto>: <campo>: ` (ruta exacta tal como se pasó).

        Se exige además que sea el PREFIJO del mensaje: un separador, una ruta o un índice
        alterados (`runs[1x]`, `manifiesto.jsonx: `) no pueden colarse en medio del texto.
        """
        expected = f"{manifest}: {field}: "
        message = str(exc)
        self.assertIn(expected, message)
        self.assertTrue(message.startswith(expected), f"el mensaje debe empezar por {expected!r}: {message!r}")


class FieldErrorFormatTests(ErrorFormatTestCase):
    def test_manifest_version_invalido(self) -> None:
        # Campo de la raíz: el mensaje es `<manifiesto>: manifest_version: ...`.
        self.entry()
        path = self.manifest({"manifest_version": 2, "runs": []})
        self.assert_error(self.read_error(path), path, "manifest_version")

    def test_runs_no_es_lista(self) -> None:
        path = self.manifest({"manifest_version": 1, "runs": {}})
        self.assert_error(self.read_error(path), path, "runs")

    def test_entrada_que_no_es_objeto_en_la_posicion_1(self) -> None:
        # Entrada válida delante: el índice reportado debe ser 1 y no 0.
        path = self.manifest(self.doc([self.entry(), 5]))
        self.assert_error(self.read_error(path), path, "runs[1]")

    def test_clave_desconocida_en_una_entrada_en_la_posicion_2(self) -> None:
        # El mensaje localiza la entrada (runs[2]) y nombra la clave sobrante.
        path = self.manifest(self.doc([self.entry("a.json"), self.entry("b.json"), self.entry("c.json", kind="x")]))
        exc = self.read_error(path)
        self.assert_error(exc, path, "runs[2]")
        self.assertIn("kind", str(exc))

    def test_clave_desconocida_en_la_raiz(self) -> None:
        # Error del fichero entero: `<manifiesto>: <problema>` sin campo intermedio.
        path = self.manifest(self.doc([self.entry()], extra=1))
        exc = self.read_error(path)
        self.assertTrue(str(exc).startswith(f"{path}: "), str(exc))
        self.assertIn("extra", str(exc))

    def test_raiz_que_no_es_objeto_usa_el_prefijo_del_fichero(self) -> None:
        path = self.manifest("[]")
        self.assertTrue(str(self.read_error(path)).startswith(f"{path}: "))

    def test_path_vacio_en_la_entrada_1(self) -> None:
        path = self.manifest(self.doc([self.entry("a.json"), self.entry("b.json", path="")]))
        self.assert_error(self.read_error(path), path, "runs[1].path")

    def test_format_desconocido_en_la_entrada_3(self) -> None:
        runs = [self.entry("a.json"), self.entry("b.json"), self.entry("c.json"), self.entry("d.json", format="nope")]
        path = self.manifest(self.doc(runs))
        self.assert_error(self.read_error(path), path, "runs[3].format")

    def test_milestone_no_bool_en_la_entrada_2(self) -> None:
        runs = [self.entry("a.json"), self.entry("b.json"), self.entry("c.json", milestone="true")]
        path = self.manifest(self.doc(runs))
        self.assert_error(self.read_error(path), path, "runs[2].milestone")

    def test_run_id_invalido_en_la_entrada_1(self) -> None:
        path = self.manifest(self.doc([self.entry("a.json"), self.entry("b.json", run_id="con espacios")]))
        self.assert_error(self.read_error(path), path, "runs[1].run_id")

    def test_el_esquema_de_todas_las_entradas_se_valida_antes_que_los_ficheros(self) -> None:
        # Informe inexistente en la 0 y error de esquema en la 1: debe ganar el de esquema (runs[1].format).
        bad_first = {"path": "no-existe.json", "format": "rows-v1", "milestone": False}
        path = self.manifest(self.doc([bad_first, self.entry("b.json", format="nope")]))
        self.assert_error(self.read_error(path), path, "runs[1].format")


class FileErrorFormatTests(ErrorFormatTestCase):
    def test_informe_inexistente_en_la_entrada_2_con_validas_antes_y_despues(self) -> None:
        # El índice reportado es el de ESA entrada (2), no el de la primera ni el de la última.
        missing = {"path": "falta.json", "format": "rows-v1", "milestone": False}
        runs = [self.entry("a.json"), self.entry("b.json"), missing, self.entry("d.json")]
        path = self.manifest(self.doc(runs))
        exc = self.read_error(path)
        self.assert_error(exc, path, "runs[2].path")
        self.assertIn("falta.json", str(exc))

    def test_ruta_con_byte_nulo_es_manifest_error_y_no_value_error_cruda(self) -> None:
        # En Windows resolve()/is_file() con `\x00` puede lanzar ValueError; el producto debe convertirlo.
        # Si la plataforma no lanza nada, la ruta con NUL tampoco puede existir: sigue siendo ManifestError en runs[0].path.
        runs = [{"path": "inf\x00orme.json", "format": "rows-v1", "milestone": False}]
        path = self.manifest(self.doc(runs))
        with self.assertRaises(tool.ManifestError) as caught:
            tool.read_manifest(path, root=self.dir)
        self.assert_error(caught.exception, path, "runs[0].path")

    def test_fallo_del_sistema_de_ficheros_al_resolver_se_convierte_en_manifest_error(self) -> None:
        # En algunas plataformas `resolve()` no falla con rutas raras (p. ej. byte nulo), así que el
        # camino `except (OSError, ValueError)` se fuerza simulando el fallo en la frontera del disco.
        # Debe salir ManifestError con campo runs[1].path y no la excepción cruda ni un UnboundLocalError.
        path = self.manifest(self.doc([self.entry("a.json"), self.entry("b.json")]))
        for error in (ValueError("embedded null byte"), OSError("fallo de disco")):
            with self.subTest(error=type(error).__name__):
                with mock.patch.object(Path, "resolve", side_effect=[self.dir / "a.json", error]):
                    with self.assertRaises(tool.ManifestError) as caught:
                        tool.read_manifest(path, root=self.dir)
                self.assert_error(caught.exception, path, "runs[1].path")
                self.assertIn(str(error), str(caught.exception))

    def test_json_invalido_indica_que_el_fallo_es_de_json(self) -> None:
        # El usuario debe saber que falla el JSON y no el contrato: prefijo del fichero y la palabra JSON.
        path = self.manifest('{"manifest_version": 1, "runs": [')
        exc = self.read_error(path)
        self.assertTrue(str(exc).startswith(f"{path}: "), str(exc))
        self.assertIn("JSON", str(exc))

    def test_manifiesto_inexistente_usa_el_prefijo_del_fichero(self) -> None:
        missing = self.dir / "no-existe.json"
        self.assertTrue(str(self.read_error(missing)).startswith(f"{missing}: "))


class MergeErrorFormatTests(ErrorFormatTestCase):
    def test_informe_repetido_acusa_al_manifiesto_que_repite_y_a_su_indice(self) -> None:
        # La entrada repetida es la posición 1 del SEGUNDO manifiesto: el error usa ese manifiesto e índice.
        first = self.manifest(self.doc([self.entry("x.json")]), name="uno.json")
        second = self.manifest(self.doc([self.entry("y.json"), self.entry("x.json")]), name="dos.json")
        with self.assertRaises(tool.ManifestError) as caught:
            tool.merge_manifests([first, second], root=self.dir)
        self.assert_error(caught.exception, second, "runs[1].path")

    def test_run_id_repetido_acusa_al_manifiesto_que_repite_y_a_su_indice(self) -> None:
        first = self.manifest(self.doc([self.entry("a.json", run_id="mismo")]), name="uno.json")
        second = self.manifest(
            self.doc([self.entry("b.json", run_id="otro"), self.entry("c.json", run_id="mismo")]),
            name="dos.json",
        )
        with self.assertRaises(tool.ManifestError) as caught:
            tool.merge_manifests([first, second], root=self.dir)
        self.assert_error(caught.exception, second, "runs[1].run_id")


if __name__ == "__main__":
    unittest.main()
