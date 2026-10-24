from contextlib import contextmanager

import pytest

from app.errors import ApiError


def test_api_error_survives_context_manager_traceback_restoration():
    @contextmanager
    def request_scope():
        yield

    error = ApiError(429, "TooManyRequests", "Retry later", {"Retry-After": "3"})
    with pytest.raises(ApiError) as caught:
        with request_scope():
            raise error

    assert caught.value is error
    assert error.status_code == 429
    assert error.code == "TooManyRequests"
    assert error.message == "Retry later"
    assert error.headers == {"Retry-After": "3"}
