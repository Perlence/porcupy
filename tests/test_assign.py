import pytest

from porcupy.compiler import compile as compile_


@pytest.mark.skip('Not implemented yet')
def test_tuple_assign():
    assert compile_('x, y = 1, 2') == 'p1z 1 p2z 2'


def test_consts():
    assert compile_('X = 4') == ''
    assert compile_('X = 4; y = X') == 'p1z 4'
    assert compile_('X = "HELLO"; y = X') == 's0z HELLO'

    assert compile_('X = 4; Y = X; z = Y') == 'p1z 4'

    with pytest.raises(ValueError) as exc_info:
        compile_('X = 4; X = 5')
    assert 'cannot redefine a constant' in str(exc_info.value)


def test_numbers():
    assert compile_('x = 4') == 'p1z 4'
    assert compile_('x = 4.0') == 'p1z 4'
    assert compile_('x = 4.5') == 'p2z 9 p1z p2z/2'
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


def test_binary_op():
    assert compile_('x = 1+2') == 'p1z 3'
    assert compile_('x = 1+2+3') == 'p1z 6'
    assert compile_('x = 1+2*3') == 'p1z 7'

    assert compile_('x = 1; y = x+2') == 'p1z 1 p2z p1z+2'
    # assert compile_('x = 1; y = x+2+3') == 'p1z 1 p2z p1z+5'
    assert compile_('x = 1; y = x+2+3') == 'p1z 1 p3z p1z+2 p2z p3z+3'
    assert compile_('x = 1; y = x+2*3') == 'p1z 1 p2z p1z+6'
    assert compile_('x = 2; y = 1+x*3') == 'p1z 2 p3z p1z*3 p2z p3z+1'

    assert compile_('x = 1; y = 1-x; y = 1-x') == 'p1z 1 p3z 1 p2z p3z-p1z p3z 1 p2z p3z-p1z'
    assert compile_('x = 5; y = 1/x') == 'p1z 5 p3z 1 p2z p3z/p1z'
    assert compile_('x = 1; y = 1-x*5') == 'p1z 1 p3z 1 p4z p1z*5 p2z p3z-p4z'
    assert compile_('x = 1; y = 1-x*5/2') == 'p1z 1 p3z p1z*5 p4z 1 p5z p3z/2 p2z p4z-p5z'
    assert compile_('x = 1; y = 1-5*x/2') == 'p1z 1 p3z p1z*5 p4z 1 p5z p3z/2 p2z p4z-p5z'


def test_compare():
    # assert compile_('x = 3 < 5') == 'p1z 1'
    # assert compile_('x = 3 < 5 < 6') == 'p1z 1'
    # assert compile_('x = 3 < 5 > 6') == 'p1z 0'

    assert compile_('x = 3; y = x < 5') == 'p1z 3 p3z 0 # p1z < 5 ( p3z 1 ) p2z p3z'
    assert compile_('x = 3; y = x < 5 < 6') == 'p1z 3 p3z 0 # p1z < 5 & 5 < 6 ( p3z 1 ) p2z p3z'


def test_bool_op():
    # assert compile_('x = True and True') == 'p1z 1'
    # assert compile_('x = True or False') == 'p1z 1'

    # assert compile_('x = True; y = True; z = x and y') == 'p1z 1 p2z 1 p3z 0 # p1z ! 0 & p2z ! 0 ( p3z p2z ) p3z p3z'
    # assert compile_('x = True; y = False; z = x or y') == 'p1z 1 p2z 0 p3z 0 # p1z ! 0 | p2z ! 0 ( p3z p1z ) p3z p3z'
    assert compile_('x = True; y = True; z = x and y') == 'p1z 1 p2z 1 p4z 0 # p1z ! 0 & p2z ! 0 ( p4z 1 ) p3z p4z'
    assert compile_('x = True; y = False; z = x or y') == 'p1z 1 p2z 0 p4z 1 # p1z = 0 & p2z = 0 ( p4z 0 ) p3z p4z'

    assert compile_('x = 3; y = x < 5 and x < 6') == 'p1z 3 p3z 0 # p1z < 5 & p1z < 6 ( p3z 1 ) p2z p3z'

    assert (compile_('x = 11; y = x < 12 and (x < 13 or x < 14)') ==
            'p1z 11 '
            'p3z 1 # p1z >= 13 & p1z >= 14 ( p3z 0 ) '
            'p4z 0 # p1z < 12 & p3z ! 0 ( p4z 1 ) p2z p4z')
    assert (compile_('x = 11; y = x < 12 and (x < 13 or x < 14 or x < 15)') ==
            'p1z 11 '
            'p3z 1 # p1z >= 13 & p1z >= 14 & p1z >= 15 ( p3z 0 ) '
            'p4z 0 # p1z < 12 & p3z ! 0 ( p4z 1 ) p2z p4z')
    assert (compile_('x = 11; y = x < 12 and (x < 13 or (x < 14 or x < 15))') ==
            'p1z 11 '
            'p3z 1 # p1z >= 14 & p1z >= 15 ( p3z 0 ) '
            'p4z 1 # p1z >= 13 & p3z = 0 ( p4z 0 ) '
            'p5z 0 # p1z < 12 & p4z ! 0 ( p5z 1 ) p2z p5z')


def test_unary_op():
    assert compile_('x = +4') == 'p1z 4'
    assert compile_('x = -4') == 'p1z -4'
    assert compile_('x = 4; y = -x') == 'p1z 4 p2z p1z*-1'

    assert compile_('x = ~5') == 'p1z -6'
    assert compile_('x = ~-6') == 'p1z 5'
    assert compile_('x = ~True') == 'p1z -2'
    assert compile_('x = ~False') == 'p1z -1'
    # assert compile_('x = 5; y = ~x') == 'p1z 5 p2z p1z*-1 p2z p2z-1'

    # assert compile_('x = not 4') == 'p1z 0'
    # assert compile_('x = not 0') == 'p1z 1'
    # assert compile_('x = not True') == 'p1z 0'
    # assert compile_('x = not False') == 'p1z 1'
    # assert compile_('x = 4; y = not z') == 'p1z 4 p2z 0 # p1z = 0 ( p2z 1 )'


def test_undefined():
    with pytest.raises(NameError) as exc_info:
        compile_('x = y')
    assert "name 'y' is not defined" in str(exc_info.value)


def test_lists():
    with pytest.raises(TypeError) as exc_info:
        assert compile_('x = [1, "2"]')
    assert 'list items must be of the same type' in str(exc_info.value)

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
    assert 'ran out of variable slots' in str(exc_info.value)

    assert compile_('x = [1, 2]; y = x[0]') == 'p1z 1 p2z 2 p3z 1 p5z p3z+0 p6z p^5z p4z p6z'
    assert compile_('x = [1, 2]; y = 0; z = x[y]') == 'p1z 1 p2z 2 p3z 1 p4z 0 p6z p3z+p4z p7z p^6z p5z p7z'

    assert compile_('x = [1, 2]; x[0] = 5') == 'p1z 1 p2z 2 p3z 1 p4z p3z+0 p^4z 5'

    with pytest.raises(IndexError) as exc_info:
        compile_('x = [1, 2]; y = x[2]')
    assert 'list index out of range' in str(exc_info.value)

    # assert compile_('x = [0] * 3') == 'p1z 0 p2z 0 p3z 0 p4z 1'

    # assert compile_('x = [11, 22, 33]; x = [11, 22, 33]') == 'p1z 11 p2z 22 p3z 33 p4z 1 p1z 11 p2z 22 p3z 33'

    assert compile_('x = [1, 2]; x[0] = x[1] = 5') == 'p1z 1 p2z 2 p3z 1 p4z p3z+0 p^4z 5 p5z p3z+1 p^5z 5'

    assert compile_('x = [11, 22]; y = x[0] + x[1]') == 'p1z 11 p2z 22 p3z 1 p5z p3z+0 p6z p^5z p5z p3z+1 p7z p^5z p4z p6z+p7z'


def test_const_list():
    assert compile_('X = [11, 22, 33]') == 'p1z 11 p2z 22 p3z 33'

    assert compile_('X = [11, 22, 33]; y = X[0]') == 'p1z 11 p2z 22 p3z 33 p4z p1z'

    with pytest.raises(ValueError) as exc_info:
        assert compile_('X = [11, 22, 33]; X[0] = 44')
    assert 'cannot modify items' in str(exc_info)

    with pytest.raises(ValueError) as exc_info:
        assert compile_('X = [11, 22, 33]; X[0] += 44')
    assert 'cannot modify items' in str(exc_info)


def test_range():
    assert compile_('X = range(5)') == ''
    assert compile_('X = range(11, 44, 11)') == ''

    assert compile_('X = range(11, 44, 11); y = X[0]; y = X[2]') == 'p1z 11 p1z 33'

    assert compile_('x = range(5)') == ''


def test_multiple_assign():
    assert compile_('x = y = 5') == 'p1z 5 p2z 5'
    assert compile_('x = y = [1, 2]') == 'p1z 1 p2z 2 p3z 1 p4z 1'


def test_game_objects():
    # TODO: Make this assertion work
    # assert compile_('x = system') == ''

    assert compile_('x = yegiks[0].frags') == 'p1z e1f'
    assert compile_('x = 1; y = yegiks[x].frags') == 'p1z 1 p3z p1z+1 p2z e^3f'
    assert compile_('x = 5; y = yegiks[x]') == 'p1z 5 p3z p1z+1 p2z p3z'

    assert compile_('yegiks[0].frags = 99') == 'e1f 99'
    assert compile_('x = yegiks[0]; x.frags = 99') == 'p1z 1 e^1f 99'

    assert compile_('x = yegiks[0]') == 'p1z 1'
    assert compile_('x = [yegiks[0], yegiks[1]]') == 'p1z 1 p2z 2 p3z 1'
    assert (compile_('x = [yegiks[0], yegiks[1]]; y = 1; y = y+3/y; z = x[0].frags') ==
            'p1z 1 p2z 2 p3z 1 p4z 1 p6z 3 p7z p6z/p4z p4z p4z+p7z p7z p3z+0 p6z p^7z p5z e^6f')

    assert compile_('x = timers[2]; x.value = 0') == 'p1z 2 t^1i 0'

    assert compile_('system.bots = 4') == 'yb 4'
    assert compile_('system.color = 256') == 'yc 256'

    assert compile_('x = [yegiks[7], yegiks[8]]; x[0].frags = 55') == 'p1z 8 p2z 9 p3z 1 p4z p3z+0 p5z p^4z e^5f 55'


def test_black_hole():
    assert compile_('_ = 4') == ''


def test_aug_assign():
    assert compile_('x = 5; x += 4') == 'p1z 5 p1z p1z+4'
    assert compile_('x = 5; x -= 4') == 'p1z 5 p1z p1z-4'
    assert compile_('x = 5; x *= 4') == 'p1z 5 p1z p1z*4'
    assert compile_('x = 5; x /= 4') == 'p1z 5 p1z p1z/4'

    assert compile_('yegiks[0].speed_y *= 0.88') == 'p1z 22 p2z p1z/25 e1v e1v*p2z'
    assert compile_('x = 2; yegiks[x].speed_y *= 0.88') == 'p1z 2 p2z 22 p3z p1z+1 p4z p2z/25 e^3v e^3v*p4z'
    assert compile_('YEGS = [yegiks[4], yegiks[5]]; x = 1; YEGS[x].speed_y *= 0.88') == 'p1z 5 p2z 6 p3z 1 p4z 22 p5z p3z+1 p6z p^5z p5z p4z/25 e^6v e^6v*p5z'

    # with pytest.raises(NameError) as exc_info:
    #     compile_('x += 4')
    # assert "name 'x' is not defined" in str(exc_info.value)

    assert compile_('x = yegiks[1].speed_x; x *= -1') == 'p1z e2u p1z p1z*-1'


def test_static_type():
    sources = [
        'x = 1; x = "s"',
        'x = [11, 22, 33]; x = 3',
        'x = [11, 22, 33]; x = [44, 55, 66, 77]',
        'x = range(4); x = 0',
        'x = [11, 22, 33]; y = x[:]; y = [1]',
        # 'bots[2].goto = 4',
    ]

    for source in sources:
        with pytest.raises(TypeError) as exc_info:
            compile_('x = 1; x = "s"')
        assert 'cannot assign object of type' in str(exc_info.value)
