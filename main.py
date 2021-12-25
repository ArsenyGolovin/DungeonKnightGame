import pygame
import sys
import os

pygame.init()
screen = pygame.display.set_mode((900, 900))
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


def draw_lvl(obj, x, y, screen2):
    x *= 70
    y *= 70
    img = 0
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
    screen2.blit(img, (x + 2, y + 12))


def generate_level(level, screen2):
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '0':
                draw_lvl('floor', x, y, screen2)
            elif level[y][x] == '1':
                draw_lvl('wall', x, y, screen2)
            elif level[y][x] == 'S':
                draw_lvl('floor', x, y, screen2)
                draw_lvl('player_sword', x, y, screen2)
            elif level[y][x] == 'K':
                draw_lvl('floor', x, y, screen2)
                draw_lvl('player_kope', x, y, screen2)
            elif level[y][x] == 'A':
                draw_lvl('floor', x, y, screen2)
                draw_lvl('player_axe', x, y, screen2)
            elif level[y][x] == '2':
                draw_lvl('door', x, y, screen2)
            elif level[y][x] == '3':
                draw_lvl('door2', x, y, screen2)
            elif level[y][x] == 'H':
                draw_lvl('floor', x, y, screen2)
                draw_lvl('shop', x, y, screen2)

def start_screen():
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

width, height = 845, 780
pygame.init()
screen = pygame.display.set_mode((width, height))
screen.fill((255, 255, 255))
screen2 = pygame.display.set_mode((width, height))
screen2.fill((255, 255, 255))
running = True
FPS = 50
start_screen()


def load_level(filename):
    filename = "data/" + filename
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]

    max_width = max(map(len, level_map))

    return list(map(lambda x: x.ljust(max_width, '.'), level_map))


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                pass
            if event.key == pygame.K_RIGHT:
                pass
            if event.key == pygame.K_UP:
                pass
            if event.key == pygame.K_DOWN:
                pass

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT:
                pass
            if event.key == pygame.K_RIGHT:
                pass
            if event.key == pygame.K_UP:
                pass
            if event.key == pygame.K_DOWN:
                pass

    screen.fill('black')
    generate_level(load_level('map.txt'), screen2)
    screen.blit(screen2, (0, 0))
    pygame.display.flip()