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
number = 19

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
pygame.display.set_caption("Ball with Trailing Effect and Dynamic Size")

# Constants
FPS = 60
MAX_SPEED = 5  # Maximum initial speed of ball
TRAIL_LENGTH = 40  # Number of trail segments
GRAVITY = 0.2  # Gravity effect
BALL_GROWTH_RATE = 1.033  # Growth rate of the ball
BALL_RADIUS_THRESHOLD = 300  # Threshold radius for ending the simulation
SPEED_INCREASE_FACTOR = 1.01  # Factor to increase speed after each bounce

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TRAIL_COLORS = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 127, 255), (0, 0, 255), (139, 0, 255)]

# Ball settings
ball_radius = 15
ball_pos = [WIDTH // 2, HEIGHT // 2]
ball_speed = [random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])]

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

circle = Circle(350)

def randomize_direction(ball_speed):
    angle = random.uniform(-math.pi / 6, math.pi / 6)  # Random angle between -30 and 30 degrees
    speed = math.hypot(ball_speed[0], ball_speed[1])  # Current speed magnitude
    new_angle = math.atan2(ball_speed[1], ball_speed[0]) + angle
    ball_speed[0] = speed * math.cos(new_angle)
    ball_speed[1] = speed * math.sin(new_angle)

def increase_speed(ball_speed):
    ball_speed[0] *= SPEED_INCREASE_FACTOR
    ball_speed[1] *= SPEED_INCREASE_FACTOR

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

def check_ball_circle_collision(ball_pos, ball_speed, ball_radius, circle):
    circle_center = [WIDTH // 2, HEIGHT // 2]
    distance = math.hypot(ball_pos[0] - circle_center[0], ball_pos[1] - circle_center[1])
    if distance + ball_radius >= circle.radius:
        overlap = distance + ball_radius - circle.radius
        normal = [(ball_pos[0] - circle_center[0]) / distance, (ball_pos[1] - circle_center[1]) / distance]
        ball_pos[0] -= normal[0] * overlap  # Move ball out of collision
        ball_pos[1] -= normal[1] * overlap  # Move ball out of collision
        ball_speed[:] = reflect_velocity(ball_speed, normal)
        randomize_direction(ball_speed)
        increase_speed(ball_speed)
        play_piano_notes()
        return True
    return False

# Initialize font
font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 64)

# Setup video writer
video_writer = imageio.get_writer(os.path.join(video_dir, f'{number}_ball_in_circle_sound.mp4'), fps=FPS)

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
        # Update ball position
        ball_speed[1] += GRAVITY
        ball_pos[0] += ball_speed[0]
        ball_pos[1] += ball_speed[1]

        # Ball collision with walls
        if (ball_pos[0] - ball_radius <= 0 or ball_pos[0] + ball_radius >= WIDTH) and not show_end_message:
            ball_speed[0] = -ball_speed[0]
            randomize_direction(ball_speed)
            play_piano_notes()  # Play piano notes on bounce
            bounce_count += 1
            ball_radius *= BALL_GROWTH_RATE

        if (ball_pos[1] - ball_radius <= 0 or ball_pos[1] + ball_radius >= HEIGHT) and not show_end_message:
            ball_speed[1] = -ball_speed[1]
            randomize_direction(ball_speed)
            play_piano_notes()  # Play piano notes on bounce
            bounce_count += 1
            ball_radius *= BALL_GROWTH_RATE

        # Ball collision with circle
        if (check_ball_circle_collision(ball_pos, ball_speed, ball_radius, circle)) and not show_end_message:
            bounce_count += 1
            ball_radius *= BALL_GROWTH_RATE

        # Update trail positions
        trail_positions.append(tuple(ball_pos))
        if len(trail_positions) > TRAIL_LENGTH:
            trail_positions.pop(0)

        # Check if ball size threshold is met
        if ball_radius >= BALL_RADIUS_THRESHOLD:
            show_end_message = True
            if end_message_start_time is None:
                end_message_start_time = time.time()
    else:
        running = False

    # Draw everything
    screen.fill(BLACK)

    if not game_over:
        # Draw title and bounce counter
        title_text = font.render("GUESS THE SONG", True, WHITE)
        bounce_text = font.render(f"BOUNCES: {bounce_count}", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))
        screen.blit(bounce_text, (WIDTH // 2 - bounce_text.get_width() // 2, 200))

        # Draw trail
        for i, pos in enumerate(trail_positions):
            color = TRAIL_COLORS[i % len(TRAIL_COLORS)]
            pygame.draw.circle(screen, color, pos, ball_radius)

        # Draw circle
        circle.draw(screen)

        # Draw ball
        pygame.draw.circle(screen, WHITE, ball_pos, ball_radius)

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
            if time.time() - end_message_start_time >= 5:
                game_over = True
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
final_audio.export(os.path.join(video_dir, f'{number}_ball_competition_sound.mp3'), format="mp3")

# Close the MIDI output
midi_out.close()
pygame.midi.quit()
pygame.quit()

# Combine video and audio
video_clip = VideoFileClip(os.path.join(video_dir, f'{number}_ball_in_circle_sound.mp4'))
audio_clip = AudioFileClip(os.path.join(video_dir, f'{number}_ball_competition_sound.mp3'))
final_clip = video_clip.set_audio(audio_clip)
final_clip.write_videofile(os.path.join(video_dir, f'{number}_final_output.mp4'), codec='libx264')

print("Video with sound saved successfully!")
