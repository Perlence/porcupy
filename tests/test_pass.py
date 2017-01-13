from pyegs.compiler import compile as compile_


def test_pass():
    assert compile_('pass') == ''


def test_pass_if():
    assert (compile_('x = 11\n'
                     'if x > 0: pass') == 'p1z 11')
    assert (compile_('x = 11\n'
                     'if x > 0: x += 1\n'
                     'else: pass') ==
            'p1z 11 '
            'p2z 0 # p1z > 0 ( p2z 1 ) # p2z ! 0 ( p1z p1z+1 )')


def test_pass_for():
    assert (compile_('items = [11]\n'
                     'for list in items: pass') ==
            'p1z 11 p2z 1')
