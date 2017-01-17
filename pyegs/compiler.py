import ast
from collections import defaultdict
from numbers import Number

import attr

from .ast import (AST, Module, Assign, If, Const, Slot, ShortSlot, BoolOp,
                  BinOp, operator, Add, Sub, Mult, Div, FloorDiv, Mod, Compare,
                  Label)
from .runtime import Yegik, Timer, Point, Bot, System
from .types import GameObjectRef, GameObjectList, ListPointer, Range


def compile(source, filename='<unknown>'):
    top = ast.parse(source, filename)

    converter = NodeConverter()
    converted_top = converter.visit(top)
    converter.scope.allocate_temporary()
    return str(converted_top)


@attr.s
class NodeConverter(ast.NodeVisitor):
    scope = attr.ib(default=attr.Factory(lambda: Scope()))
    body = attr.ib(default=attr.Factory(list))
    last_label = attr.ib(default=0)
    loop_labels = attr.ib(default=attr.Factory(list))
    current_node = attr.ib(default=None)
    slots_to_recycle_later = attr.ib(default=attr.Factory(lambda: defaultdict(list)))

    def visit(self, node):
        try:
            self.current_node = node
            result = super().visit(node)
            for slot in self.slots_to_recycle_later[node]:
                self.scope.recycle_temporary(slot)
            return result
        except Exception as e:
            if not hasattr(node, 'lineno') or not hasattr(node, 'col_offset'):
                raise
            self.annotate_node_position(e, node.lineno, node.col_offset)
            raise

    def annotate_node_position(self, exc, lineno, col_offset):
        old_msg, *rest_args = exc.args
        line_col = 'line {}, column {}'.format(lineno, col_offset)
        msg = old_msg + '; ' + line_col if old_msg else line_col
        exc.args = [msg] + rest_args
        return exc

    def generic_visit(self, node):
        raise NotImplementedError("node '{}' is not implemented yet".format(node))

    def visit_Module(self, node):
        for stmt in node.body:
            self.visit(stmt)
        return Module(self.body)

    def visit_Assign(self, node):
        # TODO: Reassign lists to list pointers without allocating more memory:
        # 'x = [11, 22]; x = [11, 22]' -> 'p1z 11 p2z 22 p4z 1 p1z 11 p2z 22'
        src_slot = None
        for target in node.targets:
            if isinstance(target, (ast.Tuple, ast.List)):
                # TODO: Implement iterable unpacking
                raise NotImplementedError('iterable unpacking is not implemented yet')
            if self.is_black_hole(target):
                continue
            if src_slot is None:
                src_slot = self.load_expr(node.value)
            dest_slot = self.store_value(target, src_slot)
            if dest_slot is None:
                continue
            self.append_to_body(Assign(dest_slot, src_slot))

    def visit_AugAssign(self, node):
        # TODO: Raise NameError if target is not defined
        src_slot = self.load_expr(node.value)
        dest_slot = self.store_value(node.target, src_slot)
        if dest_slot is None:
            return
        bin_op = self.load_bin_op(BinOp(dest_slot, self.load_bin_operator(node.op), src_slot))
        self.append_to_body(Assign(dest_slot, bin_op))

    def store_value(self, target, src_slot):
        if isinstance(target, ast.Name):
            if self.is_const(target):
                # TODO: Constant must not be redefined
                self.scope.define_const(target.id, src_slot)
            else:
                return self.scope.assign(target.id, src_slot)
        elif isinstance(target, ast.Attribute):
            return self.load_attribute(target)
        elif isinstance(target, ast.Subscript):
            return self.load_subscript(target)
        else:
            raise NotImplementedError("assigning values to '{}' is not implemented yet".format(target))

    def visit_For(self, node):
        # For(expr target, expr iter, stmt* body, stmt* orelse)
        if self.is_body_empty(node.body):
            return

        label_end = self.new_label()
        self.loop_labels.append((None, label_end))

        is_black_hole = self.is_black_hole(node.target)
        iter_slot = self.load_expr(node.iter)

        if not hasattr(iter_slot.type, 'iter'):
            raise NotImplementedError("iterating over '{}' is not implemented yet".format(iter_slot.type))

        iterable = iter_slot.type.iter(self, iter_slot, subscript=(not is_black_hole))

        for src_slot in iterable:
            if not is_black_hole:
                dest_slot = self.store_value(node.target, src_slot)
                self.append_to_body(Assign(dest_slot, src_slot))
            for stmt in node.body:
                self.visit(stmt)

        self.append_to_body(label_end)
        self.loop_labels.pop()

    def visit_Continue(self, node):
        label_start, _ = self.loop_labels[-1]
        goto_start = Slot('g', label_start.index, 'z', None)
        self.append_to_body(goto_start)

    def visit_Break(self, node):
        _, label_end = self.loop_labels[-1]
        goto_end = Slot('g', label_end.index, 'z', None)
        self.append_to_body(goto_end)

    def visit_Pass(self, node):
        pass

    def visit_While(self, node):
        # While(expr test, stmt* body, stmt* orelse)
        label_start = self.new_label()
        self.append_to_body(label_start)
        self.generic_if(node, label_start)
        self.loop_labels.pop()

    def visit_If(self, node):
        # If(expr test, stmt* body, stmt* orelse)
        if self.is_body_empty(node.body) and self.is_body_empty(node.orelse):
            return
        if isinstance(node.test, (ast.Num, ast.Str, ast.NameConstant, ast.List)):
            self.optimized_if(node.test, node.body)
            if node.orelse:
                self.optimized_if(node.test, node.orelse, negate_test=True)
        else:
            self.generic_if(node)

    def optimized_if(self, test, body, negate_test=False):
        truthy = negate_test
        if self.is_body_empty(body):
            return
        if isinstance(test, ast.Num) and bool(test.n) is truthy:
            return
        elif isinstance(test, ast.Str) and bool(test.s) is truthy:
            return
        elif isinstance(test, ast.NameConstant) and bool(test.value) is truthy:
            return
        elif isinstance(test, ast.List) and bool(test.elts) is truthy:
            return
        for stmt in body:
            self.visit(stmt)

    def generic_if(self, node, label_start=None):
        is_loop = label_start is not None

        test = self.load_expr(node.test)
        if not isinstance(test, Compare):
            test = Compare(test, ast.NotEq(), Const(False, bool))
        not_test = self.negate_bool(test)

        label_end = self.new_label()
        goto_end = Slot('g', label_end.index, 'z', None)
        if is_loop:
            self.loop_labels.append((label_start, label_end))

        label_else = None
        if not self.is_body_empty(node.orelse):
            label_else = self.new_label()
            goto_else = Slot('g', label_else.index, 'z', None)
            self.append_to_body(If(not_test, [goto_else]))
        else:
            self.append_to_body(If(not_test, [goto_end]))

        for stmt in node.body:
            self.visit(stmt)

        if is_loop:
            goto_start = Slot('g', label_start.index, 'z', None)
            self.append_to_body(goto_start)

        if label_else is not None:
            if not is_loop:
                self.append_to_body(goto_end)
            self.append_to_body(label_else)

            for stmt in node.orelse:
                self.visit(stmt)

        self.append_to_body(label_end)

    def new_label(self):
        self.last_label += 1
        if self.last_label > 99:
            raise ValueError('ran out of jump labels')
        return Label(self.last_label)

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            expr = self.load_expr(node.value)
            self.append_to_body(expr)
        else:
            raise NotImplementedError('plain expressions are not supported')

    def load_expr(self, value):
        if isinstance(value, AST):
            return value
        elif isinstance(value, ast.Num):
            return Const(value.n, Number)
        elif isinstance(value, ast.Str):
            return Const(value.s, str)
        elif isinstance(value, ast.NameConstant):
            return Const(value.value, type(value.value))
        elif isinstance(value, ast.List):
            return self.load_list(value)
        elif isinstance(value, ast.Name):
            return self.scope.get(value.id)
        elif isinstance(value, ast.Attribute):
            return self.load_attribute(value)
        elif isinstance(value, ast.Subscript):
            return self.load_subscript(value)
        elif isinstance(value, ast.Index):
            return self.load_expr(value.value)
        elif isinstance(value, (ast.Compare, ast.BoolOp)):
            return self.load_extended_bool_op(value)
        elif isinstance(value, ast.BinOp):
            return self.load_bin_op(value)
        elif isinstance(value, ast.UnaryOp):
            return self.load_unary_op(value)
        elif isinstance(value, ast.Call):
            return self.load_call(value)
        else:
            raise NotImplementedError("expression '{}' is not implemented yet".format(value))

    def load_list(self, value):
        loaded_items = [self.load_expr(item) for item in value.elts]
        item_type = self.type_of_objects(loaded_items)
        if item_type is None:
            raise TypeError('list items must be of the same type')

        capacity = len(value.elts)
        item_slots = self.scope.allocate_many(item_type, capacity)
        for dest_slot, item in zip(item_slots, loaded_items):
            self.append_to_body(Assign(dest_slot, item))
        first_item = item_slots[0]
        return Const(first_item.index, ListPointer.of_type(capacity, item_type))

    def type_of_objects(self, objects):
        type_set = set()
        for obj in objects:
            type_set.add(obj.type)
            if len(type_set) > 1:
                return
        if type_set:
            return next(iter(type_set))

    def load_attribute(self, value):
        value_slot = self.load_expr(value.value)
        if not hasattr(value_slot.type, 'getattr'):
            raise NotImplementedError("getting attribute of object of type '{}' is not implemented yet".format(value_slot.type))
        return value_slot.type.getattr(self, value_slot, value.attr)

    def load_subscript(self, value):
        value_slot = self.load_expr(value.value)
        slice_slot = self.load_expr(value.slice)

        if isinstance(value.ctx, ast.Load):
            if not hasattr(value_slot.type, 'getitem'):
                raise NotImplementedError("getting item of collection of type '{}' is not implemented yet".format(value_slot.type))

            return value_slot.type.getitem(self, value_slot, slice_slot)

        elif isinstance(value.ctx, ast.Store):
            if not hasattr(value_slot.type, 'setitem'):
                raise NotImplementedError("setting item of collection of type '{}' is not implemented yet".format(value_slot.type))
            return value_slot.type.setitem(self, value_slot, slice_slot)

    def load_extended_bool_op(self, value):
        initial = Const(False, bool)
        if isinstance(value, ast.Compare):
            expr = self.load_compare(value)
        elif isinstance(value, ast.BoolOp):
            # TODO: AND must return last value, OR must return first
            expr = self.load_bool_op(value)
            if isinstance(expr.op, ast.Or):
                initial = Const(True, bool)
                expr.op = ast.And()
                expr.values = list(map(self.negate_bool, expr.values))

        bool_slot = self.scope.get_temporary(bool)
        self.append_to_body(Assign(bool_slot, initial))
        assign = Assign(bool_slot, self.negate_bool(initial))
        self.append_to_body(If(expr, [assign]))
        self.recycle_later(bool_slot)
        return bool_slot

    def load_compare(self, value):
        # TODO: Try to evaluate comparisons literally, e.g. 'x = 3 < 5' -> p1z 1
        left = self.load_expr(value.left)
        comparators = [self.load_expr(comparator) for comparator in value.comparators]

        values = []
        for op, comparator in zip(value.ops, comparators):
            values.append(Compare(left, op, comparator))
            left = comparator
        if len(values) == 1:
            return values[0]
        else:
            return BoolOp(ast.And(), values)

    def load_bool_op(self, value):
        # TODO: Try to evaluate bool operations literally, e.g. 'y = x and False' -> 'p1z 0'
        values = []
        for bool_op_value in value.values:
            if isinstance(bool_op_value, ast.Compare):
                compare = self.load_compare(bool_op_value)
            else:
                slot = self.load_expr(bool_op_value)
                compare = Compare(slot, ast.NotEq(), Const(False, bool))
            values.append(compare)
        return BoolOp(value.op, values)

    def negate_bool(self, expr):
        if isinstance(expr, Const):
            return attr.assoc(expr, value=(not expr.value))
        elif isinstance(expr, Compare):
            op = expr.op
            if isinstance(op, ast.Eq):
                return attr.assoc(expr, op=ast.NotEq())
            elif isinstance(op, ast.NotEq):
                return attr.assoc(expr, op=ast.Eq())
            elif isinstance(op, ast.Lt):
                return attr.assoc(expr, op=ast.GtE())
            elif isinstance(op, ast.LtE):
                return attr.assoc(expr, op=ast.Gt())
            elif isinstance(op, ast.Gt):
                return attr.assoc(expr, op=ast.LtE())
            elif isinstance(op, ast.GtE):
                return attr.assoc(expr, op=ast.Lt())
        else:
            raise NotImplementedError("cannot invert expression '{}'".format(expr))

    def load_bin_op(self, value):
        # TODO: Initialize lists, e.g. 'x = [0] * 3'
        left = self.load_expr(value.left)
        op = self.load_bin_operator(value.op)
        right = self.load_expr(value.right)

        if isinstance(left, Const) and isinstance(right, Const):
            value = op(left.value, right.value)
            return Const(value, type(value))

        temp = []
        if isinstance(left, Const):
            if isinstance(op, (Sub, Div, FloorDiv, Mod)):
                left_slot = self.scope.get_temporary(left.type)
                self.append_to_body(Assign(left_slot, left))
                temp.append(left_slot)
                left = left_slot
            else:
                left, right = right, left

        if not isinstance(left, (Const, Slot)):
            left_slot = self.scope.get_temporary(left.type)
            self.append_to_body(Assign(left_slot, left))
            temp.append(left_slot)
            left = left_slot
        if not isinstance(right, (Const, Slot)):
            right_slot = self.scope.get_temporary(right.type)
            self.append_to_body(Assign(right_slot, right))
            temp.append(right_slot)
            right = right_slot

        self.recycle_later(*temp)

        return BinOp(left, op, right)

    def load_bin_operator(self, value):
        if isinstance(value, operator):
            return value
        if not isinstance(value, ast.operator):
            raise SyntaxError("node '{}' is not a binary operator".format(value))

        if isinstance(value, ast.Add):
            return Add()
        elif isinstance(value, ast.Sub):
            return Sub()
        elif isinstance(value, ast.Mult):
            return Mult()
        elif isinstance(value, ast.Div):
            return Div()
        elif isinstance(value, ast.FloorDiv):
            return FloorDiv()
        elif isinstance(value, ast.Mod):
            return Mod()
        else:
            raise NotImplementedError("operation '{}' is not implemented yet".format(value))

    def load_unary_op(self, value):
        operand = self.load_expr(value.operand)
        if isinstance(value.op, ast.UAdd):
            return operand
        elif isinstance(value.op, ast.USub):
            if isinstance(operand, Const):
                return attr.assoc(operand, value=-operand.value)
            else:
                return self.load_bin_op(BinOp(operand, Mult(), Const(-1, Number)))
        elif isinstance(value.op, ast.Invert):
            if isinstance(operand, Const):
                return attr.assoc(operand, value=~operand.value)
            else:
                return self.load_bin_op(BinOp(self.load_bin_op(BinOp(operand, Mult(), Const(-1, Number)), Sub(), Const(1, Number))))
        else:
            raise NotImplementedError("unary operation '{}' is not implemented yet".format(value.op))

    def load_call(self, value):
        if value.keywords:
            raise NotImplementedError('function keywords are not implemented yet')
        func = self.load_expr(value.func)
        args = [self.load_expr(arg) for arg in value.args]
        if not hasattr(func.type, 'call'):
            raise NotImplementedError("calling function '{}' is not implemented yet".format(func))
        return func.type.call(self, func, args)

    def append_to_body(self, stmt):
        self.body.append(stmt)

    def recycle_later(self, *slots):
        self.slots_to_recycle_later[self.current_node].extend(slots)

    def is_body_empty(self, body):
        return all(isinstance(stmt, ast.Pass) for stmt in body)

    def is_const(self, target):
        return target.id is not None and target.id.isupper()

    def is_black_hole(self, target):
        return isinstance(target, ast.Name) and target.id == '_'


@attr.s
class Scope:
    names = attr.ib(default=attr.Factory(dict))
    numeric_slots = attr.ib(default=attr.Factory(lambda: Slots(start=1)))
    string_slots = attr.ib(default=attr.Factory(lambda: Slots()))
    temporary_slots = attr.ib(default=attr.Factory(list))
    recycled_temporary_slots = attr.ib(default=attr.Factory(lambda: defaultdict(list)))

    def __attrs_post_init__(self):
        self.populate_builtins()
        self.populate_game_objects()

    def populate_builtins(self):
        self.names['range'] = Const(None, Range)

    def populate_game_objects(self):
        self.names['yegiks'] = Const(None, GameObjectList.of_type(Yegik, 1, 10))
        self.names['points'] = Const(None, GameObjectList.of_type(Point, 1, 100))
        self.names['bots'] = Const(None, GameObjectList.of_type(Bot, 1, 10))
        self.names['timers'] = Const(None, GameObjectList.of_type(Timer, 0, 100))
        self.names['system'] = Slot(System.metadata['abbrev'], None, None, GameObjectRef.of_type(System))

    def define_const(self, name, value):
        self.names[name] = value

    def assign(self, name, src_slot):
        slot = self.names.get(name)
        if slot is not None:
            # TODO: Check destination type
            return slot
        slot = self.allocate(src_slot.type)
        slot.type = src_slot.type
        slot.metadata = src_slot.metadata
        self.names[name] = slot
        return slot

    def get_by_index(self, index, type):
        if issubclass(type, Number):
            slots = self.numeric_slots.slots
            register = 'p'
        elif issubclass(type, str):
            slots = self.string_slots.slots
            register = 's'
        else:
            raise TypeError("cannot get slot of type '{}'".format(type))

        is_reserved = slots[index]
        if not is_reserved:
            raise IndexError("variable #{} is not reserved".format(index))
        return Slot(register, index, 'z', type)

    def allocate(self, type):
        if issubclass(type, Number):
            index = self.numeric_slots.allocate()
            return Slot('p', index, 'z', Number)
        elif issubclass(type, str):
            index = self.string_slots.allocate()
            return Slot('s', index, 'z', str)
        else:
            raise TypeError("cannot allocate slot of type '{}'".format(type))

    def allocate_many(self, type, length):
        return [self.allocate(type) for _ in range(length)]

    def get_temporary(self, type):
        if not issubclass(type, (Number, str)):
            raise TypeError("cannot create volatile slot of type '{}'".format(type))
        if self.recycled_temporary_slots[type]:
            return self.recycled_temporary_slots[type].pop()
        slot = Slot('p', None, 'z', type)
        self.temporary_slots.append(slot)
        return slot

    def recycle_temporary(self, slot):
        self.recycled_temporary_slots[slot.type].append(slot)

    def allocate_temporary(self):
        for slot in self.temporary_slots:
            new_slot = self.allocate(slot.type)
            slot.index = new_slot.index

    def get(self, name):
        slot = self.names.get(name)
        if slot is None:
            raise NameError("name '{}' is not defined".format(name))
        return slot


@attr.s
class Slots:
    start = attr.ib(default=0)
    stop = attr.ib(default=100)
    slots = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.slots = [None for x in range(self.start, self.stop)]

    def allocate(self):
        for addr, value in enumerate(self.slots):
            if value is None:
                self.slots[addr] = RESERVED
                return addr + self.start
        raise MemoryError('ran out of variable slots')

    def free(self, addr):
        self.slots[addr-self.start] = None

    def count_reserved(self):
        return len(slot for slot in self.slots if slot is RESERVED)


RESERVED = object()
