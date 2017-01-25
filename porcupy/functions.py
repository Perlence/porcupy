import ast
import types

import attr

from .ast import Const, Random, Assign


@attr.s
class CallableType:
    @classmethod
    def from_function(cls, func, instance=None):
        if instance is None:
            def call(self, converter, fn, *args):
                return func(converter, *args)
        else:
            def call(self, converter, fn, *args):
                return func(converter, instance, *args)

        callable_type = cls()
        callable_type.call = types.MethodType(call, callable_type)
        return callable_type


def length(converter, sequence):
    return sequence.type.len(converter, sequence)


def capacity(converter, sequence):
    return sequence.type.cap(converter, sequence)


def slice(converter, type_slot, length, capacity=None):
    from .types import IntType, FloatType, BoolType

    if capacity is None:
        capacity = length

    if not isinstance(capacity, Const):
        raise ValueError('slice capacity must be constant')

    if isinstance(type_slot.type, IntType):
        item = ast.Num(0)
    elif isinstance(type_slot.type, FloatType):
        item = ast.Num(0.0)
    elif isinstance(type_slot.type, BoolType):
        item = ast.NameConstant(False)
    else:
        raise TypeError('cannot create slice of type {}'.format(type_slot.type))

    return converter.visit(ast.Subscript(ast.List([item] * capacity.value, ast.Load()),
                                         ast.Slice(None, length, None), ast.Load()))


def randint(converter, a, b):
    from .types import IntType

    if not isinstance(a, Const) or not isinstance(b, Const):
        raise ValueError('arguments must be constant')

    if a.value > b.value:
        raise ValueError('left random boundary must not be greater than right')

    if a.value == 0:
        return Random(b.value + 1)
    else:
        tmp = converter.scope.get_temporary(IntType())
        converter.recycle_later(tmp)
        converter.append_to_body(Assign(tmp, Random(abs(b.value - a.value) + 1)))
        return converter.visit(ast.BinOp(tmp, ast.Add(), a))
