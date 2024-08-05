import pygame
import random
import time
import imageio
from pydub import AudioSegment
import os
import io
import math

# Video number
number = 26

# Directory path
video_dir = rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}'
if not os.path.exists(video_dir):
    os.makedirs(video_dir)

# Load MP3 file
music_path = r'C:\Users\jmask\Downloads\Jaxomy x Agatino Romero x Raffaella Carra - Pedro.mp3'
music = AudioSegment.from_mp3(music_path)

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Create Pygame window
WIDTH, HEIGHT = 720, 1280  # Adjusted to be divisible by 16
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball with Trailing Effect and Dynamic Circles")

# Constants
FPS = 60
MAX_SPEED = 4  # Maximum initial speed of ball
TRAIL_LENGTH = 40  # Number of trail segments
GRAVITY = 0.1  # Gravity effect
CIRCLE_SHRINK_RATE = 2  # Rate at which circles shrink
NEW_CIRCLE_INTERVAL = 0.15  # Initial time interval in seconds to add new circle
MIN_CIRCLE_RADIUS = 5  # Minimum circle radius before disappearing
SPEED_INCREASE_FACTOR = 1.002  # Factor to increase speed after each bounce
CIRCLE_CREATION_ACCELERATION = 0.999  # Factor to decrease interval for circle creation after each bounce

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CIRCLE_COLORS = [(0, 255, 255), (255, 0, 0), (255, 255, 0)]  # Glowy blue, red, and yellow
TRAIL_COLORS = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 127, 255), (0, 0, 255), (139, 0, 255)]

# Ball settings
BALL_RADIUS = 15
ball_positions = [[WIDTH // 2 + 50, HEIGHT // 2], [WIDTH // 2 - 50, HEIGHT // 2]]  # Two balls
ball_speeds = [
    [random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])],
    [random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])]
]

GREY = (50, 50, 50)

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

# Adjusted initial circle radii to fit within the screen
circles = [Circle(radius, random.choice(CIRCLE_COLORS)) for radius in range(400, 100, -35)]  # Adjusted radii to fit better

# Trail settings
trail_positions = [[] for _ in range(2)]  # Separate trail positions for each ball

# Particle system for sparks
class Particle:
    def __init__(self, position):
        self.position = list(position)
        self.velocity = [random.uniform(-2, 2), random.uniform(-2, 2)]
        self.lifetime = random.uniform(0.5, 1.0)

    def update(self, dt):
        self.lifetime -= dt
        self.position[0] += self.velocity[0] * dt * 60
        self.position[1] += self.velocity[1] * dt * 60

    def draw(self, screen):
        if self.lifetime > 0:
            pygame.draw.circle(screen, WHITE, (int(self.position[0]), int(self.position[1])), 2)

particles = []

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

def reflect_velocity(velocity, normal):
    dot_product = velocity[0] * normal[0] + velocity[1] * normal[1]
    return [velocity[0] - 2 * dot_product * normal[0], velocity[1] - 2 * dot_product * normal[1]]

def play_music_segment(start_time, duration=0.5):
    segment = music[int(start_time * 1000):int(start_time * 1000 + duration * 1000)]
    audio_segments.append((segment, time.time()))

    with io.BytesIO() as f:
        segment.export(f, format="wav")
        f.seek(0)
        pygame.mixer.Sound(f).play()

def create_new_ball():
    print(f"Creating new ball")
    ball_positions.append([WIDTH // 2, HEIGHT // 2])
    ball_speeds.append([random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])])
    trail_positions.append([])

# Initialize font
font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 72)

# Setup video writer
video_writer = imageio.get_writer(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_1\1_ball_in_circles_sound.mp4', fps=FPS)

# Main game loop
running = True
clock = pygame.time.Clock()
start_time = time.time()
last_circle_add_time = start_time
last_ball_add_time = start_time  # Track time for new ball creation
no_circle_time = None
timer = time.time()

while running:
    dt = clock.tick(FPS) / 1000  # Delta time in seconds

    if not game_over:
        if time.time() - timer >= 50 and not show_end_message:
            show_end_message = True
            end_message_start_time = time.time()

        # Update ball positions
        for i in range(len(ball_positions)):
            ball_speeds[i][1] += GRAVITY
            ball_positions[i][0] += ball_speeds[i][0]
            ball_positions[i][1] += ball_speeds[i][1]

            # Ball collision with walls
            if ball_positions[i][0] <= BALL_RADIUS or ball_positions[i][0] >= WIDTH - BALL_RADIUS:
                ball_speeds[i][0] = -ball_speeds[i][0]
                randomize_direction(ball_speeds[i])
                if no_circle_time is None:
                    bounce_count += 1

            if ball_positions[i][1] <= BALL_RADIUS or ball_positions[i][1] >= HEIGHT - BALL_RADIUS:
                ball_speeds[i][1] = -ball_speeds[i][1]
                randomize_direction(ball_speeds[i])

                if no_circle_time is None:
                    bounce_count += 1

            # Check collision with circles
            for circle in circles[:]:
                dist = math.hypot(ball_positions[i][0] - WIDTH // 2, ball_positions[i][1] - HEIGHT // 2)
                if circle.radius - BALL_RADIUS <= dist <= circle.radius + BALL_RADIUS:
                    normal = [(ball_positions[i][0] - WIDTH // 2) / dist, (ball_positions[i][1] - HEIGHT // 2) / dist]
                    ball_speeds[i] = reflect_velocity(ball_speeds[i], normal)
                    circles.remove(circle)
                    increase_speed(ball_speeds[i])
                    NEW_CIRCLE_INTERVAL *= CIRCLE_CREATION_ACCELERATION  # Decrease interval for circle creation
                    play_music_segment(random.uniform(0, len(music) // 1000 - 0.5))  # Play random segment

                    if no_circle_time is None:
                        bounce_count += 1
                    break

        # Check collision with other balls
        for i in range(len(ball_positions)):
            for j in range(i + 1, len(ball_positions)):
                dist = math.hypot(ball_positions[i][0] - ball_positions[j][0], ball_positions[i][1] - ball_positions[j][1])
                if dist <= 2 * BALL_RADIUS:
                    # Reflect velocities
                    normal = [(ball_positions[i][0] - ball_positions[j][0]) / dist, (ball_positions[i][1] - ball_positions[j][1]) / dist]
                    ball_speeds[i] = reflect_velocity(ball_speeds[i], normal)
                    ball_speeds[j] = reflect_velocity(ball_speeds[j], normal)
                    # Create sparks
                    for _ in range(10):
                        particles.append(Particle([(ball_positions[i][0] + ball_positions[j][0]) / 2, (ball_positions[i][1] + ball_positions[j][1]) / 2]))

        # Update trail positions
        for i in range(len(ball_positions)):
            trail_positions[i].append(tuple(ball_positions[i]))
            if len(trail_positions[i]) > TRAIL_LENGTH:
                trail_positions[i].pop(0)

        # Update circles
        for circle in circles:
            circle.update()
        circles = [circle for circle in circles if circle.radius > MIN_CIRCLE_RADIUS]

        # Add new circle based on current interval if there are circles
        if circles:
            current_time = time.time()
            if current_time - last_circle_add_time >= NEW_CIRCLE_INTERVAL:
                new_circle = Circle(400, random.choice(CIRCLE_COLORS))
                circles.append(new_circle)
                last_circle_add_time = current_time
        elif not show_end_message:
            show_end_message = True
            end_message_start_time = time.time()

        # Create new ball every 5 seconds
        current_time = time.time()
        if current_time - last_ball_add_time >= 5:
            create_new_ball()
            last_ball_add_time = current_time

        # Update particles
        particles = [p for p in particles if p.lifetime > 0]
        for p in particles:
            p.update(dt)

        # Draw everything
        screen.fill(BLACK)

        # Draw title and bounce counter
        title_text = font.render("How many bounces it need to escape?", True, WHITE)
        bounce_text = font.render(f"BOUNCES: {bounce_count}", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 50))
        screen.blit(bounce_text, (WIDTH // 2 - bounce_text.get_width() // 2, 125))

        # Draw circles
        for circle in circles:
            circle.draw(screen)

        # Draw trail and balls
        for i in range(len(ball_positions)):
            for j, pos in enumerate(trail_positions[i]):
                color = TRAIL_COLORS[j % len(TRAIL_COLORS)]
                pygame.draw.circle(screen, color, pos, BALL_RADIUS)
            pygame.draw.circle(screen, WHITE, ball_positions[i], BALL_RADIUS)

        # Draw particles
        for p in particles:
            p.draw(screen)

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
    frame = frame.transpose([1, 0, 2])  # Pygame uses (width, height, channels), ImageIO uses (height, width, channels)
    video_writer.append_data(frame)

    pygame.display.flip()

video_writer.close()
pygame.quit()
print("Video with sound saved successfully!")
