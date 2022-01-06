import os
import sys
import sqlite3
import pygame
from pygame import draw, transform

width, height = 840, 770
pygame.init()
screen = pygame.display.set_mode((width, height), pygame.NOFRAME)
screen.fill('black')

all_sprites = pygame.sprite.Group()
sprite = pygame.sprite.Sprite()
clock = pygame.time.Clock()

con = sqlite3.connect("data/dungeon_knight.db")
cur = con.cursor()


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
    if colorkey == -1:
        colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def terminate():
    pygame.quit()
    sys.exit()


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y):
        super().__init__(all_sprites)
        self.frames = []
        self.cut_sheet(sheet, columns, rows)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = self.rect.move(x, y)

    def cut_sheet(self, sheet, columns, rows):
        self.rect = pygame.Rect(0, 0, sheet.get_width() // columns,
                                sheet.get_height() // rows)
        for j in range(rows):
            for i in range(columns):
                frame_location = (self.rect.w * i, self.rect.h * j)
                self.frames.append(sheet.subsurface(pygame.Rect(
                    frame_location, self.rect.size)))

    def update(self):
        self.cur_frame = (self.cur_frame + 1) % len(self.frames)
       # self.image = transform.flip(self.frames[self.cur_frame], True, False)
        self.image = self.frames[self.cur_frame]


class Player:
    BIG_IMAGE: pygame.Surface
    CHAR = 'P'
    status = 'lock'
    side = -1  # Влево


class PlayerSword(Player):
    BIG_IMAGE = load_image('sword.png', -1)
    CHAR = 'S'
    Name = 'sword'
    status = 'unlock'

    def __init__(self):
        self.image = transform.scale(PlayerSword.BIG_IMAGE, (70, 70))
        self.hp = 100
        self.dmg = 20
        self.armor = 10
        self.attack_speed_per_second = 4.0


class PlayerAxe(Player):
    BIG_IMAGE = load_image('axe.png', -1)
    CHAR = 'A'
    Name = 'axe'

    def __init__(self):
        self.image = transform.scale(PlayerAxe.BIG_IMAGE, (70, 70))
        self.hp = 120
        self.dmg = 40
        self.armor = 25
        self.attack_speed_per_second = 2.0


class PlayerKope(Player):
    BIG_IMAGE = load_image('kope.png', -1)
    CHAR = 'K'
    Name = 'kope'

    def __init__(self):
        self.image = transform.scale(PlayerKope.BIG_IMAGE, (70, 70))
        self.hp = 90
        self.dmg = 50
        self.armor = 10
        self.attack_speed_per_second = 1.5


class Shop:
    IMAGE = load_image('shop.png', -1)
    CHAR = 'H'

    def __init__(self):
        self.additions_num = (1, 1, 1, 0.1)
        self.icons = (load_image('heart_icon.png', -1),
                      load_image('damage_icon.jpg', -1),
                      load_image('armor_icon.png', -1),
                      load_image('speed_icon.jpg', -1),
                      load_image('coins.png', -1))
        self.font = pygame.font.SysFont('serif', 25)
        self.coins = 100

    def buy(self, pos, player):
        if pos[0] in range(20, 290):
            for i in range(1, 7):
                if pos[1] in range(i * 90, 90 + i * 90):
                    if i == 1 and self.coins >= 50 and self.txt2 != ' BOUGHT':
                        self.txt2 = ' BOUGHT'
                        board.players['axe'].status = 'unlock'
                        cur.execute("UPDATE Knights SET status = ? where name = ?", ('unlock', 'axe'))
                        self.coins -= 50
                    elif i == 2 and int(self.coins) >= 50 and self.txt1 != ' BOUGHT':
                        self.txt1 = ' BOUGHT'
                        board.players['kope'].status = 'unlock'
                        cur.execute("UPDATE Knights SET status = ? where name = ?", ('unlock', 'kope'))
                        self.coins -= 50
                    elif i == 3 and self.coins >= 10:
                        player.hp += 1
                        cur.execute("UPDATE Knights SET hp = ? where name = ?", (player.hp, player.Name))
                        self.coins -= 10
                    elif i == 4 and self.coins >= 10:
                        player.dmg += 1
                        cur.execute("UPDATE Knights SET damage = ? where name = ?", (player.dmg, player.Name))
                        self.coins -= 10
                    elif i == 5 and self.coins >= 10:
                        player.armor += 1
                        cur.execute("UPDATE Knights SET armor = ? where name = ?", (player.armor, player.Name))
                        self.coins -= 10
                    elif i == 6 and self.coins >= 10:
                        player.attack_speed_per_second = round(player.attack_speed_per_second + 0.1, 1)
                        cur.execute("UPDATE Knights SET attack_speed = ? where name = ?",
                                    (player.attack_speed_per_second, player.Name))
                        self.coins -= 10
                    cur.execute("UPDATE Knights SET coins = ? where name in (?, ?, ?)",
                                (self.coins, 'axe', 'kope', 'sword'))
                    con.commit()

    @staticmethod
    def draw_shop_title(screen):
        font = pygame.font.SysFont('serif', 37)
        text = font.render('SHOP', True, (0, 0, 0))
        screen.blit(text, (335, 12))

    def draw_icon(self, screen, img, img_size, img_pos, txt, txt_pos):
        screen.blit(transform.scale(img, img_size), img_pos)
        text = self.font.render(txt, True, (0, 0, 0))
        screen.blit(text, txt_pos)

    def draw(self, screen, player):
        screen.fill('#FFCC66')
        draw.rect(screen, 'red', (20, 90, 270, 540), 3)
        for i in range(1, 7):
            draw.line(screen, 'red', (20, i * 90), (290, i * 90), 3)
        self.draw_content(player)

    @staticmethod
    def highlight(screen, mouse_pos):
        if mouse_pos[0] in range(20, 290):
            for i in range(1, 7):
                if mouse_pos[1] in range(i * 90, 90 + i * 90):
                    draw.rect(screen, 'yellow', (20, i * 90, 270, 90))
                    break
                else:
                    shop.draw(screen, board.current_player)
        else:
            shop.draw(screen, board.current_player)

    def draw_content(self, player):

        ent = (player.Name, '')
        hp = list(cur.execute("SELECT hp from Knights where name in (?, ?)", ent))
        dmg = list(cur.execute("SELECT damage from Knights where name in (?, ?)", ent))
        armor = list(cur.execute("SELECT armor from Knights where name in (?, ?)", ent))
        attack_speed = list(cur.execute("SELECT attack_speed from Knights where name in (?, ?)", ent))
        coins = list(cur.execute("SELECT coins from Knights where name in (?, ?)", ent))
        status = list(cur.execute("SELECT status from Knights where name in (?, ?)", ('kope', 'axe')))

        player.hp, player.dmg, player.armor, player.attack_speed_per_second, self.coins, st1, st2 = \
        float(*hp[0]), int(*dmg[0]), float(*armor[0]), float(*attack_speed[0]), int(*coins[0]), *status[0], *status[1]

        if st2 == 'lock':
            self.txt1, board.players['axe'].status = '    50 coins', 'unlock'
        elif st2 == 'unlock':
            self.txt1, board.players['axe'].status = ' BOUGHT', 'lock'
        if st1 == 'lock':
            self.txt2, board.players['kope'].status = '    50 coins', 'unlock'
        elif st1 == 'unlock':
            self.txt2, board.players['kope'].status = ' BOUGHT', 'lock'

        icon_size = (60, 60)
        player_img_size = (70, 70)
        player_specifications_strings = (f'HP   {player.hp}',
                                         f'DAMAGE   {player.dmg}',
                                         f'ARMOR  {player.armor}',
                                         f'ATTACK SPEED  {player.attack_speed_per_second}',
                                         f'COINS  {self.coins}')
        self.draw_icon(screen, PlayerAxe.BIG_IMAGE, player_img_size,
                       (30, 100), self.txt1, (110, 210))
        self.draw_icon(screen, PlayerKope.BIG_IMAGE, player_img_size,
                       (30, 190), self.txt2, (110, 120))

        for i in range(len(self.additions_num)):
            self.draw_icon(screen, self.icons[i], icon_size, (30, 285 + i * 90),
                           f'+ {str(self.additions_num[i]).ljust(5)} 10 coins', (110, 300 + i * 90))
            self.draw_icon(screen, self.icons[i], icon_size, (430, 285 + i * 90),
                           player_specifications_strings[i], (510, 300 + i * 90))
        self.draw_icon(screen, self.icons[4], icon_size, (430, 665),
                       player_specifications_strings[4], (510, 660))
        screen.blit(transform.scale(player.BIG_IMAGE, (200, 200)), (430, 70))
        self.draw_shop_title(screen)


class Board:
    WALL_IMAGE = load_image('box.jpg')
    FLOOR_IMAGE = load_image('floor0.jpg')
    DOOR1_IMAGE = load_image('door.png')
    DOOR2_IMAGE = load_image('door2.png')
    knight = AnimatedSprite(load_image("sword_walk.jpg", -1), 6, 1, 50, 50)

    def __init__(self):
        self.current_level = self.load_level('map.txt')
        self.players = {'sword': sword, 'kope': kope, 'axe': axe}
        self.current_player = self.players['sword']

    def show_start_screen(self):
        intro_text = ["           Dungeon Knight"]
        fon = transform.scale(load_image('fon.jpg'), (width, height))
        screen.blit(fon, (0, 0))
        font = pygame.font.Font('data/ebrima.ttf', 60)
        text_coord = 50
        for line in intro_text:
            string_rendered = font.render(line, True, pygame.Color('orange'))
            intro_rect = string_rendered.get_rect()
            text_coord += 10
            intro_rect.top = text_coord
            intro_rect.x = 10
            text_coord += intro_rect.height
            screen.blit(string_rendered, intro_rect)

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate()
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    running = False
            pygame.display.flip()
        self.mainloop()

    @staticmethod
    def load_level(filename: str):
        return Level(filename)

    def draw_level(self):
        field = self.current_level.get_field()
        for y in range(len(field)):
            for x in range(len(field[y])):
                char = field[y][x]
                if char == '0':
                    self.draw_image('floor', x, y)
                elif char == '1':
                    self.draw_image('wall', x, y)
                elif char == PlayerSword.CHAR:
                    self.draw_image('floor', x, y)
                    self.draw_image('sword', x, y)
                elif char == 'K':
                    self.draw_image('floor', x, y)
                    self.draw_image('kope', x, y)
                elif char == PlayerAxe.CHAR:
                    self.draw_image('floor', x, y)
                    self.draw_image('axe', x, y)
                elif char == '2':
                    self.draw_image('door', x, y)
                elif char == '3':
                    self.draw_image('door2', x, y)
                elif char == Shop.CHAR:
                    self.draw_image('floor', x, y)
                    self.draw_image('shop', x, y)

    def draw_image(self, obj: str, x: int, y: int):
        img: pygame.Surface
        size = (70, 70)
        if obj == 'player_sword':
            img = transform.scale(sword.BIG_IMAGE, size)
        elif obj == 'player_kope':
            img = transform.scale(kope.BIG_IMAGE, size)
        elif obj == 'player_axe':
            img = transform.scale(axe.BIG_IMAGE, size)
        elif obj == 'wall':
            img = transform.scale(Board.WALL_IMAGE, size)
        elif obj == 'floor':
            img = transform.scale(Board.FLOOR_IMAGE, size)
        elif obj == 'door':
            img = transform.scale(Board.DOOR1_IMAGE, size)
        elif obj == 'door2':
            img = transform.scale(Board.DOOR2_IMAGE, size)
        elif obj == 'shop':
            img = transform.scale(Shop.IMAGE, size)
        else:
            img = transform.scale(self.players[obj].image, size)
        screen.blit(img, (x * size[0], y * size[1]))

    def get_player(self, char: str):
        for x in self.players.values():
            if x.CHAR == char:
                return x

    def mainloop(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.current_level.move_player('left', self.current_player)
                        if self.current_player.side == 1:
                            self.current_player.image = transform.flip(self.current_player.image, True, False)
                            self.current_player.side = -1
                    if event.key == pygame.K_RIGHT:
                        self.current_level.move_player('right', self.current_player)
                        if self.current_player.side == -1:
                            self.current_player.image = transform.flip(self.current_player.image, True, False)
                            self.current_player.side = 1
                    if event.key == pygame.K_UP:
                        self.current_level.move_player('up', self.current_player)
                    if event.key == pygame.K_DOWN:
                        self.current_level.move_player('down', self.current_player)
                    if event.key == pygame.K_e:
                        self.current_level.action(self.current_player)
            self.draw_level()
            pygame.display.flip()


class Level:
    def __init__(self, name: str):
        with open('data/' + name) as mapFile:
            level_map = [line.strip() for line in mapFile]
        max_width = max(map(len, level_map))
        self.field = list(map(lambda x: x.ljust(max_width, '.'), level_map))

    def get_field(self):
        return self.field

    def get_coords(self, elem: str):
        for y, s in enumerate(self.field):
            for x, e in enumerate(s):
                if self.field[y][x] == elem:
                    return x, y

    def move_player(self, direction: str, player: Player):
        char = player.CHAR
        x, y = self.get_coords(char)

        if direction == 'up':
            if self.field[y - 1][x] == '0':
                self.field[y] = list(self.field[y])
                self.field[y - 1] = list(self.field[y - 1])
                self.field[y - 1][x] = char
                self.field[y][x] = '0'
                self.field[y] = ''.join(self.field[y])
                self.field[y - 1] = ''.join(self.field[y - 1])
        elif direction == 'down':
            if self.field[y + 1][x] == '0':
                self.field[y] = list(self.field[y])
                self.field[y + 1] = list(self.field[y + 1])
                self.field[y + 1][x] = char
                self.field[y][x] = '0'
                self.field[y] = ''.join(self.field[y])
                self.field[y + 1] = ''.join(self.field[y + 1])
        elif direction == 'right':
            if self.field[y][x + 1] == '0':
                s = list(self.field[y])
                s[x + 1], s[x] = char, '0'
                self.field[y] = ''.join(s)
        elif direction == 'left':
            if self.field[y][x - 1] == '0':
                s = list(self.field[y])
                s[x - 1], s[x] = char, '0'
                self.field[y] = ''.join(s)

    def action(self, player: Player):
        char = player.CHAR
        side = player.side
        x, y = self.get_coords(char)
        if self.field[y][x + side] == 'H':
            self.open_shop(player)
        elif board.get_player(self.field[y][x + side]):  # Если соседнее поле занял игрок
            self.change_player(player)

    def change_player(self, current_player):
        status = list(cur.execute("SELECT status from Knights where name in (?, ?)", ('kope', 'axe')))
        st1, st2 = *status[0], *status[1]
        side = current_player.side
        x, y = self.get_coords(current_player.CHAR)
        player2 = board.get_player(self.field[y][x + side])
        if player2.Name == 'kope':
            if st1 == 'unlock':
                self.field[y] = list(self.field[y])
                self.field[y][x], self.field[y][x + side] = self.field[y][x + side], self.field[y][x]
                self.field[y] = ''.join(self.field[y])
                board.current_player = player2
        elif player2.Name == 'axe':
            if st2 == 'unlock':
                self.field[y] = list(self.field[y])
                self.field[y][x], self.field[y][x + side] = self.field[y][x + side], self.field[y][x]
                self.field[y] = ''.join(self.field[y])
                board.current_player = player2
        elif player2.Name == 'sword':
            self.field[y] = list(self.field[y])
            self.field[y][x], self.field[y][x + side] = self.field[y][x + side], self.field[y][x]
            self.field[y] = ''.join(self.field[y])
            board.current_player = player2


    @staticmethod
    def open_shop(player: Player):
        running = True
        while running:
            screen.fill('black')
            shop.draw(screen, player)
            for event in pygame.event.get():
                event_type = event.type
                if event_type == pygame.QUIT:
                    terminate()
                if event_type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                if event_type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    shop.buy(pos, board.current_player)
                    screen.fill('black')
                    shop.draw(screen, player)
                if event_type == pygame.MOUSEMOTION:
                    pos = event.pos
                    shop.highlight(screen, pos)
                    shop.draw_content(player)

                pygame.display.flip()


sword = PlayerSword()
axe = PlayerAxe()
kope = PlayerKope()
board = Board()
shop = Shop()
board.show_start_screen()