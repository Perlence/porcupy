PLAYER = yegiks[0]

NUMBER = 1

ADD = 2
SUB = 3
MUL = 4
DIV = 5
OPERATION = 5

PUSH = 6
RESET = 7

NOP = 8

# Init
if timers[1].value == 1:
    stack = [0, 0, 0, 0, 0][:0]
    digits = [0, 0, 0, 0, 0, 0, 0, 0][:0]

    PLAYER.spawn(1)
    PLAYER.weapon = 4
    PLAYER.has_weapon = 1
    PLAYER.ammo = 1

    clear_display_on_next_number = False

PLAYER.health = 1

# Display controls
x = points[0].pos_x; y = points[0].pos_y; system.message_at(x, y, 1, '1')
x = points[1].pos_x; y = points[1].pos_y; system.message_at(x, y, 1, '0')
x = points[2].pos_x; y = points[2].pos_y; system.message_at(x, y, 1, '-1')
x = points[9].pos_x; y = points[9].pos_y; system.message_at(x, y, 1, 'P')
x = points[10].pos_x; y = points[10].pos_y; system.message_at(x, y, 1, '+')
x = points[11].pos_x; y = points[11].pos_y; system.message_at(x, y, 1, '-')
x = points[12].pos_x; y = points[12].pos_y; system.message_at(x, y, 1, '*')
x = points[13].pos_x; y = points[13].pos_y; system.message_at(x, y, 1, '/')
# x = points[3].pos_x; y = points[3].pos_y; system.message_at(x, y, 1, '0')
# x = points[4].pos_x; y = points[4].pos_y; system.message_at(x, y, 1, '1')
# x = points[5].pos_x; y = points[5].pos_y; system.message_at(x, y, 1, '/')
# x = points[17].pos_x; y = points[17].pos_y; system.message_at(x, y, 1, '*')
# x = points[7].pos_x; y = points[7].pos_y; system.message_at(x, y, 1, '-')
# x = points[8].pos_x; y = points[8].pos_y; system.message_at(x, y, 1, '+')
x = points[16].pos_x; y = points[16].pos_y; system.message_at(x, y, 1, 'R')

# LED
x = points[15].pos_x
y = points[15].pos_y
for digit in digits:
    if digit < 0:
        system.message_at(x, y, 1, '-')
    elif digit == 0:
        system.message_at(x, y, 1, digit)
    else:
        system.message_at(x, y, 1, '+')
    x += 12.0

# Handle controls
value = NOP
if PLAYER.ammo == 0:
    PLAYER.ammo = 1
    if 0 <= PLAYER.view_angle <= 3:
        value = -1
    elif 15 <= PLAYER.view_angle <= 22:
        value = 0
    elif 22 < PLAYER.view_angle < 35:
        value = RESET
    elif 35 <= PLAYER.view_angle <= 42:
        value = 1
    elif 53 <= PLAYER.view_angle <= 59:
        value = DIV
    elif 69 <= PLAYER.view_angle <= 76:
        value = MUL
    elif 86 <= PLAYER.view_angle <= 95:
        value = SUB
    elif 106 <= PLAYER.view_angle <= 114:
        value = ADD
    elif 125 <= PLAYER.view_angle <= 127:
        value = PUSH

# Evaluate the stack
while value != NOP:
    if value <= NUMBER:
        if clear_display_on_next_number:
            digits = digits[:0]
            clear_display_on_next_number = False
        digits.append(value)

    elif value <= OPERATION or value == PUSH:
        if clear_display_on_next_number == False and len(digits):
            # Convert ternary digits to a number
            number = 0
            exponent = 1
            # for digit in reversed(digits):
            for i in range(len(digits)-1, -1, -1):
                digit = digits[i]
                number += digits[i] * exponent
                exponent *= 3

            stack.append(number)
            digits = digits[:0]

        # Apply operation
        if value <= OPERATION:
            len_stack = len(stack)
            system.message(len_stack)
            if len(stack) < 2:
                system.message('Error: not enough values on the stack, 2 required')
                break

            op1 = stack[len(stack)-2]
            op2 = stack[len(stack)-1]
            stack = stack[:len(stack)-2]
            result = 0
            if value == ADD:
                result = op1 + op2
            elif value == SUB:
                result = op1 - op2
            elif value == MUL:
                result = op1 * op2
            elif value == DIV:
                result = op1 // op2

            # TODO: Unary operation Not is not implemented
            # if not (-3280 <= result <= 3280):
            if -3280 > result or result > 3280:
                system.message('Error: number is too big')
                break

            stack.append(result)

            # Translate number to ternary digits
            reversed_digits = [0, 0, 0, 0, 0, 0, 0, 0][:0]
            while result != 0:
                if result % 3 == 0:
                    reversed_digits.append(0)
                    result //= 3
                elif result % 3 == 1:
                    reversed_digits.append(1)
                    result //= 3
                elif result % 3 == 2:
                    reversed_digits.append(-1)
                    result = (result + 1) // 3
            if len(reversed_digits) == 0:
                reversed_digits.append(0)

            for i in range(len(reversed_digits)-1, -1, -1):
                digits.append(reversed_digits[i])

            clear_display_on_next_number = True

    elif value == RESET:
        stack = stack[:0]
        digits = digits[:0]

    value = NOP
