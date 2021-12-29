import os
import sys

import pygame

width, height = 840, 770
pygame.init()
screen = pygame.display.set_mode((width, height), pygame.NOFRAME)
screen.fill('black')


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


class Player:
    CHAR = 'P'
    side = -1  # Влево


class PlayerSword(Player):
    CHAR = 'S'
    image = pygame.transform.scale(load_image('sword.png', -1), (70, 70))

    def __init__(self):
        self.hp = 100
        self.dmg = 20
        self.armor = 10
        self.attack_speed_per_second = 4


class PlayerAxe(Player):
    CHAR = 'A'
    image = pygame.transform.scale(load_image('axe.png', -1), (70, 70))

    def __init__(self):
        self.hp = 120
        self.dmg = 40
        self.armor = 25
        self.attack_speed_per_second = 2


class PlayerKope(Player):
    image = pygame.transform.scale(load_image('kope.png', -1), (70, 70))
    CHAR = 'K'

    def __init__(self):
        self.hp = 90
        self.dmg = 50
        self.armor = 10
        self.attack_speed_per_second = 1.5


class Shop:
    IMAGE = load_image('shop.png', -1)
    CHAR = 'H'

    def __init__(self):
        self.running = True
        self.coins = 0

    def draw(self, screen):
        screen.fill('yellow')
        self.shop_icon(screen)
        self.axe_icon(screen)
        pygame.display.flip()

    def shop_icon(self, screen):
        font = pygame.font.SysFont('serif', 37)
        text = font.render('SHOP', True, 'black')
        screen.blit(text, (10, 2, text.get_width(), text.get_height()))

    def axe_icon(self, screen):
        screen.blit(PlayerAxe.image, (1, 10))
        font = pygame.font.SysFont('serif', 15)
        text = font.render(f'Axe(2)   {self.coins}/50 coins', True, 'black')
        screen.blit(text, (10, 10))


class Board:
    wall_image = load_image('box.jpg')
    floor_image = load_image('floor0.jpg')
    door_image = load_image('door.png')
    door2_image = load_image('door2.png')

    def __init__(self):
        self.players = {'sword': PlayerSword(), 'kope': PlayerKope(), 'axe': PlayerAxe()}
        self.current_player = self.players['sword']
        self.current_level = self.load_level('map.txt')

    def show_start_screen(self):
        intro_text = ["           Dungeon Knight"]
        fon = pygame.transform.scale(load_image('fon.jpg'), (width, height))
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
        screen.fill('black')
        self.mainloop()

    @staticmethod
    def load_level(filename):
        return Level(filename)

    def draw_level(self):
        field = self.current_level.get_field()
        for y in range(len(field)):
            for x in range(len(field[y])):
                if field[y][x] == '0':
                    self.draw_img('floor', x, y)
                elif field[y][x] == '1':
                    self.draw_img('wall', x, y)
                elif field[y][x] == PlayerSword.CHAR:
                    self.draw_img('floor', x, y)
                    self.draw_img('sword', x, y)
                elif field[y][x] == PlayerKope.CHAR:
                    self.draw_img('floor', x, y)
                    self.draw_img('kope', x, y)
                elif field[y][x] == PlayerAxe.CHAR:
                    self.draw_img('floor', x, y)
                    self.draw_img('axe', x, y)
                elif field[y][x] == '2':
                    self.draw_img('door', x, y)
                elif field[y][x] == '3':
                    self.draw_img('door2', x, y)
                elif field[y][x] == Shop.CHAR:
                    self.draw_img('floor', x, y)
                    self.draw_img('shop', x, y)

    def draw_img(self, obj, x, y):
        img: pygame.Surface
        size = (70, 70)
        if obj == 'wall':
            img = pygame.transform.scale(Board.wall_image, size)
        elif obj == 'floor':
            img = pygame.transform.scale(Board.floor_image, size)
        elif obj == 'door':
            img = pygame.transform.scale(Board.door_image, size)
        elif obj == 'door2':
            img = pygame.transform.scale(Board.door2_image, size)
        elif obj == 'shop':
            img = pygame.transform.scale(Shop.IMAGE, size)
        else:
            img = self.players[obj].image  # Изображения героев
        screen.blit(img, (x * size[0], y * size[1]))

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
                            self.current_player.image = pygame.transform.flip(self.current_player.image, True, False)
                            self.current_player.side = -1
                    if event.key == pygame.K_RIGHT:
                        self.current_level.move_player('right', self.current_player)
                        if self.current_player.side == -1:
                            self.current_player.image = pygame.transform.flip(self.current_player.image, True, False)
                            self.current_player.side = 1
                    if event.key == pygame.K_UP:
                        self.current_level.move_player('up', self.current_player)
                    if event.key == pygame.K_DOWN:
                        self.current_level.move_player('down', self.current_player)
                    if event.key == pygame.K_e:
                        self.current_level.action(self.current_player)

            screen.fill('black')
            self.draw_level()
            pygame.display.flip()


shop = Shop()


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
        x, y = self.get_coords(char)
        # смена героя
        side = player.side
        if self.field[y][x + side] in map(lambda x: x.CHAR, board.players.values()):
            self.field[y] = list(self.field[y])
            self.field[y][x], self.field[y][x + side] = self.field[y][x + side], self.field[y][x]
            self.field[y] = ''.join(self.field[y])
            if self.field[y][x] == 'A':
                board.current_player = board.players['axe']
            elif self.field[y][x] == 'K':
                board.current_player = board.players['kope']
            elif self.field[y][x] == 'S':
                board.current_player = board.players['sword']
        # магазин
        elif self.field[y][x + player.side] == 'H':
            shop.running = True
            while shop.running:
                screen.fill('yellow')
                shop.draw(screen)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        terminate()
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            shop.running = False


board = Board()
board.show_start_screen()
