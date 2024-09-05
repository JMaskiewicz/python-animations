import pygame
import pygame.midi
import random
import math
import time
import mido
import threading
import imageio
from pydub import AudioSegment
from pydub.generators import Sine
from moviepy.editor import VideoFileClip, AudioFileClip
import sys
import colorsys

# Initialize Pygame and Pygame MIDI
pygame.init()

# Create Pygame window
WIDTH, HEIGHT = 720, 1280
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball with Trailing Effect and Dynamic Circles")

# Load sound
pop_sound = pygame.mixer.Sound(r'C:\Users\jmask\Downloads\pop-39222.mp3')

# Constants
FPS = 60
MAX_SPEED = 3
TRAIL_LENGTH = 40
GRAVITY = 0.15
CIRCLE_SHRINK_RATE = 0.5
NEW_CIRCLE_INTERVAL = 1.1
MIN_CIRCLE_RADIUS = 5
SPEED_INCREASE_FACTOR = 1.02
CIRCLE_CREATION_ACCELERATION = 0.999
SPARK_COUNT = 100  # Number of sparks per circle destruction
BALL_RADIUS_increase = 1.02

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TRAIL_COLORS = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 127, 255), (0, 0, 255), (139, 0, 255)]

# Ball settings
BALL_RADIUS = 15
ball_pos = [WIDTH // 2, HEIGHT // 2]
ball_speed = [random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])]

# Circle settings
class Circle:
    def __init__(self, radius, color):
        self.radius = radius
        self.color = color

    def draw(self, screen):
        if self.radius > 0:
            pygame.draw.circle(screen, self.color, (WIDTH // 2, HEIGHT // 2), self.radius, 5)

    def update(self):
        self.radius -= CIRCLE_SHRINK_RATE

def hsv_to_rgb(h, s, v):
    rgb = colorsys.hsv_to_rgb(h, s, v)
    return tuple(int(255 * x) for x in rgb)

circles = [Circle(radius, hsv_to_rgb(random.random(), 1.0, 1.0)) for radius in range(400, 100, -35)]

# Trail settings
trail_positions = []
sparks = []

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

def reflect_velocity(velocity, normal):
    dot_product = velocity[0] * normal[0] + velocity[1] * normal[1]
    return [velocity[0] - 2 * dot_product * normal[0], velocity[1] - 2 * dot_product * normal[1]]

class Spark:
    def __init__(self, x, y, vx, vy, color):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.alive = True

    def move(self):
        if self.y < HEIGHT:
            self.vy += GRAVITY
            self.x += self.vx
            self.y += self.vy
        else:
            self.alive = False

    def draw(self, screen):
        if self.alive:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 3)

def create_sparks_from_circle(circle_center, circle_radius, color, sparks):
    for _ in range(SPARK_COUNT):
        angle = random.uniform(0, 2 * math.pi)  # Random angle
        x = circle_center[0] + math.cos(angle) * circle_radius
        y = circle_center[1] + math.sin(angle) * circle_radius
        vx = math.cos(angle) * random.uniform(1, 3)  # Horizontal velocity away from the center
        vy = math.sin(angle) * random.uniform(1, 3)  # Vertical velocity away from the center
        new_spark = Spark(x, y, vx, vy, color)
        sparks.append(new_spark)

# Setup video writer
video_writer = imageio.get_writer(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_1\1_ball_in_circles_sound.mp4', fps=FPS)

# Main game loop
running = True
clock = pygame.time.Clock()
start_time = time.time()
last_circle_add_time = start_time
no_circle_time = None

# Initialize font
font = pygame.font.SysFont(None, 48)
font_2 = pygame.font.SysFont(None, 32)
large_font = pygame.font.SysFont(None, 64)

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:
        ball_speed[1] += GRAVITY
        ball_pos[0] += ball_speed[0]
        ball_pos[1] += ball_speed[1]

        if ball_pos[0] <= BALL_RADIUS or ball_pos[0] >= WIDTH - BALL_RADIUS:
            ball_speed[0] = -ball_speed[0]
            randomize_direction(ball_speed)
            if no_circle_time is None:
                bounce_count += 1

        if ball_pos[1] <= BALL_RADIUS or ball_pos[1] >= HEIGHT - BALL_RADIUS:
            ball_speed[1] = -ball_speed[1]
            randomize_direction(ball_speed)
            if no_circle_time is None:
                bounce_count += 1

        for circle in circles[:]:
            dist = math.hypot(ball_pos[0] - WIDTH // 2, ball_pos[1] - HEIGHT // 2)
            if circle.radius - BALL_RADIUS <= dist <= circle.radius + BALL_RADIUS:
                normal = [(ball_pos[0] - WIDTH // 2) / dist, (ball_pos[1] - HEIGHT // 2) / dist]
                ball_speed = reflect_velocity(ball_speed, normal)
                create_sparks_from_circle([WIDTH // 2, HEIGHT // 2], circle.radius, circle.color, sparks)
                circles.remove(circle)
                increase_speed(ball_speed)
                BALL_RADIUS *= BALL_RADIUS_increase
                NEW_CIRCLE_INTERVAL *= CIRCLE_CREATION_ACCELERATION
                pop_sound.play()
                if no_circle_time is None:
                    bounce_count += 1
                break

        for circle in circles:
            circle.update()
        circles = [circle for circle in circles if circle.radius > MIN_CIRCLE_RADIUS]

        if circles:
            current_time = time.time()
            if current_time - last_circle_add_time >= NEW_CIRCLE_INTERVAL:
                new_circle = Circle(400, hsv_to_rgb(random.random(), 1.0, 1.0))
                circles.append(new_circle)
                last_circle_add_time = current_time
        else:
            if no_circle_time is None:
                no_circle_time = time.time()
            elif time.time() - no_circle_time >= 5:
                game_over = True
            else:
                show_end_message = True
                if end_message_start_time is None:
                    end_message_start_time = time.time()

        trail_positions.append(tuple(ball_pos))
        if len(trail_positions) > TRAIL_LENGTH:
            trail_positions.pop(0)

        # Update and draw sparks
        for spark in sparks[:]:
            spark.move()
            if not spark.alive:
                sparks.remove(spark)

    screen.fill(BLACK)

    # Add watermark text
    watermark_font = pygame.font.SysFont(None, 36)
    watermark_texts = [
        watermark_font.render("yt:@jbbm_motions", True, (150, 150, 150)),
        watermark_font.render("tiktok:@jbbm_motions", True, (150, 150, 150)),
        watermark_font.render("subscribe for more!", True, (150, 150, 150))
    ]
    for idx, text in enumerate(watermark_texts):
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 1100 + idx * 30))

    if not game_over:
        title_text = font_2.render("INCREASING IN SIZE BALL TRYING TO ESCAPE", True, WHITE)
        bounce_text = font.render(f"BOUNCES: {bounce_count}", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))
        screen.blit(bounce_text, (WIDTH // 2 - bounce_text.get_width() // 2, 150))

        for circle in circles:
            circle.draw(screen)

        for i, pos in enumerate(trail_positions):
            color = TRAIL_COLORS[i % len(TRAIL_COLORS)]
            pygame.draw.circle(screen, color, pos, BALL_RADIUS)

        pygame.draw.circle(screen, WHITE, ball_pos, BALL_RADIUS)

        for spark in sparks:
            spark.draw(screen)

        if show_end_message:
            game_over_text1 = large_font.render("LIKE", True, WHITE)
            game_over_text2 = large_font.render("FOLLOW", True, WHITE)
            game_over_text3 = large_font.render("SUBSCRIBE", True, WHITE)
            game_over_text4 = large_font.render("COMMENT WHAT TO DO NEXT", True, WHITE)
            screen.blit(game_over_text1, (WIDTH // 2 - game_over_text1.get_width() // 2, HEIGHT // 2 - 150))
            screen.blit(game_over_text2, (WIDTH // 2 - game_over_text2.get_width() // 2, HEIGHT // 2 - 50))
            screen.blit(game_over_text3, (WIDTH // 2 - game_over_text3.get_width() // 2, HEIGHT // 2 + 50))
            screen.blit(game_over_text4, (WIDTH // 2 - game_over_text4.get_width() // 2, HEIGHT // 2 + 150))

            if time.time() - end_message_start_time >= 5:
                game_over = True
    else:
        running = False

    frame = pygame.surfarray.array3d(screen)
    frame = frame.transpose([1, 0, 2])
    video_writer.append_data(frame)

    pygame.display.flip()

pygame.quit()
sys.exit()
