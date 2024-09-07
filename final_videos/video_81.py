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
pygame.display.set_caption("Two Balls with Trailing Effect and Dynamic Circles")

# Constants
FPS = 60
MAX_SPEED = 8  # Maximum initial speed of ball
TRAIL_LENGTH = float('inf')  # Infinite trail
GRAVITY = 0.25  # Gravity effect
CIRCLE_SHRINK_RATE = 1  # Reduced shrink rate
MIN_CIRCLE_RADIUS = 10  # Minimum circle radius before disappearing
SPEED_INCREASE_FACTOR = 1.0025  # Factor to increase speed after each bounce
ball_size_increase = 1.005  # Factor to increase ball size after each bounce
MIN_SPEED = 2  # Minimum speed to prevent the ball from stopping
GAME_DURATION = 5  # Duration of the game in seconds

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Ball settings for both balls
BALL_RADIUS = 12
ball1_pos = [WIDTH // 3, HEIGHT // 3]  # Starting position for the first ball
ball1_speed = [-5, 5]

ball2_pos = [2 * WIDTH // 3, HEIGHT // 3]  # Starting position for the second ball
ball2_speed = [5, 5]

# Circle settings
class Circle:
    def __init__(self, radius, color):
        self.radius = radius
        self.color = color

    def draw(self, screen):
        if self.radius > 0:
            pygame.draw.circle(screen, self.color, (WIDTH // 2, HEIGHT // 2), self.radius, 10)

    def update(self, color):
        self.radius *= CIRCLE_SHRINK_RATE
        self.color = color  # Update color on each bounce

# Initial circle
circle = Circle(350, WHITE)

# Trail settings for both balls
trail_positions_1 = []
trail_positions_2 = []

left_hand_index = 0
right_hand_play_count = 0
bounce_count = 0  # Global bounce count
game_over = False
show_end_message = False
end_message_start_time = None

NOTE_OFF_EVENT = pygame.USEREVENT + 1

# Create a list to store audio segments
audio_segments = []

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
large_font = pygame.font.SysFont(None, 64)

# Setup video writer
video_writer = imageio.get_writer(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_6\6_ball_in_circle_sound.mp4', fps=FPS)

# Function to calculate hue color
def get_hue_color(hue):
    color = pygame.Color(0)
    color.hsva = (hue % 360, 100, 100)
    return color

# Constants
CIRCLE_SHRINK_RATE = 1  # Slightly increased shrink rate to slow down shrinking
COLLISION_COOLDOWN = 0.15  # Time in seconds during which collision detection is disabled after a collision

# Update ball positions and handle collisions with walls and circle
def update_ball(ball_pos, ball_speed, trail_positions, hue_value):
    global bounce_count  # Declare as global to avoid UnboundLocalError

    # Update ball position
    ball_speed[1] += GRAVITY
    ball_pos[0] += ball_speed[0]
    ball_pos[1] += ball_speed[1]

    # Ball collision with walls
    if ball_pos[0] - BALL_RADIUS <= 0 or ball_pos[0] + BALL_RADIUS >= WIDTH:
        ball_speed[0] = -ball_speed[0]
        play_piano_notes()
        bounce_count += 1

    if ball_pos[1] - BALL_RADIUS <= 0 or ball_pos[1] + BALL_RADIUS >= HEIGHT:
        ball_speed[1] = -ball_speed[1]
        play_piano_notes()
        bounce_count += 1

    # Check collision with the circle using the ball's radius
    dist = math.hypot(ball_pos[0] - WIDTH // 2, ball_pos[1] - HEIGHT // 2)

    # Collision condition adjusted to include the ball's radius
    if dist + BALL_RADIUS >= circle.radius:
        normal = [(ball_pos[0] - WIDTH // 2) / dist, (ball_pos[1] - HEIGHT // 2) / dist]
        ball_speed = reflect_velocity(ball_speed, normal)
        increase_speed(ball_speed)
        play_piano_notes()
        bounce_count += 1

        # Move the ball outside the circle so it doesn't overlap
        overlap = dist + BALL_RADIUS - circle.radius
        ball_pos[0] -= overlap * normal[0]
        ball_pos[1] -= overlap * normal[1]

    # Update trail positions
    trail_positions.append((tuple(ball_pos), BALL_RADIUS))
    if len(trail_positions) > TRAIL_LENGTH:
        trail_positions.pop(0)

    return ball_speed

# Main game loop
running = True
clock = pygame.time.Clock()
start_time = time.time()
trail_length = TRAIL_LENGTH  # Initial trail length
hue_value_1 = 0  # Initial hue value for ball 1
hue_value_2 = 180  # Initial hue value for ball 2

while running:
    clock.tick(FPS)

    current_time = time.time()
    elapsed_time = current_time - start_time

    if current_time - start_time > 50 and not show_end_message:
        show_end_message = True
        end_message_start_time = current_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update ball 1
    ball1_speed = update_ball(ball1_pos, ball1_speed, trail_positions_1, hue_value_1)

    # Update ball 2
    ball2_speed = update_ball(ball2_pos, ball2_speed, trail_positions_2, hue_value_2)

    # Update hue values for both balls
    hue_value_1 += 2
    hue_value_2 += 2

    # Clear the screen
    screen.fill(BLACK)

    # Draw the shrinking circle
    circle.draw(screen)

    # Draw trail for ball 1
    for pos, radius in trail_positions_1:
        pygame.draw.circle(screen, get_hue_color(hue_value_1), pos, radius, 1)

    # Draw trail for ball 2
    for pos, radius in trail_positions_2:
        pygame.draw.circle(screen, get_hue_color(hue_value_2), pos, radius, 1)

    # Now draw the balls on top of the trails

    # Draw black outline (slightly larger than the ball)
    pygame.draw.circle(screen, BLACK, ball1_pos, BALL_RADIUS + 5)
    pygame.draw.circle(screen, BLACK, ball2_pos, BALL_RADIUS + 5)


    # Draw the actual balls on top of the black outlines
    pygame.draw.circle(screen, get_hue_color(hue_value_1), ball1_pos, BALL_RADIUS)  # Ball 1
    pygame.draw.circle(screen, get_hue_color(hue_value_2), ball2_pos, BALL_RADIUS)  # Ball 2

    # Watermark and subscribe messages
    watermark_font = pygame.font.SysFont(None, 36)
    watermark_texts = [
        watermark_font.render("yt:@jbbm_motions", True, (150, 150, 150)),
        watermark_font.render("tiktok:@jbbm_motions", True, (150, 150, 150)),
        watermark_font.render("subscribe for more!", True, (150, 150, 150))
    ]
    for idx, text in enumerate(watermark_texts):
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 1000 + idx * 30))

    # Title and bounce counter
    title_text = font.render("Watch the Balls!", True, WHITE)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 125))

    bounce_text = font.render(f"BOUNCES: {bounce_count}", True, WHITE)
    screen.blit(bounce_text, (WIDTH // 2 - bounce_text.get_width() // 2, 240))

    # End message after game over
    if show_end_message:
        game_over_text1 = large_font.render("LIKE", True, WHITE)
        game_over_text2 = large_font.render("FOLLOW", True, WHITE)
        game_over_text3 = large_font.render("SUBSCRIBE", True, WHITE)
        game_over_text4 = large_font.render("COMMENT WHAT TO DO NEXT", True, WHITE)
        screen.blit(game_over_text1, (WIDTH // 2 - game_over_text1.get_width() // 2, HEIGHT // 2 - 150))
        screen.blit(game_over_text2, (WIDTH // 2 - game_over_text2.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(game_over_text3, (WIDTH // 2 - game_over_text3.get_width() // 2, HEIGHT // 2 + 50))
        screen.blit(game_over_text4, (WIDTH // 2 - game_over_text4.get_width() // 2, HEIGHT // 2 + 150))

        if current_time - end_message_start_time >= 3:
            running = False

    # Update display
    pygame.display.flip()

    # Capture the screen for video
    frame = pygame.surfarray.array3d(screen)
    frame = frame.transpose([1, 0, 2])  # Pygame uses (width, height, channels), ImageIO uses (height, width, channels)
    video_writer.append_data(frame)

# Close the video writer
video_writer.close()

# Concatenate all audio segments and export final audio and video as before
