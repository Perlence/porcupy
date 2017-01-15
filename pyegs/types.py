from inspect import signature

import attr
import funcy

from .ast import Const, Slot, BinOp, Add, Assign, Call


class ListPointer(int):
    @classmethod
    @funcy.memoize
    def of_type(cls, capacity, item_type):
        return type('TypedListPointer', (cls,), {'item_type': item_type, 'capacity': capacity})

    @classmethod
    def getitem(cls, converter, slot, slice_slot, pointer_math_slot=None):
        # TODO: Optimize constant list subscription with constant index
        if isinstance(slice_slot, Const) and slice_slot.value >= cls.capacity:
            raise IndexError('list index out of range')
        if pointer_math_slot is None:
            pointer_math_slot = converter.scope.get_temporary(ListPointer)
        addition = converter.load_bin_op(BinOp(slot, Add(), slice_slot))
        converter.append_to_body(Assign(pointer_math_slot, addition))
        slot = attr.assoc(pointer_math_slot, type=cls.item_type, ref=pointer_math_slot)
        if issubclass(cls.item_type, GameObjectRef):
            converter.append_to_body(Assign(pointer_math_slot, slot))
        return slot

    @classmethod
    def iter(cls, converter, slot, subscript=True):
        if not subscript:
            yield from range(cls.capacity)
            return

        pointer_math_slot = converter.scope.get_temporary(ListPointer)
        for i in range(cls.capacity):
            yield cls.getitem(converter, slot, Const(i, int), pointer_math_slot)
        converter.scope.recycle_temporary(pointer_math_slot)


class Range(int):
    @classmethod
    def iter(cls, converter, slot, subscript=True):
        range_props = start, stop, step = slot.metadata['start'], slot.metadata['stop'], slot.metadata['step']
        if not all(isinstance(range_prop, Const) for range_prop in range_props):
            raise TypeError('only constant range can be iterated')

        for i in range(start.value, stop.value, step.value):
            yield Const(i, int)

    @classmethod
    def call(cls, converter, func, args):
        start_value, step_value = Const(0, int), Const(1, int)
        if len(args) == 1:
            stop_value = args[0]
        elif len(args) == 2:
            start_value, stop_value = args
        elif len(args) == 3:
            start_value, stop_value, step_value = args

        start_slot, stop_slot, step_slot = converter.scope.allocate_many(int, 3)
        converter.append_to_body(Assign(start_slot, start_value))
        converter.append_to_body(Assign(stop_slot, stop_value))
        converter.append_to_body(Assign(step_slot, step_value))

        metadata = {
            'start': start_value,
            'stop': stop_value,
            'step': step_value,
        }
        return Const(start_slot.number, Range, metadata=metadata)


class GameObjectList:
    # TODO: Implement 'iter' classmethod

    @classmethod
    @funcy.memoize
    def of_type(cls, game_obj_type, *args):
        start = 0
        if len(args) == 1:
            stop = args[0]
        elif len(args) == 2:
            start, stop = args

        return type('GameObjectTypedList', (cls,), {'type': game_obj_type, 'start': start, 'stop': stop})

    @classmethod
    def getitem(cls, converter, value_slot, slice_slot):
        register = cls.type.metadata['abbrev']
        slot_type = GameObjectRef.of_type(cls.type)
        if isinstance(slice_slot, Const):
            return Slot(register, slice_slot.value, None, slot_type)
        else:
            return attr.assoc(slice_slot, type=slot_type)


class GameObjectRef(int):
    @classmethod
    @funcy.memoize
    def of_type(cls, game_obj_type):
        return type('GameObjectTypedRef', (cls,), {'type': game_obj_type})

    @classmethod
    def getattr(cls, converter, slot, attr_name):
        game_obj_type = cls.type
        register = game_obj_type.metadata['abbrev']
        attrib = getattr(game_obj_type, attr_name)
        if slot.is_variable():
            ref = slot
            if slot.ref is not None:
                ref = slot.ref
            slot = attr.assoc(slot, register=register, ref=ref)

        metadata_stub = {**attrib.metadata}
        attrib_type = metadata_stub.pop('type')
        attrib_abbrev = metadata_stub.pop('abbrev')
        metadata = {**slot.metadata, **metadata_stub}

        return attr.assoc(slot, type=attrib_type, attrib=attrib_abbrev,
                          metadata=metadata)


class GameObjectMethod:
    @classmethod
    @funcy.memoize
    def with_signature(cls, fn):
        return type('SignedFunctionType', (cls,), {'signature': signature(fn)})

    @classmethod
    def call(cls, converter, func, args):
        cls.signature.bind(None, *args)
        return Call(func, args)
