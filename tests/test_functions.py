import pytest

from porcupy.compiler import compile as compile_


def test_no_args_no_return():
    assert (compile_('def f(): print("Hey")\n'
                     'f()') ==
            'ym Hey')


def test_no_args_return():
    assert (compile_('def f():\n'
                     '    return\n'
                     'f()') ==
            'g1z :1')


def test_args_return():
    assert (compile_('def f(x):\n'
                     '    print(x)\n'
                     'f(42)') ==
            'ym 42')


def test_no_args():
    assert (compile_('def f():\n'
                     '    return 42\n'
                     'x = f()') ==
            'p2z 42 g1z :1 p1z p2z')


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


@pytest.mark.xfail
def test_recursion():
    with pytest.raises(NotImplementedError) as exc_info:
        compile_('def f():\n'
                 '    f()\n'
                 'f()')
    assert 'recursive functions are not implemented' in str(exc_info)
