"""Fixtures explícitas: escenarios históricos y contrato del manifiesto JUP-133.

No se deduce lo esperado de la salida del adaptador. El manifiesto histórico sólo
contiene referencias a informes; no duplica datos ni sustituye el manifiesto real.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_MANIFEST = ROOT / "scripts/tests/fixtures/evaluation-before-infra.json"
INFRA_PATHS = tuple(
    f"docs/evidence/JUP-133/JUP-133-infra-{campaign}-r{repetition}.rows.json"
    for campaign in ("jup070-a", "jup071") for repetition in (1, 2, 3)
)
INFRA_IDS = tuple(
    f"jup133-infra-{campaign}-r{repetition}-20261023"
    for campaign in ("jup070-a", "jup071") for repetition in (1, 2, 3)
)
INFRA_ROW_COUNTS = (73, 73, 73, 268, 268, 268)
EVOLUTION_IDS = ('jup133-evolution-friday-20261023', 'jup133-evolution-sunday-20261025')
EVOLUTION_PATHS = tuple(f'docs/evidence/JUP-133/evolution-20261025/{day}.rows.json' for day in ('friday', 'sunday'))
EVOLUTION_ROW_COUNTS = (45, 85)
VERSIONED_RUNS = 20
VERSIONED_RESULTS = 1800
LOAD_SUMMARY = f"{VERSIONED_RUNS} ejecuciones y {VERSIONED_RESULTS} resultados cargados\n"


def historical_dataset(tool):
    """Base de doce informes anterior a las seis repeticiones de infraestructura."""
    return tool.build_dataset([HISTORICAL_MANIFEST], root=ROOT)
