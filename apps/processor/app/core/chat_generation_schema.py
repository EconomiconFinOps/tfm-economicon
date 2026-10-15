"""Lossless schema spelling for providers that reject structured constants.

This does not drop validation keywords, merge response modes, repair answers or
change the public contract. A constant object becomes an exact closed object;
its keys and leaf values remain mandatory. Unsupported intersections fail closed.
"""
import copy


def _constant(value):
    if value is None:
        return {'type': 'null'}
    if type(value) in (str, bool, int, float):
        kind = {str: 'string', bool: 'boolean', int: 'integer', float: 'number'}[type(value)]
        return {'type': kind, 'enum': [value]}
    if isinstance(value, dict):
        if any(type(key) is not str for key in value):
            raise ValueError('Invalid schema constant.')
        return {'type': 'object', 'properties': {key: _constant(item) for key, item in value.items()},
                'required': list(value), 'additionalProperties': False}
    if isinstance(value, list):
        result = {'type': 'array', 'minItems': len(value), 'maxItems': len(value), 'items': False}
        if value:
            result['prefixItems'] = [_constant(item) for item in value]
        return result
    raise ValueError('Invalid schema constant.')


def expand_constants(schema):
    """Return an equivalent JSON Schema without object/array/scalar const.

    Visit schema positions only: an enum member or a literal property named
    ``const`` is data, never an instruction to transform another schema.
    """
    if type(schema) is bool:
        return schema
    if not isinstance(schema, dict):
        raise ValueError('Invalid generation schema.')
    result = copy.deepcopy(schema)
    if 'const' in result:
        value = result.pop('const')
        exact = _constant(value)
        if isinstance(value, (dict, list)):
            if set(result) - {'type', 'title', 'description'}:
                raise ValueError('Unsupported constant intersection.')
            if 'type' in result and result['type'] != exact['type']:
                raise ValueError('Incompatible constant type.')
            result = {**result, **exact}
        else:
            if 'enum' in result:
                # JSON Schema does not identify true with the number one.
                matches = [item for item in result['enum']
                           if type(item) is type(value) and item == value]
                if not matches:
                    raise ValueError('Incompatible constant enum.')
            result = {**exact, **result}
            if value is not None:
                result['enum'] = [value]
    for key in ('$defs', 'definitions', 'properties', 'patternProperties', 'dependentSchemas'):
        if key in result:
            result[key] = {name: expand_constants(item) for name, item in result[key].items()}
    for key in ('items', 'additionalProperties', 'contains', 'not', 'if', 'then', 'else', 'propertyNames'):
        if key in result:
            result[key] = expand_constants(result[key])
    for key in ('anyOf', 'oneOf', 'allOf', 'prefixItems'):
        if key in result:
            result[key] = [expand_constants(item) for item in result[key]]
    return result
