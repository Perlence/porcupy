import ast
from numbers import Number

import attr

from . import runtime


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
            if isinstance(target, ast.List):
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
            elif isinstance(node.value, ast.List):
                self.assign_list(target, node.value, slot)
            elif isinstance(node.value, ast.Subscript):
                self.assign_subscript(target, node.value, slot)
            else:
                raise NotImplementedError("unable to assign the value '{}'".format(node.value))

    def assign_num(self, target, value, slot):
        if self.is_const(target):
            self.scope.define_const(target.id, value.n)
            return
        if slot is None:
            slot = self.scope.define(NumberSlot, target.id)
        value = NumberConst(value.n)
        self.output_assign(slot, value)

    def assign_str(self, target, value, slot):
        if self.is_const(target):
            self.scope.define_const(target.id, value.s)
            return
        if slot is None:
            slot = self.scope.define(StringSlot, target.id)
        value = StringConst(value.s)
        self.output_assign(slot, value)

    def is_const(self, target):
        return target.id is not None and target.id.isupper()

    def assign_name(self, target, value, dest_slot):
        src_slot = self.scope.get(value.id)
        if dest_slot is None:
            if isinstance(src_slot, NumberConst):
                dest_slot = self.scope.define(NumberSlot, target.id)
            elif isinstance(src_slot, StringConst):
                dest_slot = self.scope.define(StringSlot, target.id)
            else:
                dest_slot = self.scope.copy(src_slot, target.id)
        self.output_assign(dest_slot, src_slot)

    def assign_const(self, target, call):
        const_arg = call.args[0]
        self.scope.define_const(target.id, const_arg)

    def assign_list(self, target, value, slot):
        list_type = self.type_of_items(value.elts)
        if list_type is None:
            raise TypeError('list items must be of the same type')

        capacity = len(value.elts)
        if slot is None:
            list_pointer = self.scope.define(ListPointerSlot, target.id, capacity)
        else:
            list_pointer = slot
        slots = self.scope.allocate_many(list_type, capacity)
        first_item = slots[0]
        self.output_assign(list_pointer, first_item.slot_number)
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
                type_set.add(slot.slot_type)
            else:
                raise NotImplementedError("cannot declare item '{}' in a container yet".format(item))
            if len(type_set) > 1:
                return
        return next(iter(type_set))

    def assign_subscript(self, target, value, slot):
        container_name = value.value.id
        var = self.scope.get(container_name)
        if isinstance(var, GameVariable):
            ref = self.scope.define(Reference, target.id, type(var))
            index = value.slice.value.n
            self.output_assign(ref, getattr(runtime, container_name)[index]._number)

    def output_assign(self, dest, value):
        self.output += '{}{}z {} '.format(dest.letter, dest.slot_number, value)


@attr.s
class Scope:
    names = attr.ib(default=attr.Factory(dict))
    numeric_slots = attr.ib(default=attr.Factory(lambda: Slots(1)))
    string_slots = attr.ib(default=attr.Factory(lambda: Slots()))

    def __attrs_post_init__(self):
        self.populate_game_vars()

    def populate_game_vars(self):
        self.names['yegiks'] = GameVariable(runtime.Yegik)

    def define_const(self, name, value):
        if isinstance(value, Number):
            const = NumberConst(value)
        elif isinstance(value, str):
            const = StringConst(value)
        self.names[name] = const
        return const

    def copy(self, src_slot, name):
        slot = self.names.get(name)
        if slot is not None:
            # TODO: Check destination type
            return slot
        slot_number = self.allocate(src_slot.slot_type)
        print(src_slot)
        slot = self.names[name] = attr.assoc(src_slot, slot_number=slot_number)
        return slot

    def define(self, type, name, *attrs):
        slot = self.names.get(name)
        if slot is not None:
            # TODO: Check destination type
            return slot
        slot_number = self.allocate(type.slot_type)
        slot = self.names[name] = type(slot_number, *attrs)
        return slot

    def allocate(self, type):
        if issubclass(type, Number):
            slot_number = self.numeric_slots.allocate()
        elif issubclass(type, str):
            slot_number = self.string_slots.allocate()
        else:
            raise TypeError("cannot allocate slot of type '{}'".format(type))
        return slot_number

    def allocate_many(self, type, length):
        # TODO: Ensure the memory region is one block
        if issubclass(type, Number):
            slotnums = [self.numeric_slots.allocate() for _ in range(length)]
            return list(map(NumberSlot, slotnums))
        elif issubclass(type, str):
            slotnums = [self.string_slots.allocate() for _ in range(length)]
            return list(map(StringSlot, slotnums))

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
class NumberConst:
    value = attr.ib()

    def __str__(self):
        return str(self.value).replace('.', ',')


@attr.s
class StringConst:
    value = attr.ib()

    def __str__(self):
        return self.value.replace(' ', '_')


@attr.s
class NumberSlot:
    slot_number = attr.ib()
    slot_type = Number
    letter = 'p'

    def __str__(self):
        return 'p{}z'.format(self.slot_number)


@attr.s
class StringSlot:
    slot_number = attr.ib()
    slot_type = str
    letter = 's'

    def __str__(self):
        return 's{}z'.format(self.slot_number)


@attr.s
class ListPointerSlot(NumberSlot):
    capacity = attr.ib()


@attr.s
class GameVariable:
    # slot_number = attr.ib()
    type = attr.ib()

    # def __str__(self):
    #     return str(self.slot_number)


@attr.s
class GameAttribute:
    game_var = attr.ib()
    attrib = attr.ib()

    def __str__(self):
        return '{}{}{}'.format(self.game_var._type._letter,
                               self.game_var.slot_number,
                               self.attrib.metadata['letter'])


@attr.s
class Reference(NumberSlot):
    gamevar_type = attr.ib()
