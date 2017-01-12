import ast
from numbers import Number

import attr

from .runtime import GameObjectRef, Yegik, Timer, Point, Bot, System


def compile(source, filename='<unknown>'):
    top = ast.parse(source, filename)

    converter = NodeConverter()
    converted_top = converter.visit(top)
    converter.scope.allocate_temporary()
    return str(converted_top)


@attr.s
class NodeConverter(ast.NodeVisitor):
    scope = attr.ib(default=attr.Factory(lambda: Scope()))
    bodies = attr.ib(default=attr.Factory(list))
    tests = attr.ib(default=attr.Factory(list))
    loaded_values = attr.ib(default=attr.Factory(dict))

    def visit(self, node):
        try:
            return super().visit(node)
        except Exception as e:
            try:
                lineno = node.lineno
                col_offset = node.col_offset
            except AttributeError:
                raise e
            old_msg = e.args[0]
            line_col = 'line {}, column {}'.format(lineno, col_offset)
            msg = old_msg + '; ' + line_col if old_msg else line_col
            e.args = (msg,) + e.args[1:]
            raise e

    def generic_visit(self, node):
        raise NotImplementedError("node '{}' is not implemented yet".format(node))

    def visit_Module(self, node):
        body = []
        self.bodies.append(body)
        for stmt in node.body:
            self.visit(stmt)
        return Module(body)

    def visit_Assign(self, node):
        # TODO: Reassign lists to list pointers without allocating more memory:
        # 'x = [11, 22]; x = [11, 22]' -> 'p1z 11 p2z 22 p4z 1 p1z 11 p2z 22'
        for target in node.targets:
            if isinstance(target, (ast.Tuple, ast.List)):
                # TODO: Implement iterable unpacking
                raise NotImplementedError('iterable unpacking is not implemented yet')
            src_slot = self.load_cached_expr(node.value)
            dest_slot = self.store_value(target, src_slot)
            if dest_slot is None:
                continue
            self.append_to_body(Assign(dest_slot, src_slot))

    def visit_AugAssign(self, node):
        # TODO: Raise NameError if target is not defined
        src_slot = self.load_cached_expr(node.value)
        dest_slot = self.store_value(node.target, src_slot)
        if dest_slot is None:
            return
        bin_op = BinOp(dest_slot, node.op, src_slot)
        self.append_to_body(Assign(dest_slot, bin_op))

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            expr = self.load_cached_expr(node.value)
            self.append_to_body(expr)
        else:
            raise NotImplementedError('plain expressions are not supported')

    def visit_If(self, node):
        if isinstance(node.test, (ast.Num, ast.Str, ast.NameConstant, ast.List)):
            self.optimized_if(node.test, node.body)
            if node.orelse:
                self.optimized_if(node.test, node.orelse, negate_test=True)
        else:
            self.generic_if(node)

    def optimized_if(self, test, body, negate_test=False):
        truthy = negate_test
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

    def generic_if(self, node):
        test = self.load_cached_expr(node.test)
        if not isinstance(test, Compare):
            test = Compare(test, ast.NotEq(), Const(False, bool))

        for stmt in self.prepare_if_stmt(test, node.body):
            self.visit(stmt)
        if node.orelse:
            for stmt in self.prepare_if_stmt(self.negate_bool(test), node.orelse):
                self.visit(stmt)

    def prepare_if_stmt(self, test, body):
        all_tests = test
        self.tests.append(test)
        if len(self.tests) > 1:
            all_tests = BoolOp(ast.And(), self.tests[:])

        previous_body = None
        if len(self.bodies) > 1:
            previous_body = self.bodies.pop()

        if_body = []
        self.append_to_body(If(all_tests, if_body))
        self.bodies.append(if_body)

        yield from body

        self.bodies.pop()

        if previous_body is not None:
            self.bodies.append(previous_body)

        self.tests.remove(test)

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
        loaded_items = [self.load_cached_expr(item) for item in value.elts]
        item_type = type_of_objects(loaded_items)
        if item_type is None:
            raise TypeError('list items must be of the same type')

        capacity = len(value.elts)
        item_slots = self.scope.allocate_many(item_type, capacity)
        for dest_slot, item in zip(item_slots, value.elts):
            src_slot = self.load_cached_expr(item)
            self.append_to_body(Assign(dest_slot, src_slot))
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
        register = value_slot.type.metadata['abbrev']
        slot_type = GameObjectRef.type(value_slot.type)
        if isinstance(slice_slot, Const):
            return Slot(register, slice_slot.value, None, slot_type)
        else:
            return attr.assoc(slice_slot, type=slot_type)

    def load_list_subscript(self, value_slot, slice_slot):
        # TODO: Optimize constant list subscription with constant index
        if isinstance(slice_slot, Const) and slice_slot.value >= value_slot.metadata['capacity']:
            raise IndexError('list index out of range')
        pointer_math_slot = self.scope.create_temporary(ListPointer)
        addition = BinOp(value_slot, ast.Add(), slice_slot)
        self.append_to_body(Assign(pointer_math_slot, addition))
        slot = attr.assoc(pointer_math_slot, type=value_slot.metadata['item_type'], ref=pointer_math_slot)
        if issubclass(value_slot.metadata['item_type'], GameObjectRef):
            self.append_to_body(Assign(pointer_math_slot, slot))
        return slot

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
                expr.values = [self.negate_bool(value) for value in expr.values]

        bool_slot = self.scope.create_temporary(bool)
        self.append_to_body(Assign(bool_slot, initial))
        body = [Assign(bool_slot, self.negate_bool(initial))]
        for stmt in self.prepare_if_stmt(expr, body):
            self.append_to_body(stmt)
        return bool_slot

    def load_compare(self, value):
        # TODO: Try to evaluate comparisons literally, e.g. 'x = 3 < 5' -> p1z 1
        left = self.load_cached_expr(value.left)
        comparators = [self.load_cached_expr(comparator) for comparator in value.comparators]

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
                slot = self.load_cached_expr(bool_op_value)
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
        # TODO: Try to evaluate binary operations literally
        # TODO: Initialize lists, e.g. 'x = [0] * 3'
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
            else:
                return BinOp(operand, ast.Mult(), Const(-1, Number))
        elif isinstance(value.op, ast.Invert):
            if isinstance(operand, Const):
                return attr.assoc(operand, value=~operand.value)
            else:
                return BinOp(BinOp(operand, ast.Mult(), Const(-1, Number)), ast.Sub(), Const(1, Number))
        else:
            raise NotImplementedError("unary operation '{}' is not implemented yet".format(value.op))

    def load_call(self, value):
        func = self.load_cached_expr(value.func)
        args = [self.load_cached_expr(arg) for arg in value.args]
        if value.keywords:
            raise NotImplementedError('function keywords are not implemented yet')
        func.type.signature.bind(None, *args)  # pass None as 'self' argument
        return Call(func, args)

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

    def is_const(self, target):
        return target.id is not None and target.id.isupper()

    def append_to_body(self, stmt):
        body = self.bodies[-1]
        body.append(stmt)


@attr.s
class Scope:
    names = attr.ib(default=attr.Factory(dict))
    numeric_slots = attr.ib(default=attr.Factory(lambda: Slots(start=1)))
    string_slots = attr.ib(default=attr.Factory(lambda: Slots()))
    temporary_slots = attr.ib(default=attr.Factory(list))

    def __attrs_post_init__(self):
        self.populate_game_objects()

    def populate_game_objects(self):
        self.names['yegiks'] = GameObjectList(Yegik)
        self.names['points'] = GameObjectList(Point)
        self.names['bots'] = GameObjectList(Bot)
        self.names['timers'] = GameObjectList(Timer)
        self.names['system'] = Slot(System.metadata['abbrev'], None, None, GameObjectRef.type(System))

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

    def create_temporary(self, type):
        if not issubclass(type, (Number, str)):
            raise TypeError("cannot create volatile slot of type '{}'".format(type))
        slot = Slot('p', None, 'z', type)
        self.temporary_slots.append(slot)
        return slot

    def allocate_temporary(self):
        for slot in self.temporary_slots:
            new_slot = self.allocate(slot.type)
            slot.number = new_slot.number

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


@attr.s
class Module:
    body = attr.ib()

    def __str__(self):
        return ' '.join(map(str, self.body))


@attr.s
class Assign:
    target = attr.ib()
    value = attr.ib()

    def __str__(self):
        return ' '.join([str(self.target), str(self.value)])


@attr.s
class If:
    test = attr.ib()
    body = attr.ib()

    def __str__(self):
        body = ' '.join(map(str, self.body))
        return '# {} ( {} )'.format(self.test, body)


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
    ref = attr.ib(default=None)

    def is_variable(self):
        return self.register in ('p', 's')

    def __str__(self):
        if self.attrib is not None:
            number = self.number
            if self.ref is not None:
                number = self.ref.number
            if number is None:
                number = ''
            return '{register}{ref}{number}{attrib}'.format(
                register=self.register,
                ref='^' if self.ref is not None else '',
                number=number,
                attrib=self.attrib)
        else:
            return str(self.number)


class ListPointer(int):
    pass


@attr.s
class GameObjectList:
    type = attr.ib()


@attr.s
class BoolOp:
    op = attr.ib()
    values = attr.ib()

    type = attr.ib(init=False)
    metadata = attr.ib(default=attr.Factory(dict))

    def __attrs_post_init__(self):
        self.type = bool

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

    type = attr.ib(init=False)
    metadata = attr.ib(default=attr.Factory(dict))

    def __attrs_post_init__(self):
        if issubclass(self.left.type, self.right.type):
            self.type = self.right.type
        elif issubclass(self.right.type, self.left.type):
            self.type = self.left.type
        else:
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


@attr.s
class Compare:
    left = attr.ib()
    op = attr.ib()
    right = attr.ib()

    type = attr.ib(init=False)
    metadata = attr.ib(default=attr.Factory(dict))

    def __attrs_post_init__(self):
        self.type = bool

    def __str__(self):
        return '{} {} {}'.format(self.left, self.translate_cmpop(self.op), self.right)

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


@attr.s
class Call:
    func = attr.ib()
    args = attr.ib()

    def __str__(self):
        result = [str(self.func)]
        if self.args:
            positional_args = ' '.join(map(str, self.args))
            result.append(positional_args)
        return ' '.join(result)
