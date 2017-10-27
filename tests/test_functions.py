import pytest

from porcupy.compiler import compile as compile_


def test_no_args_no_return():
    assert (compile_('def f(): print("Hey")\n'
                     'f()') ==
            'ym Hey')


def test_args_no_return():
    assert (compile_('def f(x):\n'
                     '    print(x)\n'
                     'f(42)') ==
            'p1z 42 ym ^1')


def test_no_args_return():
    assert (compile_('def f():\n'
                     '    return\n'
                     'f()') ==
            'g1z :1')
    assert (compile_('def f():\n'
                     '    return 42\n'
                     'x = f()\n'
                     'x = f()\n') ==
            'p2z 42 g1z :1 p1z p2z p2z 42 g2z :2 p1z p2z')
    assert (compile_('def f():\n'
                     '    return 42\n'
                     'x = 1-f()\n') ==
            'p2z 42 g1z :1 p3z 1 p1z p3z-p2z')


def test_local_vars():
    assert (compile_('x = 99\n'
                     'def f(): x = 100\n'
                     'f()\n'
                     'y = 101') ==
            'p1z 99 p2z 100 p2z 101')
    assert (compile_('x = 99\n'
                     'def f():\n'
                     '    X = 100\n'
                     '    print(X)\n'
                     'f()\n'
                     'y = 101') ==
            'p1z 99 ym 100 p2z 101')
    with pytest.raises(ValueError) as exc_info:
        compile_('X = 99\n'
                 'def f():\n'
                 '    X = 100\n'
                 'f()\n')
    assert 'cannot redefine a constant' in str(exc_info.value)


def test_nested():
    assert (compile_('x = 99\n'
                     'def f():\n'
                     '    x = 100\n'
                     '    def g():\n'
                     '        x = 101\n'
                     '        print(x)\n'
                     '    g()\n'
                     'f()') ==
            'p1z 99 p2z 100 p3z 101 ym ^3')
    with pytest.raises(NameError) as exc_info:
        compile_('x = 99\n'
                 'def f():\n'
                 '    def g():\n'
                 '        pass\n'
                 'g()')
    assert 'is not defined' in str(exc_info)


def test_temporary_vars():
    assert (compile_('def f(x):\n'
                     '    return 1-x\n'
                     'x = 42\n'
                     'y = f(x)') ==
            'p1z 42 '
            'p2z p1z p3z 1 p4z p3z-p2z g1z :1 p2z p4z')
    assert (compile_('def f(x):\n'
                     '    y = 1-x\n'
                     '    return 1-y\n'
                     'x = 42\n'
                     'y = f(x)') ==
            'p1z 42 '
            'p2z p1z '
            'p4z 1 p3z p4z-p2z '
            'p4z 1 p5z p4z-p3z '
            'g1z :1 '
            'p2z p5z')


def test_nested_return():
    assert (compile_('def f():\n'
                     '    def g():\n'
                     '        return 42\n'
                     '    return g()+1\n'
                     'x = f()') ==
            'p2z 42 g2z :2 p3z p2z+1 g1z :1 p1z p3z')


def test_global_reference():
    assert (compile_('x = 99\n'
                     'def f():\n'
                     '    global x\n'
                     '    x = 100\n'
                     'f()') ==
            'p1z 99 p1z 100')


def test_nonlocal_reference():
    assert (compile_('x = 99\n'
                     'def f():\n'
                     '    x = 100\n'
                     '    def g():\n'
                     '        nonlocal x\n'
                     '        x = 101\n'
                     '        print(x)\n'
                     '    g()\n'
                     'f()') ==
            'p1z 99 p2z 100 p2z 101 ym ^2')
    with pytest.raises(NameError) as exc_info:
        compile_('x = 99\n'
                 'def f():\n'
                 '    nonlocal x\n'
                 '    x = 101\n'
                 'f()')
    assert 'no binding for nonlocal' in str(exc_info)


def test_call_by_value():
    assert (compile_('def f(x):\n'
                     '    x = 43\n'
                     'x = 42\n'
                     'f(x)') ==
            'p1z 42 p2z p1z p2z 43')


@pytest.mark.xfail
def test_return_tuple():
    assert (compile_('def f():\n'
                     '    return 42, 42\n'
                     'x, y = f()') ==
            'p3z 42 p4z 42 g1z :1 p1z p3z p2z p4z')


def test_return_different_types():
    with pytest.raises(TypeError) as exc_info:
        compile_('def f():\n'
                 '    return 0\n'
                 '    return slice(int, 5)\n'
                 'x = f()')
    assert "cannot assign value of type 'Slice(item_type=NumberType())' to variable of type 'NumberType()'" in str(exc_info)


def test_return_slice():
    assert (compile_('def myslice(xs, lower, upper):\n'
                     '    return xs[lower:upper]\n'
                     'xs = [11, 22, 33, 44, 55]\n'
                     'ys = myslice(xs, 0, 3)') ==
            'p1z 11 p2z 22 p3z 33 p4z 44 p5z 55 p6z 1 '
            'p7z p6z p8z 0 p9z 3 '
            'p10z 5 p11z p7z+p8z p12z p10z-p8z p13z p12z*100 p14z p9z-p8z p15z p11z*10000 p16z p13z+p14z '
            'p17z p15z+p16z g1z :1 '
            'p7z p17z')


@pytest.mark.xfail
def test_recursion():
    with pytest.raises(NotImplementedError) as exc_info:
        compile_('def f():\n'
                 '    f()\n'
                 'f()')
    assert 'recursive functions are not implemented' in str(exc_info)
