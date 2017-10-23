from abc import ABCMeta, abstractmethod
import ast
from collections import ChainMap
from inspect import signature
import string
import _string
import types

import attr

from .ast import Const, Slot, EvolvedSlot, BinOp, Add, Sub, Div, FloorDiv, Mod, Call


@attr.s(hash=True)
class Type:
    def _getattr(self, converter, slot, attr_name):
        attrib = getattr(self, attr_name)
        if callable(attrib):
            return Const(None, CallableType.from_function(attrib, slot))
        raise AttributeError("type object '{}' has no attribute '{}'".format(self, attr_name))


@attr.s(hash=True)
class NumberType(Type):
    def _bin_op(self, converter, left, op, right):
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
                converter.append_assign(left_slot, left)
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
        if not isinstance(value, (Const, Slot, EvolvedSlot)):
            value_slot = converter.scope.get_temporary(value.type)
            converter.append_assign(value_slot, value)
            temp.append(value_slot)
            value = value_slot
        return value

    def _unary_op(self, converter, op, operand):
        if isinstance(op, ast.UAdd):
            return operand
        elif isinstance(op, ast.USub):
            if isinstance(operand, Const):
                return attr.evolve(operand, value=-operand.value)
            return converter.visit(ast.BinOp(operand, ast.Mult(), Const(-1)))
        elif isinstance(op, ast.Invert):
            if isinstance(operand, Const):
                return attr.evolve(operand, value=~operand.value)
            return converter.visit(ast.BinOp(ast.BinOp(operand, ast.Mult(), Const(-1)), ast.Sub(), Const(1)))
        elif isinstance(op, ast.Not):
            if isinstance(operand, Const):
                return attr.evolve(operand, value=(not operand.value), type=BoolType())
            return converter.visit(ast.Compare(operand.type._truthy(converter, operand), [ast.Eq()], [Const(0)]))
        else:
            raise NotImplementedError("unary operation '{}' is not implemented yet".format(op))

    def _truthy(self, converter, slot):
        return slot


@attr.s(hash=True)
class FloatType(NumberType):
    pass


@attr.s(hash=True)
class IntType(NumberType):
    pass


@attr.s(hash=True)
class BoolType(IntType):
    pass


@attr.s(hash=True)
class StringType(Type):
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
            if field_name is None:
                continue
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

            if field_name is not None and not self._arg_index_is_present(field_name):
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
    def _getptr(self, converter, slot):
        pass

    @abstractmethod
    def _getitem(self, converter, slot, slice_slot):
        pass

    @abstractmethod
    def _len(self, converter, slot):
        pass

    @abstractmethod
    def _cap(self, converter, slot):
        pass


@attr.s(hash=True)
@Sequence.register
class ListPointer(IntType):
    item_type = attr.ib()
    capacity = attr.ib()

    def _getptr(self, converter, slot):
        return slot

    def _getitem(self, converter, slot, slice_slot):
        if isinstance(slice_slot, Const):
            if slice_slot.value >= self.capacity:
                raise IndexError('list index out of range')
            if isinstance(slot, Const):
                return converter.scope.get_by_index(slot.value + slice_slot.value, self.item_type)
        else:
            # TODO: Check list bounds in run-time
            pass

        return get_slot_via_offset(converter, slot, slice_slot, self.item_type)

    def _setitem(self, converter, slot, slice_slot):
        if isinstance(slice_slot, Const):
            try:
                capacity = self.capacity
            except AttributeError:
                # TODO: Check sequence bounds in run-time
                pass
            else:
                if slice_slot.value >= capacity:
                    raise IndexError('list index out of range')

        if isinstance(self.item_type, GameObject):
            item_slot = converter.scope.get_temporary(self.item_type)
            converter.append_assign(item_slot, slot)
            converter.recycle_later(item_slot)
            return item_slot
        else:
            pointer_math_slot = item_addr(converter, slot, slice_slot)
            converter.recycle_later(pointer_math_slot)
            return EvolvedSlot(pointer_math_slot, type=self.item_type, ref=True)

    def _len(self, converter, slot):
        return Const(self.capacity)

    def _cap(self, converter, slot):
        return Const(self.capacity)

    def _truthy(self, converter, slot):
        # Empty lists are not allowed, so each ListPointer instance is True
        return Const(True)


def get_slot_via_offset(converter, pointer, offset, type):
    pointer_math_slot = item_addr(converter, pointer, offset)
    reference = EvolvedSlot(pointer_math_slot, type=type, ref=True)

    item_slot = converter.scope.get_temporary(type)
    converter.append_assign(item_slot, reference)
    converter.scope.recycle_temporary(pointer_math_slot)
    converter.recycle_later(item_slot)

    return item_slot


def item_addr(converter, pointer, offset):
    pointer_math_slot = converter.scope.get_temporary(pointer.type)
    addition = converter.visit(ast.BinOp(pointer, ast.Add(), offset))
    addition.type = pointer.type
    converter.append_assign(pointer_math_slot, addition)
    return pointer_math_slot


@attr.s(hash=True)
@Sequence.register
class Slice(IntType):
    item_type = attr.ib()

    slot_methods = {'append'}

    def _new(self, converter, pointer, length, capacity):
        # pointer * 10000 + capacity * 100 + length
        result = converter.visit(
            ast.BinOp(ast.BinOp(pointer, ast.Mult(), Const(10000)), ast.Add(),
                      ast.BinOp(ast.BinOp(capacity, ast.Mult(), Const(100)), ast.Add(),
                                length)))
        result.type = self
        return result

    def _getptr(self, converter, slot):
        # slot // 10000
        return converter.visit(ast.BinOp(slot, ast.FloorDiv(), Const(10000)))

    def _cap(self, converter, slot):
        # slot // 100 % 100
        return converter.visit(ast.BinOp(ast.BinOp(slot, ast.FloorDiv(), Const(100)), ast.Mod(), Const(100)))

    def _len(self, converter, slot):
        # slot % 100
        return converter.visit(ast.BinOp(slot, ast.Mod(), Const(100)))

    def _getitem(self, converter, slot, slice_slot):
        ptr_slot = self._getptr(converter, slot)
        return get_slot_via_offset(converter, ptr_slot, slice_slot, self.item_type)

    def _setitem(self, converter, slot, slice_slot):
        ptr_slot = self._getptr(converter, slot)
        return ListPointer._setitem(self, converter, ptr_slot, slice_slot)

    def _truthy(self, converter, slot):
        return self._len(converter, slot)

    def append(self, converter, slot, value):
        # TODO: Check type of *value*.
        pointer = self._getptr(converter, slot)
        length = self._len(converter, slot)
        # capacity = self._cap(converter, slot)

        # TODO: Raise an error if length equals capacity

        tmp = converter.scope.get_temporary(pointer.type)
        new_item_ptr = converter.visit(ast.BinOp(pointer, ast.Add(), length))
        new_item_ptr.type = pointer.type
        converter.append_assign(tmp, new_item_ptr)

        reference = EvolvedSlot(tmp, type=self.item_type, ref=True)
        converter.append_assign(reference, value)
        converter.scope.recycle_temporary(tmp)

        # Increment length
        converter.visit(ast.AugAssign(slot, ast.Add(), ast.Num(1)))


@attr.s(hash=True)
@Sequence.register
class Range(Type):
    def _len(self, converter, slot):
        start = slot.metadata['start']
        stop = slot.metadata['stop']
        step = slot.metadata['step']
        return converter.visit(ast.BinOp(ast.BinOp(stop, ast.Sub(), start), ast.FloorDiv(), step))

    def _getitem(self, converter, slot, slice_slot):
        # TODO: Raise error if index is greater than range length
        start = slot.metadata['start']
        step = slot.metadata['step']
        return converter.visit(ast.BinOp(start, ast.Add(), ast.BinOp(step, ast.Mult(), slice_slot)))

    def _call(self, converter, func, *args):
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


@attr.s(hash=True)
@Sequence.register
class Reversed(Type):
    def _call(self, converter, func, sequence):
        metadata = {
            'sequence': sequence,
        }
        return Const(None, self, metadata=metadata)

    def _getptr(self, converter, slot):
        sequence = slot.metadata['sequence']
        return sequence.type._getptr(converter, sequence)

    def _len(self, converter, slot):
        sequence = slot.metadata['sequence']
        return sequence.type._len(converter, sequence)

    def _cap(self, converter, slot):
        sequence = slot.metadata['sequence']
        return sequence.type._cap(converter, sequence)

    def _getitem(self, converter, slot, slice_slot):
        sequence = slot.metadata['sequence']
        length = self._len(converter, slot)
        reversed_index = converter.visit(ast.BinOp(ast.BinOp(length, ast.Sub(), Const(1)), ast.Sub(), slice_slot))
        return sequence.type._getitem(converter, sequence, reversed_index)


@attr.s(init=False, hash=True)
class GameObjectList(Type):
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

    def _len(self, converter, slot):
        return Const(self.stop - self.start)

    def _getitem(self, converter, value_slot, slice_slot):
        register = self.type.metadata['abbrev']
        if isinstance(slice_slot, Const):
            return Slot(register, slice_slot.value + self.start, None, self.type)
        else:
            temp = converter.scope.get_temporary(IntType())
            offset = converter.visit(ast.BinOp(slice_slot, ast.Add(), Const(self.start)))
            converter.append_assign(temp, offset)
            converter.recycle_later(temp)
            return EvolvedSlot(temp, type=self.type)


@attr.s(hash=True)
class GameObject(IntType):
    def _getattr(self, converter, slot, attr_name):
        register = self.metadata['abbrev']
        attrib = getattr(self, attr_name)
        if callable(attrib):
            attrib.metadata['type'] = GameObjectMethod(attrib)

        if slot.is_variable():
            slot = EvolvedSlot(slot, register=register, ref=True)

        metadata_stub = dict(**attrib.metadata)
        attrib_type = metadata_stub.pop('type')
        attrib_abbrev = metadata_stub.pop('abbrev')
        metadata = ChainMap(metadata_stub, slot.metadata)

        return EvolvedSlot(slot, type=attrib_type, attrib=attrib_abbrev,
                           metadata=metadata)


@attr.s(hash=True)
class CallableType(Type):
    @classmethod
    def from_function(cls, func, instance=None):
        sig = signature(func)
        if instance is None:
            def _call(self, converter, fn, *args):
                check_func_args(converter, sig, args)
                return func(converter, *args)
        else:
            def _call(self, converter, fn, *args):
                args_with_instance = (instance, *args)
                check_func_args(converter, sig, args_with_instance)
                return func(converter, instance, *args)

        callable_type = cls()
        callable_type._call = types.MethodType(_call, callable_type)
        return callable_type


@attr.s(hash=True)
class GameObjectMethod(Type):
    fn = attr.ib()

    signature = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.signature = signature(self.fn)

    def _call(self, converter, func, *args):
        check_func_args(converter, self.signature, args)
        args = shorten_func_args(converter, args)
        result = self.fn(converter, *args)
        if result is None:
            return Call(func, args)
        else:
            return result


def check_type(dest_slot, src_slot):
    dest_type_obj = dest_slot.type
    dest_type = type(dest_type_obj)
    src_type_obj = src_slot.type
    src_type = type(src_type_obj)

    have_different_fields = (attr.fields(src_type) or attr.fields(dest_type)) and src_type_obj != dest_type_obj
    if not are_types_related(src_type_obj, dest_type) or have_different_fields:
        raise TypeError("cannot assign value of type '{!r}' to variable of type '{!r}'"
                        .format(src_type_obj, dest_type_obj))


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
    elif not isinstance(slot, (Slot, EvolvedSlot)) or not slot.is_variable():
        tmp_slot = converter.scope.get_temporary(slot.type)
        tmp_slots.append(tmp_slot)
        converter.append_assign(tmp_slot, slot)
        slot = tmp_slot
    return EvolvedSlot(slot, short_form=True)
