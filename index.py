import pygame
import random
import math
import sys
from pygame import mixer

# Initialize pygame
pygame.init()
mixer.init()

# Detect platform
is_mobile = any([
    pygame.display.get_driver() == 'android',
    pygame.display.get_driver() == 'ios',
    hasattr(sys, 'getandroidapilevel')
])

# Screen dimensions - responsive based on device
if is_mobile:
    info = pygame.display.Info()
    WIDTH, HEIGHT = info.current_w, info.current_h
else:
    WIDTH, HEIGHT = 800, 600

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE if not is_mobile else 0)
pygame.display.set_caption("Space Shooter")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 150, 255)
YELLOW = (255, 255, 0)
PURPLE = (180, 70, 255)
CYAN = (0, 255, 255)

# Scaling factors for different screen sizes
SCALE = min(WIDTH / 800, HEIGHT / 600)
FONT_SIZE = int(36 * SCALE)

# Load sounds (replace with your files if available)
try:
    shoot_sound = mixer.Sound("shoot.wav")
    explosion_sound = mixer.Sound("explosion.wav")
    powerup_sound = mixer.Sound("powerup.wav")
    mixer.music.load("background.mp3")
    mixer.music.play(-1)
except:
    shoot_sound = explosion_sound = powerup_sound = None

# Player
class Player:
    def __init__(self):
        self.width = 50 * SCALE
        self.height = 40 * SCALE
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT - self.height - (20 * SCALE)
        self.speed = 5 * SCALE
        self.color = BLUE
        self.shoot_cooldown = 0
        self.health = 500
        self.max_health = 500
        self.lives = 3
        self.rapid_fire = False
        self.rapid_timer = 0
        self.shield_active = False
        self.shield_timer = 0

    def draw(self):
        pygame.draw.polygon(screen, self.color, [
            (self.x + self.width // 2, self.y),
            (self.x, self.y + self.height),
            (self.x + self.width, self.y + self.height)
        ])
        glow_size = random.randint(int(5 * SCALE), int(10 * SCALE))
        pygame.draw.polygon(screen, YELLOW, [
            (self.x + self.width // 2 - (10 * SCALE), self.y + self.height),
            (self.x + self.width // 2, self.y + self.height + glow_size),
            (self.x + self.width // 2 + (10 * SCALE), self.y + self.height)
        ])
        
        # Draw shield if active
        if self.shield_active:
            shield_radius = max(self.width, self.height) + (5 * SCALE)
            shield_surface = pygame.Surface((int(shield_radius*2), int(shield_radius*2)), pygame.SRCALPHA)
            pygame.draw.circle(shield_surface, (100, 200, 255, 150), 
                              (int(shield_radius), int(shield_radius)), int(shield_radius))
            screen.blit(shield_surface, (self.x + self.width//2 - shield_radius, 
                                        self.y + self.height//2 - shield_radius))

    def move(self, dx, dy):
        self.x = max(0, min(WIDTH - self.width, self.x + dx * self.speed))
        self.y = max(0, min(HEIGHT - self.height, self.y + dy * self.speed))

    def update(self):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.rapid_fire:
            self.rapid_timer -= 1
            if self.rapid_timer <= 0:
                self.rapid_fire = False
        
        # Update shield timer
        if self.shield_active:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield_active = False

    # Activate shield power-up
    def activate_shield(self, duration=500):
        self.shield_active = True
        self.shield_timer = duration
        if powerup_sound: powerup_sound.play()

    # Normal single bullet shoot
    def shoot(self, bullets):
        if self.shoot_cooldown == 0:
            bullets.append(Bullet(self.x + self.width // 2, self.y, SCALE))
            self.shoot_cooldown = 5 if self.rapid_fire else 15
            if shoot_sound: shoot_sound.play()
            return True
        return False

    # Burst fire: 10 bullets at once
    def burst_shoot(self, bullets):
        for i in range(10):
            bullets.append(Bullet(self.x + self.width // 2, self.y - i * (10 * SCALE), SCALE))
        if shoot_sound: shoot_sound.play()

# Bullet
class Bullet:
    def __init__(self, x, y, scale):
        self.x = x
        self.y = y
        self.radius = 4 * scale
        self.speed = 7 * scale
        self.color = GREEN

    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.radius))

    def move(self):
        self.y -= self.speed

    def off_screen(self):
        return self.y < 0

# Enemy
class Enemy:
    def __init__(self, scale):
        self.width = 40 * scale
        self.height = 40 * scale
        self.x = random.randint(int(20 * scale), int(WIDTH - self.width - (20 * scale)))
        self.y = random.randint(int(-100 * scale), int(-40 * scale))
        self.speed = random.uniform(1.0, 3.0) * scale
        self.color = RED
        self.direction = random.choice([-1, 1])
        self.oscillation_speed = random.uniform(0.5, 1.5)

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, PURPLE, 
                        (self.x + (5 * SCALE), self.y + (5 * SCALE), 
                         self.width - (10 * SCALE), self.height - (10 * SCALE)))

    def move(self):
        self.y += self.speed
        self.x += math.sin(pygame.time.get_ticks() * 0.001 * self.oscillation_speed) * self.direction * (2 * SCALE)

    def off_screen(self):
        return self.y > HEIGHT

    def collides_with(self, bullet):
        return (self.x < bullet.x < self.x + self.width and
                self.y < bullet.y < self.y + self.height)
                
    def collides_with_player(self, player):
        return (self.x < player.x + player.width and
                self.x + self.width > player.x and
                self.y < player.y + player.height and
                self.y + self.height > player.y)

# Power-up class
class PowerUp:
    def __init__(self, scale):
        self.width = 30 * scale
        self.height = 30 * scale
        self.x = random.randint(int(20 * scale), int(WIDTH - self.width - (20 * scale)))
        self.y = random.randint(int(-100 * scale), int(-40 * scale))
        self.speed = 2.0 * scale
        self.type = random.choice(["shield", "rapid_fire", "health"])
        self.colors = {
            "shield": CYAN,
            "rapid_fire": YELLOW,
            "health": GREEN
        }

    def draw(self):
        pygame.draw.rect(screen, self.colors[self.type], (self.x, self.y, self.width, self.height))
        # Draw a symbol based on power-up type
        if self.type == "shield":
            pygame.draw.circle(screen, WHITE, 
                              (int(self.x + self.width//2), int(self.y + self.height//2)), 
                              int(8 * SCALE), int(2 * SCALE))
        elif self.type == "rapid_fire":
            pygame.draw.polygon(screen, WHITE, [
                (self.x + self.width//2, self.y + (8 * SCALE)),
                (self.x + (8 * SCALE), self.y + self.height - (8 * SCALE)),
                (self.x + self.width - (8 * SCALE), self.y + self.height - (8 * SCALE))
            ])
        elif self.type == "health":
            pygame.draw.rect(screen, WHITE, 
                            (self.x + (8 * SCALE), self.y + (8 * SCALE), 
                             self.width - (16 * SCALE), self.height - (16 * SCALE)))

    def move(self):
        self.y += self.speed

    def off_screen(self):
        return self.y > HEIGHT

    def collides_with_player(self, player):
        return (self.x < player.x + player.width and
                self.x + self.width > player.x and
                self.y < player.y + player.height and
                self.y + self.height > player.y)

# Star background
class Star:
    def __init__(self, width, height):
        self.x = random.randint(0, width)
        self.y = random.randint(0, height)
        self.size = random.uniform(0.5, 2) * SCALE
        self.speed = random.uniform(0.5, 1.5) * SCALE
        self.brightness = random.randint(150, 255)

    def draw(self):
        color = (self.brightness, self.brightness, self.brightness)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)

    def move(self):
        self.y += self.speed
        if self.y > HEIGHT:
            self.y = 0
            self.x = random.randint(0, WIDTH)

# Explosion
class Explosion:
    def __init__(self, x, y, scale):
        self.x = x
        self.y = y
        self.radius = 5 * scale
        self.max_radius = 30 * scale
        self.growth_rate = 2 * scale
        self.color = YELLOW
        self.alpha = 255

    def draw(self):
        if self.radius < self.max_radius:
            self.radius += self.growth_rate
        else:
            self.alpha -= 15
        s = pygame.Surface((int(self.radius*2), int(self.radius*2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, self.alpha), 
                          (int(self.radius), int(self.radius)), int(self.radius))
        screen.blit(s, (self.x - self.radius, self.y - self.radius))

    def is_done(self):
        return self.alpha <= 0

# Touch Control Button
class TouchButton:
    def __init__(self, x, y, width, height, color, text="", alpha=150):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.text = text
        self.alpha = alpha
        self.rect = pygame.Rect(x, y, width, height)
        
    def draw(self):
        s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        s.fill((*self.color, self.alpha))
        screen.blit(s, (self.x, self.y))
        
        if self.text:
            font = pygame.font.SysFont(None, int(30 * SCALE))
            text_surface = font.render(self.text, True, WHITE)
            text_rect = text_surface.get_rect(center=(self.x + self.width//2, self.y + self.height//2))
            screen.blit(text_surface, text_rect)
            
    def is_pressed(self, pos):
        return self.rect.collidepoint(pos)

# Game
class Game:
    def __init__(self):
        self.player = Player()
        self.bullets = []
        self.enemies = []
        self.powerups = []
        self.stars = [Star(WIDTH, HEIGHT) for _ in range(100)]
        self.explosions = []
        self.score = 0
        self.font = pygame.font.SysFont(None, FONT_SIZE)
        self.small_font = pygame.font.SysFont(None, int(24 * SCALE))
        self.game_over = False
        
        # Create touch controls for mobile
        self.touch_controls = []
        if is_mobile:
            btn_size = 60 * SCALE
            padding = 20 * SCALE
            
            # Movement buttons (left side)
            self.move_up = TouchButton(padding, HEIGHT - btn_size*3 - padding*2, btn_size, btn_size, BLUE, "↑")
            self.move_left = TouchButton(padding, HEIGHT - btn_size*2 - padding, btn_size, btn_size, BLUE, "←")
            self.move_down = TouchButton(padding, HEIGHT - btn_size - padding, btn_size, btn_size, BLUE, "↓")
            self.move_right = TouchButton(btn_size + padding*2, HEIGHT - btn_size*2 - padding, btn_size, btn_size, BLUE, "→")
            
            # Action buttons (right side)
            self.shoot_btn = TouchButton(WIDTH - btn_size - padding, HEIGHT - btn_size*2 - padding, btn_size, btn_size, RED, "FIRE")
            self.burst_btn = TouchButton(WIDTH - btn_size*2 - padding*2, HEIGHT - btn_size*2 - padding, btn_size, btn_size, GREEN, "BURST")
            
            self.touch_controls.extend([
                self.move_up, self.move_left, self.move_down, self.move_right,
                self.shoot_btn, self.burst_btn
            ])
            
            # Restart button for game over
            self.restart_btn = TouchButton(WIDTH//2 - 100*SCALE, HEIGHT//2 + 50*SCALE, 200*SCALE, 60*SCALE, GREEN, "RESTART")

    def update(self):
        if self.game_over:
            return
        self.player.update()
        
        # Update bullets
        for bullet in self.bullets[:]:
            bullet.move()
            if bullet.off_screen():
                self.bullets.remove(bullet)
                
        # Update enemies
        for enemy in self.enemies[:]:
            enemy.move()
            if enemy.off_screen():
                self.enemies.remove(enemy)
                
            # Check collision with bullets
            for bullet in self.bullets[:]:
                if enemy.collides_with(bullet):
                    self.explosions.append(Explosion(enemy.x + enemy.width//2, enemy.y + enemy.height//2, SCALE))
                    self.enemies.remove(enemy)
                    self.bullets.remove(bullet)
                    self.score += 10
                    if explosion_sound: explosion_sound.play()
                    break
                    
            # Check collision with player
            if enemy.collides_with_player(self.player):
                if not self.player.shield_active:
                    self.player.health -= 50
                    if self.player.health <= 0:
                        self.player.lives -= 1
                        self.player.health = self.player.max_health
                        if self.player.lives <= 0:
                            self.game_over = True
                self.explosions.append(Explosion(enemy.x + enemy.width//2, enemy.y + enemy.height//2, SCALE))
                self.enemies.remove(enemy)
                if explosion_sound: explosion_sound.play()
                
        # Update power-ups
        for powerup in self.powerups[:]:
            powerup.move()
            if powerup.off_screen():
                self.powerups.remove(powerup)
                
            # Check collision with player
            if powerup.collides_with_player(self.player):
                if powerup.type == "shield":
                    self.player.activate_shield(500)
                elif powerup.type == "rapid_fire":
                    self.player.rapid_fire = True
                    self.player.rapid_timer = 500
                elif powerup.type == "health":
                    self.player.health = min(self.player.max_health, self.player.health + 100)
                self.powerups.remove(powerup)
        
        # Update explosions
        for explosion in self.explosions[:]:
            explosion.draw()
            if explosion.is_done():
                self.explosions.remove(explosion)
                
        # Update stars
        for star in self.stars:
            star.move()
            
        # Spawn enemies randomly
        if random.random() < 0.02:
            self.enemies.append(Enemy(SCALE))
            
        # Spawn power-ups randomly
        if random.random() < 0.005:
            self.powerups.append(PowerUp(SCALE))

    def draw(self):
        screen.fill(BLACK)
        for star in self.stars: star.draw()
        self.player.draw()
        for bullet in self.bullets: bullet.draw()
        for enemy in self.enemies: enemy.draw()
        for powerup in self.powerups: powerup.draw()
        
        # Draw UI elements
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10 * SCALE, 10 * SCALE))
        
        # Draw health bar
        health_width = 200 * SCALE
        health_height = 20 * SCALE
        pygame.draw.rect(screen, RED, (10 * SCALE, 50 * SCALE, health_width, health_height))
        pygame.draw.rect(screen, GREEN, (10 * SCALE, 50 * SCALE, 
                                       health_width * (self.player.health / self.player.max_health), health_height))
        pygame.draw.rect(screen, WHITE, (10 * SCALE, 50 * SCALE, health_width, health_height), 2)
        
        # Draw lives
        lives_text = self.font.render(f"Lives: {self.player.lives}", True, WHITE)
        screen.blit(lives_text, (WIDTH - lives_text.get_width() - (10 * SCALE), 10 * SCALE))
        
        # Draw power-up status
        if self.player.shield_active:
            shield_text = self.small_font.render("Shield Active!", True, CYAN)
            screen.blit(shield_text, (WIDTH - shield_text.get_width() - (10 * SCALE), 50 * SCALE))
        if self.player.rapid_fire:
            rapid_text = self.small_font.render("Rapid Fire!", True, YELLOW)
            screen.blit(rapid_text, (WIDTH - rapid_text.get_width() - (10 * SCALE), 75 * SCALE))
            
        # Draw touch controls for mobile
        if is_mobile:
            for control in self.touch_controls:
                control.draw()
            
        if self.game_over:
            # Semi-transparent overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            
            game_over_text = self.font.render("GAME OVER", True, RED)
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 50))
            
            score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
            screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
            
            if is_mobile:
                self.restart_btn.draw()
            else:
                restart_text = self.font.render("Press R to Restart", True, GREEN)
                screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 50))

# Main
game = Game()
clock = pygame.time.Clock()
running = True

# For touch controls
touch_id = None
movement = [0, 0]  # [dx, dy]

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        # Handle window resize
        elif event.type == pygame.VIDEORESIZE and not is_mobile:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            SCALE = min(WIDTH / 800, HEIGHT / 600)
            
        # Handle keyboard events
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not game.game_over:
                game.player.burst_shoot(game.bullets)
            elif event.key == pygame.K_r and game.game_over:
                game = Game()
                
        # Handle touch events for mobile
        elif is_mobile and event.type == pygame.FINGERDOWN:
            x, y = event.x * WIDTH, event.y * HEIGHT
            if game.game_over and game.restart_btn.is_pressed((x, y)):
                game = Game()
            else:
                for control in game.touch_controls:
                    if control.is_pressed((x, y)):
                        touch_id = event.finger_id
                        if control == game.shoot_btn:
                            game.player.shoot(game.bullets)
                        elif control == game.burst_btn:
                            game.player.burst_shoot(game.bullets)
                        elif control == game.move_up:
                            movement[1] = -1
                        elif control == game.move_down:
                            movement[1] = 1
                        elif control == game.move_left:
                            movement[0] = -1
                        elif control == game.move_right:
                            movement[0] = 1
                        break
                            
        elif is_mobile and event.type == pygame.FINGERUP:
            if event.finger_id == touch_id:
                movement = [0, 0]
                touch_id = None
                
        elif is_mobile and event.type == pygame.FINGERMOTION and event.finger_id == touch_id:
            # You could implement joystick-like movement here if desired
            pass

    # Handle keyboard movement
    keys = pygame.key.get_pressed()
    dx, dy = 0, 0
    if keys[pygame.K_LEFT]: dx -= 1
    if keys[pygame.K_RIGHT]: dx += 1
    if keys[pygame.K_UP]: dy -= 1
    if keys[pygame.K_DOWN]: dy += 1
    
    # Use touch movement if available
    if is_mobile and touch_id is not None:
        dx, dy = movement
    
    # Apply movement
    if not game.game_over:
        game.player.move(dx, dy)
        
        # Autoshoot if SPACE is held down (keyboard)
        if keys[pygame.K_SPACE]:
            game.player.shoot(game.bullets)

    if not game.game_over:
        game.update()

    game.draw()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()