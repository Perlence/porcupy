from inspect import signature

import attr
import funcy

__all__ = ('timers', 'system', 'yegiks', 'bots', 'points')


class FunctionType:
    @staticmethod
    @funcy.memoize
    def with_signature(fn):
        return type('SignedFunctionType', (FunctionType,), {'signature': signature(fn)})


SignedFunctionType = FunctionType.with_signature(lambda: None)


@attr.s
class Timer:
    value = attr.ib(default=0, metadata={'abbrev': 'i', 'type': int})
    enabled = attr.ib(default=0, metadata={'abbrev': 'r', 'type': bool})

    metadata = {'abbrev': 't'}


timers = [Timer() for x in range(100)]
timers[1].enabled = 1


@attr.s
class System:
    bots = attr.ib(default=0, metadata={'abbrev': 'b', 'type': int})
    color = attr.ib(default=0, metadata={'abbrev': 'c', 'type': int})

    metadata = {'abbrev': 'y'}

    def message(self, s):
        pass

    message.metadata = {'abbrev': 'm', 'type': FunctionType.with_signature(message)}

    def message_at(self, x, y, dur, s):
        pass

    message_at.metadata = {'abbrev': 'y', 'type': FunctionType.with_signature(message_at)}

    def set_color(self, r, g, b):
        self.color = r + (g << 8) + (b << 16)

    set_color.metadata = {'type': FunctionType.with_signature(set_color)}

    def load_map(self, name):
        pass

    load_map.metadata = {'abbrev': 'l', 'type': FunctionType.with_signature(load_map)}


system = System()


@attr.s
class Bot:
    ai = attr.ib(default=False, metadata={'abbrev': 'i', 'type': bool})
    target = attr.ib(default=0, metadata={'abbrev': 't', 'type': int})
    level = attr.ib(default=0, metadata={'abbrev': 'l', 'type': int})
    point = attr.ib(default=0, metadata={'abbrev': 'p', 'type': int})

    metadata = {'abbrev': 'a'}

    def goto(self, point):
        pass

    goto.metadata = {'abbrev': 'g', 'type': FunctionType.with_signature(goto)}


bots = [Bot() for x in range(1, 10)]


@attr.s
class Yegik:
    frags = attr.ib(default=0, metadata={'abbrev': 'f', 'type': int})
    pos_x = attr.ib(default=0.0, metadata={'abbrev': 'x', 'type': float})
    pos_y = attr.ib(default=0.0, metadata={'abbrev': 'y', 'type': float})
    speed_x = attr.ib(default=0.0, metadata={'abbrev': 'u', 'type': float})
    speed_y = attr.ib(default=0.0, metadata={'abbrev': 'v', 'type': float})
    health = attr.ib(default=0, metadata={'abbrev': 'p', 'type': int})
    armor = attr.ib(default=0, metadata={'abbrev': 'n', 'type': int})
    has_weapon = attr.ib(default=False, metadata={'abbrev': 'e', 'type': bool})
    weapon = attr.ib(default=0, metadata={'abbrev': 'w', 'type': int})
    ammo = attr.ib(default=0, metadata={'abbrev': 's', 'type': int})
    view_angle = attr.ib(default=0.0, metadata={'abbrev': 'a', 'type': float})

    metadata = {'abbrev': 'e'}

    def spawn(self, point):
        pass

    spawn.metadata = {'abbrev': 'b', 'type': FunctionType.with_signature(spawn)}


yegiks = [Yegik() for x in range(1, 10)]


@attr.s
class Point:
    pos_x = attr.ib(default=0.0, metadata={'abbrev': 'x', 'type': float})
    pos_y = attr.ib(default=0.0, metadata={'abbrev': 'y', 'type': float})

    metadata = {'abbrev': 'c'}


points = [Point() for x in range(1, 100)]
