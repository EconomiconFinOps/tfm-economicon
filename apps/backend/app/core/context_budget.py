"""Pinned context accounting; runtime configuration can only lower model limits."""
import os

MODEL_CONTEXT = 1048576
OUTPUT_TOKENS = 11000
SUMMARY_OUTPUT_TOKENS = 10000
MARGIN_TOKENS = 1024
CHAT_BYTES = 2097152
SUMMARY_BYTES = 1048576


def budget(kind):
    if kind not in ('chat', 'summary'):
        raise ValueError('Unknown context budget kind.')
    if kind == 'chat':
        output = os.getenv('CHAT_MAX_OUTPUT_TOKENS', str(OUTPUT_TOKENS))
        if not output.isascii() or not output.isdecimal() or not 1 <= int(output) <= OUTPUT_TOKENS:
            raise ValueError('Invalid chat output token budget.')
        output_tokens = int(output)
    else:
        output_tokens = SUMMARY_OUTPUT_TOKENS
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
