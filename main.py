import os
import sqlite3
import sys

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
        terminate()
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
    for x in board.players:
        p: Player = board.players[x]
        cur.execute("UPDATE Knights SET hp=?,damage=?,armor=?,attack_speed=?,unlocked=? WHERE name=?",
                    (p.hp, p.dmg, p.armor, p.attack_speed_per_second, p.unlocked, x))
    cur.execute("UPDATE Player SET coins=?, current_player=?", (shop.coins, board.current_player.NAME))
    con.commit()
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
    unlocked = False
    side = -1  # Влево
    hp, dmg, armor, attack_speed_per_second, CHAR = 0, 0, 0, 0, 'P'


class PlayerSword(Player):
    BIG_IMAGE = load_image('sword.png', -1)
    CHAR = 'S'
    NAME = 'sword'
    unlocked = True

    def __init__(self):
        self.image = transform.scale(PlayerSword.BIG_IMAGE, (70, 70))
        self.hp = 100
        self.dmg = 20
        self.armor = 10
        self.attack_speed_per_second = 4.0


class PlayerAxe(Player):
    BIG_IMAGE = load_image('axe.png', -1)
    CHAR = 'A'
    NAME = 'axe'

    def __init__(self):
        self.image = transform.scale(PlayerAxe.BIG_IMAGE, (70, 70))
        self.hp = 120
        self.dmg = 40
        self.armor = 25
        self.attack_speed_per_second = 2.0


class PlayerKope(Player):
    BIG_IMAGE = load_image('kope.png', -1)
    CHAR = 'K'
    NAME = 'kope'

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
        coins = cur.execute("SELECT coins from Player")
        for i in coins:
            self.coins = i[0]
        self.kope_status, self.axe_status = '  50 coins', '  50 coins'

    def buy(self, pos: (int, int), player: Player):
        if pos[0] in range(20, 290):
            for i in range(1, 7):
                if pos[1] in range(i * 90, 90 + i * 90):
                    if i == 1 and self.coins >= 50 and not board.players['axe'].unlocked:
                        self.kope_status = ' BOUGHT'
                        board.players['axe'].unlocked = True
                        self.coins -= 50
                    elif i == 2 and self.coins >= 50 and not board.players['kope'].unlocked:
                        self.axe_status = ' BOUGHT'
                        board.players['kope'].unlocked = True
                        self.coins -= 50
                    elif i == 3 and self.coins >= 10:
                        player.hp += 1
                        self.coins -= 10
                    elif i == 4 and self.coins >= 10:
                        player.dmg += 1
                        self.coins -= 10
                    elif i == 5 and self.coins >= 10:
                        player.armor += 1
                        self.coins -= 10
                    elif i == 6 and self.coins >= 10:
                        player.attack_speed_per_second = round(player.attack_speed_per_second + 0.1, 1)
                        self.coins -= 10
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
        self.kope_status = ' BOUGHT' if board.players['kope'].unlocked else '    50 coins'
        self.axe_status = ' BOUGHT' if board.players['axe'].unlocked else '    50 coins'

        icon_size = (60, 60)
        player_img_size = (70, 70)
        player_specifications_strings = (f'HP   {player.hp}',
                                         f'DAMAGE   {player.dmg}',
                                         f'ARMOR  {player.armor}',
                                         f'ATTACK SPEED  {player.attack_speed_per_second}',
                                         f'COINS  {self.coins}')
        self.draw_icon(screen, PlayerAxe.BIG_IMAGE, player_img_size,
                       (30, 100), self.kope_status, (110, 210))
        self.draw_icon(screen, PlayerKope.BIG_IMAGE, player_img_size,
                       (30, 190), self.axe_status, (110, 120))

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

    def __init__(self):
        self.current_level = self.load_level('map.txt')
        self.players = {'sword': PlayerSword(), 'kope': PlayerKope(), 'axe': PlayerAxe()}
        self.knight = AnimatedSprite(load_image("sword_walk.jpg", -1), 6, 1, 50, 50)

        player_db = cur.execute("SELECT current_player from Player")
        for i in player_db:
            self.current_player = self.players[i[0]]
            xa, ya = self.current_level.get_coords('A')
            xs, ys = self.current_level.get_coords('S')
            xk, yk = self.current_level.get_coords('K')
            if i[0] == 'axe':
                self.current_level.field[ya] = list(self.current_level.field[ya])
                self.current_level.field[ys] = list(self.current_level.field[ys])
                self.current_level.field[ya][xa], self.current_level.field[ys][xs] = \
                    self.current_level.field[ys][xs], self.current_level.field[ya][xa]
                self.current_level.field[ya] = ''.join(self.current_level.field[ya])
                self.current_level.field[ys] = ''.join(self.current_level.field[ys])
            elif i[0] == 'kope':
                self.current_level.field[yk] = list(self.current_level.field[yk])
                self.current_level.field[ys] = list(self.current_level.field[ys])
                self.current_level.field[yk][xk], self.current_level.field[ys][xs] = \
                    self.current_level.field[ys][xs], self.current_level.field[yk][xk]
                self.current_level.field[yk] = ''.join(self.current_level.field[yk])
                self.current_level.field[ys] = ''.join(self.current_level.field[ys])

    def load_db_info(self):
        for x in cur.execute("SELECT name FROM Knights").fetchall():
            p: Player = self.players[x[0]]
            hp, dmg, armor, attack_speed_per_second, unlocked = cur.execute(
                f"SELECT hp, damage, armor, attack_speed, unlocked FROM Knights WHERE name = '{x[0]}'").fetchone()
            p.hp, p.dmg, p.armor, p.attack_speed_pes_second, p.unlocked = \
                int(hp), int(dmg), int(armor), float(attack_speed_per_second), bool(unlocked)

    def show_start_screen(self):
        self.load_db_info()
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
            img = transform.scale(PlayerSword.BIG_IMAGE, size)
        elif obj == 'player_kope':
            img = transform.scale(PlayerKope.BIG_IMAGE, size)
        elif obj == 'player_axe':
            img = transform.scale(PlayerAxe.BIG_IMAGE, size)
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
                    terminate()
                if event.type == pygame.KEYDOWN:
                    dir_x, dir_y = 0, 0
                    if event.key == pygame.K_ESCAPE:
                        terminate()
                    if event.key == pygame.K_LEFT:
                        dir_x -= 1
                        if self.current_player.side == 1:
                            self.current_player.image = transform.flip(self.current_player.image, True, False)
                            self.current_player.side = -1
                    if event.key == pygame.K_RIGHT:
                        dir_x += 1
                        if self.current_player.side == -1:
                            self.current_player.image = transform.flip(self.current_player.image, True, False)
                            self.current_player.side = 1
                    if event.key == pygame.K_UP:
                        dir_y -= 1
                    if event.key == pygame.K_DOWN:
                        dir_y += 1
                    self.current_level.move_player(dir_x, dir_y, self.current_player)
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

    def get_coords(self, elem: str) -> (int, int):
        for y, s in enumerate(self.field):
            for x, e in enumerate(s):
                if self.field[y][x] == elem:
                    return x, y

    def move_player(self, dir_x: int, dir_y: int, player: Player):
        char = player.CHAR
        x, y = self.get_coords(char)

        if self.field[y + dir_y][x] == '0':
            s = list(self.field[y])
            s1 = list(self.field[y + dir_y])
            s1[x] = char
            s[x] = '0'
            self.field[y] = ''.join(s)
            self.field[y + dir_y] = ''.join(s1)
        if self.field[y][x + dir_x] == '0':
            s = list(self.field[y])
            s[x + dir_x], s[x] = char, '0'
            self.field[y] = ''.join(s)

    def action(self, player: Player):
        side = player.side
        x, y = self.get_coords(player.CHAR)
        target = self.field[y][x + side]
        shop_target = [self.field[y + 1][x], self.field[y][x - 1], self.field[y - 1][x],
                       self.field[y - 1][x - 1], self.field[y + 1][x + 1]]
        if shop.CHAR in shop_target:
            self.open_shop(player)
        elif board.get_player(target):  # Если соседнее поле занял игрок
            self.change_player(player)

    def change_player(self, current_player):
        side = current_player.side
        x, y = self.get_coords(current_player.CHAR)
        player2 = board.get_player(self.field[y][x + side])
        if player2.unlocked:
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


board = Board()
shop = Shop()
board.show_start_screen()
