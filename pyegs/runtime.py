import attr

__all__ = ('timers', 'system', 'yegiks', 'bots', 'points')


@attr.s
class Timer:
    value = attr.ib(default=0, metadata={'abbrev': 'i'})
    enabled = attr.ib(default=0, metadata={'abbrev': 'r'})

    _abbrev = 't'


timers = [Timer() for x in range(100)]
timers[1].enabled = 1


@attr.s
class System:
    bots = attr.ib(default=0, metadata={'abbrev': 'b'})
    color = attr.ib(default=0, metadata={'abbrev': 'c'})

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
    ai = attr.ib(default=False, metadata={'abbrev': 'i'})
    target = attr.ib(default=0, metadata={'abbrev': 't'})
    level = attr.ib(default=0, metadata={'abbrev': 'l'})
    point = attr.ib(default=0, metadata={'abbrev': 'p'})

    _abbrev = 'a'

    def goto(self, point):
        pass


bots = [Bot() for x in range(1, 10)]


@attr.s
class Yegik:
    frags = attr.ib(default=0, metadata={'abbrev': 'f'})
    pos_x = attr.ib(default=0.0, metadata={'abbrev': 'x'})
    pos_y = attr.ib(default=0.0, metadata={'abbrev': 'y'})
    speed_x = attr.ib(default=0.0, metadata={'abbrev': 'u'})
    speed_y = attr.ib(default=0.0, metadata={'abbrev': 'v'})
    health = attr.ib(default=0, metadata={'abbrev': 'p'})
    armor = attr.ib(default=0, metadata={'abbrev': 'n'})
    has_weapon = attr.ib(default=False, metadata={'abbrev': 'e'})
    weapon = attr.ib(default=0, metadata={'abbrev': 'w'})
    ammo = attr.ib(default=0, metadata={'abbrev': 's'})
    view_angle = attr.ib(default=0.0, metadata={'abbrev': 'a'})

    _abbrev = 'e'

    def spawn(self, point):
        pass


yegiks = [Yegik() for x in range(1, 10)]


@attr.s
class Point:
    pos_x = attr.ib(default=0.0, metadata={'abbrev': 'x'})
    pos_y = attr.ib(default=0.0, metadata={'abbrev': 'y'})

    _abbrev = 'c'


points = [Point() for x in range(1, 100)]
