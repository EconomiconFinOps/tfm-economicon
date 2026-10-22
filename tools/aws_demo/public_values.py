"""Recognizable credentials must never enter public configuration artifacts.

This is input validation, not a general secret detector. Secret values belong
in Secrets Manager and are passed by reference through the separate contract.
"""
import math
import re


_CREDENTIAL = re.compile(
    r'[a-z][a-z0-9+.-]*://[^\s/]+@'
    r'|\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'
    r'|-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----'
    r'|\b(?:Bearer|Basic)\s+\S+'
    r'|\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+'
    r'|(?:password|access_key|api_key|secret|token)=\S+', re.I)


def validate_public_values(value):
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise ValueError('Public configuration keys must be strings')
        for child in value.values():
            validate_public_values(child)
    elif isinstance(value, list):
        for child in value:
            validate_public_values(child)
    elif isinstance(value, str):
        if _CREDENTIAL.search(value):
            raise ValueError('Credential-like value in public configuration')
    elif value is not None and (type(value) not in (int, float, bool)
                                or type(value) is float and not math.isfinite(value)):
        raise ValueError('Invalid public configuration value')
