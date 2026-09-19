import threading

import uvicorn

from app.core.config import get_settings
from app.core.runtime_secrets import startup_boundary
from app.core.logging import configure_logging
from app.workers.runner import ProcessorWorker


@startup_boundary
def main() -> None:
    settings = get_settings()
    configure_logging()

    worker = ProcessorWorker(settings)
    thread = None
    try:
        thread = threading.Thread(target=worker.run_forever, daemon=True, name="processor-worker")
        thread.start()
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=settings.processor_port,
            reload=False,
            access_log=False,
            log_config=None,
        )
    finally:
        try:
            worker.stop()
        finally:
            try:
                if thread is not None and thread.ident is not None:
                    thread.join()
            finally:
                worker.close()


if __name__ == "__main__":
    main()
