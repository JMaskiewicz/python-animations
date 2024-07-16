import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Create Pygame window
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball with Trailing Effect and Concentric Circles")

# Constants
FPS = 60
MAX_SPEED = 5  # Maximum initial speed of ball
TRAIL_LENGTH = 30  # Number of trail segments
GRAVITY = 0.2  # Gravity effect

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
        pygame.draw.circle(screen, self.color, (WIDTH // 2, HEIGHT // 2), self.radius, 5)

circles = [Circle(radius, CIRCLE_COLORS[i % len(CIRCLE_COLORS)]) for i, radius in enumerate(range(300, 50, -50))]

# Trail settings
trail_positions = []

# Main game loop
running = True
clock = pygame.time.Clock()

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
    if ball_pos[1] <= BALL_RADIUS or ball_pos[1] >= HEIGHT - BALL_RADIUS:
        ball_speed[1] = -ball_speed[1]

    # Check collision with circles
    for circle in circles[:]:
        dist = math.hypot(ball_pos[0] - WIDTH // 2, ball_pos[1] - HEIGHT // 2)
        if circle.radius - BALL_RADIUS <= dist <= circle.radius + BALL_RADIUS:
            circles.remove(circle)
            ball_speed[0] = -ball_speed[0]
            ball_speed[1] = -ball_speed[1]
            break

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
