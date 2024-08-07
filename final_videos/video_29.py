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
number = 29

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
midi_file = mido.MidiFile(r'C:\Users\jmask\Downloads\Never-Gonna-Give-You-Up-1.mid')

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
MAX_SPEED = 8  # Maximum initial speed of ball
TRAIL_LENGTH = 0  # Number of trail segments
GRAVITY = 0.25  # Gravity effect
BALL_GROWTH_RATE = 1  # Growth rate of the ball
BALL_RADIUS_THRESHOLD = 3  # Threshold radius for ending the simulation
SPEED_INCREASE_FACTOR = 1.01  # Factor to increase speed after each bounce

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TRAIL_COLORS = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 127, 255), (0, 0, 255), (139, 0, 255)]
GREY = (30, 30, 30)

# Ball settings
ball_radius = 50
ball_pos = [WIDTH // 2, 100]  # Ball starts at the top of the screen
ball_speed = [random.choice([-MAX_SPEED, MAX_SPEED]), MAX_SPEED]

# Trail settings
trail_positions = []

# List to store hit points on the circle
hit_points = []

left_hand_index = 0
right_hand_play_count = 0
bounce_count = 0
circle_shrink_count = 0  # Counter for how many times the circles have shrunk
game_over = False
show_end_message = False
end_message_start_time = None

NOTE_OFF_EVENT = pygame.USEREVENT + 1

# Create a list to store audio segments
audio_segments = []


class Circle:
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        self.hue = 0

    def draw(self, screen):
        if self.radius > 0:
            self.hue = (self.hue + 0.0025) % 1.0  # Faster color change
            rgb_color = colorsys.hsv_to_rgb(self.hue, 1.0, 1.0)
            color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
            pygame.draw.circle(screen, color, (self.x, self.y), self.radius, 5)


# Function to draw lines from the hit points to the center of the ball
def draw_lines(screen, hit_points, ball_center):
    for hit_point, circle in hit_points:
        hue = random.random()  # Random hue for each line
        rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
        if circle is not None:  # If the collision was with a circle
            new_collision_point = closest_point_on_circle(hit_point, circle)
            pygame.draw.line(screen, color, new_collision_point, ball_center, 2)


left_circle = Circle(100, HEIGHT // 2 + 100, 500)
right_circle = Circle(WIDTH - 100, HEIGHT // 2 + 100, 500)


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


def closest_point_on_circle(ball_pos, circle):
    angle = math.atan2(ball_pos[1] - circle.y, ball_pos[0] - circle.x)
    return (circle.x + circle.radius * math.cos(angle), circle.y + circle.radius * math.sin(angle))


def check_ball_circle_collision(ball_pos, ball_speed, ball_radius, circle):
    global circle_shrink_count
    distance = math.hypot(ball_pos[0] - circle.x, ball_pos[1] - circle.y)
    if distance <= ball_radius + circle.radius:
        overlap = ball_radius + circle.radius - distance
        normal = [(ball_pos[0] - circle.x) / distance, (ball_pos[1] - circle.y) / distance]
        ball_pos[0] += normal[0] * overlap  # Move ball out of collision
        ball_pos[1] += normal[1] * overlap  # Move ball out of collision
        ball_speed[:] = reflect_velocity(ball_speed, normal)
        randomize_direction(ball_speed)
        increase_speed(ball_speed)
        play_piano_notes()
        collision_point = closest_point_on_circle(ball_pos, circle)
        hit_points.append([collision_point, circle])  # Store circle for shrinking line
        circle.radius *= 0.975
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
        if ball_pos[0] - ball_radius <= 0:
            ball_pos[0] = ball_radius  # Ensure ball is within bounds
            ball_speed[0] = abs(ball_speed[0])  # Reflect speed
            randomize_direction(ball_speed)
            play_piano_notes()
            if not show_end_message:
                bounce_count += 1
            ball_radius *= BALL_GROWTH_RATE

        if ball_pos[0] + ball_radius >= WIDTH:
            ball_pos[0] = WIDTH - ball_radius  # Ensure ball is within bounds
            ball_speed[0] = -abs(ball_speed[0])  # Reflect speed
            randomize_direction(ball_speed)
            play_piano_notes()
            if not show_end_message:
                bounce_count += 1
            ball_radius *= BALL_GROWTH_RATE

        if ball_pos[1] - ball_radius <= 0:
            ball_pos[1] = ball_radius  # Ensure ball is within bounds
            ball_speed[1] = abs(ball_speed[1])  # Reflect speed
            randomize_direction(ball_speed)
            play_piano_notes()
            if not show_end_message:
                bounce_count += 1
            ball_radius *= BALL_GROWTH_RATE

        if ball_pos[1] + ball_radius >= HEIGHT:
            ball_pos[1] = HEIGHT - ball_radius  # Ensure ball is within bounds
            ball_speed[1] = -abs(ball_speed[1])  # Reflect speed
            randomize_direction(ball_speed)
            play_piano_notes()
            if not show_end_message:
                bounce_count += 1
            ball_radius *= BALL_GROWTH_RATE

        # Ball collision with circles
        if check_ball_circle_collision(ball_pos, ball_speed, ball_radius, left_circle) or check_ball_circle_collision(
                ball_pos, ball_speed, ball_radius, right_circle):
            if not show_end_message:
                bounce_count += 1
            ball_radius *= BALL_GROWTH_RATE

        # Update trail positions
        trail_positions.append(tuple(ball_pos))
        if len(trail_positions) > TRAIL_LENGTH:
            trail_positions.pop(0)

        # Check if ball size threshold is met
        if ball_pos[1] >= HEIGHT - 200:
            show_end_message = True
            if end_message_start_time is None:
                end_message_start_time = time.time()
    else:
        running = False

    # Draw everything
    screen.fill(BLACK)

    if not game_over:
        # Draw title and bounce counter
        title_text = font.render("GUESS THE NUMBER OF BOUCES", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))

        # Draw bounce counter
        bounce_counter_text = font.render(f"Bounce Count: {bounce_count}", True, WHITE)
        screen.blit(bounce_counter_text, (WIDTH // 2 - bounce_counter_text.get_width() // 2, 150))

        # Draw lines from hit points to the center of the ball
        draw_lines(screen, hit_points, ball_pos)

        # Draw trail
        for i, pos in enumerate(trail_positions):
            color = TRAIL_COLORS[i % len(TRAIL_COLORS)]
            pygame.draw.circle(screen, color, pos, ball_radius)

        # Draw circles
        left_circle.draw(screen)
        right_circle.draw(screen)

        # Draw ball
        pygame.draw.circle(screen, WHITE, ball_pos, ball_radius)

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
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 800+idx * 30))

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
