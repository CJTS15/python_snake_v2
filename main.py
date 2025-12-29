import pygame
import sys
import random
import math

# --- Configuration & Constants ---
SCREEN_WIDTH = 810  
SCREEN_HEIGHT = 600
GRID_SIZE = 30  
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

# Colors
COLOR_BG = (240, 248, 255)
COLOR_TEXT = (50, 50, 80)
COLOR_BUTTON = (100, 149, 237)
COLOR_BUTTON_HOVER = (65, 105, 225)

# Game Speed Settings
START_MOVE_DELAY = 180  
DELAY_DECREMENT = 8     
MIN_MOVE_DELAY = 30     

# Event Settings
APPLES_FOR_EVENT = 10  # Every 10 apples, trigger event

# Initialize Pygame
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake 2.0")
clock = pygame.time.Clock()

# --- Asset Loading ---
sprites_loaded = False
try:
    # Existing assets
    raw_head = pygame.image.load("head.png").convert_alpha()
    raw_body = pygame.image.load("body.png").convert_alpha()
    raw_apple = pygame.image.load("apple.png").convert_alpha()
    raw_cookie = pygame.image.load("cookie.png").convert_alpha()
    raw_bomb = pygame.image.load("bomb.png").convert_alpha()

    # Scaling
    img_head = pygame.transform.scale(raw_head, (GRID_SIZE, GRID_SIZE))
    img_body = pygame.transform.scale(raw_body, (GRID_SIZE + 4, GRID_SIZE + 4)) 
    img_apple = pygame.transform.scale(raw_apple, (GRID_SIZE, GRID_SIZE))
    img_cookie = pygame.transform.scale(raw_cookie, (GRID_SIZE, GRID_SIZE))
    img_bomb = pygame.transform.scale(raw_bomb, (GRID_SIZE, GRID_SIZE))
    
    sprites_loaded = True
except FileNotFoundError:
    print("One or more images not found. Using fallback shapes.")

# --- Sound Manager ---
class SoundManager:
    def __init__(self):
        self.sounds_enabled = True
        try:
            # self.snd_eat = pygame.mixer.Sound('eat.wav')
            pass
        except:
            self.sounds_enabled = False

    def play_eat(self):
        if self.sounds_enabled:
            pygame.mixer.Sound('eat.wav').play()
            pass 

    def play_crash(self):
        if self.sounds_enabled:
            pygame.mixer.Sound('crash.wav').play()
            pass
    def play_bonus(self):
        if self.sounds_enabled:
            pygame.mixer.Sound('bonus.wav').play()
            pass
    def play_explode(self):
        if self.sounds_enabled:
            pygame.mixer.Sound('explode.wav').play()
            pass

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
        mouse_pos = pygame.mouse.get_pos()
        current_color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(surface, current_color, self.rect, border_radius=15)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 3, border_radius=15)
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

# --- Game Classes ---
class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        self.body = [(GRID_WIDTH // 2, GRID_HEIGHT // 2), 
                     (GRID_WIDTH // 2 - 1, GRID_HEIGHT // 2), 
                     (GRID_WIDTH // 2 - 2, GRID_HEIGHT // 2),
                     (GRID_WIDTH // 2 - 3, GRID_HEIGHT // 2)]
        
        self.prev_body = list(self.body)
        self.direction = (1, 0)
        self.new_direction = (1, 0)
        self.grow = False
        self.alive = True

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
        """Removes 'amount' segments from the tail."""
        current_len = len(self.body)
        # Keep at least the head
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

        if new_head[0] < 0 or new_head[0] >= GRID_WIDTH or new_head[1] < 0 or new_head[1] >= GRID_HEIGHT:
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
        wiggle_amp = 8.0 
        wiggle_freq = 1.25
        wiggle_speed = 0.005

        for i in range(len(self.body) - 1, -1, -1):
            curr_x, curr_y = self.body[i]
            
            if i < len(self.prev_body):
                prev_x, prev_y = self.prev_body[i]
            else:
                prev_x, prev_y = curr_x, curr_y

            exact_x = prev_x * GRID_SIZE + (curr_x * GRID_SIZE - prev_x * GRID_SIZE) * interpolation_alpha
            exact_y = prev_y * GRID_SIZE + (curr_y * GRID_SIZE - prev_y * GRID_SIZE) * interpolation_alpha

            if i > 0:
                wave = math.sin(i * wiggle_freq - time_ticks * wiggle_speed) * wiggle_amp
            else:
                wave = 0
            
            if i == 0:
                dx, dy = self.direction
            else:
                p_x, p_y = self.body[i-1]
                dx = p_x - curr_x
                dy = p_y - curr_y

            if dx != 0: exact_y += wave
            else:       exact_x += wave

            if sprites_loaded:
                if i == 0:
                    angle = 0
                    if self.direction == (1, 0): angle = -90
                    elif self.direction == (-1, 0): angle = 90
                    elif self.direction == (0, 1): angle = 180
                    elif self.direction == (0, -1): angle = 0
                    
                    rotated_head = pygame.transform.rotate(img_head, angle)
                    rect = rotated_head.get_rect(center=(exact_x + GRID_SIZE/2, exact_y + GRID_SIZE/2))
                    surface.blit(rotated_head, rect)
                else:
                    offset = (img_body.get_width() - GRID_SIZE) / 2
                    surface.blit(img_body, (exact_x - offset, exact_y - offset))
            else:
                pygame.draw.circle(surface, (50, 205, 50), 
                                   (int(exact_x + GRID_SIZE/2), int(exact_y + GRID_SIZE/2)), 
                                   GRID_SIZE//2 + 1)

class Item:
    def __init__(self, img_sprite=None, fallback_color=(255, 255, 255)):
        self.position = (-1, -1)
        self.active = False
        self.sprite = img_sprite
        self.color = fallback_color
    
    def spawn_random(self, occupied_positions):
        # Limit attempts to prevent infinite loops if screen is full
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
        if not self.active: return
        
        x, y = self.position
        pos_x = x * GRID_SIZE
        pos_y = y * GRID_SIZE
        
        bob = math.sin(pygame.time.get_ticks() * 0.005) * 4

        if sprites_loaded and self.sprite:
            surface.blit(self.sprite, (pos_x, pos_y + bob))
        else:
            center = (pos_x + GRID_SIZE // 2, int(pos_y + GRID_SIZE // 2 + bob))
            pygame.draw.circle(surface, self.color, center, GRID_SIZE // 2)

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
    cookie = Item(img_cookie, (210, 180, 140))
    
    bombs = [] 
    
    score = 0
    move_delay = START_MOVE_DELAY
    last_move_time = pygame.time.get_ticks()
    apples_eaten_count = 0 
    
    font_score = pygame.font.SysFont("comicsansms", 30, bold=True)
    font_title = pygame.font.SysFont("comicsansms", 72, bold=True)
    font_inst = pygame.font.SysFont("comicsansms", 26)
    
    btn_w, btn_h = 200, 50
    cx = SCREEN_WIDTH // 2 - btn_w // 2
    
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
        if apple.active: occ.add(apple.position)
        if cookie.active: occ.add(cookie.position)
        for b in bombs:
            if b.active: occ.add(b.position)
        return occ

    running = True
    while running:
        current_time = pygame.time.get_ticks()

        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if current_state == STATE_GAME:
                snake.handle_input(event)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    current_state = STATE_PAUSE
            
            elif current_state == STATE_MENU:
                for btn in menu_buttons:
                    if btn.is_clicked(event):
                        if btn.action_code == "new":
                            snake.reset()
                            score = 0
                            move_delay = START_MOVE_DELAY
                            last_move_time = current_time
                            apples_eaten_count = 0
                            bombs = []
                            cookie.active = False
                            apple.spawn_random(get_occupied())
                            current_state = STATE_GAME
                        elif btn.action_code == "inst":
                            current_state = STATE_INSTRUCTION
                        elif btn.action_code == "quit":
                            running = False
                            
            elif current_state == STATE_PAUSE:
                for btn in pause_buttons:
                    if btn.is_clicked(event):
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
                            cookie.active = False
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
                        cookie.active = False
                        apple.spawn_random(get_occupied())
                        current_state = STATE_GAME
                    elif event.key == pygame.K_ESCAPE:
                        current_state = STATE_MENU

        # 2. Logic Update
        alpha = 0.0
        
        if current_state == STATE_GAME:
            time_since_move = current_time - last_move_time
            if time_since_move >= move_delay:
                snake.update_logic()
                last_move_time = current_time
                time_since_move = 0
                
                head = snake.body[0]
                
                # A. Apple Collision
                if head == apple.position:
                    snake.grow = True
                    score += 10
                    sound_manager.play_eat()
                    move_delay = max(MIN_MOVE_DELAY, move_delay - DELAY_DECREMENT)
                    
                    # --- EVENT LOGIC ---
                    apples_eaten_count += 1
                    
                    # Modulo operator checks if count is 10, 20, 30, etc.
                    if apples_eaten_count % APPLES_FOR_EVENT == 0:
                        
                        # 1. Spawn Cookie
                        cookie.spawn_random(get_occupied())
                        
                        # 2. Spawn 2 NEW Bombs (Adding to the existing ones)
                        for _ in range(2):
                            b = Item(img_bomb, (0, 0, 0))
                            b.spawn_random(get_occupied())
                            bombs.append(b)
                            
                    apple.spawn_random(get_occupied())

                # B. Cookie Collision
                if cookie.active and head == cookie.position:
                    score += 50
                    sound_manager.play_bonus()
                    cookie.active = False
                
                # C. Bomb Collision
                for b in bombs[:]: 
                    if b.active and head == b.position:
                        sound_manager.play_explode()
                        snake.shrink(4) # Lose 4 body parts
                        b.active = False
                        bombs.remove(b)

                if not snake.alive:
                    current_state = STATE_GAMEOVER
            
            alpha = time_since_move / move_delay
            if alpha > 1.0: alpha = 1.0

        # 3. Drawing
        screen.fill(COLOR_BG)

        for x in range(0, SCREEN_WIDTH + 1, GRID_SIZE):
            pygame.draw.line(screen, (230, 230, 250), (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT + 1, GRID_SIZE):
            pygame.draw.line(screen, (230, 230, 250), (0, y), (SCREEN_WIDTH, y))

        if current_state == STATE_MENU:
            title_surf = font_title.render("Snake 2.0", True, (255, 105, 180))
            title_shadow = font_title.render("Snake 2.0", True, (100, 100, 100))
            screen.blit(title_shadow, (SCREEN_WIDTH//2 - title_surf.get_width()//2 + 3, 103))
            screen.blit(title_surf, (SCREEN_WIDTH//2 - title_surf.get_width()//2, 100))
            for btn in menu_buttons:
                btn.draw(screen)

        elif current_state == STATE_GAME:
            apple.draw(screen)
            cookie.draw(screen)
            for b in bombs:
                b.draw(screen)
            snake.draw(screen, alpha)
            score_text = font_score.render(f"Score: {score}", True, COLOR_TEXT)
            screen.blit(score_text, (20, 20))

        elif current_state == STATE_PAUSE:
            apple.draw(screen)
            cookie.draw(screen)
            for b in bombs: b.draw(screen)
            snake.draw(screen, 0.0)
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            screen.blit(overlay, (0, 0))
            status_text = font_title.render("Game Paused", True, (255, 255, 255))
            screen.blit(status_text, (SCREEN_WIDTH//2 - status_text.get_width()//2, 100))
            for btn in pause_buttons:
                btn.draw(screen)

        elif current_state == STATE_INSTRUCTION:
            screen.fill((255, 253, 208)) 
            inst_title = font_title.render("How to Play", True, COLOR_TEXT)
            screen.blit(inst_title, (SCREEN_WIDTH//2 - inst_title.get_width()//2, 50))
            lines = [
                "Arrows to Move.",
                "Eat Apples (+10 pts) & Speed Up.",
                "Every 10 Apples:",
                "  -> A COOKIE appears (+50 pts).",
                "  -> 2 NEW BOMBS appear (They stack!)",
                "Hit a BOMB to lose tail.",
                "Don't hit walls or yourself!",
                "ESC to Pause."
            ]
            for i, line in enumerate(lines):
                txt = font_inst.render(line, True, COLOR_TEXT)
                screen.blit(txt, (SCREEN_WIDTH//2 - txt.get_width()//2, 150 + i * 40))

        elif current_state == STATE_GAMEOVER:
            apple.draw(screen)
            for b in bombs: b.draw(screen)
            snake.draw(screen, 1.0)
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((50, 0, 0, 128))
            screen.blit(overlay, (0, 0))
            msg1 = font_title.render("Game Over!", True, (255, 255, 0))
            msg2 = font_score.render(f"Final Score: {score}", True, (255, 255, 255))
            msg3 = font_inst.render("Press ENTER to Restart", True, (200, 200, 200))
            screen.blit(msg1, (SCREEN_WIDTH//2 - msg1.get_width()//2, 200))
            screen.blit(msg2, (SCREEN_WIDTH//2 - msg2.get_width()//2, 280))
            screen.blit(msg3, (SCREEN_WIDTH//2 - msg3.get_width()//2, 350))

        pygame.display.flip()
        clock.tick(60) 

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()