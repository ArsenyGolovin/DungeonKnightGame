import pygame
import sys
import os

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


class PlayerSword(Player):
    IMAGE = load_image('sword.png', -1)
    CHAR = 'S'

    def __init__(self):
        self.hp = 100
        self.dmg = 20
        self.armor = 10
        self.attack_speed_per_second = 4


class PlayerAxe(Player):
    IMAGE = load_image('axe.png', -1)
    CHAR = 'A'

    def __init__(self):
        self.hp = 120
        self.dmg = 40
        self.armor = 25
        self.attack_speed_per_second = 2


class PlayerKope(Player):
    IMAGE = load_image('kope.png', -1)
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
        self.BLACK = (255, 255, 255)
        self.running = True
        self.coins = 0

    def draw(self, screen):
        screen.fill('yellow')
        self.shop_icon(screen)
        self.axe_icon(screen)

    def shop_icon(self, screen):
        font = pygame.font.SysFont('serif', 37)
        text = font.render('SHOP', True, self.BLACK)
        screen.blit(text, (10, 2))

    def axe_icon(self, screen):
        screen.blit(PlayerAxe.IMAGE, (1, 10))
        font = pygame.font.SysFont('serif', 15)
        text = font.render(f'Axe(2)   {self.coins}/50 coins', True, self.BLACK)
        screen.blit(text, (10, 10))


shop = Shop()


class Board:
    wall_image = load_image('box.jpg')
    floor_image = load_image('floor0.jpg')
    door_image = load_image('door.png')
    door2_image = load_image('door2.png')

    def __init__(self):
        self.current_level = self.load_level('map.txt')
        self.current_player = PlayerSword()
        self.flag_hero2 = PlayerKope()
        self.flag_hero3 = PlayerAxe()


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
        self.mainloop()

    @staticmethod
    def load_level(filename):
        return Level(filename)

    def draw_level(self):
        field = self.current_level.get_field()
        for y in range(len(field)):
            for x in range(len(field[y])):
                if field[y][x] == '0':
                    Board.draw_img('floor', x, y)
                elif field[y][x] == '1':
                    Board.draw_img('wall', x, y)
                elif field[y][x] == PlayerSword.CHAR:
                    Board.draw_img('floor', x, y)
                    Board.draw_img('player_sword', x, y)
                elif field[y][x] == 'K':
                    Board.draw_img('floor', x, y)
                    Board.draw_img('player_kope', x, y)
                elif field[y][x] == 'A':
                    Board.draw_img('floor', x, y)
                    Board.draw_img('player_axe', x, y)
                elif field[y][x] == '2':
                    Board.draw_img('door', x, y)
                elif field[y][x] == '3':
                    Board.draw_img('door2', x, y)
                elif field[y][x] == Shop.CHAR:
                    Board.draw_img('floor', x, y)
                    Board.draw_img('shop', x, y)

    @staticmethod
    def draw_img(obj, x, y):
        img: pygame.Surface
        size = (70, 70)
        if obj == 'player_sword':
            img = pygame.transform.scale(PlayerSword.IMAGE, size)
        elif obj == 'player_kope':
            img = pygame.transform.scale(PlayerKope.IMAGE, size)
        elif obj == 'player_axe':
            img = pygame.transform.scale(PlayerAxe.IMAGE, size)
        elif obj == 'wall':
            img = pygame.transform.scale(Board.wall_image, size)
        elif obj == 'floor':
            img = pygame.transform.scale(Board.floor_image, size)
        elif obj == 'door':
            img = pygame.transform.scale(Board.door_image, size)
        elif obj == 'door2':
            img = pygame.transform.scale(Board.door2_image, size)
        elif obj == 'shop':
            img = pygame.transform.scale(Shop.IMAGE, size)
        screen.blit(img, (x * size[0], y * size[1]))

    def mainloop(self):
        running = True
        FPS = 60
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.current_level.move_player('left', self.current_player)
                    if event.key == pygame.K_RIGHT:
                        self.current_level.move_player('right', self.current_player)
                    if event.key == pygame.K_UP:
                        self.current_level.move_player('up', self.current_player)
                    if event.key == pygame.K_DOWN:
                        self.current_level.move_player('down', self.current_player)
                    if event.key == pygame.K_e:
                        self.current_level.move_player('action', self.current_player)


            screen2.fill('black')
            self.draw_level()
            screen.blit(screen2, (0, 0))
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
        elif direction == 'action':
            # смена героя
            if self.field[y][x - 1] in [board.flag_hero2.CHAR, board.flag_hero3.CHAR]:
                li = list(self.field[y])
                if y < 3:
                    self.field[y] = li[0] + li[2] + li[1] + li[3] + li[4] + li[5] + li[6] + li[7] + li[8] \
                               + li[9] + li[10] + li[11]
                    board.current_player, board.flag_hero2 = board.flag_hero2, board.current_player

                if y >= 3:
                    self.field[y] = li[0] + li[2] + li[1] + li[3] + li[4] + li[5] + li[6] + li[7] + li[8] \
                               + li[9] + li[10] + li[11]

                    board.current_player, board.flag_hero3 = board.flag_hero3, board.current_player
             # магазин
            elif self.field[y][x - 1] == 'H' or self.field[y - 1][x] == 'H' or self.field[y - 1][x - 1] == 'H' or \
                    self.field[y + 1][x - 1] == 'H' or self.field[y + 1][x] == 'H':
                print('+')
                global shop
                shop.running = True
                while shop.running:
                    for event in pygame.event.get():
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                shop.running = False
                    shop.draw(screen)



board = Board()
width, height = 840, 770
screen2 = pygame.display.set_mode((width, height), pygame.NOFRAME)
screen2.fill('black')
board.show_start_screen()
