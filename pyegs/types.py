from inspect import signature

import attr
import funcy


class ListPointer(int):
    @classmethod
    @funcy.memoize
    def of_type(cls, capacity, item_type):
        return type('TypedListPointer', (cls,), {'item_type': item_type, 'capacity': capacity})


class Range(int):
    pass


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
