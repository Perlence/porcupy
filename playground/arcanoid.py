PLAYER = yozhiks[0]
BALL = yozhiks[1]
BALL_BOT = bots[1]

GAME_TIMER = timers[1]

FLOOR = points[0].pos_y
CEIL = points[1].pos_y

PUNCH_VELOCITY = 15

# Initialization
if timers[0].value == 1:
    system.bots = 1

    PLAYER.spawn(2)
    PLAYER.weapon = W_ROCKET_LAUNCHER
    PLAYER.has_weapon = True
    PLAYER.ammo = 30

# Restart game after player shoots
if timers[0].value == 1 or PLAYER.ammo < 30 and BALL.health == 0:
    BALL.spawn(1)
    BALL_BOT.ai = False
    ball_speed_x = 0

    green_armor = yellow_armor = red_armor = 0
    ball_damage = 0

    GAME_TIMER.value = 1
    GAME_TIMER.start()

PLAYER.health = 100

if PLAYER.ammo < 30:
    launch_x = PLAYER.pos_x
    launch_y = PLAYER.pos_y
    PLAYER.ammo = 30

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

# End screen
if -BALL.pos_y < -FLOOR:
    game_duration = GAME_TIMER.value / 50
    GAME_TIMER.stop()

    BALL.health = 0

    X, y = 250, 150

    print_at(X, y, 1, 'Game_Over!')
    y += 30

    print_at(X, y, 1, 'Your score:', score)
    y += 15
    print_at(X, y, 1, 'Green:', green_armor)
    y += 15
    print_at(X, y, 1, 'Yellow:', yellow_armor)
    y += 15
    print_at(X, y, 1, 'Red:', red_armor)
    y += 15
    print_at(X, y, 1, 'Game duration:', game_duration)
    y += 15
    print_at(X, y, 1, 'Ball damage:', ball_damage)
    y += 30

    print_at(X, y, 1, 'Shoot to restart')

if BALL.health > 0:
    print_at(30, 30, 1, 'Your score:', score)

# Ball movement
if BALL.speed_y > 0:
    BALL.speed_y *= 0.9

# Ball bouncing off the walls
if BALL.speed_x != 0 and BALL.speed_y != 0:
    ball_speed_x = BALL.speed_x
    ball_speed_y = BALL.speed_y
if ball_speed_x != 0 and BALL.speed_x == 0 and BALL.speed_y != 0:
    ball_speed_x *= -1
    BALL.speed_x = ball_speed_x
if -BALL.pos_y > -CEIL:
    BALL.pos_y = CEIL
    BALL.speed_y *= -1

# Ball impulse
is_ball_damaged = 0 < BALL.health < 100
if is_ball_damaged:
    dist_x = BALL.pos_x - launch_x
    dist_y = BALL.pos_y - launch_y

    # Calculate length of speed vector via Newton's method
    sqr_hypo = dist_y*dist_y + dist_x*dist_x
    hypo = sqr_hypo/2
    for _ in range(8):
        hypo = (hypo + sqr_hypo/hypo) / 2

    BALL.speed_x = dist_x/hypo * PUNCH_VELOCITY/2
    BALL.speed_y = dist_y/hypo * PUNCH_VELOCITY

    ball_damage += 100 - BALL.health
    BALL.health = 100
