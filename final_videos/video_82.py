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
number = 82

# Directory path
video_dir = rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}'
if not os.path.exists(video_dir):
    os.makedirs(video_dir)

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Load sounds
pop_sound_1 = pygame.mixer.Sound(r'C:\Users\jmask\Downloads\pacman_chomp.mp3')
pop_sound_2 = pygame.mixer.Sound(r'C:\Users\jmask\Downloads\pacman_eatfruit.mp3')
pop_sound_3 = pygame.mixer.Sound(r'C:\Users\jmask\Downloads\pacman_eatghost.mp3')

# List of sounds
collision_sounds = [pop_sound_1, pop_sound_2, pop_sound_3]

# Create Pygame window
WIDTH, HEIGHT = 720, 1280
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball with Trailing Effect and Dynamic Polygon")

# Constants
FPS, MAX_SPEED, TRAIL_LENGTH, GRAVITY, ROTATION_SPEED = 60, 4, 1, 0.005, 0
spark_number = 25
BLACK, WHITE = (0, 0, 0), (255, 255, 255)
GREY = (30, 30, 30)

# Ball settings
BALL_RADIUS = 5  # Smaller ball size
SPARK_LIFETIME = 100  # Lifetime of sparks in frames
INITIAL_BALL_RADIUS = BALL_RADIUS

class Ball:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = WHITE  # Make the ball white
        self.radius = INITIAL_BALL_RADIUS

    def move(self):
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

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
            # Scale the spark size based on remaining lifetime
            spark_size = max(1, int(2 * (self.lifetime / SPARK_LIFETIME)))  # Decreases as lifetime decreases
            color = (
                min(255, max(0, self.color[0])),
                min(255, max(0, self.color[1])),
                min(255, max(0, self.color[2])),
            )
            pygame.draw.circle(screen, color, self.pos, spark_size)

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

    def is_empty(self):
        return all(self.holes)  # Return True if all holes are True (i.e., all edges are destroyed)

# Create concentric polygons with different initial hues and values
polygon_centers = [(WIDTH // 2, HEIGHT // 2)]

# Define a list of values for the hue change rates, ranging from 0.05 to 0.0005
hue_change_values = [0.0005, 0.0004, 0.0003, 0.0002, 0.00015, 0.0001, 0.00005]

# Create polygons with different initial hues and hue change rates
polygons = [
    (polygon_centers[0], 50, 4, random.random(), hue_change_values[0]),
    (polygon_centers[0], 100, 10, random.random(), hue_change_values[1]),
    (polygon_centers[0], 150, 13, random.random(), hue_change_values[2]),
    (polygon_centers[0], 200, 16, random.random(), hue_change_values[3]),
    (polygon_centers[0], 250, 19, random.random(), hue_change_values[4]),
    (polygon_centers[0], 300, 22, random.random(), hue_change_values[5]),
    (polygon_centers[0], 350, 25, random.random(), hue_change_values[6]),
]

polygons = [Polygon(*args) for args in polygons]

balls = [Ball(WIDTH // 2, HEIGHT // 2, random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED]))]
sparks = []
bounce_count = 0
game_over, show_end_message, end_message_start_time = False, False, None
audio_segments = []

def randomize_direction(ball_speed):
    angle = random.uniform(-math.pi / 6, math.pi / 6)
    speed = math.hypot(*ball_speed)
    new_angle = math.atan2(ball_speed[1], ball_speed[0]) + angle
    return [speed * math.cos(new_angle), speed * math.sin(new_angle)]

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

def generate_sparks_on_edge(edge, color):
    # Generate sparks along the entire length of the edge
    start, end = edge
    for _ in range(spark_number):  # Create 10 sparks along the edge
        t = random.uniform(0, 1)  # Random point along the edge
        random_point = [start[0] + t * (end[0] - start[0]), start[1] + t * (end[1] - start[1])]
        sparks.append(Spark(random_point, color))

font, large_font = pygame.font.SysFont(None, 48), pygame.font.SysFont(None, 64)
video_writer = imageio.get_writer(rf'{video_dir}\{number}_ball_in_lines_sound.mp4', fps=FPS)
running, clock, start_time = True, pygame.time.Clock(), time.time()
last_ball_spawn_time = start_time

# Start with 2 new balls and double each time
X = 1

def point_on_segment(px, py, ax, ay, bx, by):
    cross_product = (py - ay) * (bx - ax) - (px - ax) * (by - ay)
    if abs(cross_product) > 1e-6:
        return False  # Not on the line

    dot_product = (px - ax) * (bx - ax) + (py - ay) * (by - ay)
    if dot_product < 0:
        return False  # Beyond point a

    squared_length_ba = (bx - ax) * (bx - ax) + (by - ay) * (by - ay)
    if dot_product > squared_length_ba:
        return False  # Beyond point b

    return True  # The point is on the segment

def spawn_new_balls(number_of_balls=2):
    for _ in range(number_of_balls):
        # Add randomness to both the position and velocity to avoid overlap
        random_offset_x = random.randint(-10, 10)  # Slight random position offset
        random_offset_y = random.randint(-10, 10)
        random_speed_x = random.uniform(-6, 6)  # Add random speed variation
        random_speed_y = random.uniform(-6, 6)

        new_ball = Ball(
            WIDTH // 2 + random_offset_x,  # Slightly different starting positions
            HEIGHT // 2 + random_offset_y,
            random_speed_x,  # Random speed to avoid same velocities
            random_speed_y
        )
        balls.append(new_ball)

# Wait for 1 second before starting the video
while time.time() - start_time < 1:
    screen.fill(BLACK)
    pygame.display.flip()

while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:
        current_time = time.time()

        for ball in balls:
            ball.move()

            if ball.x <= BALL_RADIUS or ball.x >= WIDTH - BALL_RADIUS:
                ball.vx = -ball.vx
                ball.x = max(BALL_RADIUS, min(WIDTH - BALL_RADIUS, ball.x))  # Keep the ball within bounds
            if ball.y <= BALL_RADIUS or ball.y >= HEIGHT - BALL_RADIUS:
                ball.vy = -ball.vy
                ball.vx, ball.vy = randomize_direction([ball.vx, ball.vy])
                ball.y = max(BALL_RADIUS, min(HEIGHT - BALL_RADIUS, ball.y))  # Keep the ball within bounds

            # Check for collisions with polygons
            for j, polygon in enumerate(polygons):
                edges = polygon.get_edges()
                for i, edge in enumerate(edges):
                    if polygon.holes[i]:
                        continue
                    if enhanced_collision_detection([ball.x, ball.y], edge):
                        normal = [-(edge[1][1] - edge[0][1]), edge[1][0] - edge[0][0]]
                        normal_mag = math.hypot(*normal)
                        normal = [normal[0] / normal_mag, normal[1] / normal_mag]
                        ball.vx, ball.vy = reflect_velocity([ball.vx, ball.vy], normal)

                        if j == 0 or polygons[j - 1].is_empty():
                            if not polygon.holes[i]:
                                polygon.holes[i] = True
                                # Randomly play one of the 3 sounds
                                random.choice(collision_sounds).play()
                                bounce_count += 1
                                rgb_color = colorsys.hsv_to_rgb(polygon.hue, 1.0, 1.0)
                                color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))

                                # Generate sparks along the whole edge, not just at the endpoints
                                generate_sparks_on_edge(edge, color)

                                if polygon.is_empty():
                                    spawn_new_balls(X)  # Spawn X new balls
                                    X *= 2
                                    print(len(balls))
                        break


        for polygon in polygons:
            polygon.rotation_angle += ROTATION_SPEED

    screen.fill(BLACK)
    if not game_over:
        title_text = font.render("EACH TIME POLYGON IS DESTROYED", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 90))

        title_text = font.render("NUMBER OF BALLS DOUBLES!", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 140))

        title_text = font.render(f"BALLS: {len(balls)}", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 190))


        for polygon in polygons:
            polygon.draw(screen)

        for ball in balls:
            ball.draw(screen)
        for spark in sparks:
            spark.update()
            spark.draw(screen)

        sparks = [spark for spark in sparks if spark.lifetime > 0]  # Remove expired sparks

        if all(polygon.is_empty() for polygon in polygons) and not show_end_message:
            show_end_message = True
            end_message_start_time = time.time()

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

        watermark_font = pygame.font.SysFont(None, 36)
        watermark_texts = [
            watermark_font.render("yt:@jbbm_motions", True, GREY),
            watermark_font.render("tiktok:@jbbm_motions", True, GREY),
            watermark_font.render("subscribe for more!", True, GREY)
        ]
        for idx, text in enumerate(watermark_texts):
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 1050 + idx * 30))
    else:
        running = False

    frame = pygame.surfarray.array3d(screen).transpose([1, 0, 2])
    video_writer.append_data(frame)
    pygame.display.flip()

video_writer.close()
pygame.quit()
print("Video with sound saved successfully!")
