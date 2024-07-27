import pygame
import pygame.midi
import random
import time
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

# Create Pygame window
WIDTH, HEIGHT = 720, 1280
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rock Paper Scissors Animation")

# Initialize font
font = pygame.font.SysFont(None, 72)
large_font = pygame.font.SysFont(None, 64)

# Constants
FPS = 60
NUM_OBJECTS = 20
MAX_SPEED = 5

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Object Types
ROCK = 'rock'
PAPER = 'paper'
SCISSORS = 'scissors'
types = [ROCK, PAPER, SCISSORS]

# Emojis
ROCK_EMOJI = "🪨"
PAPER_EMOJI = "📄"
SCISSORS_EMOJI = "✂️"

# Load font
font = pygame.font.SysFont("Segoe UI Emoji", 40)
large_font = pygame.font.SysFont(None, 68)

# Setup video writer
video_writer = imageio.get_writer(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_7\7_rock_paper_scissors.mp4', fps=FPS)

# Create a list to store audio segments
audio_segments = []

class RPSObject:
    def __init__(self, obj_type):
        self.type = obj_type
        self.radius = 10
        self.x = random.randint(self.radius, WIDTH - self.radius)
        self.y = random.randint(self.radius, HEIGHT - self.radius)
        self.dx = random.uniform(-MAX_SPEED, MAX_SPEED)
        self.dy = random.uniform(-MAX_SPEED, MAX_SPEED)

    def move(self):
        self.dx += random.uniform(-0.5, 0.5)
        self.dy += random.uniform(-0.5, 0.5)
        self.dx = max(min(self.dx, MAX_SPEED), -MAX_SPEED)
        self.dy = max(min(self.dy, MAX_SPEED), -MAX_SPEED)
        self.x += self.dx
        self.y += self.dy
        if self.x <= self.radius:
            self.x = self.radius
            self.dx *= -1
        elif self.x >= WIDTH - self.radius:
            self.x = WIDTH - self.radius
            self.dx *= -1
        if self.y <= self.radius:
            self.y = self.radius
            self.dy *= -1
        elif self.y >= HEIGHT - self.radius:
            self.y = HEIGHT - self.radius
            self.dy *= -1

    def draw(self, screen):
        if self.type == ROCK:
            text_surface = font.render(ROCK_EMOJI, True, WHITE)
        elif self.type == PAPER:
            text_surface = font.render(PAPER_EMOJI, True, WHITE)
        elif self.type == SCISSORS:
            text_surface = font.render(SCISSORS_EMOJI, True, WHITE)
        screen.blit(text_surface, (self.x - self.radius, self.y - self.radius))

    def check_collision(self, other):
        dist = ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5
        if dist < self.radius + other.radius:
            self.resolve_collision(other, dist)
            self.transform(other)

    def resolve_collision(self, other, dist):
        overlap = 0.5 * (self.radius + other.radius - dist)
        self.x += overlap * (self.x - other.x) / dist
        self.y += overlap * (self.y - other.y) / dist
        other.x -= overlap * (self.x - other.x) / dist
        other.y -= overlap * (self.y - other.y) / dist
        self.bounce(other)

    def bounce(self, other):
        self.dx, other.dx = other.dx, self.dx
        self.dy, other.dy = other.dy, self.dy

    def transform(self, other):
        if self.type == ROCK and other.type == SCISSORS:
            other.type = ROCK
        elif self.type == SCISSORS and other.type == PAPER:
            other.type = SCISSORS
        elif self.type == PAPER and other.type == ROCK:
            other.type = PAPER
        elif self.type == SCISSORS and other.type == ROCK:
            self.type = ROCK
        elif self.type == PAPER and other.type == SCISSORS:
            self.type = SCISSORS
        elif self.type == ROCK and other.type == PAPER:
            self.type = PAPER
        self.play_note()

    def play_note(self):
        note = random.randint(60, 72)
        threading.Thread(target=play_note_thread, args=(note,)).start()

def play_note_thread(note, duration=0.1):
    midi_out.note_on(note, 127)
    note_sound = Sine(note * 8).to_audio_segment(duration=int(duration * 1000))
    audio_segments.append((note_sound, time.time()))
    time.sleep(duration)
    midi_out.note_off(note, 127)

# Initialize objects
objects = ([RPSObject(ROCK) for _ in range(NUM_OBJECTS)] +
           [RPSObject(PAPER) for _ in range(NUM_OBJECTS)] +
           [RPSObject(SCISSORS) for _ in range(NUM_OBJECTS)])

# Main loop
running = True
clock = pygame.time.Clock()
start_time = time.time()
game_over = False
show_end_message = False
end_message_start_time = None

while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BLACK)

    # Draw title and bounce counter
    title_text = font.render("ROCK PAPER SCISSORS?", True, WHITE)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 200))

    for obj in objects:
        obj.move()
        obj.draw(screen)
        for other_obj in objects:
            if obj != other_obj:
                obj.check_collision(other_obj)

    if not game_over or show_end_message:
        pygame.display.flip()

    frame = pygame.surfarray.array3d(screen)
    frame = frame.transpose([1, 0, 2])
    video_writer.append_data(frame)

    first_type = objects[0].type
    if all(obj.type == first_type for obj in objects):
        show_end_message = True
        if end_message_start_time is None:
            end_message_start_time = time.time()

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

        pygame.display.flip()  # Ensure the display updates to show the end message

        # Check if the 5-second period is over
        if time.time() - end_message_start_time >= 5:
            game_over = True

    if game_over:
        running = False

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
    silence_duration = (timestamp - start_time) * 1000
    final_audio += AudioSegment.silent(duration=max(0, silence_duration - len(final_audio)))
    final_audio += segment

final_audio = final_audio[:int(game_duration * 1000)]
final_audio.export(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_7\7_rock_paper_scissors.mp3', format="mp3")

# Close the MIDI output
midi_out.close()
pygame.midi.quit()
pygame.quit()

# Combine video and audio
video_clip = VideoFileClip(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_7\7_rock_paper_scissors.mp4')
audio_clip = AudioFileClip(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_7\7_rock_paper_scissors.mp3')
final_clip = video_clip.set_audio(audio_clip)
final_clip.write_videofile(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_7\7_final_output_rps.mp4', codec="libx264")

print("Rock-Paper-Scissors video with sound saved successfully!")
