import pytest

from porcupy.compiler import compile as compile_


def test_call():
    assert compile_('print("Hello World")') == 'ym Hello_World'
    assert compile_('print_at(10, 10, 1, "Hello World")') == 'yy 10 10 1 Hello_World'
    assert compile_('yozhiks[1].spawn(1)') == 'e2b 1'
    assert compile_('timers[2].start()') == 't2g'
    assert compile_('SPAWNS = [2, 3]; yozhiks[1].spawn(SPAWNS[0])') == 'p1z 2 p2z 3 e2b ^1'
    assert compile_('SPAWNS = [2, 3]; yozhiks[1].spawn(SPAWNS[0]); yozhiks[1].spawn(SPAWNS[1])') == 'p1z 2 p2z 3 e2b ^1 e2b ^2'

    with pytest.raises(NotImplementedError):
        assert compile_('yozhiks[1].spawn(point=1)')

    with pytest.raises(TypeError) as exc_info:
        compile_('yozhiks[1].spawn()')
    assert "missing a required argument: 'point'" in str(exc_info.value)

    assert compile_('SPAWN = yozhiks[1].spawn; SPAWN(1)') == 'e2b 1'

    with pytest.raises(TypeError) as exc_info:
        compile_('spawn = yozhiks[1].spawn; spawn(1)')
    assert "cannot allocate slot of type 'GameObjectMethod" in str(exc_info.value)

    assert compile_('print("Hey")') == 'ym Hey'

    assert compile_('x = 2; print(x)') == 'p1z 2 ym ^1'
    assert compile_('s = "Hello World"; print(s)') == 's0z Hello_World ym $0'
    # assert compile_('print(yozhiks[0].health)') == 'p1z e1h ym ^1'

    # assert compile_('subject = "World"; print("Hello {subject}")') == 's0z World ym Hello_$0'
    # assert compile_('n = 2; print("Yozhiks in Quake {n}")') == 'p1z 2 ym Yozhiks_in_Quake_^1'

    # assert compile_('system.set_color(255, 255, 255)') == 'yc 16777215'
