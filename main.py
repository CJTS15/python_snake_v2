import math
import random
import sys

import pygame

# --- Configuration & Constants ---
# We use "Virtual" dimensions for the game logic.
# The window can be any size, but the game thinks it's 810x600.
VIRTUAL_WIDTH = 810
VIRTUAL_HEIGHT = 600
GRID_SIZE = 30
GRID_WIDTH = VIRTUAL_WIDTH // GRID_SIZE
GRID_HEIGHT = VIRTUAL_HEIGHT // GRID_SIZE

# Colors
COLOR_BG = (240, 248, 255)
COLOR_TEXT = (50, 50, 80)
COLOR_BUTTON = (100, 149, 237)
COLOR_BUTTON_HOVER = (65, 105, 225)
COLOR_TIMER = (255, 215, 0)
COLOR_LETTERBOX = (50, 50, 50)

# Game Speed Settings
START_MOVE_DELAY = 160.0
DELAY_DECREMENT = 1.75
MIN_MOVE_DELAY = 10.0

# Event Settings
APPLES_FOR_EVENT = 10
SCORE_FOR_ROCK = 200
STAR_DURATION = 10000

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Create the actual window (Resizable)
screen = pygame.display.set_mode((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Snake 2.0 - Python Snake Game")

# Create the "Virtual" Surface where we draw everything
game_surface = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))

clock = pygame.time.Clock()

# --- Asset Loading ---
sprites_loaded = False
try:
    try:
        bg_image = pygame.image.load("background.png")
    except:
        bg_image = None

    raw_head = pygame.image.load("head.png").convert_alpha()
    raw_body = pygame.image.load("body.png").convert_alpha()
    raw_apple = pygame.image.load("apple.png").convert_alpha()
    raw_cookie = pygame.image.load("cookie.png").convert_alpha()
    raw_bomb = pygame.image.load("bomb.png").convert_alpha()
    raw_rock = pygame.image.load("rock.png").convert_alpha()
    raw_star = pygame.image.load("star.png").convert_alpha()
    raw_banana = pygame.image.load("banana.png").convert_alpha()

    # Scale Sprites
    img_head = pygame.transform.scale(raw_head, (GRID_SIZE, GRID_SIZE))
    img_body = pygame.transform.scale(raw_body, (GRID_SIZE + 2, GRID_SIZE + 2))
    img_apple = pygame.transform.scale(raw_apple, (GRID_SIZE + 8, GRID_SIZE + 8))
    img_cookie = pygame.transform.scale(raw_cookie, (GRID_SIZE + 8, GRID_SIZE + 8))
    img_bomb = pygame.transform.scale(raw_bomb, (GRID_SIZE + 8, GRID_SIZE + 8))
    img_rock = pygame.transform.scale(raw_rock, (GRID_SIZE * 3, GRID_SIZE * 3))
    img_star = pygame.transform.scale(raw_star, (GRID_SIZE + 8, GRID_SIZE + 8))
    img_banana = pygame.transform.scale(raw_banana, (GRID_SIZE + 8, GRID_SIZE + 8))

    sprites_loaded = True
except FileNotFoundError:
    print("One or more images not found. Using fallback shapes.")


# --- Helper: Virtual Mouse Coordinates ---
def get_virtual_mouse_pos():
    """
    Translates the real mouse position on the resizable window
    to the coordinates on the 810x600 game surface.
    """
    real_w, real_h = screen.get_size()
    real_mouse = pygame.mouse.get_pos()

    # Calculate scale factor (Aspect Ratio Fit)
    scale = min(real_w / VIRTUAL_WIDTH, real_h / VIRTUAL_HEIGHT)

    # Calculate the size of the game on screen
    new_w = VIRTUAL_WIDTH * scale
    new_h = VIRTUAL_HEIGHT * scale

    # Calculate offset (centering)
    offset_x = (real_w - new_w) // 2
    offset_y = (real_h - new_h) // 2

    # Translate coordinate
    vx = (real_mouse[0] - offset_x) / scale
    vy = (real_mouse[1] - offset_y) / scale

    return int(vx), int(vy)


# --- Sound Manager ---
class SoundManager:
    def __init__(self):
        self.sounds_enabled = True
        try:
            pygame.mixer.get_init()
        except:
            self.sounds_enabled = False

        # We must hold the sound object in a variable to stop it later
        self.powerup_loop_snd = None

        if self.sounds_enabled:
            try:
                # Pre-load the loop sound specifically
                self.powerup_loop_snd = pygame.mixer.Sound("powerup_loop.wav")
            except:
                print("Warning: powerup_loop.wav not found")

    # This generic function is fine for one-off sounds (eat, crash)
    def play_sound(self, file_name):
        if self.sounds_enabled:
            try:
                pygame.mixer.Sound(file_name).play()
            except:
                pass

    # One-shot sounds
    def play_eat(self):
        self.play_sound("eat.wav")

    def play_crash(self):
        self.play_sound("crash.wav")

    def play_bonus(self):
        self.play_sound("bonus.wav")

    def play_explode(self):
        self.play_sound("explode.wav")

    def play_powerup(self):
        self.play_sound("powerup.wav")

    # --- LOOPING LOGIC ---
    def start_powerup_loop(self):
        # We check if the variable exists, not the function
        if self.powerup_loop_snd:
            self.powerup_loop_snd.stop()  # Stop just in case it's running
            self.powerup_loop_snd.play(loops=-1)  # -1 means loop forever

    def stop_powerup_loop(self):
        if self.powerup_loop_snd:
            self.powerup_loop_snd.stop()


sound_manager = SoundManager()


# --- UI Classes ---
class Button:
    def __init__(self, text, x, y, width, height, action_code):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.action_code = action_code
        self.color = COLOR_BUTTON
        self.hover_color = COLOR_BUTTON_HOVER
        self.font = pygame.font.SysFont("comicsansms", 24, bold=True)

    def draw(self, surface):
        # We pass the virtual mouse pos to check hover state
        vx, vy = get_virtual_mouse_pos()
        is_hovered = self.rect.collidepoint(vx, vy)

        current_color = self.hover_color if is_hovered else self.color
        pygame.draw.rect(surface, current_color, self.rect, border_radius=15)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 3, border_radius=15)
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self):
        # We don't rely on event.pos directly, we rely on calculated virtual pos
        vx, vy = get_virtual_mouse_pos()
        if self.rect.collidepoint(vx, vy):
            return True
        return False


# --- Game Classes ---
class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        self.body = [
            (GRID_WIDTH // 2, GRID_HEIGHT // 2),
            (GRID_WIDTH // 2 - 1, GRID_HEIGHT // 2),
            (GRID_WIDTH // 2 - 2, GRID_HEIGHT // 2),
            (GRID_WIDTH // 2 - 3, GRID_HEIGHT // 2),
        ]
        self.prev_body = list(self.body)
        self.direction = (1, 0)
        self.new_direction = (1, 0)
        self.grow = False
        self.alive = True
        self.wrap_mode = False

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP and self.direction != (0, 1):
                self.new_direction = (0, -1)
            elif event.key == pygame.K_DOWN and self.direction != (0, -1):
                self.new_direction = (0, 1)
            elif event.key == pygame.K_LEFT and self.direction != (1, 0):
                self.new_direction = (-1, 0)
            elif event.key == pygame.K_RIGHT and self.direction != (-1, 0):
                self.new_direction = (1, 0)

    def shrink(self, amount):
        current_len = len(self.body)
        new_len = max(1, current_len - amount)
        self.body = self.body[:new_len]
        self.prev_body = self.prev_body[:new_len]

    def update_logic(self):
        if not self.alive:
            return

        self.prev_body = list(self.body)
        self.direction = self.new_direction

        head_x, head_y = self.body[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        if self.wrap_mode:
            new_head = (new_head[0] % GRID_WIDTH, new_head[1] % GRID_HEIGHT)
        else:
            if (
                new_head[0] < 0
                or new_head[0] >= GRID_WIDTH
                or new_head[1] < 0
                or new_head[1] >= GRID_HEIGHT
            ):
                self.alive = False
                sound_manager.play_crash()
                return

        if new_head in self.body:
            self.alive = False
            sound_manager.play_crash()
            return

        self.body.insert(0, new_head)

        if not self.grow:
            self.body.pop()
        else:
            self.grow = False
            self.prev_body.append(self.prev_body[-1])

    def draw(self, surface, interpolation_alpha):
        time_ticks = pygame.time.get_ticks()
        wiggle_amp = 4.0
        wiggle_freq = 0.6
        wiggle_speed = 0.01

        for i in range(len(self.body) - 1, -1, -1):
            curr_x, curr_y = self.body[i]
            if i < len(self.prev_body):
                prev_x, prev_y = self.prev_body[i]
            else:
                prev_x, prev_y = curr_x, curr_y

            # Disable interpolation on wrap-around to prevent flying artifacts
            if abs(curr_x - prev_x) > 1 or abs(curr_y - prev_y) > 1:
                exact_x = curr_x * GRID_SIZE
                exact_y = curr_y * GRID_SIZE
            else:
                exact_x = (
                    prev_x * GRID_SIZE
                    + (curr_x * GRID_SIZE - prev_x * GRID_SIZE) * interpolation_alpha
                )
                exact_y = (
                    prev_y * GRID_SIZE
                    + (curr_y * GRID_SIZE - prev_y * GRID_SIZE) * interpolation_alpha
                )

            if i > 0:
                wave = (
                    math.sin(i * wiggle_freq - time_ticks * wiggle_speed) * wiggle_amp
                )
            else:
                wave = 0

            if i == 0:
                dx, dy = self.direction
            else:
                p_x, p_y = self.body[i - 1]
                dx = p_x - curr_x
                dy = p_y - curr_y

            if abs(dx) > 1 or abs(dy) > 1:
                pass
            elif dx != 0:
                exact_y += wave
            else:
                exact_x += wave

            if sprites_loaded:
                if i == 0:
                    angle = 0
                    if self.direction == (1, 0):
                        angle = -90
                    elif self.direction == (-1, 0):
                        angle = 90
                    elif self.direction == (0, 1):
                        angle = 180
                    elif self.direction == (0, -1):
                        angle = 0
                    rotated_head = pygame.transform.rotate(img_head, angle)
                    rect = rotated_head.get_rect(
                        center=(exact_x + GRID_SIZE / 2, exact_y + GRID_SIZE / 2)
                    )
                    surface.blit(rotated_head, rect)
                else:
                    offset = (img_body.get_width() - GRID_SIZE) / 2
                    surface.blit(img_body, (exact_x - offset, exact_y - offset))
            else:
                pygame.draw.circle(
                    surface,
                    (50, 205, 50),
                    (int(exact_x + GRID_SIZE / 2), int(exact_y + GRID_SIZE / 2)),
                    GRID_SIZE // 2 + 1,
                )


class Item:
    def __init__(self, img_sprite=None, fallback_color=(255, 255, 255)):
        self.position = (-1, -1)
        self.active = False
        self.sprite = img_sprite
        self.color = fallback_color

    def spawn_random(self, occupied_positions):
        attempts = 0
        while attempts < 500:
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            if (x, y) not in occupied_positions:
                self.position = (x, y)
                self.active = True
                break
            attempts += 1

    def draw(self, surface):
        if not self.active:
            return
        x, y = self.position
        pos_x = x * GRID_SIZE
        pos_y = y * GRID_SIZE
        bob = math.sin(pygame.time.get_ticks() * 0.005) * 4

        if sprites_loaded and self.sprite:
            surface.blit(self.sprite, (pos_x, pos_y + bob))
        else:
            center = (pos_x + GRID_SIZE // 2, int(pos_y + GRID_SIZE // 2 + bob))
            pygame.draw.circle(surface, self.color, center, GRID_SIZE // 2)


class BigRock:
    def __init__(self, img_sprite):
        self.position = (-1, -1)
        self.active = False
        self.sprite = img_sprite
        self.footprint = []

    def spawn_random(self, occupied_positions):
        attempts = 0
        while attempts < 500:
            x = random.randint(0, GRID_WIDTH - 2)
            y = random.randint(0, GRID_HEIGHT - 2)
            proposed_area = [(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)]

            collision = False
            for spot in proposed_area:
                if spot in occupied_positions:
                    collision = True
                    break

            if not collision:
                self.position = (x, y)
                self.footprint = proposed_area
                self.active = True
                break
            attempts += 1

    def draw(self, surface):
        if not self.active:
            return
        x, y = self.position
        pos_x = x * GRID_SIZE
        pos_y = y * GRID_SIZE
        if sprites_loaded and self.sprite:
            surface.blit(self.sprite, (pos_x, pos_y))
        else:
            rect = pygame.Rect(pos_x, pos_y, GRID_SIZE * 2, GRID_SIZE * 2)
            pygame.draw.rect(surface, (100, 100, 100), rect)


# --- Game States ---
STATE_MENU = 0
STATE_GAME = 1
STATE_INSTRUCTION = 2
STATE_PAUSE = 3
STATE_GAMEOVER = 4


# --- Main Game Loop ---
def main():
    current_state = STATE_MENU

    snake = Snake()
    apple = Item(img_apple, (255, 50, 50))
    banana = Item(img_banana, (210, 180, 140))
    cookie = Item(img_cookie, (210, 180, 140))
    star = Item(img_star, (255, 255, 0))

    bombs = []
    rocks = []

    score = 0
    move_delay = START_MOVE_DELAY
    last_move_time = pygame.time.get_ticks()

    apples_eaten_count = 0
    rock_milestone = SCORE_FOR_ROCK
    star_end_time = 0

    font_score = pygame.font.SysFont("comicsansms", 30, bold=True)
    font_title = pygame.font.SysFont("comicsansms", 72, bold=True)
    font_inst = pygame.font.SysFont("comicsansms", 26)

    btn_w, btn_h = 200, 50
    cx = VIRTUAL_WIDTH // 2 - btn_w // 2

    btn_new_game = Button("New Game", cx, 250, btn_w, btn_h, "new")
    btn_inst = Button("Instructions", cx, 320, btn_w, btn_h, "inst")
    btn_quit = Button("Quit", cx, 390, btn_w, btn_h, "quit")

    btn_pause_resume = Button("Resume", cx, 200, btn_w, btn_h, "resume")
    btn_pause_new = Button("New Game", cx, 270, btn_w, btn_h, "new")
    btn_pause_inst = Button("Instructions", cx, 340, btn_w, btn_h, "inst")
    btn_pause_quit = Button("Quit", cx, 410, btn_w, btn_h, "quit")

    menu_buttons = [btn_new_game, btn_inst, btn_quit]
    pause_buttons = [btn_pause_resume, btn_pause_new, btn_pause_inst, btn_pause_quit]

    def get_occupied():
        occ = set(snake.body)
        if apple.active:
            occ.add(apple.position)
        if cookie.active:
            occ.add(cookie.position)
        if banana.active:
            occ.add(banana.position)
        if star.active:
            occ.add(star.position)
        for b in bombs:
            if b.active:
                occ.add(b.position)
        for r in rocks:
            if r.active:
                for spot in r.footprint:
                    occ.add(spot)
        return occ

    running = True
    while running:
        current_time = pygame.time.get_ticks()

        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Fullscreen Toggle Logic
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    is_fullscreen = pygame.display.is_fullscreen()
                    if is_fullscreen:
                        pygame.display.set_mode(
                            (VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.RESIZABLE
                        )
                    else:
                        pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

            if current_state == STATE_GAME:
                snake.handle_input(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    current_state = STATE_PAUSE

            elif current_state == STATE_MENU:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for btn in menu_buttons:
                        if btn.is_clicked():  # Using virtual mouse internally
                            if btn.action_code == "new":
                                sound_manager.stop_powerup_loop()
                                snake.reset()
                                score = 0
                                move_delay = START_MOVE_DELAY
                                last_move_time = current_time
                                apples_eaten_count = 0
                                bombs = []
                                rocks = []
                                rock_milestone = SCORE_FOR_ROCK
                                cookie.active = False
                                banana.active = False
                                star.active = False
                                star_end_time = 0
                                apple.spawn_random(get_occupied())
                                current_state = STATE_GAME
                            elif btn.action_code == "inst":
                                current_state = STATE_INSTRUCTION
                            elif btn.action_code == "quit":
                                running = False

            elif current_state == STATE_PAUSE:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for btn in pause_buttons:
                        if btn.is_clicked():
                            if btn.action_code == "resume":
                                last_move_time = current_time
                                current_state = STATE_GAME
                            elif btn.action_code == "new":
                                snake.reset()
                                score = 0
                                move_delay = START_MOVE_DELAY
                                last_move_time = current_time
                                apples_eaten_count = 0
                                bombs = []
                                rocks = []
                                rock_milestone = SCORE_FOR_ROCK
                                cookie.active = False
                                banana.active = False
                                star.active = False
                                star_end_time = 0
                                apple.spawn_random(get_occupied())
                                current_state = STATE_GAME
                            elif btn.action_code == "inst":
                                current_state = STATE_INSTRUCTION
                            elif btn.action_code == "quit":
                                running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    last_move_time = current_time
                    current_state = STATE_GAME

            elif current_state == STATE_INSTRUCTION:
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    if snake.alive and score > 0:
                        current_state = STATE_PAUSE
                    else:
                        current_state = STATE_MENU

            elif current_state == STATE_GAMEOVER:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        snake.reset()
                        score = 0
                        move_delay = START_MOVE_DELAY
                        last_move_time = current_time
                        apples_eaten_count = 0
                        bombs = []
                        rocks = []
                        rock_milestone = SCORE_FOR_ROCK
                        cookie.active = False
                        banana.active = False
                        star.active = False
                        star_end_time = 0
                        apple.spawn_random(get_occupied())
                        current_state = STATE_GAME
                    elif event.key == pygame.K_ESCAPE:
                        current_state = STATE_MENU

        # 2. Logic Update
        alpha = 0.0

        if current_state == STATE_GAME:
            if current_time < star_end_time:
                snake.wrap_mode = True
            else:
                sound_manager.stop_powerup_loop()
                snake.wrap_mode = False

            time_since_move = current_time - last_move_time
            if time_since_move >= move_delay:
                snake.update_logic()
                last_move_time = current_time
                time_since_move = 0
                head = snake.body[0]

                if score >= rock_milestone:
                    r = BigRock(img_rock if sprites_loaded else None)
                    r.spawn_random(get_occupied())
                    rocks.append(r)
                    rock_milestone += SCORE_FOR_ROCK

                # Interactions
                if head == apple.position:
                    snake.grow = True
                    score += 10
                    sound_manager.play_eat()
                    move_delay = max(MIN_MOVE_DELAY, move_delay - DELAY_DECREMENT)
                    apples_eaten_count += 1

                    if apples_eaten_count % APPLES_FOR_EVENT == 0:
                        cookie.spawn_random(get_occupied())
                        banana.spawn_random(get_occupied())
                        for _ in range(4):
                            b = Item(img_bomb, (0, 0, 0))
                            b.spawn_random(get_occupied())
                            bombs.append(b)

                    if not star.active and current_time > star_end_time:
                        if random.random() < 0.15:
                            star.spawn_random(get_occupied())
                    apple.spawn_random(get_occupied())

                if cookie.active and head == cookie.position:
                    score += 50
                    sound_manager.play_bonus()
                    cookie.active = False

                if banana.active and head == banana.position:
                    score += 20
                    sound_manager.play_bonus()
                    banana.active = False

                if star.active and head == star.position:
                    sound_manager.play_powerup()
                    sound_manager.start_powerup_loop()
                    star_end_time = current_time + STAR_DURATION
                    star.active = False

                for b in bombs[:]:
                    if b.active and head == b.position:
                        sound_manager.play_explode()
                        if len(snake.body) <= 4:
                            snake.alive = False
                        else:
                            snake.shrink(4)
                        b.active = False
                        bombs.remove(b)

                for r in rocks:
                    if r.active and (head in r.footprint):
                        sound_manager.play_crash()
                        snake.alive = False

                if not snake.alive:
                    sound_manager.stop_powerup_loop()
                    current_state = STATE_GAMEOVER

            alpha = time_since_move / move_delay
            if alpha > 1.0:
                alpha = 1.0

        # 3. Drawing (Draw to Virtual Surface)
        if bg_image:
            game_surface.blit(bg_image, (0, 0))
        else:
            game_surface.fill(COLOR_BG)

        if snake.wrap_mode:
            pygame.draw.rect(
                game_surface, (255, 215, 0), (0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT), 5
            )
        else:
            pygame.draw.rect(
                game_surface, (50, 50, 50), (0, 0, VIRTUAL_WIDTH, VIRTUAL_HEIGHT), 2
            )

        if current_state == STATE_MENU:
            title_surf = font_title.render("Snake 2.0", True, (255, 105, 180))
            title_shadow = font_title.render("Snake 2.0", True, (100, 100, 100))
            game_surface.blit(
                title_shadow,
                (VIRTUAL_WIDTH // 2 - title_surf.get_width() // 2 + 3, 103),
            )
            game_surface.blit(
                title_surf, (VIRTUAL_WIDTH // 2 - title_surf.get_width() // 2, 100)
            )
            for btn in menu_buttons:
                btn.draw(game_surface)

        elif current_state == STATE_GAME:
            apple.draw(game_surface)
            cookie.draw(game_surface)
            banana.draw(game_surface)
            star.draw(game_surface)
            for b in bombs:
                b.draw(game_surface)
            for r in rocks:
                r.draw(game_surface)
            snake.draw(game_surface, alpha)

            score_text = font_score.render(f"Score: {score}", True, COLOR_TEXT)
            game_surface.blit(score_text, (20, 20))
            if current_time < star_end_time:
                remaining_sec = math.ceil((star_end_time - current_time) / 1000)
                timer_text = font_score.render(
                    f"Powerups : {remaining_sec}s", True, COLOR_TIMER
                )
                game_surface.blit(timer_text, (20, 55))

        elif current_state == STATE_PAUSE:
            apple.draw(game_surface)
            cookie.draw(game_surface)
            star.draw(game_surface)
            for b in bombs:
                b.draw(game_surface)
            for r in rocks:
                r.draw(game_surface)
            snake.draw(game_surface, 0.0)
            overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            game_surface.blit(overlay, (0, 0))
            status_text = font_title.render("Game Paused", True, (255, 255, 255))
            game_surface.blit(
                status_text, (VIRTUAL_WIDTH // 2 - status_text.get_width() // 2, 100)
            )
            for btn in pause_buttons:
                btn.draw(game_surface)

        elif current_state == STATE_INSTRUCTION:
            game_surface.fill((255, 253, 208))
            inst_title = font_title.render("How to Play", True, COLOR_TEXT)
            game_surface.blit(
                inst_title, (VIRTUAL_WIDTH // 2 - inst_title.get_width() // 2, 50)
            )
            lines = [
                "Arrows to Move. Eat Apples (+10 pts)",
                "Every 10 Apples: Cookies, Bananas & Bombs appear.",
                "STAR = 10s Wall Pass (Pass through walls!)",
                "Hit BOMB = Lose Tail (DIE if too short!).",
                "Hit ROCK = GAME OVER.",
                "ESC to Pause. F11 for Fullscreen.",
            ]
            for i, line in enumerate(lines):
                txt = font_inst.render(line, True, COLOR_TEXT)
                game_surface.blit(
                    txt, (VIRTUAL_WIDTH // 2 - txt.get_width() // 2, 150 + i * 40)
                )

        elif current_state == STATE_GAMEOVER:
            apple.draw(game_surface)
            for b in bombs:
                b.draw(game_surface)
            for r in rocks:
                r.draw(game_surface)
            snake.draw(game_surface, 1.0)
            overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
            overlay.fill((50, 0, 0, 128))
            game_surface.blit(overlay, (0, 0))
            msg1 = font_title.render("Game Over!", True, (255, 255, 0))
            msg2 = font_score.render(f"Final Score: {score}", True, (255, 255, 255))
            msg3 = font_inst.render("Press ENTER to Restart", True, (200, 200, 200))
            game_surface.blit(msg1, (VIRTUAL_WIDTH // 2 - msg1.get_width() // 2, 200))
            game_surface.blit(msg2, (VIRTUAL_WIDTH // 2 - msg2.get_width() // 2, 280))
            game_surface.blit(msg3, (VIRTUAL_WIDTH // 2 - msg3.get_width() // 2, 350))

        # --- Scale and Draw to Real Screen ---
        screen.fill(COLOR_LETTERBOX)  # Fill black bars

        real_w, real_h = screen.get_size()
        scale = min(real_w / VIRTUAL_WIDTH, real_h / VIRTUAL_HEIGHT)
        new_w = int(VIRTUAL_WIDTH * scale)
        new_h = int(VIRTUAL_HEIGHT * scale)

        scaled_surf = pygame.transform.scale(game_surface, (new_w, new_h))
        offset_x = (real_w - new_w) // 2
        offset_y = (real_h - new_h) // 2

        screen.blit(scaled_surf, (offset_x, offset_y))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
