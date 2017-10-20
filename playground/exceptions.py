def simple_raise():
    """
    seq = [11, 22, 33]
    x = 3
    if x >= len(seq):
        raise IndexError('list index out of range')
    """
    INDEX_ERROR_LIST_INDEX_OUT_OF_RANGE = 98
    END = 99

    seq = [11, 22, 33]
    x = 3
    if x >= len(seq):
        print('g{}z'.format(INDEX_ERROR_LIST_INDEX_OUT_OF_RANGE))

    print('g{}z'.format(END))

    print(':{}'.format(INDEX_ERROR_LIST_INDEX_OUT_OF_RANGE))
    print_at(10, 10, 50, """\
Traceback (most recent call last):
  File "exceptions.py", line 4, in <module>
IndexError('list index out of range')""")
    print('g{}z'.format(END))

    print(':{}'.format(END))


def try_except():
    """
    seq = [11, 22, 33]
    x = 3
    try:
        if x >= len(seq):
            raise IndexError('list index out of range')
        y = seq[x]
    except IndexError:
        print('oops')
    """
    EXCEPT_INDEX_ERROR_LIST_INDEX_OUT_OF_RANGE = 90
    TRY_END = 91

    seq = [11, 22, 33]
    x = 3

    # try:
    if x >= len(seq):
        print('g{}z'.format(EXCEPT_INDEX_ERROR_LIST_INDEX_OUT_OF_RANGE))
    y = seq[x]
    print('g{}z'.format(TRY_END))

    # except IndexError:
    print(':{}'.format(EXCEPT_INDEX_ERROR_LIST_INDEX_OUT_OF_RANGE))
    print('oops')

    # end try
    print(':{}'.format(TRY_END))
