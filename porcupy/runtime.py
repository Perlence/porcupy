import enum

import attr

from .types import IntType, FloatType, BoolType, StringType, GameObjectRef, GameObjectMethod

int_type = IntType()
bool_type = BoolType()
float_type = FloatType()
str_type = StringType()


@attr.s
class Timer:
    value = attr.ib(metadata={'abbrev': 'i', 'type': int_type})
    enabled = attr.ib(metadata={'abbrev': 'r', 'type': bool_type, 'readonly': True})

    metadata = {'abbrev': 't'}

    def start(self) -> None:
        pass

    start.metadata = {'abbrev': 'g', 'type': GameObjectMethod(start)}

    def stop(self) -> None:
        pass

    stop.metadata = {'abbrev': 's', 'type': GameObjectMethod(stop)}


# TODO: Populate scope with enums


class GameMode(enum.Enum):
    multi_lan = 1
    multi_duel = 2
    hot_seat = 3
    menu = 4
    single = 5
    sheep = 6
    hot_seat_split = 7


@attr.s
class System:
    bots = attr.ib(metadata={'abbrev': 'b', 'type': int_type})
    color = attr.ib(metadata={'abbrev': 'c', 'type': int_type})
    frag_limit = attr.ib(metadata={'abbrev': 'f', 'type': int_type})
    game_mode = attr.ib(metadata={'abbrev': 'g', 'type': GameMode, 'readonly': True})

    metadata = {'abbrev': 'y'}

    def print(self, s: str_type) -> None:
        pass

    print.metadata = {'abbrev': 'm', 'type': GameObjectMethod(print)}

    def print_at(self, x: float_type, y: float_type, dur: float_type, s: str_type) -> None:
        pass

    print_at.metadata = {'abbrev': 'y', 'type': GameObjectMethod(print_at)}

    # def set_color(self, r: int_type, g: int_type, b: int_type) -> None:
    #     self.color = r + (g << 8) + (b << 16)

    # set_color.metadata = {'type': GameObjectMethod(set_color)}

    def load_map(self, name: str_type) -> None:
        pass

    load_map.metadata = {'abbrev': 'l', 'type': GameObjectMethod(load_map)}


@attr.s
class Point:
    pos_x = attr.ib(metadata={'abbrev': 'x', 'type': float_type})
    pos_y = attr.ib(metadata={'abbrev': 'y', 'type': float_type})

    metadata = {'abbrev': 'c'}


@attr.s
class Bot:
    ai = attr.ib(metadata={'abbrev': 'i', 'type': bool_type})
    target = attr.ib(metadata={'abbrev': 't', 'type': int_type})
    level = attr.ib(metadata={'abbrev': 'l', 'type': int_type})
    point = attr.ib(metadata={'abbrev': 'p', 'type': int_type, 'readonly': True})
    goto = attr.ib(metadata={'abbrev': 'g', 'type': GameObjectRef(Point)})
    can_see_target = attr.ib(metadata={'abbrev': 's', 'type': bool_type, 'readonly': True})

    metadata = {'abbrev': 'a'}


@attr.s
class Yozhik:
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

    spawn.metadata = {'abbrev': 'b', 'type': GameObjectMethod(spawn)}


@attr.s
class Sheep:
    def spawn(self, point: int_type) -> None:
        pass

    spawn.metadata = {'abbrev': 'b', 'type': GameObjectMethod(spawn)}


class DoorState(enum.IntEnum):
    closed = 0
    open = 1
    opening = 2
    closing = 3


@attr.s
class Door:
    state = attr.ib(metadata={'abbrev': 's', 'type': DoorState, 'readonly': True})

    metadata = {'abbrev': 'd'}

    def open(self) -> None:
        pass

    open.metadata = {'abbrev': 'o', 'type': GameObjectMethod(open)}

    def close(self) -> None:
        pass

    close.metadata = {'abbrev': 'c', 'type': GameObjectMethod(close)}


@attr.s
class Button:
    is_pressed = attr.ib(metadata={'abbrev': 'u', 'type': bool_type, 'readonly': True})

    metadata = {'abbrev': 'b'}

    def press(self) -> None:
        pass

    press.metadata = {'abbrev': 'd', 'type': GameObjectMethod(press)}


@attr.s
class Viewport:
    pos_x = attr.ib(metadata={'abbrev': 'x', 'type': int_type})
    pos_y = attr.ib(metadata={'abbrev': 'y', 'type': int_type})

    metadata = {'abbrev': 'w'}
