import pytest

from pyegs.compiler import compile as compile_


def test_call():
    assert compile_('system.message("Hello World")') == 'ym Hello_World'
    assert compile_('system.message_at(10, 10, 1, "Hello World")') == 'yy 10 10 1 Hello_World'
    assert compile_('bots[2].goto(points[1])') == 'a2g 1'
    assert compile_('SPAWNS = [2, 3]; yegiks[2].spawn(SPAWNS[0])') == 'p1z 2 p2z 3 p3z 1+0 e2b p^3z'

    with pytest.raises(NotImplementedError):
        assert compile_('bots[2].goto(point=points[1])')

    with pytest.raises(TypeError) as exc_info:
        compile_('bots[2].goto()')
    assert "missing a required argument: 'point'" in str(exc_info.value)

    assert compile_('GOTO = bots[2].goto; GOTO(points[1])') == 'a2g 1'

    with pytest.raises(TypeError) as exc_info:
        compile_('goto = bots[2].goto; goto(points[1])')
    assert "cannot allocate slot of type '<class 'pyegs.runtime.SignedFunctionType'>'" in str(exc_info.value)

    # assert compile_('x = 2; system.message(x)') == 'p1z 2 ym ^1'
    # assert compile_('s = "Hello World"; system.message(s)') == 's0z Hello_World ym $0'
    # assert compile_('subject = "World"; system.message("Hello {subject}")') == 's0z World ym Hello_$0'
    # assert compile_('n = 2; system.message("Egiks in Quake {n}")') == 'p1z 2 ym Egiks_in_Quake_^1'

    # assert compile_('system.set_color(255, 255, 255)') == 'yc 16777215'
