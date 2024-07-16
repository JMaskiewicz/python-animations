import pygame
import random
import os

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Create Pygame window
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tech Company Logos Animation")

# Constants
FPS = 60
NUM_OBJECTS = 10
MAX_SPEED = 3  # Maximum speed of objects
MUSIC_PLAY_TIME = 1000  # Play 1 second of music for each collision in milliseconds

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Load logos
LOGO_DIR = "tech"
logos = ["amazon.jpg", "apple.png", "meta.png", "microsoft.jpg", "NVIDIA.jpg", "Tesla.jpg"]
logo_images = {logo: pygame.image.load(os.path.join(LOGO_DIR, logo)).convert_alpha() for logo in logos}

# Check if images are loaded correctly
for logo in logos:
    if logo not in logo_images:
        print(f"Failed to load {logo}")
    else:
        print(f"Loaded {logo}")

# Load music
pygame.mixer.music.load(rf"D:\rower\Freestailo mix.mp3")
music_length = pygame.mixer.Sound(rf"D:\rower\Freestailo mix.mp3").get_length() * 100000  # Convert length to milliseconds
current_music_pos = 0  # Start at the beginning of the song

def create_circular_mask(radius):
    mask_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(mask_surface, (255, 255, 255, 255), (radius, radius), radius)
    mask = pygame.mask.from_surface(mask_surface)
    return mask_surface, mask

# Object class
class RPSObject:
    def __init__(self, logo_name):
        self.logo_name = logo_name
        self.radius = 20  # Adjust to match the logo size
        self.increment_factor = 1.25
        self.x = random.randint(self.radius, WIDTH - self.radius)
        self.y = random.randint(self.radius, HEIGHT - self.radius)
        self.dx = random.uniform(-MAX_SPEED, MAX_SPEED)
        self.dy = random.uniform(-MAX_SPEED, MAX_SPEED)
        self.update_logo_and_mask()

    def update_logo_and_mask(self):
        # Resize logo image based on the current radius
        original_logo = logo_images[self.logo_name]
        self.logo_image = pygame.transform.smoothscale(original_logo, (int(self.radius * 2), int(self.radius * 2)))
        self.mask_surface, self.mask = create_circular_mask(int(self.radius))

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
        temp_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        temp_surface.blit(self.logo_image, (0, 0))
        temp_surface.blit(self.mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        screen.blit(temp_surface, (self.x - self.radius, self.y - self.radius))

    def check_collision(self, other):
        dist = ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5
        if dist < self.radius + other.radius:
            self.play_collision_music()  # Play music segment
            self.resolve_collision(other, dist)
            self.transform(other)

    def play_collision_music(self):
        global current_music_pos
        # Play a short segment of the music
        pygame.mixer.music.play(0, start=current_music_pos / 100000.0)
        pygame.time.set_timer(pygame.USEREVENT, MUSIC_PLAY_TIME)
        current_music_pos = (current_music_pos + MUSIC_PLAY_TIME) % music_length

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
        if self.logo_name != other.logo_name:
            if random.random() < other.radius / (other.radius + self.radius):
                other.logo_name = self.logo_name
                other.radius *= self.increment_factor
                other.update_logo_and_mask()
            else:
                self.logo_name = other.logo_name
                self.radius *= self.increment_factor
                self.update_logo_and_mask()

# Initialize objects
objects = [RPSObject(random.choice(logos)) for _ in range(NUM_OBJECTS)]

# Main loop
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.USEREVENT:
            pygame.mixer.music.stop()  # Stop the music after the segment is played

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
    first_logo = objects[0].logo_name
    if all(obj.logo_name == first_logo for obj in objects):
        running = False

pygame.quit()
