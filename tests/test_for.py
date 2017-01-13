import pytest

from pyegs.compiler import compile as compile_


def test_iterate_lists():
    assert (compile_('items = [11, 22, 33]\n'
                     'for item in items:\n'
                     '    x = item') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p7z p4z+0 p5z p^7z p6z p5z '
            'p7z p4z+1 p5z p^7z p6z p5z '
            'p7z p4z+2 p5z p^7z p6z p5z '
            ':1')

    assert (compile_('items = [[11, 22, 33]]\n'
                     'for item in items[0]:\n'
                     '    x = item') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 p5z 4 '
            'p8z p5z+0 '
            'p9z p^8z+0 p6z p^9z p7z p6z '
            'p9z p^8z+1 p6z p^9z p7z p6z '
            'p9z p^8z+2 p6z p^9z p7z p6z '
            ':1')

    assert (compile_('items = [[11], [22], [33]]\n'
                     'for list in items:\n'
                     '    for item in list:\n'
                     '        x = item') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 p5z 2 p6z 3 p7z 4 '
            'p11z p7z+0 p8z p^11z p12z p8z+0 p9z p^12z p10z p9z :2 '
            'p11z p7z+1 p8z p^11z p12z p8z+0 p9z p^12z p10z p9z :3 '
            'p11z p7z+2 p8z p^11z p12z p8z+0 p9z p^12z p10z p9z :4 '
            ':1')

    assert (compile_('items = [11, 22, 33]\n'
                     'for _ in items:\n'
                     '    system.message("hey")') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'ym hey '
            'ym hey '
            'ym hey '
            ':1')


def test_break():
    assert (compile_('items = [11, 22, 33]\n'
                     'for item in items:\n'
                     '    if item > 20:\n'
                     '        break') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z p4z+0 p5z p^6z p7z 0 # p5z > 20 ( p7z 1 ) # p7z ! 0 ( g1z ) '
            'p6z p4z+1 p5z p^6z p8z 0 # p5z > 20 ( p8z 1 ) # p8z ! 0 ( g1z ) '
            'p6z p4z+2 p5z p^6z p9z 0 # p5z > 20 ( p9z 1 ) # p9z ! 0 ( g1z ) '
            ':1')


@pytest.mark.skip('Not implemented yet')
def test_continue():
    assert (compile_('items = [11, 22, 33]\n'
                     'for item in items:\n'
                     '    if item < 20:\n'
                     '        continue\n'
                     '    y = 22') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z p4z+0 p6z p^6z p7z 1 p8z 0 # p6z < 20 ( p8z 1 ) # p8z ! 0 ( p7z 0 ) # p7z ! 0 ( p5z 22 ) '
            'p6z p4z+1 p6z p^6z p7z 1 p8z 0 # p6z < 20 ( p8z 1 ) # p8z ! 0 ( p7z 0 ) # p7z ! 0 ( p5z 22 ) '
            'p6z p4z+1 p6z p^6z p7z 1 p8z 0 # p6z < 20 ( p8z 1 ) # p8z ! 0 ( p7z 0 ) # p7z ! 0 ( p5z 22 ) '
            ':2')


def test_range():
    assert (compile_('for x in range(5): y = x') ==
            'p1z 0 p2z p1z '
            'p1z 1 p2z p1z '
            'p1z 2 p2z p1z '
            'p1z 3 p2z p1z '
            'p1z 4 p2z p1z '
            ':1')


@pytest.mark.skip('Not implemented yet')
def test_enumerate():
    assert (compile_('items = [11, 22, 33]\n'
                     'for i, item in enumerate(items):\n'
                     '    x = i'
                     '    y = item') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 0 p6z p4z+p5z p7z p5z p8z p6z '
            'p5z 1 p6z p4z+p5z p7z p5z p8z p6z '
            'p5z 2 p6z p4z+p5z p7z p5z p8z p6z')
