import pytest

from pyegs.compiler import compile as compile_


def test_assign():
    with pytest.raises(NotImplementedError):
        compile_('x, y = 1, 2')

    assert compile_('x = const(4)') == ''
    assert compile_('x = const(4); y = x') == 'p1z 4'

    assert compile_('x = 4') == 'p1z 4'
    assert compile_('x = 4.0') == 'p1z 4,0'
    assert compile_('x = 4; y = 5') == 'p1z 4 p2z 5'
    assert compile_('x = 4; y = x') == 'p1z 4 p2z p1z'
    assert compile_('x = 4; y = x; z = y; y = 5') == 'p1z 4 p2z p1z p3z p2z p2z 5'
    assert compile_('x = 4; y = x; x = y') == 'p1z 4 p2z p1z p1z p2z'

    assert compile_('s = "Hello World"') == 's0z Hello_World'

    with pytest.raises(NameError) as exc_info:
        compile_('x = y')
    assert str(exc_info.value) == "name 'y' is not defined"
