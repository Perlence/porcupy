import pytest

from porcupy.compiler import compile as compile_


def test_call():
    assert compile_('print("Hello World")') == 'ym Hello_World'
    assert compile_('print_at(10, 10, 1, "Hello World")') == 'yy 10 10 1 Hello_World'
    assert compile_('yozhiks[1].spawn(1)') == 'e2b 1'
    assert compile_('timers[1].start()') == 't2g'
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

    assert compile_('x = 1; yozhiks[0].spawn(x+1)') == 'p1z 1 p2z p1z+1 e1b ^2'

    assert compile_('X = points[0]; Y = points[1]; spawn_sheep(X, Y)') == 'p1z 1 p2z 2 hb ^1 ^2'


def test_print():
    assert compile_('print("Hey")') == 'ym Hey'

    assert compile_('x = 2; print(x)') == 'p1z 2 ym ^1'
    assert compile_('print(yozhiks[0].health)') == 'p1z e1p ym ^1'

    assert compile_('print("Hello", "World")') == 'ym Hello_World'
    assert compile_('x = 500; print_at(10, 10, 1, "Score:", x)') == 'p1z 500 yy 10 10 1 Score:_^1'


def test_set_color():
    assert compile_('set_color(188, 0, 0)') == 'yc 188'
    assert compile_('set_color(0, 188, 0)') == 'yc 48128'
    assert compile_('set_color(0, 0, 188)') == 'yc 12320768'
    assert compile_('set_color(255, 255, 255)') == 'yc 16777215'


def test_format():
    assert compile_('print("Hello {}".format("World"))') == 'ym Hello_World'
    assert compile_('print("Hello {}!".format("World"))') == 'ym Hello_World!'
    assert compile_('N = 2; print("Yozhiks in Quake {}".format(N))') == 'ym Yozhiks_in_Quake_2'
    assert compile_('n = 2; print("Yozhiks in Quake {}".format(n))') == 'p1z 2 ym Yozhiks_in_Quake_^1'
    assert compile_('print("{2}{1}{0}".format("a", "b", "c"))') == 'ym cba'
    assert compile_('print("Health: {}".format(yozhiks[0].health))') == 'p1z e1p ym Health:_^1'
    assert compile_('print("Health: {0.health}".format(yozhiks[0]))') == 'p1z e1p ym Health:_^1'
    assert compile_('print("Health: {.health}".format(yozhiks[0]))') == 'p1z e1p ym Health:_^1'
    assert compile_('print("Health: {[0].health}".format(yozhiks))') == 'p1z e1p ym Health:_^1'


@pytest.mark.xfail
def test_unused_result():
    unused = [
        'slice(int, 0, 1)',
        'x = slice(int, 0, 5); len(x)',
        'x = slice(int, 0, 5); cap(x)',
        'randint(0, 5)',
        'range(5)',
        'x = slice(int, 5); reversed(x)',
    ]
    for source in unused:
        with pytest.raises(ValueError) as exc_info:
            compile_(source)
        assert 'function return value is unused' in str(exc_info)


def test_type_check():
    wrong_types = [
        'slice(int, "4")',
        'randint(3, "5")',
    ]
    for source in wrong_types:
        with pytest.raises(TypeError) as exc_info:
            compile_(source)
        assert 'argument of type' in str(exc_info)
