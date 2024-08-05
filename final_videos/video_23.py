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
number = 23

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
FPS, MAX_SPEED, TRAIL_LENGTH, GRAVITY = 60, 8, 20, 0.3
BALL_RADIUS = 15
OLYMPIC_COLORS = [(0, 255, 0), (255, 0, 0), (0, 0, 255)]  # Removed black color
SQUARE_SIZE = WIDTH // 3  # Increased size for squares
SQUARE_PADDING = 20  # Padding between squares

# Adjusting positions to match the new square layout with 3 rows
SQUARE_POSITIONS = [
    (WIDTH // 2 - SQUARE_SIZE - SQUARE_PADDING // 2, HEIGHT // 4 - SQUARE_SIZE // 2),  # Top row left
    (WIDTH // 2, HEIGHT // 4 - SQUARE_SIZE // 2),  # Top row middle
    (WIDTH // 2 + SQUARE_SIZE + SQUARE_PADDING // 2, HEIGHT // 4 - SQUARE_SIZE // 2),  # Top row right
    (WIDTH // 2 - SQUARE_SIZE - SQUARE_PADDING // 2, HEIGHT // 2 - SQUARE_SIZE // 2),  # Middle row left
    (WIDTH // 2, HEIGHT // 2 - SQUARE_SIZE // 2),  # Middle row middle
    (WIDTH // 2 + SQUARE_SIZE + SQUARE_PADDING // 2, HEIGHT // 2 - SQUARE_SIZE // 2),  # Middle row right
    (WIDTH // 2 - SQUARE_SIZE - SQUARE_PADDING // 2, 3 * HEIGHT // 4 - SQUARE_SIZE // 2),  # Bottom row left
    (WIDTH // 2, 3 * HEIGHT // 4 - SQUARE_SIZE // 2),  # Bottom row middle
    (WIDTH // 2 + SQUARE_SIZE + SQUARE_PADDING // 2, 3 * HEIGHT // 4 - SQUARE_SIZE // 2),  # Bottom row right
]

BLACK = (0, 0, 0)
GREY = (60, 60, 60)


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

    def check_collision(self, squares):
        for square in squares:
            if (square.pos[0] - square.size // 2 <= self.pos[0] <= square.pos[0] + square.size // 2 and
                    square.pos[1] - square.size // 2 <= self.pos[1] <= square.pos[1] + square.size // 2):
                square.size -= 5  # Shrink the square
                self.main_color = square.color  # Change the ball's main color
                self.speed[1] = -self.speed[1]  # Bounce back
                play_music_segment(bounce_count * 0.15)
                break


class Square:
    def __init__(self, pos, color):
        self.pos = pos
        self.color = color
        self.size = SQUARE_SIZE

    def draw(self, screen):
        pygame.draw.rect(screen, self.color,
                         (self.pos[0] - self.size // 2, self.pos[1] - self.size // 2, self.size, self.size), 10)


def randomize_direction(ball_speed):
    angle = random.uniform(-math.pi / 6, math.pi / 6)
    speed = math.hypot(*ball_speed)
    new_angle = math.atan2(ball_speed[1], ball_speed[0]) + angle
    return [speed * math.cos(new_angle), speed * math.sin(new_angle)]


def play_music_segment(start_time, duration=0.15):
    segment = music[start_time * 1000:start_time * 1000 + duration * 1000]
    audio_segments.append((segment, time.time()))

    with io.BytesIO() as f:
        segment.export(f, format="wav")
        f.seek(0)
        pygame.mixer.Sound(f).play()


font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 64)
title_font = pygame.font.SysFont(None, 72)

squares = [Square(pos, color) for pos, color in zip(SQUARE_POSITIONS, OLYMPIC_COLORS * 3)]
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
    ball.check_collision(squares)

    if ball.pos[1] >= HEIGHT - BALL_RADIUS:
        show_end_message = True
        end_message_start_time = time.time()

    screen.fill(BLACK)
    pygame.draw.rect(screen, (0, 100, 0), (0, HEIGHT - GREEN_ZONE_HEIGHT, WIDTH, GREEN_ZONE_HEIGHT))  # Draw green zone

    # Draw title
    title_text = title_font.render("Can the ball go through the Olympic squares?", True, (255, 255, 255))
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 50))

    # Draw squares
    for square in squares:
        square.draw(screen)
    ball.draw(screen)

    if show_end_message:
        game_over_texts = [
            large_font.render("LIKE", True, (255, 255, 255)),
            large_font.render("FOLLOW", True, (255, 255, 255)),
            large_font.render("SUBSCRIBE", True, (255, 255, 255)),
            large_font.render("COMMENT WHAT TO DO NEXT", True, (255, 255, 255))
        ]
        for idx, text in enumerate(game_over_texts):
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 150 + 100 * idx))
        if time.time() - end_message_start_time >= 3:
            running = False

    # Add watermark text
    watermark_font = pygame.font.SysFont(None, 36)
    watermark_texts = [
        watermark_font.render("yt:@jbbm_motions", True, GREY),
        watermark_font.render("tiktok:@jbbm_motions", True, GREY),
        watermark_font.render("subscribe for more!", True, GREY)
    ]
    for idx, text in enumerate(watermark_texts):
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 175 + idx * 30))

    frame = pygame.surfarray.array3d(screen).transpose([1, 0, 2])
    video_writer.append_data(frame)
    pygame.display.flip()

video_writer.close()
pygame.quit()
print("Video saved successfully!")
