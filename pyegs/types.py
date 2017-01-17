from inspect import signature

import attr
import funcy

from .ast import Const, Slot, BinOp, Add, Sub, Mult, FloorDiv, Assign, Call, ShortSlot


class ListPointer(int):
    @classmethod
    @funcy.memoize
    def of_type(cls, capacity, item_type):
        return type('TypedListPointer', (cls,), {'item_type': item_type, 'capacity': capacity})

    @classmethod
    def getitem(cls, converter, slot, slice_slot):
        if isinstance(slice_slot, Const) and slice_slot.value >= cls.capacity:
            raise IndexError('list index out of range')
        if isinstance(slot, Const) and isinstance(slice_slot, Const):
            return converter.scope.get_by_index(slot.value + slice_slot.value, cls.item_type)

        pointer_math_slot = cls.item_index(converter, slot, slice_slot)
        reference = attr.assoc(pointer_math_slot, ref=pointer_math_slot)
        slot = converter.scope.get_temporary(cls.item_type)
        converter.append_to_body(Assign(slot, reference))
        converter.scope.recycle_temporary(pointer_math_slot)
        converter.recycle_later(slot)

        return slot

    @classmethod
    def setitem(cls, converter, slot, slice_slot):
        # TODO: Optimize constant list subscription with constant index
        if isinstance(slice_slot, Const) and slice_slot.value >= cls.capacity:
            raise IndexError('list index out of range')

        if issubclass(cls.item_type, GameObjectRef):
            slot = converter.scope.get_temporary(cls.item_type)
            converter.append_to_body(Assign(slot, slot))
            converter.recycle_later(slot)
            return slot
        else:
            pointer_math_slot = cls.item_index(converter, slot, slice_slot)
            converter.recycle_later(pointer_math_slot)
            return attr.assoc(pointer_math_slot, ref=pointer_math_slot)

    @classmethod
    def item_index(cls, converter, slot, slice_slot):
        pointer_math_slot = converter.scope.get_temporary(ListPointer)
        addition = converter.load_bin_op(BinOp(slot, Add(), slice_slot))
        converter.append_to_body(Assign(pointer_math_slot, addition))
        return pointer_math_slot

    @classmethod
    def len(cls, converter, slot):
        return Const(cls.capacity, int)


class Range(int):
    @classmethod
    def len(cls, converter, slot):
        start = slot.metadata['start']
        stop = slot.metadata['stop']
        step = slot.metadata['step']
        return converter.load_bin_op(BinOp(BinOp(stop, Sub(), start), FloorDiv(), step))

    @classmethod
    def getitem(cls, converter, slot, slice_slot):
        # TODO: Raise error if index is greater than range length
        start = slot.metadata['start']
        step = slot.metadata['step']
        print(repr(start), repr(step))
        return converter.load_bin_op(BinOp(start, Add(), BinOp(step, Mult(), slice_slot)))

    @classmethod
    def call(cls, converter, func, args):
        # TODO: Range must be immutable
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
        return Const(start_slot.index, Range, metadata=metadata)


class GameObjectList:
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
    def len(cls, converter, slot):
        return Const(cls.stop - cls.start, int)

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
        args = cls._shorten_args(args)
        return Call(func, args)

    @classmethod
    def _shorten_args(cls, args):
        short_args = []
        for arg in args:
            if isinstance(arg, Slot):
                arg = ShortSlot(arg)
            short_args.append(arg)
        return short_args
