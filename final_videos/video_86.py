import pygame
import math
import time

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 720, 1280
CENTER = (WIDTH // 2, HEIGHT // 2)
RADIUS = 300  # Radius of the circle
INITIAL_BALL_RADIUS = 6
CIRCLE_COLOR = (255, 255, 255)  # White color for the circle
BALL_COUNT = 3  # Number of balls

# Create Pygame window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bouncing Balls with Infinite Trails")

# Set the frame rate
clock = pygame.time.Clock()
FPS = 60

# Ball class to handle individual ball properties
class Ball:
    def __init__(self, start_time, delay, color, x=None, y=None):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2 - 280
        self.speed_x = -4
        self.speed_y = 7
        self.radius = INITIAL_BALL_RADIUS
        self.color = color
        self.trail_points = []  # Contains tuples of ((x, y), radius, color, timestamp)
        self.collision_cooldown = 0
        self.start_time = start_time
        self.delay = delay
        self.active = False

    def move(self):
        if time.time() >= self.start_time + self.delay:
            self.active = True

        if self.active:
            self.x += self.speed_x
            self.y += self.speed_y

    def check_collision(self):
        if self.active:
            # Cooldown for collision detection
            if self.collision_cooldown > 0:
                self.collision_cooldown -= 1

            # Check collision with the circle boundary accounting for the ball's radius
            dx = self.x - CENTER[0]
            dy = self.y - CENTER[1]
            dist = math.sqrt(dx ** 2 + dy ** 2)

            # Adjust for ball's radius and apply cooldown
            if dist >= RADIUS - self.radius and self.collision_cooldown == 0:
                # Reflect the ball's velocity based on the normal to the circle
                angle = math.atan2(dy, dx)
                normal_x = math.cos(angle)
                normal_y = math.sin(angle)
                dot_product = self.speed_x * normal_x + self.speed_y * normal_y
                self.speed_x -= 2 * dot_product * normal_x
                self.speed_y -= 2 * dot_product * normal_y

                # Increase the ball size on each bounce
                self.radius *= 1.05  # No need to cast here, we keep it as a float for gradual growth

                # Move ball slightly away from the boundary after growth to avoid immediate collision
                self.x += normal_x * 2
                self.y += normal_y * 2

                # Set collision cooldown to prevent infinite loop
                self.collision_cooldown = 10  # Cooldown of 10 frames before next collision detection

    def add_trail(self):
        if self.active:
            # Add the current ball position, its radius, color, and timestamp to the trail
            self.trail_points.append(((int(self.x), int(self.y)), self.radius, self.color, time.time()))


# List to hold the balls
balls = []
start_time = time.time()

# Define colors for each ball
colors = [(0, 0, 255), (255, 0, 0), (0, 255, 0)]  # Blue, Red, Green

# Create three balls with staggered start times and different colors
for i in range(BALL_COUNT):
    balls.append(Ball(start_time, i * 1.5, colors[i]))  # Delay the start of each ball by 0.5 seconds and assign color

# Main loop
running = True
while running:
    screen.fill((0, 0, 0))  # Black background

    # Draw the circle
    pygame.draw.circle(screen, CIRCLE_COLOR, CENTER, RADIUS, 5)

    # Collect all trail points across all balls into one list
    all_trail_points = []
    for ball in balls:
        ball.move()
        ball.check_collision()
        ball.add_trail()
        all_trail_points.extend(ball.trail_points)

    # Sort all trail points by the timestamp (the 4th element in the tuple)
    all_trail_points.sort(key=lambda p: p[3])

    # Draw the sorted trail points
    for point, radius, color, _ in all_trail_points:
        pygame.draw.circle(screen, color, point, int(radius))

    # Draw each ball on top of the trails
    for ball in balls:
        if ball.active:
            pygame.draw.circle(screen, ball.color, (int(ball.x), int(ball.y)), int(ball.radius))

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update the display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(FPS)

# Quit Pygame
pygame.quit()
