import pytest

from porcupy.compiler import compile as compile_


def test_assign():
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z p4z+0 p7z p6z*10000 p5z p7z+303')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[1:]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z p4z+1 p7z p6z*10000 p5z p7z+202')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:2]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z p4z+0 p7z p6z*10000 p5z p7z+302')

    assert (compile_('x = [11, 22, 33]\n'
                     'y = 1\n'
                     'z = x[:y]') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 1 '
            'p7z p4z+0 p8z p5z-0 p9z p7z*10000 p10z p8z+300 p6z p9z+p10z')

    assert (compile_('xs = [11, 22, 33, 0, 0][:3]\n'
                     'ys = xs[0:]') ==
            'p1z 11 p2z 22 p3z 33 p4z 0 p5z 0 p6z 10503 '
            'p8z p6z{100 p9z p6z{10000 p10z p6z}100 p11z p8z}100 p12z p9z+0 p13z p11z-0 p14z p13z*100 p15z p10z-0 '
            'p16z p12z*10000 p17z p14z+p15z p7z p16z+p17z')


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
            'p7z p4z+0 p8z p7z*10000 p5z p8z+303 '
            'p6z p5z}100 '
            'p8z p5z{100 p6z p8z}100')


def test_get_item():
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[:]\n'
                     'print(y[0])') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z p4z+0 p7z p6z*10000 p5z p7z+303 '
            'p6z p5z{10000 p7z p6z+0 p8z p^7z ym ^8')
    assert (compile_('x = [11, 22, 33]\n'
                     'start = 1\n'
                     'y = x[start:len(x)-1]\n'
                     'print(y[0])') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p5z 1 '
            'p7z 2 p8z 3 '
            'p9z p4z+p5z p10z p8z-p5z '
            'p11z p10z*100 p12z p7z-p5z p13z p9z*10000 p14z p11z+p12z '
            'p6z p13z+p14z p13z p6z{10000 p14z p13z+0 p12z p^14z ym ^12')


def test_for():
    assert (compile_('x = [11, 22, 33, 44, 55]\n'
                     'start = 1\n'
                     'for item in x[start:len(x)-1]:\n'
                     '    print(item)') ==
            'p1z 11 p2z 22 p3z 33 p4z 44 p5z 55 p6z 1 '
            'p7z 1 '
            'p9z -1 '
            'p10z 4 p11z 5 '
            'p12z p6z+p7z p13z p11z-p7z '
            'p14z p13z*100 p15z p10z-p7z p16z p12z*10000 '
            'p17z p14z+p15z p18z p16z+p17z '
            ':1 p9z p9z+1 # p9z >= p18z}100 ( g2z ) '
            'p19z p16z+p17z p21z p19z{10000 p20z p21z+p9z p22z p^20z p8z p22z ym ^8 g1z :2')


def test_append():
    assert (compile_('x = [0, 0, 0]\n'
                     'y = x[:0]\n'
                     'y.append(11)\n'
                     'y.append(22)\n'
                     'y.append(33)') ==
            'p1z 0 p2z 0 p3z 0 p4z 1 '
            'p6z p4z+0 p7z p6z*10000 p5z p7z+300 '
            'p6z p5z{10000 p8z p5z}100 p7z p6z+p8z p^7z 11 p5z p5z+1 '
            'p6z p5z{10000 p7z p5z}100 p8z p6z+p7z p^8z 22 p5z p5z+1 '
            'p6z p5z{10000 p8z p5z}100 p7z p6z+p8z p^7z 33 p5z p5z+1')


def test_set_item():
    assert (compile_('x = [11, 22, 33][1:]\n'
                     'x[0] = 55\n'
                     'print(x[0])') ==
            'p1z 11 p2z 22 p3z 33 p4z 20202 '
            'p6z p4z{10000 p5z p6z+0 p^5z 55 '
            'p6z p4z{10000 p5z p6z+0 p7z p^5z ym ^7')
    assert (compile_('x = [11, 22, 33]\n'
                     'y = x[1:]\n'
                     'y[0] = 55\n'
                     'print(y[0])') ==
            'p1z 11 p2z 22 p3z 33 p4z 1 '
            'p6z p4z+1 p7z p6z*10000 p5z p7z+202 '
            'p6z p5z{10000 p7z p6z+0 p^7z 55 '
            'p6z p5z{10000 p7z p6z+0 p8z p^7z ym ^8')


def test_slice_shortcut():
    assert (compile_('x = slice(int, 5)') == compile_('x = [0, 0, 0, 0, 0][:]'))
    assert (compile_('x = slice(int, 0, 5)') == compile_('x = [0, 0, 0, 0, 0][:0]'))

    assert (compile_('x = slice(float, 5)') == compile_('x = [0.0, 0.0, 0.0, 0.0, 0.0][:]'))

    assert (compile_('x = slice(float, 5)') == compile_('x = [False, False, False, False, False][:]'))

    with pytest.raises(ValueError) as exc_info:
        compile_('x = 5; y = slice(int, x)')
    assert 'slice capacity must be constant' in str(exc_info)
