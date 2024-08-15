import pygame
import random
import math
import time
import imageio
import os
import io
from pydub import AudioSegment

# Video number
number = 45

# Directory path
video_dir = rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}'

# Check if there is a folder for this video
if not os.path.exists(video_dir):
    os.makedirs(video_dir)

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Load MP3 file
music_path = r'C:\Users\jmask\Downloads\Eiffel 65 - Im blue (PedroDJDaddy Trap 2018 Remix).mp3'
music = AudioSegment.from_mp3(music_path)

# Create Pygame window
WIDTH, HEIGHT = 720, 1280
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball with Moving Triangles")

# Constants
FPS = 60
MAX_SPEED = 5
TRAIL_LENGTH = 2
GRAVITY = 0.3
TRIANGLE_HEIGHT = 40
TRIANGLE_BASE = 80
TRIANGLE_RESPAWN_RATE = random.randint(3, 3)
TRIANGLE_SPEED = 4
SPEED_INCREASE_FACTOR = 1.00002
MIN_SPEED = 5

# Colors
BLACK, WHITE, GREY = (0, 0, 0), (255, 255, 255), (30, 30, 30)
TRIANGLE_COLORS = [
    (135, 206, 235),  # Sky Blue
    (70, 130, 180),   # Steel Blue
    (0, 191, 255),    # Deep Sky Blue
    (30, 144, 255),   # Dodger Blue
    (100, 149, 237),  # Cornflower Blue
    (65, 105, 225),   # Royal Blue
    (0, 0, 255)       # Blue
]
TRAIL_COLORS = [(255, 1 * i, 0) for i in range(1, 250)]

# Ball settings
BALL_RADIUS = 20
ball_pos = [WIDTH // 2, HEIGHT // 3]
ball_speed = [random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])]

# Triangle settings
class Triangle:
    def __init__(self, color, x):
        self.color = color
        self.x = x
        self.y = HEIGHT
        self.base = TRIANGLE_BASE
        self.height = TRIANGLE_HEIGHT
        self.vertices = [
            (self.x, self.y),
            (self.x + self.base, self.y),
            (self.x + self.base // 2, self.y - self.height)
        ]

    def draw(self, screen):
        pygame.draw.polygon(screen, self.color, self.vertices)

    def update(self):
        self.y -= TRIANGLE_SPEED
        self.vertices = [
            (self.x, self.y),
            (self.x + self.base, self.y),
            (self.x + self.base // 2, self.y - self.height)
        ]

# Initialize with three triangles at different starting positions
triangles = [Triangle(random.choice(TRIANGLE_COLORS), random.randint(0, WIDTH)) for _ in range(4)]

# Trail settings
trail_positions = []

left_hand_index = 0
right_hand_play_count = 0
bounce_count = 0
game_over = False
show_end_message = False
end_message_start_time = None

NOTE_OFF_EVENT = pygame.USEREVENT + 1

# Create a list to store audio segments
audio_segments = []

def randomize_direction(ball_speed):
    angle = random.uniform(-math.pi / 6, math.pi / 6)
    speed = math.hypot(ball_speed[0], ball_speed[1])
    new_angle = math.atan2(ball_speed[1], ball_speed[0]) + angle
    ball_speed[0] = speed * math.cos(new_angle)
    ball_speed[1] = speed * math.sin(new_angle)

def increase_speed(ball_speed):
    ball_speed[0] *= SPEED_INCREASE_FACTOR
    ball_speed[1] *= SPEED_INCREASE_FACTOR
    if abs(ball_speed[0]) < MIN_SPEED:
        ball_speed[0] = MIN_SPEED if ball_speed[0] > 0 else -MIN_SPEED
    if abs(ball_speed[1]) < MIN_SPEED:
        ball_speed[1] = MIN_SPEED if ball_speed[1] > 0 else -MIN_SPEED

def play_music_segment(start_time, duration=0.25):
    segment = music[int(start_time * 1000):int(start_time * 1000 + duration * 1000)]
    audio_segments.append((segment, time.time()))

    with io.BytesIO() as f:
        segment.export(f, format="wav")
        f.seek(0)
        pygame.mixer.Sound(f).play()

def reflect_velocity(velocity, normal):
    dot_product = velocity[0] * normal[0] + velocity[1] * normal[1]
    return [velocity[0] - 2 * dot_product * normal[0], velocity[1] - 2 * dot_product * normal[1]]

def check_collision_with_triangle(ball_pos, triangle):
    # Collision detection logic for triangle
    for i in range(3):
        p1 = triangle.vertices[i]
        p2 = triangle.vertices[(i + 1) % 3]
        edge_vector = (p2[0] - p1[0], p2[1] - p1[1])
        edge_normal = (-edge_vector[1], edge_vector[0])
        ball_to_p1 = (ball_pos[0] - p1[0], ball_pos[1] - p1[1])
        if ball_to_p1[0] * edge_normal[0] + ball_to_p1[1] * edge_normal[1] > BALL_RADIUS:
            return False, None

    # Find normal based on triangle's orientation
    normal = (0, -1)  # Assuming upward-pointing triangles
    return True, normal

# Initialize font
font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 68)

# Setup video writer
video_writer = imageio.get_writer(rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_ball_in_triangles_sound.mp4', fps=FPS)

# Main game loop
running = True
clock = pygame.time.Clock()
start_time = time.time()
trail_length = TRAIL_LENGTH

triangle_respawn_counter = 0

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    current_time = time.time()
    elapsed_time = current_time - start_time

    # Update ball position
    ball_speed[1] += GRAVITY
    ball_pos[0] += ball_speed[0]
    ball_pos[1] += ball_speed[1]

    if not game_over:

        # Ball collision with walls
        if ball_pos[0] - BALL_RADIUS <= 0:
            ball_pos[0] = BALL_RADIUS
            ball_speed[0] = -ball_speed[0]
            randomize_direction(ball_speed)

        elif ball_pos[0] + BALL_RADIUS >= WIDTH:
            ball_pos[0] = WIDTH - BALL_RADIUS
            ball_speed[0] = -ball_speed[0]
            randomize_direction(ball_speed)

        if ball_pos[1] - BALL_RADIUS <= 0:
            ball_pos[1] = BALL_RADIUS
            ball_speed[1] = -ball_speed[1]
            randomize_direction(ball_speed)

        elif ball_pos[1] + BALL_RADIUS >= HEIGHT and not show_end_message:
            show_end_message = True
            end_message_start_time = time.time()

        # Check collision with triangles
        triangles_to_remove = []
        for triangle in triangles:
            collision, normal = check_collision_with_triangle(ball_pos, triangle)
            if collision:
                ball_speed = reflect_velocity(ball_speed, normal)
                triangles_to_remove.append(triangle)
                bounce_count += 1
                trail_length += 1
                if trail_length > 75:
                    TRIANGLE_RESPAWN_RATE = 4
                if trail_length > 125:
                    trail_length -= 1
                    TRIANGLE_RESPAWN_RATE = 4
                play_music_segment(elapsed_time)
                increase_speed(ball_speed)
                break

        # Remove triangles that were collided with
        for triangle in triangles_to_remove:
            triangles.remove(triangle)

        # Update triangles
        for triangle in triangles:
            triangle.update()

        # Remove triangles that are off the screen
        triangles = [triangle for triangle in triangles if triangle.y + TRIANGLE_HEIGHT > 0]

        # Respawn triangles if not in end message state
        if not show_end_message:
            triangle_respawn_counter += 1
            if triangle_respawn_counter >= TRIANGLE_RESPAWN_RATE:
                triangle_respawn_counter = 0
                new_triangle = Triangle(random.choice(TRIANGLE_COLORS), random.randint(-100, WIDTH+100))
                triangles.append(new_triangle)

    # Update trail positions
    trail_positions.append(tuple(ball_pos))
    if len(trail_positions) > trail_length:
        trail_positions.pop(0)

    # Draw everything
    screen.fill(BLACK)

    if not game_over:
        # Draw title and bounce counter
        title_text = font.render("Ball Escaping Moving Triangles", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))
        bounce_text = font.render(f"BOUNCES: {bounce_count}", True, WHITE)
        screen.blit(bounce_text, (WIDTH // 2 - bounce_text.get_width() // 2, 300))

        # Draw triangles
        for triangle in triangles:
            triangle.draw(screen)

        # Draw trail
        for i, pos in enumerate(trail_positions):
            color = TRAIL_COLORS[i % len(TRAIL_COLORS)]
            pygame.draw.circle(screen, color, pos, BALL_RADIUS)

        # Draw ball
        pygame.draw.circle(screen, WHITE, ball_pos, BALL_RADIUS)

        # Draw end message if needed
        if show_end_message:
            game_over_texts = [
                large_font.render("LIKE", True, WHITE),
                large_font.render("FOLLOW", True, WHITE),
                large_font.render("SUBSCRIBE", True, WHITE),
                large_font.render("COMMENT WHAT TO DO NEXT", True, WHITE)
            ]
            for idx, text in enumerate(game_over_texts):
                screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 100 + 100 * idx))
            if time.time() - end_message_start_time >= 3:
                game_over = True

        # Add watermark text
        watermark_font = pygame.font.SysFont(None, 36)
        watermark_texts = [
            watermark_font.render("yt:@jbbm_motions", True, GREY),
            watermark_font.render("tiktok:@jbbm_motions", True, GREY),
            watermark_font.render("subscribe for more!", True, GREY)
        ]
        for idx, text in enumerate(watermark_texts):
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 175 + idx * 30))
    else:
        running = False

    # Capture the screen for video
    frame = pygame.surfarray.array3d(screen)
    frame = frame.transpose([1, 0, 2])
    video_writer.append_data(frame)

    pygame.display.flip()

video_writer.close()
pygame.quit()
print("Video with sound saved successfully!")
