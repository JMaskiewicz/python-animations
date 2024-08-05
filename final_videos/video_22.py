import pygame
import random
import math
import time
import imageio
from pydub import AudioSegment
import os
import colorsys
import io

# Video number
number = 22

# Directory path
video_dir = rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}'
if not os.path.exists(video_dir):
    os.makedirs(video_dir)

# Load MP3 file
music_path = r'C:\Users\jmask\Downloads\rush-e-piano-made-with-Voicemod.mp3'
music = AudioSegment.from_mp3(music_path)

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Create Pygame window
WIDTH, HEIGHT = 720, 1280
GREEN_ZONE_HEIGHT = 50
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Olympic Challenge Simulation")

# Constants
FPS, MAX_SPEED, TRAIL_LENGTH, GRAVITY = 60, 10, 20, 0.25
BALL_RADIUS = 15
OLYMPIC_COLORS = [(0, 112, 192), (255, 0, 0), (0, 0, 0), (255, 255, 0), (0, 176, 80)]
CIRCLE_RADIUS = 180  # Further increased radius for larger circles
# Adjusting positions to match the Olympic rings layout and moving them lower
CIRCLE_POSITIONS = [
    (WIDTH // 2 - 200, HEIGHT // 2),  # Blue (top left)
    (WIDTH // 2, HEIGHT // 2),  # Black (top middle)
    (WIDTH // 2 + 200, HEIGHT // 2),  # Red (top right)
    (WIDTH // 2 - 100, HEIGHT // 2 + 180),  # Yellow (bottom left)
    (WIDTH // 2 + 100, HEIGHT // 2 + 180)  # Green (bottom right)
]
WHITE = (150, 150, 150)
BLACK = (0, 0, 0)
GREY = (120, 120, 120)
GREEN = (0, 255, 0)


class Ball:
    def __init__(self, pos, speed):
        self.pos = pos
        self.speed = speed
        self.trail_positions = [pos[:] for _ in range(TRAIL_LENGTH)]  # Initialize with fixed length
        self.main_color = (255, 255, 255)  # White color

    def move(self):
        self.speed[1] += GRAVITY
        self.pos = [self.pos[0] + self.speed[0], self.pos[1] + self.speed[1]]
        self.trail_positions.append(self.pos[:])  # Add a copy of the current position
        if len(self.trail_positions) > TRAIL_LENGTH:
            self.trail_positions.pop(0)

        # Bounce off walls
        if self.pos[0] <= BALL_RADIUS or self.pos[0] >= WIDTH - BALL_RADIUS:
            self.speed[0] = -self.speed[0]
        if self.pos[1] <= BALL_RADIUS or self.pos[1] >= HEIGHT - BALL_RADIUS:
            self.speed[1] = -self.speed[1]

    def draw(self, screen):
        for i, pos in enumerate(self.trail_positions):
            hue_offset = (i * 0.05) % 1.0  # Adjust the offset to create the smooth rainbow effect
            hue = hue_offset % 1.0
            rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
            pygame.draw.circle(screen, color, (int(pos[0]), int(pos[1])), BALL_RADIUS)
        pygame.draw.circle(screen, self.main_color, (int(self.pos[0]), int(self.pos[1])), BALL_RADIUS)

    def check_collision(self, circles):
        for circle in circles:
            dist = math.hypot(self.pos[0] - circle.pos[0], self.pos[1] - circle.pos[1])
            if dist <= BALL_RADIUS + circle.radius:
                circle.radius -= 5  # Shrink the circle
                self.main_color = circle.color  # Change the ball's main color
                self.speed[1] = -self.speed[1]  # Bounce back
                play_music_segment(bounce_count * 0.15)
                break


class Circle:
    def __init__(self, pos, color):
        self.pos = pos
        self.color = color
        self.radius = CIRCLE_RADIUS

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.pos[0]), int(self.pos[1])), self.radius, 20)


def randomize_direction(ball_speed):
    angle = random.uniform(-math.pi / 6, math.pi / 6)
    speed = math.hypot(*ball_speed)
    new_angle = math.atan2(ball_speed[1], ball_speed[0]) + angle
    return [speed * math.cos(new_angle), speed * math.sin(new_angle)]


def play_music_segment(start_time, duration=0.25):
    segment = music[start_time * 1000:start_time * 1000 + duration * 1000]
    audio_segments.append((segment, time.time()))

    with io.BytesIO() as f:
        segment.export(f, format="wav")
        f.seek(0)
        pygame.mixer.Sound(f).play()


font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 64)
title_font = pygame.font.SysFont(None, 48)

circles = [Circle(pos, color) for pos, color in zip(CIRCLE_POSITIONS, OLYMPIC_COLORS)]
ball = Ball([WIDTH // 2, 20], [random.choice([-4, 4]), 4])
running = True
clock = pygame.time.Clock()
video_writer = imageio.get_writer(rf'{video_dir}\{number}_olympic_challenge.mp4', fps=FPS)
show_end_message = False
end_message_start_time = None
audio_segments = []
bounce_count = 0

while running:
    clock.tick(FPS)

    ball.move()
    ball.check_collision(circles)

    if ball.pos[1] >= HEIGHT - BALL_RADIUS:
        show_end_message = True
        end_message_start_time = time.time()

    screen.fill(WHITE)
    pygame.draw.rect(screen, GREEN, (0, HEIGHT - GREEN_ZONE_HEIGHT, WIDTH, GREEN_ZONE_HEIGHT))  # Draw green zone

    # Draw title
    title_text = title_font.render("Can ball go through the Olympic rings?", True, BLACK)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 50))

    # Draw circles
    for circle in circles:
        circle.draw(screen)
    ball.draw(screen)

    if show_end_message:
        game_over_texts = [
            large_font.render("LIKE", True, BLACK),
            large_font.render("FOLLOW", True, BLACK),
            large_font.render("SUBSCRIBE", True, BLACK),
            large_font.render("COMMENT WHAT TO DO NEXT", True, BLACK)
        ]
        for idx, text in enumerate(game_over_texts):
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 150 + 100 * idx))

        if time.time() - end_message_start_time >= 3:
            running = False

    # Add watermark text
    watermark_font = pygame.font.SysFont(None, 36)
    watermark_texts = [
        watermark_font.render("yt: @jbbm_motions", True, GREY),
        watermark_font.render("tiktok: @jbbm_motions", True, GREY),
        watermark_font.render("Subscribe for more!!!", True, GREY)
    ]
    for idx, text in enumerate(watermark_texts):
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 175 + idx * 30))

    frame = pygame.surfarray.array3d(screen).transpose([1, 0, 2])
    video_writer.append_data(frame)
    pygame.display.flip()

video_writer.close()
pygame.quit()
print("Video saved successfully!")
