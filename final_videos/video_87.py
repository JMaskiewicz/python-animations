import pygame
import pygame.midi
import random
import math
import time
import mido
import threading
import imageio
import colorsys
from pydub import AudioSegment
from pydub.generators import Sine
from moviepy.editor import VideoFileClip, AudioFileClip
import os

# Video number
number = 87

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
pygame.display.set_caption("Ball with Trailing Effect and Dynamic Hexagons")

# Constants
FPS = 60
MAX_SPEED = 3  # Maximum initial speed of ball
GRAVITY = 0.1  # Gravity effect
HEXAGON_SHRINK_RATE = 1.7  # Rate at which hexagons shrink
NEW_HEXAGON_INTERVAL = 0.25  # Initial time interval in seconds to add new hexagon
MIN_HEXAGON_SIDE = 5  # Minimum hexagon side length before disappearing
SPEED_INCREASE_FACTOR = 1.01  # Factor to increase speed after each bounce
HEXAGON_CREATION_ACCELERATION = 0.998  # Factor to decrease interval for hexagon creation after each bounce

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Ball settings
BALL_RADIUS = 15
ball_pos = [WIDTH // 2, HEIGHT // 2]
ball_speed = [random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])]
hue_value_1 = 0  # Initial hue value for trail color

# Hexagon settings
class Hexagon:
    def __init__(self, side_length, hue, rotation_speed, initial_angle=0):
        self.side_length = side_length
        self.hue = hue
        self.rotation_speed = rotation_speed
        self.angle = initial_angle

    def draw(self, screen):
        if self.side_length > 0:
            # Convert the HSV hue to RGB color
            rgb_color = colorsys.hsv_to_rgb(self.hue, 1.0, 1.0)
            color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))

            center = (WIDTH // 2, HEIGHT // 2)
            half_length = self.side_length / 2
            height = math.sqrt(3) * half_length
            vertices = [
                (center[0] + half_length * math.cos(self.angle + i * math.pi / 3),
                 center[1] + half_length * math.sin(self.angle + i * math.pi / 3))
                for i in range(6)
            ]
            pygame.draw.polygon(screen, color, vertices, 5)

    def update(self):
        self.side_length -= HEXAGON_SHRINK_RATE
        self.angle += self.rotation_speed
        self.hue = (self.hue + 0.001) % 1.0  # Smoothly increase the hue for color change
        if self.angle >= 2 * math.pi:
            self.angle -= 2 * math.pi

    def get_edges(self):
        center = (WIDTH // 2, HEIGHT // 2)
        half_length = self.side_length / 2
        height = math.sqrt(3) * half_length
        vertices = [
            (center[0] + half_length * math.cos(self.angle + i * math.pi / 3),
             center[1] + half_length * math.sin(self.angle + i * math.pi / 3))
            for i in range(6)
        ]
        edges = [(vertices[i], vertices[(i + 1) % 6]) for i in range(6)]
        return edges

# Create hexagons with smooth hue transition
initial_angles = [i * math.pi / 3 for i in range(6)]  # Angles separated by 60 degrees (π/3 radians)
hexagons = [
    Hexagon(side_length, hue=i * 0.1, rotation_speed=0.01, initial_angle=initial_angles[i % len(initial_angles)])
    for i, side_length in enumerate(range(700, 300, -50))
]

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

# Initialize font
font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 64)

# Setup video writer
video_writer = imageio.get_writer(rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}\{number}_ball_in_lines_sound.mp4', fps=FPS)

# Main game loop
running = True
clock = pygame.time.Clock()
start_time = time.time()
last_hexagon_add_time = start_time
no_hexagon_time = None

rt = random.uniform(-0.1, 0.1)

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
        if ball_pos[0] <= BALL_RADIUS or ball_pos[0] >= WIDTH - BALL_RADIUS:
            ball_speed[0] = -ball_speed[0]
            randomize_direction(ball_speed)
            play_piano_notes()  # Play piano notes on bounce
            if no_hexagon_time is None:
                bounce_count += 1

        if ball_pos[1] <= BALL_RADIUS or ball_pos[1] >= HEIGHT - BALL_RADIUS:
            ball_speed[1] = -ball_speed[1]
            randomize_direction(ball_speed)
            play_piano_notes()  # Play piano notes on bounce
            if no_hexagon_time is None:
                bounce_count += 1

        # Check collision with hexagons
        for hexagon in hexagons[:]:
            edges = hexagon.get_edges()
            for edge in edges:
                dist = point_to_line_distance(ball_pos, edge[0], edge[1])
                if dist <= BALL_RADIUS:
                    normal = [-(edge[1][1] - edge[0][1]), edge[1][0] - edge[0][0]]
                    normal_mag = math.hypot(normal[0], normal[1])
                    normal = [normal[0] / normal_mag, normal[1] / normal_mag]
                    ball_speed = reflect_velocity(ball_speed, normal)
                    hexagons.remove(hexagon)
                    increase_speed(ball_speed)
                    NEW_HEXAGON_INTERVAL *= HEXAGON_CREATION_ACCELERATION  # Decrease interval for hexagon creation
                    play_piano_notes()  # Play piano notes on bounce
                    if no_hexagon_time is None:
                        bounce_count += 1
                    break

        # Update hexagons
        for hexagon in hexagons:
            hexagon.update()
        hexagons = [hexagon for hexagon in hexagons if hexagon.side_length > MIN_HEXAGON_SIDE]

        # Add new hexagon based on current interval if there are hexagons
        if hexagons:
            current_time = time.time()
            if current_time - last_hexagon_add_time >= NEW_HEXAGON_INTERVAL:
                new_hexagon = Hexagon(800, hue=len(hexagons) * 0.1, rotation_speed=rt)
                rt = random.uniform(-0.1, 0.1)
                hexagons.append(new_hexagon)
                last_hexagon_add_time = current_time
        else:
            if no_hexagon_time is None:
                no_hexagon_time = time.time()
            elif time.time() - no_hexagon_time >= 5:
                game_over = True
            else:
                show_end_message = True
                if end_message_start_time is None:
                    end_message_start_time = time.time()

        # Update trail positions
        trail_positions.append((tuple(ball_pos), BALL_RADIUS))

        # Update hue value for trail
        hue_value_1 += 0.01

    # Draw everything
    screen.fill(BLACK)

    if not game_over:
        # Draw title and bounce counter
        title_text = font.render("HEXAGON MADNESS", True, WHITE)
        bounce_text = font.render(f"BOUNCES: {bounce_count}", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))
        screen.blit(bounce_text, (WIDTH // 2 - bounce_text.get_width() // 2, 200))

        pygame.draw.circle(screen, BLACK, ball_pos, BALL_RADIUS + 8)  # Slightly larger circle for the border

        # Now draw the ball itself
        pygame.draw.circle(screen, WHITE, ball_pos, BALL_RADIUS)

        # When drawing the trail, we could reduce the alpha (transparency) or brightness:
        for i, (pos, radius) in enumerate(trail_positions):
            hue = (hue_value_1 + i * 0.01) % 1.0  # Increment hue for each trail position
            rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            # Dim the brightness of the trail color slightly for a more subtle effect
            dimmed_color = (int(rgb_color[0] * 150), int(rgb_color[1] * 150), int(rgb_color[2] * 150))
            pygame.draw.circle(screen, dimmed_color, pos, radius)

        # Draw hexagons on top of the trail
        for hexagon in hexagons:
            hexagon.draw(screen)

        watermark_font = pygame.font.SysFont(None, 36)
        watermark_texts = [
            watermark_font.render("yt:@jbbm_motions", True, (50, 50, 50)),
            watermark_font.render("tiktok:@jbbm_motions", True, (50, 50, 50)),
            watermark_font.render("subscribe for more!", True, (50, 50, 50))
        ]
        for idx, text in enumerate(watermark_texts):
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 1050 + idx * 30))

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
