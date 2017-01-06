import pytest

from pyegs.compiler import compile as compile_


def test_if():
    assert compile_('x = 11\nif x > 0: y = 22') == 'p1z 11 # p1z > 0 ( p2z 22 )'
    assert compile_('x = 11\n'
                    'if x > 0:\n'
                    '    y = 22\n'
                    '    z = 33') == 'p1z 11 # p1z > 0 ( p2z 22 p3z 33 )'
    assert compile_('x = 11\nif 0 < x < 5: y = 22') == 'p1z 11 # 0 < p1z & p1z < 5 ( p2z 22 )'

    with pytest.skip():
        assert compile_('x = 11\nif x < 12 and x < 13: y = 22') == 'p1z 11 # p1z < 12 & p1z < 13 ( p2z 22 )'
        assert compile_('x = 11\nif x < 12 and x < 13 and x < 14: y = 22') == 'p1z 11 # p1z < 12 & p1z < 13 & p1z < 14 ( p2z 22 )'
        assert compile_('x = 11\nif x < 12 and x < 13 or x < 14: y = 22') == 'p1z 11 # p1z < 12 & p1z < 13 | p1z < 14 ( p2z 22 )'
