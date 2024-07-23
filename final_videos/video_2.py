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
NUM_OBJECTS = 20
MAX_SPEED = 5  # Maximum speed of objects
MAX_RADIUS = 50  # Maximum radius of objects

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Create Pygame window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("WHICH COLOUR WILL WIN?")


# Object class
class RPSObject:
    def __init__(self, number):
        self.number = number
        self.radius = 15
        self.increment_factor = 1.15
        self.x = random.randint(self.radius, WIDTH - self.radius)
        self.y = random.randint(self.radius, HEIGHT - self.radius)
        self.dx = random.uniform(-MAX_SPEED, MAX_SPEED)
        self.dy = random.uniform(-MAX_SPEED, MAX_SPEED)
        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    def move(self):
        # Apply random motion component
        self.dx += random.uniform(-0.5, 0.5)
        self.dy += random.uniform(-0.5, 0.5)

        # Limit speed to max speed
        self.dx = max(min(self.dx, MAX_SPEED), -MAX_SPEED)
        self.dy = max(min(self.dy, MAX_SPEED), -MAX_SPEED)

        self.x += self.dx
        self.y += self.dy

        # Wall collision handling
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
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)

    def check_collision(self, other):
        dist = ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
        if dist < self.radius + other.radius:
            self.resolve_collision(other, dist)
            self.transform(other)
            play_piano_notes()  # Play sound on collision

    def resolve_collision(self, other, dist):
        # Calculate overlap
        overlap = 0.5 * (self.radius + other.radius - dist)
        # Displace current object
        self.x += overlap * (self.x - other.x) / dist
        self.y += overlap * (self.y - other.y) / dist
        # Displace other object
        other.x -= overlap * (self.x - other.x) / dist
        other.y -= overlap * (self.y - other.y) / dist
        # Bounce
        self.bounce(other)

    def bounce(self, other):
        self.dx, other.dx = other.dx, self.dx
        self.dy, other.dy = other.dy, self.dy

    def transform(self, other):
        if self.color != other.color:
            if random.random() < 2 * other.radius / (2 * other.radius + self.radius):
                other.color = self.color
                other.number = self.number
                other.radius = min(other.radius * self.increment_factor, MAX_RADIUS)
            else:
                self.color = other.color
                self.radius = min(self.radius * self.increment_factor, MAX_RADIUS)
                self.number = other.number


# Initialize objects
objects = [RPSObject(i) for i in range(NUM_OBJECTS)]

# Initialize font
font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 64)

# Setup video writer
video_writer = imageio.get_writer(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_2\2_rps_simulation.mp4', fps=FPS)

# Create a list to store audio segments
audio_segments = []

# Main loop
running = True
clock = pygame.time.Clock()
start_time = time.time()
end_message_start_time = None
show_end_message = False
game_over = False

NOTE_OFF_EVENT = pygame.USEREVENT + 1

left_hand_index = 0
right_hand_play_count = 0


def midi_note_to_freq(note):
    """ Convert MIDI note to frequency. """
    return 420.0 * (2.0 ** ((note - 69) / 12.0))


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


# Adjust the initialization of show_end_message
show_end_message = False

# Main game loop
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BLACK)

    # Draw title and bounce counter
    title_text = font.render("WHICH COLOUR WILL WIN?", True, WHITE)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 50))

    for obj in objects:
        obj.move()
        obj.draw(screen)
        for other_obj in objects:
            if obj != other_obj:
                obj.check_collision(other_obj)

    pygame.display.flip()

    # Check if all objects are of the same type
    first_type = objects[0].number
    if all(obj.number == first_type for obj in objects):
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
    silence_duration = (timestamp - start_time) * 1000  # Convert to milliseconds
    final_audio += AudioSegment.silent(duration=silence_duration - len(final_audio))
    final_audio += segment

# Ensure the final audio is at least as long as the game duration
final_audio += AudioSegment.silent(duration=(game_duration * 1000) - len(final_audio))

# Save the audio to a file
final_audio.export(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_2\2_rps_simulation_sound.mp3', format="mp3")

# Close the MIDI output
midi_out.close()
pygame.midi.quit()
pygame.quit()

# Combine video and audio
video_clip = VideoFileClip(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_2\2_rps_simulation.mp4')
audio_clip = AudioFileClip(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_2\2_rps_simulation_sound.mp3')

# Trim the audio clip to match the duration of the video clip
audio_clip = audio_clip.subclip(0, video_clip.duration)

final_clip = video_clip.set_audio(audio_clip)
final_clip.write_videofile(r'C:\Users\jmask\OneDrive\Pulpit\videos\video_2\2_final_output.mp4', codec="libx264")

print("Video with sound saved successfully!")
