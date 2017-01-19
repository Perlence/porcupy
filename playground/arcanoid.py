PLAYER = yegiks[0]
BALL = yegiks[1]
BALL_BOT = bots[1]

FLOOR = points[0].pos_y
CEIL = points[1].pos_y

# Initialization
if timers[1].value == 1:
    system.bots = 1

    PLAYER.spawn(2)
    PLAYER.weapon = 2
    PLAYER.has_weapon = True

    BALL.spawn(1)
    BALL_BOT.ai = False
    ball_speed_x = 0.0

    green_armor = 0
    yellow_armor = 0
    red_armor = 0
    ball_damage = 0

# Infinite ammo
PLAYER.ammo = 50

# End screen
if -BALL.pos_y < -FLOOR:
    game_duration = timers[1].value / 50
    timers[1].stop()

    BALL.health = 0

    system.message_at(280, 200, 1, 'Game_Over!')
    system.message_at(280, 215, 1, 'Your score: {score}')
    system.message_at(280, 230, 1, 'Green: {green_armor}')
    system.message_at(280, 245, 1, 'Yellow: {yellow_armor}')
    system.message_at(280, 260, 1, 'Red: {red_armor}')
    system.message_at(280, 275, 1, 'Game duration: {game_duration}')
    system.message_at(280, 290, 1, 'Ball damage: {ball_damage}')

# Scoring
if BALL.armor > 0:
    if BALL.armor == 100:
        green_armor += 1
    elif BALL.armor == 150:
        yellow_armor += 1
    elif BALL.armor == 200:
        red_armor += 1
    BALL.armor = 0

score = green_armor*100 + yellow_armor*150 + red_armor*200

if BALL.health > 0:
    system.message_at(30, 30, 1, 'Your score: {score}')

# Ball movement
BALL.speed_y *= 0.9

# Ball bouncing off the walls
if BALL.speed_x != 0 and BALL.speed_y != 0:
    ball_speed_x = BALL.speed_x
if ball_speed_x != 0 and BALL.speed_x == 0 and BALL.speed_y != 0:
    ball_speed_x *= -1.0
    BALL.speed_x = ball_speed_x
if -BALL.pos_y > -CEIL:
    BALL.pos_y = CEIL
    BALL.speed_y *= -0.5

# Ball impulse
is_ball_damaged = 0 < BALL.health < 100
if is_ball_damaged:
    speed_x = BALL.pos_x - PLAYER.pos_x
    speed_y = (PLAYER.pos_y - BALL.pos_y) / (speed_x * 0.1)

    if speed_x < 0:
        speed_x = -10.0
    elif speed_x > 0:
        speed_x = 10.0
        speed_y *= -1.0

    BALL.speed_x = speed_x
    BALL.speed_y = speed_y

    ball_damage += 100 - BALL.health
    BALL.health = 100
