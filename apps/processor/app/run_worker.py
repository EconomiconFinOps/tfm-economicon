from app.core.config import get_settings
from app.core.runtime_secrets import startup_boundary
from app.core.logging import configure_logging
from app.workers.runner import ProcessorWorker


@startup_boundary
def main() -> None:
    settings = get_settings()
    configure_logging()
    worker = ProcessorWorker(settings)
    try:
        worker.run_forever()
    finally:
        worker.close()


if __name__ == "__main__":
    main()
