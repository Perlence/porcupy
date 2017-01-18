import pytest

from pyegs.compiler import compile as compile_


def test_iterate_lists():
    assert (compile_('items = [11, 22, 33]\n'
                     'for item in items:\n'
                     '    system.message(item)') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z -1 '
            ':1 p6z p6z+1 # p6z >= 3 ( g2z ) '
            'p7z p4z+p6z p8z p^7z p5z p8z '
            'ym ^5 '
            'g1z '
            ':2')

    assert (compile_('items = [[11, 22, 33]]\n'
                     'for item in items[0]:\n'
                     '    system.message(item)') ==
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
                     '        system.message(item)') ==
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
                     '    system.message("hey")') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z -1 :1 p5z p5z+1 # p5z >= 3 ( g2z ) ym hey g1z '
            ':2')


def test_iterate_game_objs():
    assert (compile_('for bot in bots:\n'
                     '    bot.goto = 0') ==
            'p2z -1 '
            ':1 p2z p2z+1 # p2z >= 9 ( g2z ) p3z p2z+1 p1z p3z a^1g 0 g1z :2')


def test_break():
    assert (compile_('items = [11, 22, 33]\n'
                     'for item in items:\n'
                     '    if item > 23:\n'
                     '        break\n'
                     '    system.message(item)') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z -1 '
            ':1 p6z p6z+1 # p6z >= 3 ( g2z ) '
            'p7z p4z+p6z p8z p^7z p5z p8z '
            'p8z 0 # p5z > 23 ( p8z 1 ) # p8z = 0 ( g3z ) '
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
                     '    system.message(item)') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z -1 '
            ':1 p6z p6z+1 # p6z >= 3 ( g2z ) '
            'p7z p4z+p6z p8z p^7z '
            'p5z p8z '
            'p8z 0 # p5z < 20 ( p8z 1 ) # p8z = 0 ( g3z ) '
            'g1z '
            ':3 '
            'ym ^5 '
            'g1z '
            ':2')


def test_range():
    assert (compile_('for item in range(1, 40, 3): system.message(item)') ==
            'p2z -1 '
            ':1 p2z p2z+1 '
            '# p2z >= 13 ( g2z ) '
            'p3z p2z*3 p1z p3z+1 '
            'ym ^1 '
            'g1z '
            ':2')

    assert (compile_('x = 40\n'
                     'for item in range(1, x, 3):\n'
                     '    system.message(item)') ==
            'p1z 40 '
            'p3z -1 '
            'p4z p1z-1 '
            ':1 p3z p3z+1 '
            '# p3z >= p4z{3 ( g2z ) '
            'p5z p3z*3 p2z p5z+1 '
            'ym ^2 '
            'g1z '
            ':2')


@pytest.mark.skip('Not implemented yet')
def test_enumerate():
    assert (compile_('items = [11, 22, 33]\n'
                     'for i, item in enumerate(items):\n'
                     '    x = i\n'
                     '    y = item') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 0 p6z p4z+p5z p7z p5z p8z p6z '
            'p5z 1 p6z p4z+p5z p7z p5z p8z p6z '
            'p5z 2 p6z p4z+p5z p7z p5z p8z p6z')
