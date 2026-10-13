"""Closed corrective policy and authenticated recovery snapshots (private only)."""

import hashlib
import hmac
import json

INSTRUCTIONS = {
    "non_actionable_with_metrics_or_recommendations": "Correct the response: non-actionable status requires empty metrics and recommendations. Hypothetical explanations may remain in answer.",
    "documentary_support_missing": "Correct the response: every documentary text segment must reference selected authorized evidence with a literal supporting passage. Non-documentary text must have empty documentary references.",
    "unused_documentary_evidence": "Correct the response: remove documentary evidence unused by any segment or structured element. Do not invent a claim to justify an irrelevant source.",
}
IDENTITY = ("tenant_id", "user_id", "conversation_id", "operation_id", "input_hash")


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode()


def seal_cache(identity, result, effective, key):
    payload = {"identity": {k: identity[k] for k in IDENTITY},
               "result": result, "effective": effective}
    raw = encoded(payload)
    if len(raw) > 1024 * 1024 or not isinstance(key, bytes) or len(key) < 32:
        raise ValueError("Recovery cache limit.")
    return {**payload, "signature": hmac.new(key, b"chat-recovery-v1\n" + raw, hashlib.sha256).hexdigest()}


def verify_cache(cache, identity, key):
    if not isinstance(cache, dict) or set(cache) != {"identity", "result", "effective", "signature"}:
        raise ValueError("Recovery cache integrity.")
    expected = seal_cache(identity, cache["result"], cache["effective"], key)
    if cache["identity"] != expected["identity"] or not isinstance(cache["signature"], str) or not hmac.compare_digest(cache["signature"], expected["signature"]):
        raise ValueError("Recovery cache integrity.")
    return cache


def correction_code(error):
    # Only exact fixed validator messages, never arbitrary exception text.
    messages = {
        "Documentary support missing.": "documentary_support_missing",
        "Documentary calculation citation missing.": "documentary_support_missing",
        "Unused documentary evidence.": "unused_documentary_evidence",
        "non_actionable_with_metrics_or_recommendations": "non_actionable_with_metrics_or_recommendations",
    }
    if type(error) is ValueError:
        return messages.get(str(error))
    if hasattr(error, "errors"):
        for item in error.errors(include_url=False, include_input=False):
            message = item.get("msg", "")
            if message == "Value error, non-actionable responses cannot contain metrics or recommendations":
                return "non_actionable_with_metrics_or_recommendations"
    return None


def correction_message(code):
    if code not in INSTRUCTIONS:
        raise ValueError("Invalid correction code.")
    return {"role": "user", "content": "SERVER_RESPONSE_CORRECTION_V1: " + INSTRUCTIONS[code]}
