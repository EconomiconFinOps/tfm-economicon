"""Run with the approved image, network none, and safe_logging.py mounted at /fixture."""
import asyncio
from copy import deepcopy
import io
import json
import logging
import os
import sys

from litellm.proxy.spend_tracking.spend_log_error_logger import (
    SUPPRESS_SPEND_LOG_TRACEBACKS_ENV,
    spend_log_error,
    verbose_proxy_logger,
)

from safe_logging import SAFE_ERROR_MESSAGE, safe_error_logger


def traceback_privacy():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    logger = verbose_proxy_logger
    previous = (logger.handlers[:], logger.level, logger.propagate)
    previous_flag = os.environ.get(SUPPRESS_SPEND_LOG_TRACEBACKS_ENV)
    removed = "--without-traceback-suppression" in sys.argv
    sentinel = "SYNTHETIC_PRIVATE_TRACEBACK"
    try:
        if removed:
            os.environ.pop(SUPPRESS_SPEND_LOG_TRACEBACKS_ENV, None)
        else:
            os.environ[SUPPRESS_SPEND_LOG_TRACEBACKS_ENV] = "true"
        logger.handlers, logger.propagate = [handler], False
        logger.setLevel(logging.ERROR)
        try:
            raise RuntimeError(sentinel)
        except RuntimeError as exc:
            spend_log_error("Synthetic spend failure", exc=exc)
        output = stream.getvalue()
        assert "Synthetic spend failure" in output, "Real error event was discarded"
        return {"helper": "spend_log_error", "flag_removed": removed,
                "logger_level": "ERROR", "error_event_retained": True,
                "sentinel_absent": sentinel not in output,
                "traceback_absent": "Traceback (most recent call last)" not in output}
    finally:
        logger.handlers, logger.level, logger.propagate = previous
        if previous_flag is None:
            os.environ.pop(SUPPRESS_SPEND_LOG_TRACEBACKS_ENV, None)
        else:
            os.environ[SUPPRESS_SPEND_LOG_TRACEBACKS_ENV] = previous_flag
        handler.close()


async def probe():
    request_data = {"model": "economicon-chat", "metadata": {
        "response_cost": 0.125, "usage": {"prompt_tokens": 17, "completion_tokens": 23, "total_tokens": 40},
        "request_id": "synthetic-preservation", "duration_ms": 125,
    }}
    original = RuntimeError("SYNTHETIC_PRIVATE_ERROR")
    original.message = original.detail = original.litellm_debug_info = "SYNTHETIC_PRIVATE_ERROR"
    original.status_code = 503
    original.response_cost = 0.125
    original.usage = deepcopy(request_data["metadata"]["usage"])
    original.model = "economicon-chat"
    original.request_id = "synthetic-preservation"
    original.duration_ms = 125
    before_request = deepcopy(request_data)
    before_exception = deepcopy(vars(original))
    await safe_error_logger.async_post_call_failure_hook(request_data, original, None, "SYNTHETIC_TRACEBACK")
    assert request_data == before_request
    preserved = {key: value for key, value in vars(original).items()
                 if key not in {"message", "detail", "litellm_debug_info"}}
    assert preserved == {key: value for key, value in before_exception.items()
                         if key not in {"message", "detail", "litellm_debug_info"}}
    assert all(getattr(original, key) == SAFE_ERROR_MESSAGE for key in ("message", "detail", "litellm_debug_info"))
    assert original.args == (SAFE_ERROR_MESSAGE,)
    trace = traceback_privacy()
    private = trace["sentinel_absent"] and trace["traceback_absent"]
    print(json.dumps({"result": "PASS" if private else "FAIL", "mode": "synthetic-direct-public-hook-no-network",
                      "preserved": preserved, "request_data_unchanged": True,
                      "traceback_check": trace,
                      "limit": "Direct hook and real logging helper at ERROR; not HTTP/SpendLogs or real billed cost"}))
    assert private, "Real spend_log_error leaked the synthetic traceback after flag removal"


asyncio.run(probe())
