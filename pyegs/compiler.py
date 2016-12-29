import ast
import numbers

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

    def visit_Assign(self, node):
        target = node.targets[0]
        if isinstance(target, ast.Tuple):
            raise NotImplementedError('iterable destruction is not implemented yet')

        if isinstance(node.value, ast.Num):
            self.assign_num(target, node.value)
        elif isinstance(node.value, ast.Str):
            self.assign_str(target, node.value)
        elif isinstance(node.value, ast.Name):
            self.assign_name(target, node.value)
        elif isinstance(node.value, ast.UnaryOp):
            raise NotImplementedError('assigning unary operations is not implemented yet')
        elif isinstance(node.value, ast.BinOp):
            raise NotImplementedError('assigning binary operations is not implemented yet')
        elif isinstance(node.value, ast.Call):
            self.assign_call(target, node.value)
        # elif isinstance(node.value, ast.Tuple):
        #     self.assign_tuple(target, node.value)
        else:
            raise NotImplementedError("unable to assign the value '{}'".format(node.value))

    def assign_num(self, target, value):
        type = 'p'
        var = self.scope.define(target.id, type)
        value = format_number(value.n)
        self.output_assign(var, value)

    def assign_str(self, target, value):
        type = 's'
        var = self.scope.define(target.id, type)
        value = format_string(value.s)
        self.output_assign(var, value)

    def assign_name(self, target, value):
        src_var = self.scope.get(value.id)
        dest_var = self.scope.define(target.id, src_var.type())
        self.output_assign(dest_var, src_var)

    def assign_call(self, target, value):
        if value.func.id == 'const':
            self.assign_const(target, value)
        else:
            raise NotImplementedError('functions are not implemented yet')

    def assign_const(self, target, call):
        const_arg = call.args[0]
        self.scope.define_const(target.id, const_arg)

    # def assign_tuple(self, target, value):
    #     tuple_type = self.type_of_items(value.elts)
    #     if tuple_type is None:
    #         raise TypeError('tuple items must be of the same type')

    #     tuple_pointer = self.numeric_variables.allocate_or_set(target.id)
    #     for i, item in enumerate(value.elts):
    #         item_target = ast.Name(id=None)
    #         node = ast.Assign(targets=[item_target], value=item)
    #         variable_number = vself.visit_Assign(node)
    #     return tuple_start

    # def type_of_items(self, items):
    #     type_set = set()
    #     for item in items:
    #         if isinstance(item, ast.Num):
    #             type_set.add(numbers.Number)
    #         elif isinstance(item, ast.Str):
    #             type_set.add(str)
    #         elif isinstance(item, ast.Name):
    #             vartype = self.type_of_variable(item.id)
    #             if vartype is numbers.Number:
    #                 type_set.add(ast.Num)
    #             elif vartype is str:
    #                 type_set.add(ast.Str)
    #             elif vartype is None:
    #                 raise NameError("name '{}' is not defined".format(item.id))
    #         if len(type_set) > 1:
    #             return
    #     return next(iter(type_set))

    # def type_of_variable(self, name):
    #     if name in self.numeric_variables.names:
    #         return numbers.Number
    #     elif name in self.string_variables.names:
    #         return str
    #     else:
    #         return None

    def output_assign(self, var, value):
        self.output += '{}{}z {} '.format(var.type(), var.varnum, value)


@attr.s
class Scope:
    names = attr.ib(default=attr.Factory(dict))
    numeric_variables = attr.ib(default=attr.Factory(lambda: Variables(1)))
    string_variables = attr.ib(default=attr.Factory(lambda: Variables()))

    def define(self, name, type):
        var = self.names.get(name)
        if var is not None:
            return var

        if type == 'p':
            varnum = self.numeric_variables.allocate_one()
            var = Variable.number(varnum)
        elif type == 's':
            varnum = self.string_variables.allocate_one()
            var = Variable.string(varnum)

        self.names[name] = var
        return var

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

    def allocate_one(self):
        for i, value in enumerate(self.variables):
            if value is None:
                self.variables[i] = RESERVED
                return i + self.start


RESERVED = object()


@attr.s
class Const:
    value = attr.ib()

    def type(self):
        if isinstance(self.value, numbers.Number):
            return 'p'
        elif isinstance(self.value, str):
            return 's'

    def __str__(self):
        if isinstance(self.value, numbers.Number):
            return format_number(self.value)
        elif isinstance(self.value, str):
            return format_string(self.value)


@attr.s
class Variable:
    varnum = attr.ib()
    _type = attr.ib(default='p')

    @classmethod
    def number(cls, number):
        obj = cls(number)
        obj._type = 'p'
        return obj

    @classmethod
    def string(cls, number):
        obj = cls(number)
        obj._type = 's'
        return obj

    def type(self):
        return self._type

    def __str__(self):
        return '{}{}z'.format(self._type, self.varnum)


def format_number(n):
    return str(n).replace('.', ',')


def format_string(s):
    return s.replace(' ', '_')
