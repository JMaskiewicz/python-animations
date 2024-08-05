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
from tqdm import tqdm

# Video number
number = 10

# Directory path
video_dir = rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}'

# Check if there is a folder for this video
os.makedirs(video_dir, exist_ok=True)

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
pygame.display.set_caption("Competition Between Balls")

# Constants
FPS = 60
MAX_SPEED = 7  # Maximum initial speed of balls
TRAIL_LENGTH = 3  # Number of trail segments
GRAVITY = 0.005  # Gravity effect
SPEED_INCREASE_FACTOR = 1  # Factor to increase speed after each bounce
BLUE_MAX_COUNT = 100
RED_MAX_COUNT = 100
COOLDOWN_TIME = 0.25  # Cooldown time in seconds

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
BLUE_TRAIL = (0, 0, 255)
RED_TRAIL = (255, 0, 0)

# Ball settings
BALL_RADIUS = 15
WHITE_BALL_RADIUS = 80

class Ball:
    def __init__(self, color, trail_color, position=None, radius=BALL_RADIUS):
        self.color = color
        self.trail_color = trail_color
        self.radius = radius
        if position is None:
            self.position = [random.randint(self.radius, WIDTH - self.radius), random.randint(self.radius, HEIGHT - self.radius)]
        else:
            self.position = position
        self.speed = [random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])]
        self.trail = []
        self.last_collision_time = time.time()

    def update(self):
        self.speed[1] += GRAVITY
        self.position[0] += self.speed[0]
        self.position[1] += self.speed[1]

        # Ball collision with walls
        if self.position[0] <= self.radius or self.position[0] >= WIDTH - self.radius:
            self.speed[0] = -self.speed[0]
        if self.position[1] <= self.radius or self.position[1] >= HEIGHT - self.radius:
            self.speed[1] = -self.speed[1]

        # Update trail positions
        self.trail.append(tuple(self.position))
        if len(self.trail) > TRAIL_LENGTH:
            self.trail.pop(0)

def play_note_thread(note, duration=0.1):
    midi_out.note_on(note, 127)
    note_sound = Sine(note * 8).to_audio_segment(duration=int(duration * 1000))
    with audio_segments_lock:
        audio_segments.append((note_sound, time.time()))  # Append note sound and the current time
    time.sleep(duration)  # Play the note for 100 ms
    midi_out.note_off(note, 127)

def play_piano_notes():
    # Play right hand note
    if right_hand_notes:
        right_note = random.choice(right_hand_notes)
        threading.Thread(target=play_note_thread, args=(right_note,)).start()

    # Play left hand note every second bounce
    if left_hand_notes:
        left_note = random.choice(left_hand_notes)
        threading.Thread(target=play_note_thread, args=(left_note,)).start()

def check_collision(ball1, ball2):
    dist = math.hypot(ball1.position[0] - ball2.position[0], ball1.position[1] - ball2.position[1])
    return dist <= (ball1.radius + ball2.radius)

def resolve_collision(ball1, ball2):
    dx = ball1.position[0] - ball2.position[0]
    dy = ball1.position[1] - ball2.position[1]
    dist = math.hypot(dx, dy)
    if dist == 0:
        dist = ball1.radius + ball2.radius  # Prevent division by zero by setting a minimal distance

    nx = dx / dist
    ny = dy / dist

    # Calculate the overlap distance
    overlap = (ball1.radius + ball2.radius) - dist

    # Displace the balls to remove overlap
    ball1.position[0] += nx * overlap / 2
    ball1.position[1] += ny * overlap / 2
    ball2.position[0] -= nx * overlap / 2
    ball2.position[1] -= ny * overlap / 2

    # Calculate the relative velocity
    rel_vel = [ball1.speed[0] - ball2.speed[0], ball1.speed[1] - ball2.speed[1]]
    rel_speed = rel_vel[0] * nx + rel_vel[1] * ny

    # Apply the impulse
    impulse = 2 * rel_speed / (ball1.radius + ball2.radius)
    ball1.speed[0] -= impulse * ball2.radius * nx
    ball1.speed[1] -= impulse * ball2.radius * ny
    ball2.speed[0] += impulse * ball1.radius * nx
    ball2.speed[1] += impulse * ball1.radius * ny

# Initialize font
font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 64)

# Setup video writer
video_writer = imageio.get_writer(rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_ball_competition.mp4', fps=FPS)

# Main game loop
running = True
clock = pygame.time.Clock()
start_time = time.time()
audio_segments = []
audio_segments_lock = threading.Lock()

blue_ball_count = 1
red_ball_count = 1
game_over = False
show_end_message = False
end_message_start_time = None

blue_balls = [Ball(BLUE, BLUE_TRAIL)]
red_balls = [Ball(RED, RED_TRAIL)]
white_ball = Ball(WHITE, WHITE, position=[WIDTH // 2, HEIGHT // 2], radius=WHITE_BALL_RADIUS)

def draw_counter(surface, color, position, text):
    padding = 10
    rect = pygame.Rect(position[0], position[1], 160, 50)
    pygame.draw.rect(surface, color, rect, border_radius=15)
    pygame.draw.rect(surface, BLACK, rect, 2, border_radius=15)
    text_surf = font.render(text, True, BLACK)
    surface.blit(text_surf, (position[0] + padding, position[1] + padding))

helping = 0
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Check for game end
    if (blue_ball_count >= BLUE_MAX_COUNT or red_ball_count >= RED_MAX_COUNT) and helping==0:
        helping = 1
        show_end_message = True
        end_message_start_time = time.time()

    if not game_over:
        # Update ball position
        for ball in blue_balls:
            ball.update()
        for ball in red_balls:
            ball.update()
        white_ball.update()

        # Check for collisions with the white ball
        new_blue_balls = []
        new_red_balls = []

        for ball in blue_balls:
            if check_collision(ball, white_ball):
                if not show_end_message and time.time() - ball.last_collision_time > COOLDOWN_TIME:
                    resolve_collision(ball, white_ball)
                    new_blue_balls.append(Ball(BLUE, BLUE_TRAIL, position=ball.position[:]))
                    blue_ball_count += 1
                    play_piano_notes()
                    ball.last_collision_time = time.time()

        for ball in red_balls:
            if check_collision(ball, white_ball):
                if not show_end_message and time.time() - ball.last_collision_time > COOLDOWN_TIME:
                    resolve_collision(ball, white_ball)
                    new_red_balls.append(Ball(RED, RED_TRAIL, position=ball.position[:]))
                    red_ball_count += 1
                    play_piano_notes()
                    ball.last_collision_time = time.time()

        # Check for collisions between balls
        all_balls = blue_balls + red_balls + [white_ball]
        for i in range(len(all_balls)):
            for j in range(i + 1, len(all_balls)):
                if check_collision(all_balls[i], all_balls[j]):
                    resolve_collision(all_balls[i], all_balls[j])

        blue_balls.extend(new_blue_balls)
        red_balls.extend(new_red_balls)

        # Draw everything
        screen.fill(BLACK)

        # Draw trails
        for ball in blue_balls:
            for pos in ball.trail:
                pygame.draw.circle(screen, ball.trail_color, pos, ball.radius)
        for ball in red_balls:
            for pos in ball.trail:
                pygame.draw.circle(screen, ball.trail_color, pos, ball.radius)
        for pos in white_ball.trail:
            pygame.draw.circle(screen, white_ball.trail_color, pos, white_ball.radius)

        # Draw balls
        for ball in blue_balls:
            pygame.draw.circle(screen, ball.color, ball.position, ball.radius)
        for ball in red_balls:
            pygame.draw.circle(screen, ball.color, ball.position, ball.radius)
        pygame.draw.circle(screen, white_ball.color, white_ball.position, white_ball.radius)

        # Draw title
        title_text = large_font.render("Ball Competition", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 150))

        # Draw counters
        draw_counter(screen, BLUE, (50, 250), f"BLUE: {blue_ball_count}")
        draw_counter(screen, RED, (WIDTH - 200, 250), f"RED: {red_ball_count}")

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
                print("Game over!")
                game_over = True
                running = False

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
final_audio.export(rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_ball_competition_sound.mp3', format="mp3")

# Close the MIDI output
midi_out.close()
pygame.midi.quit()
pygame.quit()

# Combine video and audio
video_clip = VideoFileClip(rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_ball_competition.mp4')
audio_clip = AudioFileClip(rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_ball_competition_sound.mp3')
final_clip = video_clip.set_audio(audio_clip)
final_clip.write_videofile(rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_final_output.mp4', codec="libx264")

print("Video with sound saved successfully!")
