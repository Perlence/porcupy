PLAYER = yozhiks[0]

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
if timers[0].value == 1:
    stack = slice(int, 0, 5)
    digits = slice(int, 0, 8)

    PLAYER.spawn(1)
    PLAYER.weapon = W_MACHINE_GUN
    PLAYER.has_weapon = 1
    PLAYER.ammo = 1

    clear_display_on_next_number = False

PLAYER.health = 100

# Display controls
print_at(points[0].pos_x, points[0].pos_y, 1, '-1')
print_at(points[1].pos_x, points[1].pos_y, 1, '0')
print_at(points[2].pos_x, points[2].pos_y, 1, 'R')
print_at(points[3].pos_x, points[3].pos_y, 1, '1')
print_at(points[4].pos_x, points[4].pos_y, 1, 'P')
print_at(points[5].pos_x, points[5].pos_y, 1, '+')
print_at(points[6].pos_x, points[6].pos_y, 1, '-')
print_at(points[7].pos_x, points[7].pos_y, 1, '*')
print_at(points[8].pos_x, points[8].pos_y, 1, '/')

# LED
x = points[9].pos_x
y = points[9].pos_y
for digit in digits:
    if digit < 0:
        print_at(x, y, 1, '-')
    elif digit == 0:
        print_at(x, y, 1, digit)
    else:
        print_at(x, y, 1, '+')
    x += 12

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
        value = PUSH
    elif 69 <= PLAYER.view_angle <= 76:
        value = ADD
    elif 86 <= PLAYER.view_angle <= 95:
        value = SUB
    elif 106 <= PLAYER.view_angle <= 114:
        value = MUL
    elif 125 <= PLAYER.view_angle <= 127:
        value = DIV

# Evaluate the stack
while value != NOP:
    if value <= NUMBER:
        if len(digits) == cap(digits):
            break
        if clear_display_on_next_number:
            digits = digits[:0]
            clear_display_on_next_number = False
        digits.append(value)

    elif value <= OPERATION or value == PUSH:
        if not clear_display_on_next_number and digits:
            # Convert ternary digits to a number
            number = 0
            exponent = 1
            for digit in reversed(digits):
                number += digit * exponent
                exponent *= 3

            stack.append(number)

        # Apply the operation
        if value <= OPERATION:
            if len(stack) < 2:
                print('Error: not enough values on the stack, 2 required')
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

            print(number)

            if not -3280 <= result <= 3280:
                print('Error: number is too big')
                break

            stack.append(result)

            # Translate number to ternary digits
            reversed_digits = slice(int, 0, 8)
            while result != 0:
                mod = result % 3
                if mod < 2:
                    reversed_digits.append(mod)
                    result //= 3
                else:
                    reversed_digits.append(-1)
                    result = (result + 1) // 3
            if not reversed_digits:
                reversed_digits.append(0)

            digits = digits[:0]
            for digit in reversed(reversed_digits):
                digits.append(digit)

            clear_display_on_next_number = True

        else:
            digits = digits[:0]

    elif value == RESET:
        stack = stack[:0]
        digits = digits[:0]

    value = NOP
