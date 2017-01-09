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

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, (ast.Tuple, ast.List)):
                raise NotImplementedError('iterable unpacking is not implemented yet')
            src_slot = self.load_value(node.value)
            dest_slot = self.store_value(target, src_slot)
            if dest_slot is not None:
                self.output_assign(dest_slot, src_slot)

    def visit_If(self, node):
        self.output.append('#')
        self.output_test(node.test)
        self.output.append('(')
        for body_node in node.body:
            self.visit(body_node)
        self.output.append(')')

    def output_test(self, test):
        if isinstance(test, ast.Compare):
            self.output_compare(test)
        elif isinstance(test, ast.BoolOp):
            self.output_bool_op(test)
        else:
            raise NotImplementedError

    def output_compare(self, compare):
        left = self.load_value(compare.left)
        self.output.append(str(left))
        and_left = False
        for op, comparator in zip(compare.ops, compare.comparators):
            if and_left:
                self.output += ['&', str(left)]
            self.output_cmpop(op)
            comp_slot = self.load_value(comparator)
            self.output.append(str(comp_slot))
            left = comp_slot
            and_left = True

    def output_bool_op(self, bool_op):
        first = bool_op.values[0]
        slot = self.load_value(first)
        self.output.append(str(slot))
        for value in bool_op.values[1:]:
            slot = self.load_value(value)
            self.output_boolop(bool_op.op)
            self.output.append(str(slot))

    def output_cmpop(self, op):
        if isinstance(op, ast.Eq):
            self.output.append('=')
        elif isinstance(op, ast.NotEq):
            self.output.append('!')
        elif isinstance(op, ast.Lt):
            self.output.append('<')
        elif isinstance(op, ast.LtE):
            self.output.append('<=')
        elif isinstance(op, ast.Gt):
            self.output.append('>')
        elif isinstance(op, ast.GtE):
            self.output.append('>=')

    def output_boolop(self, op):
        if isinstance(op, ast.And):
            self.output.append('&')
        elif isinstance(op, ast.Or):
            self.output.append('|')

    def load_value(self, value):
        def fn():
            if isinstance(value, ast.Num):
                return Const(value.n, Number)
            elif isinstance(value, ast.Str):
                return Const(value.s, str)
            elif isinstance(value, ast.List):
                return self.load_list(value)
            elif isinstance(value, ast.NameConstant):
                return Const(value.value, type(value.value))
            elif isinstance(value, ast.Name):
                return self.scope.get(value.id)
            elif isinstance(value, ast.Attribute):
                return self.load_attribute(value)
            elif isinstance(value, ast.Subscript):
                return self.load_subscript(value)
            elif isinstance(value, ast.Index):
                return self.load_value(value.value)
            else:
                raise NotImplementedError

        slot = self.loaded_values.get(value)
        if slot is None:
            slot = self.loaded_values[value] = fn()
        return slot

    def load_list(self, value):
        item_type = self.type_of_items(value.elts)
        if item_type is None:
            raise TypeError('list items must be of the same type')

        capacity = len(value.elts)
        item_slots = self.scope.allocate_many(item_type, capacity)
        for dest_slot, item in zip(item_slots, value.elts):
            src_slot = self.load_value(item)
            self.output_assign(dest_slot, src_slot)
        first_item = item_slots[0]
        metadata = {'capacity': capacity, 'item_type': item_type}
        return Const(first_item.number, ListPointer, metadata=metadata)

    def type_of_items(self, items):
        type_set = set()
        for item in items:
            src_slot = self.load_value(item)
            print(repr(src_slot))
            type_set.add(src_slot.type)
            if len(type_set) > 1:
                return
        if type_set:
            return next(iter(type_set))

    def load_attribute(self, value):
        value_slot = self.load_value(value.value)
        if issubclass(value_slot.type, GameObjectRef):
            return self.load_game_obj_attr(value_slot, value.attr)
        else:
            raise NotImplementedError

    def load_game_obj_attr(self, slot, attr_name):
        game_obj_type = slot.type.type
        register = game_obj_type._abbrev
        attrib = getattr(game_obj_type, attr_name)
        if slot.is_variable():
            slot = attr.assoc(slot, register=register, ref=True)
        return attr.assoc(slot, type=attrib.metadata['type'], attrib=attrib.metadata['abbrev'])

    def load_subscript(self, value):
        value_slot = self.load_value(value.value)
        slice_slot = self.load_value(value.slice)
        if isinstance(value_slot, GameObjectList):
            return self.load_game_obj_list_subscript(value_slot, slice_slot)
        elif issubclass(value_slot.type, ListPointer):
            return self.load_list_subscript(value_slot, slice_slot)
        else:
            raise NotImplementedError

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
        addition = BinaryOp(value_slot, ast.Add(), slice_slot)
        self.output_assign(pointer_math_slot, addition)
        slot = attr.assoc(pointer_math_slot, type=value_slot.metadata['item_type'], ref=True)
        if issubclass(value_slot.metadata['item_type'], GameObjectRef):
            self.output_assign(pointer_math_slot, slot)
        self.scope.free(pointer_math_slot)
        return slot

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
            raise NotImplementedError

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

    def is_variable(self):
        return self.register in ('p', 's')

    def __str__(self):
        if self.attrib is not None:
            return '{}{}{}{}'.format(
                self.register,
                '^' if self.ref else '',
                self.number if self.number is not None else '',
                self.attrib)
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
class BinaryOp:
    left = attr.ib()
    op = attr.ib()
    right = attr.ib()

    def __str__(self):
        if isinstance(self.op, ast.Add):
            op = '+'
        else:
            raise NotImplementedError
        return '{}{}{}'.format(self.left, op, self.right)
