
import os.path
from enum import Enum

import random
import pygame
from pygame.locals import *

from model import Model


class GameState(Enum):
    Menu = 1
    Waiting = 2
    FirstCardOpened = 3
    SecondCardOpened = 4
    GameOver = 5


# Переменные и константы
score = 0
start_time = 0
screen_size = Rect(0, 0, 1024, 850)
difficulty_levels = [(4, 4), (5, 4), (6, 4), (6, 5), (6, 6)]
field_size = difficulty_levels[0]

folder_main = os.path.split(os.path.abspath(__file__))[0]


def open_sprite_multiple(paths):
    sprites = []
    for path in paths:
        sprites.append(open_sprite(path))
    return sprites


def open_sprite(path):
    """Загрузить картинку из файла"""
    path = os.path.join(folder_main, 'data', path)
    try:
        texture = pygame.image.load(path)
    except pygame.error:
        raise SystemExit('Ошибка загрузки: %s' % path)
    return texture.convert_alpha()


class emptysound:
    def play(self): pass


def load_sound(path):
    """Загрузить звук из файла"""
    if not pygame.mixer:
        return emptysound()
    path = os.path.join(folder_main, 'data', path)
    try:
        return pygame.mixer.Sound(path)
    except pygame.error:
        print('Ошибка загрузки: %s' % path)
    return emptysound()


class Card(pygame.sprite.Sprite):
    def __init__(self, image, image_opened, index):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.image = image
        self.image_closed = image
        self.image_opened = image_opened
        self.index = index
        self.opened = False
        self.alive = True
        self.rect = self.image.get_rect()

        self.animating = 0

    def open(self):
        self.opened = True

        self.anim_progress = 0
        self.animating = 1

    def close(self):
        self.opened = False

        self.anim_progress = 0
        self.animating = -1

    def update(self):
        if self.animating != 0:
            self.anim_progress += clock.get_time() / 250
            center = self.rect.center
            width = 98

            if (self.animating == 1) != (self.anim_progress > 0.5):
                img = self.image_closed
            else:
                img = self.image_opened

            if self.anim_progress > 1:
                self.animating = 0
            elif self.anim_progress > 0.5:
                width *= self.anim_progress * 2 - 1
            else:
                width *= 1 - self.anim_progress * 2

            self.image = pygame.transform.scale(img, (int(width), self.rect.height))
            self.rect = self.image.get_rect()
            self.rect.center = center


class Score(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font(None, 50)
        self.prev_displayed = -10
        self.update()
        size = self.image.get_rect()
        self.rect = size.move(30, 30)

    def update(self):
        if score != self.prev_displayed:
            self.prev_displayed = score
            msg = "счет: %d" % score
            self.image = self.font.render(msg, 0, Color('white'))


class Congrats(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font(None, 65)
        self.set_text()
        self.rect = self.image.get_rect()
        self.rect.centerx = screen_size.centerx
        self.rect.centery = screen_size.centery

    def set_text(self):
        time = pygame.time.get_ticks() - start_time

        minutes = (time // 1000) // 60
        seconds = (time // 1000) % 60

        msg = "Ты выйграл ! Счет - %s Время - %s:%s" % (score, minutes, seconds)
        self.image = self.font.render(msg, 0, Color('white'))


def main(winstyle=0):
    global score

    if pygame.get_sdl_version()[0] == 2:
        pygame.mixer.pre_init(44100, 32, 2, 1024)
    pygame.init()
    if pygame.mixer and not pygame.mixer.get_init():
        print('Warning, no sound')
        pygame.mixer = None

    bestdepth = pygame.display.mode_ok(screen_size.size, winstyle, 32)
    screen = pygame.display.set_mode(screen_size.size, winstyle, bestdepth)

    # Загружаем все спрайты
    menu_sprites = open_sprite_multiple(['menu (' + str(x) + ').png' for x in range(1, 6)])
    cards_sprites = open_sprite_multiple([str(x) + '.png' for x in range(1, 27)])
    card_back = open_sprite('card_back.png')
    random.shuffle(cards_sprites)

    # Задаём параметры окна
    icon = pygame.transform.scale(card_back, (32, 32))
    pygame.display.set_icon(icon)
    pygame.display.set_caption('Memory puzzle')

    # Загружаем фон
    bg = pygame.Surface(screen_size.size)
    bg.fill((2, 75, 89))
    screen.fill([2, 75, 89])
    pygame.display.flip()

    game_state = GameState.Menu

    all = pygame.sprite.RenderUpdates()

    Card.containers = all
    Score.containers = all
    Congrats.containers = all

    timer_started = 0

    global clock
    clock = pygame.time.Clock()

    cards = []
    buttons = create_menu(menu_sprites)

    done = 0
    while not done:
        mouse_click = 0

        # Считываем что нажал пользователь
        for e in pygame.event.get():
            if e.type == QUIT or (e.type == KEYUP and e.key == K_ESCAPE):
                done = 1
                break
            elif e.type == MOUSEBUTTONDOWN and e.button == 1:
                mouse_click = list(e.pos)

        if mouse_click:
            if game_state == GameState.Menu:
                # Кликнули по кнопке сложности в меню, начинаем игру
                clicked_button = get_clicked_button(buttons, mouse_click)
                if clicked_button is not None:
                    global field_size
                    global start_time
                    field_size = clicked_button.difficulty
                    start_time = pygame.time.get_ticks()
                    cards = create_level(card_back, cards_sprites)
                    for button in buttons:
                        button.kill()
                    game_state = GameState.Waiting
                    all.add(Score())

            elif game_state == GameState.Waiting:
                # Открыли первую карту
                clicked_card = get_clicked_card(cards, mouse_click)
                if clicked_card is not None:
                    clicked_card.open()
                    game_state = GameState.FirstCardOpened

            elif game_state == GameState.FirstCardOpened:
                # Открыли вторую карту
                card = get_clicked_card(cards, mouse_click)
                if card is not None:
                    card.open()
                    game_state = GameState.SecondCardOpened
                    # Ставим таймер
                    timer_started = pygame.time.get_ticks()

        if game_state == GameState.SecondCardOpened and pygame.time.get_ticks() - timer_started > 1000:
            # Прошла секунда с открытия второй карты
            card1 = get_opened_card(cards)
            card1.close()
            card2 = get_opened_card(cards)
            card2.close()
            game_state = GameState.Waiting

            if card1.index == card2.index:
                # Карты совпали
                card1.kill()
                card1.alive = False
                card2.kill()
                card2.alive = False
                score += 2

                if is_over(cards):
                    # Игра закончена
                    all.add(Congrats())
                    game_state = GameState.GameOver
                    # Ставим таймер
                    timer_started = pygame.time.get_ticks()

        if game_state == GameState.GameOver and pygame.time.get_ticks() - timer_started > 4000:
            # Прошло 4 секунды с конца игры
            game_state = GameState.Menu

            score = 0
            all.empty()
            buttons = create_menu(menu_sprites)

        # Очищаем экран
        all.clear(screen, bg)
        all.update()

        # Рисуем всю сцену
        dirty = all.draw(screen)
        pygame.display.update(dirty)

        clock.tick(40)

    if pygame.mixer:
        pygame.mixer.music.fadeout(1000)
    pygame.time.wait(1000)
    pygame.quit()


def get_clicked_button(buttons, mouse_click):
    """Вернуть кнопку под мышкой"""
    for x in range(len(difficulty_levels)):
        if buttons[x].rect.collidepoint(mouse_click):
            return buttons[x]


def get_clicked_card(cards, mouse_click):
    """Вернуть карту под мышкой"""
    for y in range(field_size[1]):
        for x in range(field_size[0]):
            if cards[y][x].alive and cards[y][x].rect.collidepoint(mouse_click):
                return cards[y][x]


def get_opened_card(cards):
    """Вернуть первую открытую карту"""
    for y in range(field_size[1]):
        for x in range(field_size[0]):
            if cards[y][x].alive and cards[y][x].opened:
                return cards[y][x]


def is_over(cards):
    """Проверить закончена ли игра"""
    for y in range(field_size[1]):
        for x in range(field_size[0]):
            if cards[y][x].alive:
                return False
    return True


def create_menu(menu_sprites):
    """Создать меню, и вернуть массив кнопок"""
    buttons = [0] * len(difficulty_levels)

    for x in range(len(difficulty_levels)):
        buttons[x] = Card(menu_sprites[x], 0, x)
        buttons[x].rect.centerx = screen_size.centerx + (x - (len(difficulty_levels) - 1) / 2) * 150
        buttons[x].rect.centery = screen_size.centery
        buttons[x].difficulty = difficulty_levels[x]

    return buttons


def create_level(card_back, cards_sprites):
    """Создать уровень, и вернуть 2d массив карточек"""
    level = Model(field_size[0], field_size[1]).generate_level()
    cards = [[0] * field_size[0] for x in range(field_size[1])]

    for y in range(field_size[1]):
        for x in range(field_size[0]):
            index = level[y][x]
            if index != -1:
                # создать карточку в координатах (x, y)
                cards[y][x] = Card(card_back, cards_sprites[index], index)
                cards[y][x].rect.centerx = screen_size.centerx + (x - (field_size[0] - 1) / 2) * 100
                cards[y][x].rect.centery = screen_size.centery + (y - (field_size[1] - 1) / 2) * 130
            else:
                # создать пустое место, т.к. всего нечётное количество карт
                cards[y][x] = Card(card_back, card_back, -1)
                cards[y][x].kill()
                cards[y][x].alive = False

    return cards

if __name__ == '__main__':
    main()
