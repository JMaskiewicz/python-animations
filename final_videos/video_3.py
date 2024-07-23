import pygame
import pygame.midi
import random
import time
import threading
import imageio
import mido
from pydub import AudioSegment
from pydub.generators import Sine
from moviepy.editor import VideoFileClip, AudioFileClip
import math

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

# Constants
WIDTH, HEIGHT = 720, 1280
FPS = 60
MAX_SPEED = 5  # Maximum speed of objects
BALL_RADIUS = 15
PARTICLE_COUNT = 100  # Number of particles when a figure breaks
SPEED_INCREMENT = 1.25  # Speed increment factor
INITIAL_SPEED_MULTIPLIER = 1.0  # Initial speed multiplier

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Create Pygame window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Escape Simulation")

# Initialize font
font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 64)

# Setup video writer
video_writer = imageio.get_writer(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_3\simulation.mp4', fps=FPS)

# Create a list to store audio segments
audio_segments = []

# Figures specifications with different scales
figures = [
    {"sides": 3, "color": (255, 0, 0), "hole_size": 20, "rotation_speed": 0.0075, "scale": 0.3},
    {"sides": 4, "color": (0, 255, 0), "hole_size": 30, "rotation_speed": -0.01, "scale": 0.5},
    {"sides": 5, "color": (0, 0, 255), "hole_size": 40, "rotation_speed": 0.015, "scale": 0.8},
    {"sides": 6, "color": (255, 255, 0), "hole_size": 50, "rotation_speed": -0.02, "scale": 1},
    {"sides": 7, "color": (255, 0, 255), "hole_size": 60, "rotation_speed": 0.0225, "scale": 1.2},
    {"sides": 8, "color": (0, 255, 255), "hole_size": 70, "rotation_speed": -0.025, "scale": 1.5}
]

# Particle class for visual effects
class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.dx = random.uniform(-2, 2)
        self.dy = random.uniform(2, 5)
        self.color = color
        self.size = random.randint(2, 5)
        self.lifetime = random.uniform(0.5, 1.5)  # Lifetime in seconds
        self.creation_time = time.time()

    def move(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

    def is_alive(self):
        return time.time() - self.creation_time < self.lifetime

# Ball class
class Ball:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.dx = random.uniform(-MAX_SPEED, MAX_SPEED) * INITIAL_SPEED_MULTIPLIER
        self.dy = random.uniform(-MAX_SPEED, MAX_SPEED) * INITIAL_SPEED_MULTIPLIER
        self.color = (255, 255, 255)
        self.radius = BALL_RADIUS
        self.bounce_count = 0
        self.speed_multiplier = INITIAL_SPEED_MULTIPLIER  # Speed multiplier

    def move(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def check_collision(self, vertices, hole_start, hole_end):
        passed_through_gap = self.line_circle_collision(hole_start, hole_end)

        if passed_through_gap:
            return True

        for i in range(len(vertices)):
            next_i = (i + 1) % len(vertices)
            if not self.is_point_in_hole(vertices[i], vertices[next_i], hole_start, hole_end):
                if self.line_circle_collision(vertices[i], vertices[next_i]):
                    self.bounce(vertices[i], vertices[next_i])
                    self.bounce_count += 1
                    play_piano_notes()
                    break

        return False

    def is_point_in_hole(self, p1, p2, hole_start, hole_end):
        """ Check if the line segment between p1 and p2 is part of the hole """
        return (p1 == hole_start and p2 == hole_end) or (p1 == hole_end and p2 == hole_start)

    def line_circle_collision(self, p1, p2):
        line_vec = (p2[0] - p1[0], p2[1] - p1[1])
        p1_to_circle = (self.x - p1[0], self.y - p1[1])
        line_len = math.sqrt(line_vec[0] ** 2 + line_vec[1] ** 2)
        line_unit_vec = (line_vec[0] / line_len, line_vec[1] / line_len)
        projection = p1_to_circle[0] * line_unit_vec[0] + p1_to_circle[1] * line_unit_vec[1]
        if projection < 0:
            closest_point = p1
        elif projection > line_len:
            closest_point = p2
        else:
            closest_point = (p1[0] + projection * line_unit_vec[0], p1[1] + projection * line_unit_vec[1])
        dist = math.sqrt((closest_point[0] - self.x) ** 2 + (closest_point[1] - self.y) ** 2)
        return dist <= self.radius

    def bounce(self, p1, p2):
        line_vec = (p2[0] - p1[0], p2[1] - p1[1])
        line_len = math.sqrt(line_vec[0] ** 2 + line_vec[1] ** 2)
        line_unit_vec = (line_vec[0] / line_len, line_vec[1] / line_len)
        normal_vec = (-line_unit_vec[1], line_unit_vec[0])
        vel_dot_normal = self.dx * normal_vec[0] + self.dy * normal_vec[1]
        self.dx -= 2 * vel_dot_normal * normal_vec[0]
        self.dy -= 2 * vel_dot_normal * normal_vec[1]

        # Recalculate position to avoid getting stuck
        self.x += self.dx
        self.y += self.dy

def draw_polygon(sides, color, hole_size, angle, scale, line_width=10):
    angle_step = 2 * math.pi / sides
    radius = (WIDTH // 3) * scale
    vertices = [(WIDTH // 2 + radius * math.cos(i * angle_step + angle),
                 HEIGHT // 2 + radius * math.sin(i * angle_step + angle))
                for i in range(sides)]

    hole_index = sides // 2
    hole_start = vertices[hole_index]
    next_index = (hole_index + 1) % sides
    hole_end = ((hole_start[0] + vertices[next_index][0]) / 2, (hole_start[1] + vertices[next_index][1]) / 2)

    # Draw the polygon except for the part that has the hole
    for i in range(sides):
        next_i = (i + 1) % len(vertices)
        if i == hole_index:
            pygame.draw.line(screen, color, hole_end, vertices[next_i], line_width)
        elif next_i == hole_index:
            pygame.draw.line(screen, color, vertices[i], hole_start, line_width)
        else:
            pygame.draw.line(screen, color, vertices[i], vertices[next_i], line_width)

    return vertices, hole_start, hole_end

NOTE_OFF_EVENT = pygame.USEREVENT + 1

left_hand_index = 0
right_hand_play_count = 0

def midi_note_to_freq(note):
    """ Convert MIDI note to frequency. """
    return 440.0 * (2.0 ** ((note - 69) / 12.0))

def play_note_thread(note, duration=0.1):
    freq = midi_note_to_freq(note)
    note_sound = Sine(freq).to_audio_segment(duration=int(duration * 1000))
    audio_segments.append((note_sound, time.time()))  # Append note sound and the current time
    midi_out.note_on(note, 127)
    time.sleep(duration)  # Play the note for the given duration
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

# Main loop
running = True
clock = pygame.time.Clock()
ball = Ball()
particles = []
figure_index = 0
start_time = time.time()
rotation_angles = [0] * len(figures)  # Initialize rotation angles for all figures
show_end_message = False
end_message_start_time = 0

while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BLACK)

    if not show_end_message:
        for i in range(figure_index, len(figures)):
            rotation_angles[i] += figures[i]["rotation_speed"]
            draw_polygon(figures[i]["sides"], figures[i]["color"], figures[i]["hole_size"], rotation_angles[i],
                         figures[i]["scale"])

        vertices, hole_start, hole_end = draw_polygon(figures[figure_index]["sides"], figures[figure_index]["color"],
                                                      figures[figure_index]["hole_size"], rotation_angles[figure_index],
                                                      figures[figure_index]["scale"])
        ball.move()
        if ball.check_collision(vertices, hole_start, hole_end):
            ball.color = figures[figure_index]["color"]  # Change ball color to the vanished figure's color
            figure_index += 1
            if figure_index >= len(figures):
                show_end_message = True
                end_message_start_time = time.time()
            else:
                # Increase ball speed and apply speed multiplier
                ball.speed_multiplier *= SPEED_INCREMENT
                ball.dx = ball.dx / abs(ball.dx) * MAX_SPEED * ball.speed_multiplier
                ball.dy = ball.dy / abs(ball.dy) * MAX_SPEED * ball.speed_multiplier

                # Create particles for breaking effect
                for _ in range(PARTICLE_COUNT):
                    particles.append(Particle(WIDTH // 2, HEIGHT // 2, figures[figure_index - 1]["color"]))

        ball.draw(screen)
    else:
        # Continue to move the ball
        ball.move()
        ball.draw(screen)

        # Draw end message
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
            running = False

    # Draw particles
    for particle in particles:
        particle.move()
        if particle.is_alive():
            particle.draw(screen)
        else:
            particles.remove(particle)

    # Draw title and bounce counter
    title_text = font.render("Bounce to the Beat!", True, WHITE)
    bounce_text = font.render(f"BOUNCES: {ball.bounce_count}", True, WHITE)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 50))
    screen.blit(bounce_text, (WIDTH // 2 - bounce_text.get_width() // 2, 150))

    pygame.display.flip()

    # Capture the screen for video
    frame = pygame.surfarray.array3d(screen)
    frame = frame.transpose([1, 0, 2])  # Pygame uses (width, height, channels), ImageIO uses (height, width, channels)
    video_writer.append_data(frame)

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
final_audio.export(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_3\simulation_sound.mp3', format="mp3")

# Close the MIDI output
midi_out.close()
pygame.midi.quit()
pygame.quit()

# Combine video and audio
video_clip = VideoFileClip(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_3\simulation.mp4')
audio_clip = AudioFileClip(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_3\simulation_sound.mp3')

# Trim the audio clip to match the duration of the video clip
audio_clip = audio_clip.subclip(0, video_clip.duration)

final_clip = video_clip.set_audio(audio_clip)
final_clip.write_videofile(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_3\final_output.mp4', codec="libx264")

print(f"Simulation finished with {ball.bounce_count} bounces.")
