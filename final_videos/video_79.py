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

# Constants for sparks
GRAVITY = 0.2
SPARK_COUNT = 200

# Add Spark class
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

def create_sparks_from_triangle(triangle_edges, color, sparks):
    for edge in triangle_edges:
        start, end = edge
        for _ in range(SPARK_COUNT // len(triangle_edges)):
            t = random.uniform(0, 1)  # Parameter for linear interpolation
            x = start[0] + t * (end[0] - start[0])
            y = start[1] + t * (end[1] - start[1])
            angle = random.uniform(0, 2 * math.pi)
            vx = math.cos(angle) * random.uniform(1, 3)
            vy = math.sin(angle) * random.uniform(1, 3)
            new_spark = Spark(x, y, vx, vy, color)
            sparks.append(new_spark)

# Video number
number = 79

# Directory path
video_dir = rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}'

# Check if there is a folder for this video
if not os.path.exists(video_dir):
    os.makedirs(video_dir)

# Initialize Pygame and Pygame MIDI
pygame.init()

pop_sound = pygame.mixer.Sound(r'C:\Users\jmask\Downloads\pop-39222.mp3')

# Create Pygame window
WIDTH, HEIGHT = 720, 1280
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Triangles and Dynamic Squares")

# Constants
FPS = 60
TRAIL_LENGTH = 7
TRIANGLE_GROWTH_RATE = 3  # Triangles grow
NEW_TRIANGLE_INTERVAL = 0.3
MIN_TRIANGLE_SIDE = 10  # Small triangles start small
SQUARE_SHRINK_RATE = 2  # Squares shrink
SQUARE_CREATION_ACCELERATION = 1
NEW_SQUARE_INTERVAL = 0.25

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TRAIL_COLORS = [(255, 0, 0), (255, 140, 0), (255, 255, 0), (0, 255, 0), (0, 255, 255), (0, 0, 255), (238, 130, 238)]


class Triangle:
    def __init__(self, side_length, color, rotation_speed, initial_angle=0):
        self.side_length = side_length
        self.color = color
        self.rotation_speed = rotation_speed
        self.angle = initial_angle

    def draw(self, screen):
        if self.side_length < 10000:  # Adjust the condition if needed
            half_length = self.side_length / 2
            center = (WIDTH // 2, HEIGHT // 2)

            vertices = [
                (center[0] + half_length * math.cos(self.angle + 2 * math.pi / 3 * i),
                 center[1] + half_length * math.sin(self.angle + 2 * math.pi / 3 * i))
                for i in range(3)
            ]

            pygame.draw.polygon(screen, self.color, vertices, 5)

    def update(self):
        self.side_length += TRIANGLE_GROWTH_RATE
        self.angle += self.rotation_speed
        if self.angle >= 2 * math.pi:
            self.angle -= 2 * math.pi

    def get_edges(self):
        half_length = self.side_length / 2
        center = (WIDTH // 2, HEIGHT // 2)

        vertices = [
            (center[0] + half_length * math.cos(self.angle + 2 * math.pi / 3 * i),
             center[1] + half_length * math.sin(self.angle + 2 * math.pi / 3 * i))
            for i in range(3)
        ]

        edges = []
        for i in range(len(vertices)):
            start = vertices[i]
            end = vertices[(i + 1) % len(vertices)]
            edges.append((start, end))

        return edges


# Square class (formerly Square)
class ShrinkingSquare:
    def __init__(self, side_length, color, rotation_speed, initial_angle=0):
        self.side_length = side_length
        self.color = color
        self.rotation_speed = rotation_speed
        self.angle = initial_angle

    def draw(self, screen):
        if self.side_length > 0:
            half_length = self.side_length / 2
            center = (WIDTH // 2, HEIGHT // 2)

            vertices = [
                (center[0] - half_length, center[1] - half_length),
                (center[0] + half_length, center[1] - half_length),
                (center[0] + half_length, center[1] + half_length),
                (center[0] - half_length, center[1] + half_length),
            ]

            rotated_vertices = []
            for x, y in vertices:
                x -= center[0]
                y -= center[1]
                new_x = x * math.cos(self.angle) - y * math.sin(self.angle)
                new_y = x * math.sin(self.angle) + y * math.cos(self.angle)
                rotated_vertices.append((new_x + center[0], new_y + center[1]))

            pygame.draw.polygon(screen, self.color, rotated_vertices, 5)

    def update(self):
        self.side_length -= SQUARE_SHRINK_RATE
        self.angle += self.rotation_speed
        if self.angle >= 2 * math.pi:
            self.angle -= 2 * math.pi

    def get_edges(self):
        half_length = self.side_length / 2
        center = (WIDTH // 2, HEIGHT // 2)

        vertices = [
            (center[0] - half_length, center[1] - half_length),
            (center[0] + half_length, center[1] - half_length),
            (center[0] + half_length, center[1] + half_length),
            (center[0] - half_length, center[1] + half_length),
        ]

        rotated_vertices = []
        for x, y in vertices:
            x -= center[0]
            y -= center[1]
            new_x = x * math.cos(self.angle) - y * math.sin(self.angle)
            new_y = x * math.sin(self.angle) + y * math.cos(self.angle)
            rotated_vertices.append((new_x + center[0], new_y + center[1]))

        edges = []
        for i in range(len(rotated_vertices)):
            start = rotated_vertices[i]
            end = rotated_vertices[(i + 1) % len(rotated_vertices)]
            edges.append((start, end))

        return edges

# Initialize variables
hue = 0.0
hue_2 = 0.0
triangles = []
squares = []
trail_positions = []
left_hand_index = 0
right_hand_play_count = 0
bounce_count = 0
game_over = False
show_end_message = False
end_message_start_time = None
NOTE_OFF_EVENT = pygame.USEREVENT + 1
sparks = []

# Initialize font
font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 64)

# Setup video writer
video_writer = imageio.get_writer(rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_triangle_and_square_sound.mp4', fps=FPS)

# Initialize triangles list and track time for triangle creation
start_time = time.time()
last_triangle_add_time = start_time

# Main game loop
running = True
clock = pygame.time.Clock()
last_square_add_time = start_time
no_square_time = None
rotation_triangle = 0.00005
rotation_square = -0.05
counter = 0

# Add this function to check if two lines intersect
def lines_intersect(line1, line2):
    (x1, y1), (x2, y2) = line1
    (x3, y3), (x4, y4) = line2

    denom = (x4 - x3) * (y2 - y1) - (x2 - x1) * (y4 - y3)
    if denom == 0:
        return False

    ua = ((x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)) / denom
    ub = ((x4 - x3) * (y3 - y1) - (y4 - y3) * (x3 - x1)) / denom

    return 0 <= ua <= 1 and 0 <= ub <= 1

time.sleep(1)
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:
        current_time = time.time()
        # Spawn a new triangle at the center based on the NEW_TRIANGLE_INTERVAL
        if current_time - last_triangle_add_time >= NEW_TRIANGLE_INTERVAL:
            hue = (hue + 0.075) % 1
            rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            triangle_color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
            triangles.append(Triangle(10, triangle_color, rotation_triangle))  # Start small
            rotation_triangle += 0.0005
            last_triangle_add_time = current_time
            NEW_TRIANGLE_INTERVAL += 0.001
            counter += 1
            if counter > 30:
                NEW_TRIANGLE_INTERVAL *= 0.99

        if current_time - last_square_add_time >= NEW_SQUARE_INTERVAL and not show_end_message:
            hue_2 = (hue_2 - 0.0075) % 1.0
            rgb_color = colorsys.hsv_to_rgb(hue_2, 1.0, 1.0)
            square_color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
            new_square = ShrinkingSquare(700, square_color, rotation_square)  # Start large
            rotation_square *= -0.99
            squares.append(new_square)
            last_square_add_time = current_time

        # Update triangles
        for triangle in triangles:
            triangle.update()
        triangles = [triangle for triangle in triangles if triangle.side_length < 1900]

        # Update squares
        for square in squares:
            square.update()
        squares = [square for square in squares if square.side_length > 0]

        # Check for collisions between squares and triangles
        for square in squares[:]:
            square_edges = square.get_edges()
            for triangle in triangles[:]:
                triangle_edges = triangle.get_edges()
                collision_detected = False
                for square_edge in square_edges:
                    for triangle_edge in triangle_edges:
                        if lines_intersect(square_edge, triangle_edge):
                            collision_detected = True
                            break
                    if collision_detected:
                        break
                if collision_detected:
                    # Play the pop sound
                    pop_sound.play()
                    create_sparks_from_triangle(triangle_edges, triangle.color, sparks)
                    squares.remove(square)
                    triangles.remove(triangle)
                    break

    # Check if there are no squares or triangles
    if (not squares or not triangles) and current_time - start_time > 5:
        show_end_message = True
        if end_message_start_time is None:
            end_message_start_time = time.time()

    # Draw everything
    screen.fill(BLACK)

    # Add watermark text
    watermark_font = pygame.font.SysFont(None, 36)
    watermark_texts = [
        watermark_font.render("yt:@jbbm_motions", True, (50, 50, 50)),
        watermark_font.render("tiktok:@jbbm_motions", True, (50, 50, 50)),
        watermark_font.render("subscribe for more!", True, (50, 50, 50))
    ]
    for idx, text in enumerate(watermark_texts):
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 1100 + idx * 30))

    if not game_over:
        # Draw title
        title_text = font.render("TriangleBurst Symphony", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 125))

        # Draw squares
        for square in squares:
            square.draw(screen)

        # Draw triangles
        for triangle in triangles:
            triangle.draw(screen)

        # Draw sparks
        for spark in sparks:
            spark.move()
            spark.draw(screen)
        sparks = [spark for spark in sparks if spark.alive]

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

            # Check if the 3-second period is over
            if time.time() - end_message_start_time >= 3:
                game_over = True
    else:
        running = False

    # Capture the screen for video
    frame = pygame.surfarray.array3d(screen)
    frame = frame.transpose([1, 0, 2])
    video_writer.append_data(frame)

    pygame.display.flip()

print('capturing video')

video_writer.close()
pygame.quit()
