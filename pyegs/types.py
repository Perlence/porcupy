from inspect import signature

import funcy

from .ast import Const, Slot, AssociatedSlot, BinOp, Add, Sub, Mult, FloorDiv, Assign, Call


class ListPointer(int):
    @classmethod
    @funcy.memoize
    def of_type(cls, capacity, item_type):
        return type('TypedListPointer', (cls,), {'item_type': item_type, 'capacity': capacity})

    @classmethod
    def getitem(cls, converter, slot, slice_slot):
        if isinstance(slice_slot, Const) and slice_slot.value >= cls.capacity:
            raise IndexError('list index out of range')
        # TODO: Check list bounds in run-time
        if isinstance(slot, Const) and isinstance(slice_slot, Const):
            return converter.scope.get_by_index(slot.value + slice_slot.value, cls.item_type)

        pointer_math_slot = cls.item_index(converter, slot, slice_slot)
        reference = AssociatedSlot(pointer_math_slot, ref=pointer_math_slot)
        slot = converter.scope.get_temporary(cls.item_type)
        converter.append_to_body(Assign(slot, reference))
        converter.scope.recycle_temporary(pointer_math_slot)
        converter.recycle_later(slot)

        return slot

    @classmethod
    def setitem(cls, converter, slot, slice_slot):
        if isinstance(slot, Const):
            raise ValueError('cannot modify items of constant list pointer')
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
            return AssociatedSlot(pointer_math_slot, ref=pointer_math_slot)

    @classmethod
    def item_index(cls, converter, slot, slice_slot):
        pointer_math_slot = converter.scope.get_temporary(ListPointer)
        addition = converter.load_bin_op(BinOp(slot, Add(), slice_slot))
        converter.append_to_body(Assign(pointer_math_slot, addition))
        return pointer_math_slot

    @classmethod
    def len(cls, converter, slot):
        return Const(cls.capacity, int)

    @classmethod
    def cap(cls, converter, slot):
        return Const(cls.capacity, int)


class Slice(int):
    # TODO: Implement 'getitem' method
    # TODO: Implement 'append' method

    @classmethod
    def new(cls, lower, upper):
        metadata = {
            'lower': lower,
            'upper': upper,
        }
        return Const(None, cls, metadata=metadata)

    @classmethod
    def len(cls, converter, slot):
        return slot.metadata['length']

    @classmethod
    def cap(cls, converter, slot):
        return slot.metadata['capacity']


class Range:
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
        return converter.load_bin_op(BinOp(start, Add(), BinOp(step, Mult(), slice_slot)))

    @classmethod
    def call(cls, converter, func, *args):
        start_value, step_value = Const(0, int), Const(1, int)
        if len(args) == 1:
            stop_value = args[0]
        elif len(args) == 2:
            start_value, stop_value = args
        elif len(args) == 3:
            start_value, stop_value, step_value = args

        metadata = {
            'start': start_value,
            'stop': stop_value,
            'step': step_value,
        }
        return Const(None, cls, metadata=metadata)


class GameObjectList:
    # TODO: Implement GameObjectList iteration

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
            return Slot(register, slice_slot.value + cls.start, None, slot_type)
        else:
            temp = converter.scope.get_temporary(int)
            offset = converter.load_bin_op(BinOp(slice_slot, Add(), Const(cls.start, int)))
            converter.append_to_body(Assign(temp, offset))
            converter.recycle_later(temp)
            return AssociatedSlot(temp, type=slot_type)


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
            slot = AssociatedSlot(slot, register=register, ref=ref)

        metadata_stub = {**attrib.metadata}
        attrib_type = metadata_stub.pop('type')
        attrib_abbrev = metadata_stub.pop('abbrev')
        metadata = {**slot.metadata, **metadata_stub}

        return AssociatedSlot(slot, type=attrib_type, attrib=attrib_abbrev,
                              metadata=metadata)


class GameObjectMethod:
    @classmethod
    @funcy.memoize
    def with_signature(cls, fn):
        return type('SignedFunctionType', (cls,), {'signature': signature(fn)})

    @classmethod
    def call(cls, converter, func, *args):
        cls.signature.bind(None, *args)
        args = cls._shorten_args(args)
        return Call(func, args)

    @classmethod
    def _shorten_args(cls, args):
        short_args = []
        for arg in args:
            if isinstance(arg, Slot):
                arg = AssociatedSlot(arg, short_form=True)
            short_args.append(arg)
        return short_args


class Length:
    @classmethod
    def call(cls, converter, func, container):
        return container.type.len(converter, container)


class Capacity:
    @classmethod
    def call(cls, converter, func, container):
        return container.type.cap(converter, container)
