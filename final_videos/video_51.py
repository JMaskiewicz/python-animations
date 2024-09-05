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
number = 51

# Directory path
video_dir = rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}'

# Check if there is a folder for this video
if not os.path.exists(video_dir):
    os.makedirs(video_dir)

# Initialize Pygame and Pygame MIDI
pygame.init()

pop_sound = pygame.mixer.Sound(r'C:\Users\jmask\Downloads\pop-39222.mp3')

# Create Pygame window
WIDTH, HEIGHT = 720, 1280  # Adjusted to be divisible by 16
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Triangles and Dynamic Squares")

# Constants
FPS = 60
TRAIL_LENGTH = 7  # Number of trail segments
TRIANGLE_SHRINK_RATE = 2  # Rate at which triangles shrink (adjusted to make the triangle visible longer)
NEW_TRIANGLE_INTERVAL = 0.3  # Initial time interval in seconds to add new triangle
MIN_TRIANGLE_SIDE = 50  # Minimum triangle side length before disappearing (increased to ensure visibility)
SQUARE_GROWTH_RATE = 2  # Rate at which squares grow
SQUARE_CREATION_ACCELERATION = 1  # Factor to decrease interval for square creation after each bounce
NEW_SQUARE_INTERVAL = 0.25  # Initial time interval in seconds to add new square

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TRAIL_COLORS = [(255, 0, 0), (255, 140, 0), (255, 255, 0), (0, 255, 0), (0, 255, 255), (0, 0, 255), (238, 130, 238)]

# Triangle class to handle rotating triangles
class Triangle:
    def __init__(self, side_length, color, rotation_speed, initial_angle=0):
        self.side_length = side_length
        self.color = color
        self.rotation_speed = rotation_speed
        self.angle = initial_angle

    def draw(self, screen):
        if self.side_length > MIN_TRIANGLE_SIDE:
            half_length = self.side_length / (2 * math.sqrt(3) / 3)
            center = (WIDTH // 2, HEIGHT // 2)

            # Calculate the vertices of the triangle
            vertices = [
                (center[0] + half_length * math.cos(self.angle),
                 center[1] + half_length * math.sin(self.angle)),
                (center[0] + half_length * math.cos(self.angle + 2 * math.pi / 3),
                 center[1] + half_length * math.sin(self.angle + 2 * math.pi / 3)),
                (center[0] + half_length * math.cos(self.angle + 4 * math.pi / 3),
                 center[1] + half_length * math.sin(self.angle + 4 * math.pi / 3)),
            ]

            # Draw the rotated triangle
            pygame.draw.polygon(screen, self.color, vertices, 5)

    def update(self):
        self.side_length -= TRIANGLE_SHRINK_RATE
        self.angle += self.rotation_speed
        if self.angle >= 2 * math.pi:
            self.angle -= 2 * math.pi

    def get_edges(self):
        half_length = self.side_length / (2 * math.sqrt(3) / 3)
        center = (WIDTH // 2, HEIGHT // 2)

        # Calculate the vertices of the triangle
        vertices = [
            (center[0] + half_length * math.cos(self.angle),
             center[1] + half_length * math.sin(self.angle)),
            (center[0] + half_length * math.cos(self.angle + 2 * math.pi / 3),
             center[1] + half_length * math.sin(self.angle + 2 * math.pi / 3)),
            (center[0] + half_length * math.cos(self.angle + 4 * math.pi / 3),
             center[1] + half_length * math.sin(self.angle + 4 * math.pi / 3)),
        ]

        # Create edges from vertices
        edges = []
        for i in range(len(vertices)):
            start = vertices[i]
            end = vertices[(i + 1) % len(vertices)]
            edges.append((start, end))

        return edges

# Square settings
class Square:
    def __init__(self, side_length, color, rotation_speed, initial_angle=0):
        self.side_length = side_length
        self.color = color
        self.rotation_speed = rotation_speed
        self.angle = initial_angle

    def draw(self, screen):
        if self.side_length > 0:
            half_length = self.side_length / 2
            center = (WIDTH // 2, HEIGHT // 2)

            # Calculate the vertices of the square
            vertices = [
                (center[0] - half_length, center[1] - half_length),
                (center[0] + half_length, center[1] - half_length),
                (center[0] + half_length, center[1] + half_length),
                (center[0] - half_length, center[1] + half_length),
            ]

            # Rotate the vertices
            rotated_vertices = []
            for x, y in vertices:
                x -= center[0]
                y -= center[1]
                new_x = x * math.cos(self.angle) - y * math.sin(self.angle)
                new_y = x * math.sin(self.angle) + y * math.cos(self.angle)
                rotated_vertices.append((new_x + center[0], new_y + center[1]))

            # Draw the rotated square
            pygame.draw.polygon(screen, self.color, rotated_vertices, 5)

    def update(self):
        self.side_length += SQUARE_GROWTH_RATE
        self.angle += self.rotation_speed
        if self.angle >= 2 * math.pi:
            self.angle -= 2 * math.pi

    def get_edges(self):
        half_length = self.side_length / 2
        center = (WIDTH // 2, HEIGHT // 2)

        # Calculate the vertices of the square
        vertices = [
            (center[0] - half_length, center[1] - half_length),
            (center[0] + half_length, center[1] - half_length),
            (center[0] + half_length, center[1] + half_length),
            (center[0] - half_length, center[1] + half_length),
        ]

        # Rotate the vertices
        rotated_vertices = []
        for x, y in vertices:
            x -= center[0]
            y -= center[1]
            new_x = x * math.cos(self.angle) - y * math.sin(self.angle)
            new_y = x * math.sin(self.angle) + y * math.cos(self.angle)
            rotated_vertices.append((new_x + center[0], new_y + center[1]))

        # Create edges from vertices
        edges = []
        for i in range(len(rotated_vertices)):
            start = rotated_vertices[i]
            end = rotated_vertices[(i + 1) % len(rotated_vertices)]
            edges.append((start, end))

        return edges

# Hue variable for colors
hue = 0.0
hue_2 = 0.0

# Create squares with adjusted initial side lengths to start small and grow
squares = []

# Trail settings
trail_positions = []

left_hand_index = 0
right_hand_play_count = 0
bounce_count = 0
game_over = False
show_end_message = False
end_message_start_time = None

NOTE_OFF_EVENT = pygame.USEREVENT + 1

def point_to_line_distance(point, line_start, line_end):
    px, py = point
    sx, sy = line_start
    ex, ey = line_end

    line_mag = math.hypot(ex - sx, ey - sy)
    if line_mag == 0:
        return math.hypot(px - sx, py - sy)

    u = ((px - sx) * (ex - sx) + (py - sy) * (ey - sy)) / (line_mag ** 2)
    if u < 0 or u > 1:
        return min(math.hypot(px - sx, py - sy), math.hypot(px - ex, py - ey))

    ix = sx + u * (ex - sx)
    iy = sy + u * (ey - sy)
    return math.hypot(px - ix, py - iy)

# Initialize font
font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 64)

# Setup video writer
video_writer = imageio.get_writer(rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_triangle_and_square_sound.mp4', fps=FPS)

# Initialize triangles list and track time for triangle creation
start_time = time.time()
triangles = []
last_triangle_add_time = start_time

# Main game loop
running = True
clock = pygame.time.Clock()
start_time = time.time()
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

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:
        current_time = time.time()
        # Spawn a new triangle at the center based on the NEW_TRIANGLE_INTERVAL
        if current_time - last_triangle_add_time >= NEW_TRIANGLE_INTERVAL:
            hue = (hue + 0.05) % 1.0  # Increment hue
            rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            triangle_color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
            triangles.append(Triangle(700, triangle_color, rotation_triangle))  # Start large
            rotation_triangle += 0.0005
            last_triangle_add_time = current_time
            NEW_TRIANGLE_INTERVAL += 0.001
            counter += 1
            if counter > 30:
                NEW_TRIANGLE_INTERVAL *= 0.985

        if current_time - last_square_add_time >= NEW_SQUARE_INTERVAL:
            hue_2 = (hue_2 + 0.0075) % 1.0  # Increment hue
            rgb_color = colorsys.hsv_to_rgb(hue_2, 1.0, 1.0)
            square_color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
            new_square = Square(20, square_color, rotation_square)
            rotation_square *= 0.99
            squares.append(new_square)
            last_square_add_time = current_time

        # Update triangles
        for triangle in triangles:
            triangle.update()
        triangles = [triangle for triangle in triangles if triangle.side_length > 0]

        # Update squares
        for square in squares:
            square.update()
        squares = [square for square in squares if square.side_length < 700]

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
                    squares.remove(square)
                    triangles.remove(triangle)
                    break

    # Check if there are no squares or triangles
    if (not squares or not triangles) and current_time-start_time>5:
        show_end_message = True
        if end_message_start_time is None:
            end_message_start_time = time.time()

    # Draw everything
    screen.fill(BLACK)

    # Add watermark text
    watermark_font = pygame.font.SysFont(None, 36)
    watermark_texts = [
        watermark_font.render("yt:@jbbm_motions", True, (30, 30, 30)),
        watermark_font.render("tiktok:@jbbm_motions", True, (30, 30, 30)),
        watermark_font.render("subscribe for more!", True, (30, 30, 30))
    ]
    for idx, text in enumerate(watermark_texts):
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 1000 + idx * 30))

    if not game_over:
        # Draw title
        title_text = font.render("ARE YOU HYPNOTIZED?", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 125))

        # Draw squares
        for square in squares:
            square.draw(screen)

        # Draw triangles
        for triangle in triangles:
            triangle.draw(screen)

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
                game_over = True
    else:
        running = False

    # Capture the screen for video
    frame = pygame.surfarray.array3d(screen)
    frame = frame.transpose([1, 0, 2])  # Pygame uses (width, height, channels), ImageIO uses (height, width, channels)
    video_writer.append_data(frame)

    pygame.display.flip()

print('capturing video')

video_writer.close()
pygame.quit()

