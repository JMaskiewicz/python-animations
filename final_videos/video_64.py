import pygame
import pygame.midi
import random
import math
import time
import mido
import threading
import imageio
import colorsys
import io
from pydub import AudioSegment
from pydub.generators import Sine
from moviepy.editor import VideoFileClip, AudioFileClip
import os

# Video number
number = 64

# Directory path
video_dir = rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}'

# Check if there is a folder for this video
if not os.path.exists(video_dir):
    os.makedirs(video_dir)

# Initialize Pygame and Pygame MIDI
pygame.init()
pygame.midi.init()
pygame.mixer.init()

# Open a MIDI output port
midi_out = pygame.midi.Output(0)
instrument = 0  # Piano
midi_out.set_instrument(instrument)

# Load MP3 file
music_path = r'C:\Users\jmask\Downloads\Jaxomy x Agatino Romero x Raffaella Carra - Pedro.mp3'
music = AudioSegment.from_mp3(music_path)

# Create Pygame window
WIDTH, HEIGHT = 720, 1280  # Adjusted to be divisible by 16
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball with Moving Lines")
X = 45
# Constants
FPS = 60
MAX_SPEED = 10  # Maximum initial speed of ball
TRAIL_LENGTH = 0  # Number of trail segments
GRAVITY = 0.5  # Gravity effect
LINE_HEIGHT = 20  # Line height
LINE_RESPAWN_RATE = random.randint(X, 2*X)  # Number of frames between line respawns
LINE_SPEED = 5  # Speed of lines moving upwards
SPEED_INCREASE_FACTOR = 1.15  # Factor to increase speed after each bounce
LINE_SPEED_BOOST = 0.002  # Line speed increase after each hit
MIN_SPEED = 5  # Minimum speed to prevent the ball from stopping
GAME_DURATION = 50  # Duration of the game in seconds

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LINE_COLORS = [(255, 105, 180), (135, 206, 250), (144, 238, 144), (255, 182, 193), (255, 160, 122), (173, 255, 47), (127, 255, 212)]

# Ball settings
BALL_RADIUS = 20
ball_pos = [WIDTH // 2, HEIGHT // 3]
ball_speed = [12, 6]

# Line settings
class Line:
    def __init__(self, color, y):
        self.color = color
        self.y = y

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (0, self.y, WIDTH, LINE_HEIGHT))

    def update(self):
        self.y -= LINE_SPEED

# Initialize with three lines at different starting positions
lines = [Line(random.choice(LINE_COLORS), HEIGHT - i * (HEIGHT // 5)) for i in range(4)]

# Trail settings
trail_positions = []
trail_colors = []  # Store trail colors for hue adjustment

# Store hit points for permanent lines
hit_points = []

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
    angle = random.uniform(-math.pi / 6, math.pi / 6)  # Random angle between -30 and 30 degrees
    speed = math.hypot(ball_speed[0], ball_speed[1])  # Current speed magnitude
    new_angle = math.atan2(ball_speed[1], ball_speed[0]) + angle
    ball_speed[0] = speed * math.cos(new_angle)
    ball_speed[1] = speed * math.sin(new_angle)

def increase_speed(ball_speed):
    ball_speed[0] *= SPEED_INCREASE_FACTOR
    ball_speed[1] *= SPEED_INCREASE_FACTOR
    # Ensure the ball's speed does not fall below a minimum threshold
    if abs(ball_speed[0]) < MIN_SPEED:
        ball_speed[0] = MIN_SPEED if ball_speed[0] > 0 else -MIN_SPEED
    if abs(ball_speed[1]) < MIN_SPEED:
        ball_speed[1] = MIN_SPEED if ball_speed[1] > 0 else -MIN_SPEED

def play_music_segment(start_time, duration=0.3):
    segment = music[start_time * 1000:start_time * 1000 + duration * 1000]
    audio_segments.append((segment, time.time()))

    with io.BytesIO() as f:
        segment.export(f, format="wav")
        f.seek(0)
        pygame.mixer.Sound(f).play()

def reflect_velocity(velocity, normal):
    dot_product = velocity[0] * normal[0] + velocity[1] * normal[1]
    return [velocity[0] - 2 * dot_product * normal[0], velocity[1] - 2 * dot_product * normal[1]]

def draw_lines(screen, hit_points):
    for point in hit_points:
        hue = random.random()  # Random hue for each line
        rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
        pygame.draw.line(screen, color, point, ball_pos, 2)

def draw_sparks(screen, pos, color, radius=10, num_sparks=10):
    for _ in range(num_sparks):
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(0, radius)
        spark_pos = (int(pos[0] + distance * math.cos(angle)), int(pos[1] + distance * math.sin(angle)))
        pygame.draw.circle(screen, color, spark_pos, 2)

# Initialize font
font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 68)

# Setup video writer
video_writer = imageio.get_writer(rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_ball_in_lines_sound.mp4', fps=FPS)

# Main game loop
running = True
clock = pygame.time.Clock()
start_time = time.time()
no_line_time = None
trail_length = TRAIL_LENGTH  # Initial trail length

line_respawn_counter = 0  # Counter for line respawn timing

# wait 1 sec
while time.time() - start_time < 1:
    clock.tick(FPS)

while running:
    LINE_RESPAWN_RATE = random.randint(math.floor(X), math.floor(2*X))
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    current_time = time.time()
    elapsed_time = current_time - start_time

    # Update ball position
    ball_speed[1] += GRAVITY
    new_ball_pos = [ball_pos[0] + ball_speed[0], ball_pos[1] + ball_speed[1]]

    # Check for collision with lines
    lines_to_remove = []
    for line in lines:
        if (line.y <= new_ball_pos[1] + BALL_RADIUS <= line.y + LINE_HEIGHT):
            # Check if the ball passes through the line in one frame
            if ball_pos[1] - BALL_RADIUS < line.y + LINE_HEIGHT <= new_ball_pos[1] + BALL_RADIUS:
                ball_speed[1] = -ball_speed[1]
                if abs(ball_speed[1]) < 10:
                    ball_speed[1] -= 2
                lines_to_remove.append(line)  # Mark the line for removal
                bounce_count += 1
                trail_length += 0  # Increase trail length
                spark_color = random.choice(LINE_COLORS)
                draw_sparks(screen, ball_pos, spark_color)  # Draw sparks at collision point
                LINE_SPEED += LINE_SPEED_BOOST  # Increase line speed
                play_music_segment(bounce_count * 0.3)
                break

    # Remove lines that were collided with
    for line in lines_to_remove:
        lines.remove(line)

    # Update ball position after checking for collisions
    ball_pos = new_ball_pos

    # Ball collision with walls
    if ball_pos[0] - BALL_RADIUS <= 0:
        ball_pos[0] = BALL_RADIUS  # Ensure the ball stays within bounds
        ball_speed[0] = -ball_speed[0]
        randomize_direction(ball_speed)
        hit_points.append((ball_pos[0], ball_pos[1]))
        LINE_SPEED += LINE_SPEED_BOOST  # Increase line speed
        play_music_segment(bounce_count * 0.3)
        bounce_count += 1

    elif ball_pos[0] + BALL_RADIUS >= WIDTH:
        ball_pos[0] = WIDTH - BALL_RADIUS  # Ensure the ball stays within bounds
        ball_speed[0] = -ball_speed[0]
        randomize_direction(ball_speed)
        hit_points.append((ball_pos[0], ball_pos[1]))
        LINE_SPEED += LINE_SPEED_BOOST  # Increase line speed
        play_music_segment(bounce_count * 0.3)
        bounce_count += 1

    if ball_pos[1] - BALL_RADIUS <= 0:
        ball_pos[1] = BALL_RADIUS  # Ensure the ball stays within bounds
        ball_speed[1] = -ball_speed[1]
        randomize_direction(ball_speed)
        hit_points.append((ball_pos[0], ball_pos[1]))
        LINE_SPEED += LINE_SPEED_BOOST  # Increase line speed
        play_music_segment(bounce_count * 0.3)
        bounce_count += 1

    elif ball_pos[1] + BALL_RADIUS >= HEIGHT:
        ball_pos[1] = HEIGHT - BALL_RADIUS  # Ensure the ball stays within bounds
        ball_speed[1] = -ball_speed[1]
        randomize_direction(ball_speed)
        hit_points.append((ball_pos[0], ball_pos[1]))
        LINE_SPEED += LINE_SPEED_BOOST  # Increase line speed
        play_music_segment(bounce_count * 0.3)
        bounce_count += 1

    # Update lines
    for line in lines:
        line.update()

    # Remove lines that are off the screen
    lines = [line for line in lines if line.y + LINE_HEIGHT > 0]

    # Respawn lines if not in end message state
    if not show_end_message:
        line_respawn_counter += 1
        if line_respawn_counter >= LINE_RESPAWN_RATE:
            X = X * 1.025
            line_respawn_counter = 0
            new_line = Line(random.choice(LINE_COLORS), HEIGHT)
            lines.append(new_line)

    # Check if there are no lines on screen
    if not lines and not show_end_message and current_time - start_time >= 5:
        show_end_message = True
        end_message_start_time = time.time()

    # Update trail positions and colors with hue
    trail_positions.append(tuple(ball_pos))
    hue = (elapsed_time % 360) / 360.0
    rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
    trail_colors.append(color)

    if len(trail_positions) > trail_length:
        trail_positions.pop(0)
        trail_colors.pop(0)

    # Draw everything
    screen.fill(BLACK)

    # Draw title and bounce counter
    title_text = font.render("CAN IT REACH BOTTOM?", True, WHITE)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))
    bounce_text = font.render(f"BOUNCES: {bounce_count}", True, WHITE)
    screen.blit(bounce_text, (WIDTH // 2 - bounce_text.get_width() // 2, 200))

    # Draw lines
    for line in lines:
        line.draw(screen)

    # Draw permanent lines from hit points
    draw_lines(screen, hit_points)

    # Draw trail
    for i, pos in enumerate(trail_positions):
        pygame.draw.circle(screen, trail_colors[i], pos, BALL_RADIUS)

    # Draw ball
    pygame.draw.circle(screen, WHITE, ball_pos, BALL_RADIUS)

    # Draw end message if needed
    if show_end_message:
        game_over_text1 = large_font.render("LIKE", True, WHITE)
        game_over_text2 = large_font.render("FOLLOW", True, WHITE)
        game_over_text3 = large_font.render("SUBSCRIBE", True, WHITE)
        game_over_text4 = large_font.render("COMMENT WHAT TO DO NEXT", True, WHITE)
        screen.blit(game_over_text1, (WIDTH // 2 - game_over_text1.get_width() // 2, HEIGHT // 2 - 150))
        screen.blit(game_over_text2, (WIDTH // 2 - game_over_text2.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(game_over_text3, (WIDTH // 2 - game_over_text3.get_width() // 2, HEIGHT // 2 + 50))
        screen.blit(game_over_text4, (WIDTH // 2 - game_over_text4.get_width() // 2, HEIGHT // 2 + 150))

        # Check if the 5-second period is over
        if time.time() - end_message_start_time >= 3:
            running = False

    # Add watermark text
    watermark_font = pygame.font.SysFont(None, 36)
    watermark_texts = [
        watermark_font.render("yt:@jbbm_motions", True, (30,30, 30)),
        watermark_font.render("tiktok:@jbbm_motions", True, (30,30, 30)),
        watermark_font.render("subscribe for more!", True, (30,30, 30))
    ]
    for idx, text in enumerate(watermark_texts):
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 500 + idx * 30))


    # Capture the screen for video
    frame = pygame.surfarray.array3d(screen)
    frame = frame.transpose([1, 0, 2])  # Pygame uses (width, height, channels), ImageIO uses (height, width, channels)
    video_writer.append_data(frame)

    pygame.display.flip()

print('capturing video')

video_writer.close()
pygame.quit()
