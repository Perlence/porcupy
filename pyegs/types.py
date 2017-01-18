from inspect import signature

import attr

from .ast import Const, Slot, AssociatedSlot, BinOp, Add, Sub, Mult, FloorDiv, Assign, Call


@attr.s
class NumberType:
    pass


@attr.s
class FloatType(NumberType):
    pass


@attr.s
class IntType(NumberType):
    pass


@attr.s
class BoolType(IntType):
    pass


@attr.s
class StringType:
    pass


@attr.s
class ListPointer(NumberType):
    capacity = attr.ib()
    item_type = attr.ib()

    def getitem(self, converter, slot, slice_slot):
        capacity_slot = self.cap(converter, slot)
        if isinstance(slice_slot, Const) and isinstance(capacity_slot, Const):
            if slice_slot.value >= capacity_slot.value:
                raise IndexError('list index out of range')
        # TODO: Check list bounds in run-time
        if isinstance(slot, Const) and isinstance(slice_slot, Const):
            return converter.scope.get_by_index(slot.value + slice_slot.value, self.item_type)

        pointer_math_slot = item_addr(converter, slot, slice_slot)
        reference = AssociatedSlot(pointer_math_slot, ref=pointer_math_slot)
        slot = converter.scope.get_temporary(self.item_type)
        converter.append_to_body(Assign(slot, reference))
        converter.scope.recycle_temporary(pointer_math_slot)
        converter.recycle_later(slot)

        return slot

    def setitem(self, converter, slot, slice_slot):
        if isinstance(slot, Const):
            raise ValueError('cannot modify items of constant list pointer')
        if isinstance(slice_slot, Const) and slice_slot.value >= self.capacity:
            raise IndexError('list index out of range')

        if isinstance(self.item_type, GameObjectRef):
            slot = converter.scope.get_temporary(self.item_type)
            converter.append_to_body(Assign(slot, slot))
            converter.recycle_later(slot)
            return slot
        else:
            pointer_math_slot = item_addr(converter, slot, slice_slot)
            converter.recycle_later(pointer_math_slot)
            return AssociatedSlot(pointer_math_slot, ref=pointer_math_slot)

    def len(self, converter, slot):
        return Const(self.capacity)

    def cap(self, converter, slot):
        return Const(self.capacity)


def item_addr(converter, slot, index_slot):
    pointer_math_slot = converter.scope.get_temporary(IntType())
    addition = converter.load_bin_op(BinOp(slot, Add(), index_slot))
    converter.append_to_body(Assign(pointer_math_slot, addition))
    return pointer_math_slot


@attr.s
class Slice(IntType):
    # TODO: Implement 'getitem' method
    # TODO: Implement 'append' method

    item_type = attr.ib()

    def getitem(self, converter, slot, slice_slot):
        return ListPointer.getitem(self, converter, slot, slice_slot)

    def len(self, converter, slot):
        return slot.metadata['length']

    def cap(self, converter, slot):
        return slot.metadata['capacity']


@attr.s
class Range:
    def len(self, converter, slot):
        start = slot.metadata['start']
        stop = slot.metadata['stop']
        step = slot.metadata['step']
        return converter.load_bin_op(BinOp(BinOp(stop, Sub(), start), FloorDiv(), step))

    def getitem(self, converter, slot, slice_slot):
        # TODO: Raise error if index is greater than range length
        start = slot.metadata['start']
        step = slot.metadata['step']
        return converter.load_bin_op(BinOp(start, Add(), BinOp(step, Mult(), slice_slot)))

    def call(self, converter, func, *args):
        start_value, step_value = Const(0), Const(1)
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
        return Const(None, self, metadata=metadata)


@attr.s(init=False)
class GameObjectList:
    # TODO: Implement GameObjectList iteration
    type = attr.ib()
    start = attr.ib()
    stop = attr.ib()

    def __init__(self, game_obj_type, *args):
        self.type = game_obj_type

        self.start = 0
        if len(args) == 1:
            self.stop = args[0]
        elif len(args) == 2:
            self.start, self.stop = args

    def len(self, converter, slot):
        return Const(self.stop - self.start)

    def getitem(self, converter, value_slot, slice_slot):
        register = self.type.metadata['abbrev']
        slot_type = GameObjectRef(self.type)
        if isinstance(slice_slot, Const):
            return Slot(register, slice_slot.value + self.start, None, slot_type)
        else:
            temp = converter.scope.get_temporary(IntType())
            offset = converter.load_bin_op(BinOp(slice_slot, Add(), Const(self.start)))
            converter.append_to_body(Assign(temp, offset))
            converter.recycle_later(temp)
            return AssociatedSlot(temp, type=slot_type)


@attr.s
class GameObjectRef(NumberType):
    type = attr.ib()

    def getattr(self, converter, slot, attr_name):
        game_obj_type = self.type
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


@attr.s(init=False)
class GameObjectMethod:
    signature = attr.ib()

    def __init__(self, fn):
        self.signature = signature(fn)

    def call(self, converter, func, *args):
        self.signature.bind(None, *args)
        args = self._shorten_args(args)
        return Call(func, args)

    def _shorten_args(self, args):
        short_args = []
        for arg in args:
            if isinstance(arg, Slot):
                arg = AssociatedSlot(arg, short_form=True)
            short_args.append(arg)
        return short_args


@attr.s
class Length:
    def call(self, converter, func, container):
        return container.type.len(converter, container)


@attr.s
class Capacity:
    def call(self, converter, func, container):
        return container.type.cap(converter, container)
