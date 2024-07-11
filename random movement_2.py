import pygame
import random

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 600, 800
FPS = 60
NUM_OBJECTS = 10  # Number of each type
MAX_SPEED = 3  # Maximum speed of objects

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Object Types
ROCK = 'rock'
PAPER = 'paper'
SCISSORS = 'scissors'
types = [ROCK, PAPER, SCISSORS]

# Create Pygame window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rock Paper Scissors Animation")


# Object class
class RPSObject:
    def __init__(self, obj_type):
        self.type = obj_type
        self.radius = 10
        self.x = random.randint(self.radius, WIDTH - self.radius)
        self.y = random.randint(self.radius, HEIGHT - self.radius)
        self.dx = random.uniform(-MAX_SPEED, MAX_SPEED)
        self.dy = random.uniform(-MAX_SPEED, MAX_SPEED)
        self.color = self.get_color()

    def get_color(self):
        if self.type == ROCK:
            return (200, 0, 0)
        elif self.type == PAPER:
            return (0, 200, 0)
        elif self.type == SCISSORS:
            return (0, 0, 200)
        return WHITE

    def move(self):
        # Apply random motion component
        self.dx += random.uniform(-0.5, 0.5)
        self.dy += random.uniform(-0.5, 0.5)

        # Limit speed to max speed
        self.dx = max(min(self.dx, MAX_SPEED), -MAX_SPEED)
        self.dy = max(min(self.dy, MAX_SPEED), -MAX_SPEED)

        self.x += self.dx
        self.y += self.dy

        # Wall collision handling
        if self.x <= self.radius:
            self.x = self.radius
            self.dx *= -1
        elif self.x >= WIDTH - self.radius:
            self.x = WIDTH - self.radius
            self.dx *= -1
        if self.y <= self.radius:
            self.y = self.radius
            self.dy *= -1
        elif self.y >= HEIGHT - self.radius:
            self.y = HEIGHT - self.radius
            self.dy *= -1

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)

    def check_collision(self, other, objects):
        dist = ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
        if dist < self.radius + other.radius:
            self.resolve_collision(other, dist)
            self.transform(other, objects)

    def resolve_collision(self, other, dist):
        # Calculate overlap
        overlap = 0.5 * (self.radius + other.radius - dist)
        # Displace current object
        self.x += overlap * (self.x - other.x) / dist
        self.y += overlap * (self.y - other.y) / dist
        # Displace other object
        other.x -= overlap * (self.x - other.x) / dist
        other.y -= overlap * (self.y - other.y) / dist
        # Bounce
        self.bounce(other)

    def bounce(self, other):
        self.dx, other.dx = other.dx, self.dx
        self.dy, other.dy = other.dy, self.dy

    def can_grow(self, new_radius, objects):
        # Check if the object can grow to the new radius without overlapping others or walls
        if self.x - new_radius < 0 or self.x + new_radius > WIDTH:
            return False
        if self.y - new_radius < 0 or self.y + new_radius > HEIGHT:
            return
