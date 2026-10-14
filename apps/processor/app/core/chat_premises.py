"""Three-valued decisions over premises bound by trusted server code.

This evaluator does not extract facts or establish entailment from prose. Its
caller must bind premises to the captured request or authorized evidence before
evaluation. Provider-supplied truth values must never be passed as bound facts.
Grounded numeric comparisons use this evaluator. Free-prose scenario binding
and recommendation rendering remain separate integration requirements.
"""
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class Premise:
    value: bool | None
    # References are opaque identities owned by the binder, not citation text.
    support: tuple[str, ...] = ()

    def __post_init__(self):
        if self.value is not None and type(self.value) is not bool:
            raise ValueError('Premise must be true, false or unknown.')
        if (type(self.support) is not tuple or len(self.support) > 20
                or any(type(x) is not str or not x or len(x) > 256 for x in self.support)
                or len(set(self.support)) != len(self.support)):
            raise ValueError('Invalid premise support.')
        if (self.value is None) != (not self.support):
            raise ValueError('Known premises require support; unknown is not negative evidence.')


@dataclass(frozen=True)
class Decision:
    value: bool | None
    # Keep every consulted premise, including unknowns when another condition
    # decides an AND/OR. A false conjunction does not make its operands false.
    premises: Mapping[str, Premise]

    @property
    def unknown(self):
        return tuple(key for key, premise in self.premises.items() if premise.value is None)

    @property
    def support(self):
        return tuple(dict.fromkeys(ref for premise in self.premises.values() for ref in premise.support))


def evaluate(expression, premises):
    """Evaluate a bounded server-owned tree with strong Kleene truth tables.

    Leaves are {'premise': id}; operators are {'not': child}, {'all': children}
    and {'any': children}. An absent identity is a binding error, not an unknown
    observation. Unknown observations must be registered explicitly by a binder.
    """
    if (not isinstance(premises, Mapping) or len(premises) > 64
            or any(type(k) is not str or not k or len(k) > 128 or type(v) is not Premise
                   for k, v in premises.items())):
        raise ValueError('Invalid bound premises.')
    snapshot = dict(premises)
    used = {}
    count = 0

    def visit(node, depth):
        nonlocal count
        count += 1
        if depth > 8 or count > 64 or type(node) is not dict or len(node) != 1:
            raise ValueError('Invalid or excessive decision tree.')
        operator, operand = next(iter(node.items()))
        if operator == 'premise':
            if type(operand) is not str or operand not in snapshot:
                raise ValueError('Unknown premise identity.')
            used[operand] = snapshot[operand]
            return snapshot[operand].value
        if operator == 'not':
            value = visit(operand, depth + 1)
            return None if value is None else not value
        if operator not in ('all', 'any') or type(operand) is not list or not 2 <= len(operand) <= 16:
            raise ValueError('Invalid decision operator.')
        # Validate every branch: short circuiting would hide malformed or
        # unsupported premises, and omit unknowns from the public rationale.
        values = [visit(child, depth + 1) for child in operand]
        decisive = False if operator == 'all' else True
        if any(value is decisive for value in values):
            return decisive
        return None if any(value is None for value in values) else not decisive

    value = visit(expression, 0)
    return Decision(value, MappingProxyType(used))
