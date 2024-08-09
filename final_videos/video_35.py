import pygame
import math

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 720, 1280
BG_COLOR = (0, 0, 0)
BALL_COLOR = (255, 0, 0)
BALL_RADIUS = 10
SPIRAL_COLOR = (255, 255, 255)
FPS = 60
GRAVITY = 0.1  # Gravity constant
SUB_STEPS = 10  # Number of sub-steps for collision detection

# Create the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Ball Bouncing off Spiral')

# Ball initial position and velocity
ball_pos = [WIDTH // 2, HEIGHT // 2]
ball_vel = [3, 2]

# Spiral parameters
spiral_center = (WIDTH // 2, HEIGHT // 2)
initial_radius = 20
spiral_spacing = 10  # Adjust the spacing for larger gaps
spiral_turns = 10
rotation_speed = 0.01  # Speed of spiral rotation


# Function to draw the spiral
def draw_spiral(surface, center, initial_radius, spacing, turns, rotation):
    theta = rotation
    radius = initial_radius
    points = []
    for _ in range(int(turns * 20)):  # Finite spiral by limiting number of points
        x = int(center[0] + radius * math.cos(theta))
        y = int(center[1] + radius * math.sin(theta))
        points.append((x, y))
        radius += spacing / (2 * math.pi)
        theta += 0.1
    for i in range(len(points) - 1):
        pygame.draw.line(surface, SPIRAL_COLOR, points[i], points[i + 1], 2)
    return points


# Function to draw the ball
def draw_ball(surface, position, radius, color):
    pygame.draw.circle(surface, color, (int(position[0]), int(position[1])), radius)


# Function to check collision with spiral
def check_collision(ball_pos, ball_vel, spiral_points):
    collision_detected = False
    for i in range(len(spiral_points) - 1):
        point1 = spiral_points[i]
        point2 = spiral_points[i + 1]
        if line_circle_collision(point1, point2, ball_pos, BALL_RADIUS):
            collision_detected = True
            # Calculate the normal to the segment
            normal = [point2[1] - point1[1], -(point2[0] - point1[0])]
            norm_length = math.hypot(normal[0], normal[1])
            normal = [normal[0] / norm_length, normal[1] / norm_length]

            # Reflect the velocity
            dot_product = ball_vel[0] * normal[0] + ball_vel[1] * normal[1]
            ball_vel[0] -= 2 * dot_product * normal[0]
            ball_vel[1] -= 2 * dot_product * normal[1]

            # Move the ball out of collision slightly more to avoid sticking
            ball_pos[0] += normal[0] * (BALL_RADIUS + 1)
            ball_pos[1] += normal[1] * (BALL_RADIUS + 1)
    return collision_detected


def line_circle_collision(p1, p2, center, radius):
    ac = [center[0] - p1[0], center[1] - p1[1]]
    ab = [p2[0] - p1[0], p2[1] - p1[1]]
    ab2 = ab[0] ** 2 + ab[1] ** 2
    acab = ac[0] * ab[0] + ac[1] * ab[1]
    t = acab / ab2
    t = max(0, min(1, t))
    h = [ab[0] * t + p1[0], ab[1] * t + p1[1]]
    return math.hypot(center[0] - h[0], center[1] - h[1]) <= radius


# Main loop
def main():
    clock = pygame.time.Clock()
    rotation = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Rotate the spiral
        rotation += rotation_speed

        # Draw everything
        screen.fill(BG_COLOR)
        spiral_points = draw_spiral(screen, spiral_center, initial_radius, spiral_spacing, spiral_turns, rotation)
        draw_ball(screen, ball_pos, BALL_RADIUS, BALL_COLOR)

        # Apply gravity
        ball_vel[1] += GRAVITY

        # Move the ball in sub-steps
        for _ in range(SUB_STEPS):
            ball_pos[0] += ball_vel[0] / SUB_STEPS
            ball_pos[1] += ball_vel[1] / SUB_STEPS

            # Bounce off walls
            if ball_pos[0] <= BALL_RADIUS or ball_pos[0] >= WIDTH - BALL_RADIUS:
                ball_vel[0] = -ball_vel[0]
            if ball_pos[1] <= BALL_RADIUS or ball_pos[1] >= HEIGHT - BALL_RADIUS:
                ball_vel[1] = -ball_vel[1]

            # Check collision with spiral
            if check_collision(ball_pos, ball_vel, spiral_points):
                break  # Exit sub-step loop if a collision is detected

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
