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
number = 70

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
pygame.display.set_caption("Ball with Trailing Effect and Dynamic Squares")

# Constants
FPS = 60
MAX_SPEED = 6  # Maximum initial speed of ball
TRAIL_LENGTH = 7  # Number of trail segments
GRAVITY = 0.15  # Gravity effect
CIRCLE_SHRINK_RATE = 4  # Rate at which squares shrink
NEW_SQUARE_INTERVAL = 0.5  # Initial time interval in seconds to add new square
MIN_SQUARE_SIDE = 5  # Minimum square side length before disappearing
SPEED_INCREASE_FACTOR = 1.01  # Factor to increase speed after each bounce
SQUARE_CREATION_ACCELERATION = 1.001  # Factor to decrease interval for square creation after each bounce
SPARK_COUNT = 10  # Number of sparks per edge

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TRAIL_COLORS = [(255, 0, 0), (255, 140, 0), (255, 255, 0), (0, 255, 0), (0, 255, 255), (0, 0, 255), (238, 130, 238)]

# Ball settings
BALL_RADIUS = 15

# Ball class to handle both balls
class Ball:
    def __init__(self, pos, speed):
        self.pos = pos
        self.speed = speed
        self.trail = []
        self.last_collision_time = 0  # Initialize last collision time

    def update(self):
        self.speed[1] += GRAVITY
        self.pos[0] += self.speed[0]
        self.pos[1] += self.speed[1]
        self.trail.append(tuple(self.pos))
        if len(self.trail) > TRAIL_LENGTH:
            self.trail.pop(0)

# Initialize two balls
balls = [
    Ball([WIDTH // 2 , HEIGHT // 2], [random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])]),
]

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
            edges.append((start, end))  # Append as tuple of tuples

        return edges

# Spark class for creating the sparks when polygons are destroyed
class Spark:
    def __init__(self, x, y, vx, vy, color):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.alive = True

    def move(self):
        if self.y < HEIGHT:  # Keep moving until it reaches the bottom
            self.vy += GRAVITY  # Apply gravity to the vertical velocity
            self.x += self.vx
            self.y += self.vy
        else:
            self.alive = False  # Mark as not alive if it reaches the bottom

    def draw(self, screen):
        if self.alive:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 3)

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
    angle = random.uniform(-math.pi / 6, math.pi / 6)  # Random angle between -30 and 30 degrees
    speed = math.hypot(ball_speed[0], ball_speed[1])  # Current speed magnitude
    new_angle = math.atan2(ball_speed[1], ball_speed[0]) + angle
    ball_speed[0] = speed * math.cos(new_angle)
    ball_speed[1] = speed * math.sin(new_angle)

def increase_speed(ball_speed):
    ball_speed[0] = min(SPEED_INCREASE_FACTOR * ball_speed[0], MAX_SPEED)
    ball_speed[1] = min(SPEED_INCREASE_FACTOR * ball_speed[1], MAX_SPEED)

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

def reflect_velocity(velocity, normal):
    dot_product = velocity[0] * normal[0] + velocity[1] * normal[1]
    return [velocity[0] - 2 * dot_product * normal[0], velocity[1] - 2 * dot_product * normal[1]]

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


def create_sparks_from_polygon_edges(edges, color, sparks):
    for edge in edges:
        start_point = edge[0]
        end_point = edge[1]
        spark_count_per_edge = SPARK_COUNT  # Number of sparks per edge

        for _ in range(spark_count_per_edge):
            t = random.random()  # Random point along the edge
            spark_x = start_point[0] + t * (end_point[0] - start_point[0])  # Calculate x-coordinate
            spark_y = start_point[1] + t * (end_point[1] - start_point[1])  # Calculate y-coordinate
            vx = random.uniform(-1, 1)  # Horizontal velocity
            vy = random.uniform(1, 3)  # Initial downward velocity
            new_spark = Spark(spark_x, spark_y, vx, vy, color)
            sparks.append(new_spark)

def create_sparks_from_point(point, color, sparks):
    for _ in range(SPARK_COUNT):
        vx = random.uniform(-1, 1)  # Horizontal velocity
        vy = random.uniform(1, 3)  # Initial downward velocity
        new_spark = Spark(point[0], point[1], vx, vy, color)
        sparks.append(new_spark)

# Initialize font
font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 64)

# Setup video writer
video_writer = imageio.get_writer(rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_ball_in_lines_sound.mp4', fps=FPS)

# Main game loop
running = True
clock = pygame.time.Clock()
start_time = time.time()
last_square_add_time = start_time
no_square_time = None

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:
        for ball in balls:
            # Update ball position
            ball.update()

            # Ball collision with walls
            if ball.pos[0] <= BALL_RADIUS or ball.pos[0] >= WIDTH - BALL_RADIUS:
                ball.speed[0] = -ball.speed[0]
                randomize_direction(ball.speed)
                play_piano_notes()  # Play piano notes on bounce
                create_sparks_from_point(ball.pos, WHITE, sparks)  # Create sparks on bounce
                if no_square_time is None:
                    bounce_count += 1

            if ball.pos[1] <= BALL_RADIUS or ball.pos[1] >= HEIGHT - BALL_RADIUS:
                ball.speed[1] = -ball.speed[1]
                randomize_direction(ball.speed)
                play_piano_notes()  # Play piano notes on bounce
                create_sparks_from_point(ball.pos, WHITE, sparks)  # Create sparks on bounce
                if no_square_time is None:
                    bounce_count += 1

            # Check collision with squares
            current_time = time.time()
            if current_time - ball.last_collision_time > 0.05:  # 50 ms cooldown between collisions
                for square in squares[:]:
                    edges = square.get_edges()
                    collision_occurred = False
                    for edge in edges:
                        dist = point_to_line_distance(ball.pos, edge[0], edge[1])
                        if dist <= BALL_RADIUS:
                            normal = [-(edge[1][1] - edge[0][1]), edge[1][0] - edge[0][0]]
                            normal_mag = math.hypot(normal[0], normal[1])
                            normal = [normal[0] / normal_mag, normal[1] / normal_mag]
                            ball.speed = reflect_velocity(ball.speed, normal)
                            create_sparks_from_polygon_edges(edges, square.color, sparks)  # Create falling sparks with the square's color on collision
                            squares.remove(square)
                            increase_speed(ball.speed)
                            NEW_SQUARE_INTERVAL *= SQUARE_CREATION_ACCELERATION  # Decrease interval for square creation
                            play_piano_notes()  # Play piano notes on bounce
                            ball.last_collision_time = current_time  # Update last collision time
                            collision_occurred = True
                            if no_square_time is None:
                                bounce_count += 1
                            break
                    if collision_occurred:
                        break

        # Update squares
        for square in squares:
            square.update()
        squares = [square for square in squares if square.side_length > MIN_SQUARE_SIDE]

        # Add new square based on current interval if there are squares
        if squares:
            current_time = time.time()
            if current_time - last_square_add_time >= NEW_SQUARE_INTERVAL:
                hue = (hue + 0.007) % 1.0  # Increment hue
                rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                square_color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
                new_square = Square(700, square_color, 0.04)
                squares.append(new_square)
                last_square_add_time = current_time
        else:
            if no_square_time is None:
                no_square_time = time.time()
            elif time.time() - no_square_time >= 5:
                game_over = True
            else:
                show_end_message = True
                if end_message_start_time is None:
                    end_message_start_time = time.time()

        # Update sparks
        for spark in sparks:
            spark.move()
        sparks = [spark for spark in sparks if spark.alive]

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
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 1150 + idx * 30))

    if not game_over:
        # Draw title and bounce counter
        title_text = font.render("WILL IT ESCAPE?", True, WHITE)
        bounce_text = font.render(f"BOUNCES: {bounce_count}", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 75))
        screen.blit(bounce_text, (WIDTH // 2 - bounce_text.get_width() // 2, 150))

        # Draw squares
        for square in squares:
            square.draw(screen)

        # Draw trails and balls
        for ball in balls:
            for i, pos in enumerate(ball.trail):
                color = TRAIL_COLORS[i % len(TRAIL_COLORS)]
                pygame.draw.circle(screen, color, pos, BALL_RADIUS)
            pygame.draw.circle(screen, WHITE, ball.pos, BALL_RADIUS)

        # Draw sparks
        for spark in sparks:
            spark.draw(screen)

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

# Close the video writer
video_writer.close()

# Concatenate all audio segments
final_audio = AudioSegment.silent(duration=0)
game_duration = time.time() - start_time

for segment, timestamp in audio_segments:
    silence_duration = (timestamp - start_time) * 1000  # Convert to milliseconds
    final_audio += AudioSegment.silent(duration=silence_duration - len(final_audio))
    final_audio += segment

# Ensure the final audio is exactly the same length as the video duration
final_audio = final_audio[:int(game_duration * 1000)]

# Save the audio to a file
final_audio.export(rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_ball_in_lines_sound.mp3', format="mp3")

# Close the MIDI output
midi_out.close()
pygame.midi.quit()
pygame.quit()

# Combine video and audio
video_clip = VideoFileClip(rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_ball_in_lines_sound.mp4')
audio_clip = AudioFileClip(rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_ball_in_lines_sound.mp3')
final_clip = video_clip.set_audio(audio_clip)
final_clip.write_videofile(rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_final_output.mp4', codec="libx264")

print("Video with sound saved successfully!")
