import dataclasses
import random
import c

button = False
buttondown = False

sfx_power_template = [1,0,None,.01,0,.1,1,1,0,0,0,0,0,0,0,0,0,1,0,0,0]
notes = {}
for octave in range(8):
    for i, note in enumerate(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']):
        notes[f'{note}{octave}'] = 13.37858 * 2 ** (octave + i / 12)


def event(type, id, data):
    global button, buttondown, initial, gameover
    if type == 'button' and id == 0:
        if gameover:
            if data:
                reset()
            else:
                gameover = False
        else:
            initial = False
        button = data
        if data:
            buttondown = True


def interpolate(x, x1, x2, y1, y2):
    return y1 + (y2 - y1) * (x - x1) / (x2 - x1)


def power_to_dx_dy(power):
    dx = round(interpolate(power, 0, 120, 120, 240))
    dy = round(interpolate(power, 0, 120, 240, 480))
    return dx, dy


def text(x, y, text, color=0, monospace=True, draw_sprite=c.draw_sprite):
    initial_x = x
    c.set_palette_map([color])
    for i in text:
        if i in '0123456789':
            draw_sprite(x, y, (ord(i) - ord('0')) * 3, 123, 3, 5)
            x += 4
        elif i in 'mM' and not monospace:
            draw_sprite(x, y, 108, 123, 5, 5)
            x += 6
        elif i in 'wW' and not monospace:
            draw_sprite(x, y, 113, 123, 5, 5)
            x += 6
        elif i.lower() in 'abcdefghijklmnopqrstuvwxyz':
            draw_sprite(x, y, (ord(i.lower()) - ord('a')) * 3 + 30, 123, 3, 5)
            x += 4
        elif i == ' ':
            x += 4 if monospace else 3
        elif i == ':':
            if monospace:
                draw_sprite(x + 1, y, 120, 123, 1, 5)
                x += 4
            else:
                draw_sprite(x, y, 120, 123, 1, 5)
                x += 2
        elif i == '!':
            if monospace:
                draw_sprite(x + 1, y, 96, 117, 1, 5)
                x += 4
            else:
                draw_sprite(x, y, 96, 117, 1, 5)
                x += 2
        elif i == '+':
            draw_sprite(x, y, 97, 117, 3, 5)
            x += 4
        elif i == '/':
            if monospace:
                draw_sprite(x, y, 42, 115, 3, 5)
                x += 4
            else:
                draw_sprite(x + 1, y - 1, 42, 114, 3, 7)
                x += 6
        elif i == '\n':
            y += 6
            x = initial_x


@dataclasses.dataclass
class Floor:
    id: int
    x: int
    w_: int
    y: int

    @property
    def w(self):
        return self.w_ * 6

    @property
    def h(self):
        return 7


@dataclasses.dataclass
class Text:
    id: int
    x: int
    y: int
    text: str
    tick: int = 0


time = 0
scale = 120
player_x_scaled = 0
player_y_scaled = 0
player_dx_scaled = 0
player_dy_scaled = 0
player_x = 0
player_y = 0
player_on = 1
camera_x_scaled = -2400
camera_y_scaled = -2400
camera_x = -20
camera_y = -20
old_camera_x = -20
next_entity_id = 100
floors = {
    1: Floor(1, -17, 8, 0),
    2: Floor(2, 50, 8, 0),
    3: Floor(3, 80, 8, 40),
}
texts = {}
last_floor = 3
power = 0
extra_score = 0
initial = True
gameover = False


def fill_rect(x, y, width, height, color):
    c.fill_rect(x - camera_x, 128 - y + camera_y, width, height, color)


def draw_sprite(x, y, sprite_x, sprite_y, width, height):
    c.draw_sprite(x - camera_x, 128 - y + camera_y, sprite_x, sprite_y, width, height)


def movement():
    global player_x_scaled, player_y_scaled, player_dx_scaled, player_dy_scaled, player_x, player_y, player_on, gameover, next_entity_id, power, extra_score
    if player_on and player_dx_scaled == 0:
        if button:
            power += 1
        if power and not button or power == 120:
            player_dx_scaled, player_dy_scaled = power_to_dx_dy(power)
            player_on = None
            c.sfx([.5,0,523.2511,.01,0,interpolate(power, 0, 120, .3, .7),1,1,10,0,0,0,0,.3,0,0,0,1,0,0,0])
            power = 0
        player_x_scaled += player_dx_scaled
        player_y_scaled += player_dy_scaled
        player_x = player_x_scaled // scale
        player_y = player_y_scaled // scale
    elif player_on:
        player_dx_scaled = max(0, player_dx_scaled - 30)
        player_x_scaled += player_dx_scaled
        player_y_scaled += player_dy_scaled
        player_x = player_x_scaled // scale
        player_y = player_y_scaled // scale
        floor = floors[player_on]
        if player_dx_scaled == 0:
            if player_x + 7 == floor.x + floor.w // 2:
                texts[next_entity_id] = Text(next_entity_id, player_x - 16, player_y + 19, 'perfect! +100')
                next_entity_id += 1
                extra_score += 100
                c.sfx([1,0,523.2511,.01,0,.47,0,2.5,0,0,200,.12,.12,0,0,0,0,1,0,0,657])
        if player_x >= floor.x + floor.w + 3:
            player_on = None
            texts[next_entity_id] = Text(next_entity_id, player_x - 16, player_y + 19, 'slipped! +100')
            next_entity_id += 1
            extra_score += 100
            c.sfx([.5,0,315,.03,.19,.11,2,.7,4,19,0,0,0,0,0,0,0,.66,.13,0,0])
    else:
        if player_y <= -35:
            gameover = True
            c.sfx([1,0,46,.01,0,.76,1,1.2,1,-6,0,0,0,0,0,.8,0,.48,.23,.14,102])
        player_dy_scaled -= 15
        old_player_y = player_y
        player_x_scaled += player_dx_scaled
        player_y_scaled += player_dy_scaled
        player_x = player_x_scaled // scale
        player_y = player_y_scaled // scale
        if player_y + 15 > 108:
            player_y = 108 - 15
            player_y_scaled = player_y * scale
        for floor in floors.values():
            if player_y < floor.y and player_x + 15 > floor.x - 2 and player_x < floor.x + floor.w + 3 and old_player_y >= floor.y:
                player_y = floor.y
                player_y_scaled = player_y * scale
                player_dy_scaled = 0
                player_on = floor.id
                break


def generate():
    global last_floor, next_entity_id
    for _ in range(old_camera_x, camera_x):
        count = 0
        for floor in floors.values():
            if floor.x > camera_x + 96:
                count += 1
        p = 100 if count == 0 else 1
        if random.randrange(100) < p:
            if score < 500:
                width = 8
            elif score < 1000:
                width = random.randrange(6, 9)
            elif score < 1500:
                width = random.randrange(4, 7)
            elif score < 2000:
                width = random.randrange(2, 5)
            else:
                width = random.randrange(1)
            height = random.randrange(64)
            floor = Floor(next_entity_id, camera_x + 130, width, height)
            ok = True
            for i in floors.values():
                if floor.x + floor.w + 5 > i.x - 5 and floor.x - 5 < i.x + i.w + 5 and floor.y + 5 > i.y - i.h - 5 and floor.y - i.h - 5 < i.y + 5:
                    ok = False
                    break
            if ok:
                floors[next_entity_id] = floor
                last_floor = next_entity_id
                next_entity_id += 1
    for floor in list(floors.values()):
        if floor.x + floor.w + 5 < camera_x:
            del floors[floor.id]


score = 0
try:
    high_score = int(c.load_high_score('jump'))
except Exception:
    high_score = 0


def camera():
    global camera_x_scaled, camera_x, old_camera_x, score, high_score
    target = (player_x - 20) * scale
    camera_x_scaled += (target - camera_x_scaled) // 10
    old_camera_x = camera_x
    camera_x = camera_x_scaled // scale
    score = (camera_x + 20) // 10 + extra_score
    if score > high_score:
        high_score = score
        c.save_high_score('jump', high_score)


def draw():
    c.clear_screen(12)
    c.set_palette_map([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 255, 13, 14, 15])
    for floor in floors.values():
        if floor.w_ == 0:
            draw_sprite(floor.x - 2, floor.y, 0, 16, 3, 7)
            draw_sprite(floor.x + 1, floor.y, 15, 16, 3, 7)
            continue
        for i in range(floor.w_ + 1):
            if i == 0:
                draw_sprite(floor.x - 2, floor.y, 0, 16, 6, 7)
            elif i < floor.w_:
                draw_sprite(floor.x - 2 + i * 6, floor.y, 6, 16, 6, 7)
            else:
                draw_sprite(floor.x - 2 + i * 6, floor.y, 12, 16, 6, 7)
    if not player_on:
        draw_sprite(player_x, player_y + 14, 32, 0, 15, 15)
    elif time % 60 < 30:
        draw_sprite(player_x, player_y + 14, 0, 0, 15, 14)
    else:
        draw_sprite(player_x, player_y + 14, 16, 0, 15, 14)
    if power:
        height = (power * 15 + 119) // 120
        if ((power - 1) * 15 + 119) // 120 < height:
            sfx_power = sfx_power_template.copy()
            sfx_power[2] = notes[['C4', 'D4', 'E4', 'G4', 'D4', 'E4', 'G4', 'A4', 'E4', 'G4', 'A4', 'C5', 'G4', 'A4', 'C5'][height - 1]]
            c.sfx(sfx_power)
        if height < 4:
            color = 5
        elif height < 8:
            color = 4
        elif height < 12:
            color = 3
        else:
            color = 2
        draw_sprite(player_x + 16, player_y + 16, 48, 0, 4, 17)
        fill_rect(player_x + 17, player_y + height, 2, height, color)
        fill_rect(player_x + 18, player_y + 4, 1, 1, 13)
        fill_rect(player_x + 18, player_y + 8, 1, 1, 13)
        fill_rect(player_x + 18, player_y + 12, 1, 1, 13)
    for i in list(texts.values()):
        text(i.x, i.y, i.text, draw_sprite=draw_sprite)
        i.tick += 1
        if i.tick % 6 == 0:
            i.y += 1
        if i.tick == 60:
            del texts[i.id]
    text(1, 1, f'score:{score}\n high:{high_score}')
    if initial:
        c.draw_sprite(16, 48, 0, 113, 95, 9)
        text(4, 60, 'long press screen/mouse/space', monospace=False)
    if power and not next_entity_id:
        x_scaled = player_x_scaled + 7 * scale
        y_scaled = player_y_scaled + scale
        dx_scaled, dy_scaled = power_to_dx_dy(power)
        for _ in range(100):
            fill_rect(x_scaled // scale, y_scaled // scale, 1, 1, 0)
            x_scaled += dx_scaled
            y_scaled += dy_scaled
            dy_scaled -= 15


def reset():
    global player_x_scaled, player_y_scaled, player_dx_scaled, player_dy_scaled, player_x, player_y, player_on, camera_x_scaled, camera_x, old_camera_x, next_entity_id, floors, texts, last_floor, power, extra_score, initial, score
    player_x_scaled = 0
    player_y_scaled = 0
    player_dx_scaled = 0
    player_dy_scaled = 0
    player_x = 0
    player_y = 0
    player_on = 1
    camera_x_scaled = -2400
    camera_x = -20
    old_camera_x = -20
    next_entity_id = 100
    floors = {
        1: Floor(1, -17, 8, 0),
        2: Floor(2, 50, 8, 0),
        3: Floor(3, 80, 8, 40),
    }
    texts = {}
    last_floor = 3
    power = 0
    extra_score = 0
    initial = True
    score = 0


def tick():
    global time, buttondown
    if not gameover:
        movement()
        generate()
        camera()
    draw()
    time += 1
    buttondown = False
