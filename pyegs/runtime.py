import attr

__all__ = ('timers', 'system', 'yegiks', 'bots', 'points')


@attr.s
class Timer:
    _number = attr.ib()
    value = attr.ib(default=0)
    enabled = attr.ib(default=0)


timers = [Timer(x) for x in range(100)]
timers[1].enabled = 1


@attr.s
class System:
    bots = attr.ib(default=0)
    color = attr.ib(default=0)

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
    _number = attr.ib()
    ai = attr.ib(default=False)
    target = attr.ib(default=0)
    level = attr.ib(default=0)
    point = attr.ib(default=0)

    def goto(self, point):
        pass


bots = [Bot(x) for x in range(1, 10)]


@attr.s
class Yegik:
    _number = attr.ib()
    frags = attr.ib(default=0)
    pos_x = attr.ib(default=0.0)
    pos_y = attr.ib(default=0.0)
    speed_x = attr.ib(default=0.0)
    speed_y = attr.ib(default=0.0)
    health = attr.ib(default=0)
    armor = attr.ib(default=0)
    has_weapon = attr.ib(default=False)
    weapon = attr.ib(default=0)
    ammo = attr.ib(default=0)
    view_angle = attr.ib(default=0.0)

    def spawn(self, point):
        pass


yegiks = [Yegik(x) for x in range(1, 10)]


@attr.s
class Point:
    _number = attr.ib()
    pos_x = attr.ib(default=0.0)
    pos_y = attr.ib(default=0.0)


points = [Point(x) for x in range(1, 100)]
