import ast
import enum

import attr

from .ast import Const, Slot, Assign, Call
from .types import IntType, FloatType, BoolType, StringType, GameObject

int_type = IntType()
bool_type = BoolType()
float_type = FloatType()
str_type = StringType()

# TODO: Use enumerations in attribute metadata


@attr.s(init=False)
class Timer(GameObject):
    value = attr.ib(metadata={'abbrev': 'i', 'type': int_type})
    enabled = attr.ib(metadata={'abbrev': 'r', 'type': bool_type, 'readonly': True})

    metadata = {'abbrev': 't'}

    def start(self, converter):
        pass

    start.metadata = {'abbrev': 'g'}

    def stop(self, converter):
        pass

    stop.metadata = {'abbrev': 's'}


class FragLimit(enum.IntEnum):
    ten = 1
    twenty = 2
    thirty = 3
    fifty = 4
    one_hundred = 5
    two_hundred = 6


class GameMode(enum.IntEnum):
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
    game_mode = attr.ib(metadata={'abbrev': 'g', 'type': int_type, 'readonly': True})

    metadata = {'abbrev': 'y'}

    def print(self, converter, *values):
        slot = Slot('y', None, 'm', None)
        interspaced = self._interspace(values)
        return Call(slot, [Const(interspaced)])

    print.metadata = {'abbrev': 'm'}

    def print_at(self, converter, x: FloatType, y: FloatType, dur: FloatType, *values):
        slot = Slot('y', None, 'y', None)
        interspaced = self._interspace(values)
        return Call(slot, [x, y, dur, Const(interspaced)])

    print_at.metadata = {'abbrev': 'y'}

    def set_color(self, converter, r: IntType, g: IntType, b: IntType):
        # system.color = r + g * 256 + b * 65536
        color = converter.visit(ast.BinOp(ast.BinOp(r, ast.Add(),
                                                    ast.BinOp(g, ast.Mult(), Const(256))), ast.Add(),
                                          ast.BinOp(b, ast.Mult(), Const(65536))))
        sys_slot = Slot(self.metadata['abbrev'], None, self.color.metadata['abbrev'], self.color.metadata['type'])
        converter.append_to_body(Assign(sys_slot, color))

    def load_map(self, converter, name: StringType):
        pass

    load_map.metadata = {'abbrev': 'l'}

    def _interspace(self, seq):
        result = [seq[0]]
        for item in seq[1:]:
            result.append(' ')
            result.append(item)
        return result


@attr.s(init=False)
class Point(GameObject):
    pos_x = attr.ib(metadata={'abbrev': 'x', 'type': float_type})
    pos_y = attr.ib(metadata={'abbrev': 'y', 'type': float_type})

    metadata = {'abbrev': 'c'}


class Weapon(enum.IntEnum):
    bfg10k = 0
    blaster = 1
    shotgun = 2
    super_shotgun = 3
    machine_gun = 4
    chain_gun = 5
    grenade_launcher = 6
    rocket_launcher = 7
    hyperblaster = 8
    railgun = 9


@attr.s(init=False)
class Yozhik(GameObject):
    frags = attr.ib(metadata={'abbrev': 'f', 'type': int_type})
    pos_x = attr.ib(metadata={'abbrev': 'x', 'type': float_type})
    pos_y = attr.ib(metadata={'abbrev': 'y', 'type': float_type})
    speed_x = attr.ib(metadata={'abbrev': 'u', 'type': float_type})
    speed_y = attr.ib(metadata={'abbrev': 'v', 'type': float_type})
    health = attr.ib(metadata={'abbrev': 'p', 'type': int_type})
    armor = attr.ib(metadata={'abbrev': 'n', 'type': int_type})
    is_weapon_in_inventory = attr.ib(metadata={'abbrev': 'e', 'type': bool_type})
    weapon = attr.ib(metadata={'abbrev': 'w', 'type': int_type})
    ammo = attr.ib(metadata={'abbrev': 's', 'type': int_type})
    view_angle = attr.ib(metadata={'abbrev': 'a', 'type': float_type})
    team = attr.ib(metadata={'abbrev': 't', 'type': int_type})

    metadata = {'abbrev': 'e'}

    def spawn(self, converter, point: IntType):
        pass

    spawn.metadata = {'abbrev': 'b'}


class BotLevel(enum.IntEnum):
    very_easy = 1
    easy = 2
    normal = 3
    hard = 4
    impossible = 5


@attr.s(init=False)
class Bot(GameObject):
    ai = attr.ib(metadata={'abbrev': 'i', 'type': bool_type})
    target = attr.ib(metadata={'abbrev': 't', 'type': Yozhik()})
    level = attr.ib(metadata={'abbrev': 'l', 'type': int_type})
    point = attr.ib(metadata={'abbrev': 'p', 'type': int_type, 'readonly': True})
    goto = attr.ib(metadata={'abbrev': 'g', 'type': Point()})
    can_see_target = attr.ib(metadata={'abbrev': 's', 'type': bool_type, 'readonly': True})

    metadata = {'abbrev': 'a'}


@attr.s(init=False)
class Sheep(GameObject):
    metadata = {'abbrev': 'h'}

    def spawn(self, converter, start: Point, finish: Point):
        pass

    spawn.metadata = {'abbrev': 'b'}


class DoorState(enum.IntEnum):
    closed = 0
    open = 1
    opening = 2
    closing = 3


@attr.s(init=False)
class Door(GameObject):
    state = attr.ib(metadata={'abbrev': 's', 'type': int_type, 'readonly': True})

    metadata = {'abbrev': 'd'}

    def open(self, converter):
        pass

    open.metadata = {'abbrev': 'o'}

    def close(self, converter):
        pass

    close.metadata = {'abbrev': 'c'}


@attr.s(init=False)
class Button(GameObject):
    is_pressed = attr.ib(metadata={'abbrev': 'u', 'type': bool_type, 'readonly': True})

    metadata = {'abbrev': 'b'}

    def press(self, converter):
        pass

    press.metadata = {'abbrev': 'd'}


@attr.s(init=False)
class Viewport(GameObject):
    pos_x = attr.ib(metadata={'abbrev': 'x', 'type': int_type})
    pos_y = attr.ib(metadata={'abbrev': 'y', 'type': int_type})

    metadata = {'abbrev': 'w'}
