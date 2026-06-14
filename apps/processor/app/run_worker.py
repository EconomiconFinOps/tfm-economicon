from app.core.config import get_settings
from app.core.logging import configure_logging
from app.workers.runner import ProcessorWorker


def main() -> None:
    settings = get_settings()
    configure_logging()
    worker = ProcessorWorker(settings)
    worker.run_forever()


if __name__ == "__main__":
    main()
