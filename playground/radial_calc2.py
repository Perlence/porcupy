PLAYER = yozhiks[0]

NUMBER = 9

ADD = 10
SUB = 11
MUL = 12
DIV = 13
OPERATION = 13

PUSH = 14
RESET = 15

NOP = 16

BASE = 10

# Init
if timers[0].value == 1:
    stack = [0, 0, 0, 0, 0][:0]
    digits = [0, 0, 0, 0, 0, 0, 0, 0][:0]

    PLAYER.spawn(1)
    PLAYER.weapon = 4
    PLAYER.has_weapon = 1
    PLAYER.ammo = 1

    number = 0

PLAYER.health = 100

# Display controls
print_at(points[0].pos_x, points[0].pos_y, 1, '0')
print_at(points[1].pos_x, points[1].pos_y, 1, '1')
print_at(points[2].pos_x, points[2].pos_y, 1, '2')
print_at(points[3].pos_x, points[3].pos_y, 1, '3')
print_at(points[4].pos_x, points[4].pos_y, 1, '4')
print_at(points[5].pos_x, points[5].pos_y, 1, '5')
print_at(points[6].pos_x, points[6].pos_y, 1, '6')
print_at(points[7].pos_x, points[7].pos_y, 1, '7')
print_at(points[8].pos_x, points[8].pos_y, 1, '8')
print_at(points[9].pos_x, points[9].pos_y, 1, '9')
print_at(points[10].pos_x, points[10].pos_y, 1, 'P')
print_at(points[11].pos_x, points[11].pos_y, 1, '+')
print_at(points[12].pos_x, points[12].pos_y, 1, '-')
print_at(points[13].pos_x, points[13].pos_y, 1, '*')
print_at(points[14].pos_x, points[14].pos_y, 1, '/')
print_at(points[15].pos_x, points[15].pos_y, 1, 'C')

# LED
x = points[16].pos_x
y = points[16].pos_y
print_at(x, y, 1, number)
for val in stack:
    y -= 15.0
    print_at(x, y, 1, val)

# Handle controls
value = NOP
if PLAYER.ammo == 0:
    PLAYER.ammo = 1
    if 0 <= PLAYER.view_angle < 8:
        value = 0
    elif 8 <= PLAYER.view_angle < 16:
        value = 1
    elif 16 <= PLAYER.view_angle < 24:
        value = 2
    elif 24 <= PLAYER.view_angle < 32:
        value = 3
    elif 32 <= PLAYER.view_angle < 40:
        value = 4
    elif 40 <= PLAYER.view_angle < 48:
        value = 5
    elif 48 <= PLAYER.view_angle < 56:
        value = 6
    elif 56 <= PLAYER.view_angle < 64:
        value = 7
    elif 64 <= PLAYER.view_angle < 72:
        value = 8
    elif 72 <= PLAYER.view_angle < 80:
        value = 9
    elif 80 <= PLAYER.view_angle < 88:
        value = PUSH
    elif 88 <= PLAYER.view_angle < 96:
        value = ADD
    elif 96 <= PLAYER.view_angle < 104:
        value = SUB
    elif 104 <= PLAYER.view_angle < 112:
        value = MUL
    elif 112 <= PLAYER.view_angle < 120:
        value = DIV
    elif 120 <= PLAYER.view_angle <= 128:
        value = RESET

# Evaluate the stack
while value != NOP:
    if value <= NUMBER:
        if len(digits) == cap(digits):
            break
        if len(digits) == 1 and digits[0] == value == 0:
            break
        digits.append(value)

        # Convert digits to a number
        number = 0
        exponent = 1
        # for digit in reversed(digits):
        for i in range(len(digits)-1, -1, -1):
            digit = digits[i]
            number += digits[i] * exponent
            exponent *= BASE

    elif value <= OPERATION or value == PUSH:
        if len(stack) == cap(stack):
            break
        if len(digits) or value == PUSH:
            stack.append(number)

        # Calculate the result
        if value <= OPERATION:
            if len(stack) < 2:
                print('Error: not enough values on the stack, 2 required')
                break

            op1 = stack[len(stack)-2]
            op2 = stack[len(stack)-1]
            stack = stack[:len(stack)-2]
            if value == ADD:
                number = op1 + op2
            elif value == SUB:
                number = op1 - op2
            elif value == MUL:
                number = op1 * op2
            elif value == DIV:
                number = op1 // op2

            if len(stack) == cap(stack):
                break
            stack.append(number)

        digits = digits[:0]

    elif value == RESET:
        stack = stack[:0]
        digits = digits[:0]
        number = 0

    value = NOP
