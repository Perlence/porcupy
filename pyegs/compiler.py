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

    def visit_Assign(self, node, var=None):
        target = node.targets[0]
        if isinstance(target, ast.Tuple):
            raise NotImplementedError('iterable destruction is not implemented yet')

        if isinstance(node.value, ast.Num):
            self.assign_num(target, node.value, var)
        elif isinstance(node.value, ast.Str):
            self.assign_str(target, node.value, var)
        elif isinstance(node.value, ast.Name):
            self.assign_name(target, node.value, var)
        elif isinstance(node.value, ast.UnaryOp):
            raise NotImplementedError('assigning unary operations is not implemented yet')
        elif isinstance(node.value, ast.BinOp):
            raise NotImplementedError('assigning binary operations is not implemented yet')
        elif isinstance(node.value, ast.Call):
            self.assign_call(target, node.value, var)
        elif isinstance(node.value, ast.Tuple):
            self.assign_tuple(target, node.value, var)
        else:
            raise NotImplementedError("unable to assign the value '{}'".format(node.value))

    def assign_num(self, target, value, var):
        type = Number
        if var is None:
            var = self.scope.define(target.id, type)
        value = format_number(value.n)
        self.output_assign(var, value)

    def assign_str(self, target, value, var):
        type = str
        if var is None:
            var = self.scope.define(target.id, type)
        value = format_string(value.s)
        self.output_assign(var, value)

    def assign_name(self, target, value, dest_var):
        src_var = self.scope.get(value.id)
        if dest_var is None:
            dest_var = self.scope.define(target.id, src_var.type())
        self.output_assign(dest_var, src_var)

    def assign_call(self, target, value, var):
        if value.func.id == 'const':
            self.assign_const(target, value)
        else:
            raise NotImplementedError('functions are not implemented yet')

    def assign_const(self, target, call):
        const_arg = call.args[0]
        self.scope.define_const(target.id, const_arg)

    def assign_tuple(self, target, value, var):
        tuple_type = self.type_of_items(value.elts)
        if tuple_type is None:
            raise TypeError('tuple items must be of the same type')

        if var is None:
            tuple_pointer = self.scope.define(target.id, tuple)
        else:
            tuple_pointer = var
        variables = self.scope.allocate_many(tuple_type, len(value.elts))
        first_item = variables[0]
        self.output_assign(tuple_pointer, first_item.varnum)
        for dest, src in zip(variables, value.elts):
            target = ast.Name(id=None)
            assign = ast.Assign(targets=[target], value=src)
            self.visit_Assign(assign, var=dest)

    def type_of_items(self, items):
        type_set = set()
        for item in items:
            if isinstance(item, ast.Num):
                type_set.add(Number)
            elif isinstance(item, ast.Str):
                type_set.add(str)
            elif isinstance(item, ast.Name):
                var = self.scope.get(item.id)
                type_set.add(var.type())
            else:
                raise NotImplementedError("cannot declare item '{}' in a container yet".format(item))
            if len(type_set) > 1:
                return
        return next(iter(type_set))

    def output_assign(self, var, value):
        letter = type_letter(var.type())
        self.output += '{}{}z {} '.format(letter, var.varnum, value)


@attr.s
class Scope:
    names = attr.ib(default=attr.Factory(dict))
    numeric_variables = attr.ib(default=attr.Factory(lambda: Variables(1)))
    string_variables = attr.ib(default=attr.Factory(lambda: Variables()))

    def define(self, name, type):
        var = self.names.get(name)
        if var is not None:
            return var
        var = self.allocate(type)
        self.names[name] = var
        return var

    def allocate(self, type):
        if type in (Number, tuple):
            varnum = self.numeric_variables.allocate()
            return Variable.number(varnum)
        elif type == str:
            varnum = self.string_variables.allocate()
            return Variable.string(varnum)

    def allocate_many(self, type, length):
        # TODO: Ensure the memory region is one block
        if type in (Number, tuple):
            varnums = [self.numeric_variables.allocate() for _ in range(length)]
            return list(map(Variable.number, varnums))
        elif type == str:
            varnums = [self.string_variables.allocate() for _ in range(length)]
            return list(map(Variable.string, varnums))

    def define_const(self, name, value):
        if isinstance(value, ast.Num):
            self.names[name] = Const(value.n)
        elif isinstance(value, ast.Str):
            self.names[name] = Const(value.s)

    def get(self, name):
        var = self.names.get(name)
        if var is None:
            raise NameError("name '{}' is not defined".format(name))
        return var


@attr.s
class Variables:
    start = attr.ib(default=0)
    stop = attr.ib(default=100)
    variables = attr.ib(init=False)

    def __attrs_post_init__(self):
        self.variables = [None for x in range(self.start, self.stop)]

    def allocate(self):
        for i, value in enumerate(self.variables):
            if value is None:
                self.variables[i] = RESERVED
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
class Variable:
    varnum = attr.ib()
    _type = attr.ib(default=Number)

    @classmethod
    def number(cls, number):
        obj = cls(number)
        obj._type = Number
        return obj

    @classmethod
    def string(cls, number):
        obj = cls(number)
        obj._type = str
        return obj

    def type(self):
        return self._type

    def __str__(self):
        letter = type_letter(self._type)
        return '{}{}z'.format(letter, self.varnum)


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
