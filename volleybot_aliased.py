from pyegs.runtime import timers, system, yegiks, bots, points

PLAYERS = [yegiks[1], yegiks[2]]
BALL = yegiks[2]

PLAYER_BOT = bots[2]
BALL_BOT = bots[3]

NET = points[1]
WAYPOINT = points[2]

PLAYER_SPAWNS = [1, 4]
BALL_SPAWNS = [2, 3]

PUNCH_FORCE = -15

if timers[1].value <= 1:
    ball_speed_x = 0  # p12z 0
    player_touches = [0, 0]  # p13z 0 p14z 0

    system.bots = 2  # yb 2
    PLAYERS[0].spawn(PLAYER_SPAWNS[0])  # p15z 1+0 p16z 8+0 e^15b p16z
    PLAYERS[1].spawn(PLAYER_SPAWNS[1])  # p15z 1+0 p16z 8+0 e^15b p16z
    PLAYER_BOT.ai = False  # a^5i 0
    PLAYER_BOT.goto(WAYPOINT)  # a^5g p7z

    BALL.spawn(BALL_SPAWNS[0])
    BALL_BOT.ai = 0
    BALL.speed_y = 0
    BALL.speed_x = 0

# Ball movement
BALL.health = 100
BALL.speed_y *= 0.88

if BALL.speed_x != 0 and BALL.speed_y != 0:
    ball_speed_x = BALL.speed_x

if ball_speed_x != 0 and BALL.speed_x == 0 and BALL.speed_y != 0:
    ball_speed_x *= -0.8
    BALL.speed_x = ball_speed_x

# Calculate punches
for player_num, player in enumerate(PLAYERS):
    if player_touches[player_num] >= 4:
        continue
    if (player.pos_y - 20 < BALL.pos_y < NET.pos_y and
            player.pos_x - 20 < BALL.pos_x < player.pos_x + 20):
        player_touches[player_num] += 1
        player_touches[1-player_num] = 0
        player_ball_distance_x = BALL.pos_x - player.pos_x

        if player_ball_distance_x > 0:
            BALL.speed_x = 10

        if player_ball_distance_x < 0:
            BALL.speed_x = -10

        BALL.speed_y = PUNCH_FORCE  # e^3v -15

# Check touches
if player_touches[0] == 3 or player_touches[1] == 3:
    system.message_at(282, 100, 50, '3 касания!')

# Player scores
player_num_scores = -1
if BALL.pos_y > NET.pos_y and BALL.pos_x > NET.pos_x:
    player_num_scores = 0
elif BALL.pos_y > NET.pos_y and BALL.pos_x < NET.pos_x:
    player_num_scores = 1

if player_num_scores > -1:
    timers[1].value = 5

    PLAYERS[player_num].frags += 1

    BALL.spawn(BALL_SPAWNS[player_num])
    BALL.speed_y = 0
    BALL.speed_x = 0

    ball_speed_x = 0
    ball_speed_y = 0

    player_touches = (0, 0)

# Bot intelligence
WAYPOINT.pos_y = 425
WAYPOINT.pos_x = BALL.pos_x
PLAYER_BOT.goto(2)
