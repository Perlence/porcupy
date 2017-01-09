import ast
from numbers import Number

import attr
import funcy

from . import runtime


def compile(source, filename='<unknown>'):
    top = ast.parse(source, filename)

    visitor = NodeVisitor()
    visitor.visit(top)
    return ' '.join(visitor.output)


@attr.s
class NodeVisitor(ast.NodeVisitor):
    scope = attr.ib(default=attr.Factory(lambda: Scope()))
    output = attr.ib(default=attr.Factory(list))
    loaded_values = attr.ib(default=attr.Factory(dict))

    def visit(self, node):
        try:
            return super().visit(node)
        except Exception as e:
            if not hasattr(node, 'lineno') or not hasattr(node, 'col_offset'):
                raise e
            line_col = 'line {}, column {}'.format(node.lineno, node.col_offset)
            if not str(e):
                msg = line_col
            else:
                msg = str(e) + '; ' + line_col
            raise type(e)(msg) from e

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, (ast.Tuple, ast.List)):
                raise NotImplementedError('iterable unpacking is not implemented yet')
            src_slot = self.load_cached_expr(node.value)
            dest_slot = self.store_value(target, src_slot)
            if dest_slot is not None:
                self.output_assign(dest_slot, src_slot)

    def visit_If(self, node):
        if isinstance(node.test, (ast.Num, ast.Str, ast.NameConstant, ast.List)):
            self.optimized_if(node)
        else:
            self.generic_if(node)

    def optimized_if(self, node):
        if isinstance(node.test, ast.Num) and not node.test.n:
            return
        elif isinstance(node.test, ast.Str) and not node.test.s:
            return
        elif isinstance(node.test, ast.NameConstant) and not node.test.value:
            return
        elif isinstance(node.test, ast.List) and not node.test.elts:
            return
        for body_node in node.body:
            self.visit(body_node)

    def generic_if(self, node):
        test_expr = self.load_expr(node.test)
        self.output.append('#')
        if isinstance(test_expr, BinOp):
            self.output += [str(test_expr), '!', '0']
        else:
            self.output.append(str(test_expr))
        self.output.append('(')
        for body_node in node.body:
            self.visit(body_node)
        self.output.append(')')

    def load_cached_expr(self, value):
        slot = self.loaded_values.get(value)
        if slot is None:
            slot = self.loaded_values[value] = self.load_expr(value)
        return slot

    def load_expr(self, value):
        if isinstance(value, ast.Num):
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
            return self.load_cached_expr(value.value)
        elif isinstance(value, ast.Compare):
            return self.load_compare(value)
        elif isinstance(value, ast.BoolOp):
            return self.load_bool_op(value)
        elif isinstance(value, ast.BinOp):
            return self.load_bin_op(value)
        elif isinstance(value, ast.UnaryOp):
            return self.load_unary_op(value)
        else:
            raise NotImplementedError("expression '{}' is not implemented yet".format(value))

    def load_list(self, value):
        loaded_items = map(self.load_cached_expr, value.elts)
        item_type = type_of_objects(loaded_items)
        if item_type is None:
            raise TypeError('list items must be of the same type')

        capacity = len(value.elts)
        item_slots = self.scope.allocate_many(item_type, capacity)
        for dest_slot, item in zip(item_slots, value.elts):
            src_slot = self.load_cached_expr(item)
            self.output_assign(dest_slot, src_slot)
        first_item = item_slots[0]
        metadata = {'capacity': capacity, 'item_type': item_type}
        return Const(first_item.number, ListPointer, metadata=metadata)

    def load_attribute(self, value):
        value_slot = self.load_cached_expr(value.value)
        if issubclass(value_slot.type, GameObjectRef):
            return self.load_game_obj_attr(value_slot, value.attr)
        else:
            raise NotImplementedError("getting attribute of object of type '{}' is not implemented yet".format(value.slot.type))

    def load_game_obj_attr(self, slot, attr_name):
        game_obj_type = slot.type.type
        register = game_obj_type._abbrev
        attrib = getattr(game_obj_type, attr_name)
        if slot.is_variable():
            slot = attr.assoc(slot, register=register, ref=True)
        return attr.assoc(slot, type=attrib.metadata['type'], attrib=attrib.metadata['abbrev'])

    def load_subscript(self, value):
        value_slot = self.load_cached_expr(value.value)
        slice_slot = self.load_cached_expr(value.slice)
        if isinstance(value_slot, GameObjectList):
            return self.load_game_obj_list_subscript(value_slot, slice_slot)
        elif issubclass(value_slot.type, ListPointer):
            return self.load_list_subscript(value_slot, slice_slot)
        else:
            raise NotImplementedError("getting item of collection of type '{}' is not implemented yet".format(value_slot.type))

    def load_game_obj_list_subscript(self, value_slot, slice_slot):
        register = value_slot.type._abbrev
        slot_type = GameObjectRef.type(value_slot.type)
        if isinstance(slice_slot, Const):
            return Slot(register, slice_slot.value, None, slot_type)
        else:
            return attr.assoc(slice_slot, type=slot_type)

    def load_list_subscript(self, value_slot, slice_slot):
        if isinstance(slice_slot, Const) and slice_slot.value >= value_slot.metadata['capacity']:
            raise IndexError('list index out of range')
        pointer_math_slot = self.scope.allocate(ListPointer)
        addition = BinOp(value_slot, ast.Add(), slice_slot, strict=False)
        self.output_assign(pointer_math_slot, addition)
        slot = attr.assoc(pointer_math_slot, type=value_slot.metadata['item_type'], ref=True)
        if issubclass(value_slot.metadata['item_type'], GameObjectRef):
            self.output_assign(pointer_math_slot, slot)
        self.scope.free(pointer_math_slot)
        return slot

    def load_compare(self, value):
        left = self.load_cached_expr(value.left)
        comparators = [self.load_cached_expr(comparator) for comparator in value.comparators]
        return Compare(left, value.ops, comparators)

    def load_bool_op(self, value):
        values = [self.load_cached_expr(bool_op_value) for bool_op_value in value.values]
        return BoolOp(value.op, values)

    def load_bin_op(self, value):
        left = self.load_cached_expr(value.left)
        right = self.load_cached_expr(value.right)
        return BinOp(left, value.op, right)

    def load_unary_op(self, value):
        operand = self.load_cached_expr(value.operand)
        if isinstance(value.op, ast.UAdd):
            return operand
        elif isinstance(value.op, ast.USub):
            if isinstance(operand, Const):
                return attr.assoc(operand, value=-operand.value)
            elif isinstance(operand, Slot):
                return attr.assoc(operand, usub=(not operand.usub))
            else:
                raise NotImplementedError("unary subtraction is not implemented for '{}' yet".format(operand))
        elif isinstance(value.op, ast.Invert):
            if isinstance(operand, Const):
                return attr.assoc(operand, value=~operand.value)
            else:
                return BinOp(Const(-1, Number), ast.Sub(), operand)
        else:
            raise NotImplementedError("unary operation '{}' is not implemented yet".format(value.op))

    def store_value(self, target, src_slot):
        if isinstance(target, ast.Name):
            if self.is_const(target):
                self.scope.define_const(target.id, src_slot)
            else:
                return self.scope.assign(target.id, src_slot)
        elif isinstance(target, ast.Attribute):
            return self.load_attribute(target)
        elif isinstance(target, ast.Subscript):
            return self.load_subscript(target)
        else:
            raise NotImplementedError("assigning values to '{}' is not implemented yet".format(target))

    def is_const(self, target):
        return target.id is not None and target.id.isupper()

    def output_assign(self, dest, value):
        self.output += [str(dest), str(value)]


@attr.s
class Scope:
    names = attr.ib(default=attr.Factory(dict))
    numeric_slots = attr.ib(default=attr.Factory(lambda: Slots(1)))
    string_slots = attr.ib(default=attr.Factory(lambda: Slots()))

    def __attrs_post_init__(self):
        self.populate_game_objects()

    def populate_game_objects(self):
        self.names['yegiks'] = GameObjectList(runtime.Yegik)
        self.names['points'] = GameObjectList(runtime.Point)
        self.names['bots'] = GameObjectList(runtime.Bot)
        self.names['timers'] = GameObjectList(runtime.Timer)
        self.names['system'] = Slot(runtime.System._abbrev, None, None, GameObjectRef.type(runtime.System))

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

    def allocate(self, type):
        if issubclass(type, Number):
            number = self.numeric_slots.allocate()
            return Slot('p', number, 'z', Number)
        elif issubclass(type, str):
            number = self.string_slots.allocate()
            return Slot('s', number, 'z', str)
        else:
            raise TypeError("cannot allocate slot of type '{}'".format(type))

    def allocate_many(self, type, length):
        return [self.allocate(type) for _ in range(length)]

    def free(self, slot):
        if issubclass(slot.type, Number):
            self.numeric_slots.free(slot.number)
        elif issubclass(slot.type, str):
            self.string_slots.free(slot.number)

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


RESERVED = object()


@attr.s
class Const:
    value = attr.ib()
    type = attr.ib()
    metadata = attr.ib(default=attr.Factory(dict))

    def __str__(self):
        if issubclass(self.type, bool):
            return str(int(self.value))
        elif issubclass(self.type, Number):
            return str(self.value).replace('.', ',')
        elif issubclass(self.type, str):
            return self.value.replace(' ', '_')
        else:
            raise TypeError("cannot format '{}' const".format(self.type))


@attr.s
class Slot:
    register = attr.ib()
    number = attr.ib()
    attrib = attr.ib()
    type = attr.ib()
    metadata = attr.ib(default=attr.Factory(dict))
    ref = attr.ib(default=False)
    usub = attr.ib(default=False)

    def is_variable(self):
        return self.register in ('p', 's')

    def __str__(self):
        if self.attrib is not None:
            return '{usub}{register}{ref}{number}{attrib}'.format(
                usub='-' if self.usub else '',
                register=self.register,
                ref='^' if self.ref else '',
                number=self.number if self.number is not None else '',
                attrib=self.attrib)
        else:
            return str(self.number)


class ListPointer(int):
    pass


class GameObjectRef(int):
    @staticmethod
    @funcy.memoize
    def type(game_obj_type):
        return type('GameObjectTypedRef', (GameObjectRef,), {'type': game_obj_type})


@attr.s
class GameObjectList:
    type = attr.ib()


@attr.s
class BoolOp:
    op = attr.ib()
    values = attr.ib()

    def __str__(self):
        result = []
        first, *rest = self.values
        result.append(str(first))
        for value in rest:
            result.append(self.translate_boolop(self.op))
            result.append(str(value))
        return ' '.join(result)

    def translate_boolop(self, op):
        if not isinstance(op, ast.boolop):
            raise SyntaxError("node '{}' is not a boolean operator".format(op))

        if isinstance(op, ast.And):
            return '&'
        elif isinstance(op, ast.Or):
            return '|'


@attr.s
class BinOp:
    left = attr.ib()
    op = attr.ib()
    right = attr.ib()
    strict = attr.ib(default=True)
    type = attr.ib(init=False)
    metadata = attr.ib(default=attr.Factory(dict))

    def __attrs_post_init__(self):
        if not self.strict:
            return
        self.type = type_of_objects([self.left, self.right])
        if self.type is None:
            raise TypeError("operands '{}' and '{}' are not of the same type".format(self.left, self.right))

    def __str__(self):
        return '{}{}{}'.format(self.left, self.translate_operator(self.op), self.right)

    def translate_operator(self, op):
        if not isinstance(op, ast.operator):
            raise SyntaxError("node '{}' is not a binary operator".format(op))

        if isinstance(op, ast.Add):
            return '+'
        elif isinstance(op, ast.Sub):
            return '-'
        elif isinstance(op, ast.Mult):
            return '*'
        elif isinstance(op, ast.Div):
            return '/'
        elif isinstance(op, ast.FloorDiv):
            return '{'
        elif isinstance(op, ast.Mod):
            return '}'
        else:
            raise NotImplementedError("operation '{}' is not implemented yet".format(op))


# @attr.s
# class UnaryOp:
#     op = attr.ib()
#     operand = attr.ib()

#     def __str__(self):
#         return '{}{}'.format(self.translate_unaryop(self.op), self.operand)

#     def translate_unaryop(self, op):
#         if isinstance(op, ast.UAdd):
#             return ''
#         elif isinstance(op, ast.USub):
#             return '-'
#         # elif isinstance(op, ast.Invert):
#         # elif isinstance(op, ast.Not):
#         else:
#             raise NotImplementedError("operation '{}' is not implemented yet".format(op))


@attr.s
class Compare:
    left = attr.ib()
    ops = attr.ib()
    comparators = attr.ib()

    def __str__(self):
        result = []
        left = self.left
        result.append(str(left))
        and_left = False
        for op, comparator in zip(self.ops, self.comparators):
            if and_left:
                result += ['&', str(left)]
            result.append(self.translate_cmpop(op))
            result.append(str(comparator))
            left = comparator
            and_left = True
        return ' '.join(result)

    def translate_cmpop(self, op):
        if not isinstance(op, ast.cmpop):
            raise SyntaxError("node '{}' is not a comparison operator".format(op))

        if isinstance(op, ast.Eq):
            return '='
        elif isinstance(op, ast.NotEq):
            return '!'
        elif isinstance(op, ast.Lt):
            return '<'
        elif isinstance(op, ast.LtE):
            return '<='
        elif isinstance(op, ast.Gt):
            return '>'
        elif isinstance(op, ast.GtE):
            return '>='


def type_of_objects(objects):
    type_set = set()
    for obj in objects:
        type_set.add(obj.type)
        if len(type_set) > 1:
            return
    if type_set:
        return next(iter(type_set))
