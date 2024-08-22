import pygame
import math
import random
import colorsys
import time
import io
from pydub import AudioSegment

# Constants
WIDTH, HEIGHT = 720, 1280
INITIAL_BALL_RADIUS = 10
RED_BALL_COLOR = (200, 0, 0)
BLUE_BALL_COLOR = (0, 100, 255)
BACKGROUND_COLOR = (0, 0, 0)
GREY = (30, 30, 30)
WHITE = (255, 255, 255)
GRAVITY = 0
FPS = 60
CIRCLE_RADIUS = 80  # Smaller radius for the moving circle
WHITE_CIRCLE_RADIUS = 30  # Initial radius for the white circle
CIRCLE_VX = 3  # Slower horizontal velocity of the moving circle
CIRCLE_VY = 3  # Slower vertical velocity of the moving circle
WHITE_CIRCLE_VX = 4  # Speed of the white circle
WHITE_CIRCLE_VY = 4
WHITE_CIRCLE_BORDER_THICKNESS = 10  # Thickness of the white circle's border

VELOCITY_DAMPING = 1
COOLDOWN = 20
SPEED_INCREASE = 1
MAX_SPEED = 10
MAX_BALLS = 10000  # Maximum number of balls to prevent overflow

# Initialize pygame
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball Collision Simulation with Moving Circle")
clock = pygame.time.Clock()

# Load sound
pop_sound = pygame.mixer.Sound(r'C:\Users\jmask\Downloads\pop-39222.mp3')

class Ball:
    def __init__(self, x, y, vx, vy, color):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.radius = INITIAL_BALL_RADIUS
        self.cooldown = 0
        self.spawn_cooldown = 0  # Cooldown for spawning new balls
        self.bounce_count = 0

    def move(self):
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy
        if self.cooldown > 0:
            self.cooldown -= 1
        if self.spawn_cooldown > 0:
            self.spawn_cooldown -= 1

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.radius))

    def limit_speed(self):
        speed = math.hypot(self.vx, self.vy)
        if speed > MAX_SPEED:
            self.vx = self.vx / speed * MAX_SPEED
            self.vy = self.vy / speed * MAX_SPEED

    def check_boundary_collision(self, circle, balls, sparks):
        dx = self.x - circle.x
        dy = self.y - circle.y
        distance = math.hypot(dx, dy)
        if distance < CIRCLE_RADIUS + self.radius:
            if self.cooldown == 0:
                angle = math.atan2(dy, dx)
                random_angle = random.uniform(0, 2 * math.pi)
                self.vx = math.cos(random_angle) * MAX_SPEED
                self.vy = math.sin(random_angle) * MAX_SPEED

                self.cooldown = COOLDOWN

                # Adjust position to avoid sticking inside the circle
                overlap = (CIRCLE_RADIUS + self.radius) - distance
                self.x += math.cos(angle) * overlap
                self.y += math.sin(angle) * overlap

                # Create sparks at the point of collision
                for _ in range(10):
                    spark_vx = random.uniform(-3, 3)
                    spark_vy = random.uniform(-3, 3)
                    sparks.append(Spark(self.x, self.y, spark_vx, spark_vy, self.color))

                # Play sound on collision
                pop_sound.play()

                # Spawn a new ball outside the circle, but only if the cooldown allows it
                if len(balls) < MAX_BALLS and self.spawn_cooldown == 0:
                    self.spawn_ball_outside_circle(circle, balls)
                    self.spawn_cooldown = FPS * 0.25  # Set cooldown for 3 seconds

    def spawn_ball_outside_circle(self, circle, balls):
        angle = random.uniform(0, 2 * math.pi)
        distance = CIRCLE_RADIUS + INITIAL_BALL_RADIUS + 20  # Ensure the ball starts outside the circle
        new_ball_x = circle.x + math.cos(angle) * distance
        new_ball_y = circle.y + math.sin(angle) * distance
        new_ball_vx = math.cos(angle) * MAX_SPEED / 2
        new_ball_vy = math.sin(angle) * MAX_SPEED / 2
        new_ball_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        # Create the new ball with a cooldown
        new_ball = Ball(new_ball_x, new_ball_y, new_ball_vx, new_ball_vy, new_ball_color)
        new_ball.spawn_cooldown = FPS * 0.25  # Set cooldown for the newly spawned ball
        balls.append(new_ball)

    def ensure_within_boundary(self):
        # Boundary checks and position correction to prevent sticking
        if self.x < self.radius:
            self.x = self.radius
            self.vx *= -1
        if self.x > WIDTH - self.radius:
            self.x = WIDTH - self.radius
            self.vx *= -1
        if self.y < self.radius:
            self.y = self.radius
            self.vy *= -1
        if self.y > HEIGHT - self.radius:
            self.y = HEIGHT - self.radius
            self.vy *= -1

        # Ensure the ball is not inside the circle after movement
        self.ensure_outside_circle(circle)

    def ensure_outside_circle(self, circle):
        # Check if the ball is inside the circle and move it outside if necessary
        dx = self.x - circle.x
        dy = self.y - circle.y
        distance = math.hypot(dx, dy)
        if distance < CIRCLE_RADIUS + self.radius:
            # Calculate the angle and reposition the ball outside the circle
            angle = math.atan2(dy, dx)
            self.x = circle.x + math.cos(angle) * (CIRCLE_RADIUS + self.radius)
            self.y = circle.y + math.sin(angle) * (CIRCLE_RADIUS + self.radius)

            # Apply a force to push the ball away from the center of the circle
            force_magnitude = 2  # Adjust the magnitude of the force as needed
            self.vx += math.cos(angle) * force_magnitude
            self.vy += math.sin(angle) * force_magnitude


class Spark:
    def __init__(self, x, y, vx, vy, color, lifespan=30):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifespan = lifespan

    def move(self):
        self.x += self.vx
        self.y += self.vy
        self.lifespan -= 1

    def draw(self, screen):
        if self.lifespan > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 3)


def check_collision(ball1, ball2, sparks):
    dx = ball1.x - ball2.x
    dy = ball1.y - ball2.y
    distance = math.hypot(dx, dy)
    if distance < ball1.radius + ball2.radius:
        pop_sound.play()
        angle = math.atan2(dy, dx)
        total_mass = ball1.radius + ball2.radius

        v1n = ball1.vx * math.cos(angle) + ball1.vy * math.sin(angle)
        v2n = ball2.vx * math.cos(angle) + ball2.vy * math.sin(angle)
        v1t = -ball1.vx * math.sin(angle) + ball1.vy * math.cos(angle)
        v2t = -ball2.vx * math.sin(angle) + ball2.vy * math.cos(angle)

        v1n_new = (v1n * (ball1.radius - ball2.radius) + 2 * ball2.radius * v2n) / total_mass
        v2n_new = (v2n * (ball2.radius - ball1.radius) + 2 * ball1.radius * v1n) / total_mass

        ball1.vx = v1n_new * math.cos(angle) - v1t * math.sin(angle)
        ball1.vy = v1n_new * math.sin(angle) + v1t * math.cos(angle)
        ball2.vx = v2n_new * math.cos(angle) - v2t * math.sin(angle)
        ball2.vy = v2n_new * math.sin(angle) + v2t * math.cos(angle)

        ball1.vx *= VELOCITY_DAMPING
        ball1.vy *= VELOCITY_DAMPING
        ball2.vx *= VELOCITY_DAMPING
        ball2.vy *= VELOCITY_DAMPING

        overlap = ball1.radius + ball2.radius - distance
        ball1.x += math.cos(angle) * overlap / 2
        ball1.y += math.sin(angle) * overlap / 2
        ball2.x -= math.cos(angle) * overlap / 2
        ball2.y -= math.sin(angle) * overlap / 2

        ball1.limit_speed()
        ball2.limit_speed()

        for _ in range(5):
            spark_vx = random.uniform(-3, 3)
            spark_vy = random.uniform(-3, 3)
            sparks.append(Spark((ball1.x + ball2.x) / 2, (ball1.y + ball2.y) / 2, spark_vx, spark_vy, ball1.color))


class MovingCircle:
    def __init__(self, x, y, vx, vy, radius):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius

    def move(self):
        self.x += self.vx
        self.y += self.vy
        if self.x < self.radius or self.x > WIDTH - self.radius:
            self.vx *= -1
        if self.y < self.radius or self.y > HEIGHT - self.radius:
            self.vy *= -1

    def draw(self, screen, color):
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius, 5)


class WhiteCircle:
    def __init__(self, x, y, vx, vy, radius):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.consumed_balls = 0

    def move(self):
        self.x += self.vx
        self.y += self.vy
        if self.x < self.radius:
            self.x = self.radius
            self.vx *= -1
        if self.x > WIDTH - self.radius:
            self.x = WIDTH - self.radius
            self.vx *= -1
        if self.y < self.radius:
            self.y = self.radius
            self.vy *= -1
        if self.y > HEIGHT - self.radius:
            self.y = HEIGHT - self.radius
            self.vy *= -1

    def draw(self, screen):
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius, WHITE_CIRCLE_BORDER_THICKNESS)
        font = pygame.font.SysFont(None, 48)
        text = font.render(str(self.consumed_balls), True, WHITE)
        screen.blit(text, (int(self.x) - text.get_width() // 2, int(self.y) - text.get_height() // 2))

    def check_ball_collision(self, balls):
        for ball in balls[:]:
            dx = self.x - ball.x
            dy = self.y - ball.y
            distance = math.hypot(dx, dy)
            if distance < self.radius + ball.radius:
                balls.remove(ball)
                self.consumed_balls += 1
                self.radius += 4  # Increase the size of the white circle
                # Ensure the circle remains within boundaries after growing
                self.adjust_position()

    def adjust_position(self):
        if self.x - self.radius < 0:
            self.x = self.radius
        if self.x + self.radius > WIDTH:
            self.x = WIDTH - self.radius
        if self.y - self.radius < 0:
            self.y = self.radius
        if self.y + self.radius > HEIGHT:
            self.y = HEIGHT - self.radius


balls = [
    Ball(WIDTH // 2 - 125, HEIGHT // 2 + 100, 0, 15, RED_BALL_COLOR),
    Ball(WIDTH // 2 + 125, HEIGHT // 2, 0, 15, BLUE_BALL_COLOR),
    Ball(WIDTH // 2, HEIGHT // 2 - 125, 15, 0, (0, 255, 0)),
    Ball(WIDTH // 2, HEIGHT // 2 + 125, 15, 0, (255, 0, 255)),
    Ball(WIDTH // 2 - 100, HEIGHT // 2 - 100, 10, 10, (255, 255, 0)),
    Ball(WIDTH // 2 + 100, HEIGHT // 2 + 100, 10, 10, (0, 255, 255)),
]
circle = MovingCircle(WIDTH // 2, HEIGHT // 2, CIRCLE_VX, CIRCLE_VY, CIRCLE_RADIUS)
white_circle = WhiteCircle(WIDTH // 4, HEIGHT // 4, WHITE_CIRCLE_VX, WHITE_CIRCLE_VY, WHITE_CIRCLE_RADIUS)

running = True
game_over = False
hue = 0.0
font, large_font = pygame.font.SysFont(None, 48), pygame.font.SysFont(None, 64)
sparks = []

time.sleep(1)

# Initialize the timer
start_time = pygame.time.get_ticks()
time_limit = 50000  # 50 seconds in milliseconds
hue = 0.0  # Starting hue value
hue_2 = 0.0  # Starting hue value for dynamic color effects
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:
        screen.fill(BACKGROUND_COLOR)

        # Calculate the elapsed time
        elapsed_time = pygame.time.get_ticks() - start_time
        remaining_time = max(0, (time_limit - elapsed_time) // 10)  # Time left in seconds

        # Update the hue for dynamic color effects
        hue_2 = (hue_2 + 0.001) % 1.0
        rgb_color = colorsys.hsv_to_rgb(hue_2, 1.0, 1.0)
        dynamic_color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))

        title_text = font.render("WILL IT GET THEM ALL?", True, dynamic_color)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))

        timer_text = font.render(f"BEFORE TIME RUNS OUT?", True, dynamic_color)
        screen.blit(timer_text, (WIDTH // 2 - timer_text.get_width() // 2, 150))

        timer_text = font.render(f"TIME LEFT: {remaining_time}", True, dynamic_color)
        screen.blit(timer_text, (WIDTH // 2 - timer_text.get_width() // 2, 200))

        for ball in balls:
            ball.move()
            ball.draw(screen)
            ball.check_boundary_collision(circle, balls, sparks)
            ball.ensure_within_boundary()

        for spark in sparks[:]:
            spark.move()
            spark.draw(screen)
            if spark.lifespan <= 0:
                sparks.remove(spark)

        for i in range(len(balls)):
            for j in range(i + 1, len(balls)):
                check_collision(balls[i], balls[j], sparks)

        circle.move()
        hue = (hue + 0.05) % 1.0
        rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        circle_color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
        circle.draw(screen, circle_color)

        white_circle.move()
        white_circle.draw(screen)
        white_circle.check_ball_collision(balls)

        watermark_font = pygame.font.SysFont(None, 36)
        watermark_texts = [
            watermark_font.render("yt:@jbbm_motions", True, GREY),
            watermark_font.render("tiktok:@jbbm_motions", True, GREY),
            watermark_font.render("subscribe for more!", True, GREY),
            watermark_font.render("comment what to do next!", True, GREY),
        ]
        for idx, text in enumerate(watermark_texts):
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 900 + idx * 30))

        # Check if time is up
        if elapsed_time >= time_limit + 2000:
            running = False  # Stop the game when time runs out

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
