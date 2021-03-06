import pytest

from porcupy.compiler import compile as compile_


def test_iterate_lists():
    assert (compile_('items = [11, 22, 33]\n'
                     'for item in items:\n'
                     '    print(item)') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z -1 '
            ':1 p6z p6z+1 # p6z >= 3 ( g2z ) '
            'p7z p4z+p6z p8z p^7z p5z p8z '
            'ym ^5 '
            'g1z '
            ':2')

    assert (compile_('items = [[11, 22, 33]]\n'
                     'for item in items[0]:\n'
                     '    print(item)') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 p5z 4 '
            'p7z -1 p8z p5z+0 p9z p^8z '
            ':1 p7z p7z+1 # p7z >= 3 ( g2z ) '
            'p8z p9z+p7z p10z p^8z '
            'p6z p10z '
            'ym ^6 '
            'g1z '
            ':2')

    assert (compile_('items = [[11], [22], [33]]\n'
                     'for list in items:\n'
                     '    for item in list:\n'
                     '        print(item)') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 p5z 2 p6z 3 p7z 4 '
            'p10z -1 '
            ':1 p10z p10z+1 # p10z >= 3 ( g2z ) '
            'p11z p7z+p10z p12z p^11z '
            'p8z p12z '
            'p12z -1 '
            ':3 p12z p12z+1 # p12z >= 1 ( g4z ) '
            'p11z p8z+p12z p13z p^11z '
            'p9z p13z '
            'ym ^9 '
            'g3z '
            ':4 '
            'g1z '
            ':2')

    assert (compile_('items = [11, 22, 33]\n'
                     'for _ in items:\n'
                     '    print("hey")') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z -1 :1 p5z p5z+1 # p5z >= 3 ( g2z ) ym hey g1z '
            ':2')


def test_iterate_game_objs():
    assert (compile_('for bot in bots:\n'
                     '    bot.goto = points[0]') ==
            'p2z -1 '
            ':1 p2z p2z+1 # p2z >= 9 ( g2z ) p3z p2z+1 p1z p3z a^1g 1 g1z :2')


def test_break():
    assert (compile_('items = [11, 22, 33]\n'
                     'for item in items:\n'
                     '    if item > 23:\n'
                     '        break\n'
                     '    print(item)') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z -1 '
            ':1 p6z p6z+1 # p6z >= 3 ( g2z ) '
            'p7z p4z+p6z p8z p^7z p5z p8z '
            '# p5z <= 23 ( g3z ) '
            'g2z '
            ':3 '
            'ym ^5 '
            'g1z '
            ':2')


def test_continue():
    assert (compile_('items = [11, 22, 33]\n'
                     'for item in items:\n'
                     '    if item < 20:\n'
                     '        continue\n'
                     '    print(item)') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z -1 '
            ':1 p6z p6z+1 # p6z >= 3 ( g2z ) '
            'p7z p4z+p6z p8z p^7z '
            'p5z p8z '
            '# p5z >= 20 ( g3z ) '
            'g1z '
            ':3 '
            'ym ^5 '
            'g1z '
            ':2')


def test_range():
    assert (compile_('for item in range(1, 40, 3): print(item)') ==
            'p2z -1 '
            ':1 p2z p2z+1 '
            '# p2z >= 13 ( g2z ) '
            'p3z p2z*3 p1z p3z+1 '
            'ym ^1 '
            'g1z '
            ':2')

    assert (compile_('x = 40\n'
                     'for item in range(1, x, 3):\n'
                     '    print(item)') ==
            'p1z 40 '
            'p3z -1 '
            'p4z p1z-1 '
            ':1 p3z p3z+1 '
            '# p3z >= p4z{3 ( g2z ) '
            'p5z p3z*3 p2z p5z+1 '
            'ym ^2 '
            'g1z '
            ':2')


def test_enumerate():
    assert (compile_('items = [11, 22, 33]\n'
                     'for i, item in items:\n'
                     '    print(i)\n'
                     '    print(item)') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z -1 '
            ':1 p5z p5z+1 # p5z >= 3 ( g2z ) '
            'p7z p4z+p5z p8z p^7z p6z p8z '
            'ym ^5 '
            'ym ^6 '
            'g1z '
            ':2')

    with pytest.raises(ValueError) as exc_info:
        compile_('items = [11, 22, 33]\n'
                 'for i, item, extra in items:\n'
                 '    print(i)\n'
                 '    print(item)')
    assert 'exactly 2 receiver variables required' in str(exc_info.value)


def test_reversed():
    assert (compile_('items = [11, 22, 33]\n'
                     'for item in reversed(items):\n'
                     '    print(item)') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z -1 '
            ':1 p6z p6z+1 # p6z >= 3 ( g2z ) '
            'p7z 2 p9z p7z-p6z p8z p4z+p9z p10z p^8z p5z p10z '
            'ym ^5 '
            'g1z '
            ':2')
    assert (compile_('items = [11, 22, 33][:]\n'
                     'for item in reversed(items):\n'
                     '    print(item)') ==
            'p1z 11 p2z 22 p3z 33 p4z 10303 '
            'p6z -1 '
            ':1 p6z p6z+1 # p6z >= p4z}100 ( g2z ) '
            'p7z p4z}100 p8z p7z-1 p10z p4z{10000 p11z p8z-p6z p9z p10z+p11z p12z p^9z p5z p12z '
            'ym ^5 '
            'g1z '
            ':2')
