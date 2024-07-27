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

# Initialize Pygame and Pygame MIDI
pygame.init()
pygame.midi.init()

# Open a MIDI output port
midi_out = pygame.midi.Output(0)
instrument = 0  # Piano
midi_out.set_instrument(instrument)

# Load MIDI file
midi_file = mido.MidiFile(r'C:\Users\jmask\Downloads\Pirates.mid')

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
pygame.display.set_caption("Ball with Trailing Effect and Dynamic Circles")

# Constants
FPS = 60
MAX_SPEED = 7  # Maximum initial speed of ball
TRAIL_LENGTH = 2  # Number of trail segments
GRAVITY = 0.15  # Gravity effect
CIRCLE_SHRINK_RATE = 0.9915  # Reduced shrink rate
MIN_CIRCLE_RADIUS = 50  # Minimum circle radius before disappearing
SPEED_INCREASE_FACTOR = 1.01  # Factor to increase speed after each bounce
MIN_SPEED = 2  # Minimum speed to prevent the ball from stopping
GAME_DURATION = 50  # Duration of the game in seconds

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CIRCLE_COLORS = [(255, 105, 180), (135, 206, 250), (144, 238, 144), (255, 182, 193), (255, 160, 122), (173, 255, 47), (127, 255, 212)]
TRAIL_COLORS = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 127, 255), (0, 0, 255), (139, 0, 255)]

# Ball settings
BALL_RADIUS = 20
ball_pos = [WIDTH // 2, HEIGHT // 2]
ball_speed = [random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])]

# Circle settings
class Circle:
    def __init__(self, radius, color):
        self.radius = radius
        self.color = color

    def draw(self, screen):
        if self.radius > 0:
            pygame.draw.circle(screen, self.color, (WIDTH // 2, HEIGHT // 2), self.radius, 5)

    def update(self, color):
        self.radius *= CIRCLE_SHRINK_RATE
        self.color = color  # Update color on each bounce

# Initial circle
circle = Circle(350, CIRCLE_COLORS[0])

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

def randomize_direction(ball_speed):
    angle = random.uniform(-math.pi / 6, math.pi / 6)  # Random angle between -30 and 30 degrees
    speed = math.hypot(ball_speed[0], ball_speed[1])  # Current speed magnitude
    new_angle = math.atan2(ball_speed[1], ball_speed[0]) + angle
    ball_speed[0] = speed * math.cos(new_angle)
    ball_speed[1] = speed * math.sin(new_angle)

def increase_speed(ball_speed):
    ball_speed[0] *= SPEED_INCREASE_FACTOR
    ball_speed[1] *= SPEED_INCREASE_FACTOR
    # Ensure the ball's speed does not fall below a minimum threshold
    if abs(ball_speed[0]) < MIN_SPEED:
        ball_speed[0] = MIN_SPEED if ball_speed[0] > 0 else -MIN_SPEED
    if abs(ball_speed[1]) < MIN_SPEED:
        ball_speed[1] = MIN_SPEED if ball_speed[1] > 0 else -MIN_SPEED

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

# Initialize font
font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 68)

# Setup video writer
video_writer = imageio.get_writer(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_6\6_ball_in_circle_sound.mp4', fps=FPS)

# Main game loop
running = True
clock = pygame.time.Clock()
start_time = time.time()
no_circle_time = None
trail_length = TRAIL_LENGTH  # Initial trail length

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    current_time = time.time()
    elapsed_time = current_time - start_time

    # Update ball position
    ball_speed[1] += GRAVITY
    ball_pos[0] += ball_speed[0]
    ball_pos[1] += ball_speed[1]

    if not game_over:
        if elapsed_time >= GAME_DURATION:
            game_over = True
            show_end_message = True
            end_message_start_time = time.time()

        # Ball collision with walls
        if ball_pos[0] - BALL_RADIUS <= 0 or ball_pos[0] + BALL_RADIUS >= WIDTH:
            ball_speed[0] = -ball_speed[0]
            randomize_direction(ball_speed)
            play_piano_notes()  # Play piano notes on bounce
            if no_circle_time is None:
                bounce_count += 1
                trail_length += 1  # Increase trail length
                circle.update(CIRCLE_COLORS[bounce_count % len(CIRCLE_COLORS)])  # Change circle color

        if ball_pos[1] - BALL_RADIUS <= 0 or ball_pos[1] + BALL_RADIUS >= HEIGHT:
            ball_speed[1] = -ball_speed[1]
            randomize_direction(ball_speed)
            play_piano_notes()  # Play piano notes on bounce
            if no_circle_time is None:
                bounce_count += 1
                trail_length += 1  # Increase trail length
                circle.update(CIRCLE_COLORS[bounce_count % len(CIRCLE_COLORS)])  # Change circle color

        # Check collision with the circle
        dist = math.hypot(ball_pos[0] - WIDTH // 2, ball_pos[1] - HEIGHT // 2)
        if dist + BALL_RADIUS >= circle.radius:
            # Move the ball back outside the circle
            overlap = dist + BALL_RADIUS - circle.radius
            ball_pos[0] -= overlap * (ball_pos[0] - WIDTH // 2) / dist
            ball_pos[1] -= overlap * (ball_pos[1] - HEIGHT // 2) / dist
            # Ensure the ball is placed just outside the updated circle boundary
            dist = math.hypot(ball_pos[0] - WIDTH // 2, ball_pos[1] - HEIGHT // 2)
            if dist + BALL_RADIUS >= circle.radius:
                ball_pos[0] = WIDTH // 2 + (ball_pos[0] - WIDTH // 2) * (circle.radius - BALL_RADIUS) / dist
                ball_pos[1] = HEIGHT // 2 + (ball_pos[1] - HEIGHT // 2) * (circle.radius - BALL_RADIUS) / dist
            # Reflect velocity
            normal = [(ball_pos[0] - WIDTH // 2) / dist, (ball_pos[1] - HEIGHT // 2) / dist]
            ball_speed = reflect_velocity(ball_speed, normal)
            increase_speed(ball_speed)
            play_piano_notes()  # Play piano notes on bounce
            if no_circle_time is None:
                bounce_count += 1
                trail_length += 1  # Increase trail length
                circle.update(CIRCLE_COLORS[bounce_count % len(CIRCLE_COLORS)])  # Change circle color

        # Check if circle is too small
        if circle.radius <= MIN_CIRCLE_RADIUS:
            circle.radius = 10000  # Circle vanishes
            no_circle_time = time.time()
            show_end_message = True
            end_message_start_time = time.time()

    # Update trail positions
    trail_positions.append(tuple(ball_pos))
    if len(trail_positions) > trail_length:
        trail_positions.pop(0)

    # Draw everything
    screen.fill(BLACK)

    if not game_over or show_end_message:
        # Draw title and bounce counter
        title_text = font.render("Bouncing Ball in Shrinking Circle", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))
        if not game_over:
            bounce_text = font.render(f"BOUNCES: {bounce_count}", True, WHITE)
            screen.blit(bounce_text, (WIDTH // 2 - bounce_text.get_width() // 2, 200))

        if not game_over and circle.radius > 0:
            # Draw circle
            circle.draw(screen)

        # Draw trail
        for i, pos in enumerate(trail_positions):
            color = TRAIL_COLORS[i % len(TRAIL_COLORS)]
            pygame.draw.circle(screen, color, pos, BALL_RADIUS)

        # Draw ball
        pygame.draw.circle(screen, WHITE, ball_pos, BALL_RADIUS)

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
            if time.time() - end_message_start_time >= 5:
                running = False

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
    final_audio += AudioSegment.silent(duration=max(0, silence_duration - len(final_audio)))
    final_audio += segment

# Ensure the final audio is exactly the same length as the video duration
final_audio = final_audio[:int(game_duration * 1000)]

# Save the audio to a file
final_audio.export(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_6\6_ball_in_circle_sound.mp3', format="mp3")

# Close the MIDI output
midi_out.close()
pygame.midi.quit()
pygame.quit()

# Combine video and audio
video_clip = VideoFileClip(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_6\6_ball_in_circle_sound.mp4')
audio_clip = AudioFileClip(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_6\6_ball_in_circle_sound.mp3')
final_clip = video_clip.set_audio(audio_clip)
final_clip.write_videofile(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_6\6_final_output.mp4', codec="libx264")

print("Video with sound saved successfully!")
