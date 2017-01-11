import pytest

from pyegs.compiler import compile as compile_


@pytest.mark.skip('Not implemented yet')
def test_for():
    assert (compile_('items = [11, 22, 33]\nfor item in items: x = item') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z p4z+0 p5z p^5z p6z p5z '
            'p5z p4z+1 p5z p^5z p6z p5z '
            'p5z p4z+2 p5z p^5z p6z p5z')

    assert (compile_('for x in range(5): y = x') ==
            'p1z 0 p2z p1z '
            'p1z 1 p2z p1z '
            'p1z 2 p2z p1z '
            'p1z 3 p2z p1z '
            'p1z 4 p2z p1z')

    assert (compile_('items = [11, 22, 33]\n'
                     'for i, item in enumerate(items):\n'
                     '    x = i'
                     '    y = item') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 0 p6z p4z+p5z p7z p5z p8z p6z '
            'p5z 1 p6z p4z+p5z p7z p5z p8z p6z '
            'p5z 2 p6z p4z+p5z p7z p5z p8z p6z')
