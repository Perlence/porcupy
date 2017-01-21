from porcupy.compiler import compile as compile_


def test_while():
    assert (compile_('x = 0\n'
                     'while x < 5:\n'
                     '    print(x)\n'
                     '    x += 1') ==
            'p1z 0 '
            ':1 p2z 0 # p1z < 5 ( p2z 1 ) # p2z = 0 ( g2z ) '
            'ym ^1 p1z p1z+1 '
            'g1z '
            ':2')


def test_else():
    assert (compile_('x = 0\n'
                     'while x < 5:\n'
                     '    print(x)\n'
                     '    x += 1\n'
                     'else:\n'
                     '    print("else")') ==
            'p1z 0 '
            ':1 p2z 0 # p1z < 5 ( p2z 1 ) # p2z = 0 ( g3z ) '
            'ym ^1 p1z p1z+1 '
            'g1z '
            ':3 ym else '
            ':2')


def test_break():
    assert (compile_('x = 0\n'
                     'while x < 5:\n'
                     '    print(x)\n'
                     '    x += 1\n'
                     '    break\n'
                     'else:\n'
                     '    print("else")') ==
            'p1z 0 '
            ':1 p2z 0 # p1z < 5 ( p2z 1 ) # p2z = 0 ( g3z ) '
            'ym ^1 p1z p1z+1 '
            'g2z '
            'g1z '
            ':3 ym else '
            ':2')


def test_pass():
    assert (compile_('x = 0\n'
                     'while x < 5:\n'
                     '    pass\n'
                     'else:\n'
                     '    print("else")') ==
            'p1z 0 '
            ':1 p2z 0 # p1z < 5 ( p2z 1 ) # p2z = 0 ( g3z ) '
            'g1z '
            ':3 ym else '
            ':2')

    assert (compile_('x = 0\n'
                     'while x < 5:\n'
                     '    print(x)\n'
                     'else:\n'
                     '    pass') ==
            'p1z 0 '
            ':1 p2z 0 # p1z < 5 ( p2z 1 ) # p2z = 0 ( g2z ) '
            'ym ^1 '
            'g1z '
            ':2')


def test_continue():
    assert (compile_('x = 0\n'
                     'while x < 5:\n'
                     '    x += 1\n'
                     '    if x < 3:\n'
                     '        continue\n'
                     'else:\n'
                     '    print("else")') ==
            'p1z 0 '
            ':1 p2z 0 # p1z < 5 ( p2z 1 ) # p2z = 0 ( g3z ) '
            'p1z p1z+1 '
            'p3z 0 # p1z < 3 ( p3z 1 ) # p3z = 0 ( g4z ) g1z :4 '
            'g1z '
            ':3 ym else '
            ':2')
