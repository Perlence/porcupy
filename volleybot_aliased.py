from pyegs.runtime import timers, system, yegiks, bots, points

PUNCH_FORCE = -15

if timers[1].value <= 1:
    players = (yegiks[0], yegiks[1])  # p1z 1 p2z 2
    ball = yegiks[2]  # p3z 3

    player_bot = bots[1]  # p4z 2
    ball_bot = bots[2]  # p5z 3

    net = points[0]  # p6z 1
    waypoint = points[1]  # p7z 2

    player_spawns = (1, 4)  # p8z 1 p9z 4
    ball_spawns = (2, 3)  # p10z 2 p11z 3
    ball_speed_x = 0  # p12z 0
    player_touches = (0, 0)  # p13z 0 p14z 0

    system.bots = 2  # yb 2
    players[0].spawn(player_spawns[0])  # p15z 1+0 p16z 8+0 e^15b p16z
    players[1].spawn(player_spawns[1])  # p15z 1+0 p16z 8+0 e^15b p16z
    player_bot.ai = False  # a^5i 0
    player_bot.goto(waypoint)  # a^5g p7z

    ball.spawn(2)
    ball_bot.ai = 0
    ball.speed_y = 0
    ball.speed_x = 0

# Ball movement
ball.health = 100
ball.speed_y *= 0.88

if ball.speed_x != 0 and ball.speed_y != 0:
    ball_speed_x = ball.speed_x

if ball_speed_x != 0 and ball.speed_x == 0 and ball.speed_y != 0:
    ball_speed_x *= -0.8
    ball.speed_x = ball_speed_x

# Calculate punches
for player_num, player in enumerate(players):
    if player_touches[player_num] >= 4:
        continue
    if (player.pos_y - 20 < ball.pos_y < net.pos_y and
            player.pos_x - 20 < ball.pos_x < player.pos_x + 20):
        player_touches[player_num] += 1
        player_touches[1-player_num] = 0
        player_ball_distance_x = ball.pos_x - player.pos_x

        if player_ball_distance_x > 0:
            ball.speed_x = 10

        if player_ball_distance_x < 0:
            ball.speed_x = -10

        ball.speed_y = PUNCH_FORCE  # e^3v -15

# Check touches
if player_touches[0] == 3 or player_touches[1] == 3:
    system.message_at(282, 100, 50, '3 касания!')

# Player scores
player_num_scores = -1
if ball.pos_y > net.pos_y and ball.pos_x > net.pos_x:
    player_num_scores = 0
elif ball.pos_y > net.pos_y and ball.pos_x < net.pos_x:
    player_num_scores = 1

if player_num_scores > -1:
    timers[1].value = 5

    players[player_num].frags += 1

    ball.spawn(ball_spawns[player_num])
    ball.speed_y = 0
    ball.speed_x = 0

    ball_speed_x = 0
    ball_speed_y = 0

    player_touches = (0, 0)

# Bot intelligence
waypoint.pos_y = 425
waypoint.pos_x = ball.pos_x
player_bot.goto(2)
