import dataclasses
import math
import random
import c


sfx_good = [.5,0,329.6276,0,0,.1,3,.2,0,0,0,0,0,0,0,0,0,1,0,0,0]
sfx_bad = [1,0,440,0,0,.1,4,1.4,0,0,0,0,0,0,0,0,0,1,0,0,0]
sfx_press = [.5,0,261.6256,0,0,.1,3,.3,0,0,0,0,0,0,0,0,0,1,0,0,0]
sfx_release = [.5,0,195.9977,0,0,.1,3,.3,0,0,0,0,0,0,0,0,0,1,0,0,0]


buttons = [False]


def event(type, id, data):
    global start
    if type == 'button':
        buttons[id] = data
    if type == 'button' and id == 0:
        c.sfx(sfx_press if data else sfx_release)
        start = False


def _draw_block(x, y, opeartor, value, face_color, border_color, shadow_color, text_color):
    c.set_palette_map([border_color, shadow_color, face_color])
    if -1 >= value >= -2:
        c.draw_sprite(x - 1, y - 1, 13, 21, 15, 16)
        return
    elif -3 >= value >= -4:
        c.draw_sprite(x - 1, y - 1, 28, 21, 15, 16)
        return
    c.draw_sprite(x, y, 0, 21, 13, 14)
    c.set_palette_map([text_color])
    if opeartor is not None:
        if opeartor in '+-*/=':
            c.draw_sprite(x + 3, y + 4, {'+': 30, '-': 33, '*': 36, '/': 39, '=': 42}[opeartor], 0, 3, 5)
            c.draw_sprite(x + 7, y + 4, value * 3, 0, 3, 5)
        elif opeartor == 'sqrt':
            c.draw_sprite(x + 4, y + 4, 40, 5, 5, 5)
        elif opeartor == 'log':
            c.draw_sprite(x + 2, y + 3, 0, 35, 9, 7)
        return
    text1 = str(value)
    text2 = (len(text1) - 1) // 3
    digits = len(text1) % 3
    if text2 == 0:
        if digits == 1:
            c.draw_sprite(x + 5, y + 4, (ord(text1[0]) - 48) * 3, 0, 3, 5)
        elif digits == 2:
            c.draw_sprite(x + 3, y + 4, (ord(text1[0]) - 48) * 3, 0, 3, 5)
            c.draw_sprite(x + 7, y + 4, (ord(text1[1]) - 48) * 3, 0, 3, 5)
        else:
            c.draw_sprite(x + 1, y + 4, (ord(text1[0]) - 48) * 3, 0, 3, 5)
            c.draw_sprite(x + 5, y + 4, (ord(text1[1]) - 48) * 3, 0, 3, 5)
            c.draw_sprite(x + 9, y + 4, (ord(text1[2]) - 48) * 3, 0, 3, 5)
    elif text2 < 9:
        if digits == 1:
            c.draw_sprite(x + 1, y + 1, (ord(text1[0]) - 48) * 3, 0, 3, 5)
            c.set_pixel(x + 6, y + 5, text_color)
            c.draw_sprite(x + 9, y + 1, (ord(text1[1]) - 48) * 3, 0, 3, 5)
        elif digits == 2:
            c.draw_sprite(x + 3, y + 1, (ord(text1[0]) - 48) * 3, 0, 3, 5)
            c.draw_sprite(x + 7, y + 1, (ord(text1[1]) - 48) * 3, 0, 3, 5)
        else:
            c.draw_sprite(x + 1, y + 1, (ord(text1[0]) - 48) * 3, 0, 3, 5)
            c.draw_sprite(x + 5, y + 1, (ord(text1[1]) - 48) * 3, 0, 3, 5)
            c.draw_sprite(x + 9, y + 1, (ord(text1[2]) - 48) * 3, 0, 3, 5)
        c.draw_sprite(x + 4, y + 7, (text2 - 1) * 5, 5, 5, 5)
    else:
        c.draw_sprite(x + 1, y + 1, 0, 10, 11, 11)


def draw_block(x, y, operator, value, face_color, border_color, shadow_color, text_color):
    _draw_block(x, y, operator, value, face_color, border_color, shadow_color, text_color)
    if x < 1:
        _draw_block(x + 128, y, operator, value, face_color, border_color, shadow_color, text_color)
    if x > 114:
        _draw_block(x - 128, y, operator, value, face_color, border_color, shadow_color, text_color)


x_speed = 1
x_tick = 0
y_speed = 1
y_tick = 0


@dataclasses.dataclass
class Block:
    id: int
    x: int
    y: int
    value: int
    face_color: int    # 11, 10, 9, 8, 0
    border_color: int
    shadow_color: int  # 13, 14, 15, 0, 8
    text_color: int    # 0, 0, 0, 12, 12
    operator: str | None = None
    type: str = 'neutral'  # player | neutral | none
    width: int = 13
    height: int = 13

    def intersect(self, other):
        x1 = 64
        x2 = x1 + self.width
        x3 = (other.x - self.x + 64) & 0x7f
        x4 = x3 + other.width
        x_intersect = x2 > x3 and x1 < x4
        y_intersect = self.y + self.height > other.y and self.y < other.y + other.height
        return x_intersect and y_intersect


next_entity_id = 2
entities = {
    0: Block(0, 0, 110, 1, 11, 11, 13, 0, None, 'player'),
}
score = 1
try:
    high_score = int(c.load_high_score('numbers'))
except Exception:
    high_score = 1


def movement():
    global x_tick, y_tick, entities
    y_tick += 1
    if y_tick >= y_speed:
        y_tick = 0
    if y_tick == 0:
        for n in entities.values():
            if n.type != 'neutral':
                continue
            n.y += 1
            for p in entities.values():
                if p.type != 'player':
                    continue
                if p.intersect(n):
                    if n.operator is None:
                        c.sfx(sfx_good)
                        n.type = 'player'
                        n.y -= 1
                        break
                    elif n.operator == '+':
                        c.sfx(sfx_good)
                        p.value += n.value
                        n.value = -1
                        n.type = 'none'
                        n.y -= 1
                        break
                    elif n.operator == '-':
                        c.sfx(sfx_bad)
                        if p.value > n.value:
                            p.value -= n.value
                            n.value = -1
                            n.type = 'none'
                            n.y -= 1
                            break
                        elif p.value < n.value:
                            n.value -= p.value
                            p.value = -1
                            p.type = 'none'
                        else:
                            p.value = -1
                            p.type = 'none'
                            n.value = -1
                            n.type = 'none'
                            n.y -= 1
                            break
                    elif n.operator == '*':
                        c.sfx(sfx_good)
                        p.value *= n.value
                        n.value = -1
                        n.type = 'none'
                        n.y -= 1
                        break
                    elif n.operator == '/':
                        c.sfx(sfx_bad)
                        if p.value >= n.value:
                            p.value //= n.value
                            n.value = -1
                            n.type = 'none'
                            n.y -= 1
                            break
                        else:
                            p.value = -1
                            p.type = 'none'
                    elif n.operator == '=':
                        c.sfx(sfx_bad)
                        p.value = n.value
                        n.value = -1
                        n.type = 'none'
                        n.y -= 1
                        break
                    elif n.operator == 'sqrt':
                        c.sfx(sfx_bad)
                        p.value = math.isqrt(p.value)
                        n.value = -1
                        n.type = 'none'
                        n.y -= 1
                        break
                    elif n.operator == 'log':
                        c.sfx(sfx_bad)
                        if p.value >= 10:
                            p.value = len(str(p.value)) - 1
                            n.value = -1
                            n.type = 'none'
                            n.y -= 1
                            break
                        else:
                            p.value = -1
                            p.type = 'none'
    x_tick += 1
    if x_tick >= x_speed:
        x_tick = 0
    if x_tick == 0:
        dx = -1 if buttons[0] else 1
        players = [e for e in entities.values() if e.type == 'player']
        while players:
            p = players.pop()
            p.x = (p.x + dx) & 0x7f
            for n in entities.values():
                if n.type != 'neutral':
                    continue
                if p.intersect(n):
                    if n.operator is None:
                        c.sfx(sfx_good)
                        n.type = 'player'
                        players.append(n)
                    elif n.operator == '+':
                        c.sfx(sfx_good)
                        p.value += n.value
                        n.value = -1
                        n.type = 'none'
                    elif n.operator == '-':
                        c.sfx(sfx_bad)
                        if p.value > n.value:
                            p.value -= n.value
                            n.value = -1
                            n.type = 'none'
                        elif p.value < n.value:
                            n.value -= p.value
                            p.value = -1
                            p.type = 'none'
                            p.x = (p.x - dx) & 0x7f
                            break
                        else:
                            p.value = -1
                            p.type = 'none'
                            p.x = (p.x - dx) & 0x7f
                            n.value = -1
                            n.type = 'none'
                            break
                    elif n.operator == '*':
                        c.sfx(sfx_good)
                        p.value *= n.value
                        n.value = -1
                        n.type = 'none'
                    elif n.operator == '/':
                        c.sfx(sfx_bad)
                        if p.value >= n.value:
                            p.value //= n.value
                            n.value = -1
                            n.type = 'none'
                        else:
                            p.value = -1
                            p.type = 'none'
                            p.x = (p.x - dx) & 0x7f
                            break
                    elif n.operator == '=':
                        c.sfx(sfx_bad)
                        p.value = n.value
                        n.value = -1
                        n.type = 'none'
                    elif n.operator == 'sqrt':
                        c.sfx(sfx_bad)
                        p.value = math.isqrt(p.value)
                        n.value = -1
                        n.type = 'none'
                    elif n.operator == 'log':
                        c.sfx(sfx_bad)
                        if p.value >= 10:
                            p.value = len(str(p.value)) - 1
                            n.value = -1
                            n.type = 'none'
                        else:
                            p.value = -1
                            p.type = 'none'
                            p.x = (p.x - dx) & 0x7f
                            break


def color():
    global score, high_score
    score = 0
    for e in entities.values():
        if e.type != 'player':
            continue
        if e.value < 10:
            e.face_color = 11
            e.border_color = 11
            e.shadow_color = 13
            e.text_color = 0
        elif e.value < 100:
            e.face_color = 10
            e.border_color = 10
            e.shadow_color = 14
            e.text_color = 0
        elif e.value < 1000:
            e.face_color = 9
            e.border_color = 9
            e.shadow_color = 15
            e.text_color = 0
        elif e.value < 1000_000:
            e.face_color = 8
            e.border_color = 8
            e.shadow_color = 0
            e.text_color = 12
        else:
            e.face_color = 0
            e.border_color = 0
            e.shadow_color = 8
            e.text_color = 12
        score += e.value
    if score > high_score:
        high_score = score
        c.save_high_score('numbers', str(high_score))


def generate():
    global entities, next_entity_id
    if random.randrange(60) < 4:
        e = Block(next_entity_id, random.randrange(128), -16, 0, 11, 11, 13, 0)
        next_entity_id += 1
        for e2 in entities.values():
            if e2.type != 'neutral':
                continue
            if e.intersect(e2):
                return
        operator_random = random.randrange(100)
        if score < 1100:
            p = {'': 20, '+': 55, '*': 60, '-': 90, '/': 99, '=': 100, 'sqrt': 100, 'log': 100}
        elif score < 1100_000:
            p = {'': 20, '+': 55, '*': 60, '-': 88, '/': 97, '=': 99, 'sqrt': 100, 'log': 100}
        elif score < 1100_000_000:
            p = {'': 20, '+': 55, '*': 60, '-': 83, '/': 92, '=': 97, 'sqrt': 99, 'log': 100}
        elif score < 1100_000_000_000:
            p = {'': 20, '+': 55, '*': 60, '-': 73, '/': 83, '=': 93, 'sqrt': 98, 'log': 100}
        elif score < 1100_000_000_000_000:
            p = {'': 20, '+': 55, '*': 60, '-': 70, '/': 80, '=': 90, 'sqrt': 95, 'log': 100}
        elif score < 1100_000_000_000_000_000:
            p = {'': 20, '+': 55, '*': 60, '-': 65, '/': 70, '=': 80, 'sqrt': 90, 'log': 100}
        else:
            p = {'': 20, '+': 55, '*': 60, '-': 62, '/': 64, '=': 76, 'sqrt': 88, 'log': 100}
        if operator_random < p['']:
            e.operator = None
            e.value = random.randrange(1, 10)
        elif operator_random < p['+']:
            e.operator = '+'
            e.value = random.randrange(1, 6)
            e.face_color = 6
            e.border_color = 6
            e.shadow_color = 7
        elif operator_random < p['*']:
            e.operator = '*'
            e.value = random.randrange(2, 5)
            e.face_color = 6
            e.border_color = 6
            e.shadow_color = 7
        elif operator_random < p['-']:
            e.operator = '-'
            e.value = random.randrange(1, 10)
            e.face_color = 2
            e.border_color = 2
            e.text_color = 12
            e.shadow_color = 1
        elif operator_random < p['/']:
            e.operator = '/'
            e.value = random.randrange(2, 10)
            e.face_color = 2
            e.border_color = 2
            e.text_color = 12
            e.shadow_color = 1
        elif operator_random < p['=']:
            e.operator = '='
            e.value = random.randrange(1, 10)
            e.face_color = 2
            e.border_color = 2
            e.text_color = 12
            e.shadow_color = 1
        elif operator_random < p['sqrt']:
            e.operator = 'sqrt'
            e.value = 0
            e.face_color = 2
            e.border_color = 2
            e.text_color = 12
            e.shadow_color = 1
        else:
            e.operator = 'log'
            e.value = 0
            e.face_color = 2
            e.border_color = 2
            e.text_color = 12
            e.shadow_color = 1
        entities[e.id] = e


def bottom():
    for e in entities.values():
        if e.type == 'none':
            continue
        if e.y + e.height >= 128:
            e.type = 'none'
            e.value = -1


def animation():
    global entities
    to_remove = []
    for n in entities.values():
        if n.value >= 0:
            continue
        n.value -= 1
        if n.value == -5:
            to_remove.append(n.id)
    for i in to_remove:
        del entities[i]


last_button = False
pause = False
start = True


def draw():
    global pause
    def key(e):
        return (e.type != 'none', e.y)
    for e in sorted(entities.values(), key=key):
        draw_block(e.x, e.y, e.operator, e.value, e.face_color, e.border_color, e.shadow_color, e.text_color)
    c.fill_rect(0, 127, 128, 1, 14)
    if score == 0:
        pause = True
    score_s = str(score)
    c.set_palette_map([0])
    c.draw_sprite(0, 0, 11, 10, 22, 5)
    if len(score_s) > 26:
        c.draw_sprite(24, 0, 9, 37, 35, 5)
    else:
        for i, char in enumerate(score_s):
            c.draw_sprite(24 + i * 4, 0, (ord(char) - 48) * 3, 0, 3, 5)
    score_s = str(high_score)
    c.draw_sprite(4, 6, 29, 37, 22, 5)
    if len(score_s) > 26:
        c.draw_sprite(24, 6, 9, 37, 35, 5)
    else:
        for i, char in enumerate(score_s):
            c.draw_sprite(24 + i * 4, 6, (ord(char) - 48) * 3, 0, 3, 5)
    if pause or start:
        c.draw_sprite(29, 56, 0, 42, 69, 7)
        c.draw_sprite(41, 65, 0, 49, 45, 7)


def restart():
    global entities, next_entity_id, score, pause
    next_entity_id = 2
    entities = {
        0: Block(0, 0, 110, 1, 11, 11, 13, 0, None, 'player'),
    }
    score = 1
    pause = False


def tick():
    global last_button, pause
    if pause:
        if buttons[0] and not last_button:
            restart()
    else:
        c.clear_screen(12)
        movement()
        color()
        generate()
        bottom()
        animation()
        draw()
    last_button = buttons[0]
