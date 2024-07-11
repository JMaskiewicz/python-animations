import pygame
import random

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 600, 800
FPS = 60
NUM_OBJECTS = 10  # Number of each type

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
        self.dx = random.choice([-3, 3])
        self.dy = random.choice([-3, 3])
        self.color = WHITE
        if self.type == ROCK:
            self.color = (200, 0, 0)
        elif self.type == PAPER:
            self.color = (0, 200, 0)
        elif self.type == SCISSORS:
            self.color = (0, 0, 200)

    def move(self):
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

    def check_collision(self, other):
        dist = ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5
        if dist < self.radius + other.radius:
            self.resolve_collision(other, dist)
            self.transform(other)

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

    def transform(self, other):
        if self.type == ROCK and other.type == SCISSORS:
            other.type = ROCK
            other.color = self.color
            other.radius *= 1.25
        elif self.type == SCISSORS and other.type == PAPER:
            other.type = SCISSORS
            other.color = self.color
            other.radius *= 1.25
        elif self.type == PAPER and other.type == ROCK:
            other.type = PAPER
            other.color = self.color
            other.radius *= 1.25

# Initialize objects
objects = ([RPSObject(ROCK) for _ in range(NUM_OBJECTS)] +
           [RPSObject(PAPER) for _ in range(NUM_OBJECTS)] +
           [RPSObject(SCISSORS) for _ in range(NUM_OBJECTS)])

# Main loop
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BLACK)

    for obj in objects:
        obj.move()
        obj.draw(screen)
        for other_obj in objects:
            if obj != other_obj:
                obj.check_collision(other_obj)

    pygame.display.flip()
    clock.tick(FPS)

    # Check if all objects are of the same type
    first_type = objects[0].type
    if all(obj.type == first_type for obj in objects):
        running = False

pygame.quit()
