timers = []
system = object()
yozhiks = []
bots = []
var = []
points = []

if timers[1].value == 1:
    system.bots = 2
    yozhiks[1].spawn = 1
    yozhiks[2].spawn = 4
    bots[2].ai = 0
    bots[2].goto(2)

    yozhiks[3].spawn = 2
    bots[3].ai = 0
    yozhiks[3].speed_y = 0
    yozhiks[3].speed_x = 0
    var[15].value = 0
    var[16].value = 0
    var[90].value = 0
    var[10].value = 0
    var[11].value = 0
    var[12].value = 0

yozhiks[3].health = 100
var[1].value = yozhiks[3].speed_y
var[1].value = var[1].value * 0.88
yozhiks[3].speed_y = var[1].value

if yozhiks[3].speed_x != 0 and yozhiks[3].speed_y != 0:
    var[15].value = yozhiks[3].speed_x
    var[16].value = yozhiks[3].speed_y

if var[15].value != 0 and yozhiks[3].speed_x == 0 and yozhiks[3].speed_y != 0:
    var[15].value = var[15].value * -0.8
    yozhiks[3].speed_x = var[15].value
    yozhiks[3].speed_y = var[16].value

# p1
if (yozhiks[3].pos_y > yozhiks[1].pos_y - 20 and yozhiks[3].pos_y < points[1].pos_y and
        yozhiks[3].pos_x > yozhiks[1].pos_x - 20 and yozhiks[3].pos_x < yozhiks[1].pos_x + 20 and
        var[10].value != 4):
    var[7].value = yozhiks[3].pos_x - yozhiks[1].pos_x
    var[8].value = -15
    var[12].value = 0
    var[10].value = var[10].value + 1

if (yozhiks[3].pos_y > yozhiks[1].pos_y - 20 and yozhiks[3].pos_y < points[1].pos_y and
        yozhiks[3].pos_x > yozhiks[1].pos_x - 20 and yozhiks[3].pos_x < yozhiks[1].pos_x + 20 and
        var[7].value > 0 and var[10].value != 4):
    var[7].value = 10

if (yozhiks[3].pos_y > yozhiks[1].pos_y - 20 and yozhiks[3].pos_y < points[1].pos_y and
        yozhiks[3].pos_x > yozhiks[1].pos_x - 20 and yozhiks[3].pos_x < yozhiks[1].pos_x + 20 and
        var[7].value < 0 and var[10].value != 4):
    var[7].value = 10
    var[7].value = var[7].value * -1

if (yozhiks[3].pos_y > yozhiks[1].pos_y - 20 and yozhiks[3].pos_y < points[1].pos_y and
        yozhiks[3].pos_x > yozhiks[1].pos_x - 20 and yozhiks[3].pos_x < yozhiks[1].pos_x + 20 and
        var[10].value != 4):
    yozhiks[3].speed_x = var[7].value
    yozhiks[3].speed_y = var[8].value
# ------------------------------------------------------------------------------

# p2
if (yozhiks[3].pos_y > yozhiks[2].pos_y - 20 and yozhiks[3].pos_y < points[1].pos_y and
        yozhiks[3].pos_x > yozhiks[2].pos_x - 20 and yozhiks[3].pos_x < yozhiks[2].pos_x + 20 and
        var[12].value != 4):
    var[7].value = yozhiks[3].pos_x-yozhiks[2].pos_x
    var[8].value = -15
    var[10].value = 0
    var[12].value += 1

if (yozhiks[3].pos_y > yozhiks[2].pos_y - 20 and yozhiks[3].pos_y < points[1].pos_y and
        yozhiks[3].pos_x > yozhiks[2].pos_x - 20 and yozhiks[3].pos_x < yozhiks[2].pos_x + 20 and
        var[7].value > 0 and var[12].value != 4):
    var[7].value = var[7].value + 0.4
    var[7].value = var[7].value + 10

if (yozhiks[3].pos_y > yozhiks[2].pos_y - 20 and yozhiks[3].pos_y < points[1].pos_y and
        yozhiks[3].pos_x > yozhiks[2].pos_x - 20 and yozhiks[3].pos_x < yozhiks[2].pos_x + 20 and
        var[7].value < 0 and var[12].value != 4):
    var[7].value = var[7].value * 0.4
    var[7].value = var[7].value + 10
    var[7].value = var[7].value * -1

if (yozhiks[3].pos_y > yozhiks[2].pos_y - 20 and yozhiks[3].pos_y < points[1].pos_y and
        yozhiks[3].pos_x > yozhiks[2].pos_x - 20 and yozhiks[3].pos_x < yozhiks[2].pos_x + 20 and
        var[12].value != 4):
    yozhiks[3].speed_x = var[7].value
    yozhiks[3].speed_y = var[8].value
# ------------------------------------------------------------------------------

if var[10].value == 3 or var[12].value == 3:
    system.message_point(282, 100, 50, '3 касания!')

# +1
if yozhiks[3].pos_y > points[1].pos_y and yozhiks[3].pos_x > points[1].pos_x:
    timers[1].value = 5
    var[11].value = yozhiks[1].frags+1
    yozhiks[1].frags = var[11].value
    var[11].value = 0
    yozhiks[3].spawn = 2
    yozhiks[3].speed_y = 0
    yozhiks[3].speed_x = 0
    var[15].value = 0
    var[16].value = 0
    var[90].value = 0
    var[10].value = 0
    var[11].value = 0
    var[12].value = 0

if yozhiks[3].pos_y > points[1].pos_y and yozhiks[3].pos_x < points[1].pos_x:
    timers[1].value = 5
    var[11].value = yozhiks[2].frags+1
    yozhiks[2].frags = var[11].value
    var[11].value = 0
    yozhiks[3].spawn = 3
    yozhiks[3].speed_y = 0
    yozhiks[3].speed_x = 0
    var[15].value = 0
    var[16].value = 0
    var[90].value = 0
    var[10].value = 0
    var[11].value = 0
    var[12].value = 0

# aihg
points[2].pos_y = 425
points[2].pos_x = yozhiks[3].pos_x
bots[2].goto = 2
