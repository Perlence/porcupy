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
    loaded_values = attr.ib(default=attr.Factory(dict))

    def visit_Assign(self, node, slot=None):
        for target in node.targets:
            if isinstance(target, ast.List):
                raise NotImplementedError('iterable destruction is not implemented yet')
            src_slot = self.load_value(node.value)
            dest_slot = self.store_value(target, src_slot)
            if dest_slot is not None:
                self.output_assign(dest_slot, src_slot)

    def load_value(self, value):
        def fn():
            if isinstance(value, ast.Num):
                return NumberSlot.const(value.n)
            elif isinstance(value, ast.Str):
                return StringSlot.const(value.s)
            elif isinstance(value, ast.List):
                return self.load_list(value)
            elif isinstance(value, ast.Name):
                return self.scope.get(value.id)
                return self.load_value(value.value)
            else:
                raise NotImplementedError()

        try:
            slot = self.loaded_values[value]
        except KeyError:
            slot = self.loaded_values[value] = fn()
        return slot

    def load_list(self, value):
        list_type = self.type_of_items(value.elts)
        if list_type is None:
            raise TypeError('list items must be of the same type')

        capacity = len(value.elts)
        item_slots = self.scope.allocate_many(list_type.slot_type, capacity)
        for dest_slot, item in zip(item_slots, value.elts):
            src_slot = self.load_value(item)
            self.output_assign(dest_slot, src_slot)
        first_item = item_slots[0]
        return ListPointerSlot.const(first_item.slot_number, capacity)

    def type_of_items(self, items):
        type_set = set()
        for item in items:
            src_slot = self.load_value(item)
            type_set.add(type(src_slot))
            if len(type_set) > 1:
                return
        if type_set:
            return next(iter(type_set))

    def store_value(self, target, src_slot):
        if isinstance(target, ast.Name):
            if self.is_const(target):
                self.scope.define_const(target.id, src_slot)
            else:
                return self.scope.copy(src_slot, target.id)
        else:
            raise NotImplementedError()

    def is_const(self, target):
        return target.id is not None and target.id.isupper()

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
        self.names['yegiks'] = GameList(runtime.Yegik)

    def define_const(self, name, value):
        self.names[name] = value

    def copy(self, src_slot, name):
        slot = self.names.get(name)
        if slot is not None:
            # TODO: Check destination type
            return slot
        slot_number = self.allocate(src_slot.slot_type)
        slot = self.names[name] = attr.assoc(src_slot, slot_number=slot_number, value=None)
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
            return list(map(NumberSlot.slot, slotnums))
        elif issubclass(type, str):
            slotnums = [self.string_slots.allocate() for _ in range(length)]
            return list(map(StringSlot.slot, slotnums))

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
class NumberSlot:
    slot_number = attr.ib()
    value = attr.ib()

    slot_type = Number
    letter = 'p'

    @classmethod
    def slot(cls, slot_number, *attrs, **kwattrs):
        return cls(slot_number, None, *attrs, **kwattrs)

    @classmethod
    def const(cls, value, *attrs, **kwattrs):
        return cls(None, value, *attrs, **kwattrs)

    def __str__(self):
        if self.slot_number is not None:
            return 'p{}z'.format(self.slot_number)
        elif self.value is not None:
            return str(self.value).replace('.', ',')


@attr.s
class StringSlot:
    slot_number = attr.ib()
    value = attr.ib()

    slot_type = str
    letter = 's'

    @classmethod
    def slot(cls, slot_number, *attrs, **kwattrs):
        return cls(slot_number, None, *attrs, **kwattrs)

    @classmethod
    def const(cls, value, *attrs, **kwattrs):
        return cls(None, value=value, *attrs, **kwattrs)

    def __str__(self):
        if self.slot_number is not None:
            return 's{}z'.format(self.slot_number)
        elif self.value is not None:
            return self.value.replace(' ', '_')


@attr.s
class ListPointerSlot(NumberSlot):
    capacity = attr.ib()


@attr.s
class GameList:
    type = attr.ib()


@attr.s
class GameVariable:
    slot = attr.ib()
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
