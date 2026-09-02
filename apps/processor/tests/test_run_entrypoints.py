from unittest.mock import patch

from app.core.config import Settings


def _settings() -> Settings:
    return Settings(_env_file=None)


def test_run_all_disables_uvicorn_default_log_config():
    import app.run_all as run_all

    with (
        patch("app.run_all.get_settings", return_value=_settings()),
        patch("app.run_all.configure_logging"),
        patch("app.run_all.ProcessorWorker"),
        patch("app.run_all.threading.Thread"),
        patch("app.run_all.uvicorn.run") as mock_run,
    ):
        run_all.main()

    _, kwargs = mock_run.call_args
    assert kwargs["access_log"] is False
    assert kwargs["log_config"] is None


def test_run_api_disables_uvicorn_default_log_config():
    import app.run_api as run_api

    with (
        patch("app.run_api.get_settings", return_value=_settings()),
        patch("app.run_api.configure_logging"),
        patch("app.run_api.uvicorn.run") as mock_run,
    ):
        run_api.main()

    _, kwargs = mock_run.call_args
    assert kwargs["access_log"] is False
    assert kwargs["log_config"] is None
