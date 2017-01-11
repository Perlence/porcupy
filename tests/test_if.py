from pyegs.compiler import compile as compile_


def test_optimized_if():
    assert compile_('if 0: x = 11') == ''
    assert compile_('if 1: x = 11') == 'p1z 11'

    assert compile_("if '': x = 11") == ''
    assert compile_("if 'beep': x = 11") == 'p1z 11'

    assert compile_('if None: x = 11') == ''
    assert compile_('if False: x = 11') == ''
    assert compile_('if True: x = 11') == 'p1z 11'

    assert compile_('if []: x = 11') == ''
    assert compile_('if [1, 2, 3]: x = 11') == 'p1z 11'

    # assert compile_('x = 11\nif 5 + 7 and True: y = 22') == 'p1z 11 p2z 22'


def test_generic_if():
    # Test is Compare
    assert compile_('x = 11\nif x > 0: y = 22') == 'p1z 11 p2z 0 # p1z > 0 ( p2z 1 ) # p2z ! 0 ( p2z 22 )'
    assert compile_('x = 11\n'
                    'if x > 0:\n'
                    '    y = 22\n'
                    '    z = 33') == 'p1z 11 p2z 0 # p1z > 0 ( p2z 1 ) # p2z ! 0 ( p2z 22 p3z 33 )'
    assert (compile_('x = 11\n'
                     'if 0 < x < 5: y = 22') ==
            'p1z 11 '
            'p2z 0 # 0 < p1z & p1z < 5 ( p2z 1 ) # p2z ! 0 ( p2z 22 )')
    assert (compile_('x = 11; y = 12\n'
                     'if 0 < x < y < 5: y = 22') ==
            'p1z 11 p2z 12 '
            'p3z 0 # 0 < p1z & p1z < p2z & p2z < 5 ( p3z 1 ) # p3z ! 0 ( p2z 22 )')
    assert (compile_('x = [11, 22, 33]\n'
                     'if x[0] > 0: y = 44') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z p4z+0 p6z 0 # p^5z > 0 ( p6z 1 ) # p6z ! 0 ( p5z 44 )')

    # Test is BoolOp
    assert (compile_('x = 11\n'
                     'if x < 12 and x < 13: y = 22') ==
            'p1z 11 p2z 0 # p1z < 12 & p1z < 13 ( p2z 1 ) # p2z ! 0 ( p2z 22 )')
    assert (compile_('x = 11\n'
                     'if x < 12 and x < 13 and x < 14: y = 22') ==
            'p1z 11 p2z 0 # p1z < 12 & p1z < 13 & p1z < 14 ( p2z 1 ) # p2z ! 0 ( p2z 22 )')

    # Chaining different bool operations is broken in Egiks, resort to
    # this workaround instead
    assert (compile_('x = 11\n'
                     'if x < 12 and x < 13 or x < 14: y = 22') ==
            'p1z 11 '
            'p2z 0 # p1z < 12 & p1z < 13 ( p2z 1 ) '
            'p3z 0 # p2z ! 0 | p1z < 14 ( p3z 1 ) # p3z ! 0 ( p2z 22 )')

    # assert compile_('x = 11\nif x < 5 + 7: y = 22') == 'p1z 11 # p1z < 12 ( p2z 22 )'
    assert compile_('x = 11; y = 22\nif x < y + 7: z = 33') == 'p1z 11 p2z 22 p3z 0 # p1z < p2z+7 ( p3z 1 ) # p3z ! 0 ( p3z 33 )'

    # Test is BinOp
    assert compile_('x = 1\nif x + 2: y = 22') == 'p1z 1 # p1z+2 ! 0 ( p2z 22 )'
    # Test is UnaryOp
    assert compile_('x = -1\nif -x: y = 22') == 'p1z -1 # p1z*-1 ! 0 ( p2z 22 )'
