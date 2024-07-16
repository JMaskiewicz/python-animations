import pygame
import random
import math
import time

# Initialize Pygame
pygame.init()

# Create Pygame window
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball with Trailing Effect and Dynamic Circles")

# Constants
FPS = 60
MAX_SPEED = 1  # Maximum initial speed of ball
TRAIL_LENGTH = 30  # Number of trail segments
GRAVITY = 0.2  # Gravity effect
CIRCLE_SHRINK_RATE = 0.5  # Rate at which circles shrink
NEW_CIRCLE_INTERVAL = 1  # Initial time interval in seconds to add new circle
MIN_CIRCLE_RADIUS = 5  # Minimum circle radius before disappearing
SPEED_INCREASE_FACTOR = 1.025  # Factor to increase speed after each bounce
CIRCLE_CREATION_ACCELERATION = 0.99  # Factor to decrease interval for circle creation after each bounce

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CIRCLE_COLORS = [(255, 105, 180), (255, 182, 193), (255, 240, 245), (255, 228, 225), (255, 192, 203)]
TRAIL_COLORS = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 127, 255), (0, 0, 255), (139, 0, 255)]

# Ball settings
BALL_RADIUS = 15
ball_pos = [WIDTH // 2, HEIGHT // 2]
ball_speed = [random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])]

# Circle settings
class Circle:
    def __init__(self, radius, color):
        self.radius = radius
        self.color = color

    def draw(self, screen):
        if self.radius > 0:
            pygame.draw.circle(screen, self.color, (WIDTH // 2, HEIGHT // 2), self.radius, 5)

    def update(self):
        self.radius -= CIRCLE_SHRINK_RATE

circles = [Circle(radius, random.choice(CIRCLE_COLORS)) for radius in range(300, 50, -50)][:4]  # Initialize with 4 circles

# Trail settings
trail_positions = []

def randomize_direction(ball_speed):
    angle = random.uniform(-math.pi / 6, math.pi / 6)  # Random angle between -30 and 30 degrees
    speed = math.hypot(ball_speed[0], ball_speed[1])  # Current speed magnitude
    new_angle = math.atan2(ball_speed[1], ball_speed[0]) + angle
    ball_speed[0] = speed * math.cos(new_angle)
    ball_speed[1] = speed * math.sin(new_angle)

def increase_speed(ball_speed):
    ball_speed[0] *= SPEED_INCREASE_FACTOR
    ball_speed[1] *= SPEED_INCREASE_FACTOR

# Main game loop
running = True
clock = pygame.time.Clock()
last_circle_add_time = time.time()

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update ball position
    ball_speed[1] += GRAVITY
    ball_pos[0] += ball_speed[0]
    ball_pos[1] += ball_speed[1]

    # Ball collision with walls
    if ball_pos[0] <= BALL_RADIUS or ball_pos[0] >= WIDTH - BALL_RADIUS:
        ball_speed[0] = -ball_speed[0]
        randomize_direction(ball_speed)
    if ball_pos[1] <= BALL_RADIUS or ball_pos[1] >= HEIGHT - BALL_RADIUS:
        ball_speed[1] = -ball_speed[1]
        randomize_direction(ball_speed)

    # Check collision with circles
    for circle in circles[:]:
        dist = math.hypot(ball_pos[0] - WIDTH // 2, ball_pos[1] - HEIGHT // 2)
        if circle.radius - BALL_RADIUS <= dist <= circle.radius + BALL_RADIUS:
            circles.remove(circle)
            ball_speed[0] = -ball_speed[0]
            ball_speed[1] = -ball_speed[1]
            randomize_direction(ball_speed)
            increase_speed(ball_speed)
            NEW_CIRCLE_INTERVAL *= CIRCLE_CREATION_ACCELERATION  # Decrease interval for circle creation
            break

    # Update circles
    for circle in circles:
        circle.update()
    circles = [circle for circle in circles if circle.radius > MIN_CIRCLE_RADIUS]

    # Add new circle based on current interval
    current_time = time.time()
    if current_time - last_circle_add_time >= NEW_CIRCLE_INTERVAL:
        new_circle = Circle(300, random.choice(CIRCLE_COLORS))
        circles.append(new_circle)
        last_circle_add_time = current_time

    # Update trail positions
    trail_positions.append(tuple(ball_pos))
    if len(trail_positions) > TRAIL_LENGTH:
        trail_positions.pop(0)

    # Draw everything
    screen.fill(BLACK)

    # Draw circles
    for circle in circles:
        circle.draw(screen)

    # Draw trail
    for i, pos in enumerate(trail_positions):
        color = TRAIL_COLORS[i % len(TRAIL_COLORS)]
        pygame.draw.circle(screen, color, pos, BALL_RADIUS)

    # Draw ball
    pygame.draw.circle(screen, WHITE, ball_pos, BALL_RADIUS)

    pygame.display.flip()

pygame.quit()
