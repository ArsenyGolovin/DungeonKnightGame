import pygame
import sys
import os

pygame.init()
screen = pygame.display.set_mode((900, 900), pygame.NOFRAME)
screen.fill((255, 255, 255))


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


player_sword_image = load_image('sword.png', -1)
player_kope_image = load_image('kope.png', -1)
player_axe_image = load_image('axe.png', -1)
wall_image = load_image('box.jpg')
floor_image = load_image('floor0.jpg')
door_image = load_image('door.png')
door2_image = load_image('door2.png')
shop_image = load_image('shop.png', -1)


def load_level(filename):
    filename = "data/" + filename
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    max_width = max(map(len, level_map))
    return list(map(lambda x: x.ljust(max_width, '.'), level_map))


def draw_img(obj, x, y):
    img: pygame.Surface
    if obj == 'player_sword':
        img = pygame.transform.scale(player_sword_image, (70, 70))
    elif obj == 'player_kope':
        img = pygame.transform.scale(player_kope_image, (70, 70))
    elif obj == 'player_axe':
        img = pygame.transform.scale(player_axe_image, (70, 70))
    elif obj == 'wall':
        img = pygame.transform.scale(wall_image, (70, 70))
    elif obj == 'floor':
        img = pygame.transform.scale(floor_image, (70, 70))
    elif obj == 'door':
        img = pygame.transform.scale(door_image, (70, 70))
    elif obj == 'door2':
        img = pygame.transform.scale(door2_image, (70, 70))
    elif obj == 'shop':
        img = pygame.transform.scale(shop_image, (70, 70))
    screen.blit(img, (x * 70, y * 70))


def draw_level(level):
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '0':
                draw_img('floor', x, y)
            elif level[y][x] == '1':
                draw_img('wall', x, y)
            elif level[y][x] == 'S':
                draw_img('floor', x, y)
                draw_img('player_sword', x, y)
            elif level[y][x] == 'K':
                draw_img('floor', x, y)
                draw_img('player_kope', x, y)
            elif level[y][x] == 'A':
                draw_img('floor', x, y)
                draw_img('player_axe', x, y)
            elif level[y][x] == '2':
                draw_img('door', x, y)
            elif level[y][x] == '3':
                draw_img('door2', x, y)
            elif level[y][x] == 'H':
                draw_img('floor', x, y)
                draw_img('shop', x, y)


def show_start_screen():
    intro_text = ["           Dungeon Knight",
                  "",
                  "",
                  "",
                  "",
                  ""]

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

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                return
        pygame.display.flip()


width, height = 840, 770
screen2 = pygame.display.set_mode((width, height), pygame.NOFRAME)
screen2.fill((255, 255, 255))
running = True
FPS = 50
show_start_screen()
level = load_level('map.txt')


def get_coords(level, elem: str):
    for y, s in enumerate(level):
        for x, e in enumerate(s):
            if level[y][x] == elem:
                return x, y


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                x, y = get_coords(level, 'S')
                if level[y][x - 1] == '0':
                    s = list(level[y])
                    s[x - 1], s[x] = 'S', '0'
                    level[y] = ''.join(s)
            if event.key == pygame.K_RIGHT:
                x, y = get_coords(level, 'S')
                if level[y][x + 1] == '0':
                    s = list(level[y])
                    s[x + 1] = 'S'
                    s[x] = '0'
                    level[y] = ''.join(s)
            if event.key == pygame.K_UP:
                x, y = get_coords(level, 'S')
                if level[y - 1][x] == '0':
                    level[y] = list(level[y])
                    level[y - 1] = list(level[y - 1])
                    level[y - 1][x] = 'S'
                    level[y][x] = '0'
                    level[y] = ''.join(level[y])
                    level[y - 1] = ''.join(level[y - 1])
            if event.key == pygame.K_DOWN:
                x, y = get_coords(level, 'S')
                if level[y + 1][x] == '0':
                    level[y] = list(level[y])
                    level[y + 1] = list(level[y + 1])
                    level[y + 1][x] = 'S'
                    level[y][x] = '0'
                    level[y] = ''.join(level[y])
                    level[y + 1] = ''.join(level[y + 1])

    screen2.fill('black')
    draw_level(level)
    screen.blit(screen2, (0, 0))
    pygame.display.flip()