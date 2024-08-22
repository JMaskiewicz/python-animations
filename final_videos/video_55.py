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
number = 56

# Directory path
video_dir = rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}'
if not os.path.exists(video_dir):
    os.makedirs(video_dir)

# Load MP3 file
music_path = r'C:\Users\jmask\Downloads\Jaunty Gumption.mp3'
music = AudioSegment.from_mp3(music_path)

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Create Pygame window
WIDTH, HEIGHT = 720, 1280
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball with Trailing Effect and Dynamic Polygon")

# Constants
FPS, MAX_SPEED, TRAIL_LENGTH, GRAVITY, ROTATION_SPEED = 60, 8, 1, 0.33, 0.02
BLACK, WHITE = (0, 0, 0), (255, 255, 255)
GREY = (30, 30, 30)

# Ball settings
BALL_RADIUS = 15
SPARK_LIFETIME = 30  # Lifetime of sparks in frames

class Ball:
    def __init__(self, pos, speed, color=True):
        self.pos = pos
        self.speed = speed
        self.trail_positions = [pos[:] for _ in range(TRAIL_LENGTH)]  # Initialize with fixed length
        self.colorful = color

    def move(self):
        # Apply gravity towards the center (white ball position)
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        direction_x, direction_y = center_x - self.pos[0], center_y - self.pos[1]
        distance = math.hypot(direction_x, direction_y)
        direction_x, direction_y = direction_x / distance, direction_y / distance

        self.speed[0] += direction_x * GRAVITY
        self.speed[1] += direction_y * GRAVITY

        self.pos[0] += self.speed[0]
        self.pos[1] += self.speed[1]

        self.trail_positions.append(self.pos[:])  # Add a copy of the current position
        if len(self.trail_positions) > TRAIL_LENGTH:
            self.trail_positions.pop(0)

    def draw(self, screen):
        if self.colorful:
            for i, pos in enumerate(self.trail_positions):
                hue_offset = (i * 0.05) % 1.0  # Adjust the offset to create the smooth rainbow effect
                hue = (polygon.hue + hue_offset) % 1.0
                rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
                pygame.draw.circle(screen, color, pos, BALL_RADIUS)
        else:
            pygame.draw.circle(screen, WHITE, self.pos, BALL_RADIUS)

    def bounce(self):
        self.speed[0] = -self.speed[0]
        self.speed = randomize_direction(self.speed)

class Spark:
    def __init__(self, pos, color):
        self.pos = pos
        self.color = color
        self.lifetime = SPARK_LIFETIME
        self.speed = [random.uniform(-2, 2), random.uniform(-2, 2)]

    def update(self):
        self.pos[0] += self.speed[0]
        self.pos[1] += self.speed[1]
        self.lifetime -= 1

    def draw(self, screen):
        if self.lifetime > 0:
            color = (
                min(255, max(0, self.color[0])),
                min(255, max(0, self.color[1])),
                min(255, max(0, self.color[2])),
            )
            pygame.draw.circle(screen, color, self.pos, 3)

class Polygon:
    def __init__(self, center, radius, num_sides=15, initial_hue=0.0, value=None):
        self.value = value
        self.center = center
        self.radius, self.num_sides = radius, num_sides
        self.holes = [False] * num_sides
        self.rotation_angle = 0
        self.hue = initial_hue  # Set initial hue for each polygon

    def draw(self, screen):
        angle_step = 2 * math.pi / self.num_sides
        points = [(self.center[0] + self.radius * math.cos(i * angle_step + self.rotation_angle),
                   self.center[1] + self.radius * math.sin(i * angle_step + self.rotation_angle)) for i in
                  range(self.num_sides)]
        for i in range(self.num_sides):
            if not self.holes[i]:
                start, end = points[i], points[(i + 1) % self.num_sides]
                self.hue = (self.hue + self.value) % 1.0  # Increased hue change rate
                rgb_color = colorsys.hsv_to_rgb(self.hue, 1.0, 1.0)
                color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
                pygame.draw.line(screen, color, start, end, 10)

    def get_edges(self):
        angle_step = 2 * math.pi / self.num_sides
        points = [(self.center[0] + self.radius * math.cos(i * angle_step + self.rotation_angle),
                   self.center[1] + self.radius * math.sin(i * angle_step + self.rotation_angle)) for i in
                  range(self.num_sides)]
        return [(points[i], points[(i + 1) % len(points)]) for i in range(len(points))]

    def contains_point(self, point):
        return math.hypot(point[0] - self.center[0], point[1] - self.center[1]) <= self.radius

# Create concentric polygons with different initial hues and values
polygon_centers = [(WIDTH // 2, HEIGHT // 2)]

# Define a list of values for the hue change rates, ranging from 0.05 to 0.0005
hue_change_values = [0.0005, 0.0004, 0.0003, 0.0002, 0.00015, 0.0001, 0.00005]

# Create polygons with different initial hues and hue change rates
polygons = [Polygon(polygon_centers[0], radius, num_sides=10, initial_hue=random.random(), value=hue_change_values[i])
            for i, radius in enumerate([350, 300, 250, 200, 150, 100, 50])]

# Create the white ball in the center
white_ball = Ball([WIDTH // 2, HEIGHT // 2], [0, 0], color=False)

# Create the colorful ball
balls = [Ball([WIDTH // 2, 30], [random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])])]

sparks = []
bounce_count = 0
game_over, show_end_message, end_message_start_time = False, False, None
audio_segments = []

def randomize_direction(ball_speed):
    angle = random.uniform(-math.pi / 6, math.pi / 6)
    speed = math.hypot(*ball_speed)
    new_angle = math.atan2(ball_speed[1], ball_speed[0]) + angle
    return [speed * math.cos(new_angle), speed * math.sin(new_angle)]

def play_music_segment(start_time, duration=0.2):
    segment = music[start_time * 1000:start_time * 1000 + duration * 1000]
    audio_segments.append((segment, time.time()))

    with io.BytesIO() as f:
        segment.export(f, format="wav")
        f.seek(0)
        pygame.mixer.Sound(f).play()

def reflect_velocity(velocity, normal):
    dot_product = velocity[0] * normal[0] + velocity[1] * normal[1]
    return [velocity[0] - 2 * dot_product * normal[0], velocity[1] - 2 * dot_product * normal[1]]

def enhanced_collision_detection(ball_pos, edge):
    line_start, line_end = edge
    line_vec = [line_end[0] - line_start[0], line_end[1] - line_start[1]]
    ball_vec = [ball_pos[0] - line_start[0], ball_pos[1] - line_start[1]]
    line_len = math.hypot(*line_vec)
    line_unitvec = [line_vec[0] / line_len, line_vec[1] / line_len]
    proj_len = ball_vec[0] * line_unitvec[0] + ball_vec[1] * line_unitvec[1]

    if proj_len < 0 or proj_len > line_len:
        return False

    closest_point = [line_start[0] + proj_len * line_unitvec[0], line_start[1] + proj_len * line_unitvec[1]]

    if math.hypot(closest_point[0] - ball_pos[0], closest_point[1] - ball_pos[1]) <= BALL_RADIUS:
        return point_on_segment(closest_point[0], closest_point[1], line_start[0], line_start[1], line_end[0],
                                line_end[1])

    return False

font, large_font = pygame.font.SysFont(None, 48), pygame.font.SysFont(None, 64)
video_writer = imageio.get_writer(rf'{video_dir}\{number}_ball_in_lines_sound.mp4', fps=FPS)
running, clock, start_time = True, pygame.time.Clock(), time.time()
last_ball_spawn_time = start_time

def point_on_segment(px, py, ax, ay, bx, by):
    # Calculate the cross product to determine if point p is on line segment ab
    cross_product = (py - ay) * (bx - ax) - (px - ax) * (by - ay)
    if abs(cross_product) > 1e-6:
        return False  # Not on the line

    # Check if the point is in the bounding rectangle
    dot_product = (px - ax) * (bx - ax) + (py - ay) * (by - ay)
    if dot_product < 0:
        return False  # Beyond point a

    squared_length_ba = (bx - ax) * (bx - ax) + (by - ay) * (by - ay)
    if dot_product > squared_length_ba:
        return False  # Beyond point b

    return True  # The point is on the segment

# wait 1 second before starting the music
while time.time() - start_time < 1:
    clock.tick(FPS)

while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    if not game_over:
        current_time = time.time()

        for ball in balls:
            ball.move()
            if ball.pos[0] <= BALL_RADIUS or ball.pos[0] >= WIDTH - BALL_RADIUS:
                TRAIL_LENGTH +=1
                ball.bounce()
            if ball.pos[1] <= BALL_RADIUS or ball.pos[1] >= HEIGHT - BALL_RADIUS:
                TRAIL_LENGTH += 1
                ball.speed[1] = -ball.speed[1]
                ball.speed = randomize_direction(ball.speed)

            # Check for collisions with polygons
            for polygon in polygons:
                edges = polygon.get_edges()
                for i, edge in enumerate(edges):
                    if not polygon.holes[i] and enhanced_collision_detection(ball.pos, edge):
                        normal = [-(edge[1][1] - edge[0][1]), edge[1][0] - edge[0][0]]
                        normal_mag = math.hypot(*normal)
                        normal = [normal[0] / normal_mag, normal[1] / normal_mag]
                        ball.speed = reflect_velocity(ball.speed, normal)
                        polygon.holes[i] = True
                        play_music_segment(bounce_count * 0.2)
                        bounce_count += 1
                        rgb_color = colorsys.hsv_to_rgb(polygon.hue, 1.0, 1.0)
                        color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
                        for _ in range(10):  # Create more sparks
                            sparks.append(Spark(list(edge[0]), color))
                            sparks.append(Spark(list(edge[1]), color))
                        break

            # Check for collision with the white ball
            if math.hypot(ball.pos[0] - white_ball.pos[0], ball.pos[1] - white_ball.pos[1]) <= 2 * BALL_RADIUS:
                show_end_message = True
                end_message_start_time = time.time()

        for polygon in polygons:
            polygon.rotation_angle += ROTATION_SPEED

    screen.fill(BLACK)
    if not game_over:
        title_text = font.render("TO THE MIDDLE", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))

        for polygon in polygons:
            polygon.draw(screen)
        white_ball.draw(screen)
        for ball in balls:
            ball.draw(screen)
        for spark in sparks:
            spark.update()
            spark.draw(screen)

        sparks = [spark for spark in sparks if spark.lifetime > 0]  # Remove expired sparks

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
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 950 + idx * 30))
    else:
        running = False

    frame = pygame.surfarray.array3d(screen).transpose([1, 0, 2])
    video_writer.append_data(frame)
    pygame.display.flip()

video_writer.close()
pygame.quit()
print("Video with sound saved successfully!")
