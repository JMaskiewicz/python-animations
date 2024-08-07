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

# Constants
WIDTH, HEIGHT = 720, 1280
FPS = 90
MAX_SPEED = 4  # Maximum speed of objects
BALL_RADIUS = 15
SPEED_INCREMENT = 1  # Speed increment factor
INITIAL_SPEED_MULTIPLIER = 1.0  # Initial speed multiplier
GRAVITY = 2  # Gravity effect

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREY = (30, 30, 30)

# Create Pygame window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Escape Simulation")

# Initialize font
font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 64)

# Setup video writer
video_writer = imageio.get_writer(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_33\simulation.mp4', fps=FPS)

# Create a list to store audio segments
audio_segments = []

# Figures specifications with different scales
figures = [
    {"sides": 80, "color": (0, 255, 255), "hole_size": 10, "rotation_speed": -0.015, "scale": 0.5},
    {"sides": 80, "color": (255, 0, 0), "hole_size": 10, "rotation_speed": 0.015, "scale": 1},
    {"sides": 80, "color": (0, 255, 0), "hole_size": 10, "rotation_speed": -0.01, "scale": 1.5}
]

# Particle class
class Particle:
    def __init__(self, position):
        self.position = list(position)
        self.velocity = [random.uniform(-2, 2), random.uniform(-2, 2)]
        self.lifetime = random.uniform(0.5, 1.0)

    def update(self, dt):
        self.lifetime -= dt
        self.position[0] += self.velocity[0] * dt * 60
        self.position[1] += self.velocity[1] * dt * 60

    def draw(self, screen):
        if self.lifetime > 0:
            pygame.draw.circle(screen, WHITE, (int(self.position[0]), int(self.position[1])), 2)

# Ball class
class Ball:
    def __init__(self, x=None, y=None):
        if x is None or y is None:
            x = WIDTH // 2 + random.uniform(-10, 10)  # Add a small random offset
            y = HEIGHT // 2 + random.uniform(-10, 10)  # Add a small random offset
        self.x = x
        self.y = y
        self.dx = random.uniform(-MAX_SPEED, MAX_SPEED) * INITIAL_SPEED_MULTIPLIER
        self.dy = random.uniform(-MAX_SPEED, MAX_SPEED) * INITIAL_SPEED_MULTIPLIER
        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        self.radius = BALL_RADIUS
        self.bounce_count = 0
        self.speed_multiplier = INITIAL_SPEED_MULTIPLIER  # Speed multiplier

    def move(self):
        self.dy += GRAVITY  # Apply gravity
        self.x += self.dx
        self.y += self.dy

        # Check for collision with edges
        if self.x <= self.radius or self.x >= WIDTH - self.radius:
            self.dx *= -1
            # Adjust position to be inside the boundary
            self.x = max(self.radius, min(self.x, WIDTH - self.radius))
            play_piano_notes()
        if self.y <= self.radius:
            self.dy *= -1
            # Adjust position to be inside the boundary
            self.y = max(self.radius, self.y)
            play_piano_notes()
            return "top"
        if self.y >= HEIGHT - self.radius:
            return "bottom"  # Indicates that the ball hit the bottom
        return None

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def check_collision(self, vertices, hole_indices, particles):
        for i in range(len(vertices)):
            next_i = (i + 1) % len(vertices)
            if not self.is_index_in_hole(i, hole_indices):
                if self.line_circle_collision(vertices[i], vertices[next_i]):
                    self.bounce(vertices[i], vertices[next_i])
                    self.bounce_count += 1
                    play_piano_notes()
                    draw_sparkles(particles, self.x, self.y)
                    break

    def is_index_in_hole(self, index, hole_indices):
        """ Check if the index is part of the hole """
        return index in hole_indices

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

        # Recalculate position to avoid getting stuck inside the polygon
        p1_to_circle = (self.x - p1[0], self.y - p1[1])
        projection = p1_to_circle[0] * line_unit_vec[0] + p1_to_circle[1] * line_unit_vec[1]
        if projection < 0:
            closest_point = p1
        elif projection > line_len:
            closest_point = p2
        else:
            closest_point = (p1[0] + projection * line_unit_vec[0], p1[1] + projection * line_unit_vec[1])
        dist = math.sqrt((closest_point[0] - self.x) ** 2 + (closest_point[1] - self.y) ** 2)
        overlap_distance = self.radius - dist + 1  # Ensure it is out of the polygon
        self.x += overlap_distance * normal_vec[0]
        self.y += overlap_distance * normal_vec[1]

        # Add a small speed towards the center
        center_x, center_y = WIDTH // 2, HEIGHT // 2
        to_center_vec = (center_x - self.x, center_y - self.y)
        to_center_dist = math.sqrt(to_center_vec[0] ** 2 + to_center_vec[1] ** 2)
        if to_center_dist > 0:  # Prevent division by zero
            to_center_unit_vec = (to_center_vec[0] / to_center_dist, to_center_vec[1] / to_center_dist)
            center_premium = 0.1  # Adjust this value as needed
            self.dx += center_premium * to_center_unit_vec[0]
            self.dy += center_premium * to_center_unit_vec[1]

        # Add a small random displacement to prevent getting stuck
        self.x += random.uniform(-1, 1)
        self.y += random.uniform(-1, 1)

    def check_ball_collision(self, other, particles):
        dx = self.x - other.x
        dy = self.y - other.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance < self.radius + other.radius:
            # Swap velocities
            angle = math.atan2(dy, dx)
            speed_self = math.sqrt(self.dx ** 2 + self.dy ** 2)
            speed_other = math.sqrt(other.dx ** 2 + other.dy ** 2)
            self.dx, self.dy = speed_other * math.cos(angle), speed_other * math.sin(angle)
            other.dx, other.dy = speed_self * math.cos(angle + math.pi), speed_self * math.sin(angle + math.pi)
            draw_sparkles(particles, self.x, self.y)


def draw_polygon(sides, color, hole_size, angle, scale, line_width=10):
    angle_step = 2 * math.pi / sides
    radius = (WIDTH // 3) * scale
    vertices = [(WIDTH // 2 + radius * math.cos(i * angle_step + angle),
                 HEIGHT // 2 + radius * math.sin(i * angle_step + angle))
                for i in range(sides)]

    hole_start_index = sides // 2 - hole_size // 2
    hole_indices = [(hole_start_index + i) % sides for i in range(hole_size)]

    # Draw the polygon except for the part that has the hole
    for i in range(sides):
        next_i = (i + 1) % sides
        if not i in hole_indices:
            pygame.draw.line(screen, color, vertices[i], vertices[next_i], line_width)

    return vertices, hole_indices

def draw_sparkles(particles, x, y):
    for _ in range(10):
        particles.append(Particle([x, y]))

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
balls = [Ball()]
particles = []

figure_index = 0
start_time = time.time()
rotation_angles = [0] * len(figures)  # Initialize rotation angles for all figures
show_end_message = False
end_message_start_time = 0

while running:
    dt = clock.tick(FPS) / 1000.0  # Delta time in seconds
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BLACK)

    if not show_end_message:

        if time.time() - start_time > 50:
            show_end_message = True
            end_message_start_time = time.time()

        all_vertices = []
        all_hole_indices = []
        for i in range(len(figures)):
            rotation_angles[i] += figures[i]["rotation_speed"]
            vertices, hole_indices = draw_polygon(figures[i]["sides"], figures[i]["color"], figures[i]["hole_size"], rotation_angles[i], figures[i]["scale"])
            all_vertices.append(vertices)
            all_hole_indices.append(hole_indices)

        new_balls = []
        balls_to_remove = []
        for ball in balls:
            result = ball.move()
            if result == "bottom" or result == "top":
                # If the ball hits the top or bottom, create two new balls with random directions and remove the current ball
                for _ in range(2):
                    new_ball = Ball()
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(1, MAX_SPEED)
                    new_ball.dx = speed * math.cos(angle)
                    new_ball.dy = speed * math.sin(angle)
                    new_balls.append(new_ball)
                balls_to_remove.append(ball)
            for vertices, hole_indices in zip(all_vertices, all_hole_indices):
                ball.check_collision(vertices, hole_indices, particles)
            ball.draw(screen)

        for ball in balls:
            for other_ball in balls:
                if ball != other_ball:
                    ball.check_ball_collision(other_ball, particles)

        # Remove balls that hit the top or bottom
        balls = [ball for ball in balls if ball not in balls_to_remove]

        balls.extend(new_balls)

        if figure_index >= len(figures):
            show_end_message = True
            end_message_start_time = time.time()
        else:
            # Increase ball speed and apply speed multiplier
            for ball in balls:
                ball.speed_multiplier *= SPEED_INCREMENT
                ball.dx = ball.dx / abs(ball.dx) * MAX_SPEED * ball.speed_multiplier
                ball.dy = ball.dy / abs(ball.dy) * MAX_SPEED * ball.speed_multiplier

    else:
        # Continue to move the balls
        for ball in balls:
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

    # Update particles
    particles = [p for p in particles if p.lifetime > 0]
    for p in particles:
        p.update(dt)

    # Draw particles
    for p in particles:
        p.draw(screen)

    # Draw title and bounce counter
    title_text = font.render("CAN MY PC HANDLE THIS?", True, WHITE)
    bounce_text = font.render(f"BALLS: {len(balls)}", True, WHITE)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 50))
    screen.blit(bounce_text, (WIDTH // 2 - bounce_text.get_width() // 2, 150))

    # Add watermark text
    watermark_font = pygame.font.SysFont(None, 36)
    watermark_texts = [
        watermark_font.render("yt:@jbbm_motions", True, GREY),
        watermark_font.render("tiktok:@jbbm_motions", True, GREY),
        watermark_font.render("subscribe for more!", True, GREY)
    ]
    for idx, text in enumerate(watermark_texts):
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 1000 + idx * 30))

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
final_audio.export(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_33\simulation_sound.mp3', format="mp3")

# Close the MIDI output
midi_out.close()
pygame.midi.quit()
pygame.quit()

# Combine video and audio
video_clip = VideoFileClip(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_33\simulation.mp4')
audio_clip = AudioFileClip(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_33\simulation_sound.mp3')

# Trim the audio clip to match the duration of the video clip
audio_clip = audio_clip.subclip(0, video_clip.duration)

final_clip = video_clip.set_audio(audio_clip)
final_clip.write_videofile(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_33\final_output.mp4', codec="libx264")

print(f"Simulation finished with {len(balls)} balls.")
