# import pytest

from pyegs.compiler import compile as compile_


def test_if():
    assert compile_('x = 11\nif x > 0: y = 22') == 'p1z 11 # p1z > 0 ( p2z 22 )'
    assert compile_('x = 11\n'
                    'if x > 0:\n'
                    '    y = 22\n'
                    '    z = 33') == 'p1z 11 # p1z > 0 ( p2z 22 p3z 33 )'
    assert compile_('x = 11\nif 0 < x < 5: y = 22') == 'p1z 11 # 0 < p1z & p1z < 5 ( p2z 22 )'
