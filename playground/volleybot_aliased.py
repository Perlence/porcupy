PLAYERS = [yegiks[0], yegiks[1]]
BALL = yegiks[2]

PLAYER_BOT = bots[1]
BALL_BOT = bots[2]

NET = points[0]
WAYPOINT = points[1]

PLAYER_SPAWNS = [1, 4]
BALL_SPAWNS = [2, 3]

PUNCH_VELOCITY_X = 10
PUNCH_VELOCITY_Y = -15

if timers[1].value == 1:
    player_touches = [0, 0]

    system.bots = 2
    PLAYERS[0].spawn(PLAYER_SPAWNS[0])
    PLAYERS[1].spawn(PLAYER_SPAWNS[1])
    PLAYER_BOT.ai = False
    PLAYER_BOT.goto = WAYPOINT

    BALL.spawn(BALL_SPAWNS[0])
    BALL_BOT.ai = 0
    ball_speed_x = BALL.speed_x = BALL.speed_y = 0

# Ball movement
BALL.health = 100
BALL.speed_y *= 0.88

if BALL.speed_x != 0 and BALL.speed_y != 0:
    ball_speed_x = BALL.speed_x

if ball_speed_x != 0 and BALL.speed_x == 0 and BALL.speed_y != 0:
    ball_speed_x *= -0.8
    BALL.speed_x = ball_speed_x

# Calculate punches
# for player_num, player in enumerate(PLAYERS):
player_num = 0
for player in PLAYERS:
    if player_touches[player_num] >= 3:
        continue
    if (player.pos_y - 20 < BALL.pos_y < NET.pos_y and
            player.pos_x - 20 < BALL.pos_x < player.pos_x + 20):
        player_touches[player_num] += 1
        player_touches[1-player_num] = 0
        player_ball_distance_x = BALL.pos_x - player.pos_x

        BALL.speed_x = PUNCH_VELOCITY_X
        if player_ball_distance_x < 0:
            BALL.speed_x *= -1

        BALL.speed_y = PUNCH_VELOCITY_Y
    player_num += 1

# Check touches
if player_touches[0] == 3 or player_touches[1] == 3:
    system.color = 188
    system.message_at(282, 100, 50, '3 kasaniya!')
    system.color = 200*256

# Player scores
player_num_scores = -1
if BALL.pos_y > NET.pos_y and BALL.pos_x > NET.pos_x:
    player_num_scores = 0
elif BALL.pos_y > NET.pos_y and BALL.pos_x < NET.pos_x:
    player_num_scores = 1

if player_num_scores > -1:
    PLAYERS[player_num_scores].frags += 1

    BALL.spawn(BALL_SPAWNS[player_num_scores])
    ball_speed_x = BALL.speed_x = BALL.speed_y = 0

    # player_touches = [0, 0]
    player_touches[0] = player_touches[1] = 0

# Bot intelligence
WAYPOINT.pos_y = 425
WAYPOINT.pos_x = BALL.pos_x
PLAYER_BOT.goto = WAYPOINT
