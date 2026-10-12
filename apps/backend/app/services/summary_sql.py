"""Job-local SQL facade: native cancellation and physical ownership, no shared pool.

Only the caller's dedicated worker uses connections. The monitor requests native
cancellation off the event loop; cancellation is not proof of closure. The caller
must await that worker, then close this owner before releasing its reservation.
Connection acquisition uses the driver's remaining connect timeout; its rounding
and native cleanup can extend beyond the logical deadline, never grant new work.
"""

import math, threading, time
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool


class SummarySQLDeadline(RuntimeError):
    pass


class SummarySQL:
    def __init__(self, parent, deadline):
        self.deadline = deadline
        self._lock = threading.RLock()
        self._close_lock = threading.Lock()
        self._cancel = threading.Event()
        self._finish = threading.Event()
        self._physical = None
        self._connections = set()
        self.closed = False
        remaining = self.remaining()
        if remaining <= 0:
            raise SummarySQLDeadline("Summary SQL deadline elapsed.")
        native = parent.dialect.name != "sqlite"
        # NullPool never leases or returns a physical connection to main chat.
        args = (
            {"connect_timeout": max(1, math.ceil(remaining))}
            if native
            else {"check_same_thread": False}
        )
        self.engine = create_engine(parent.url, poolclass=NullPool, connect_args=args)
        self.dialect = self.engine.dialect
        self.url = self.engine.url
        self.native = native
        self._monitor = threading.Thread(
            target=self._watch, name="summary-sql-owner", daemon=False
        )
        self._monitor.start()

    def remaining(self):
        return self.deadline - time.time()

    def check(self):
        if self.closed or self._cancel.is_set() or self.remaining() <= 0:
            raise SummarySQLDeadline("Summary SQL deadline/cancellation elapsed.")

    def cancel(self):
        self._cancel.set()

    def _watch(self):
        while not self._finish.wait(0.02):
            if not self._cancel.is_set() and self.remaining() > 0:
                continue
            self._cancel.set()
            # The same lock fences physical close/detach. Never cancel a handle
            # after it was released, or borrow one from another task's pool.
            with self._lock:
                driver = self._physical
                if driver is not None:
                    try:
                        if self.native:
                            if not driver.closed:
                                driver.cancel_safe(timeout=1)
                        else:
                            driver.interrupt()
                    except Exception:
                        # SET LOCAL still bounds native statements; ownership is
                        # retained until the real worker/connection returns.
                        pass

    def connect(self):
        self.check()
        connection = self.engine.connect()
        try:
            with self._lock:
                self.check()
                if self._connections:
                    raise RuntimeError("Overlapping summary SQL connections.")
                wrapped = Connection(self, connection)
                self._connections.add(wrapped)
                self._physical = wrapped.driver
                return wrapped
        except BaseException:
            connection.close()
            raise

    def close(self):
        # Called ONLY after the caller's tracked SQL/CPU worker has returned.
        with self._close_lock:
            if self.closed:
                return
            self.cancel()
            for connection in list(self._connections):
                connection.close()
            self._finish.set()
            self._monitor.join()
            self.engine.dispose()
            self.closed = True


class Connection:
    def __init__(self, owner, connection):
        self.owner = owner
        self.connection = connection
        self._local = False
        self.closed = False
        # Keep the original physical handle. Asking an invalidated SQLAlchemy
        # connection for it during cleanup could attempt a late reconnection.
        self.driver = connection.connection.driver_connection

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def execution_options(self, **options):
        self.owner.check()
        self.connection = self.connection.execution_options(**options)
        return self

    def _set_local(self):
        self.owner.check()
        if self.owner.native and not self._local:
            milliseconds = max(1, math.floor(self.owner.remaining() * 1000))
            self.connection.exec_driver_sql(
                "SET LOCAL statement_timeout = '" + str(milliseconds) + "ms'"
            )
            self._local = True

    def execute(self, *args, **kwargs):
        self._set_local()
        self.owner.check()
        return self.connection.execute(*args, **kwargs)

    def begin(self):
        self.owner.check()
        return Transaction(self, self.connection.begin())

    def close(self):
        with self.owner._lock:
            if self.closed:
                return
            driver = self.driver
            try:
                self.connection.close()
            except Exception:
                pass
            if self.owner.native:
                if not driver.closed:
                    driver.close()
                if not driver.closed:
                    raise RuntimeError("Owned SQL physical close not confirmed.")
            else:
                driver.close()
            self.closed = True
            self.owner._connections.discard(self)
            if self.owner._physical is driver:
                self.owner._physical = None


class Transaction:
    def __init__(self, connection, transaction):
        self.connection = connection
        self.transaction = transaction

    def __enter__(self):
        result = self.transaction.__enter__()
        self.connection._set_local()
        return result

    def __exit__(self, *args):
        try:
            return self.transaction.__exit__(*args)
        finally:
            self.connection._local = False
