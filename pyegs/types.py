from inspect import signature

import attr
import funcy

from .ast import Const


class ListPointer(int):
    @classmethod
    @funcy.memoize
    def of_type(cls, capacity, item_type):
        return type('TypedListPointer', (cls,), {'item_type': item_type, 'capacity': capacity})


@attr.s
class GameObjectList:
    type = attr.ib()


class GameObjectRef(int):
    @classmethod
    @funcy.memoize
    def of_type(cls, game_obj_type):
        return type('GameObjectTypedRef', (cls,), {'type': game_obj_type})


class GameObjectMethod:
    @classmethod
    @funcy.memoize
    def with_signature(cls, fn):
        return type('SignedFunctionType', (cls,), {'signature': signature(fn)})


@attr.s
class BuiltinFunction:
    func = attr.ib()


@attr.s(init=False)
class Range:
    range_ = attr.ib()

    def __init__(self, *args):
        if not all(isinstance(arg, Const) for arg in args):
            raise TypeError('range arguments must be constant')

        start, step = Const(0, int), Const(1, int)
        if len(args) == 1:
            stop = args[0]
        elif len(args) == 2:
            start, stop = args
        elif len(args) == 3:
            start, stop, step = args
        self.range_ = range(start.value, stop.value, step.value)

    def __iter__(self):
        for x in self.range_:
            yield Const(x, int)
