from unittest.mock import patch

from app.core.config import Settings


def _settings() -> Settings:
    return Settings(_env_file=None)


def test_run_disables_uvicorn_default_log_config():
    import app.run as run

    with (
        patch("app.run.get_settings", return_value=_settings()),
        patch("app.run.uvicorn.run") as mock_run,
        patch("app.run.sys.argv", ["app.run"]),
    ):
        run.main()

    _, kwargs = mock_run.call_args
    assert kwargs["access_log"] is False
    assert kwargs["log_config"] is None
    assert kwargs["reload"] is False


def test_run_enables_reload_when_flag_passed():
    import app.run as run

    with (
        patch("app.run.get_settings", return_value=_settings()),
        patch("app.run.uvicorn.run") as mock_run,
        patch("app.run.sys.argv", ["app.run", "--reload"]),
    ):
        run.main()

    _, kwargs = mock_run.call_args
    assert kwargs["reload"] is True
