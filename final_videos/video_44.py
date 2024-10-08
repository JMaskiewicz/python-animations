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
number = 44

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
midi_file = mido.MidiFile(r'C:\Users\jmask\Downloads\Gravity Falls - Made Me Realize.mid')

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
pygame.display.set_caption("Hexagon with Trailing Effect and Dynamic Size")

# Constants
FPS = 60
MAX_SPEED = 4  # Maximum initial speed of hexagon
TRAIL_LENGTH = 1500  # Number of trail segments (infinite in practice)
GRAVITY = 0.2  # Gravity effect
HEXAGON_SIZE = 30  # Constant hexagon size
CIRCLE_RADIUS_THRESHOLD = 300  # Threshold radius for ending the simulation
CIRCLE_GROWTH_RATE = 1.05  # Growth rate of the circle after each bounce
SPEED_INCREASE_FACTOR = 1.01  # Factor to increase speed after each bounce

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TRAIL_COLORS = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 127, 255), (0, 0, 255), (139, 0, 255)]
GREY = (35, 35, 35)

# Hexagon settings
hexagon_pos = [WIDTH // 2, HEIGHT // 2]
hexagon_speed = [random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])]

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

    def increase_size(self):
        self.radius *= CIRCLE_GROWTH_RATE

circle = Circle(50)  # Starting radius smaller to allow for growth

def randomize_direction(hexagon_speed):
    angle = random.uniform(-math.pi / 6, math.pi / 6)  # Random angle between -30 and 30 degrees
    speed = math.hypot(hexagon_speed[0], hexagon_speed[1])  # Current speed magnitude
    new_angle = math.atan2(hexagon_speed[1], hexagon_speed[0]) + angle
    hexagon_speed[0] = speed * math.cos(new_angle)
    hexagon_speed[1] = speed * math.sin(new_angle)

def increase_speed(hexagon_speed):
    hexagon_speed[0] *= SPEED_INCREASE_FACTOR
    hexagon_speed[1] *= SPEED_INCREASE_FACTOR

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

def check_hexagon_circle_collision(hexagon_pos, hexagon_speed, hexagon_size, circle):
    circle_center = [WIDTH // 2, HEIGHT // 2]
    distance = math.hypot(hexagon_pos[0] - circle_center[0], hexagon_pos[1] - circle_center[1])
    if distance + hexagon_size >= circle.radius:
        overlap = distance + hexagon_size - circle.radius
        normal = [(hexagon_pos[0] - circle_center[0]) / distance, (hexagon_pos[1] - circle_center[1]) / distance]
        hexagon_pos[0] -= normal[0] * overlap  # Move hexagon out of collision
        hexagon_pos[1] -= normal[1] * overlap  # Move hexagon out of collision
        hexagon_speed[:] = reflect_velocity(hexagon_speed, normal)
        randomize_direction(hexagon_speed)
        increase_speed(hexagon_speed)
        play_piano_notes()
        circle.increase_size()  # Increase the circle size on collision
        return True
    return False

# Initialize font
font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 64)

# Setup video writer
video_writer = imageio.get_writer(os.path.join(video_dir, f'{number}_hexagon_in_circle_sound.mp4'), fps=FPS)

# Main game loop
running = True
clock = pygame.time.Clock()
start_time = time.time()

def draw_hexagon(surface, color, position, size):
    angle_offset = math.pi / 6  # Start from a pointy edge
    points = [
        (
            position[0] + size * math.cos(angle_offset + i * 2 * math.pi / 6),
            position[1] + size * math.sin(angle_offset + i * 2 * math.pi / 6)
        )
        for i in range(6)
    ]
    pygame.draw.polygon(surface, color, points)

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if not game_over:
        # Update hexagon position
        hexagon_speed[1] += GRAVITY
        hexagon_pos[0] += hexagon_speed[0]
        hexagon_pos[1] += hexagon_speed[1]

        # Hexagon collision with walls
        if (hexagon_pos[0] - HEXAGON_SIZE <= 0 or hexagon_pos[0] + HEXAGON_SIZE >= WIDTH) and not show_end_message:
            hexagon_speed[0] = -hexagon_speed[0]
            randomize_direction(hexagon_speed)
            play_piano_notes()  # Play piano notes on bounce
            bounce_count += 1

        if (hexagon_pos[1] - HEXAGON_SIZE <= 0 or hexagon_pos[1] + HEXAGON_SIZE >= HEIGHT) and not show_end_message:
            hexagon_speed[1] = -hexagon_speed[1]
            randomize_direction(hexagon_speed)
            play_piano_notes()  # Play piano notes on bounce
            bounce_count += 1

        # Hexagon collision with circle
        if (check_hexagon_circle_collision(hexagon_pos, hexagon_speed, HEXAGON_SIZE, circle)) and not show_end_message:
            bounce_count += 1

        # Update trail positions
        trail_positions.append(tuple(hexagon_pos))
        if len(trail_positions) > TRAIL_LENGTH:
            trail_positions.pop(0)

        # Check if circle size threshold is met
        if circle.radius > CIRCLE_RADIUS_THRESHOLD:
            show_end_message = True
            if end_message_start_time is None:
                end_message_start_time = time.time()

    # Draw everything
    screen.fill(BLACK)

    if not game_over:
        # Draw title and bounce counter
        title_text = font.render("WAIT TILL THE END!", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))

        # Draw trail with changing colors
        for i, pos in enumerate(trail_positions):
            color = TRAIL_COLORS[i % len(TRAIL_COLORS)]
            draw_hexagon(screen, color, pos, HEXAGON_SIZE - (i * HEXAGON_SIZE // TRAIL_LENGTH))

        # Draw circle
        circle.draw(screen)

        # Draw hexagon
        draw_hexagon(screen, WHITE, hexagon_pos, HEXAGON_SIZE)

        # Draw end message if needed
        if show_end_message:
            game_over_text1 = large_font.render("LIKE", True, BLACK)
            game_over_text2 = large_font.render("FOLLOW", True, BLACK)
            game_over_text3 = large_font.render("SUBSCRIBE", True, BLACK)
            game_over_text4 = large_font.render("COMMENT WHAT TO DO NEXT", True, BLACK)
            screen.blit(game_over_text1, (WIDTH // 2 - game_over_text1.get_width() // 2, HEIGHT // 2 - 250))
            screen.blit(game_over_text2, (WIDTH // 2 - game_over_text2.get_width() // 2, HEIGHT // 2 - 150))
            screen.blit(game_over_text3, (WIDTH // 2 - game_over_text3.get_width() // 2, HEIGHT // 2 - 50))
            screen.blit(game_over_text4, (WIDTH // 2 - game_over_text4.get_width() // 2, HEIGHT // 2 + 50))

            # Check if the 5-second period is over
            if time.time() - end_message_start_time >= 3:
                running = False

        # Add watermark text
        watermark_font = pygame.font.SysFont(None, 36)
        watermark_texts = [
            watermark_font.render("yt:@jbbm_motions", True, GREY),
            watermark_font.render("tiktok:@jbbm_motions", True, GREY),
            watermark_font.render("subscribe for more!", True, GREY)
        ]
        for idx, text in enumerate(watermark_texts):
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 175 + idx * 30))


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
final_audio.export(os.path.join(video_dir, f'{number}_hexagon_competition_sound.mp3'), format="mp3")

# Close the MIDI output
midi_out.close()
pygame.midi.quit()
pygame.quit()

# Combine video and audio
video_clip = VideoFileClip(os.path.join(video_dir, f'{number}_hexagon_in_circle_sound.mp4'))
audio_clip = AudioFileClip(os.path.join(video_dir, f'{number}_hexagon_competition_sound.mp3'))
final_clip = video_clip.set_audio(audio_clip)
final_clip.write_videofile(os.path.join(video_dir, f'{number}_final_output.mp4'), codec='libx264')

print("Video with sound saved successfully!")
