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
import os
import colorsys

# Video number
number = 90

# Directory path
video_dir = rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}'

# Check if there is a folder for this video
if not os.path.exists(video_dir):
    os.makedirs(video_dir)

# Initialize Pygame and Pygame MIDI
pygame.init()
pygame.midi.init()

# Load sounds
pop_sound_1 = pygame.mixer.Sound(r'C:\Users\jmask\Downloads\balloonpop-83760.mp3')


# List of sounds
collision_sounds = [pop_sound_1]

# Create Pygame window
WIDTH, HEIGHT = 720, 1280  # Adjusted to be divisible by 16
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Bounce Quest")

# Constants
FPS = 60
MAX_SPEED = 100  # Maximum initial speed of ball
TRAIL_LENGTH = 10  # Initial number of trail segments
MAX_TRAIL_LENGTH = 100  # Maximum trail length
GRAVITY = 0.02  # Reduced Gravity Effect
MIN_BOUNCE_SPEED = 4  # Minimum vertical speed after bounce
CIRCLE_SHRINK_RATE = 2  # Rate at which circles shrink
NEW_CIRCLE_INTERVAL = 0.55  # Initial time interval in seconds to add new circle
MIN_CIRCLE_RADIUS = 5  # Minimum circle radius before disappearing
SPEED_INCREASE_FACTOR = 1.025  # Factor to increase speed after each bounce
CIRCLE_CREATION_ACCELERATION = 0.995  # Factor to decrease interval for circle creation after each bounce

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Ball settings
BALL_RADIUS = 15

# Ball class to handle both balls
class Ball:
    def __init__(self, pos, speed):
        self.pos = pos
        self.speed = speed
        self.trail = []
        self.hue_value = 0.0
        self.last_collision_time = 0  # Initialize last collision time
        self.trail_length = TRAIL_LENGTH  # Initialize trail length

    def update(self):
        self.speed[1] += GRAVITY
        self.pos[0] += self.speed[0]
        self.pos[1] += self.speed[1]
        self.trail.append(tuple(self.pos.copy()))
        if len(self.trail) > self.trail_length:
            self.trail.pop(0)
        self.hue_value = (self.hue_value + 0.01) % 1.0  # Update hue_value

# Initialize
balls = [
    Ball([WIDTH // 2, HEIGHT // 2], [2, 2])
]

# Particle class (now as circles fading from color to black)
class Particle:
    def __init__(self, pos, angle, speed, life, color):
        self.pos = pos
        self.angle = angle
        self.speed = speed
        self.life = life
        self.initial_life = life
        self.color = color

    def update(self):
        self.pos[0] += self.speed * math.cos(self.angle)
        self.pos[1] += self.speed * math.sin(self.angle)
        self.life -= 1

    def draw(self, screen):
        if self.life > 0:
            alpha = max(0, int(255 * (self.life / self.initial_life)))
            color = (
                int(self.color[0] * (self.life / self.initial_life)),
                int(self.color[1] * (self.life / self.initial_life)),
                int(self.color[2] * (self.life / self.initial_life))
            )
            pygame.draw.circle(screen, color, (int(self.pos[0]), int(self.pos[1])), 3)  # Draw particles as circles

# Circle settings
class Circle:
    def __init__(self, radius, color, rotation_speed, initial_angle=0, center=None):
        self.radius = radius
        self.color = color
        self.rotation_speed = rotation_speed
        self.angle = initial_angle
        self.particles = []
        if center is None:
            self.center = (WIDTH // 2, HEIGHT // 2)
        else:
            self.center = center

    def draw(self, screen):
        if self.radius > 0:
            center = self.center

            # Draw the circle
            pygame.draw.circle(screen, self.color, center, int(self.radius), 5)

            # Emit particles from edges of the circle
            for _ in range(20):  # Number of particles per frame (adjust the number as necessary)
                angle = random.uniform(0, 2 * math.pi)  # Random angle around the circle
                pos = [
                    center[0] + self.radius * math.cos(angle),
                    center[1] + self.radius * math.sin(angle)
                ]

                # Speed of the particle
                speed = random.uniform(1, 2)
                life = random.randint(1, 20)
                particle_color = self.color

                # Create and add the particle
                self.particles.append(Particle(pos, angle, speed, life, particle_color))

            # Update and draw particles
            for particle in self.particles:
                particle.update()
                particle.draw(screen)

            # Remove dead particles
            self.particles = [p for p in self.particles if p.life > 0]

    def update(self):
        self.radius -= CIRCLE_SHRINK_RATE
        self.angle += self.rotation_speed
        if self.angle >= 2 * math.pi:
            self.angle -= 2 * math.pi

    def get_edges(self):
        # Circles have no edges, but you could return the radius for possible collision detection
        return self.radius

# Separate hue variables for circles and balls
circle_hue = 0.0  # For circles

# Create circles with adjusted initial radii to fit within the screen and different initial rotation states
initial_angles = [i * math.pi / 3 for i in range(3)]  # Angles separated by 60 degrees (π/3 radians)
circles = []
for i, radius in enumerate(range(350, 150, -200)):  # Adjusted to make them circles with radii
    circle_hue = (circle_hue + 0.05) % 1.0  # Increment circle_hue
    rgb_color = colorsys.hsv_to_rgb(circle_hue, 1.0, 1.0)
    circle_color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
    circles.append(Circle(radius, circle_color, 0.01, initial_angle=initial_angles[i % len(initial_angles)]))

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

# Create a list to store sparks
sparks = []

def randomize_direction(ball_speed):
    angle = random.uniform(-math.pi / 3, math.pi / 3)
    speed = math.hypot(ball_speed[0], ball_speed[1])
    new_angle = math.atan2(ball_speed[1], ball_speed[0]) + angle
    ball_speed[0] = speed * math.cos(new_angle)
    ball_speed[1] = speed * math.sin(new_angle)

def increase_speed(ball_speed):
    speed_magnitude = math.hypot(ball_speed[0], ball_speed[1])
    new_speed_magnitude = min(speed_magnitude * SPEED_INCREASE_FACTOR, MAX_SPEED)
    ball_speed[0] = ball_speed[0] / speed_magnitude * new_speed_magnitude
    ball_speed[1] = ball_speed[1] / speed_magnitude * new_speed_magnitude

def reflect_velocity(velocity, normal):
    dot_product = velocity[0] * normal[0] + velocity[1] * normal[1]
    return [
        velocity[0] - 2 * dot_product * normal[0],
        velocity[1] - 2 * dot_product * normal[1]
    ]

# Initialize font
font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 64)

# Setup video writer
video_writer = imageio.get_writer(rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_ball_in_lines_sound.mp4', fps=FPS)

# Main game loop
running = True
clock = pygame.time.Clock()
start_time = time.time()
last_circle_add_time = start_time
no_circle_time = None
particles = []

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False


    for ball in balls:
        # Update ball position
        ball.update()

        # Ball collision with walls
        if ball.pos[0] <= BALL_RADIUS or ball.pos[0] >= WIDTH - BALL_RADIUS:
            ball.speed[0] = -ball.speed[0]
            randomize_direction(ball.speed)
            random.choice(collision_sounds).play()
            if no_circle_time is None:
                bounce_count += 1
                # Increase trail length
                ball.trail_length = min(ball.trail_length + 1, MAX_TRAIL_LENGTH)

        if ball.pos[1] <= BALL_RADIUS or ball.pos[1] >= HEIGHT - BALL_RADIUS:
            ball.speed[1] = -ball.speed[1]
            randomize_direction(ball.speed)
            random.choice(collision_sounds).play()
            if no_circle_time is None:
                bounce_count += 1
                # Increase trail length
                ball.trail_length = min(ball.trail_length + 1, MAX_TRAIL_LENGTH)

        # Check collision with circles
        for circle in circles[:]:
            dist = math.hypot(ball.pos[0] - WIDTH // 2, ball.pos[1] - HEIGHT // 2)
            if circle.radius - BALL_RADIUS <= dist <= circle.radius + BALL_RADIUS:
                normal = [(ball.pos[0] - WIDTH // 2) / dist, (ball.pos[1] - HEIGHT // 2) / dist]
                ball.speed = reflect_velocity(ball.speed, normal)
                circles.remove(circle)
                increase_speed(ball.speed)
                NEW_CIRCLE_INTERVAL *= CIRCLE_CREATION_ACCELERATION  # Decrease interval for circle creation
                random.choice(collision_sounds).play()
                if no_circle_time is None:
                    bounce_count += 1
                    # Increase trail length
                    ball.trail_length = min(ball.trail_length + 1, MAX_TRAIL_LENGTH)
                break

    if not game_over:
        for circle in circles:
            circle.update()
            circle.draw(screen)

        # Draw particles
        for particle in particles:
            particle.update()
            particle.draw(screen)

        # Remove particles that have disappeared
        particles = [p for p in particles if p.life > 0]

        circles = [circle for circle in circles if circle.radius > MIN_CIRCLE_RADIUS]

        # Add new circle based on current interval if there are circles
        if circles:
            current_time = time.time()
            if current_time - last_circle_add_time >= NEW_CIRCLE_INTERVAL:
                circle_hue = (circle_hue + 0.05) % 1.0  # Increment circle_hue
                rgb_color = colorsys.hsv_to_rgb(circle_hue, 1.0, 1.0)
                circle_color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
                new_circle = Circle(350, circle_color, 0)
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

        # Update sparks
        for spark in sparks:
            spark.update()
        sparks = [spark for spark in sparks if spark.life > 0]

    # Draw everything
    screen.fill(BLACK)

    # Add watermark text
    watermark_font = pygame.font.SysFont(None, 36)
    watermark_texts = [
        watermark_font.render("yt:@jbbm_motions", True, (50, 50, 50)),
        watermark_font.render("tiktok:@jbbm_motions", True, (50, 50, 50)),
        watermark_font.render("Subscribe for more!", True, (50, 50, 50))
    ]
    for idx, text in enumerate(watermark_texts):
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 1050 + idx * 30))

    if not game_over:
        # Draw title and bounce counter
        title_text = font.render("NEON BOUNCE QUEST", True, WHITE)
        bounce_text = font.render(f"BOUNCES: {bounce_count}", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 125))
        screen.blit(bounce_text, (WIDTH // 2 - bounce_text.get_width() // 2, 180))

        # Draw circles
        for circle in circles:
            circle.draw(screen)

            # Draw trails and balls with neon effect
            for ball in balls:
                # Create a surface with per-pixel alpha for the trail
                trail_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

                # Draw the trail
                trail_length = len(ball.trail)
                for idx, pos in enumerate(ball.trail):  # Removed reversed() to draw older parts first
                    factor = idx / trail_length
                    brightness = factor  # Brightness decreases away from the ball
                    hue = (ball.hue_value) % 1.0
                    saturation = 1.0  # Full saturation
                    rgb_color = colorsys.hsv_to_rgb(hue, saturation, brightness)

                    # Adjust alpha based on trail position (older = more transparent)
                    alpha = int(255 * (brightness ** 2))  # Squared to reduce older trail visibility
                    color = (
                        int(rgb_color[0] * 255),
                        int(rgb_color[1] * 255),
                        int(rgb_color[2] * 255),
                        alpha  # Add alpha for transparency
                    )

                    # Draw the trail on the transparent surface
                    pygame.draw.circle(trail_surface, color, (int(pos[0]), int(pos[1])), BALL_RADIUS)

                # Blit the trail surface onto the main screen
                screen.blit(trail_surface, (0, 0))

                # Draw the ball
                hue = (ball.hue_value) % 1.0
                rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                color = (
                    int(rgb_color[0] * 255),
                    int(rgb_color[1] * 255),
                    int(rgb_color[2] * 255)
                )
                pygame.draw.circle(screen, color, (int(ball.pos[0]), int(ball.pos[1])), BALL_RADIUS)

            # Draw sparks
            for spark in sparks:
                spark.draw(screen)


        else:

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

                # Ensure ball and trail are still drawn

                for ball in balls:

                    # Create a surface with per-pixel alpha for the trail

                    trail_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

                    # Draw the trail

                    trail_length = len(ball.trail)

                    for idx, pos in enumerate(ball.trail):
                        factor = idx / trail_length

                        brightness = factor

                        hue = (ball.hue_value) % 1.0

                        saturation = 1.0

                        rgb_color = colorsys.hsv_to_rgb(hue, saturation, brightness)

                        alpha = int(255 * (brightness ** 2))

                        color = (

                            int(rgb_color[0] * 255),

                            int(rgb_color[1] * 255),

                            int(rgb_color[2] * 255),

                            alpha

                        )

                        pygame.draw.circle(trail_surface, color, (int(pos[0]), int(pos[1])), BALL_RADIUS)

                    screen.blit(trail_surface, (0, 0))

                    # Draw the ball

                    hue = (ball.hue_value) % 1.0

                    rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)

                    color = (

                        int(rgb_color[0] * 255),

                        int(rgb_color[1] * 255),

                        int(rgb_color[2] * 255)

                    )

                    pygame.draw.circle(screen, color, (int(ball.pos[0]), int(ball.pos[1])), BALL_RADIUS)
                # Check if the 5-second period is over
                if time.time() - end_message_start_time >= 3:
                    running = False
    else:
        running = False

    # Capture the screen for video
    frame = pygame.surfarray.array3d(screen)
    frame = frame.transpose([1, 0, 2])  # Pygame uses (width, height, channels), ImageIO uses (height, width, channels)
    video_writer.append_data(frame)

    pygame.display.flip()

# Close the video writer
video_writer.close()

print("Video with neon trail saved successfully!")
