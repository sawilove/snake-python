import pygame
import random
import sys
import os
from pathlib import Path

# Инициализация PyGame
pygame.init()

# Константы
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 650
FIELD_SIZE = 488  # Увеличено на 8 пикселей вправо и вниз (было 480)
GRID_SIZE = 20
GRID_WIDTH = FIELD_SIZE // GRID_SIZE  # 24
GRID_HEIGHT = FIELD_SIZE // GRID_SIZE  # 24
FPS = 10
FIELD_OFFSET_X = (WINDOW_WIDTH - FIELD_SIZE) // 2
FIELD_OFFSET_Y = 100  # Место для текста сверху
BORDER_THICKNESS = 4  # Увеличенная толщина рамки
DEATH_SPEED = 4  # Скорость смерти змейки (чем меньше число, тем быстрее исчезают сегменты)

# Цвета
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
GREEN_ALPHA = (0, 255, 0, 128)  # Полупрозрачный зеленый для умирающей змейки
RED = (255, 0, 0)
WHITE = (255, 255, 255)
WHITE_ALPHA = (255, 255, 255, 128)  # Полупрозрачный белый для текста отладки
YELLOW = (255, 255, 0)
GRAY = (50, 50, 50)  # Цвет сетки для отладки

# Настройка экрана
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Змейка")
clock = pygame.time.Clock()
icon_path = "icon.ico"
try:
    icon = pygame.image.load(icon_path)
    pygame.display.set_icon(icon)
except FileNotFoundError:
    print(f"Файл иконки '{icon_path}' не найден. Используется стандартная иконка.")
# Путь к шрифту PIXY.ttf с обработкой ошибки
font_path = "PIXY.ttf"
try:
    font = pygame.font.Font(font_path, 36)
    game_over_font = pygame.font.Font(font_path, 40)
    small_font = pygame.font.Font(font_path, 24)
    debug_font = pygame.font.Font(font_path, 20)  # Шрифт для отладочного текста и инструкций
except FileNotFoundError:
    print("Шрифт PIXY.ttf не найден. Используется шрифт по умолчанию.")
    font = pygame.font.SysFont(None, 36)
    game_over_font = pygame.font.SysFont(None, 40)
    small_font = pygame.font.SysFont(None, 24)
    debug_font = pygame.font.SysFont(None, 20)

# Путь для сохранения рекорда
DOCUMENTS_DIR = Path.home() / "Documents"
SAVE_DIR = DOCUMENTS_DIR / "SnakeSaves"
SAVE_FILE = SAVE_DIR / "local.save"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

def load_high_score():
    if SAVE_FILE.exists():
        with open(SAVE_FILE, "r") as f:
            return int(f.read().strip())
    return 0

def save_high_score(score):
    with open(SAVE_FILE, "w") as f:
        f.write(str(score))

def reset_high_score():
    save_high_score(0)
    return 0

def wrap_text(surface, text, font, color, max_width, x_start, y_start):
    words = text.split()
    lines = []
    current_line = []
    current_width = 0

    for word in words:
        word_surface = font.render(word + " ", True, color)
        word_width = word_surface.get_width()
        if current_width + word_width <= max_width:
            current_line.append(word)
            current_width += word_width
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_width = word_width
    if current_line:
        lines.append(" ".join(current_line))

    y_position = y_start
    for line in lines:
        text_surface = font.render(line, True, color)
        surface.blit(text_surface, (x_start + (max_width - text_surface.get_width()) // 2, y_position))
        y_position += text_surface.get_height() + 10

class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        self.positions = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = random.choice([UP, DOWN, LEFT, RIGHT])
        self.length = 1
        self.dead = False
        self.death_frame = 0

    def update_position(self):
        if self.dead:
            self.death_frame += 1
            if self.positions:
                if self.death_frame % DEATH_SPEED == 0:
                    self.positions.pop()
                return True
            return False

        head_x, head_y = self.positions[0]
        if self.direction == UP:
            new_head = (head_x, head_y - 1)
        elif self.direction == DOWN:
            new_head = (head_x, head_y + 1)
        elif self.direction == LEFT:
            new_head = (head_x - 1, head_y)
        elif self.direction == RIGHT:
            new_head = (head_x + 1, head_y)

        new_head = (new_head[0] % GRID_WIDTH, new_head[1] % GRID_HEIGHT)

        if new_head in self.positions:
            self.dead = True
            self.death_frame = 0
            return True

        self.positions.insert(0, new_head)
        if len(self.positions) > self.length:
            self.positions.pop()
        return True

    def grow(self):
        self.length += 1

    def render(self, surface):
        for i, (x, y) in enumerate(self.positions):
            x_pos = FIELD_OFFSET_X + BORDER_THICKNESS + x * GRID_SIZE
            y_pos = FIELD_OFFSET_Y + BORDER_THICKNESS + y * GRID_SIZE
            outer_rect = pygame.Rect(x_pos - 1, y_pos - 1, GRID_SIZE + 1, GRID_SIZE + 1)
            pygame.draw.rect(surface, BLACK, outer_rect, 1)
            inner_rect = pygame.Rect(x_pos, y_pos, GRID_SIZE - 1, GRID_SIZE - 1)
            if self.dead:
                temp_surface = pygame.Surface((GRID_SIZE - 1, GRID_SIZE - 1), pygame.SRCALPHA)
                if i == 0 and self.death_frame % 2 == 0:  # Мерцание головы
                    continue
                temp_surface.fill(GREEN_ALPHA)
                surface.blit(temp_surface, (x_pos, y_pos))
            else:
                pygame.draw.rect(surface, GREEN, inner_rect)

# Направления
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

def spawn_apple():
    while True:
        apple = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
        if apple not in snake.positions:
            return apple

def main():
    global snake
    snake = Snake()
    apple = spawn_apple()
    score = 0
    initial_high_score = load_high_score()
    high_score = initial_high_score
    game_over = False
    game_started = False
    show_grid = False
    debug_mode = False  # Флаг режима отладки
    show_debug_vars = False  # Флаг отображения переменных в отладке (сохраняется при переключении)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:  # Включение/выключение режима отладки
                    debug_mode = not debug_mode
                    if not debug_mode:  # При выходе из режима отладки отключаем только сетку
                        show_grid = False
                    # show_debug_vars остается без изменений
                if debug_mode:  # Действия только в режиме отладки
                    if event.key == pygame.K_1:  # Добавление сегмента и увеличение счета
                        snake.grow()
                        score += 1
                        if score >= high_score:
                            high_score = score
                            save_high_score(high_score)
                    elif event.key == pygame.K_0:  # Убийство змейки как в обычной игре
                        snake.dead = True
                        snake.death_frame = 0
                    elif event.key == pygame.K_g:  # Переключение сетки
                        show_grid = not show_grid
                    elif event.key == pygame.K_2:  # Переключение отображения переменных
                        show_debug_vars = not show_debug_vars
                if event.key == pygame.K_r and not game_started and not debug_mode:
                    high_score = reset_high_score()
                    initial_high_score = high_score
                if snake.dead or game_over:  # Перезапуск возможен сразу после смерти
                    if event.type == pygame.KEYDOWN:
                        snake = Snake()
                        apple = spawn_apple()
                        score = 0
                        game_over = False
                        game_started = False
                        initial_high_score = load_high_score()
                        high_score = initial_high_score
                    continue
                if not game_started:
                    if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                        game_started = True
                        if event.key == pygame.K_UP and snake.direction != DOWN:
                            snake.direction = UP
                        elif event.key == pygame.K_DOWN and snake.direction != UP:
                            snake.direction = DOWN
                        elif event.key == pygame.K_LEFT and snake.direction != RIGHT:
                            snake.direction = LEFT
                        elif event.key == pygame.K_RIGHT and snake.direction != LEFT:
                            snake.direction = RIGHT
                else:
                    if event.key == pygame.K_UP and snake.direction != DOWN:
                        snake.direction = UP
                    elif event.key == pygame.K_DOWN and snake.direction != UP:
                        snake.direction = DOWN
                    elif event.key == pygame.K_LEFT and snake.direction != RIGHT:
                        snake.direction = LEFT
                    elif event.key == pygame.K_RIGHT and snake.direction != LEFT:
                        snake.direction = RIGHT

        if not game_over and game_started:
            if not snake.update_position():
                game_over = True
                if score > initial_high_score:
                    save_high_score(score)
            else:
                if snake.positions and snake.positions[0] == apple:
                    score += 1
                    snake.grow()
                    apple = spawn_apple()
                    if score >= high_score:
                        high_score = score
                        save_high_score(high_score)

        # Отрисовка
        screen.fill(BLACK)

        # Рисуем поле и элементы игры
        snake.render(screen)
        if not game_over and not snake.dead:
            apple_rect = pygame.Rect(FIELD_OFFSET_X + BORDER_THICKNESS + apple[0] * GRID_SIZE, 
                                   FIELD_OFFSET_Y + BORDER_THICKNESS + apple[1] * GRID_SIZE, GRID_SIZE - 1, GRID_SIZE - 1)
            pygame.draw.rect(screen, RED, apple_rect)

        # Рисуем текст всегда
        if not game_started:
            start_text = small_font.render("Двигайтесь, чтобы играть", True, WHITE)
            reset_text = small_font.render("Нажмите R, чтобы сбросить рекорд", True, WHITE)
            screen.blit(start_text, (FIELD_OFFSET_X + FIELD_SIZE // 2 - start_text.get_width() // 2, FIELD_OFFSET_Y + FIELD_SIZE - 60))
            screen.blit(reset_text, (FIELD_OFFSET_X + FIELD_SIZE // 2 - reset_text.get_width() // 2, FIELD_OFFSET_Y + FIELD_SIZE - 30))

        score_text = font.render(f"Счет: {score}", True, WHITE)
        high_score_text = font.render(f"Рекорд: {high_score}", True, WHITE)
        screen.blit(score_text, (FIELD_OFFSET_X, FIELD_OFFSET_Y - 50))
        screen.blit(high_score_text, (FIELD_OFFSET_X + 200, FIELD_OFFSET_Y - 50))

        # Отладочный режим: надпись DEV MODE и инструкции внутри поля
        if debug_mode:
            dev_mode_text = small_font.render("DEV MODE", True, RED)
            screen.blit(dev_mode_text, (FIELD_OFFSET_X + 400, FIELD_OFFSET_Y - 50))

            # Инструкция внутри игрового поля (справа)
            debug_instructions = [
                "1 - Add Length",
                "2 - ON Vars",
                "0 - Defeat",
                "G - Grid"
            ]
            instruction_x = FIELD_OFFSET_X + 320  # Справа внутри поля с отступом 120 пикселей
            instruction_y = FIELD_OFFSET_Y + 20  # Начальная позиция по вертикали внутри поля
            for i, instruction in enumerate(debug_instructions):
                instr_surface = debug_font.render(instruction, True, WHITE_ALPHA)
                screen.blit(instr_surface, (instruction_x, instruction_y + i * 25))

        # Отладочный режим: отображение переменных слева
        if debug_mode and show_debug_vars:
            debug_surface = pygame.Surface((200, WINDOW_HEIGHT), pygame.SRCALPHA)
            debug_vars = [
                f"Score: {score}",
                f"High Score: {high_score}",
                f"Snake Length: {snake.length}",
                f"Snake Dead: {snake.dead}",
                f"Game Over: {game_over}",
                f"Game Started: {game_started}",
                f"Death Frame: {snake.death_frame}"
            ]
            for i, var in enumerate(debug_vars):
                var_text = debug_font.render(var, True, WHITE_ALPHA)
                debug_surface.blit(var_text, (10, 10 + i * 25))
            screen.blit(debug_surface, (10, 10))

        # Текст проигрыша
        if snake.dead or game_over:
            center_x = FIELD_OFFSET_X + FIELD_SIZE // 2
            center_y = FIELD_OFFSET_Y + FIELD_SIZE // 2
            wrap_text(screen, "Игра окончена", game_over_font, WHITE, FIELD_SIZE - 2 * BORDER_THICKNESS, FIELD_OFFSET_X, center_y - 80)
            wrap_text(screen, "Нажмите любую клавишу чтобы начать заново", small_font, WHITE, FIELD_SIZE - 2 * BORDER_THICKNESS, FIELD_OFFSET_X, center_y)
            if score > initial_high_score:
                new_record_text = font.render("Новый рекорд!", True, YELLOW)
                screen.blit(new_record_text, (center_x - new_record_text.get_width() // 2, center_y + 80))

        # Сетка для отладки
        if show_grid:
            for x in range(0, FIELD_SIZE, GRID_SIZE):
                pygame.draw.line(screen, GRAY, (FIELD_OFFSET_X + BORDER_THICKNESS + x, FIELD_OFFSET_Y + BORDER_THICKNESS), 
                               (FIELD_OFFSET_X + BORDER_THICKNESS + x, FIELD_OFFSET_Y + FIELD_SIZE - BORDER_THICKNESS), 1)
            for y in range(0, FIELD_SIZE, GRID_SIZE):
                pygame.draw.line(screen, GRAY, (FIELD_OFFSET_X + BORDER_THICKNESS, FIELD_OFFSET_Y + BORDER_THICKNESS + y), 
                               (FIELD_OFFSET_X + FIELD_SIZE - BORDER_THICKNESS, FIELD_OFFSET_Y + BORDER_THICKNESS + y), 1)

        # Рамка
        pygame.draw.rect(screen, WHITE, (FIELD_OFFSET_X, FIELD_OFFSET_Y, FIELD_SIZE, FIELD_SIZE), BORDER_THICKNESS)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()