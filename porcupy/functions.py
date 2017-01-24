import types

import attr


@attr.s
class CallableType:
    @classmethod
    def from_function(cls, func, instance=None):
        if instance is None:
            def call(self, converter, fn, *args):
                return func(converter, *args)
        else:
            def call(self, converter, fn, *args):
                return func(converter, instance, *args)

        callable_type = cls()
        callable_type.call = types.MethodType(call, callable_type)
        return callable_type


def length(converter, sequence):
    return sequence.type.len(converter, sequence)


def capacity(converter, sequence):
    return sequence.type.cap(converter, sequence)
