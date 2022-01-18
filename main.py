import numpy as np
import os
import pygame
import sqlite3
import sys
import time
from pygame import draw, transform

width, height = 840, 770
pygame.init()
screen = pygame.display.set_mode((width, height), pygame.NOFRAME)
screen.fill('black')

con = sqlite3.connect("data/dungeon_knight.db")
cur = con.cursor()


def update_screen():
    screen.fill('black')
    board.draw_level(board.current_level)
    all_sprites.draw(screen)
    pygame.display.flip()


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
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


class Player(pygame.sprite.Sprite):
    BIG_IMAGE: pygame.Surface
    CHAR: str
    NAME: str
    unlocked = False

    def __init__(self):
        super().__init__()
        self.hp = 1
        self.dmg = 1
        self.armor = 1
        self.attack_speed_per_second = 1
        self.side = [1, 0]  # Вправо

        # 1 - игрок может атаковать поле, 0 - не может
        # Игрок находится в центре, смотрит вправо
        self.attacked_zone = np.array(((0, 0, 0),
                                       (0, 0, 0),
                                       (0, 0, 0)), dtype=bool)

        self.last_attack_time = time.time()
        frames_num = len(os.listdir(os.path.join('data', self.NAME))) // 3
        self.frames_x = tuple(transform.scale(load_image(os.path.join(self.NAME, f'{i}.png')), Board.CELL_SIZE)
                              for i in range(frames_num))

        # Если число в названии изображения - положительное, персонаж смотрит в экран, от экрана если отрицательное
        # Название изображения начинается с "1" или "-1"
        frames_y = [[], []]
        for i in range(frames_num):
            frames_y[0].append(transform.scale(load_image(os.path.join(self.NAME, f'{10 + i}.png')), Board.CELL_SIZE))
            frames_y[1].append(transform.scale(load_image(os.path.join(self.NAME, f'{-10 - i}.png')), Board.CELL_SIZE))
        self.frames_y = tuple(tuple(x) for x in frames_y)
        self.current_frames = self.frames_x
        self.image = self.current_frames[0]
        self.rect = pygame.rect.Rect((0, 0, 70, 70))

    def get_coords(self) -> (int, int):
        return self.rect.x // Board.CELL_SIZE[0], self.rect.y // Board.CELL_SIZE[1]

    def set_coords(self, x: int, y: int):
        self.rect.x = x * Board.CELL_SIZE[0]
        self.rect.y = y * Board.CELL_SIZE[1]

    def set_side(self, side_x: int, side_y: int):
        if side_y:
            self.side[0] = 0
            self.current_frames = self.frames_y[0 if side_y == 1 else 1]
            self.image = self.current_frames[0]
        elif side_x:
            self.side[0] = side_x
            self.current_frames = self.frames_x
            self.image = self.current_frames[0] if self.side[0] == 1 else transform.flip(
                self.current_frames[0], True, False)
        self.side[1] = side_y
        #update_screen()

    # Двигает персонажа на заданное число клеток, при необходимости меняя изображение
    def move(self, x: int, y: int):
        self.rect.move_ip(x * Board.CELL_SIZE[0], y * Board.CELL_SIZE[1])
        self.set_side(x, y)

    def attack(self):
        # Ограничивает скорость атаки игрока
        if self.last_attack_time + 1 / self.attack_speed_per_second > time.time():
            return

        clock = pygame.time.Clock()
        for i in range(len(self.frames_x)):
            if self.side[1] == 0:
                self.image = transform.flip(
                    self.current_frames[i], True, False) if self.side[0] == -1 else self.current_frames[i]
            else:
                self.image = self.current_frames[i]
            update_screen()
            clock.tick(10)
        self.image = (transform.flip(self.current_frames[0], True, False) if self.side[0] == -1
                      else self.current_frames[0]) if self.side[1] == 0 else self.current_frames[0]
        self.last_attack_time = time.time()
        self.show_attacked_cells()

    def show_attacked_cells(self):
        p_coords = board.current_level.get_coords(self.CHAR)

        # Поворачивает массив атакуемых клеток в зависсимости от направления игрока
        rotation_num = 0
        if self.side[1] == -1:
            rotation_num = 1
        elif self.side[1] == 1:
            rotation_num = 3
        elif self.side[0] == -1:
            rotation_num = 2

        for x in np.transpose(np.nonzero(np.rot90(self.attacked_zone, k=rotation_num))):
            a_x, a_y = p_coords[0] + x[1] - 1, p_coords[1] + x[0] - 1
            if board.current_level.get_cell(a_x, a_y) == '0':
                r = pygame.Surface(Board.CELL_SIZE)
                r.set_alpha(35)
                r.fill('red')
                screen.blit(r, (a_x * Board.CELL_SIZE[0], a_y * Board.CELL_SIZE[1],
                                *Board.CELL_SIZE))
        pygame.display.flip()
        clock = pygame.time.Clock()
        clock.tick(7)


class PlayerSword(Player):
    BIG_IMAGE = load_image('sword/0.png')
    CHAR = 'S'
    NAME = 'sword'
    unlocked = True

    def __init__(self):
        super().__init__()
        self.hp = 100
        self.dmg = 20
        self.armor = 10
        self.attack_speed_per_second = 4.0
        self.attacked_zone = np.array(((0, 0, 1),
                                       (0, 0, 1),
                                       (0, 0, 1)), dtype=bool)


class PlayerAxe(Player):
    BIG_IMAGE = load_image('axe/0.png')
    CHAR = 'A'
    NAME = 'axe'

    def __init__(self):
        super().__init__()
        self.hp = 120
        self.dmg = 55
        self.armor = 25
        self.attack_speed_per_second = 2.0
        self.attacked_zone = np.array(((0, 0, 1),
                                       (0, 0, 1),
                                       (0, 0, 0)), dtype=bool)


class PlayerKope(Player):
    BIG_IMAGE = load_image('kope/0.png')
    CHAR = 'K'
    NAME = 'kope'

    def __init__(self):
        super().__init__()
        self.hp = 90
        self.dmg = 80
        self.armor = 10
        self.attack_speed_per_second = 1.5
        self.attacked_zone = np.array(((0, 0, 0),
                                       (0, 0, 1),
                                       (0, 0, 0)), dtype=bool)


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
        self.coins = cur.execute("SELECT coins from Player").fetchone()[0]
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
    def draw_shop_title():
        font = pygame.font.SysFont('serif', 37)
        text = font.render('SHOP', True, (0, 0, 0))
        screen.blit(text, (335, 12))

    def draw_icon(self, img, img_size, img_pos, txt, txt_pos):
        screen.blit(transform.scale(img, img_size), img_pos)
        text = self.font.render(txt, True, (0, 0, 0))
        screen.blit(text, txt_pos)

    def draw(self, player: Player):
        screen.fill('#FF9900')
        draw.rect(screen, 'red', (20, 90, 270, 540), 3)
        for i in range(1, 7):
            draw.line(screen, 'red', (20, i * 90), (290, i * 90), 3)
        self.draw_content(player)

    @staticmethod
    def highlight(mouse_pos: (int, int)):
        if mouse_pos[0] in range(20, 290):
            for i in range(1, 7):
                if mouse_pos[1] in range(i * 90, 90 + i * 90):
                    draw.rect(screen, '#FFFF33', (20, i * 90, 270, 90))
                    break
                else:
                    shop.draw(board.current_player)
        else:
            shop.draw(board.current_player)

    def draw_content(self, player: Player):
        self.kope_status = ' BOUGHT' if board.players['kope'].unlocked else '    50 coins'
        self.axe_status = ' BOUGHT' if board.players['axe'].unlocked else '    50 coins'

        icon_size = (60, 60)
        player_img_size = (70, 70)
        player_specifications_strings = (f'HP   {player.hp}',
                                         f'DAMAGE   {player.dmg}',
                                         f'ARMOR  {player.armor}',
                                         f'ATTACK SPEED  {player.attack_speed_per_second}',
                                         f'COINS  {self.coins}')
        self.draw_icon(PlayerAxe.BIG_IMAGE, player_img_size,
                       (30, 100), self.kope_status, (110, 210))
        self.draw_icon(PlayerKope.BIG_IMAGE, player_img_size,
                       (30, 190), self.axe_status, (110, 120))

        for i in range(len(self.additions_num)):
            self.draw_icon(self.icons[i], icon_size, (30, 285 + i * 90),
                           f'+ {str(self.additions_num[i]).ljust(5)} 10 coins', (110, 300 + i * 90))
            self.draw_icon(self.icons[i], icon_size, (430, 285 + i * 90),
                           player_specifications_strings[i], (510, 300 + i * 90))
        self.draw_icon(self.icons[4], icon_size, (430, 640),
                       player_specifications_strings[4], (510, 660))
        screen.blit(transform.scale(player.BIG_IMAGE, (200, 200)), (430, 70))
        self.draw_shop_title()


class Board:
    CELL_SIZE = (70, 70)

    def __init__(self):
        self.levels = (Level(0), Level(1))
        self.current_level = self.levels[0]
        self.players = {'sword': sword, 'axe': axe, 'kope': kope}
        self.current_player = self.players['sword']

        # Если текущий уровень - начальный
        if self.current_level == self.levels[0]:
            current_player = self.players[cur.execute("SELECT current_player from Player").fetchone()[0]]
            self.current_level.swap_players(self.current_player, current_player)
            self.current_player = current_player

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

    def draw_level(self, level: Level):
        field = self.current_level.get_field()
        for y in range(len(field)):
            for x in range(len(field[y])):
                char = field[y][x]
                images = []
                if char == '0':
                    images.append('floor')
                elif char == '1':
                    images.append('wall')
                elif char == PlayerSword.CHAR:
                    images.append('floor')
                    images.append('sword')
                elif char == PlayerKope.CHAR:
                    images.append('floor')
                    images.append('kope')
                elif char == PlayerAxe.CHAR:
                    images.append('floor')
                    images.append('axe')
                elif char == 'P':
                    images.append('floor')
                    images.append(board.current_player.NAME)
                    self.current_level.get_field()[y][x] = self.current_player.CHAR
                elif char == '2':
                    images.append('door')
                elif char == '3':
                    images.append('door2')
                elif char == Shop.CHAR:
                    images.append('floor')
                    images.append('shop')
                for im in images:
                    self.draw_image(im, x, y, level)

    def change_level(self, next_level, signal):
        x, y = 0, 0
        if signal == 1:
            y, x = 5, 1
        elif signal == 2:
            y, x = 6, 1
        elif signal == 3:
            y, x = 5, 10
        elif signal == 4:
            y, x = 6, 10

        self.current_level.field[y][x] = '0'
        self.draw_level(next_level)
        self.current_level = next_level

    def draw_image(self, obj: str, x: int, y: int, level: Level):
        img: pygame.Surface
        size = Board.CELL_SIZE
        if obj == 'wall':
            img = transform.scale(level.wall_image, size)
        elif obj == 'floor':
            img = transform.scale(level.floor_image, size)
        elif obj == 'door':
            img = transform.scale(level.door1_image, size)
        elif obj == 'door2':
            img = transform.scale(level.door2_image, size)
        elif obj == 'shop':
            img = transform.scale(level.shop_image, size)
        else:
            self.players[obj].set_coords(x, y)
            return
        screen.blit(img, (x * size[0], y * size[1]))

    def get_player_from_char(self, char: str) -> Player:
        for player in self.players.values():
            if player.CHAR == char:
                return player

    def mainloop(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        terminate()
                    dir_x, dir_y = 0, 0
                    ctrl_pressed = pygame.key.get_mods() & pygame.KMOD_CTRL
                    if event.key == pygame.K_LEFT:
                        dir_x -= 1
                    if event.key == pygame.K_RIGHT:
                        dir_x += 1
                    if event.key == pygame.K_UP:
                        dir_y -= 1
                    if event.key == pygame.K_DOWN:
                        dir_y += 1
                    if ctrl_pressed:
                        self.current_player.set_side(dir_x, dir_y)
                    else:
                        self.current_level.move_player(dir_x, dir_y, self.current_player)
                    if event.key == pygame.K_e:
                        self.current_level.action(self.current_player)
            update_screen()


class Level:
    def __init__(self, num: int, wall_image=load_image('box.jpg'), floor_image=load_image('floor0.jpg')):
        self.wall_image = wall_image
        self.floor_image = floor_image
        self.door1_image = load_image('door.png')
        self.door2_image = load_image('door2.png')
        self.shop_image = load_image('shop.png', colorkey=-1)
        with open('data/levels/' + f'{num}.txt') as mapFile:
            level_map = [line.strip() for line in mapFile]
        max_width = max(map(len, level_map))
        self.field = list(map(lambda x: list(x.ljust(max_width, '.')), level_map))

    def get_field(self):
        return self.field

    def get_coords(self, elem: str) -> (int, int):
        for y, s in enumerate(self.field):
            for x, e in enumerate(s):
                if self.field[y][x] == elem:
                    return x, y

    def get_cell(self, x: int, y: int) -> str:
        return self.field[y][x]

    def move_player(self, dir_x: int, dir_y: int, player: Player):
        char = player.CHAR
        x, y = player.get_coords()
        if dir_y:
            if self.field[y + dir_y][x] == '0':
                self.field[y][x], self.field[y + dir_y][x] = '0', char
                player.move(0, dir_y)
            else:
                player.set_side(1, dir_y)
        elif dir_x:
            if self.field[y][x + dir_x] == '0':
                s = self.field[y]
                s[x + dir_x], s[x] = char, '0'
                player.move(dir_x, 0)
            else:
                player.set_side(dir_x, 0)

    def action(self, player: Player):
        side_x, side_y = player.side
        x, y = self.get_coords(player.CHAR)
        target = self.field[y + side_y][x + side_x]
        if target == Shop.CHAR:
            self.open_shop(player)
        elif board.get_player_from_char(target):  # Если соседнее поле занял игрок
            self.change_player(player)
        elif target in '23':  # Дверь
            current_level_num = board.levels.index(board.current_level)
            if current_level_num == 0:
                for i in all_sprites:
                    i.kill()
                all_sprites.add(player)
                board.change_level(board.levels[1], int(target) - 1)
            elif current_level_num == 1:
                for i in all_sprites:
                    i.kill()
                all_sprites.add(sword, axe, kope)
                if side_x == -1:  # Дверь слева
                    board.change_level(board.levels[0], int(target) + 1)
                elif side_x == 1:  # Дверь справа
                    board.change_level(board.levels[0], int(target) + 1)
        else:
            player.attack()

    def change_player(self, current_player: Player):
        side_x, side_y = current_player.side
        x, y = self.get_coords(current_player.CHAR)
        player2 = board.get_player_from_char(self.field[y + side_y][x + side_x])
        if player2.unlocked:
            self.swap_players(current_player, player2)
            board.current_player = player2

    def swap_players(self, current_player: Player, player2: Player):
        x1, y1 = self.get_coords(current_player.CHAR)
        x2, y2 = self.get_coords(player2.CHAR)
        self.field[y1][x1], self.field[y2][x2] = self.field[y2][x2], self.field[y1][x1]
        current_player.set_side(1, 0)

    @staticmethod
    def open_shop(player: Player):
        running = True
        while running:
            screen.fill('black')
            shop.draw(player)
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
                    shop.draw(player)
                if event_type == pygame.MOUSEMOTION:
                    pos = event.pos
                    shop.highlight(pos)
                    shop.draw_content(player)
                pygame.display.flip()


sword, axe, kope = PlayerSword(), PlayerAxe(), PlayerKope()
all_sprites = pygame.sprite.Group()
all_sprites.add(sword, axe, kope)
board = Board()
shop = Shop()
board.show_start_screen()
