import sys

import uvicorn

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.runtime_secrets import startup_boundary


@startup_boundary
def main() -> None:
    settings = get_settings()
    configure_logging()
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
