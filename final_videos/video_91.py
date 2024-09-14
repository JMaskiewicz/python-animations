# circles vs triangle

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
number = 91

# Directory path
video_dir = rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}'

# Check if there is a folder for this video
if not os.path.exists(video_dir):
    os.makedirs(video_dir)

# Initialize Pygame and Pygame MIDI
pygame.init()
pygame.midi.init()

# Open a MIDI output port
midi_out = pygame.midi.Output(0)
instrument = 0  # Piano
midi_out.set_instrument(instrument)

# Load MIDI file
midi_file = mido.MidiFile(r'C:\Users\jmask\Downloads\rush_e_real.mid')

# Extract notes from MIDI file
left_hand_notes = []
right_hand_notes = []

for track in midi_file.tracks:
    for msg in track:
        if not msg.is_meta and msg.type == 'note_on':
            if msg.channel == 0:  # Assuming left hand is on channel 0
                left_hand_notes.append(msg.note)
            elif msg.channel == 1:  # Assuming right hand is on channel 1
                right_hand_notes.append(msg.note)

# Create Pygame window
WIDTH, HEIGHT = 720, 1280  # Adjusted to be divisible by 16
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Circles and Dynamic Squares")

# Constants
FPS = 60
CIRCLE_SHRINK_RATE = 3  # Rate at which squares shrink
NEW_SQUARE_INTERVAL = 0.4  # Initial time interval in seconds to add new square
MIN_SQUARE_SIDE = 5  # Minimum square side length before disappearing
CIRCLE_GROWTH_RATE = 2  # Rate at which circles grow
SQUARE_CREATION_ACCELERATION = 1  # Factor to decrease interval for square creation after each bounce
NEW_CIRCLE_INTERVAL = 0.4  # Initial time interval in seconds to add new circle
SPARKS_PER_EDGE = 2  # Number of sparks emitted per edge per frame

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TRAIL_COLORS = [(255, 0, 0), (255, 140, 0), (255, 255, 0), (0, 255, 0), (0, 255, 255), (0, 0, 255), (238, 130, 238)]

# Particle class (for sparks)
class Particle:
    def __init__(self, pos, angle, speed, life, color):
        self.pos = list(pos)
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

# Circle class to handle growing circles
class Circle:
    def __init__(self, radius, color):
        self.radius = radius
        self.color = color

    def draw(self, screen):
        if self.radius > 0:
            pygame.draw.circle(screen, self.color, (WIDTH // 2, HEIGHT // 2), self.radius, 5)

    def update(self):
        self.radius += CIRCLE_GROWTH_RATE

    def get_edges(self):
        # Approximate the circle as a polygon for collision detection
        segments = 30  # Number of segments to approximate the circle
        angle_step = 2 * math.pi / segments
        center = (WIDTH // 2, HEIGHT // 2)
        edges = []

        for i in range(segments):
            start_angle = angle_step * i
            end_angle = angle_step * (i + 1)
            start_pos = (
                center[0] + self.radius * math.cos(start_angle),
                center[1] + self.radius * math.sin(start_angle)
            )
            end_pos = (
                center[0] + self.radius * math.cos(end_angle),
                center[1] + self.radius * math.sin(end_angle)
            )
            edges.append((start_pos, end_pos))

        return edges

# Square class
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
        self.side_length -= CIRCLE_SHRINK_RATE
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

def point_to_line_distance(point, line_start, line_end):
    px, py = point
    sx, sy = line_start
    ex, ey = line_end

    # Calculate the magnitude of the line (distance between start and end)
    line_mag = math.hypot(ex - sx, ey - sy)

    # If the line segment is just a point, return the distance between the point and the line start
    if line_mag == 0:
        return math.hypot(px - sx, py - sy)

    # Calculate projection factor 'u' along the line segment
    u = ((px - sx) * (ex - sx) + (py - sy)) / (line_mag ** 2)

    # Clamp u to be within the bounds of the line segment (0 <= u <= 1)
    if u < 0:
        u = 0
    elif u > 1:
        u = 1

    # Find the closest point on the line to the given point
    ix = sx + u * (ex - sx)
    iy = sy + u * (ey - sy)

    # Return the distance between the point and the closest point on the line
    return math.hypot(px - ix, py - iy)

# Hue variable for colors
hue = 0.0

# Create squares with adjusted initial side lengths to fit within the screen and different initial rotation states
initial_angles = [i * math.pi / 3 for i in range(6)]  # Angles separated by 60 degrees (π/3 radians)
squares = []
for i, side_length in enumerate(range(700, 300, -50)):
    hue = (hue + 0.05) % 1.0  # Increment hue
    rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
    square_color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
    squares.append(Square(side_length, square_color, 0.01, initial_angle=initial_angles[i % len(initial_angles)]))

# Trail and Spark settings
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

def play_note_thread(note, duration=0.1):
    midi_out.note_on(note, 127)
    note_sound = Sine(note * 8).to_audio_segment(duration=int(duration * 1000))
    audio_segments.append((note_sound, time.time()))  # Append note sound and the current time
    time.sleep(duration)  # Play the note for 100 ms
    midi_out.note_off(note, 127)

def play_piano_notes():
    global left_hand_index, right_hand_play_count

    # Play right hand note
    if right_hand_notes:
        right_note = random.choice(right_hand_notes)
        threading.Thread(target=play_note_thread, args=(right_note,)).start()

    # Play left hand note every second bounce
    right_hand_play_count += 1
    if right_hand_play_count % 2 == 0 and left_hand_notes:
        left_note = left_hand_notes[left_hand_index]
        threading.Thread(target=play_note_thread, args=(left_note,)).start()
        left_hand_index = (left_hand_index + 1) % len(left_hand_notes)

def emit_sparks_from_circle(circle):
    center = (WIDTH // 2, HEIGHT // 2)
    for edge in circle.get_edges():
        # Calculate midpoint of edge
        mid_x = (edge[0][0] + edge[1][0]) / 2
        mid_y = (edge[0][1] + edge[1][1]) / 2
        # Direction from edge to center
        dx = center[0] - mid_x
        dy = center[1] - mid_y
        angle = math.atan2(dy, dx)
        for _ in range(SPARKS_PER_EDGE):
            speed = random.uniform(1, 2)
            life = random.randint(1, 4)
            sparks.append(Particle((mid_x, mid_y), angle, speed, life, circle.color))

def emit_sparks_from_square(square):
    center = (WIDTH // 2, HEIGHT // 2)
    for edge in square.get_edges():
        # Calculate midpoint of edge
        mid_x = (edge[0][0] + edge[1][0]) / 2
        mid_y = (edge[0][1] + edge[1][1]) / 2
        # Direction from center to edge
        dx = mid_x - center[0]
        dy = mid_y - center[1]
        angle = math.atan2(dy, dx)
        for _ in range(SPARKS_PER_EDGE):
            speed = random.uniform(2, 5)
            life = random.randint(30, 60)
            sparks.append(Particle((mid_x, mid_y), angle, speed, life, square.color))

# Initialize font
font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 64)

# Setup video writer
video_writer = imageio.get_writer(
    rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_circle_in_lines_sound.mp4',
    fps=FPS
)

# Initialize circles list and track time for circle creation
start_time = time.time()
circles = []
last_circle_add_time = start_time

# Main game loop
running = True
clock = pygame.time.Clock()
start_time = time.time()
last_square_add_time = start_time
no_square_time = None

counter = 0
rotation_speed = 0.01

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:
        current_time = time.time()
        # Spawn a new circle at the center based on the NEW_CIRCLE_INTERVAL
        if current_time - last_circle_add_time >= NEW_CIRCLE_INTERVAL:
            hue = (hue + 0.05) % 1.0  # Increment hue
            rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            circle_color = (
                int(rgb_color[0] * 255),
                int(rgb_color[1] * 255),
                int(rgb_color[2] * 255)
            )
            circles.append(Circle(10, circle_color))
            last_circle_add_time = current_time
            NEW_CIRCLE_INTERVAL += 0.001
            counter += 1
            if counter > 50:
                NEW_CIRCLE_INTERVAL *= 0.985

        # Update circles
        for circle in circles:
            circle.update()
            emit_sparks_from_circle(circle)  # Emit sparks constantly from circle edges

        # Collision detection between circles and squares
        remaining_circles = []
        for circle in circles:
            collision_occurred = False
            for square in squares[:]:
                edges = square.get_edges()
                for edge in edges:
                    dist = point_to_line_distance((WIDTH // 2, HEIGHT // 2), edge[0], edge[1])
                    if dist <= circle.radius:
                        squares.remove(square)
                        collision_occurred = True
                        play_piano_notes()  # Play piano notes on collision
                        emit_sparks_from_square(square)  # Emit sparks from square on collision
                        emit_sparks_from_circle(circle)  # Emit sparks from circle on collision
                        break
                if collision_occurred:
                    break
            if not collision_occurred:
                remaining_circles.append(circle)

        circles = remaining_circles

        # Update squares
        for square in squares:
            square.update()
            emit_sparks_from_square(square)  # Emit sparks constantly from square edges

        squares = [square for square in squares if square.side_length > MIN_SQUARE_SIDE]

        # Add new square based on current interval if there are squares
        if squares:
            current_time = time.time()
            if current_time - last_square_add_time >= NEW_SQUARE_INTERVAL:
                hue = (hue + 0.05) % 1.0  # Increment hue
                rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                square_color = (
                    int(rgb_color[0] * 255),
                    int(rgb_color[1] * 255),
                    int(rgb_color[2] * 255)
                )
                new_square = Square(700, square_color, rotation_speed)
                rotation_speed += 0.001
                squares.append(new_square)
                last_square_add_time = current_time

    # Check if there are no squares or circles
    if (not squares or not circles) and (current_time - start_time > 5):
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
        title_text = font.render("SQUARE OR CIRCLE?", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 125))

        # Draw squares
        for square in squares:
            square.draw(screen)

        # Draw circles
        for circle in circles:
            circle.draw(screen)

        # Update and draw sparks
        for spark in sparks[:]:
            spark.update()
            if spark.life > 0:
                spark.draw(screen)
            else:
                sparks.remove(spark)

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
    frame = frame.transpose([1, 0, 2])  # Pygame uses (width, height, channels), ImageIO uses (height, width, channels)
    video_writer.append_data(frame)

    pygame.display.flip()

# Close the video writer
video_writer.close()

# Concatenate all audio segments
final_audio = AudioSegment.silent(duration=0)
game_duration = time.time() - start_time

for segment, timestamp in audio_segments:
    silence_duration = (timestamp - start_time) * 1000  # Convert to milliseconds
    if silence_duration > len(final_audio):
        final_audio += AudioSegment.silent(duration=silence_duration - len(final_audio))
    final_audio += segment

# Ensure the final audio is exactly the same length as the video duration
final_audio = final_audio[:int(game_duration * 1000)]

# Save the audio to a file
final_audio.export(
    rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_circle_in_lines_sound.mp3',
    format="mp3"
)

# Close the MIDI output
midi_out.close()
pygame.midi.quit()
pygame.quit()

# Combine video and audio
video_clip = VideoFileClip(
    rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_circle_in_lines_sound.mp4'
)
audio_clip = AudioFileClip(
    rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_circle_in_lines_sound.mp3'
)
final_clip = video_clip.set_audio(audio_clip)
final_clip.write_videofile(
    rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_final_output.mp4',
    codec="libx264"
)

print("Video with sound saved successfully!")
