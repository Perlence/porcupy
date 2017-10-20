"""
def fib(n):
    if n < 2:
        return n
    return fib(n-2) + fib(n-1)

N = 10
if timers[0].value == 50:
    x = fib(5)
    print_at(10, 10, 100, 'fib({}) = {}'.format(N, x))
"""

func_stack = slice(int, 0, 64)

FUNC_FIB = 90
FUNC_FIB_RETURN_1 = 91
FUNC_FIB_RETURN_2 = 92
FUNC_FIB_RETURN_3 = 93
FUNC_FIB_FRAME_SIZE = 3  # return label, argument `n` and result
FUNC_FIB_ARG_RETURN_LABEL = 0
FUNC_FIB_ARG_N = 1
FUNC_FIB_ARG_RESULT = 2
END = 99

N = 10
if timers[0].value == 50:
    # x = fib(5)
    func_stack.append(FUNC_FIB_RETURN_1)  # push return label
    func_stack.append(N)  # push argument
    func_stack.append(0)  # reserve value for result
    print('g{}z'.format(FUNC_FIB))
    print(':{}'.format(FUNC_FIB_RETURN_1))
    x = func_stack[len(func_stack) - FUNC_FIB_FRAME_SIZE + FUNC_FIB_ARG_RESULT]  # get result
    func_stack = func_stack[:len(func_stack)-FUNC_FIB_FRAME_SIZE]  # pop frame

    print_at(10, 10, 100, 'fib({}) = {}'.format(N, x))

# functions go below
print('g{}z'.format(END))

# def fib(n):
print(':{}'.format(FUNC_FIB))
frame = func_stack[len(func_stack)-FUNC_FIB_FRAME_SIZE:]
if frame[FUNC_FIB_ARG_N] < 2:
    frame[FUNC_FIB_ARG_RESULT] = frame[FUNC_FIB_ARG_N]  # set result
    print('g{}z'.format(frame[FUNC_FIB_ARG_RETURN_LABEL]))

# result = fib(n-2)
func_stack.append(FUNC_FIB_RETURN_2)
func_stack.append(frame[FUNC_FIB_ARG_N]-2)
func_stack.append(0)
print('g{}z'.format(FUNC_FIB))
print(':{}'.format(FUNC_FIB_RETURN_2))
frame = func_stack[len(func_stack)-FUNC_FIB_FRAME_SIZE-FUNC_FIB_FRAME_SIZE:len(func_stack)-FUNC_FIB_FRAME_SIZE]  # restore frame
frame[FUNC_FIB_ARG_RESULT] = func_stack[len(func_stack) - FUNC_FIB_FRAME_SIZE + FUNC_FIB_ARG_RESULT]
func_stack = func_stack[:len(func_stack)-FUNC_FIB_FRAME_SIZE]

# result += fib(n-1)
func_stack.append(FUNC_FIB_RETURN_3)
func_stack.append(frame[FUNC_FIB_ARG_N]-1)
func_stack.append(0)
print('g{}z'.format(FUNC_FIB))
print(':{}'.format(FUNC_FIB_RETURN_3))
frame = func_stack[len(func_stack)-FUNC_FIB_FRAME_SIZE-FUNC_FIB_FRAME_SIZE:len(func_stack)-FUNC_FIB_FRAME_SIZE]
frame[FUNC_FIB_ARG_RESULT] += func_stack[len(func_stack) - FUNC_FIB_FRAME_SIZE + FUNC_FIB_ARG_RESULT]
func_stack = func_stack[:len(func_stack)-FUNC_FIB_FRAME_SIZE]

print('g{}z'.format(frame[FUNC_FIB_ARG_RETURN_LABEL]))

# end def

print(':{}'.format(END))
