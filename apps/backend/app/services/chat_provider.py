"""Chat through the existing gateway; bounded transport and content-free errors."""
import json
from http.client import HTTPException
from urllib import error, request

from app.services.embedding_provider import (
    ProviderError, _AttemptDeadline, _DeadlineHTTPHandler, _DeadlineHTTPSHandler,
    _RejectRedirectHandler, _read_body, _reject_constant, _transport_failure,
)


class LiteLLMChatProvider:
    def __init__(self, settings):
        base = settings.litellm_base_url.rstrip("/")
        self.url = (base if base.endswith("/v1") else base + "/v1") + "/chat/completions"
        self.key = settings.litellm_api_key
        self.model = settings.chat_model
        self.timeout = settings.chat_timeout_seconds
        self.max_tokens = settings.chat_max_output_tokens
        self.transport = request.build_opener(
            request.ProxyHandler({}), _RejectRedirectHandler(),
            _DeadlineHTTPHandler(), _DeadlineHTTPSHandler(),
        )

    def generate(self, system: str, context: str, schema: dict) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": context}],
            "temperature": 0,
            "max_tokens": self.max_tokens,
            "response_format": {"type": "json_schema", "json_schema": {
                "name": "conversation_answer", "strict": True, "schema": schema,
            }},
        }
        req = request.Request(self.url, data=json.dumps(payload, allow_nan=False).encode(),
                              headers={"Authorization": "Bearer " + self.key.get_secret_value(),
                                       "Content-Type": "application/json"}, method="POST")
        category = "invalid_response"
        try:
            req._attempt_deadline = _AttemptDeadline(self.timeout)
            with self.transport.open(req, timeout=self.timeout) as response:
                body = json.loads(_read_body(response, req._attempt_deadline.expires).decode(),
                                  parse_constant=_reject_constant)
            choice = body["choices"][0]
            content = choice["message"]["content"]
            if choice.get("finish_reason") == "stop" and isinstance(content, str) and 0 < len(content) <= 32000:
                return content
        except error.HTTPError as exc:
            code = exc.code
            exc.close()
            category = ("redirect" if 300 <= code < 400 else "authentication" if code in {401, 403}
                        else "rate_limit" if code == 429 else "upstream" if code >= 500 else "request")
        except error.URLError as exc:
            category = _transport_failure(exc.reason)[0]
        except (OSError, HTTPException) as exc:
            category = _transport_failure(exc)[0]
        except (ValueError, UnicodeError, KeyError, IndexError, TypeError):
            pass
        # No chained upstream payload, no automatic generation retry/billing duplication.
        raise ProviderError(category)
