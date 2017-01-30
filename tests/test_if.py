from porcupy.compiler import compile as compile_


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

    assert compile_('if True:\n'
                    '    x = 11\n'
                    'else:\n'
                    '    x = 12') == 'p1z 11'
    assert compile_('if False:\n'
                    '    x = 11\n'
                    'else:\n'
                    '    x = 12') == 'p1z 12'

    assert compile_('X = True\n'
                    'if X: y = 11') == 'p1z 11'

    # assert compile_('x = 11\nif 5 + 7 and True: y = 22') == 'p1z 11 p2z 22'


def test_generic_if():
    # Test is Compare
    assert (compile_('x = 11\n'
                     'if x > 0: y = 22') ==
            'p1z 11 '
            '# p1z <= 0 ( g1z ) p2z 22 :1')
    assert (compile_('x = 11\n'
                     'if x > 0:\n'
                     '    y = 22\n'
                     '    z = 33') ==
            'p1z 11 '
            '# p1z <= 0 ( g1z ) p2z 22 p3z 33 :1')
    assert (compile_('x = 11\n'
                     'if 0 < x < 5: y = 22') ==
            'p1z 11 '
            'p3z 0 # 0 < p1z & p1z < 5 ( p3z 1 ) # p3z = 0 ( g1z ) p2z 22 :1')
    assert (compile_('x = 11; y = 12\n'
                     'if 0 < x < y < 5: y = 22') ==
            'p1z 11 p2z 12 '
            'p3z 0 # 0 < p1z & p1z < p2z & p2z < 5 ( p3z 1 ) # p3z = 0 ( g1z ) p2z 22 :1')
    assert (compile_('x = [11, 22, 33]\n'
                     'if x[0] > 0: y = 44') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z p4z+0 p7z p^6z # p7z <= 0 ( g1z ) p5z 44 :1')

    # Test is BoolOp
    assert (compile_('x = 11\n'
                     'if x < 12 and x < 13: y = 22') ==
            'p1z 11 p3z 0 # p1z < 12 & p1z < 13 ( p3z 1 ) # p3z = 0 ( g1z ) p2z 22 :1')
    assert (compile_('x = 11\n'
                     'if x < 12 and x < 13 and x < 14: y = 22') ==
            'p1z 11 p3z 0 # p1z < 12 & p1z < 13 & p1z < 14 ( p3z 1 ) # p3z = 0 ( g1z ) p2z 22 :1')

    # Chaining different bool operations is broken in Yozhiks, resort to
    # this workaround instead
    assert (compile_('x = 11\n'
                     'if x < 12 and x < 13 or x < 14: y = 22') ==
            'p1z 11 '
            'p3z 0 # p1z < 12 & p1z < 13 ( p3z 1 ) '
            'p4z 1 # p3z = 0 & p1z >= 14 ( p4z 0 ) # p4z = 0 ( g1z ) p2z 22 :1')

    # assert compile_('x = 11\nif x < 5 + 7: y = 22') == 'p1z 11 # p1z < 12 ( p2z 22 )'
    assert (compile_('x = 11; y = 22\n'
                     'if x < y + 7:'
                     '    z = 33') ==
            'p1z 11 p2z 22 '
            '# p1z >= p2z+7 ( g1z ) p3z 33 :1')

    # Test is BinOp
    assert compile_('x = 1\nif x + 2: y = 22') == 'p1z 1 # p1z+2 = 0 ( g1z ) p2z 22 :1'
    # Test is UnaryOp
    assert compile_('x = -1\nif -x: y = 22') == 'p1z -1 # p1z*-1 = 0 ( g1z ) p2z 22 :1'

    # Test is list pointer
    assert (compile_('x = [1, 2, 3]\n'
                     'if x: y = 11') ==
            'p1z 1 p2z 2 p3z 3 p4z 1 '
            '# 1 = 0 ( g1z ) '
            'p5z 11 '
            ':1')

    # Test is slice
    assert (compile_('x = [1, 2, 3][:]\n'
                     'if x: y = 11') ==
            'p1z 1 p2z 2 p3z 3 p4z 16771 '
            'p6z p4z{128 # p6z}128 = 0 ( g1z ) '
            'p5z 11 '
            ':1')
    assert (compile_('x = [1, 2, 3][:]\n'
                     'if not x: y = 11') ==
            'p1z 1 p2z 2 p3z 3 p4z 16771 '
            'p6z p4z{128 p7z 0 # p6z}128 = 0 ( p7z 1 ) # p7z = 0 ( g1z ) '
            'p5z 11 '
            ':1')
    assert (compile_('x = [1, 2, 3][:0]\n'
                     'if x: y = 11') ==
            'p1z 1 p2z 2 p3z 3 p4z 16387 '
            'p6z p4z{128 # p6z}128 = 0 ( g1z ) '
            'p5z 11 '
            ':1')


def test_nested():
    # Nesting if-statements is broken in Yozhiks as well
    assert (compile_('x = 11\n'
                     'if x > 0:\n'
                     '    if x < 15:\n'
                     '        y = 22') ==
            'p1z 11 '
            '# p1z <= 0 ( g1z ) '
            '# p1z >= 15 ( g2z ) '
            'p2z 22 '
            ':2 '
            ':1')

    assert (compile_('x = 11\n'
                     'if x > 0:\n'
                     '    y = 22\n'
                     '    if x < 15:\n'
                     '        z = 33') ==
            'p1z 11 '
            '# p1z <= 0 ( g1z ) '
            'p2z 22 '
            '# p1z >= 15 ( g2z ) '
            'p3z 33 '
            ':2 '
            ':1')

    assert (compile_('x = 11\n'
                     'if x > 0:\n'
                     '    if x < 15:\n'
                     '        y = 22\n'
                     '    y = 33\n'
                     '    if x < 16:\n'
                     '        y = 33') ==
            'p1z 11 '
            '# p1z <= 0 ( g1z ) '
            '# p1z >= 15 ( g2z ) '
            'p2z 22 :2 '
            'p2z 33 '
            '# p1z >= 16 ( g3z ) '
            'p2z 33 '
            ':3 '
            ':1')

    assert (compile_('x = 11\n'
                     'if x > 0:\n'
                     '    if x < 15:\n'
                     '        y = 22\n'
                     '        if x < 16:\n'
                     '            y = 33') ==
            'p1z 11 '
            '# p1z <= 0 ( g1z ) '
            '# p1z >= 15 ( g2z ) '
            'p2z 22 '
            '# p1z >= 16 ( g3z ) '
            'p2z 33 '
            ':3 '
            ':2 '
            ':1')

    # Gotcha, two different bool operations in one test expression
    assert (compile_('x = 11\n'
                     'if x > 0:\n'
                     '    if x < 15 or x < 16:\n'
                     '        y = 22') ==
            'p1z 11 '
            '# p1z <= 0 ( g1z ) '
            'p3z 1 # p1z >= 15 & p1z >= 16 ( p3z 0 ) # p3z = 0 ( g2z ) '
            'p2z 22 '
            ':2 '
            ':1')


def test_else():
    assert (compile_('x = 11\n'
                     'if x > 0:\n'
                     '    y = 22\n'
                     'else:\n'
                     '    y = 23') ==
            'p1z 11 '
            '# p1z <= 0 ( g2z ) '
            'p2z 22 '
            'g1z '
            ':2 '
            'p2z 23 '
            ':1')

    assert (compile_('x = 11\n'
                     'if x > 0:\n'
                     '    y = 22\n'
                     'elif x > 5:\n'
                     '    y = 23') ==
            'p1z 11 '
            '# p1z <= 0 ( g2z ) '
            'p2z 22 '
            'g1z '
            ':2 '
            '# p1z <= 5 ( g3z ) '
            'p2z 23 '
            ':3 '
            ':1')


def test_if_expr():
    assert (compile_('a = 5; b = 1 if a >= 0 else 0; c = 99') ==
            'p1z 5 # p1z < 0 ( g2z ) p4z 1 g1z :2 p4z 0 :1 p2z p4z p3z 99')

    assert (compile_('b = 1 if True else 0') ==
            'p2z 1 p1z p2z')
