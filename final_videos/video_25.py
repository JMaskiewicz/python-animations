import pygame
import random
import math
import time
import imageio
import os
import io
from pydub import AudioSegment

# Video number
number = 25

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
pygame.display.set_caption("Ball with Moving Lines")

# Constants
FPS = 60
MAX_SPEED = 5
TRAIL_LENGTH = 3
GRAVITY = 0.4
LINE_HEIGHT = 20
LINE_RESPAWN_RATE = random.randint(5, 10)
LINE_SPEED = 4
SPEED_INCREASE_FACTOR = 1.005
MIN_SPEED = 5

# Colors
BLACK, WHITE, GREY = (0, 0, 0), (255, 255, 255), (50, 50, 50)
LINE_COLORS = [
    (135, 206, 235),  # Sky Blue
    (70, 130, 180),   # Steel Blue
    (0, 191, 255),    # Deep Sky Blue
    (30, 144, 255),   # Dodger Blue
    (100, 149, 237),  # Cornflower Blue
    (65, 105, 225),   # Royal Blue
    (0, 0, 255)       # Blue
]
TRAIL_COLORS = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 127, 255), (0, 0, 255), (139, 0, 255)]

# Ball settings
BALL_RADIUS = 20
ball_pos = [WIDTH // 2, HEIGHT // 3]
ball_speed = [random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])]

# Line settings
class Line:
    def __init__(self, color, x):
        self.color = color
        self.x = x
        self.y = HEIGHT
        self.width = random.randint(50, 300)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, LINE_HEIGHT))

    def update(self):
        self.y -= LINE_SPEED

# Initialize with three lines at different starting positions
lines = [Line(random.choice(LINE_COLORS), random.randint(0, WIDTH - 200)) for _ in range(4)]

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

# Initialize font
font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 68)

# Setup video writer
video_writer = imageio.get_writer(rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_ball_in_lines_sound.mp4', fps=FPS)

# Main game loop
running = True
clock = pygame.time.Clock()
start_time = time.time()
trail_length = TRAIL_LENGTH

line_respawn_counter = 0

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

        # Check collision with lines
        lines_to_remove = []
        for line in lines:
            if (line.y <= ball_pos[1] + BALL_RADIUS <= line.y + LINE_HEIGHT and
                    line.x <= ball_pos[0] <= line.x + line.width):
                ball_speed[1] = -ball_speed[1]
                lines_to_remove.append(line)
                bounce_count += 1
                trail_length += 1
                play_music_segment(elapsed_time)
                increase_speed(ball_speed)
                break

        # Remove lines that were collided with
        for line in lines_to_remove:
            lines.remove(line)

        # Update lines
        for line in lines:
            line.update()

        # Remove lines that are off the screen
        lines = [line for line in lines if line.y + LINE_HEIGHT > 0]

        # Respawn lines if not in end message state
        if not show_end_message:
            line_respawn_counter += 1
            if line_respawn_counter >= LINE_RESPAWN_RATE:
                line_respawn_counter = 0
                new_line = Line(random.choice(LINE_COLORS), random.randint(0, WIDTH - 200))
                lines.append(new_line)

    # Update trail positions
    trail_positions.append(tuple(ball_pos))
    if len(trail_positions) > trail_length:
        trail_positions.pop(0)

    # Draw everything
    screen.fill(BLACK)

    if not game_over:
        # Draw title and bounce counter
        title_text = font.render("Ball Escaping Moving Lines", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))
        bounce_text = font.render(f"BOUNCES: {bounce_count}", True, WHITE)
        screen.blit(bounce_text, (WIDTH // 2 - bounce_text.get_width() // 2, 300))

        # Draw lines
        for line in lines:
            line.draw(screen)

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
