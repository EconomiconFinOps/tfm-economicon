"""Add operational memory control without rewriting history or summaries."""

from sqlalchemy import inspect, text


def schema_steps():
    return ("ALTER TABLE conversations ADD COLUMN dialogue_compaction JSONB NULL",)


def step_applied(connection, index):
    if index != 0:
        raise RuntimeError("Invalid compaction schema step.")
    columns = {
        column["name"]: column
        for column in inspect(connection).get_columns("conversations")
    }
    if "dialogue_compaction" not in columns:
        return False
    column = columns["dialogue_compaction"]
    declared = str(column["type"]).upper()
    if connection.dialect.name == "sqlite":
        declared = next(
            row["type"]
            for row in connection.execute(
                text("PRAGMA table_info(conversations)")
            ).mappings()
            if row["name"] == "dialogue_compaction"
        ).upper()
    if declared != "JSONB" or not column["nullable"]:
        raise RuntimeError("Incompatible compaction column.")
    return True


def verify(connection):
    if not step_applied(connection, 0):
        raise RuntimeError("Missing compaction column.")
