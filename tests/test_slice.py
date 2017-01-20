from porcupy.compiler import compile as compile_


def test_assign():
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z p4z+0 p7z p6z*16384 p5z p7z+387')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[1:]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z p4z+1 p7z p6z*16384 p5z p7z+258')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:2]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z p4z+0 p7z p6z*16384 p5z p7z+259')

    assert (compile_('x = [11, 22, 33]\n'
                     'y = 1\n'
                     'z = x[:y]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 1 '
            'p7z p4z+0 p8z p5z-0 p9z p8z*128 p10z p7z*16384 p11z p9z+3 p6z p10z+p11z')


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
            'p7z p4z+0 p8z p7z*16384 p5z p8z+387 '
            'p8z p5z{128 p6z p8z}128 '
            'p6z p5z}128')


def test_get_item():
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:]\n'
                     'system.message(y[0])') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z p4z+0 p7z p6z*16384 p5z p7z+387 '
            'p6z p5z{16384 p7z p6z+0 p8z p^7z ym ^8')
    assert (compile_('x = [11, 22, 33]\n'
                     'start = 1\n'
                     'y = x[start:len(x)-1]\n'
                     'system.message(y[0])') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 1 '
            'p7z 2 p8z 3 '
            'p9z p4z+p5z p10z p7z-p5z '
            'p11z p10z*128 p12z p8z-p5z p13z p9z*16384 p14z p11z+p12z '
            'p6z p13z+p14z p13z p6z{16384 p14z p13z+0 p12z p^14z ym ^12')


def test_for():
    assert (compile_('x = [11, 22, 33, 44, 55]\n'
                     'start = 1\n'
                     'for item in x[start:len(x)-1]:\n'
                     '    system.message(item)') ==
            'p1z 11 p2z 22 p3z 33 p4z 44 p5z 55 p6z 1 '
            'p7z 1 '
            'p9z -1 '
            'p10z 4 p11z 5 '
            'p12z p6z+p7z p13z p10z-p7z '
            'p14z p13z*128 p15z p11z-p7z p16z p12z*16384 '
            'p17z p14z+p15z p18z p16z+p17z '
            'p19z p18z{128 :1 p9z p9z+1 # p9z >= p19z}128 ( g2z ) '
            'p20z p16z+p17z p22z p20z{16384 p21z p22z+p9z p23z p^21z p8z p23z ym ^8 g1z :2')


def test_append():
    assert (compile_('x = [0, 0, 0]\n'
                     'y = x[:0]\n'
                     'y.append(11)\n'
                     'y.append(22)\n'
                     'y.append(33)') ==
            'p1z 0 p2z 0 p3z 0 p4z 1 '
            'p6z p4z+0 p7z p6z*16384 p5z p7z+3 '
            'p7z p5z{128 p8z p5z{16384 p9z p7z}128 p6z p8z+p9z p^6z 11 p5z p5z+128 '
            'p9z p5z{128 p7z p5z{16384 p6z p9z}128 p8z p7z+p6z p^8z 22 p5z p5z+128 '
            'p6z p5z{128 p9z p5z{16384 p8z p6z}128 p7z p9z+p8z p^7z 33 p5z p5z+128')


def test_set_item():
    assert (compile_('x = [11, 22, 33][1:]\n'
                     'x[0] = 55\n'
                     'system.message(x[0])') ==
            'p1z 11 p2z 22 p3z 33 '
            'p4z 33026 '
            'p5z p4z{16384 p7z p4z{16384 p6z p7z+0 p^6z 55 p7z p4z{16384 p6z p7z+0 p5z p^6z '
            'ym ^5')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[1:]\n'
                     'y[0] = 55\n'
                     'system.message(y[0])') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z p4z+1 p7z p6z*16384 p5z p7z+258 '
            'p7z p5z{16384 p8z p5z{16384 p6z p8z+0 p^6z 55 '
            'p8z p5z{16384 p6z p8z+0 p7z p^6z ym ^7')
