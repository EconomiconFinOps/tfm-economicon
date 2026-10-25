import json
import logging

import structlog

from app.core.logging import configure_logging


def test_configure_logging_emits_valid_json_with_required_fields(capsys):
    configure_logging()

    logger = structlog.get_logger("test.logger")
    logger.info("something happened")

    captured = capsys.readouterr()
    line = captured.out.strip().splitlines()[-1]
    payload = json.loads(line)

    assert payload["event"] == "something happened"
    assert payload["level"] == "info"
    assert payload["service"] == "backend"
    assert payload["logger"] == "test.logger"
    assert "timestamp" in payload

    logging.getLogger().handlers.clear()
