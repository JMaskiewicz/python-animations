import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Create Pygame window
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball and Concentric Circles Animation")

# Constants
FPS = 60
MAX_SPEED = 3  # Maximum speed of ball

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CIRCLE_COLORS = [(255, 105, 180), (255, 182, 193), (255, 240, 245), (255, 228, 225), (255, 192, 203)]

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

# Main game loop
running = True
clock = pygame.time.Clock()

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update ball position
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
        if circle.radius - 5 < dist < circle.radius + 5:
            circles.remove(circle)
            ball_speed[0] = -ball_speed[0]
            ball_speed[1] = -ball_speed[1]
            break

    # Draw everything
    screen.fill(BLACK)
    pygame.draw.circle(screen, WHITE, ball_pos, BALL_RADIUS)
    for circle in circles:
        circle.draw(screen)
    pygame.display.flip()

pygame.quit()
