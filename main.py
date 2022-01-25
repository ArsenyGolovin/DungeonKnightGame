import os
import random
import sqlite3
import sys
import time

import numpy as np
import pygame
from pygame import draw, transform

width, height = 840, 770
pygame.init()
screen = pygame.display.set_mode((width, height), pygame.NOFRAME)
screen.fill('black')

fon_sound = pygame.mixer.Sound("data/fon_sound.mp3")
attack_sound = pygame.mixer.Sound("data/sword_sound.mp3")
coin_sound = pygame.mixer.Sound("data/coin_sound.mp3")
won_sound = pygame.mixer.Sound("data/won_sound.mp3")

fon_sound.set_volume(0.3)
coin_sound.set_volume(1.0)
attack_sound.set_volume(1.0)
won_sound.set_volume(1.0)

con = sqlite3.connect("data/dungeon_knight.db")
cur = con.cursor()


def update_screen():
    screen.fill('black')
    board.draw_level()
    all_sprites.draw(screen)
    draw_hp_icon()
    draw_coin_icon()
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
                    (p.max_hp, p.dmg, p.armor, p.attack_speed_per_second, p.unlocked, x))
    cur.execute("UPDATE Player SET coins=?, current_player=?", (shop.coins, board.current_player.NAME))
    con.commit()
    pygame.quit()
    sys.exit()


def draw_hp_icon():
    draw.rect(screen, 'black', (702, 3, 136, 64), 3)
    draw.rect(screen, 'white', (705, 6, 130, 58))
    img = load_image('hp_icon.png', -1)
    font = pygame.font.SysFont('serif', 37)
    text = font.render(f'{board.current_player.current_hp}', True, (0, 0, 0))
    screen.blit(transform.scale(img, (55, 55)), (705, 8))
    screen.blit(text, (765, 15))


def draw_coin_icon():
    draw.rect(screen, 'black', (566, 3, 136, 64), 3)
    draw.rect(screen, 'white', (569, 6, 130, 58))
    img = load_image('coin_icon.png', -1)
    font = pygame.font.SysFont('serif', 37)
    text = font.render(f'{shop.coins}', True, (0, 0, 0))
    screen.blit(transform.scale(img, (55, 55)), (569, 8))
    screen.blit(text, (640, 15))


class Entity(pygame.sprite.Sprite):
    BIG_IMAGE = pygame.Surface((0, 0))
    CHAR = ''
    NAME = ''
    ATTACK_COLOR = ''
    ATTACKED_CHARS = ''  # Клетки, которые подсвечиваются и получают урон при атаке

    def __init__(self, side=[1, 0]):
        super().__init__()
        self.max_hp = 1
        self.current_hp = 1
        self.dmg = 1
        self.armor = 1
        self.attack_speed_per_second = 1
        self.side = side

        # 1 - игрок может атаковать поле, 0 - не может
        # Игрок находится в центре, смотрит вправо
        self.attacked_zone = np.array(((0, 0, 0),
                                       (0, 0, 0),
                                       (0, 0, 0)), dtype=bool)

        self.last_attack_time = time.time()
        frames_num = len(os.listdir(os.path.join('data', self.NAME))) // 3
        self.frames_x = tuple(transform.scale(load_image(f'{self.NAME}/{i}.png'), Board.CELL_SIZE)
                              for i in range(frames_num))

        # Если число в названии изображения - положительное, персонаж смотрит в экран, от экрана если отрицательное
        # Название изображения начинается с "1" или "-1"
        frames_y = [[], []]
        for i in range(frames_num):
            frames_y[0].append(transform.scale(load_image(f'{self.NAME}/{10 + i}.png'), Board.CELL_SIZE))
            frames_y[1].append(transform.scale(load_image(f'{self.NAME}/{-10 - i}.png'), Board.CELL_SIZE))
        self.frames_y = (tuple(frames_y[0]), tuple(frames_y[1]))
        self.current_frames = self.frames_x
        self.image = transform.flip(self.current_frames[0],
                                    True, False) if self.side[0] == -1 else self.current_frames[0]
        self.rect = pygame.rect.Rect((0, 0, 70, 70))
        self.mask = pygame.mask.from_surface(self.image)

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

    # Двигает персонажа на заданное число клеток, при необходимости меняя изображение
    def move(self, x: int, y: int):
        self.rect.move_ip(x * Board.CELL_SIZE[0], y * Board.CELL_SIZE[1])
        self.set_side(x, y)

    def take_damage(self, dmg: int):
        if self.current_hp - dmg + (self.armor // 100 * dmg) > 0:
            self.current_hp -= dmg - (self.armor // 100 * dmg)
        else:
            self.die()

    def attack(self):
        # Ограничивает скорость атаки игрока
        if self.last_attack_time + 1 / self.attack_speed_per_second > time.time():
            return
        attack_sound.play()
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
        self.damage_and_show_attacked_cells()

    def transpose_attack_array(self, side=[0, 0]) -> np.array:
        # Поворачивает массив атакуемых клеток в зависсимости от направления существа
        if side == [0, 0]:
            side = self.side
        attacked_zone = self.attacked_zone
        if side[1] == -1:
            attacked_zone = np.rot90(attacked_zone, k=1)
        elif side[1] == 1:
            attacked_zone = np.rot90(attacked_zone, k=3)
        elif side[0] == -1:
            attacked_zone = attacked_zone[::, ::-1]
        return np.transpose(np.nonzero(attacked_zone))

    def damage_and_show_attacked_cells(self):
        p_coords = self.get_coords()
        if not p_coords:
            return
        for y, x in self.transpose_attack_array():
            a_x, a_y = p_coords[0] + x - 1, p_coords[1] + y - 1
            if board.current_level.get_cell(a_x, a_y) in self.ATTACKED_CHARS:
                r = pygame.Surface(Board.CELL_SIZE)
                r.set_alpha(35)
                r.fill(self.ATTACK_COLOR)
                screen.blit(r, (a_x * Board.CELL_SIZE[0], a_y * Board.CELL_SIZE[1],
                                *Board.CELL_SIZE))
                entity = board.current_level.get_entity(a_x, a_y)
                if entity:
                    entity.take_damage(self.dmg)
                if 'O' in self.ATTACKED_CHARS:
                    for g in board.current_level.ghosts:
                        if (a_x, a_y) == g.get_coords():
                            g.take_damage(self.dmg)
        pygame.display.flip()


class Goblin(Entity):
    BIG_IMAGE = load_image('goblin/0.png')
    CHAR = 'G'
    NAME = 'goblin'
    ATTACK_COLOR = 'green'
    STEP_DELAY = .35  # Время между шагaми
    ATTACKED_CHARS = '0SAK'

    def __init__(self, x=0, y=0):
        super().__init__(side=[-1, 0])
        self.max_hp = 115
        self.current_hp = 115
        self.dmg = 15
        self.armor = 5
        self.attack_speed_per_second = 4.0
        self.attacked_zone = np.array(((0, 0, 0),
                                       (0, 0, 1),
                                       (0, 0, 1)), dtype=bool)
        self.set_coords(x, y)
        self.last_step_time = time.time()
        self.coins = random.randint(1, 10)

    def get_next_step_coords(self) -> (int, int):
        # Поворачивает гоблина, если игрока можно атаковать
        c_x, c_y = self.get_coords()
        taa = self.transpose_attack_array
        for arr in (taa(side=[-1, 0]), taa(side=[1, 0]), taa(side=[0, -1]), taa(side=[0, 1])):
            for x, y in arr - 1:
                if board.current_level.field[y + c_y][x + c_x] == board.current_player.CHAR:
                    if x == 1 and y == 1:
                        self.set_side(1, 0)
                    else:
                        self.set_side(x, y)
                    return

        # Находит способ добраться до игрока и возвращает координаты для следующего шага
        level_field = [[0 if x == '0' else 1 for x in y][1:11] for y in board.current_level.field][1:10]
        new_field = [[0 for _ in range(1, 11)] for _ in range(1, 10)]
        start, finish = self.get_coords(), board.current_player.get_coords()
        new_field[start[1] - 1][start[0] - 1] = 1
        level_field[finish[1] - 1][finish[0] - 1] = 0
        n = 1
        while new_field[finish[1] - 1][finish[0] - 1] == 0:
            for y in range(len(new_field)):
                for x in range(len(new_field[y])):
                    if new_field[y][x] == n:
                        if y and new_field[y - 1][x] == level_field[y - 1][x] == 0:
                            new_field[y - 1][x] = n + 1
                        if x and new_field[y][x - 1] == level_field[y][x - 1] == 0:
                            new_field[y][x - 1] = n + 1
                        if y < len(new_field) - 1 and new_field[y + 1][x] == level_field[y + 1][x] == 0:
                            new_field[y + 1][x] = n + 1
                        if x < len(new_field[y]) - 1 and new_field[y][x + 1] == level_field[y][x + 1] == 0:
                            new_field[y][x + 1] = n + 1
            n += 1
            if n == 30:
                return False
        x, y = finish[0] - 1, finish[1] - 1,
        path = []
        while n > 1:
            if y > 0 and new_field[y - 1][x] == n - 1:
                y, x = y - 1, x
                path.append((y, x))
                n -= 1
            elif x > 0 and new_field[y][x - 1] == n - 1:
                y, x = y, x - 1
                path.append((y, x))
                n -= 1
            elif y < len(new_field) - 1 and new_field[y + 1][x] == n - 1:
                y, x = y + 1, x
                path.append((y, x))
                n -= 1
            elif x < len(new_field[y]) - 1 and new_field[y][x + 1] == n - 1:
                y, x = y, x + 1
                path.append((y, x))
                n -= 1
        return path[-2] if len(path) > 1 else None

    def step_to_player(self):
        if time.time() - self.last_step_time <= self.STEP_DELAY:
            return
        if path := self.get_next_step_coords():
            next_y, next_x = path
        elif path is False:
            return
        else:
            self.attack()
            return
        delta_x, delta_y = self.get_coords()[0] - next_x - 1, self.get_coords()[1] - next_y - 1
        board.current_level.move_entity(-delta_x, -delta_y, self)
        self.last_step_time = time.time()
        return

    def die(self):
        shop.coins += self.coins
        x, y = self.get_coords()
        board.current_level.field[y][x] = '0'
        self.kill()


class Ghost(Entity):
    NAME = 'ghost'
    ATTACKED_CHARS = '0SAK'

    def __init__(self, x, y):
        super().__init__()
        self.max_hp = 35
        self.current_hp = 35
        self.dmg = 1
        self.coins = random.randint(25, 40)
        self.side = [0, 0]
        x2, y2 = random.randint(1, 10), random.randint(1, 9)
        while x2 == x or y2 == y:
            x2, y2 = random.randint(1, 10), random.randint(1, 9)
        if x2 > x:
            self.side[0] = 1
        elif x2 < x:
            self.side[0] = -1
        if y2 > y:
            self.side[1] = 1
        elif y2 < y:
            self.side[1] = -1
        self.delta_x = abs(x2 - x) / abs(y2 - y)
        self.delta_y = abs(y2 - y) / abs(x2 - x)
        all_sprites.add(self)
        self.set_coords(x, y)

    def step(self):
        self.rect.move_ip(self.delta_x, self.delta_y)
        x, y = self.get_coords()
        if x not in range(0, 11) or y not in range(0, 10):
            self.kill()
            return
        if pygame.sprite.collide_mask(self, board.current_player):
            board.current_player.take_damage(self.dmg)

    def die(self):
        shop.coins += self.coins
        self.kill()


class Player(Entity):
    ATTACK_COLOR = 'red'
    ATTACKED_CHARS = '0G'
    unlocked = False

    def __init__(self, side=[1, 0]):
        super().__init__(side=side)

    def revive_hp(self):
        self.current_hp = self.max_hp

    def die(self):
        shop.coins //= 2
        board.init_levels()
        board.show_death_screen()
        all_sprites.add(axe, kope)
        self.revive_hp()


class PlayerSword(Player):
    BIG_IMAGE = load_image('sword/0.png')
    CHAR = 'S'
    NAME = 'sword'
    unlocked = True

    def __init__(self):
        super().__init__(side=[-1, 0])
        self.max_hp = 100
        self.current_hp = 100
        self.dmg = 20
        self.armor = 10
        self.attack_speed_per_second = 2
        self.attacked_zone = np.array(((0, 0, 1),
                                       (0, 0, 1),
                                       (0, 0, 1)), dtype=bool)


class PlayerAxe(Player):
    BIG_IMAGE = load_image('axe/0.png')
    CHAR = 'A'
    NAME = 'axe'

    def __init__(self):
        super().__init__()
        self.max_hp = 120
        self.current_hp = 120
        self.dmg = 55
        self.armor = 25
        self.attack_speed_per_second = 1.5
        self.attacked_zone = np.array(((0, 0, 1),
                                       (0, 0, 1),
                                       (0, 0, 0)), dtype=bool)


class PlayerKope(Player):
    BIG_IMAGE = load_image('kope/0.png')
    CHAR = 'K'
    NAME = 'kope'

    def __init__(self):
        super().__init__()
        self.max_hp = 90
        self.current_hp = 90
        self.dmg = 80
        self.armor = 10
        self.attack_speed_per_second = 1.0
        self.attacked_zone = np.array(((0, 0, 0),
                                       (0, 0, 1),
                                       (0, 0, 0)), dtype=bool)


class Shop:
    IMAGE = load_image('shop.png', -1)
    CHAR = 'H'

    def __init__(self):
        self.additions_num = (10, 1, 1, 0.1)
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
                        coin_sound.play(0)
                    elif i == 2 and self.coins >= 50 and not board.players['kope'].unlocked:
                        self.axe_status = ' BOUGHT'
                        board.players['kope'].unlocked = True
                        self.coins -= 50
                        coin_sound.play(0)
                    elif i == 3 and self.coins >= 10:
                        player.max_hp += 10
                        player.current_hp += 10
                        self.coins -= 10
                        coin_sound.play(0)
                    elif i == 4 and self.coins >= 10:
                        player.dmg += 1
                        self.coins -= 10
                        coin_sound.play(0)
                    elif i == 5 and self.coins >= 10:
                        player.armor += 1
                        self.coins -= 10
                        coin_sound.play(0)
                    elif i == 6 and self.coins >= 10:
                        player.attack_speed_per_second = round(player.attack_speed_per_second + 0.1, 1)
                        self.coins -= 10
                        coin_sound.play(0)
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
        player_specifications_strings = (f'MAXIMUM HP   {player.max_hp}',
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
        self.players = {'sword': sword, 'axe': axe, 'kope': kope}
        self.current_player = self.players['sword']
        self.init_levels()
        self.flag_sound = True

        # Если текущий уровень - начальный
        if self.current_level == self.levels[0]:
            current_player = self.players[cur.execute("SELECT current_player from Player").fetchone()[0]]
            self.current_level.swap_players(self.current_player, current_player)
            self.current_player = current_player

    def load_db_info(self):
        for x in cur.execute("SELECT name FROM Knights").fetchall():
            p: Player = self.players[x[0]]
            hp, dmg, armor, attack_speed_per_second, unlocked = cur.execute(
                f"SELECT hp, damage, armor, attack_speed, unlocked FROM Knights "
                f"WHERE name = '{x[0]}'").fetchone()
            p.current_hp, p.max_hp, p.dmg, p.armor, p.attack_speed_pes_second, p.unlocked = \
                int(hp), int(hp), int(dmg), int(armor), float(attack_speed_per_second), bool(unlocked)
        self.current_player = self.players[cur.execute("SELECT current_player FROM Player").fetchone()[0]]
        shop.coins = int(cur.execute("SELECT coins FROM Player").fetchone()[0])

    def init_levels(self):
        self.levels = (Level(0), Level(1), Level(2, floor_image='floor1.jpg', ghosts_num=2),
                       Level(3, floor_image='floor2.jpg', ghosts_num=2),
                       Level(4, floor_image='floor3.jpg', ghosts_num=3),
                       Level(5, floor_image='floor3.jpg', ghosts_num=4))
        self.current_level = self.levels[0]
        all_sprites.add(sword)
        self.current_level.swap_players(self.current_player, self.players['sword'])

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
        pygame.display.flip()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate()
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    running = False
        self.mainloop()

    def show_death_screen(self):
        self.load_db_info()
        screen.fill('black')
        font1 = pygame.font.Font('data/ebrima.ttf', 60)
        font2 = pygame.font.Font('data/ebrima.ttf', 35)
        death_text = font1.render("YOU DIED", True, pygame.Color('red'))
        death_text_rect = death_text.get_rect(center=(400, 320))
        press_space_text = font2.render("Press SPACE to continue", True, pygame.Color('red'))
        press_space_text_rect = press_space_text.get_rect(center=(400, 450))
        screen.blit(death_text, death_text_rect)
        screen.blit(press_space_text, press_space_text_rect)
        pygame.display.flip()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        return
                    elif event.key == pygame.K_ESCAPE:
                        terminate()

    def show_won_screen(self):
        self.load_db_info()
        screen.fill('black')
        fon = transform.scale(load_image('cong.jpg'), (width, height))
        screen.blit(fon, (0, 0))
        font2 = pygame.font.Font('data/ebrima.ttf', 70)
        won_text = font2.render("YOU WON!", True, pygame.Color('orange'))
        won_text_rect = won_text.get_rect(center=(400, 500))
        screen.blit(won_text, won_text_rect)
        coin_sound.set_volume(0.0)
        attack_sound.set_volume(0.0)
        fon_sound.set_volume(0.0)
        won_sound.play(0)
        pygame.display.flip()
        pygame.time.delay(6000)
        coin_sound.set_volume(1.0)
        attack_sound.set_volume(1.0)
        fon_sound.set_volume(0.4)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate()
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    return
                if event.key == pygame.K_ESCAPE:
                    terminate()

    def draw_level(self):
        field = self.current_level.get_field()
        for y in range(len(field)):
            for x in range(len(field[y])):
                char = field[y][x]
                images = []
                if char == '0':
                    images.append('floor')
                elif char == '1':
                    images.append('wall')
                elif char == Goblin.CHAR:
                    images.append('floor')
                    images.append('goblin')
                elif char == PlayerSword.CHAR:
                    images.append('floor')
                    images.append('sword')
                elif char == PlayerKope.CHAR:
                    images.append('floor')
                    images.append('kope')
                elif char == PlayerAxe.CHAR:
                    images.append('floor')
                    images.append('axe')
                elif char == '2':
                    images.append('door')
                elif char == '3':
                    images.append('door2')
                elif char == Shop.CHAR:
                    images.append('floor')
                    images.append('shop')
                for im in images:
                    self.draw_image(im, x, y)

    def change_level(self, next_level_num: int, door_num: int):
        # Место появления игрока на следующем уровне
        n_x, n_y = 0, 0
        if door_num == 1:
            n_y, n_x = 5, 1
        elif door_num == 2:
            n_y, n_x = 6, 1
        elif door_num == 3:
            n_y, n_x = 5, 10
        elif door_num == 4:
            n_y, n_x = 6, 10
        if next_level_num > 5:
            next_level_num = 0
        if next_level_num == 0:
            self.show_won_screen()
            board.current_player.revive_hp()
            all_sprites.add(sword, axe, kope)
        all_sprites.add(board.current_player)
        next_level = self.levels[next_level_num]
        p_x, p_y = self.current_player.get_coords()
        next_level.field[n_y][n_x] = board.current_player.CHAR
        self.current_level.field[p_y][p_x] = '0'
        self.current_level = next_level
        self.draw_level()

    def draw_image(self, obj: str, x: int, y: int):
        img: pygame.Surface
        size = Board.CELL_SIZE
        level = board.current_level
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
            if obj == Goblin.NAME:
                self.current_level.goblins.draw(screen)
                pass
            else:
                self.players[obj].set_coords(x, y)
                self.current_level.goblins.draw(screen)
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
                    if event.key == pygame.K_LEFT:
                        dir_x -= 1
                    if event.key == pygame.K_RIGHT:
                        dir_x += 1
                    if event.key == pygame.K_UP:
                        dir_y -= 1
                    if event.key == pygame.K_DOWN:
                        dir_y += 1
                    if event.key == pygame.K_q:
                        if self.flag_sound is True:
                            coin_sound.set_volume(0.0)
                            attack_sound.set_volume(0.0)
                            fon_sound.set_volume(0.0)
                            self.flag_sound = False
                        else:
                            fon_sound.set_volume(0.4)
                            coin_sound.set_volume(1.0)
                            attack_sound.set_volume(1.0)
                            self.flag_sound = True
                    ctrl_pressed = pygame.key.get_mods() & pygame.KMOD_CTRL
                    if ctrl_pressed:
                        shift_pressed = pygame.key.get_mods() & pygame.KMOD_SHIFT
                        alt_pressed = pygame.key.get_mods() & pygame.KMOD_ALT
                        if shift_pressed and event.key == pygame.K_c:
                            self.current_player.current_hp = 9999
                        elif ctrl_pressed and alt_pressed and shift_pressed:
                            cur.execute("UPDATE Knights SET hp=100,damage=20,armor=10,attack_speed=2,"
                                        "unlocked=1 WHERE name='sword'")
                            cur.execute("UPDATE Knights SET hp=120,damage=40,armor=25,attack_speed=1.5,"
                                        "unlocked=0 WHERE name='axe'")
                            cur.execute("UPDATE Knights SET hp=90,damage=50,armor=10,attack_speed=1,"
                                        "unlocked=0 WHERE name='kope'")
                            cur.execute("UPDATE Player SET current_player='sword',coins=100")
                            con.commit()
                            self.load_db_info()
                        else:
                            self.current_player.set_side(dir_x, dir_y)

                    else:
                        self.current_level.move_entity(dir_x, dir_y, self.current_player)
                    if event.key == pygame.K_e:
                        self.current_level.action(self.current_player)
            for g in self.current_level.goblins:
                g.step_to_player()
            self.current_level.spawn_ghost()
            for g in self.current_level.ghosts:
                g.step()
            update_screen()


class Level:
    GOBLIN_SPAWN_CHANCE = 20
    GHOST_SPAWN_CHANCE = 25

    def __init__(self, num: int, ghosts_num=0, wall_image='box.jpg', floor_image='floor0.jpg'):
        self.wall_image = load_image(wall_image)
        self.floor_image = load_image(floor_image)
        self.door1_image = load_image('door.png')
        self.door2_image = load_image('door2.png')
        self.shop_image = load_image('shop.png', colorkey=-1)
        level_map = [line.strip() for line in open(f'data/levels/{num}.txt')]
        max_width = max(map(len, level_map))
        self.field = list(map(lambda x: list(x.ljust(max_width, '.')), level_map))
        self.goblins = pygame.sprite.Group()
        self.ghosts = pygame.sprite.Group()
        for y in range(len(self.field)):
            for x in range(len(self.field)):
                if self.field[y][x] == Goblin.CHAR:
                    if len(self.goblins) < num or random.randint(0, 100) < self.GOBLIN_SPAWN_CHANCE:
                        goblin = Goblin(x, y)
                        self.goblins.add(goblin)
                    else:
                        self.field[y][x] = '0'
        self.ghosts_num = 0
        self.max_ghosts_num = ghosts_num

    def get_field(self):
        return self.field

    def get_entity(self, x, y):
        char = board.current_level.field[y][x]
        if char == 'G':
            goblin = [goblin for goblin in self.goblins if goblin.get_coords() == (x, y)]
            return goblin[0] if goblin else None
        elif char == board.current_player.CHAR:
            return board.current_player

    def get_coords(self, elem: str) -> (int, int):
        for y, s in enumerate(self.field):
            for x, e in enumerate(s):
                if self.field[y][x] == elem:
                    return x, y

    def get_cell(self, x: int, y: int) -> str:
        return self.field[y][x]

    def move_entity(self, dir_x: int, dir_y: int, entity: Entity):
        char = entity.CHAR
        x, y = entity.get_coords()
        if dir_y:
            if self.field[y + dir_y][x] == '0':
                self.field[y][x], self.field[y + dir_y][x] = '0', char
                entity.move(0, dir_y)
            else:
                entity.set_side(1, dir_y)
        elif dir_x:
            if self.field[y][x + dir_x] == '0':
                s = self.field[y]
                s[x + dir_x], s[x] = char, '0'
                entity.move(dir_x, 0)
            else:
                entity.set_side(dir_x, 0)

    def spawn_ghost(self):
        if random.randint(1, 10000) > 25 or self.ghosts_num == self.max_ghosts_num:
            return
        x, y = random.randint(1, 10), random.randint(1, 9)
        while self.field[y][x] == '0':
            x, y = random.randint(1, 10), random.randint(1, 9)
        self.ghosts.add(Ghost(x, y))
        self.ghosts_num += 1

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
            if side_x == 1 and not self.get_coords('G'):  # Дверь справа
                for i in all_sprites:
                    i.kill()
                board.change_level(current_level_num + 1, int(target) - 1)
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
        while True:
            screen.fill('black')
            shop.draw(player)
            for event in pygame.event.get():
                event_type = event.type
                if event_type == pygame.QUIT:
                    terminate()
                if event_type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                    if event.key == pygame.K_q:
                        if board.flag_sound is True:
                            coin_sound.set_volume(0.0)
                            attack_sound.set_volume(0.0)
                            fon_sound.set_volume(0.0)
                            board.flag_sound = False
                        else:
                            fon_sound.set_volume(0.4)
                            coin_sound.set_volume(1.0)
                            attack_sound.set_volume(1.0)
                            board.flag_sound = True

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
all_sprites = pygame.sprite.Group(sword, axe, kope)
clock = pygame.time.Clock()
board = Board()
fon_sound.play(-1)
shop = Shop()
board.show_start_screen()
