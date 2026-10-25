"""Remove free-form failure text before the gateway's database callback."""

from litellm.integrations.custom_logger import CustomLogger


SAFE_ERROR_MESSAGE = "Request failed; consult the recorded error class and status."


class SafeErrorLogger(CustomLogger):
    async def async_post_call_failure_hook(
        self,
        request_data: dict,
        original_exception: Exception,
        user_api_key_dict,
        traceback_str: str | None = None,
    ) -> None:
        # LiteLLM passes this same object to the following database callback.
        # Returning an HTTPException would only change the client response.
        original_exception.message = SAFE_ERROR_MESSAGE
        original_exception.args = (SAFE_ERROR_MESSAGE,)
        for field in ("detail", "litellm_debug_info"):
            if hasattr(original_exception, field):
                setattr(original_exception, field, SAFE_ERROR_MESSAGE)


safe_error_logger = SafeErrorLogger()
