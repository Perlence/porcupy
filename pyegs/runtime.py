import attr

__all__ = ('timers', 'system', 'yegiks', 'bots', 'points')


@attr.s
class Timer:
    value = attr.ib(default=0, metadata={'abbrev': 'i', 'type': int})
    enabled = attr.ib(default=0, metadata={'abbrev': 'r', 'type': bool})

    _abbrev = 't'


timers = [Timer() for x in range(100)]
timers[1].enabled = 1


@attr.s
class System:
    bots = attr.ib(default=0, metadata={'abbrev': 'b', 'type': int})
    color = attr.ib(default=0, metadata={'abbrev': 'c', 'type': int})

    _abbrev = 'y'

    def message(self, s):
        pass

    def message_at(self, x, y, duration, s):
        pass

    def set_color(self, r, g, b):
        self.color = r + (g << 8) + (b << 16)

    def load_map(self, name):
        pass


system = System()


@attr.s
class Bot:
    ai = attr.ib(default=False, metadata={'abbrev': 'i', 'type': bool})
    target = attr.ib(default=0, metadata={'abbrev': 't', 'type': int})
    level = attr.ib(default=0, metadata={'abbrev': 'l', 'type': int})
    point = attr.ib(default=0, metadata={'abbrev': 'p', 'type': int})

    _abbrev = 'a'

    def goto(self, point):
        pass


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

    _abbrev = 'e'

    def spawn(self, point):
        pass


yegiks = [Yegik() for x in range(1, 10)]


@attr.s
class Point:
    pos_x = attr.ib(default=0.0, metadata={'abbrev': 'x', 'type': float})
    pos_y = attr.ib(default=0.0, metadata={'abbrev': 'y', 'type': float})

    _abbrev = 'c'


points = [Point() for x in range(1, 100)]
