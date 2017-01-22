import enum

import attr

from .types import IntType, FloatType, BoolType, StringType, GameObject

int_type = IntType()
bool_type = BoolType()
float_type = FloatType()
str_type = StringType()


@attr.s(init=False)
class Timer(GameObject):
    value = attr.ib(metadata={'abbrev': 'i', 'type': int_type})
    enabled = attr.ib(metadata={'abbrev': 'r', 'type': bool_type, 'readonly': True})

    metadata = {'abbrev': 't'}

    def start(self) -> None:
        pass

    start.metadata = {'abbrev': 'g'}

    def stop(self) -> None:
        pass

    stop.metadata = {'abbrev': 's'}


# TODO: Populate scope with enums


class GameMode(enum.Enum):
    multi_lan = 1
    multi_duel = 2
    hot_seat = 3
    menu = 4
    single = 5
    sheep = 6
    hot_seat_split = 7


@attr.s(init=False)
class System(GameObject):
    bots = attr.ib(metadata={'abbrev': 'b', 'type': int_type})
    color = attr.ib(metadata={'abbrev': 'c', 'type': int_type})
    frag_limit = attr.ib(metadata={'abbrev': 'f', 'type': int_type})
    game_mode = attr.ib(metadata={'abbrev': 'g', 'type': GameMode, 'readonly': True})

    metadata = {'abbrev': 'y'}

    def print(self, s: str_type) -> None:
        pass

    print.metadata = {'abbrev': 'm'}

    def print_at(self, x: float_type, y: float_type, dur: float_type, s: str_type) -> None:
        pass

    print_at.metadata = {'abbrev': 'y'}

    # def set_color(self, r: int_type, g: int_type, b: int_type) -> None:
    #     self.color = r + (g << 8) + (b << 16)

    def load_map(self, name: str_type) -> None:
        pass

    load_map.metadata = {'abbrev': 'l'}


@attr.s(init=False)
class Point(GameObject):
    pos_x = attr.ib(metadata={'abbrev': 'x', 'type': float_type})
    pos_y = attr.ib(metadata={'abbrev': 'y', 'type': float_type})

    metadata = {'abbrev': 'c'}


@attr.s(init=False)
class Bot(GameObject):
    ai = attr.ib(metadata={'abbrev': 'i', 'type': bool_type})
    target = attr.ib(metadata={'abbrev': 't', 'type': int_type})
    level = attr.ib(metadata={'abbrev': 'l', 'type': int_type})
    point = attr.ib(metadata={'abbrev': 'p', 'type': int_type, 'readonly': True})
    goto = attr.ib(metadata={'abbrev': 'g', 'type': Point})
    can_see_target = attr.ib(metadata={'abbrev': 's', 'type': bool_type, 'readonly': True})

    metadata = {'abbrev': 'a'}


@attr.s(init=False)
class Yozhik(GameObject):
    frags = attr.ib(metadata={'abbrev': 'f', 'type': int_type})
    pos_x = attr.ib(metadata={'abbrev': 'x', 'type': float_type})
    pos_y = attr.ib(metadata={'abbrev': 'y', 'type': float_type})
    speed_x = attr.ib(metadata={'abbrev': 'u', 'type': float_type})
    speed_y = attr.ib(metadata={'abbrev': 'v', 'type': float_type})
    health = attr.ib(metadata={'abbrev': 'p', 'type': int_type})
    armor = attr.ib(metadata={'abbrev': 'n', 'type': int_type})
    has_weapon = attr.ib(metadata={'abbrev': 'e', 'type': bool_type})
    weapon = attr.ib(metadata={'abbrev': 'w', 'type': int_type})
    ammo = attr.ib(metadata={'abbrev': 's', 'type': int_type})
    view_angle = attr.ib(metadata={'abbrev': 'a', 'type': float_type})
    team = attr.ib(metadata={'abbrev': 't', 'type': int_type})

    metadata = {'abbrev': 'e'}

    def spawn(self, point: int_type) -> None:
        pass

    spawn.metadata = {'abbrev': 'b'}


@attr.s(init=False)
class Sheep(GameObject):
    def spawn(self, point: int_type) -> None:
        pass

    spawn.metadata = {'abbrev': 'b'}


class DoorState(enum.IntEnum):
    closed = 0
    open = 1
    opening = 2
    closing = 3


@attr.s(init=False)
class Door(GameObject):
    state = attr.ib(metadata={'abbrev': 's', 'type': DoorState, 'readonly': True})

    metadata = {'abbrev': 'd'}

    def open(self) -> None:
        pass

    open.metadata = {'abbrev': 'o'}

    def close(self) -> None:
        pass

    close.metadata = {'abbrev': 'c'}


@attr.s(init=False)
class Button(GameObject):
    is_pressed = attr.ib(metadata={'abbrev': 'u', 'type': bool_type, 'readonly': True})

    metadata = {'abbrev': 'b'}

    def press(self) -> None:
        pass

    press.metadata = {'abbrev': 'd'}


@attr.s(init=False)
class Viewport(GameObject):
    pos_x = attr.ib(metadata={'abbrev': 'x', 'type': int_type})
    pos_y = attr.ib(metadata={'abbrev': 'y', 'type': int_type})

    metadata = {'abbrev': 'w'}
