import ast
from numbers import Number

import attr

# from . import runtime as rt


def compile(source, filename='<unknown>'):
    top = ast.parse(source, filename)

    visitor = NodeVisitor()
    visitor.visit(top)
    return visitor.output.strip()


@attr.s
class NodeVisitor(ast.NodeVisitor):
    scope = attr.ib(default=attr.Factory(lambda: Scope()))
    output = attr.ib(default='')

    def visit_Assign(self, node, slot=None):
        for target in node.targets:
            if isinstance(target, ast.Tuple):
                raise NotImplementedError('iterable destruction is not implemented yet')

            if isinstance(node.value, ast.Num):
                self.assign_num(target, node.value, slot)
            elif isinstance(node.value, ast.Str):
                self.assign_str(target, node.value, slot)
            elif isinstance(node.value, ast.Name):
                self.assign_name(target, node.value, slot)
            elif isinstance(node.value, ast.UnaryOp):
                raise NotImplementedError('assigning unary operations is not implemented yet')
            elif isinstance(node.value, ast.BinOp):
                raise NotImplementedError('assigning binary operations is not implemented yet')
            elif isinstance(node.value, ast.Tuple):
                self.assign_tuple(target, node.value, slot)
            else:
                raise NotImplementedError("unable to assign the value '{}'".format(node.value))

    def assign_num(self, target, value, slot):
        if self.is_const(target):
            self.scope.define_const(target.id, value.n)
            return
        type = Number
        if slot is None:
            slot = self.scope.define(target.id, type)
        value = format_number(value.n)
        self.output_assign(slot, value)

    def assign_str(self, target, value, slot):
        if self.is_const(target):
            self.scope.define_const(target.id, value.s)
            return
        type = str
        if slot is None:
            slot = self.scope.define(target.id, type)
        value = format_string(value.s)
        self.output_assign(slot, value)

    def is_const(self, target):
        return target.id is not None and target.id.isupper()

    def assign_name(self, target, value, dest_slot):
        src_slot = self.scope.get(value.id)
        if dest_slot is None:
            dest_slot = self.scope.define(target.id, src_slot.type())
        self.output_assign(dest_slot, src_slot)

    def assign_call(self, target, value, slot):
        if value.func.id == 'const':
            self.assign_const(target, value)
        else:
            raise NotImplementedError('functions are not implemented yet')

    def assign_const(self, target, call):
        const_arg = call.args[0]
        self.scope.define_const(target.id, const_arg)

    def assign_tuple(self, target, value, slot):
        tuple_type = self.type_of_items(value.elts)
        if tuple_type is None:
            raise TypeError('tuple items must be of the same type')

        if slot is None:
            tuple_pointer = self.scope.define(target.id, tuple)
        else:
            tuple_pointer = slot
        slots = self.scope.allocate_many(tuple_type, len(value.elts))
        first_item = slots[0]
        self.output_assign(tuple_pointer, first_item.slot_number)
        for dest, src in zip(slots, value.elts):
            target = ast.Name(id=None)
            assign = ast.Assign(targets=[target], value=src)
            self.visit_Assign(assign, slot=dest)

    def type_of_items(self, items):
        type_set = set()
        for item in items:
            if isinstance(item, ast.Num):
                type_set.add(Number)
            elif isinstance(item, ast.Str):
                type_set.add(str)
            elif isinstance(item, ast.Name):
                slot = self.scope.get(item.id)
                type_set.add(slot.type())
            else:
                raise NotImplementedError("cannot declare item '{}' in a container yet".format(item))
            if len(type_set) > 1:
                return
        return next(iter(type_set))

    def assign_subscript(self, target, value, var):
        z

    def output_assign(self, slot, value):
        letter = type_letter(slot.type())
        self.output += '{}{}z {} '.format(letter, slot.slot_number, value)


@attr.s
class Scope:
    names = attr.ib(default=attr.Factory(dict))
    numeric_slots = attr.ib(default=attr.Factory(lambda: Slots(1)))
    string_slots = attr.ib(default=attr.Factory(lambda: Slots()))

    def define(self, name, type):
        slot = self.names.get(name)
        if slot is not None:
            return slot
        slot = self.allocate(type)
        self.names[name] = slot
        return slot

    def allocate(self, type):
        if type in (Number, tuple):
            slot_number = self.numeric_slots.allocate()
            return Slot(slot_number, type)
        elif type == str:
            slot_number = self.string_slots.allocate()
            return Slot(slot_number, type)

    def allocate_many(self, type, length):
        # TODO: Ensure the memory region is one block
        if type in (Number, tuple):
            slotnums = [self.numeric_slots.allocate() for _ in range(length)]
            return list(map(Slot.number, slotnums))
        elif type == str:
            slotnums = [self.string_slots.allocate() for _ in range(length)]
            return list(map(Slot.string, slotnums))

    def define_const(self, name, value):
        self.names[name] = Const(value)

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
        for i, value in enumerate(self.slots):
            if value is None:
                self.slots[i] = RESERVED
                return i + self.start
        raise MemoryError('ran out of variable slots')


RESERVED = object()


@attr.s
class Const:
    value = attr.ib()

    def type(self):
        if isinstance(self.value, Number):
            return Number
        elif isinstance(self.value, str):
            return str

    def __str__(self):
        if isinstance(self.value, Number):
            return format_number(self.value)
        elif isinstance(self.value, str):
            return format_string(self.value)


@attr.s
class Slot:
    slot_number = attr.ib()
    _type = attr.ib()

    @classmethod
    def number(cls, number):
        return cls(number, Number)

    @classmethod
    def string(cls, number):
        return cls(number, str)

    def type(self):
        return self._type

    def __str__(self):
        letter = type_letter(self._type)
        return '{}{}z'.format(letter, self.slot_number)


def type_letter(type):
    if type in (Number, tuple):
        type_letter = 'p'
    elif type is str:
        type_letter = 's'
    else:
        raise TypeError("variable has unsupported type '{}'".format(type))
    return type_letter


def format_number(n):
    return str(n).replace('.', ',')


def format_string(s):
    return s.replace(' ', '_')
