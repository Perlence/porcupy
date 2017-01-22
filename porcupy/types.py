import ast
from inspect import signature

import attr

from .ast import Const, Slot, AssociatedSlot, BinOp, Add, Sub, Mult, Div, FloorDiv, Mod, Assign, Call
from .functions import CallableType


@attr.s
class NumberType:
    def bin_op(self, converter, left, op, right):
        # TODO: Implement bit shift operations
        if isinstance(left, BinOp):
            left = converter.load_bin_op(left)
        if isinstance(right, BinOp):
            right = converter.load_bin_op(right)

        if isinstance(left, Const) and isinstance(right, Const) and not isinstance(op, Div):
            value = op(left.value, right.value)
            return Const(value)

        temp = []
        if isinstance(left, Const):
            if isinstance(op, (Sub, Div, FloorDiv, Mod)):
                left_slot = converter.scope.get_temporary(left.type)
                converter.append_to_body(Assign(left_slot, left))
                temp.append(left_slot)
                left = left_slot
            else:
                left, right = right, left

        if not isinstance(left, (Const, Slot, AssociatedSlot)):
            left_slot = converter.scope.get_temporary(left.type)
            converter.append_to_body(Assign(left_slot, left))
            temp.append(left_slot)
            left = left_slot
        if not isinstance(right, (Const, Slot, AssociatedSlot)):
            right_slot = converter.scope.get_temporary(right.type)
            converter.append_to_body(Assign(right_slot, right))
            temp.append(right_slot)
            right = right_slot

        converter.recycle_later(*temp)

        return BinOp(left, op, right)

    def unary_op(self, converter, op, operand):
        if isinstance(op, ast.UAdd):
            return operand
        elif isinstance(op, ast.USub):
            if isinstance(operand, Const):
                return attr.assoc(operand, value=-operand.value)
            return converter.load_bin_op(BinOp(operand, Mult(), Const(-1)))
        elif isinstance(op, ast.Invert):
            if isinstance(operand, Const):
                return attr.assoc(operand, value=~operand.value)
            return converter.load_bin_op(BinOp(BinOp(operand, Mult(), Const(-1)), Sub(), Const(1)))
        elif isinstance(op, ast.Not):
            if isinstance(operand, Const):
                return attr.assoc(operand, value=(not operand.value), type=BoolType())
            return converter.load_expr(ast.Compare(operand, [ast.Eq()], [Const(0)]))
        else:
            # TODO: Implement 'not'
            raise NotImplementedError("unary operation '{}' is not implemented yet".format(op))


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
    # TODO: Initialize lists, e.g. 'x = [0] * 3'
    # TODO: Implement __bool__, so list can be used in test expression

    item_type = attr.ib()
    capacity = attr.ib()

    def get_pointer(self, converter, slot):
        return slot

    def getitem(self, converter, slot, slice_slot):
        if isinstance(slice_slot, Const) and slice_slot.value >= self.capacity:
            raise IndexError('list index out of range')
        # TODO: Check list bounds in run-time
        if isinstance(slot, Const) and isinstance(slice_slot, Const):
            return converter.scope.get_by_index(slot.value + slice_slot.value, self.item_type)

        return get_slot_via_offset(converter, slot, slice_slot, self.item_type)

    def setitem(self, converter, slot, slice_slot):
        capacity_slot = self.cap(converter, slot)
        if isinstance(slice_slot, Const) and isinstance(capacity_slot, Const):
            if slice_slot.value >= capacity_slot.value:
                raise IndexError('list index out of range')

        if isinstance(self.item_type, GameObject):
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


def get_slot_via_offset(converter, pointer, offset, type):
    pointer_math_slot = item_addr(converter, pointer, offset)
    reference = AssociatedSlot(pointer_math_slot, ref=pointer_math_slot)

    item_slot = converter.scope.get_temporary(type)
    converter.append_to_body(Assign(item_slot, reference))
    converter.scope.recycle_temporary(pointer_math_slot)
    converter.recycle_later(item_slot)

    return item_slot


def item_addr(converter, pointer, offset):
    pointer_math_slot = converter.scope.get_temporary(IntType())
    addition = converter.load_bin_op(BinOp(pointer, Add(), offset))
    converter.append_to_body(Assign(pointer_math_slot, addition))
    return pointer_math_slot


@attr.s
class Slice(IntType):
    item_type = attr.ib()

    slot_methods = {'append'}

    def new(self, converter, pointer, length, capacity):
        # pointer * 16384 + length * 128 + capacity
        result = converter.load_bin_op(
            BinOp(BinOp(pointer, Mult(), Const(16384)), Add(),
                  BinOp(BinOp(length, Mult(), Const(128)), Add(),
                        capacity)))
        result.type = self
        return result

    def get_pointer(self, converter, slot):
        # slot // 16384
        return converter.load_bin_op(BinOp(slot, FloorDiv(), Const(16384)))

    def len(self, converter, slot):
        # slot // 128 % 128
        return converter.load_bin_op(BinOp(BinOp(slot, FloorDiv(), Const(128)), Mod(), Const(128)))

    def cap(self, converter, slot):
        # slot % 128
        return converter.load_bin_op(BinOp(slot, Mod(), Const(128)))

    def getitem(self, converter, slot, slice_slot):
        ptr_slot = self.get_pointer(converter, slot)
        return get_slot_via_offset(converter, ptr_slot, slice_slot, self.item_type)

    def setitem(self, converter, slot, slice_slot):
        ptr_slot = self.get_pointer(converter, slot)
        return ListPointer.setitem(self, converter, ptr_slot, slice_slot)

    def getattr(self, converter, slot, attr_name):
        attrib = getattr(self, attr_name)
        if attr_name in self.slot_methods:
            return Const(None, CallableType.from_function(attrib, slot))
        raise AttributeError("type object '{}' has no attribute '{}'".format(self, attr_name))

    def append(self, converter, slot, value):
        pointer = self.get_pointer(converter, slot)
        length = self.len(converter, slot)
        # capacity = self.cap(converter, slot)

        # TODO: Raise an error if length equals capacity

        tmp = converter.scope.get_temporary(IntType())
        new_item_ptr = converter.load_bin_op(BinOp(pointer, Add(), length))
        converter.append_to_body(Assign(tmp, new_item_ptr))

        reference = AssociatedSlot(tmp, ref=tmp)
        converter.append_to_body(Assign(reference, value))
        converter.scope.recycle_temporary(tmp)

        # Increment length
        converter.visit(ast.AugAssign(slot, ast.Add(), ast.Num(128)))


@attr.s
class Range:
    # TODO: Pack range object into one slot
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


# TODO: Implement 'reversed' type


@attr.s(init=False)
class GameObjectList:
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
        if isinstance(slice_slot, Const):
            return Slot(register, slice_slot.value + self.start, None, self.type)
        else:
            temp = converter.scope.get_temporary(IntType())
            offset = converter.load_bin_op(BinOp(slice_slot, Add(), Const(self.start)))
            converter.append_to_body(Assign(temp, offset))
            converter.recycle_later(temp)
            return AssociatedSlot(temp, type=self.type)


@attr.s
class GameObject(IntType):
    def getattr(self, converter, slot, attr_name):
        register = self.metadata['abbrev']
        attrib = getattr(self, attr_name)
        if callable(attrib):
            attrib.metadata['type'] = GameObjectMethod(attrib)

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
        self.signature.bind(self, *args)
        args = self._shorten_args(converter, args)
        return Call(func, args)

    def _shorten_args(self, converter, args):
        short_args = []
        tmp_slots = []
        for arg in args:
            if isinstance(arg, (Slot, AssociatedSlot)):
                if not arg.is_variable():
                    tmp_slot = converter.scope.get_temporary(arg.type)
                    tmp_slots.append(tmp_slot)
                    converter.append_to_body(Assign(tmp_slot, arg))
                    arg = tmp_slot
                arg = AssociatedSlot(arg, short_form=True)
            short_args.append(arg)
        converter.recycle_later(*tmp_slots)
        return short_args
