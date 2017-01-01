import pytest

from pyegs.compiler import compile as compile_


@pytest.mark.skip('Not implemented yet')
def test_tuple_assign():
    compile_('x, y = 1, 2')


def test_consts():
    assert compile_('X = 4') == ''
    assert compile_('X = 4; y = X') == 'p1z 4'
    assert compile_('X = "HELLO"; y = X') == 's0z HELLO'

    assert compile_('X = 4; Y = X; z = Y') == 'p1z 4'

    with pytest.skip('Not implemented yet'):
        with pytest.raises(TypeError) as exc_info:
            compile_('X = 4; X = 5')
        assert str(exc_info.value) == 'cannot redefine a constant'


def test_numbers():
    assert compile_('x = 4') == 'p1z 4'
    assert compile_('x = 4.0') == 'p1z 4,0'
    assert compile_('x = 4; y = 5') == 'p1z 4 p2z 5'
    assert compile_('x = 4; x = 5') == 'p1z 4 p1z 5'


def test_other_names():
    assert compile_('x = 4; y = x') == 'p1z 4 p2z p1z'
    assert compile_('x = 4; y = x; z = y; y = 5') == 'p1z 4 p2z p1z p3z p2z p2z 5'
    assert compile_('x = 4; y = x; x = y') == 'p1z 4 p2z p1z p1z p2z'


def test_strings():
    assert compile_('s = "Hello World"') == 's0z Hello_World'


def test_bools():
    assert compile_('x = False') == 'p1z 0'
    assert compile_('x = True') == 'p1z 1'


def test_undefined():
    with pytest.raises(NameError) as exc_info:
        compile_('x = y')
    assert str(exc_info.value) == "name 'y' is not defined"


def test_lists():
    with pytest.raises(TypeError) as exc_info:
        assert compile_('x = [1, "2"]')
    assert str(exc_info.value) == 'list items must be of the same type'

    assert compile_('x = [1, 2]') == 'p1z 1 p2z 2 p3z 1'
    assert compile_('x = 1; y = [2, 3]') == 'p1z 1 p2z 2 p3z 3 p4z 2'

    assert compile_('x = 1; y = ["1", "2"]') == 'p1z 1 s0z 1 s1z 2 p2z 0'
    assert compile_('x = 1; y = ["Hello World", "beep boop"]') == 'p1z 1 s0z Hello_World s1z beep_boop p2z 0'

    assert compile_('x = [1, 2, 3]; y = x') == 'p1z 1 p2z 2 p3z 3 p4z 1 p5z p4z'

    assert compile_('x = [[11, 22], [33, 44]]') == 'p1z 11 p2z 22 p3z 33 p4z 44 p5z 1 p6z 3 p7z 5'

    assert compile_('x = [1, 2]; y = [3, 4]; z = [x, y]') == 'p1z 1 p2z 2 p3z 1 p4z 3 p5z 4 p6z 4 p7z p3z p8z p6z p9z 7'

    # List with 99 elements in it causes a MemoryError
    with pytest.raises(MemoryError) as exc_info:
        compile_('x = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'
                 '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'
                 '0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'
                 '0,0,0,0,0,0,0,0,0,0,0,0]')
    assert str(exc_info.value) == 'ran out of variable slots'

    assert compile_('x = [1, 2]; y = x[0]') == 'p1z 1 p2z 2 p3z 1 p4z p3z+0 p4z p^4z'
    assert compile_('x = [1, 2]; y = 0; z = x[y]') == 'p1z 1 p2z 2 p3z 1 p4z 0 p5z p3z+p4z p5z p^5z'

    assert compile_('x = [1, 2]; x[0] = 5') == 'p1z 1 p2z 2 p3z 1 p4z p3z+0 p^4z 5'

    with pytest.raises(IndexError) as exc_info:
        compile_('x = [1, 2]; y = x[2]')
    assert 'list index out of range' in str(exc_info.value)

    with pytest.skip('Not implemented yet'):
        assert compile_('x = [0] * 3') == 'p1z 0 p2z 0 p3z 0 p4z 1'

    # Constant list pointer
    assert compile_('X = [11, 22, 33]') == 'p1z 11 p2z 22 p3z 33'

    assert compile_('X = [11, 22, 33]; y = X[0]') == 'p1z 11 p2z 22 p3z 33 p4z 1+0 p4z p^4z'

    with pytest.skip('Constant list pointer subscription optimization is not implemented yet'):
        assert compile_('X = [11, 22, 33]; y = X[0]') == 'p1z 11 p2z 22 p3z 33 p4z 11'


def test_multiple_assign():
    assert compile_('x = y = 5') == 'p1z 5 p2z 5'
    assert compile_('x = y = [1, 2]') == 'p1z 1 p2z 2 p3z 1 p4z 1'


def test_game_objects():
    assert compile_('x = yegiks[1].frags') == 'p1z e1f'
    assert compile_('x = 1; y = yegiks[x].frags') == 'p1z 1 p2z e^1f'
    assert compile_('x = 1; y = yegiks[x]') == 'p1z 1 p2z p1z'

    assert compile_('yegiks[1].frags = 99') == 'e1f 99'
    assert compile_('x = yegiks[1]; x.frags = 99') == 'p1z 1 e^1f 99'

    assert compile_('x = yegiks[1]') == 'p1z 1'
    assert compile_('x = [yegiks[1], yegiks[2]]') == 'p1z 1 p2z 2 p3z 1'

    assert compile_('x = timers[2]; x.value = 0') == 'p1z 2 t^1i 0'

    assert compile_('system.bots = 4') == 'yb 4'
    assert compile_('system.color = 256') == 'yc 256'

    assert compile_('x = [yegiks[8], yegiks[9]]; x[0].frags = 55') == 'p1z 8 p2z 9 p3z 1 p4z p3z+0 p4z p^4z e^4f 55'


@pytest.mark.skip('Not implemented yet')
def test_static_type():
    with pytest.raises(TypeError) as exc_info:
        assert compile_('x = 1; x = "s"')
    assert str(exc_info.value) == "cannot assign string 's' to numeric variable"
