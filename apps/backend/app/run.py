import sys

import uvicorn

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload="--reload" in sys.argv,
        access_log=False,
        log_config=None,
    )


if __name__ == "__main__":
    main()
