from abc import ABCMeta, abstractmethod
import ast
from inspect import signature
import string
import _string
import types

import attr

from .ast import Const, Slot, AssociatedSlot, BinOp, Add, Sub, Div, FloorDiv, Mod, Assign, Call


@attr.s
class NumberType:
    def bin_op(self, converter, left, op, right):
        if isinstance(left, Const) and isinstance(right, Const) and not isinstance(op, Div):
            value = op(left.value, right.value)
            return Const(value)

        temp = []
        left, right = self._move_const_to_right(converter, left, op, right, temp)
        op, right = self._change_right_sign(op, right)
        left = self._store_temporary(converter, left, temp)
        right = self._store_temporary(converter, right, temp)
        converter.recycle_later(*temp)
        return BinOp(left, op, right)

    def _move_const_to_right(self, converter, left, op, right, temp):
        # 1 - x -> _tmp = 1; _tmp - x
        # 1 / x -> _tmp = 1; _tmp / x
        # 1 + x -> x + 1
        # 1 * x -> x * 1
        if isinstance(left, Const):
            if isinstance(op, (Sub, Div, FloorDiv, Mod)):
                left_slot = converter.scope.get_temporary(left.type)
                converter.append_to_body(Assign(left_slot, left))
                temp.append(left_slot)
                left = left_slot
            else:
                left, right = right, left
        return left, right

    def _change_right_sign(self, op, right):
        # x - (-5) -> x + 5
        # x + (-5) -> x - 5
        if isinstance(right, Const):
            if right.value < 0:
                if isinstance(op, Sub):
                    right.value = -right.value
                    op = Add()
                elif isinstance(op, Add):
                    right.value = -right.value
                    op = Sub()
        return op, right

    def _store_temporary(self, converter, value, temp):
        if not isinstance(value, (Const, Slot, AssociatedSlot)):
            value_slot = converter.scope.get_temporary(value.type)
            converter.append_to_body(Assign(value_slot, value))
            temp.append(value_slot)
            value = value_slot
        return value

    def unary_op(self, converter, op, operand):
        if isinstance(op, ast.UAdd):
            return operand
        elif isinstance(op, ast.USub):
            if isinstance(operand, Const):
                return attr.assoc(operand, value=-operand.value)
            return converter.visit(ast.BinOp(operand, ast.Mult(), Const(-1)))
        elif isinstance(op, ast.Invert):
            if isinstance(operand, Const):
                return attr.assoc(operand, value=~operand.value)
            return converter.visit(ast.BinOp(ast.BinOp(operand, ast.Mult(), Const(-1)), ast.Sub(), Const(1)))
        elif isinstance(op, ast.Not):
            if isinstance(operand, Const):
                return attr.assoc(operand, value=(not operand.value), type=BoolType())
            return converter.visit(ast.Compare(operand.type.truthy(converter, operand), [ast.Eq()], [Const(0)]))
        else:
            raise NotImplementedError("unary operation '{}' is not implemented yet".format(op))

    def truthy(self, converter, slot):
        return slot


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
    slot_methods = {'format'}

    def getattr(self, converter, slot, attr_name):
        attrib = getattr(self, attr_name)
        if attr_name in self.slot_methods:
            return Const(None, CallableType.from_function(attrib, slot))
        raise AttributeError("type object '{}' has no attribute '{}'".format(self, attr_name))

    def format(self, converter, slot, *args):
        if not isinstance(slot, Const):
            raise ValueError('cannot format a variable string')
        formatter = Formatter(converter)
        fmt_string = slot.value
        result = formatter.format(fmt_string, *args)
        return Const(result, self)


@attr.s
class Formatter(string.Formatter):
    converter = attr.ib()

    def vformat(self, fmt_string, args, kwargs):
        result = []
        tmp_slots = []
        for literal_text, field_name, _, _ in self.parse(fmt_string):
            result.append(literal_text)
            arg, _ = self.get_field(field_name, args, kwargs)
            short_arg = shorten_slot(self.converter, arg, tmp_slots)
            result.append(short_arg)
        self.converter.recycle_later(*tmp_slots)
        return result

    def parse(self, fmt_string):
        for i, (literal_text, field_name, format_spec, conversion) in enumerate(super().parse(fmt_string)):
            if format_spec:
                raise NotImplementedError('format specification is not implemented yet')
            if conversion:
                raise NotImplementedError('conversion is not implemented yet')

            if not self._arg_index_is_present(field_name):
                field_name = str(i) + field_name

            yield literal_text, field_name, format_spec, conversion

    def _arg_index_is_present(self, field_name):
        return field_name and field_name[0].isdigit()

    def get_field(self, field_name, args, kwargs):
        first, rest = _string.formatter_field_name_split(field_name)

        obj = self.get_value(first, args, kwargs)

        # loop through the rest of the field_name, doing
        # getattr or getitem as needed
        for is_attr, i in rest:
            if is_attr:
                # obj = getattr(obj, i)
                obj = self.converter.visit(ast.Attribute(obj, i, ast.Load()))
            else:
                # obj = obj[i]
                obj = self.converter.visit(ast.Subscript(obj, ast.Index(ast.Num(i)), ast.Load()))

        return obj, first


class Sequence(metaclass=ABCMeta):
    @abstractmethod
    def get_pointer(self, converter, slot):
        pass

    @abstractmethod
    def getitem(self, converter, slot, slice_slot):
        pass

    @abstractmethod
    def len(self, converter, slot):
        pass

    @abstractmethod
    def cap(self, converter, slot):
        pass


@attr.s
@Sequence.register
class ListPointer(IntType):
    item_type = attr.ib()
    capacity = attr.ib()

    def get_pointer(self, converter, slot):
        return slot

    def getitem(self, converter, slot, slice_slot):
        if isinstance(slice_slot, Const):
            if slice_slot.value >= self.capacity:
                raise IndexError('list index out of range')
            if isinstance(slot, Const):
                return converter.scope.get_by_index(slot.value + slice_slot.value, self.item_type)
        else:
            # TODO: Check list bounds in run-time
            pass

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

    def truthy(self, converter, slot):
        # Empty lists are not allowed, so each ListPointer instance is True
        return Const(True)


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
    addition = converter.visit(ast.BinOp(pointer, ast.Add(), offset))
    converter.append_to_body(Assign(pointer_math_slot, addition))
    return pointer_math_slot


@attr.s
@Sequence.register
class Slice(IntType):
    item_type = attr.ib()

    slot_methods = {'append'}

    def new(self, converter, pointer, length, capacity):
        # pointer * 16384 + length * 128 + capacity
        result = converter.visit(
            ast.BinOp(ast.BinOp(pointer, ast.Mult(), Const(16384)), ast.Add(),
                      ast.BinOp(ast.BinOp(length, ast.Mult(), Const(128)), ast.Add(),
                                capacity)))
        result.type = self
        return result

    def get_pointer(self, converter, slot):
        # slot // 16384
        return converter.visit(ast.BinOp(slot, ast.FloorDiv(), Const(16384)))

    def len(self, converter, slot):
        # slot // 128 % 128
        return converter.visit(ast.BinOp(ast.BinOp(slot, ast.FloorDiv(), Const(128)), ast.Mod(), Const(128)))

    def cap(self, converter, slot):
        # slot % 128
        return converter.visit(ast.BinOp(slot, ast.Mod(), Const(128)))

    def getitem(self, converter, slot, slice_slot):
        ptr_slot = self.get_pointer(converter, slot)
        return get_slot_via_offset(converter, ptr_slot, slice_slot, self.item_type)

    def setitem(self, converter, slot, slice_slot):
        ptr_slot = self.get_pointer(converter, slot)
        return ListPointer.setitem(self, converter, ptr_slot, slice_slot)

    def truthy(self, converter, slot):
        return self.len(converter, slot)

    def getattr(self, converter, slot, attr_name):
        attrib = getattr(self, attr_name)
        if attr_name in self.slot_methods:
            return Const(None, CallableType.from_function(attrib, slot))
        raise AttributeError("type object '{}' has no attribute '{}'".format(self, attr_name))

    def append(self, converter, slot, value):
        # TODO: Check type of *value*.
        pointer = self.get_pointer(converter, slot)
        length = self.len(converter, slot)
        # capacity = self.cap(converter, slot)

        # TODO: Raise an error if length equals capacity

        tmp = converter.scope.get_temporary(IntType())
        new_item_ptr = converter.visit(ast.BinOp(pointer, ast.Add(), length))
        converter.append_to_body(Assign(tmp, new_item_ptr))

        reference = AssociatedSlot(tmp, ref=tmp)
        converter.append_to_body(Assign(reference, value))
        converter.scope.recycle_temporary(tmp)

        # Increment length
        converter.visit(ast.AugAssign(slot, ast.Add(), ast.Num(128)))


@attr.s
@Sequence.register
class Range:
    # TODO: Pack range object into one slot
    def len(self, converter, slot):
        start = slot.metadata['start']
        stop = slot.metadata['stop']
        step = slot.metadata['step']
        return converter.visit(ast.BinOp(ast.BinOp(stop, ast.Sub(), start), ast.FloorDiv(), step))

    def getitem(self, converter, slot, slice_slot):
        # TODO: Raise error if index is greater than range length
        start = slot.metadata['start']
        step = slot.metadata['step']
        return converter.visit(ast.BinOp(start, ast.Add(), ast.BinOp(step, ast.Mult(), slice_slot)))

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


@attr.s
@Sequence.register
class Reversed:
    def call(self, converter, func, sequence):
        metadata = {
            'sequence': sequence,
        }
        return Const(None, self, metadata=metadata)

    def get_pointer(self, converter, slot):
        sequence = slot.metadata['sequence']
        return sequence.type.get_pointer(converter, sequence)

    def len(self, converter, slot):
        sequence = slot.metadata['sequence']
        return sequence.type.len(converter, sequence)

    def cap(self, converter, slot):
        sequence = slot.metadata['sequence']
        return sequence.type.cap(converter, sequence)

    def getitem(self, converter, slot, slice_slot):
        sequence = slot.metadata['sequence']
        length = self.len(converter, slot)
        reversed_index = converter.visit(ast.BinOp(ast.BinOp(length, ast.Sub(), Const(1)), ast.Sub(), slice_slot))
        return sequence.type.getitem(converter, sequence, reversed_index)


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
            offset = converter.visit(ast.BinOp(slice_slot, ast.Add(), Const(self.start)))
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


@attr.s
class CallableType:
    @classmethod
    def from_function(cls, func, instance=None):
        sig = signature(func)
        if instance is None:
            def call(self, converter, fn, *args):
                check_func_args(converter, sig, args)
                return func(converter, *args)
        else:
            def call(self, converter, fn, *args):
                args_with_instance = (instance, *args)
                check_func_args(converter, sig, args_with_instance)
                return func(converter, instance, *args)

        callable_type = cls()
        callable_type.call = types.MethodType(call, callable_type)
        return callable_type


@attr.s
class GameObjectMethod:
    fn = attr.ib()

    signature = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.signature = signature(self.fn)

    def call(self, converter, func, *args):
        check_func_args(converter, self.signature, args)
        args = shorten_func_args(converter, args)
        result = self.fn(converter, *args)
        if result is None:
            return Call(func, args)
        else:
            return result


def check_func_args(converter, signature, args):
    bound = signature.bind(converter, *args)
    for name, value in list(bound.arguments.items())[1:]:
        param = signature.parameters[name]
        if param.annotation is param.empty:
            continue
        if not are_types_related(value.type, param.annotation):
            raise TypeError('argument of type {} expected, got {}'.format(param.annotation, value))


def are_types_related(type_obj_1, type_2):
    type_1 = type(type_obj_1)
    return isinstance(type_obj_1, type_2) or issubclass(type_2, type_1)


def shorten_func_args(converter, args):
    tmp_slots = []
    short_args = [shorten_slot(converter, arg, tmp_slots) for arg in args]
    converter.recycle_later(*tmp_slots)
    return short_args


def shorten_slot(converter, slot, tmp_slots):
    if isinstance(slot, Const):
        return slot
    elif not isinstance(slot, (Slot, AssociatedSlot)) or not slot.is_variable():
        tmp_slot = converter.scope.get_temporary(slot.type)
        tmp_slots.append(tmp_slot)
        converter.append_to_body(Assign(tmp_slot, slot))
        slot = tmp_slot
    return AssociatedSlot(slot, short_form=True)
