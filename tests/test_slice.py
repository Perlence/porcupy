from porcupy.compiler import compile as compile_


def test_assign():
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z p4z+0 p6z 3 p7z 3')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[1:]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z p4z+1 p6z 2 p7z 2')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:2]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z p4z+0 p6z 2 p7z 3')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:-1]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z p4z+0 p6z 2 p7z 3')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[1:-1]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z p4z+1 p6z 1 p7z 2')

    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[3:]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z p4z+3 p6z 0 p7z 0')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[-3:]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z p4z+0 p6z 3 p7z 3')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:-3]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z p4z+0 p6z 0 p7z 3')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:3]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z p4z+0 p6z 3 p7z 3')

    assert (compile_('x = [11, 22, 33]\n'
                     'y = 1\n'
                     'z = x[:y]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 1 '
            'p9z p5z # p5z > 3 ( p9z 3 ) # p5z <= -3 ( p9z 0 ) # p5z < 0 ( p9z p5z+3 ) '
            'p6z p4z+0 p7z p9z-0 p8z 3')

    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:]\n'
                     'z = y[:]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z p4z+0 p6z 3 p7z 3 '
            'p11z 0 # 0 > p7z ( p11z p7z ) # 0 <= p7z*-1 ( p11z 0 ) # 0 < 0 ( p11z p7z+0 ) '
            'p12z p7z # p7z > p7z ( p12z p7z ) # p7z <= p7z*-1 ( p12z 0 ) # p7z < 0 ( p12z p7z+p7z ) '
            'p8z p5z+p11z p9z p12z-p11z p10z p7z-p11z')


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
                     'z = len(y)\n'
                     'z = cap(y)') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z p4z+0 p6z 3 p7z 3 '
            'p8z p6z '
            'p8z p7z')


def test_get_item():
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:]\n'
                     'system.message(y[0])') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z p4z+0 p6z 3 p7z 3 '
            'p8z p5z+0 p9z p^8z '
            'ym ^9')
    assert (compile_('x = [11, 22, 33]\n'
                     'start = 1\n'
                     'y = x[start:-1]\n'
                     'system.message(y[0])') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 1 '
            'p9z p5z # p5z > 3 ( p9z 3 ) # p5z <= -3 ( p9z 0 ) # p5z < 0 ( p9z p5z+3 ) '
            'p10z 2 p11z 3 '
            'p6z p4z+p9z '
            'p7z p10z-p9z '
            'p8z p11z-p9z '
            'p11z p6z+0 p10z p^11z '
            'ym ^10')

    assert (compile_('x = [11, 22, 33]\n'
                     'Y = x[:]\n'
                     'system.message(Y[0])\n'
                     'system.message(Y[1])\n'
                     'system.message(Y[2])') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z p4z+0 p6z 3 p7z 3 '
            'p8z p5z+0 p9z p^8z ym ^9 '
            'p9z p5z+1 p8z p^9z ym ^8 '
            'p8z p5z+2 p9z p^8z ym ^9')
    assert (compile_('x = [11, 22, 33, 44, 55]\n'
                     'start = 1\n'
                     'Y = x[start:-1]\n'
                     'system.message(Y[0])\n'
                     'system.message(Y[1])\n'
                     'system.message(Y[2])') ==
            'p1z 11 p2z 22 p3z 33 p4z 44 p5z 55 p6z 1 '
            'p7z 1 '
            'p11z p7z # p7z > 5 ( p11z 5 ) # p7z <= -5 ( p11z 0 ) # p7z < 0 ( p11z p7z+5 ) '
            'p12z 4 p13z 5 '
            'p8z p6z+p11z '
            'p9z p12z-p11z '
            'p10z p13z-p11z '
            'p13z p8z+0 p12z p^13z ym ^12 '
            'p12z p8z+1 p13z p^12z ym ^13 '
            'p13z p8z+2 p12z p^13z ym ^12')


def test_for():
    assert (compile_('x = [11, 22, 33, 44, 55]\n'
                     'start = 1\n'
                     'for item in x[start:-1]:\n'
                     '    system.message(item)') ==
            'p1z 11 p2z 22 p3z 33 p4z 44 p5z 55 p6z 1 '
            'p7z 1 '
            'p12z -1 '
            'p13z p7z # p7z > 5 ( p13z 5 ) # p7z <= -5 ( p13z 0 ) # p7z < 0 ( p13z p7z+5 ) '
            'p14z 4 p15z 5 '
            'p8z p6z+p13z '
            'p9z p14z-p13z '
            'p10z p15z-p13z '
            ':1 p12z p12z+1 '
            '# p12z >= p9z ( g2z ) '
            'p13z p8z+p12z p16z p^13z p11z p16z ym ^11 '
            'g1z :2')


def test_append():
    assert (compile_('x = [0, 0, 0]\n'
                     'y = x[:0]\n'
                     'y.append(11)\n'
                     'y.append(22)\n'
                     'y.append(33)') ==
            'p1z 0 p2z 0 p3z 0 p4z 1 '
            'p5z p4z+0 p6z 0 p7z 3 '
            'p8z p5z+p6z p^8z 11 p6z p6z+1 '
            'p8z p5z+p6z p^8z 22 p6z p6z+1 '
            'p8z p5z+p6z p^8z 33 p6z p6z+1')

    assert (compile_('x = [0, 0, 0]\n'
                     'y = x[:0]\n'
                     'y.append(11)\n'
                     'y.append(22)\n'
                     'y.append(33)\n'
                     'for item in y:'
                     '    system.message(item)') ==
            'p1z 0 p2z 0 p3z 0 p4z 1 '
            'p5z p4z+0 p6z 0 p7z 3 '
            'p9z p5z+p6z p^9z 11 p6z p6z+1 '
            'p9z p5z+p6z p^9z 22 p6z p6z+1 '
            'p9z p5z+p6z p^9z 33 p6z p6z+1 '
            'p9z -1 :1 p9z p9z+1 # p9z >= p6z ( g2z ) '
            'p10z p5z+p9z p11z p^10z p8z p11z ym ^8 g1z :2')


def test_set_item():
    assert (compile_('x = [11, 22, 33][1:]\n'
                     'x[0] = 55\n'
                     'system.message(x[0])') ==
            'p1z 11 p2z 22 p3z 33 '
            'p4z 2 p5z 2 p6z 2 '
            'p7z p4z+0 p^7z 55 '
            'p7z p4z+0 p8z p^7z '
            'ym ^8')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[1:]\n'
                     'y[0] = 55\n'
                     'system.message(y[0])') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z p4z+1 p6z 2 p7z 2 '
            'p8z p5z+0 p^8z 55 '
            'p8z p5z+0 p9z p^8z '
            'ym ^9')
