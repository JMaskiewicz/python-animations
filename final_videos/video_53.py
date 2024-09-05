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
RED_BALL_COLOR = (255, 0, 0)
BLUE_BALL_COLOR = (0, 0, 255)
BACKGROUND_COLOR = (0, 0, 0)
GREY = (30, 30, 30)
WHITE = (255, 255, 255)
GRAVITY = 0
FPS = 60
CIRCLE_RADIUS = 340

VELOCITY_DAMPING = 1.0005  # Damping factor to avoid excessive speeds
COOLDOWN = 10  # Cooldown period to prevent multiple size adjustments
SPEED_INCREASE = 1  # Speed increase factor on each bounce off the circle
MAX_SPEED = 100  # Maximum speed limit for the balls

# Initialize pygame
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball Collision Simulation with Sparks")
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

    def check_boundary_collision(self, sparks):
        dx = self.x - WIDTH // 2
        dy = self.y - HEIGHT // 2
        distance = math.hypot(dx, dy)
        if distance > CIRCLE_RADIUS - self.radius:
            if self.cooldown == 0:  # Check cooldown
                # Calculate the normal vector at the collision point
                angle = math.atan2(dy, dx)
                normal_x = math.cos(angle)
                normal_y = math.sin(angle)

                # Calculate the dot product of the velocity and the normal vector
                dot_product = self.vx * normal_x + self.vy * normal_y

                # Reflect the velocity vector over the normal vector
                self.vx = self.vx - 2 * dot_product * normal_x
                self.vy = self.vy - 2 * dot_product * normal_y

                # Correct the position to avoid sticking
                overlap = distance - (CIRCLE_RADIUS - self.radius)
                self.x -= math.cos(angle) * overlap
                self.y -= math.sin(angle) * overlap

                self.cooldown = COOLDOWN  # Reset cooldown

                # Increase speed
                speed = math.hypot(self.vx, self.vy)
                self.vx = self.vx / speed * (speed * SPEED_INCREASE)
                self.vy = self.vy / speed * (speed * SPEED_INCREASE)

                # Limit speed
                self.limit_speed()
                pop_sound.play()
                # Create sparks at the point of boundary collision
                for _ in range(10):
                    spark_vx = random.uniform(-3, 3)
                    spark_vy = random.uniform(-3, 3)
                    sparks.append(Spark(self.x, self.y, spark_vx, spark_vy, self.color))

                # Play sound on collision
                if self.color == RED_BALL_COLOR:
                    self.bounce_count += 1

    def ensure_within_boundary(self):
        dx = self.x - WIDTH // 2
        dy = self.y - HEIGHT // 2
        distance = math.hypot(dx, dy)
        if distance > CIRCLE_RADIUS - self.radius:
            angle = math.atan2(dy, dx)
            self.x = WIDTH // 2 + (CIRCLE_RADIUS - self.radius - 1) * math.cos(angle)
            self.y = HEIGHT // 2 + (CIRCLE_RADIUS - self.radius - 1) * math.sin(angle)


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


SPAWN_COOLDOWN = 10  # Cooldown in frames between new ball spawns

# Updated check_collision function with maximum ball limit and cooldown
def check_collision(ball1, ball2, balls, sparks, spawn_cooldown):
    dx = ball1.x - ball2.x
    dy = ball1.y - ball2.y
    distance = math.hypot(dx, dy)
    if distance < ball1.radius + ball2.radius:
        pop_sound.play()
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

        # Separate the balls
        overlap = ball1.radius + ball2.radius - distance
        ball1.x += math.cos(angle) * overlap / 2
        ball1.y += math.sin(angle) * overlap / 2
        ball2.x -= math.cos(angle) * overlap / 2
        ball2.y -= math.sin(angle) * overlap / 2

        # Limit speed
        ball1.limit_speed()
        ball2.limit_speed()

        # Create sparks at the point of collision
        for _ in range(10):
            spark_vx = random.uniform(-3, 3)
            spark_vy = random.uniform(-3, 3)
            sparks.append(Spark((ball1.x + ball2.x) / 2, (ball1.y + ball2.y) / 2, spark_vx, spark_vy, ball1.color))

        # Spawn a new ball only if cooldown has passed and maximum number of balls is not exceeded
        if len(balls) < MAX_BALLS and spawn_cooldown[0] == 0:
            new_ball_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            offset_x = random.uniform(-20, 20)  # Small random offset to avoid clustering
            offset_y = random.uniform(-20, 20)
            new_ball = Ball(WIDTH // 2 + offset_x, HEIGHT // 2 + offset_y, random.uniform(-5, 5), random.uniform(-5, 5), new_ball_color)

            balls.append(new_ball)
            spawn_cooldown[0] = SPAWN_COOLDOWN  # Reset the spawn cooldown


# Create initial balls
balls = [
    Ball(WIDTH // 2 - 125, HEIGHT // 2 + 100, 0, 8, RED_BALL_COLOR),
    Ball(WIDTH // 2 + 125, HEIGHT // 2, 0, 8, BLUE_BALL_COLOR)
]
MAX_BALLS = 10000
spawn_cooldown = [0]  # Cooldown tracker for spawning new balls

# Main loop
running = True
game_over = False
end_message_start_time = 0
hue = 0.0
font, large_font = pygame.font.SysFont(None, 48), pygame.font.SysFont(None, 64)
start_timer = time.time()
show_end_message = False

sparks = []  # List to store sparks

# #wait for 1 second
time.sleep(2)
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Continue running the simulation
    if not game_over:
        screen.fill(BACKGROUND_COLOR)

        title_text = font.render("HOW MANY CAN MY PC HANDLE?", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))

        # Move and draw balls
        for ball in balls:
            ball.move()
            ball.draw(screen)
            ball.check_boundary_collision(sparks)
            ball.ensure_within_boundary()

        # Move and draw sparks
        for spark in sparks[:]:
            spark.move()
            spark.draw(screen)
            if spark.lifespan <= 0:
                sparks.remove(spark)

        # Check collisions between all balls
        for i in range(len(balls)):
            for j in range(i + 1, len(balls)):
                check_collision(balls[i], balls[j], balls, sparks, spawn_cooldown)

        # Decrease spawn cooldown
        if spawn_cooldown[0] > 0:
            spawn_cooldown[0] -= 1

        # Change circle color over time
        hue = (hue + 0.005) % 1.0
        rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        circle_color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))

        # Draw thinner circle with changing color
        pygame.draw.circle(screen, circle_color, (WIDTH // 2, HEIGHT // 2), CIRCLE_RADIUS, 10)

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

    # Display the game over message on top of the ongoing simulation
    if show_end_message:
        game_over_text1 = large_font.render("LIKE", True, WHITE)
        game_over_text2 = large_font.render("FOLLOW", True, WHITE)
        game_over_text3 = large_font.render("SUBSCRIBE", True, WHITE)
        game_over_text4 = large_font.render("COMMENT WHAT TO DO NEXT", True, WHITE)
        screen.blit(game_over_text1, (WIDTH // 2 - game_over_text1.get_width() // 2, HEIGHT // 2 - 150))
        screen.blit(game_over_text2, (WIDTH // 2 - game_over_text2.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(game_over_text3, (WIDTH // 2 - game_over_text3.get_width() // 2, HEIGHT // 2 + 50))
        screen.blit(game_over_text4, (WIDTH // 2 - game_over_text4.get_width() // 2, HEIGHT // 2 + 150))

        # Check if the 3-second period is over
        if time.time() - end_message_start_time >= 3:
            running = False

    # Update the display
    pygame.display.flip()
    clock.tick(FPS)

    # Check if the timer to show the end message has been reached
    if not show_end_message and time.time() - start_timer >= 48:
        show_end_message = True
        end_message_start_time = time.time()

pygame.quit()
