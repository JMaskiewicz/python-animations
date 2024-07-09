import pygame
import math

# test

# Initialize Pygame
pygame.init()

# Screen dimensions
width, height = 1080, 1920
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Bouncing Star Animation")

# Colors
black = (0, 0, 0)
white = (255, 255, 255)

# Star properties
star_points = 5
star_radius = 20
x, y = width // 2, height // 2
vx, vy = 5, 3

# Circle properties
circle_radius = 50
angle = 0

def draw_star(surface, color, x, y, points, radius):
    angle = math.pi / points
    star = []
    for i in range(points * 2):
        r = radius if i % 2 == 0 else radius // 2
        point_x = x + int(math.cos(i * angle) * r)
        point_y = y + int(math.sin(i * angle) * r)
        star.append((point_x, point_y))
    pygame.draw.polygon(surface, color, star)

# Main loop
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Move the star
    x += vx
    y += vy

    # Bounce the star off the edges
    if x <= star_radius or x >= width - star_radius:
        vx = -vx
        star_points = max(3, star_points - 1)
    if y <= star_radius or y >= height - star_radius:
        vy = -vy
        star_points = max(3, star_points - 1)

    # Rotate the circle
    angle += 0.05
    circle_x = x + int(circle_radius * math.cos(angle))
    circle_y = y + int(circle_radius * math.sin(angle))

    # Clear the screen
    screen.fill(black)

    # Draw the rotating circle
    pygame.draw.circle(screen, white, (circle_x, circle_y), 5)

    # Draw the star
    draw_star(screen, white, x, y, star_points, star_radius)

    # Update the display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(60)

pygame.quit()