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


def _children(schema):
    if not isinstance(schema, dict):
        return
    for key in ('$defs', 'definitions', 'properties', 'patternProperties', 'dependentSchemas'):
        yield from schema.get(key, {}).values()
    for key in ('items', 'additionalProperties', 'contains', 'not', 'if', 'then', 'else', 'propertyNames'):
        if key in schema:
            yield schema[key]
    for key in ('anyOf', 'oneOf', 'allOf', 'prefixItems'):
        yield from schema.get(key, [])


def generation_schema(schema):
    """Equivalent constants and reachable definitions, without dead grammars.

    An array with maxItems zero has no item to constrain. Its unused item grammar
    must not make a provider compile financial/citation definitions that cannot
    occur in this response. Cross-field unions and every active constraint stay.
    Only local, root $defs references used by the generated contract are accepted.
    """
    result = expand_constants(schema)

    def simplify(node):
        if not isinstance(node, dict):
            return
        if any(key in node for key in ('$id', '$anchor', '$dynamicRef', '$recursiveRef')):
            raise ValueError('Unsupported generation reference scope.')
        if node.get('type') == 'array' and node.get('maxItems') == 0:
            node['items'] = {'type': 'string'}
            node.pop('prefixItems', None)
        for child in _children(node):
            simplify(child)

    simplify(result)
    if not isinstance(result, dict):
        return result
    definitions = result.pop('$defs', {})
    retained = {}

    def visit(node):
        if not isinstance(node, dict):
            return
        if '$ref' in node:
            ref = node['$ref']
            if not isinstance(ref, str) or not ref.startswith('#/$defs/') or '/' in ref[8:]:
                raise ValueError('Unsupported generation reference.')
            name = ref[8:].replace('~1', '/').replace('~0', '~')
            if name not in definitions:
                raise ValueError('Unknown generation reference.')
            if name not in retained:
                retained[name] = definitions[name]
                visit(definitions[name])
        for child in _children(node):
            visit(child)

    visit(result)
    if retained:
        result['$defs'] = {key: definitions[key] for key in definitions if key in retained}
    return result
