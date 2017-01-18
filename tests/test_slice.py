from pyegs.compiler import compile as compile_


def test_assign():
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 3 p6z 3 p7z p4z+0')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[1:]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 2 p6z 2 p7z p4z+1')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:2]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 2 p6z 3 p7z p4z+0')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:-1]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 2 p6z 3 p7z p4z+0')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[1:-1]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 1 p6z 2 p7z p4z+1')

    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[3:]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 0 p6z 0 p7z p4z+3')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[-3:]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 3 p6z 3 p7z p4z+0')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:-3]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 0 p6z 3 p7z p4z+0')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:3]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 3 p6z 3 p7z p4z+0')

    assert (compile_('x = [11, 22, 33]\n'
                     'y = 1\n'
                     'z = x[:y]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 1 '
            'p9z p5z # p5z > 3 ( p9z 3 ) # p5z <= -3 ( p9z 0 ) # p5z < 0 ( p9z p5z+3 ) '
            'p6z p9z-0 p7z 3 p8z p4z+0')

    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:]\n'
                     'z = y[:]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 3 p6z 3 p7z p4z+0 '
            'p8z 3 p9z 3 p10z p7z+0')


def test_len_cap():
    assert (compile_('x = [11]\n'
                     'y = len(x)\n'
                     'y = cap(x)') ==
            'p1z 11 p2z 1 '
            'p3z 1 '
            'p3z 1')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = len(x)\n'
                     'y = cap(x)') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 3 '
            'p5z 3')

    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:]\n'
                     'z = len(x)\n'
                     'z = cap(x)') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 3 p6z 3 p7z p4z+0 '
            'p8z 3 '
            'p8z 3')


def test_get_item():
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:]\n'
                     'system.message(y[0])') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 3 p6z 3 p7z p4z+0 '
            'p8z p7z+0 p9z p^8z '
            'ym ^9')
    assert (compile_('x = [11, 22, 33]\n'
                     'start = 1\n'
                     'y = x[start:-1]\n'
                     'system.message(y[0])') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 1 '
            'p9z p5z # p5z > 3 ( p9z 3 ) # p5z <= -3 ( p9z 0 ) # p5z < 0 ( p9z p5z+3 ) '
            'p10z 2 p11z 3 '
            'p6z p10z-p9z '  # p6z 2
            'p7z p11z-p9z '  # p7z 2
            'p8z p4z+p9z '  # p8z
            'p11z p8z+0 p10z p^11z ym ^10')
