import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Set up display
WIDTH, HEIGHT = 720, 1280
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Brownian Motion Simulation")

# Define colors
RED = (255, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

# Define circle boundary
CIRCLE_RADIUS = WIDTH // 2 - 20
CIRCLE_CENTER = (WIDTH // 2, HEIGHT // 2)

# Font for displaying distance
font = pygame.font.SysFont(None, 36)

# Ball class
class Ball:
    def __init__(self, x, y, radius, color, is_large=False):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.is_large = is_large
        self.mass = math.pi * (self.radius ** 2)  # Mass proportional to surface area
        self.vel_x = 0 if is_large else random.uniform(-2, 2)
        self.vel_y = 0 if is_large else random.uniform(-2, 2)
        self.trail = []  # Store positions for the trail

    def move(self):
        self.x += self.vel_x
        self.y += self.vel_y

        # Calculate distance from the center of the circle
        dist_from_center = math.hypot(self.x - CIRCLE_CENTER[0], self.y - CIRCLE_CENTER[1])

        # Bounce off the circle boundary
        if dist_from_center + self.radius >= CIRCLE_RADIUS:
            angle = math.atan2(self.y - CIRCLE_CENTER[1], self.x - CIRCLE_CENTER[0])

            # Reflect the velocity vector
            self.vel_x = -self.vel_x
            self.vel_y = -self.vel_y

            # Adjust position to be exactly on the boundary
            self.x = CIRCLE_CENTER[0] + (CIRCLE_RADIUS - self.radius) * math.cos(angle)
            self.y = CIRCLE_CENTER[1] + (CIRCLE_RADIUS - self.radius) * math.sin(angle)

        # Update the trail
        if self.is_large:
            self.trail.append((self.x, self.y))
            if len(self.trail) > 100:  # Limit the trail length
                self.trail.pop(0)

    def draw(self, screen):
        # Draw the trail
        if self.is_large and len(self.trail) > 1:
            pygame.draw.lines(screen, self.color, False, self.trail, 2)
        # Draw the ball
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def collide_with(self, other):
        if self == other:
            return
        dist = math.hypot(self.x - other.x, self.y - other.y)
        if dist < self.radius + other.radius:
            angle = math.atan2(other.y - self.y, other.x - self.x)
            total_radius = self.radius + other.radius

            overlap = total_radius - dist

            self.x -= overlap * math.cos(angle) / 2
            self.y -= overlap * math.sin(angle) / 2
            other.x += overlap * math.cos(angle) / 2
            other.y += overlap * math.sin(angle) / 2

            # Collision response for small particle and large ball
            if not self.is_large and other.is_large:
                # Only the large ball's velocity is updated
                new_vel_x_other = (2 * self.mass * self.vel_x) / (self.mass + other.mass)
                new_vel_y_other = (2 * self.mass * self.vel_y) / (self.mass + other.mass)
                other.vel_x += new_vel_x_other
                other.vel_y += new_vel_y_other

                # Small particle velocity update (bounce back effect)
                self.vel_x = -self.vel_x
                self.vel_y = -self.vel_y

            elif self.is_large and not other.is_large:
                # Only the large ball's velocity is updated
                new_vel_x_self = (2 * other.mass * other.vel_x) / (self.mass + other.mass)
                new_vel_y_self = (2 * other.mass * other.vel_y) / (self.mass + other.mass)
                self.vel_x += new_vel_x_self
                self.vel_y += new_vel_y_self

                # Small particle velocity update (bounce back effect)
                other.vel_x = -other.vel_x
                other.vel_y = -other.vel_y

            elif not self.is_large and not other.is_large:
                # Regular collision for small particles
                self.vel_x, other.vel_x = other.vel_x, self.vel_x
                self.vel_y, other.vel_y = other.vel_y, self.vel_y

def spawn_evenly_distributed_balls(radius, gap):
    balls = []
    current_radius = radius + gap
    while current_radius < CIRCLE_RADIUS - radius:
        circumference = 2 * math.pi * current_radius
        num_balls = int(circumference // (2 * (radius + gap)))
        for i in range(num_balls):
            angle = 2 * math.pi * i / num_balls
            x = CIRCLE_CENTER[0] + current_radius * math.cos(angle)
            y = CIRCLE_CENTER[1] + current_radius * math.sin(angle)
            balls.append(Ball(x, y, radius, RED))
        current_radius += 2 * (radius + gap)
    return balls

def draw_distance(screen, distance, color, x, y):
    text = font.render(f"Distance: {int(distance)}", True, color)
    screen.blit(text, (x, y))

# Create larger balls
large_balls = [
    Ball(WIDTH // 2, HEIGHT // 2 - 200, 20, BLUE, is_large=True),
    Ball(WIDTH // 2, HEIGHT // 2, 30, WHITE, is_large=True),
    Ball(WIDTH // 2, HEIGHT // 2 + 200, 40, GREEN, is_large=True)
]

# Create small particles
small_particles = spawn_evenly_distributed_balls(5, 5)

# Main loop
running = True
while running:
    screen.fill(BLACK)

    # Draw the boundary circle
    pygame.draw.circle(screen, RED, CIRCLE_CENTER, CIRCLE_RADIUS, 5)

    # Draw lines from the center to each large ball and calculate distances
    for ball in large_balls:
        distance = math.hypot(ball.x - CIRCLE_CENTER[0], ball.y - CIRCLE_CENTER[1])
        ball.draw(screen)  # Draw ball with its trail

        # Display the distance above the simulation
        if ball.color == BLUE:
            draw_distance(screen, distance, BLUE, 50, 10)
        elif ball.color == WHITE:
            draw_distance(screen, distance, WHITE, 250, 10)
        elif ball.color == GREEN:
            draw_distance(screen, distance, GREEN, 450, 10)

    # Update and draw small particles
    for particle in small_particles:
        particle.move()
        particle.draw(screen)

    # Handle collisions between small particles and large balls
    for particle in small_particles:
        for ball in large_balls:
            particle.collide_with(ball)
            ball.collide_with(particle)

    # Handle collisions between large balls themselves
    for i in range(len(large_balls)):
        for j in range(i + 1, len(large_balls)):
            large_balls[i].collide_with(large_balls[j])

    # Handle collisions between small particles themselves
    for i in range(len(small_particles)):
        for j in range(i + 1, len(small_particles)):
            small_particles[i].collide_with(small_particles[j])

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()
    pygame.time.delay(20)

pygame.quit()
