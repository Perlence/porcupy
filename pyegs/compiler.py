import ast
import numbers

import attr

from . import runtime as rt


def compile(source, filename='<unknown>'):
    top = ast.parse(source, filename)

    visitor = NodeVisitor()
    visitor.visit(top)
    return visitor.output.strip()


@attr.s
class NodeVisitor(ast.NodeVisitor):
    numeric_variables = attr.ib(default=attr.Factory(lambda: Variables(1)))
    string_variables = attr.ib(default=attr.Factory(lambda: Variables()))
    consts = attr.ib(default=attr.Factory(dict))
    output = attr.ib(default='')

    def visit_Assign(self, node):
        if len(node.targets) > 1:
            raise NotImplementedError('iterable destruction is not implemented yet')
        target = node.targets[0]
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
        else:
            raise NotImplementedError("unable to assign the value '{}'".format(node.value))

    def assign_num(self, target, value):
        self.output_assign(target, value.n, type='p')

    def assign_str(self, target, value):
        self.output_assign(target, value.s, type='s')

    def assign_name(self, target, value):
        name = value.id
        value, type = self.reference_name(name)
        self.output_assign(target, value, type)

    def reference_name(self, name):
        const = self.consts.get(name)
        if const is not None:
            value = const
            if isinstance(value, numbers.Number):
                type = 'p'
            if isinstance(value, str):
                type = 's'
            return value, type

        variable_number = self.numeric_variables.names.get(name)
        if variable_number is not None:
            value = 'p{}z'.format(variable_number)
            return value, 'p'

        variable_number = self.string_variables.names.get(name)
        if variable_number is not None:
            value = 's{}z'.format(variable_number)
            return value, 's'

        raise NameError("name '{}' is not defined".format(name))

    def assign_call(self, target, value):
        if value.func.id == 'const':
            self.assign_const(target, value)
        else:
            raise NotImplementedError('functions are not implemented yet')

    def assign_const(self, target, call):
        const_arg = call.args[0]
        if isinstance(const_arg, ast.Num):
            self.consts[target.id] = const_arg.n
        elif isinstance(const_arg, ast.Str):
            self.consts[target.id] = const_arg.s

    def output_assign(self, target, value, type):
        if type == 'p':
            variable_number = self.numeric_variables.allocate_one(target.id)
            value = self.format_number(value)
        elif type == 's':
            variable_number = self.string_variables.allocate_one(target.id)
            value = self.format_string(value)
        self.output += '{}{}z {} '.format(type, variable_number, value)

    def format_number(self, n):
        return str(n).replace('.', ',')

    def format_string(self, s):
        return s.replace(' ', '_')


@attr.s
class Variables:
    start = attr.ib(default=0)
    stop = attr.ib(default=100)
    variables = attr.ib(init=False)
    names = attr.ib(default=attr.Factory(dict))

    def __attrs_post_init__(self):
        self.variables = [None for x in range(self.start, self.stop)]

    def allocate_one(self, name):
        number = self.names.get(name)
        if number is None:
            for i, n in enumerate(self.variables):
                if n is None:
                    self.variables[i] = name
                    self.names[name] = i + self.start
                    number = i + self.start
                    break
        return number
