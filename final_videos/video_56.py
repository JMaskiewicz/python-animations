import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Window settings
WIDTH, HEIGHT = 720, 1280
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bouncing Ball Simulation")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# Ball settings
ball_radius = 15
ball_x = WIDTH // 2
ball_y = ball_radius + 50
ball_speed_y = 5
ball_speed_x = 3

# Line settings
lines = []
line_speed = 2
line_width = 5
line_gap = 200  # Gap between consecutive lines


# Function to draw the ball
def draw_ball(x, y):
    pygame.draw.circle(screen, RED, (x, y), ball_radius)


# Function to generate new lines attached to the edge
def generate_line():
    y = HEIGHT
    attach_to_edge = random.choice(['left', 'right'])
    if attach_to_edge == 'left':
        x1 = 0  # Start from the left edge
        x2 = random.randint(100, WIDTH)
    else:
        x1 = WIDTH  # Start from the right edge
        x2 = random.randint(0, WIDTH - 100)
    lines.append([(x1, y), (x2, y - random.randint(50, 200))])


# Function to move lines up and remove them if they go off-screen
def move_lines():
    for line in lines:
        line[0] = (line[0][0], line[0][1] - line_speed)
        line[1] = (line[1][0], line[1][1] - line_speed)
    if lines and lines[0][0][1] < 0:
        lines.pop(0)


# Function to detect collision between the ball and the lines
def check_collision(ball_x, ball_y):
    for line in lines:
        x1, y1 = line[0]
        x2, y2 = line[1]
        # Line equation components
        A = y2 - y1
        B = x1 - x2
        C = A * x1 + B * y1
        # Perpendicular distance from ball center to the line
        dist = abs(A * ball_x + B * ball_y - C) / math.sqrt(A ** 2 + B ** 2)
        # Check if within line segment bounds
        if dist <= ball_radius and min(x1, x2) <= ball_x <= max(x1, x2):
            if min(y1, y2) <= ball_y <= max(y1, y2):
                return True
    return False


# Main loop
running = True
clock = pygame.time.Clock()

# Generate initial lines
for i in range(HEIGHT // line_gap):
    generate_line()

while running:
    screen.fill(WHITE)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Ball movement
    ball_x += ball_speed_x
    ball_y += ball_speed_y

    # Ball collision detection and bounce
    if check_collision(ball_x, ball_y):
        ball_speed_y = -ball_speed_y
        ball_speed_x = -ball_speed_x
    else:
        ball_speed_y += 0.2  # Gravity effect

    # Keep ball within screen bounds
    if ball_x < ball_radius or ball_x > WIDTH - ball_radius:
        ball_speed_x = -ball_speed_x

    # Respawn the ball if it goes off the screen
    if ball_y > HEIGHT:
        ball_x = WIDTH // 2
        ball_y = ball_radius + 50
        ball_speed_y = 5
        ball_speed_x = 3

    # Generate new lines as needed
    if lines[-1][0][1] < HEIGHT - line_gap:
        generate_line()

    # Move lines and draw them
    move_lines()
    for line in lines:
        pygame.draw.line(screen, BLACK, line[0], line[1], line_width)

    # Draw the ball
    draw_ball(ball_x, ball_y)

    # Update the display
    pygame.display.flip()

    # Control the frame rate
    clock.tick(60)

pygame.quit()
