"""Pinned context accounting; runtime configuration can only lower model limits."""
import os

MODEL_CONTEXT = 1048576
OUTPUT_TOKENS = 800
SUMMARY_OUTPUT_TOKENS = 10000
MARGIN_TOKENS = 1024
CHAT_BYTES = 2097152
SUMMARY_BYTES = 1048576


def budget(kind):
    if kind not in ('chat', 'summary'):
        raise ValueError('Unknown context budget kind.')
    output_tokens = OUTPUT_TOKENS if kind == 'chat' else SUMMARY_OUTPUT_TOKENS
    name = 'CHAT_CONTEXT_TOKENS' if kind == 'chat' else 'SUMMARY_CONTEXT_TOKENS'
    raw = os.getenv(name, str(MODEL_CONTEXT))
    if not raw.isascii() or not raw.isdecimal():
        raise ValueError('Invalid context token budget.')
    tokens = int(raw)
    if not MARGIN_TOKENS + output_tokens < tokens <= MODEL_CONTEXT:
        raise ValueError('Context token budget outside model limits.')
    return {'v': 1, 'context_tokens': tokens, 'model_context_tokens': MODEL_CONTEXT,
            'wrapper_margin_tokens': MARGIN_TOKENS, 'output_tokens': output_tokens,
            'body_limit_bytes': CHAT_BYTES if kind == 'chat' else SUMMARY_BYTES}
