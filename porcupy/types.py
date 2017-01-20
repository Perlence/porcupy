import ast
from inspect import signature

import attr

from .ast import Const, Slot, AssociatedSlot, BinOp, Add, Sub, Mult, FloorDiv, Assign, Call
from .functions import CallableType


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
    item_type = attr.ib()
    capacity = attr.ib()

    def get_pointer(self, converter, slot):
        return slot

    def getitem(self, converter, slot, slice_slot):
        # TODO: Implement negative indices
        capacity_slot = self.cap(converter, slot)
        if isinstance(slice_slot, Const) and isinstance(capacity_slot, Const):
            if slice_slot.value >= capacity_slot.value:
                raise IndexError('list index out of range')
        # TODO: Check list bounds in run-time
        if isinstance(slot, Const) and isinstance(slice_slot, Const):
            return converter.scope.get_by_index(slot.value + slice_slot.value, self.item_type)

        pointer_math_slot = item_addr(converter, slot, slice_slot)
        reference = AssociatedSlot(pointer_math_slot, ref=pointer_math_slot)
        item_slot = converter.scope.get_temporary(self.item_type)
        converter.append_to_body(Assign(item_slot, reference))
        converter.scope.recycle_temporary(pointer_math_slot)
        converter.recycle_later(item_slot)

        return item_slot

    def setitem(self, converter, slot, slice_slot):
        capacity_slot = self.cap(converter, slot)
        if isinstance(slice_slot, Const) and isinstance(capacity_slot, Const):
            if slice_slot.value >= capacity_slot.value:
                raise IndexError('list index out of range')

        if isinstance(self.item_type, GameObjectRef):
            item_slot = converter.scope.get_temporary(self.item_type)
            converter.append_to_body(Assign(item_slot, slot))
            converter.recycle_later(item_slot)
            return item_slot
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
class Slice:
    item_type = attr.ib()

    slot_methods = {'append'}

    def get_pointer(self, converter, slot):
        return slot.metadata['pointer']

    def getitem(self, converter, slot, slice_slot):
        ptr_slot = slot.metadata['pointer']
        return ListPointer.getitem(self, converter, ptr_slot, slice_slot)

    def setitem(self, converter, slot, slice_slot):
        ptr_slot = slot.metadata['pointer']
        return ListPointer.setitem(self, converter, ptr_slot, slice_slot)

    def len(self, converter, slot):
        return slot.metadata['length'][0]

    def cap(self, converter, slot):
        return slot.metadata['capacity'][0]

    def getattr(self, converter, slot, attr_name):
        attrib = getattr(self, attr_name)
        if attr_name in self.slot_methods:
            return Const(None, CallableType.from_function(attrib, slot))
        raise AttributeError("type object '{}' has no attribute '{}'".format(self, attr_name))

    def append(self, converter, slot, value):
        pointer = slot.metadata['pointer']
        len_slot, len_value = slot.metadata['length']
        _, cap_value = slot.metadata['capacity']

        if isinstance(len_value, Const) and isinstance(cap_value, Const):
            if len_value.value >= cap_value.value:
                raise IndexError('cannot append to a full slice')
        else:
            # TODO: Raise error in real-time
            pass

        tmp = converter.scope.get_temporary(IntType())
        new_item_ptr = converter.load_bin_op(BinOp(pointer, Add(), len_slot))
        converter.append_to_body(Assign(tmp, new_item_ptr))

        reference = AssociatedSlot(tmp, ref=tmp)
        converter.append_to_body(Assign(reference, value))
        converter.scope.recycle_temporary(tmp)

        converter.visit(ast.AugAssign(len_slot, ast.Add(), ast.Num(1)))

        slot.metadata['length'] = (len_slot, len_value)


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
        # TODO: If argument is game object attribute, e.g. 'e1f', then
        # store it in a temporary slot, because there's no short form
        # for 'e1f'
        self.signature.bind(None, *args)
        args = self._shorten_args(args)
        return Call(func, args)

    def _shorten_args(self, args):
        short_args = []
        for arg in args:
            if isinstance(arg, (Slot, AssociatedSlot)):
                arg = AssociatedSlot(arg, short_form=True)
            short_args.append(arg)
        return short_args
