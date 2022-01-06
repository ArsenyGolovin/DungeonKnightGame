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
    side = -1  # Влево


class PlayerSword(Player):
    IMAGE = load_image('sword.png', -1)
    CHAR = 'S'
    STATUS = 'unlock'

    def __init__(self):
        self.hp = 100
        self.dmg = 20
        self.armor = 10
        self.attack_speed_per_second = 4


class PlayerAxe(Player):
    IMAGE = load_image('axe.png', -1)
    CHAR = 'A'
    STATUS = 'lock'

    def __init__(self):
        self.hp = 120
        self.dmg = 40
        self.armor = 25
        self.attack_speed_per_second = 2


class PlayerKope(Player):
    IMAGE = load_image('kope.png', -1)
    CHAR = 'K'
    STATUS = 'lock'

    def __init__(self):
        self.hp = 90
        self.dmg = 50
        self.armor = 10
        self.attack_speed_per_second = 1.5


class Shop:
    IMAGE = load_image('shop.png', -1)
    CHAR = 'H'

    def __init__(self):
        self.hp_img = load_image('heart_icon.png', -1)
        self.dmg_img = load_image('damage_icon.jpg', -1)
        self.armor_img = load_image('armor_icon.png', -1)
        self.speed_img = load_image('speed_icon.jpg', -1)
        self.coin_img = load_image('coins.png', -1)
        self.txt1 = f'         50 coins'
        self.txt2 = f'         50 coins'
        self.BLACK = (0, 0, 0)
        self.font = pygame.font.SysFont('serif', 25)
        self.running = True
        self.coins = 100

    def buy(self, pos, player):
        x = range(20, 290)
        if pos[0] in x:
            for i in range(1, 7):
                if pos[1] in range(90 * i, 90 + (90 * i)):
                    if i == 1 and self.coins >= 50 and self.txt1 != ' BOUGHT':
                        self.txt1 = ' BOUGHT'
                        PlayerAxe.STATUS = 'unlock'
                        self.coins -= 50
                    elif i == 2 and self.coins >= 50 and self.txt2 != ' BOUGHT':
                        self.txt2 = ' BOUGHT'
                        PlayerKope.STATUS = 'unlock'
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
                        player.attack_speed_per_second += 0.1
                        st = str(player.attack_speed_per_second)
                        player.attack_speed_per_second = float(st[:4])
                        self.coins -= 10

    def draw(self, screen, player, pos):
        screen.fill('#FFCC66')

        x = range(20, 290)
        if pos[0] in x:
            for i in range(1, 7):
                if pos[1] in range(90 * i, 90 + (90 * i)):
                    pygame.draw.rect(screen, (255, 255, 0), (20, 90 * i, 270, 90))

        pygame.draw.rect(screen, (255, 0, 0), (20, 90, 270, 540), 3)
        for i in range(1, 7):
            pygame.draw.line(screen, (255, 0, 0), (20, 90 * i), (290, 90 * i), 3)

        screen.blit(pygame.transform.scale(player.IMAGE, (200, 200)), (430, 70))
        self.shop_icon(screen)
        self.icon(screen, PlayerAxe.IMAGE, (70, 70), (30, 100), self.txt1, (110, 120))
        self.icon(screen, PlayerKope.IMAGE, (70, 70), (30, 190), self.txt2, (110, 210))
        self.icon(screen, self.hp_img, (60, 60), (30, 285), f'+1     10 coins', (110, 300))
        self.icon(screen, self.hp_img, (60, 60), (430, 285), f'HP {player.hp}', (510, 300))
        self.icon(screen, self.dmg_img, (60, 60), (30, 375), f'+1     10 coins', (110, 390))
        self.icon(screen, self.dmg_img, (60, 60), (430, 375), f'DMG   {player.dmg}', (510, 390))
        self.icon(screen, self.armor_img, (60, 60), (30, 465), f'+1     10 coins', (110, 480))
        self.icon(screen, self.armor_img, (60, 60), (430, 465), f'ARMOR  {player.armor}', (510, 480))
        self.icon(screen, self.speed_img, (60, 60), (30, 555), f'+0.1  10 coins', (110, 570))
        self.icon(screen, self.speed_img, (60, 60), (430, 555), f'ATTACK SPEED  {player.attack_speed_per_second}',
                  (510, 570))
        self.icon(screen, self.coin_img, (60, 60), (430, 645), f'COINS  {self.coins}', (510, 660))

    def shop_icon(self, screen):
        font = pygame.font.SysFont('serif', 37)
        text = font.render('SHOP', True, self.BLACK)
        screen.blit(text, (335, 12))

    def icon(self, screen, obj, size, pos_img, txt, pos_txt):
        screen.blit(pygame.transform.scale(obj, size), pos_img)
        text = self.font.render(txt, True, self.BLACK)
        screen.blit(text, pos_txt)


class Board:
    wall_image = load_image('box.jpg')
    floor_image = load_image('floor0.jpg')
    door_image = load_image('door.png')
    door2_image = load_image('door2.png')

    def __init__(self):
        self.current_level = self.load_level('map.txt')
        self.players = {'sword': PlayerSword(), 'kope': PlayerKope(), 'axe': PlayerAxe()}
        self.current_player = self.players['sword']

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
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.current_level.move_player('left', self.current_player)
                        if self.current_player.side == 1:
                            self.current_player.image = pygame.transform.flip(self.current_player.IMAGE, True, False)
                            self.current_player.side = -1
                    if event.key == pygame.K_RIGHT:
                        self.current_level.move_player('right', self.current_player)
                        if self.current_player.side == -1:
                            self.current_player.image = pygame.transform.flip(self.current_player.IMAGE, True, False)
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
        x, y = self.get_coords(char)
        # смена героя
        side = player.side
        if self.field[y][x + side] in map(lambda x: x.CHAR, board.players.values()):
            self.flag = False
            if self.field[y][x + side] == 'A':
                if board.players['axe'].STATUS == 'unlock':
                    self.flag = True
            elif self.field[y][x + side] == 'K':
                if board.players['kope'].STATUS == 'unlock':
                    self.flag = True
            elif self.field[y][x + side] == 'S':
                if board.players['sword'].STATUS == 'unlock':
                    self.flag = True
            if self.flag is True:
                self.field[y] = list(self.field[y])
                self.field[y][x], self.field[y][x + side] = self.field[y][x + side], self.field[y][x]
                self.field[y] = ''.join(self.field[y])
                if self.field[y][x] == 'A':
                    board.current_player = board.players['axe']
                elif self.field[y][x] == 'K':
                    board.current_player = board.players['kope']
                elif self.field[y][x] == 'S':
                    board.current_player = board.players['sword']
                self.flag = False
        # магазин
        elif self.field[y][x - 1] == 'H' or self.field[y - 1][x] == 'H' or self.field[y - 1][x - 1] == 'H' or \
                self.field[y + 1][x - 1] == 'H' or self.field[y + 1][x] == 'H':
            shop.running = True
            while shop.running:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            shop.running = False
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        pos1 = event.pos
                        print(pos1)
                        shop.buy(pos1, board.current_player)
                        shop.draw(screen, board.current_player, pos1)
                        pygame.display.flip()
                    if event.type == pygame.MOUSEMOTION:
                        pos = event.pos
                        shop.draw(screen, board.current_player, pos)
                        pygame.display.flip()


board = Board()
shop = Shop()
board.show_start_screen()
