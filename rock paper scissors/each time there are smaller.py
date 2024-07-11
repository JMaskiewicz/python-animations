import pygame
import random

# Initialize Pygame
pygame.init()

# Constants
WIDTH, HEIGHT = 600, 800
FPS = 60
NUM_OBJECTS = 10  # Number of each type
MAX_SPEED = 3  # Maximum speed of objects
MAX_OBJECTS = 500  # Maximum number of objects

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
    def __init__(self, obj_type, x=None, y=None, dx=None, dy=None, radius=10):
        self.type = obj_type
        self.radius = radius
        self.increment_factor = 0.95  # Smaller objects will be smaller by this factor
        self.x = x if x is not None else random.randint(self.radius, WIDTH - self.radius)
        self.y = y if y is not None else random.randint(self.radius, HEIGHT - self.radius)
        self.dx = dx if dx is not None else random.uniform(-MAX_SPEED, MAX_SPEED)
        self.dy = dy if dy is not None else random.uniform(-MAX_SPEED, MAX_SPEED)
        self.color = self.get_color()

    def get_color(self):
        if self.type == ROCK:
            return (200, 0, 0)
        elif self.type == PAPER:
            return (0, 200, 0)
        elif self.type == SCISSORS:
            return (0, 0, 200)

    def move(self):
        self.dx += random.uniform(-0.5, 0.5)
        self.dy += random.uniform(-0.5, 0.5)
        self.dx = max(min(self.dx, MAX_SPEED), -MAX_SPEED)
        self.dy = max(min(self.dy, MAX_SPEED), -MAX_SPEED)
        self.x += self.dx
        self.y += self.dy
        if self.x <= self.radius or self.x >= WIDTH - self.radius:
            self.dx *= -1
        if self.y <= self.radius or self.y >= HEIGHT - self.radius:
            self.dy *= -1

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def check_collision(self, other):
        dist = ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
        if dist < self.radius + other.radius:
            self.resolve_collision(other, dist)  # Pass `dist` to resolve_collision
            return self.type != other.type  # Return True only if types are different
        return False

    def resolve_collision(self, other, dist):  # Accept `dist` as an argument
        overlap = 0.5 * (self.radius + other.radius - dist)
        # Correct the calculations using `dist`
        self.x += overlap * (self.x - other.x) / dist
        self.y += overlap * (self.y - other.y) / dist
        other.x -= overlap * (self.x - other.x) / dist
        other.y -= overlap * (self.y - other.y) / dist
        self.dx, other.dx = other.dx, self.dx
        self.dy, other.dy = other.dy, self.dy

    def transform(self, other):
        results = []
        if len(objects) + 3 <= MAX_OBJECTS:  # Check capacity for at least 3 new objects
            new_radius = self.radius * self.increment_factor
            new_x = self.x + random.uniform(-new_radius, new_radius)
            new_y = self.y + random.uniform(-new_radius, new_radius)
            new_dx = self.dx + random.uniform(-1, 1)
            new_dy = self.dy + random.uniform(-1, 1)
            new_type = self.determine_winner(self.type, other.type)
            results.append(RPSObject(new_type, x=new_x, y=new_y, dx=new_dx, dy=new_dy, radius=new_radius))

            new_radius = other.radius * self.increment_factor
            new_x = other.x + random.uniform(-new_radius, new_radius)
            new_y = other.y + random.uniform(-new_radius, new_radius)
            new_dx = other.dx + random.uniform(-1, 1)
            new_dy = other.dy + random.uniform(-1, 1)
            new_type = self.determine_winner(self.type, other.type)
            results.append(RPSObject(new_type, x=new_x, y=new_y, dx=new_dx, dy=new_dy, radius=new_radius))

            # Create an additional ball
            additional_radius = new_radius * self.increment_factor
            additional_x = self.x + random.uniform(-additional_radius, additional_radius)
            additional_y = self.y + random.uniform(-additional_radius, additional_radius)
            additional_dx = self.dx + random.uniform(-1, 1)
            additional_dy = self.dy + random.uniform(-1, 1)
            additional_type = self.determine_winner(self.type, other.type)
            results.append(RPSObject(additional_type, x=additional_x, y=additional_y, dx=additional_dx, dy=additional_dy, radius=additional_radius))
        return results

    def determine_winner(self, type1, type2):
        if (type1 == ROCK and type2 == SCISSORS) or (type2 == ROCK and type1 == SCISSORS):
            return ROCK
        elif (type1 == PAPER and type2 == ROCK) or (type2 == PAPER and type1 == ROCK):
            return PAPER
        elif (type1 == SCISSORS and type2 == PAPER) or (type2 == SCISSORS and type1 == PAPER):
            return SCISSORS
        else:
            return random.choice([type1, type2])  # Return a random type if they are the same

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
    new_objects = []
    removed_objects = set()
    for i in range(len(objects)):
        for j in range(i + 1, len(objects)):
            if objects[i] not in removed_objects and objects[j] not in removed_objects:
                if objects[i].check_collision(objects[j]):
                    new_objects.extend(objects[i].transform(objects[j]))
                    removed_objects.add(objects[i])
                    removed_objects.add(objects[j])
    objects = [obj for obj in objects if obj not in removed_objects] + new_objects
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
