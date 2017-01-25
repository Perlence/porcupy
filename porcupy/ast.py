import ast
from numbers import Number
from operator import add, sub, mul, truediv, floordiv, mod

import attr

__all__ = ('AST', 'Module', 'Assign', 'If', 'Const', 'Slot', 'BoolOp', 'BinOp', 'Compare', 'Call', 'Label')


class AST:
    pass


@attr.s
class Module(AST):
    body = attr.ib()

    def __str__(self):
        return '  '.join(map(str, self.body))


@attr.s
class Assign(AST):
    target = attr.ib()
    value = attr.ib()

    def __str__(self):
        return ' '.join([str(self.target), str(self.value)])


@attr.s
class If(AST):
    test = attr.ib()
    body = attr.ib()

    def __str__(self):
        body = '  '.join(map(str, self.body))
        return '# {} ( {} )'.format(self.test, body)


@attr.s
class Const(AST):
    value = attr.ib()
    type = attr.ib(default=None)
    metadata = attr.ib(default=attr.Factory(dict))

    def __attrs_post_init__(self):
        from .types import NumberType, StringType

        if self.type is not None:
            return

        if isinstance(self.value, Number):
            self.type = NumberType()
        elif isinstance(self.value, (str, list)):
            self.type = StringType()
        else:
            raise TypeError("unable to use consts of type '{}'".format(type(self.value)))

    def __str__(self):
        from .types import NumberType, StringType

        if isinstance(self.type, NumberType):
            if isinstance(self.value, bool):
                return str(int(self.value))
            else:
                return str(self.value)
        elif isinstance(self.type, StringType):
            value = self.value
            if isinstance(self.value, list):
                value = ''.join(map(str, self.value))
            return value.replace(' ', '_')
        else:
            raise TypeError("cannot format '{}' const".format(self.type))


@attr.s
class Slot(AST):
    register = attr.ib()
    index = attr.ib()
    attrib = attr.ib()
    type = attr.ib()
    metadata = attr.ib(default=attr.Factory(dict))
    ref = attr.ib(default=None)
    short_form = attr.ib(default=False)

    def is_variable(self):
        return self.register in ('p', 's')

    def __str__(self):
        if self.short_form:
            if self.register not in ('p', 's'):
                raise ValueError("unable output slot '{!r}' in short form".format(self))
            prefix = '^' if self.register == 'p' else '$'
            return '{}{}'.format(prefix, self.index)
        elif self.attrib is not None:
            index = self.index
            if self.ref is not None:
                index = self.ref.index
            if index is None:
                index = ''
            return '{register}{ref}{index}{attrib}'.format(
                register=self.register,
                ref='^' if self.ref is not None else '',
                index=index,
                attrib=self.attrib)
        else:
            return str(self.index)


@attr.s(init=False)
class AssociatedSlot(AST):
    _original = attr.ib()
    _changes = attr.ib()

    def __init__(self, inst, **changes):
        if isinstance(inst, AssociatedSlot):
            super().__setattr__('_original', super(AssociatedSlot, inst).__getattribute__('_original'))
            super().__setattr__('_changes', {**super(AssociatedSlot, inst).__getattribute__('_changes'), **changes})
        else:
            super().__setattr__('_original', inst)
            super().__setattr__('_changes', changes)

    def __getattr__(self, name):
        try:
            return super().__getattribute__('_changes')[name]
        except KeyError:
            return super().__getattribute__('_original').__getattribute__(name)

    def __setattr__(self, name, value):
        if name in attr.asdict(super().__getattribute__('_original')):
            super().__getattribute__('_changes')[name] = value
        else:
            super().__setattr__(name, value)

    def __str__(self):
        return str(super().__getattribute__('apply_changes')())

    def apply_changes(self):
        return attr.assoc(super().__getattribute__('_original'), **super().__getattribute__('_changes'))


@attr.s
class BoolOp(AST):
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
class BinOp(AST):
    left = attr.ib()
    op = attr.ib()
    right = attr.ib()

    type = attr.ib(init=False)
    metadata = attr.ib(default=attr.Factory(dict))

    def __attrs_post_init__(self):
        from .types import NumberType, FloatType, IntType

        left_type = self.left.type
        right_type = self.right.type
        if not isinstance(left_type, NumberType) or not isinstance(right_type, NumberType):
            raise TypeError("binary operands '{}' and '{}' must be numbers".format(self.left, self.right))

        if isinstance(left_type, FloatType) or isinstance(right_type, FloatType) or isinstance(self.op, Div):
            self.type = FloatType()
        else:
            self.type = IntType()

    def __str__(self):
        return '{}{}{}'.format(self.left, self.op, self.right)


class operator:
    pass


class Add(operator):
    def __str__(self):
        return '+'

    __call__ = add


class Sub(operator):
    def __str__(self):
        return '-'

    __call__ = sub


class Mult(operator):
    def __str__(self):
        return '*'

    __call__ = mul


class Div(operator):
    def __str__(self):
        return '/'

    __call__ = truediv


class FloorDiv(operator):
    def __str__(self):
        return '{'

    __call__ = floordiv


class Mod(operator):
    def __str__(self):
        return '}'

    __call__ = mod


@attr.s
class Compare(AST):
    left = attr.ib()
    op = attr.ib()
    right = attr.ib()

    type = attr.ib(init=False)
    metadata = attr.ib(default=attr.Factory(dict))

    def __attrs_post_init__(self):
        from .types import BoolType

        self.type = BoolType()

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


@attr.s
class Call(AST):
    func = attr.ib()
    args = attr.ib()

    def __str__(self):
        result = [str(self.func)]
        if self.args:
            positional_args = ' '.join(map(str, self.args))
            result.append(positional_args)
        return ' '.join(result)


@attr.s
class Label(AST):
    index = attr.ib()

    def __str__(self):
        return ':{}'.format(self.index)
