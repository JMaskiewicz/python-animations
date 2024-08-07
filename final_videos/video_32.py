import pygame
import math
import random
import colorsys
import time
import io
from pydub import AudioSegment

# Constants
WIDTH, HEIGHT = 720, 1280
INITIAL_BALL_RADIUS = 80
RED_BALL_COLOR = (255, 0, 0)
BLUE_BALL_COLOR = (0, 0, 255)
BACKGROUND_COLOR = (0, 0, 0)
GREY = (30, 30, 30)
WHITE = (255, 255, 255)
GRAVITY = 0.2
FPS = 60
CIRCLE_RADIUS = 320

VELOCITY_DAMPING = 0.95  # Damping factor to avoid excessive speeds
COOLDOWN = 30  # Cooldown period to prevent multiple size adjustments
SPEED_INCREASE = 1.25  # Speed increase factor on each bounce off the circle
MAX_SPEED = 10  # Maximum speed limit for the balls

# Initialize pygame
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball Collision Simulation with Gravity and Size Changes")
clock = pygame.time.Clock()

# Load MP3 file
music_path = r'C:\Users\jmask\Downloads\09 All Star.mp3'
music = AudioSegment.from_mp3(music_path)


def play_music_segment(start_time, duration=0.33):
    segment = music[start_time * 1000:start_time * 1000 + duration * 1000]
    with io.BytesIO() as f:
        segment.export(f, format="wav")
        f.seek(0)
        pygame.mixer.Sound(f).play()


class Ball:
    def __init__(self, x, y, vx, vy, color):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.radius = INITIAL_BALL_RADIUS
        self.cooldown = 0  # Cooldown counter to prevent multiple adjustments
        self.bounce_count = 0

    def move(self):
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy
        if self.cooldown > 0:
            self.cooldown -= 1

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.radius))

    def limit_speed(self):
        speed = math.hypot(self.vx, self.vy)
        if speed > MAX_SPEED:
            self.vx = self.vx / speed * MAX_SPEED
            self.vy = self.vy / speed * MAX_SPEED

    def check_boundary_collision(self):
        dx = self.x - WIDTH // 2
        dy = self.y - HEIGHT // 2
        distance = math.hypot(dx, dy)
        if distance > CIRCLE_RADIUS - self.radius:
            if self.cooldown == 0:  # Check cooldown
                angle = math.atan2(dy, dx)
                self.vx = -self.vx
                self.vy = -self.vy

                # Correct the position
                overlap = distance - (CIRCLE_RADIUS - self.radius)
                self.x -= math.cos(angle) * overlap
                self.y -= math.sin(angle) * overlap

                # Ensure the ball is inside the boundary
                dx = self.x - WIDTH // 2
                dy = self.y - HEIGHT // 2
                distance = math.hypot(dx, dy)
                if distance > CIRCLE_RADIUS - self.radius:
                    angle = math.atan2(dy, dx)
                    self.x = WIDTH // 2 + (CIRCLE_RADIUS - self.radius - 1) * math.cos(angle)
                    self.y = HEIGHT // 2 + (CIRCLE_RADIUS - self.radius - 1) * math.sin(angle)

                # Adjust size based on collision with circle
                if self.color == BLUE_BALL_COLOR:
                    self.radius = min(self.radius * 1.1, 350)
                elif self.color == RED_BALL_COLOR:
                    self.radius *= 0.9

                self.cooldown = COOLDOWN  # Reset cooldown

                # Add random velocity variations
                self.vx += random.uniform(-0.5, 0.5)
                self.vy += random.uniform(-0.5, 0.5)

                # Increase speed
                speed = math.hypot(self.vx, self.vy)
                self.vx = self.vx / speed * (speed * SPEED_INCREASE)
                self.vy = self.vy / speed * (speed * SPEED_INCREASE)

                # Limit speed
                self.limit_speed()

                # Play sound on collision
                if self.color == RED_BALL_COLOR:
                    play_music_segment(self.bounce_count * 0.33)
                    self.bounce_count += 1

    def ensure_within_boundary(self):
        dx = self.x - WIDTH // 2
        dy = self.y - HEIGHT // 2
        distance = math.hypot(dx, dy)
        if distance > CIRCLE_RADIUS - self.radius:
            angle = math.atan2(dy, dx)
            self.x = WIDTH // 2 + (CIRCLE_RADIUS - self.radius - 1) * math.cos(angle)
            self.y = HEIGHT // 2 + (CIRCLE_RADIUS - self.radius - 1) * math.sin(angle)


def check_collision(ball1, ball2):
    dx = ball1.x - ball2.x
    dy = ball1.y - ball2.y
    distance = math.hypot(dx, dy)
    if distance < ball1.radius + ball2.radius:
        angle = math.atan2(dy, dx)
        total_mass = ball1.radius + ball2.radius

        # Normal velocities
        v1n = ball1.vx * math.cos(angle) + ball1.vy * math.sin(angle)
        v2n = ball2.vx * math.cos(angle) + ball2.vy * math.sin(angle)

        # Tangential velocities (unchanged)
        v1t = -ball1.vx * math.sin(angle) + ball1.vy * math.cos(angle)
        v2t = -ball2.vx * math.sin(angle) + ball2.vy * math.cos(angle)

        # New normal velocities after collision
        v1n_new = (v1n * (ball1.radius - ball2.radius) + 2 * ball2.radius * v2n) / total_mass
        v2n_new = (v2n * (ball2.radius - ball1.radius) + 2 * ball1.radius * v1n) / total_mass

        # Convert new normal and tangential velocities to x, y velocities
        ball1.vx = v1n_new * math.cos(angle) - v1t * math.sin(angle)
        ball1.vy = v1n_new * math.sin(angle) + v1t * math.cos(angle)
        ball2.vx = v2n_new * math.cos(angle) - v2t * math.sin(angle)
        ball2.vy = v2n_new * math.sin(angle) + v2t * math.cos(angle)

        # Apply damping
        ball1.vx *= VELOCITY_DAMPING
        ball1.vy *= VELOCITY_DAMPING
        ball2.vx *= VELOCITY_DAMPING
        ball2.vy *= VELOCITY_DAMPING

        # Add random velocity variations
        ball1.vx += random.uniform(-0.5, 0.5)
        ball1.vy += random.uniform(-0.5, 0.5)
        ball2.vx += random.uniform(-0.5, 0.5)
        ball2.vy += random.uniform(-0.5, 0.5)

        # Adjust sizes
        if ball1.color == BLUE_BALL_COLOR and ball2.color == RED_BALL_COLOR:
            ball1.radius *= 0.9
            ball2.radius = min(ball2.radius * 1.1, 350)
        elif ball1.color == RED_BALL_COLOR and ball2.color == BLUE_BALL_COLOR:
            ball1.radius = min(ball1.radius * 1.1, 350)
            ball2.radius *= 0.9

        # Separate the balls
        overlap = ball1.radius + ball2.radius - distance
        ball1.x += math.cos(angle) * overlap / 2
        ball1.y += math.sin(angle) * overlap / 2
        ball2.x -= math.cos(angle) * overlap / 2
        ball2.y -= math.sin(angle) * overlap / 2

        # Limit speed
        ball1.limit_speed()
        ball2.limit_speed()


# Create balls
ball1 = Ball(WIDTH // 2 - 125, HEIGHT // 2, 1, 1, RED_BALL_COLOR)
ball2 = Ball(WIDTH // 2 + 125, HEIGHT // 2, -1, -1, BLUE_BALL_COLOR)

# Main loop
running = True
game_over = False
end_message_start_time = 0
hue = 0.0
font, large_font = pygame.font.SysFont(None, 48), pygame.font.SysFont(None, 64)
start_timer = time.time()
show_end_message = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:
        screen.fill(BACKGROUND_COLOR)

        title_text = font.render("GUESS THE RULES?", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))

        # Move balls
        ball1.move()
        ball2.move()

        # Check collisions
        check_collision(ball1, ball2)
        ball1.check_boundary_collision()
        ball2.check_boundary_collision()

        # Ensure balls are within the circle boundary
        ball1.ensure_within_boundary()
        ball2.ensure_within_boundary()

        # Change circle color over time
        hue = (hue + 0.005) % 1.0
        rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        circle_color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))

        # Draw thinner circle with changing color
        pygame.draw.circle(screen, circle_color, (WIDTH // 2, HEIGHT // 2), CIRCLE_RADIUS, 10)

        # Draw balls
        ball1.draw(screen)
        ball2.draw(screen)

        # Add watermark text
        watermark_font = pygame.font.SysFont(None, 36)
        watermark_texts = [
            watermark_font.render("yt:@jbbm_motions", True, GREY),
            watermark_font.render("tiktok:@jbbm_motions", True, GREY),
            watermark_font.render("subscribe for more!", True, GREY),
            watermark_font.render("comment what to do next!", True, GREY),
        ]
        for idx, text in enumerate(watermark_texts):
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 1100 + idx * 30))

        pygame.display.flip()
        clock.tick(FPS)

        # Check if any ball reaches 250 radius
        if ball1.radius >= 230 or ball2.radius >= 230 and not show_end_message or time.time() - start_timer >= 50:
            show_end_message = True
            end_message_start_time = time.time()

        if show_end_message:
            # Display game over messages
            screen.fill(BACKGROUND_COLOR)
            large_font = pygame.font.SysFont(None, 72)
            game_over_texts = [
                large_font.render("LIKE", True, WHITE),
                large_font.render("FOLLOW", True, WHITE),
                large_font.render("SUBSCRIBE", True, WHITE),
                large_font.render("COMMENT WHAT TO DO NEXT", True, WHITE)
            ]
            for idx, text in enumerate(game_over_texts):
                screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 100 + 100 * idx))
            pygame.display.flip()

            if time.time() - end_message_start_time >= 3:
                running = False
                game_over = True

pygame.quit()
