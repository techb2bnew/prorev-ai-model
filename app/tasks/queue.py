"""A small in-process background worker.

Inference takes seconds per image, so it must not run inside the request. There
is no Redis or Docker on the target machine, so instead of Celery this uses a
thread pool inside the Flask process. The `enqueue` signature is deliberately
Celery-shaped: moving to Celery later means reimplementing this one function,
not touching any caller.

Trade-off worth knowing: jobs live in memory, so anything still running is lost
if the process restarts. `requeue_stuck_inspections` recovers those on the next
boot by putting them back in the queue.
"""

import logging
from concurrent.futures import ThreadPoolExecutor

from flask import current_app

from app.logging_config import get_correlation_id, set_correlation_id

logger = logging.getLogger(__name__)

_executor: ThreadPoolExecutor | None = None


def init_task_queue(app) -> None:
    global _executor
    workers = app.config.get("INFERENCE_WORKERS", 2)
    _executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="inference")
    app.extensions["task_queue"] = _executor
    app.logger.info("Background inference pool started with %s worker(s)", workers)


def shutdown_task_queue(wait: bool = True) -> None:
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=wait)
        _executor = None


def enqueue(func, *args, **kwargs) -> None:
    """Run `func` in a background thread with a fresh app context.

    When RUN_INFERENCE_ASYNC is False the job runs inline instead - which is
    what the tests use, so a request is finished by the time it returns.
    """
    app = current_app._get_current_object()
    correlation_id = get_correlation_id()

    if not app.config.get("RUN_INFERENCE_ASYNC", True) or _executor is None:
        func(*args, **kwargs)
        return

    def _run() -> None:
        # A background thread has no request context, so push an app context
        # for the database session and carry the correlation id across.
        set_correlation_id(correlation_id)
        with app.app_context():
            try:
                func(*args, **kwargs)
            except Exception:
                logger.exception("Background job failed")
            finally:
                # Release this thread's session so the connection returns to the pool.
                from app.extensions import db

                db.session.remove()

    _executor.submit(_run)
