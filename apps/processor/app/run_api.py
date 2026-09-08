import uvicorn

from app.core.config import get_settings
from app.core.logging import configure_logging


def main() -> None:
    settings = get_settings()
    configure_logging()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.processor_port,
        reload=False,
        access_log=False,
        log_config=None,
    )


if __name__ == "__main__":
    main()
