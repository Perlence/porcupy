import pytest

from porcupy.compiler import compile as compile_


def test_call():
    assert compile_('system.message("Hello World")') == 'ym Hello_World'
    assert compile_('system.message_at(10, 10, 1, "Hello World")') == 'yy 10 10 1 Hello_World'
    assert compile_('yegiks[1].spawn(1)') == 'e2b 1'
    assert compile_('timers[2].start()') == 't2g'
    assert compile_('SPAWNS = [2, 3]; yegiks[1].spawn(SPAWNS[0])') == 'p1z 2 p2z 3 e2b ^1'
    assert compile_('SPAWNS = [2, 3]; yegiks[1].spawn(SPAWNS[0]); yegiks[1].spawn(SPAWNS[1])') == 'p1z 2 p2z 3 e2b ^1 e2b ^2'

    with pytest.raises(NotImplementedError):
        assert compile_('yegiks[1].spawn(point=1)')

    with pytest.raises(TypeError) as exc_info:
        compile_('yegiks[1].spawn()')
    assert "missing a required argument: 'point'" in str(exc_info.value)

    assert compile_('SPAWN = yegiks[1].spawn; SPAWN(1)') == 'e2b 1'

    with pytest.raises(TypeError) as exc_info:
        compile_('spawn = yegiks[1].spawn; spawn(1)')
    assert "cannot allocate slot of type 'GameObjectMethod" in str(exc_info.value)

    assert compile_('x = 2; system.message(x)') == 'p1z 2 ym ^1'
    assert compile_('s = "Hello World"; system.message(s)') == 's0z Hello_World ym $0'

    # assert compile_('subject = "World"; system.message("Hello {subject}")') == 's0z World ym Hello_$0'
    # assert compile_('n = 2; system.message("Egiks in Quake {n}")') == 'p1z 2 ym Egiks_in_Quake_^1'

    # assert compile_('system.set_color(255, 255, 255)') == 'yc 16777215'
