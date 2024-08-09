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

# Video number
number = 16

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
pygame.display.set_caption("Ball with Moving Lines")

# Constants
FPS = 60
MAX_SPEED = 8  # Maximum initial speed of ball
TRAIL_LENGTH = 8  # Number of trail segments
GRAVITY = 0.15  # Gravity effect
LINE_HEIGHT = 20  # Line height
LINE_RESPAWN_RATE = random.randint(4, 4)  # Number of frames between line respawns
LINE_SPEED = 5  # Speed of lines moving upwards
SPEED_INCREASE_FACTOR = 1  # Factor to increase speed after each bounce
MIN_SPEED = 3  # Minimum speed to prevent the ball from stopping
GAME_DURATION = 50  # Duration of the game in seconds

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
LINE_COLORS = [(255, 105, 180), (135, 206, 250), (144, 238, 144), (255, 182, 193), (255, 160, 122), (173, 255, 47),
               (127, 255, 212)]
TRAIL_COLORS = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 127, 255), (0, 0, 255), (139, 0, 255)]

# Ball settings
BALL_RADIUS = 15


class Ball:
    def __init__(self, pos, speed):
        self.pos = pos
        self.speed = speed
        self.trail_positions = []


# Initialize with one ball
balls = [
    Ball([WIDTH // 2, HEIGHT // 3], [random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])])]


# Line settings
class Line:
    def __init__(self, color, y):
        self.color = color
        self.y = y

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (0, self.y, WIDTH, LINE_HEIGHT))

    def update(self):
        self.y -= LINE_SPEED


# Initialize with three lines at different starting positions
lines = [Line(random.choice(LINE_COLORS), HEIGHT - i * (HEIGHT // 5)) for i in range(4)]

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
video_writer = imageio.get_writer(
    rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_ball_in_lines_sound.mp4', fps=FPS)

# Main game loop
running = True
clock = pygame.time.Clock()
start_time = time.time()
no_line_time = None
trail_length = TRAIL_LENGTH  # Initial trail length

line_respawn_counter = 0  # Counter for line respawn timing
y = 0

# Constants for speed bonus
UPWARD_SPEED_BONUS_MULTIPLIER = 1.05  # Adjust this value for desired upward speed increase

# Main game loop (continue from your provided code)
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    current_time = time.time()
    elapsed_time = current_time - start_time

    if not game_over:
        if elapsed_time >= GAME_DURATION:
            game_over = True
            show_end_message = True
            end_message_start_time = time.time()

        # Update ball positions and speeds
        for ball in balls:
            ball.speed[1] += GRAVITY
            ball.pos[0] += ball.speed[0]
            ball.pos[1] += ball.speed[1]

            # Ball collision with walls
            if ball.pos[0] - BALL_RADIUS <= 0:
                ball.pos[0] = BALL_RADIUS  # Ensure the ball stays within bounds
                ball.speed[0] = -ball.speed[0]
                randomize_direction(ball.speed)
                play_piano_notes()  # Play piano notes on bounce

            elif ball.pos[0] + BALL_RADIUS >= WIDTH:
                ball.pos[0] = WIDTH - BALL_RADIUS  # Ensure the ball stays within bounds
                ball.speed[0] = -ball.speed[0]
                randomize_direction(ball.speed)
                play_piano_notes()  # Play piano notes on bounce

            if ball.pos[1] - BALL_RADIUS <= 0:
                ball.pos[1] = BALL_RADIUS  # Ensure the ball stays within bounds
                ball.speed[1] = -ball.speed[1]
                ball.speed[1] *= UPWARD_SPEED_BONUS_MULTIPLIER
                randomize_direction(ball.speed)
                play_piano_notes()  # Play piano notes on bounce

            elif ball.pos[1] + BALL_RADIUS >= HEIGHT:
                ball.pos[1] = HEIGHT - BALL_RADIUS  # Ensure the ball stays within bounds
                ball.speed[1] = -ball.speed[1]
                ball.speed[1] *= UPWARD_SPEED_BONUS_MULTIPLIER
                randomize_direction(ball.speed)
                play_piano_notes()  # Play piano notes on bounce

        # Check collision with lines
        lines_to_remove = []
        for line in lines:
            for ball in balls:
                if (line.y <= ball.pos[1] + BALL_RADIUS <= line.y + LINE_HEIGHT):
                    print(f"Collision Detected: Ball at {ball.pos} with Line at {line.y}")  # Debug line
                    ball.speed[1] = -ball.speed[1]
                    ball.speed[1] *= UPWARD_SPEED_BONUS_MULTIPLIER
                    play_piano_notes()  # Play piano notes on bounce
                    lines_to_remove.append(line)  # Mark the line for removal
                    bounce_count += 1

                    # Ensure the new ball is going upwards
                    new_ball_speed = ball.speed.copy()
                    new_ball_speed[1] = -abs(new_ball_speed[1])

                    # Create a new ball with the same position and speed
                    new_ball = Ball(ball.pos.copy(), new_ball_speed)
                    balls.append(new_ball)
                    break  # Exit the loop to avoid modifying the list during iteration

        # Remove lines that were collided with
        for line in lines_to_remove:
            lines.remove(line)

        # Update lines
        for line in lines:
            line.update()

        # Remove lines that are off the screen
        lines = [line for line in lines if line.y + LINE_HEIGHT > 0]

        # Respawn lines if not in end message state
        if not show_end_message:
            line_respawn_counter += 1
            if line_respawn_counter >= LINE_RESPAWN_RATE:
                line_respawn_counter = 0
                new_line = Line(random.choice(LINE_COLORS), HEIGHT)
                lines.append(new_line)

        # Check if there are no lines on screen
        if not lines and y == 0:
            y = 1
            no_line_time = time.time()
            show_end_message = True
            end_message_start_time = time.time()

    # Update trail positions
    for ball in balls:
        ball.trail_positions.append(tuple(ball.pos))
        if len(ball.trail_positions) > trail_length:
            ball.trail_positions.pop(0)

    # Draw everything
    screen.fill(BLACK)

    if not game_over:
        # Draw title and bounce counter
        title_text = font.render("BALLS BALLS BALLS", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))
        if not game_over:
            bounce_text = font.render(f"BALLS: {len(balls)}", True, WHITE)
            screen.blit(bounce_text, (WIDTH // 2 - bounce_text.get_width() // 2, 200))

        if not game_over:
            # Draw lines
            for line in lines:
                line.draw(screen)

        # Draw trails and balls
        for ball in balls:
            for i, pos in enumerate(ball.trail_positions):
                color = TRAIL_COLORS[i % len(TRAIL_COLORS)]
                pygame.draw.circle(screen, color, pos, BALL_RADIUS)
            pygame.draw.circle(screen, WHITE, ball.pos, BALL_RADIUS)

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
    final_audio += AudioSegment.silent(duration=max(0, silence_duration - len(final_audio)))
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
final_clip.write_videofile(rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_final_output.mp4', codec='libx264')

print("Video with sound saved successfully!")
