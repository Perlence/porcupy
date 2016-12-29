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
        is_str = False
        is_num = False

        if isinstance(node.value, ast.Num):
            value = node.value.n
            is_num = True

        elif isinstance(node.value, ast.Str):
            value = node.value.s
            is_str = True

        elif isinstance(node.value, ast.Name):
            name = node.value.id
            value, is_num, is_str = self.reference_name(name)

        elif isinstance(node.value, ast.UnaryOp):
            raise NotImplementedError('assigning unary operations is not implemented yet')

        elif isinstance(node.value, ast.BinOp):
            raise NotImplementedError('assigning binary operations is not implemented yet')

        elif isinstance(node.value, ast.Call):
            if node.value.func.id == 'const':
                self.set_const(target.id, node.value)
                return

        if is_num:
            variable_number = self.numeric_variables.allocate_one(target.id)
            value = self.format_number(value)
            register = 'p'
        elif is_str:
            variable_number = self.string_variables.allocate_one(target.id)
            value = self.format_string(value)
            register = 's'
        self.output += '{}{}z {} '.format(register, variable_number, value)

    def reference_name(self, name):
        is_num = False
        is_str = False

        const = self.consts.get(name)
        if const is not None:
            value = const
            is_num = isinstance(value, numbers.Number)
            is_str = isinstance(value, str)
            return value, is_num, is_str

        variable_number = self.numeric_variables.names.get(name)
        if variable_number is not None:
            value = 'p{}z'.format(variable_number)
            is_num = True
            return value, is_num, is_str

        variable_number = self.string_variables.names.get(name)
        if variable_number is not None:
            value = 's{}z'.format(variable_number)
            is_str = True
            return value, is_num, is_str

        raise NameError("name '{}' is not defined".format(name))

    def set_const(self, name, call):
        const_arg = call.args[0]
        if isinstance(const_arg, ast.Num):
            self.consts[name] = const_arg.n
        elif isinstance(const_arg, ast.Str):
            self.consts[name] = const_arg.s

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
