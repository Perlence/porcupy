"""
def myrange(start, stop, step):
    while start < stop:
        yield start
        start += step


if timers[0].value == 50:
    for value in myrange(0, 5, 1):
        print(value)
"""

func_stack = slice(int, 0, 50)

FUNC_MYRANGE = 90
FUNC_MYRANGE_RETURN_1 = 91
FUNC_MYRANGE_RESUME_1 = 92
FUNC_MYRANGE_FRAME_SIZE = 6
FUNC_MYRANGE_RETURN_TO = 0
FUNC_MYRANGE_ARG_START = 1
FUNC_MYRANGE_ARG_STOP = 2
FUNC_MYRANGE_ARG_STEP = 3
FUNC_MYRANGE_RESULT_1 = 4
FUNC_MYRANGE_RESUME_FROM = 5
END = 99

if timers[0].value == 50:
    # it = myrange(0, 5, 1)
    it = [
        0,  # reserve return label
        0,  # push start
        5,  # push stop
        1,  # push step
        0,  # reserve value for result
        FUNC_MYRANGE,  # push value for resume
    ][:]

    while True:
        # value, resume_from = next(IT)
        it[FUNC_MYRANGE_RETURN_TO] = FUNC_MYRANGE_RETURN_1
        for val in it:
            func_stack.append(val)
        print('INLINE g{}z'.format(it[FUNC_MYRANGE_RESUME_FROM]))
        print('INLINE :{}'.format(FUNC_MYRANGE_RETURN_1))
        it = func_stack[len(func_stack)-FUNC_MYRANGE_FRAME_SIZE:]  # get iterator frame from the stack
        func_stack = func_stack[:len(func_stack)-FUNC_MYRANGE_FRAME_SIZE]  # pop the frame
        value = it[FUNC_MYRANGE_RESULT_1]  # get result
        resume_from = it[FUNC_MYRANGE_RESUME_FROM]  # get label to resume from
        if resume_from < 0:
            break

        print(value)

# functions go below
print('INLINE g{}z'.format(END))

# def myrange(start, stop, step):
print('INLINE :{}'.format(FUNC_MYRANGE))
frame = func_stack[len(func_stack)-FUNC_MYRANGE_FRAME_SIZE:]

# while start < stop:
while frame[FUNC_MYRANGE_ARG_START] < frame[FUNC_MYRANGE_ARG_STOP]:
    # yield start
    frame[FUNC_MYRANGE_RESULT_1] = frame[FUNC_MYRANGE_ARG_START]
    frame[FUNC_MYRANGE_RESUME_FROM] = FUNC_MYRANGE_RESUME_1
    print('INLINE g{}z'.format(frame[FUNC_MYRANGE_RETURN_TO]))
    print('INLINE :{}'.format(FUNC_MYRANGE_RESUME_1))
    frame = func_stack[len(func_stack)-FUNC_MYRANGE_FRAME_SIZE:]

    # start += step
    frame[FUNC_MYRANGE_ARG_START] += frame[FUNC_MYRANGE_ARG_STEP]

frame[FUNC_MYRANGE_RESULT_1] = 0
frame[FUNC_MYRANGE_RESUME_FROM] = -1
print('INLINE g{}z'.format(frame[FUNC_MYRANGE_RETURN_TO]))

# end def

print('INLINE :{}'.format(END))
