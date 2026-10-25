import re

_ADD_COLUMN = re.compile(r"ADD\s+COLUMN", re.IGNORECASE)
_UPDATE_STATEMENT = re.compile(r"\bUPDATE\s+\w", re.IGNORECASE)
_TRANSACTIONAL_OPT_OUT = re.compile(r"transactional\s*=\s*False")


def migration_needs_non_transactional_opt_out(source: str) -> bool:
    adds_column = bool(_ADD_COLUMN.search(source))
    backfills_in_same_file = bool(_UPDATE_STATEMENT.search(source))
    declares_opt_out = bool(_TRANSACTIONAL_OPT_OUT.search(source))
    return adds_column and backfills_in_same_file and not declares_opt_out
