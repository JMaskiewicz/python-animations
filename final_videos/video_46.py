import os
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
from tqdm import tqdm
import colorsys

# Video number
number = 46

# Directory path
video_dir = rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}'

# Ensure the directory exists
os.makedirs(video_dir, exist_ok=True)

# Initialize Pygame and Pygame MIDI
pygame.init()
pygame.midi.init()

# Open a MIDI output port
midi_out = pygame.midi.Output(0)
instrument = 0  # Piano
midi_out.set_instrument(instrument)

# Load MIDI file
midi_file = mido.MidiFile(r'C:\Users\jmask\Downloads\pirates.mid')

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
pygame.display.set_caption("Triangle with Trailing Effect and Dynamic Size")

# Constants
FPS = 60
MAX_SPEED = 5  # Maximum initial speed of triangle
TRAIL_LENGTH = 0  # Number of trail segments
GRAVITY = 0.15  # Gravity effect
TRIANGLE_SIZE_THRESHOLD = 30  # Threshold size for ending the simulation
SPEED_INCREASE_FACTOR = 1.002  # Factor to increase speed after each bounce

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TRAIL_COLORS = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 127, 255), (0, 0, 255), (139, 0, 255)]
GREY = (40, 40, 40)

# Triangle settings
triangle_size = 300
triangle_pos = [WIDTH // 2, HEIGHT // 2]
triangle_speed = [random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])]
triangle_rotation = 0  # Initial rotation angle
TRIANGLE_change = 0.975

# Trail settings
trail_positions = []

# List to store hit points on the circle
hit_points = []

left_hand_index = 0
right_hand_play_count = 0
bounce_count = 0
game_over = False
show_end_message = False
end_message_start_time = None

NOTE_OFF_EVENT = pygame.USEREVENT + 1

# Create a list to store audio segments
audio_segments = []


class Circle:
    def __init__(self, radius):
        self.radius = radius
        self.hue = 0

    def draw(self, screen):
        if self.radius > 0:
            self.hue = (self.hue + 0.0025) % 1.0  # Faster color change
            rgb_color = colorsys.hsv_to_rgb(self.hue, 1.0, 1.0)
            color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
            pygame.draw.circle(screen, color, (WIDTH // 2, HEIGHT // 2), self.radius, 5)


# Function to draw lines from the circle to the center of the triangle
def draw_lines(screen, hit_points, triangle_vertices):
    for point in hit_points:
        hue = random.random()  # Random hue for each line
        rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
        for vertex in triangle_vertices:
            pygame.draw.line(screen, color, point, vertex, 2)


circle = Circle(350)


def get_triangle_vertices(position, size, rotation):
    """Calculate the vertices of the triangle based on its position, size, and rotation."""
    angle_offset = 2 * math.pi / 3
    vertices = []
    for i in range(3):
        angle = rotation + i * angle_offset
        x = position[0] + size * math.cos(angle)
        y = position[1] + size * math.sin(angle)
        vertices.append((x, y))
    return vertices


def draw_triangle(screen, vertices):
    """Draw the triangle on the screen."""
    pygame.draw.polygon(screen, WHITE, vertices, 0)


def randomize_direction(triangle_speed):
    angle = random.uniform(-math.pi / 6, math.pi / 6)  # Random angle between -30 and 30 degrees
    speed = math.hypot(triangle_speed[0], triangle_speed[1])  # Current speed magnitude
    new_angle = math.atan2(triangle_speed[1], triangle_speed[0]) + angle
    triangle_speed[0] = speed * math.cos(new_angle)
    triangle_speed[1] = speed * math.sin(new_angle)


def increase_speed(triangle_speed):
    triangle_speed[0] *= SPEED_INCREASE_FACTOR
    triangle_speed[1] *= SPEED_INCREASE_FACTOR


def play_note_thread(note, duration=0.2):
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


def check_triangle_circle_collision(triangle_vertices, triangle_speed, circle):
    """Check for collision between the triangle's vertices and the circle."""
    circle_center = [WIDTH // 2, HEIGHT // 2]
    collision_occurred = False

    for vertex in triangle_vertices:
        distance = math.hypot(vertex[0] - circle_center[0], vertex[1] - circle_center[1])
        if distance >= circle.radius:
            overlap = distance - circle.radius
            normal = [(vertex[0] - circle_center[0]) / distance, (vertex[1] - circle_center[1]) / distance]

            # Move the triangle slightly outside the circle based on the overlap
            triangle_pos[0] -= normal[0] * (overlap + 1)  # Adding 1 to ensure it fully moves outside
            triangle_pos[1] -= normal[1] * (overlap + 1)

            # Reflect triangle's speed based on the collision normal
            triangle_speed[:] = reflect_velocity(triangle_speed, normal)
            randomize_direction(triangle_speed)
            increase_speed(triangle_speed)
            play_piano_notes()
            collision_occurred = True

            # Calculate hit point on the circle
            hit_point_x = circle_center[0] + normal[0] * circle.radius
            hit_point_y = circle_center[1] + normal[1] * circle.radius
            hit_points.append((int(hit_point_x), int(hit_point_y)))

            break  # Exit after handling one collision to avoid multiple corrections in one frame

    return collision_occurred


# Initialize font
font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 64)

# Setup video writer
video_writer = imageio.get_writer(os.path.join(video_dir, f'{number}_triangle_in_circle_sound.mp4'), fps=FPS)

# Main game loop
running = True
clock = pygame.time.Clock()
start_time = time.time()

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:
        # Update triangle position
        triangle_speed[1] += GRAVITY
        triangle_pos[0] += triangle_speed[0]
        triangle_pos[1] += triangle_speed[1]
        triangle_rotation += 0.05  # Rotate the triangle slowly

        # Triangle collision with walls
        if (triangle_pos[0] - triangle_size <= 0 or triangle_pos[0] + triangle_size >= WIDTH) and not show_end_message:
            triangle_speed[0] = -triangle_speed[0]
            randomize_direction(triangle_speed)
            play_piano_notes()  # Play piano notes on bounce
            bounce_count += 1
            triangle_size *= TRIANGLE_change

        if (triangle_pos[1] - triangle_size <= 0 or triangle_pos[1] + triangle_size >= HEIGHT) and not show_end_message:
            triangle_speed[1] = -triangle_speed[1]
            randomize_direction(triangle_speed)
            play_piano_notes()  # Play piano notes on bounce
            bounce_count += 1
            triangle_size *= TRIANGLE_change

        # Get triangle vertices based on current position and rotation
        triangle_vertices = get_triangle_vertices(triangle_pos, triangle_size, triangle_rotation)

        # Triangle collision with circle
        if (check_triangle_circle_collision(triangle_vertices, triangle_speed, circle)) and not show_end_message:
            bounce_count += 1
            triangle_size *= TRIANGLE_change

        # Update trail positions
        trail_positions.append(tuple(triangle_pos))
        if len(trail_positions) > TRAIL_LENGTH:
            trail_positions.pop(0)

        # Check if triangle size threshold is met
        if triangle_size <= TRIANGLE_SIZE_THRESHOLD:
            show_end_message = True
            if end_message_start_time is None:
                end_message_start_time = time.time()
    else:
        running = False

    # Draw everything
    screen.fill(BLACK)

    if not game_over:
        # Draw title and bounce counter
        title_text = font.render("SHRINKING TRIANGLE", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))

        # Draw lines from hit points on the circle to the vertices of the triangle
        draw_lines(screen, hit_points, triangle_vertices)

        # Draw trail
        for i, pos in enumerate(trail_positions):
            color = TRAIL_COLORS[i % len(TRAIL_COLORS)]
            pygame.draw.circle(screen, color, pos, 5)

        # Draw circle
        circle.draw(screen)

        # Draw triangle
        draw_triangle(screen, triangle_vertices)

        # Draw end message if needed
        if show_end_message:
            game_over_text1 = large_font.render("LIKE", True, WHITE)
            game_over_text2 = large_font.render("FOLLOW", True, WHITE)
            game_over_text3 = large_font.render("SUBSCRIBE", True, WHITE)
            game_over_text4 = large_font.render("COMMENT WHAT TO DO NEXT", True, WHITE)
            screen.blit(game_over_text1, (WIDTH // 2 - game_over_text1.get_width() // 2, HEIGHT // 2 - 250))
            screen.blit(game_over_text2, (WIDTH // 2 - game_over_text2.get_width() // 2, HEIGHT // 2 - 150))
            screen.blit(game_over_text3, (WIDTH // 2 - game_over_text3.get_width() // 2, HEIGHT // 2 - 50))
            screen.blit(game_over_text4, (WIDTH // 2 - game_over_text4.get_width() // 2, HEIGHT // 2 + 50))

            # Check if the 5-second period is over
            if time.time() - end_message_start_time >= 5:
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

print('capturing video')

# Close the video writer
video_writer.close()

# Concatenate all audio segments
final_audio = AudioSegment.silent(duration=0)
game_duration = time.time() - start_time

for segment, timestamp in tqdm(audio_segments):
    silence_duration = (timestamp - start_time) * 1000  # Convert to milliseconds
    final_audio += AudioSegment.silent(duration=silence_duration - len(final_audio))
    final_audio += segment

# Ensure the final audio is exactly the same length as the video duration
final_audio = final_audio[:int(game_duration * 1000)]

# Save the audio to a file
final_audio.export(os.path.join(video_dir, f'{number}_triangle_competition_sound.mp3'), format="mp3")

# Close the MIDI output
midi_out.close()
pygame.midi.quit()
pygame.quit()

# Combine video and audio
video_clip = VideoFileClip(os.path.join(video_dir, f'{number}_triangle_in_circle_sound.mp4'))
audio_clip = AudioFileClip(os.path.join(video_dir, f'{number}_triangle_competition_sound.mp3'))
final_clip = video_clip.set_audio(audio_clip)
final_clip.write_videofile(os.path.join(video_dir, f'{number}_final_output.mp4'), codec='libx264')

print("Video with sound saved successfully!")
