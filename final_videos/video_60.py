import pygame
import random
import math
import time
import imageio
from pydub import AudioSegment
import os
import colorsys
import io
import pygame
import math
import random
import colorsys
import time
import io
from pydub import AudioSegment

# Video number
number = 60

# Directory path
video_dir = rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}'
if not os.path.exists(video_dir):
    os.makedirs(video_dir)


# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Load sound
pop_sound = pygame.mixer.Sound(r'C:\Users\jmask\Downloads\pop-39222.mp3')

# Create Pygame window
WIDTH, HEIGHT = 720, 1280
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball with Trailing Effect and Dynamic Polygon")

# Constants
FPS, MAX_SPEED, TRAIL_LENGTH, GRAVITY, ROTATION_SPEED = 60, 4, 1, 0.005, 0.005
BLACK, WHITE = (0, 0, 0), (255, 255, 255)
GREY = (30, 30, 30)

# Ball settings
BALL_RADIUS = 15
SPARK_LIFETIME = 30  # Lifetime of sparks in frames
INITIAL_BALL_RADIUS = 15


class Ball:
    def __init__(self, x, y, vx, vy, color):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.radius = INITIAL_BALL_RADIUS

    def move(self):
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def collide_with_ball(self, other):
        # Calculate distance between the balls
        dx = self.x - other.x
        dy = self.y - other.y
        distance = math.hypot(dx, dy)

        # Avoid division by zero if the balls are at the exact same position
        if distance == 0:
            # You could skip further calculations, or handle it differently
            return

        # Check if they are colliding (distance <= sum of radii)
        if distance < self.radius + other.radius:
            pop_sound.play()
            # Normalize the vector between the balls
            nx = dx / distance
            ny = dy / distance

            # Calculate the relative velocity in terms of the normal direction
            dvx = self.vx - other.vx
            dvy = self.vy - other.vy
            dot_product = dvx * nx + dvy * ny

            # Only resolve collision if balls are moving towards each other
            if dot_product > 0:
                return

            # Calculate impulse (assuming equal mass)
            impulse = 2 * dot_product / 2

            # Update velocities
            self.vx -= impulse * nx
            self.vy -= impulse * ny
            other.vx += impulse * nx
            other.vy += impulse * ny

            # Ensure balls are not stuck together
            overlap = 0.5 * (self.radius + other.radius - distance)
            self.x += overlap * nx
            self.y += overlap * ny
            other.x -= overlap * nx
            other.y -= overlap * ny

            # Generate colorful sparks at the collision point
            collision_point = [(self.x + other.x) / 2, (self.y + other.y) / 2]
            spark_color = [
                (self.color[i] + other.color[i]) // 2 for i in range(3)
            ]  # Average color of the two balls
            for _ in range(10):  # Number of sparks
                sparks.append(Spark(list(collision_point), spark_color))

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

    def is_empty(self):
        return all(self.holes)  # Return True if all holes are True (i.e., all edges are destroyed)


# Create concentric polygons with different initial hues and values
polygon_centers = [(WIDTH // 2, HEIGHT // 2)]

# Define a list of values for the hue change rates, ranging from 0.05 to 0.0005
hue_change_values = [0.0005, 0.0004, 0.0003, 0.0002, 0.00015, 0.0001, 0.00005]

# Create polygons with different initial hues and hue change rates
polygons = [
    (polygon_centers[0], 100, 10, random.random(), hue_change_values[0]),
    (polygon_centers[0], 150, 13, random.random(), hue_change_values[1]),
    (polygon_centers[0], 200, 16, random.random(), hue_change_values[2]),
    (polygon_centers[0], 250, 19, random.random(), hue_change_values[3]),
    (polygon_centers[0], 300, 22, random.random(), hue_change_values[4]),
    (polygon_centers[0], 350, 25, random.random(), hue_change_values[5]),
]

polygons = [Polygon(*args) for args in polygons]

balls = [Ball(WIDTH // 2, HEIGHT // 2, random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED]),
              [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)])]
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

    # Increase precision by considering BALL_RADIUS offset
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


def spawn_new_balls(number_of_balls=2):
    for _ in range(number_of_balls):
        new_ball = Ball(WIDTH // 2, HEIGHT // 2, random.choice([-MAX_SPEED, MAX_SPEED]),
                        random.choice([-MAX_SPEED, MAX_SPEED]),
                        [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)])
        balls.append(new_ball)

# wait for 1 second before starting the video
while time.time() - start_time < 1:
    screen.fill(BLACK)
    pygame.display.flip()

X = 2
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

            # Check for collisions with other balls
            for other_ball in balls:
                if ball != other_ball:
                    ball.collide_with_ball(other_ball)

            # Check for collisions with polygons
            for j, polygon in enumerate(polygons):
                edges = polygon.get_edges()
                for i, edge in enumerate(edges):
                    if polygon.holes[i]:  # Skip the edge if it has been removed
                        continue
                    if enhanced_collision_detection([ball.x, ball.y], edge):
                        normal = [-(edge[1][1] - edge[0][1]), edge[1][0] - edge[0][0]]
                        normal_mag = math.hypot(*normal)
                        normal = [normal[0] / normal_mag, normal[1] / normal_mag]
                        ball.vx, ball.vy = reflect_velocity([ball.vx, ball.vy], normal)

                        if j == 0 or polygons[j - 1].is_empty():  # Only destroy edges if smaller polygon is empty
                            if not polygon.holes[i]:
                                polygon.holes[i] = True
                                pop_sound.play()
                                bounce_count += 1
                                rgb_color = colorsys.hsv_to_rgb(polygon.hue, 1.0, 1.0)
                                color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
                                for _ in range(10):  # Create more sparks
                                    sparks.append(Spark(list(edge[0]), color))
                                    sparks.append(Spark(list(edge[1]), color))

                                # Check if the polygon is fully destroyed
                                if polygon.is_empty():
                                    spawn_new_balls(X)  # Spawn 2 new balls at the center
                                    X += 2
                        break

        for polygon in polygons:
            polygon.rotation_angle += ROTATION_SPEED

    screen.fill(BLACK)
    if not game_over:
        title_text = font.render("ESCAPING BALLS", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))

        for polygon in polygons:
            polygon.draw(screen)

        for ball in balls:
            ball.draw(screen)
        for spark in sparks:
            spark.update()
            spark.draw(screen)

        sparks = [spark for spark in sparks if spark.lifetime > 0]  # Remove expired sparks

        # Check if all polygons are empty (i.e., no sides left)
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
