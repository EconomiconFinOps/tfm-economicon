"""Prueba opt-in PostgreSQL real de la carga acotada JUP-063/JUP-121.

Ejecutar sólo en un daemon autorizado: crea UN contenedor propio, sin red/puertos,
1 CPU/1 GB y tmpfs. No crea volúmenes ni toca ningún servicio existente. No descarga
imágenes; requiere pgvector/pgvector:pg17 ya presente. Retira su recurso incluso
ante un fallo. No contiene credenciales ni realiza llamadas a modelos.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("evaluation_paired_pg", ROOT / "tools/evaluation-dashboard.py")
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)


def main(name=None):
    name = name or "economicon-jup121-paired-test-" + secrets.token_hex(6)
    if re.fullmatch(r"economicon-jup121-paired-test-[0-9a-f]{12}", name) is None:
        raise ValueError("container name must be a unique own-test identifier")
    summary = {"container": name, "limits": {"cpus": 1, "memory": "1g", "network": "none"}, "checks": []}

    def docker(*args, stdin=None, check=True):
        result = subprocess.run(["docker", *args], input=stdin, capture_output=True, text=True, timeout=45)
        if check and result.returncode:
            raise AssertionError(f"docker {' '.join(args[:3])}: {result.stderr.strip()[:500]}")
        return result

    def psql(sql, check=True):
        result = docker("exec", "-i", name, "psql", "-X", "-q", "-A", "-t", "-v", "ON_ERROR_STOP=1",
                        "-U", "postgres", "-d", "embeddings", stdin=sql, check=False)
        if check and result.returncode:
            raise AssertionError(result.stderr.strip()[:500])
        return result

    def snapshot(where=""):
        # JSONB produce orden determinista de claves; ORDER BY fija el de filas.
        sql = "SELECT row_to_json(t)::text FROM (SELECT * FROM evaluation.runs " + where + " ORDER BY run_id) t;"
        sql += "SELECT row_to_json(t)::text FROM (SELECT * FROM evaluation.results " + where
        sql += " ORDER BY run_id,grp,metric_id,behavior,status) t;"
        return psql(sql).stdout

    def checked(label, condition):
        if not condition:
            raise AssertionError(label)
        summary["checks"].append(label)

    try:
        docker("image", "inspect", "pgvector/pgvector:pg17")
        if docker("container", "inspect", name, check=False).returncode == 0:
            raise AssertionError("Unique temporary name already exists; refusing to reuse it")
        docker("run", "-d", "--pull=never", "--name", name, "--label", "economicon.jup121.test=" + name,
               "--cpus=1", "--memory=1g", "--network=none",
               "--tmpfs", "/var/lib/postgresql/data:rw,size=256m", "-e", "POSTGRES_HOST_AUTH_METHOD=trust",
               "-e", "POSTGRES_DB=embeddings", "pgvector/pgvector:pg17")
        for _ in range(30):
            if docker("exec", name, "pg_isready", "-U", "postgres", check=False).returncode == 0:
                break
            time.sleep(.5)
        else:
            raise AssertionError("PostgreSQL did not become ready")
        summary["postgres_version"] = psql("SELECT version();").stdout.strip()
        manifest = ROOT / "docs/validation/evaluation-glm-deepseek-runs.json"
        data = tool.build_dataset([manifest], root=ROOT)
        run = data["runs"][0]["run"]
        summary["run_id"] = run["run_id"]
        summary["report_sha256"] = run["report_sha256"]
        sentinel = copy.deepcopy(data)
        sentinel["runs"][0]["run"].update(run_id="sentinel-untouched", source="SENTINEL", format="rows-v1")
        sentinel["runs"][0]["results"] = [sentinel["runs"][0]["results"][3]]
        sentinel["runs"][0]["results"][0]["grp"] = "sentinel"
        psql(tool.build_sql(sentinel))  # DDL sólo en la base EFÍMERA propia.
        sentinel_before = snapshot("WHERE run_id = 'sentinel-untouched'")
        sql = tool.build_comparison_sql(data)
        psql(sql)
        once = snapshot()
        psql(sql)
        checked("idempotence", once == snapshot())
        checked("sentinel_unchanged", sentinel_before == snapshot("WHERE run_id = 'sentinel-untouched'"))
        checked("two_models_18_rows", psql("SELECT count(*) FROM evaluation.results WHERE grp = 'paired_local_provisional';").stdout.strip() == "18")
        checked("six_provisional_judgments_null", psql("SELECT count(*) FROM evaluation.results WHERE judgment IS NULL;").stdout.strip() == "6")
        dashboard = json.loads((ROOT / "apps/monitoring/grafana/dashboards/assistant-evaluation.json").read_text(encoding="utf-8"))
        panel = next(p for p in dashboard["panels"] if p["id"] == 25)
        actual = json.loads(psql("SELECT json_agg(t) FROM (" + panel["targets"][0]["rawSql"] + ") t;").stdout)
        report = json.loads((ROOT / "docs/evidence/JUP-063/glm-deepseek-20261016/comparison.json").read_text(encoding="utf-8"))
        checked("panel_two_rows", len(actual) == 2)
        for row in actual:
            original = report["models"][row["model"]]
            checked(row["model"] + "_counts", all(row[m] == original["verdicts"].get(m, 0) for m in tool.PAIRED_VERDICTS))
            checked(row["model"] + "_latency", all(row[m] == original[m] for m in ("generation_seconds_p50", "generation_seconds_p95", "generation_seconds_max")))
            checked(row["model"] + "_cost", row["reported_phase_cost_usd"] == float(original["reported_phase_cost_usd"]))
        # Error de BD tras DELETE/INSERT, antes de COMMIT: nada queda a medias.
        failed = psql(sql.replace("COMMIT;", "SELECT 1/0;\nCOMMIT;"), check=False)
        checked("injected_database_error", failed.returncode != 0)
        checked("rollback_after_delete_and_insert", once == snapshot())
        psql("UPDATE evaluation.runs SET report_sha256 = 'collision-other-full-hash' WHERE run_id = " + tool.sql_literal(run["run_id"]) + ";")
        collision_before = snapshot()
        collision = psql(sql, check=False)
        checked("same_id_different_hash_rejected", collision.returncode != 0)
        checked("collision_preserves_all_rows", collision_before == snapshot())
        checked("sentinel_still_unchanged", sentinel_before == snapshot("WHERE run_id = 'sentinel-untouched'"))
        summary["dataset_after_sha256"] = hashlib.sha256(collision_before.encode()).hexdigest()
        summary["status"] = "PASS"
    finally:
        owned = docker("inspect", "--format", '{{index .Config.Labels "economicon.jup121.test"}}', name,
                       check=False)
        if owned.returncode == 0 and owned.stdout.strip() == name:
            docker("rm", "-f", "-v", name, check=False)
        summary["container_removed"] = docker("container", "inspect", name, check=False).returncode != 0
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        if not summary["container_removed"]:
            raise AssertionError("Own temporary container could not be removed")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) == 2 else None)
