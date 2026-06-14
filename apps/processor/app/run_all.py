import threading

import uvicorn

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.workers.runner import ProcessorWorker


def main() -> None:
    settings = get_settings()
    configure_logging()

    worker = ProcessorWorker(settings)
    thread = threading.Thread(target=worker.run_forever, daemon=True, name="processor-worker")
    thread.start()

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.processor_port, reload=False)


if __name__ == "__main__":
    main()

