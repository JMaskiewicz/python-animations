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
import colorsys

# Video number
number = 14

# Directory path
video_dir = rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}'
if not os.path.exists(video_dir):
    os.makedirs(video_dir)

# Initialize Pygame and Pygame MIDI
pygame.init()
pygame.midi.init()
midi_out = pygame.midi.Output(0)
midi_out.set_instrument(0)  # Piano

# Load MIDI file
midi_file = mido.MidiFile(r'C:\Users\jmask\Downloads\rush_e_real.mid')
left_hand_notes, right_hand_notes = [], []
for track in midi_file.tracks:
    for msg in track:
        if not msg.is_meta and msg.type == 'note_on':
            if msg.channel == 0:
                left_hand_notes.append(msg.note)
            elif msg.channel == 1:
                right_hand_notes.append(msg.note)

# Create Pygame window
WIDTH, HEIGHT = 720, 1280
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bouncing Balls with Trails and Merging")

# Constants
FPS = 60
BALL_RADIUS = 20
MAX_BALLS = 20
GRAVITY = 0.001
BLACK, WHITE = (0, 0, 0), (255, 255, 255)

# Global trail list
global_trails = []

class Ball:
    def __init__(self, x, y, radius):
        self.pos = [x, y]
        self.radius = radius
        self.speed = [random.choice([-5, 5]), random.choice([-5, 5])]
        self.hue = random.random()

    def move(self):
        self.speed[1] += GRAVITY
        self.pos[0] += self.speed[0]
        self.pos[1] += self.speed[1]
        global_trails.append((tuple(self.pos), self.radius, self.hue, time.time()))

        if self.pos[0] <= self.radius or self.pos[0] >= WIDTH - self.radius:
            self.speed[0] = -self.speed[0]
            self.play_piano_notes()
        if self.pos[1] <= self.radius or self.pos[1] >= HEIGHT - self.radius:
            self.speed[1] = -self.speed[1]
            self.play_piano_notes()

    def draw_ball(self, screen):
        pygame.draw.circle(screen, WHITE, self.pos, self.radius)

    def play_piano_notes(self):
        global left_hand_index, right_hand_play_count
        if right_hand_notes:
            threading.Thread(target=play_note_thread, args=(random.choice(right_hand_notes),)).start()
        right_hand_play_count += 1
        if right_hand_play_count % 2 == 0 and left_hand_notes:
            left_note = left_hand_notes[left_hand_index]
            threading.Thread(target=play_note_thread, args=(left_note,)).start()
            left_hand_index = (left_hand_index + 1) % len(left_hand_notes)


def merge_balls(ball1, ball2):
    new_radius = math.sqrt(ball1.radius ** 2 + ball2.radius ** 2)
    new_ball = Ball((ball1.pos[0] + ball2.pos[0]) // 2, (ball1.pos[1] + ball2.pos[1]) // 2, new_radius)

    # Set a fixed speed for new ball to ensure speed is independent of size
    new_ball.speed = [
        (ball1.speed[0] + ball2.speed[0]) / 2,
        (ball1.speed[1] + ball2.speed[1]) / 2
    ]

    return new_ball


def play_note_thread(note, duration=0.1):
    midi_out.note_on(note, 127)
    note_sound = Sine(note * 8).to_audio_segment(duration=int(duration * 1000))
    audio_segments.append((note_sound, time.time()))
    time.sleep(duration)
    midi_out.note_off(note, 127)


balls = [Ball(random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50), BALL_RADIUS) for _ in range(MAX_BALLS)]
left_hand_index, right_hand_play_count = 0, 0
audio_segments = []
running = True
clock = pygame.time.Clock()
video_writer = imageio.get_writer(rf'{video_dir}\{number}_bouncing_balls.mp4', fps=FPS)
start_time = time.time()

font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 64)
game_over = False
check = 0

while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BLACK)

    for ball in balls:
        ball.move()

    # Sort trails by their timestamp to draw the newest trails last
    global_trails.sort(key=lambda x: x[3])

    # Draw all trails in sorted order
    for pos, radius, hue, _ in global_trails:
        hue_offset = (radius * 0.05) % 1.0
        hue = (hue + hue_offset) % 1.0
        rgb_color = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
        pygame.draw.circle(screen, color, pos, radius)

    # Draw balls on top of trails
    for ball in balls:
        ball.draw_ball(screen)

    merged = []
    i = 0
    while i < len(balls):
        j = i + 1
        while j < len(balls):
            dist = math.hypot(balls[i].pos[0] - balls[j].pos[0], balls[i].pos[1] - balls[j].pos[1])
            if dist <= balls[i].radius + balls[j].radius:
                merged_ball = merge_balls(balls[i], balls[j])
                merged.append(merged_ball)
                balls.pop(j)
                balls.pop(i)
                i -= 1
                break
            j += 1
        i += 1

    balls.extend(merged)

    if len(balls) == 1 and game_over == True:
        if check == 0:
            end_message_start_time = time.time()
            check = 1

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

    frame = pygame.surfarray.array3d(screen).transpose([1, 0, 2])
    video_writer.append_data(frame)
    pygame.display.flip()

video_writer.close()

final_audio = AudioSegment.silent(duration=0)
for segment, timestamp in audio_segments:
    silence_duration = (timestamp - start_time) * 1000
    final_audio += AudioSegment.silent(duration=silence_duration - len(final_audio)) + segment
final_audio = final_audio[:int((time.time() - start_time) * 1000)]
final_audio.export(rf'{video_dir}\{number}_bouncing_balls_sound.mp3', format="mp3")

midi_out.close()
pygame.midi.quit()
pygame.quit()

video_clip = VideoFileClip(rf'{video_dir}\{number}_bouncing_balls.mp4')
audio_clip = AudioFileClip(rf'{video_dir}\{number}_bouncing_balls_sound.mp3')
final_clip = video_clip.set_audio(audio_clip)
final_clip.write_videofile(rf'{video_dir}\{number}_final_output.mp4', codec="libx264")
print("Video with sound saved successfully!")
