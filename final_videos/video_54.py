# Existing imports
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
import colorsys

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
pygame.display.set_caption("Rotating Triangle with Trailing Effect and Dynamic Circles")

# Constants
FPS = 60
MAX_SPEED = 3  # Maximum initial speed of triangle
TRAIL_LENGTH = 40  # Number of trail segments
GRAVITY = 0.05  # Gravity effect
CIRCLE_SHRINK_RATE = 1  # Rate at which circles shrink
NEW_CIRCLE_INTERVAL = 0.9  # Initial time interval in seconds to add new circle
MIN_CIRCLE_RADIUS = 5  # Minimum circle radius before disappearing
SPEED_INCREASE_FACTOR = 1.02  # Factor to increase speed after each bounce
CIRCLE_CREATION_ACCELERATION = 0.998  # Factor to decrease interval for circle creation after each bounce

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
TRAIL_COLORS = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 127, 255), (0, 0, 255), (139, 0, 255)]

# Triangle settings
TRIANGLE_SIZE = 30
triangle_pos = [WIDTH // 2, HEIGHT // 2]
triangle_speed = [random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])]
triangle_angle = 0  # Initial rotation angle


# Function to rotate and draw the triangle
def draw_rotated_triangle(surface, color, position, size, angle):
    half_size = size / 2
    points = [
        (position[0] + half_size * math.cos(math.radians(angle)),
         position[1] + half_size * math.sin(math.radians(angle))),
        (position[0] + half_size * math.cos(math.radians(angle + 120)),
         position[1] + half_size * math.sin(math.radians(angle + 120))),
        (position[0] + half_size * math.cos(math.radians(angle + 240)),
         position[1] + half_size * math.sin(math.radians(angle + 240))),
    ]
    pygame.draw.polygon(surface, color, points)


# Initialize hue for color transition
hue = 0.0


# Circle settings
class Circle:
    def __init__(self, radius, hue):
        # Convert hue to RGB color
        rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        self.color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
        self.radius = radius

    def draw(self, screen):
        if self.radius > 0:
            pygame.draw.circle(screen, self.color, (WIDTH // 2, HEIGHT // 2), self.radius, 5)

    def update(self):
        self.radius -= CIRCLE_SHRINK_RATE


# Initialize circles with dynamic colors
circles = [Circle(radius, hue) for radius in range(400, 100, -50)]

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
video_writer = imageio.get_writer(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_54\1_ball_in_circles_sound.mp4',
                                  fps=FPS)

# Main game loop
running = True
clock = pygame.time.Clock()
start_time = time.time()
last_circle_add_time = start_time
no_circle_time = None

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

        # Rotate the triangle
        triangle_angle = (triangle_angle + 5) % 360

        # Triangle collision with walls
        if triangle_pos[0] <= TRIANGLE_SIZE // 2 or triangle_pos[0] >= WIDTH - TRIANGLE_SIZE // 2:
            triangle_speed[0] = -triangle_speed[0]
            randomize_direction(triangle_speed)
            play_piano_notes()  # Play piano notes on bounce
            if no_circle_time is None:
                bounce_count += 1

        if triangle_pos[1] <= TRIANGLE_SIZE // 2 or triangle_pos[1] >= HEIGHT - TRIANGLE_SIZE // 2:
            triangle_speed[1] = -triangle_speed[1]
            randomize_direction(triangle_speed)
            play_piano_notes()  # Play piano notes on bounce
            if no_circle_time is None:
                bounce_count += 1

        # Check collision with circles
        for circle in circles[:]:
            dist = math.hypot(triangle_pos[0] - WIDTH // 2, triangle_pos[1] - HEIGHT // 2)
            if circle.radius - TRIANGLE_SIZE <= dist <= circle.radius + TRIANGLE_SIZE:
                normal = [(triangle_pos[0] - WIDTH // 2) / dist, (triangle_pos[1] - HEIGHT // 2) / dist]
                triangle_speed = reflect_velocity(triangle_speed, normal)
                circles.remove(circle)
                increase_speed(triangle_speed)
                NEW_CIRCLE_INTERVAL *= CIRCLE_CREATION_ACCELERATION  # Decrease interval for circle creation
                play_piano_notes()  # Play piano notes on bounce
                if no_circle_time is None:
                    bounce_count += 1
                break

        # Update circles
        for circle in circles:
            circle.update()
        circles = [circle for circle in circles if circle.radius > MIN_CIRCLE_RADIUS]

        # Update the hue for the next circle
        hue = (hue + 0.1) % 1.0

        # Add new circle based on current interval if there are circles
        if circles:
            current_time = time.time()
            if current_time - last_circle_add_time >= NEW_CIRCLE_INTERVAL:
                new_circle = Circle(400, hue)  # Larger new circle with updated hue
                circles.append(new_circle)
                last_circle_add_time = current_time
        else:
            if no_circle_time is None:
                no_circle_time = time.time()
            elif time.time() - no_circle_time >= 5:
                game_over = True
            else:
                show_end_message = True
                if end_message_start_time is None:
                    end_message_start_time = time.time()

        # Update trail positions
        trail_positions.append(tuple(triangle_pos))
        if len(trail_positions) > TRAIL_LENGTH:
            trail_positions.pop(0)

    # Draw everything
    screen.fill(BLACK)

    if not game_over:
        # Draw title and bounce counter
        title_text = font.render("How many bounces it need to escape?", True, WHITE)
        bounce_text = font.render(f"BOUNCES: {bounce_count}", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 125))
        screen.blit(bounce_text, (WIDTH // 2 - bounce_text.get_width() // 2, 170))

        # Add watermark text
        watermark_font = pygame.font.SysFont(None, 36)
        watermark_texts = [
            watermark_font.render("yt:@jbbm_motions", True, (30, 30, 30)),
            watermark_font.render("tiktok:@jbbm_motions", True, (30, 30, 30)),
            watermark_font.render("subscribe for more!", True, (30, 30, 30))
        ]
        for idx, text in enumerate(watermark_texts):
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 1100 + idx * 30))

        # Draw circles
        for circle in circles:
            circle.draw(screen)

        # Draw trail
        for i, pos in enumerate(trail_positions):
            color = TRAIL_COLORS[i % len(TRAIL_COLORS)]
            draw_rotated_triangle(screen, color, pos, TRIANGLE_SIZE, triangle_angle)

        # Draw rotating triangle
        draw_rotated_triangle(screen, WHITE, triangle_pos, TRIANGLE_SIZE, triangle_angle)

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

# Ensure the final audio is at least as long as the game duration
final_audio += AudioSegment.silent(duration=(game_duration * 1000) - len(final_audio))

# Save the audio to a file
final_audio.export(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_54\1_ball_in_circles_sound.mp3', format="mp3")

# Close the MIDI output
midi_out.close()
pygame.midi.quit()
pygame.quit()

# Combine video and audio
video_clip = VideoFileClip(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_54\1_ball_in_circles_sound.mp4')
audio_clip = AudioFileClip(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_54\1_ball_in_circles_sound.mp3')
final_clip = video_clip.set_audio(audio_clip)
final_clip.write_videofile(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_54\1_final_output.mp4', codec="libx264")

print("Video with sound saved successfully!")
