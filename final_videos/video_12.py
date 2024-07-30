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
number = 12

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
pygame.display.set_caption("Ball with Trailing Effect and Dynamic Polygon")

# Constants
FPS, MAX_SPEED, GRAVITY, ROTATION_SPEED = 60, 5, 0.05, 0.01
BLACK, WHITE = (0, 0, 0), (255, 255, 255)

# Ball settings
BALL_RADIUS = 50
ball_pos = [WIDTH // 2, HEIGHT // 2]
ball_speed = [random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])]

class Polygon:
    def __init__(self, radius, num_sides=100):
        self.radius, self.num_sides = radius, num_sides
        self.holes = [False] * num_sides
        self.rotation_angle, self.hue = 0, 0

    def draw(self, screen):
        center = (WIDTH // 2, HEIGHT // 2)
        angle_step = 2 * math.pi / self.num_sides
        points = [(center[0] + self.radius * math.cos(i * angle_step + self.rotation_angle),
                   center[1] + self.radius * math.sin(i * angle_step + self.rotation_angle)) for i in range(self.num_sides)]
        for i in range(self.num_sides):
            if not self.holes[i]:
                start, end = points[i], points[(i + 1) % self.num_sides]
                self.hue = (self.hue + 0.000025) % 1.0
                rgb_color = colorsys.hsv_to_rgb(self.hue, 1.0, 1.0)
                color = (int(rgb_color[0] * 255), int(rgb_color[1] * 255), int(rgb_color[2] * 255))
                pygame.draw.line(screen, color, start, end, 10)

    def get_edges(self):
        center = (WIDTH // 2, HEIGHT // 2)
        angle_step = 2 * math.pi / self.num_sides
        points = [(center[0] + self.radius * math.cos(i * angle_step + self.rotation_angle),
                   center[1] + self.radius * math.sin(i * angle_step + self.rotation_angle)) for i in range(self.num_sides)]
        return [(points[i], points[(i + 1) % len(points)]) for i in range(len(points))]

    def contains_point(self, point):
        return math.hypot(point[0] - WIDTH // 2, point[1] - HEIGHT // 2) <= self.radius

polygon = Polygon(350)
left_hand_index, right_hand_play_count, bounce_count = 0, 0, 0
game_over, show_end_message, end_message_start_time = False, False, None
audio_segments = []

def randomize_direction(ball_speed):
    angle = random.uniform(-math.pi / 6, math.pi / 6)
    speed = math.hypot(*ball_speed)
    new_angle = math.atan2(ball_speed[1], ball_speed[0]) + angle
    return [speed * math.cos(new_angle), speed * math.sin(new_angle)]

def play_note_thread(note, duration=0.1):
    midi_out.note_on(note, 127)
    note_sound = Sine(note * 8).to_audio_segment(duration=int(duration * 1000))
    audio_segments.append((note_sound, time.time()))
    time.sleep(duration)
    midi_out.note_off(note, 127)

def play_piano_notes():
    global left_hand_index, right_hand_play_count
    if right_hand_notes:
        threading.Thread(target=play_note_thread, args=(random.choice(right_hand_notes),)).start()
    right_hand_play_count += 1
    if right_hand_play_count % 2 == 0 and left_hand_notes:
        left_note = left_hand_notes[left_hand_index]
        threading.Thread(target=play_note_thread, args=(left_note,)).start()
        left_hand_index = (left_hand_index + 1) % len(left_hand_notes)

def reflect_velocity(velocity, normal):
    dot_product = velocity[0] * normal[0] + velocity[1] * normal[1]
    return [velocity[0] - 2 * dot_product * normal[0], velocity[1] - 2 * dot_product * normal[1]]

def enhanced_collision_detection(ball_pos, edge):
    line_start, line_end = edge
    line_vec = [line_end[0] - line_start[0], line_end[1] - line_start[1]]
    ball_vec = [ball_pos[0] - line_start[0], ball_pos[1] - line_start[1]]
    line_len = math.hypot(*line_vec)
    line_unitvec = [line_vec[0] / line_len, line_vec[1] / line_len]
    proj_len = ball_vec[0] * line_unitvec[0] + ball_vec[1] * line_unitvec[1]
    closest_point = [line_start[0] + proj_len * line_unitvec[0], line_start[1] + proj_len * line_unitvec[1]]
    if proj_len < 0 or proj_len > line_len:
        return False
    if not point_on_segment(closest_point[0], closest_point[1], line_start[0], line_start[1], line_end[0], line_end[1]):
        return False
    return math.hypot(closest_point[0] - ball_pos[0], closest_point[1] - ball_pos[1]) <= BALL_RADIUS

font, large_font = pygame.font.SysFont(None, 48), pygame.font.SysFont(None, 64)
video_writer = imageio.get_writer(rf'{video_dir}\{number}_ball_in_lines_sound.mp4', fps=FPS)
running, clock, start_time = True, pygame.time.Clock(), time.time()

def point_on_segment(px, py, ax, ay, bx, by):
    # Calculate the cross product to determine if point p is on line segment ab
    cross_product = (py - ay) * (bx - ax) - (px - ax) * (by - ay)
    if abs(cross_product) > 1e-6:
        return False  # Not on the line

    # Check if the point is in the bounding rectangle
    dot_product = (px - ax) * (bx - ax) + (py - ay) * (by - ay)
    if dot_product < 0:
        return False  # Beyond point a

    squared_length_ba = (bx - ax) * (bx - ax) + (by - ay) * (by - ay)
    if dot_product > squared_length_ba:
        return False  # Beyond point b

    return True  # The point is on the segment

def ball_outside_polygon(ball_pos, ball_radius, polygon):
    center = (WIDTH // 2, HEIGHT // 2)
    angle_step = 2 * math.pi / 12  # Check with 12 points around the circumference
    for i in range(12):
        angle = i * angle_step
        point_x = ball_pos[0] + ball_radius * math.cos(angle)
        point_y = ball_pos[1] + ball_radius * math.sin(angle)
        if polygon.contains_point((point_x, point_y)):
            return False
    return True

while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    if not game_over:
        ball_speed[1] += GRAVITY
        ball_pos = [ball_pos[0] + ball_speed[0], ball_pos[1] + ball_speed[1]]
        if ball_pos[0] <= BALL_RADIUS or ball_pos[0] >= WIDTH - BALL_RADIUS:
            ball_speed[0] = -ball_speed[0]
            ball_speed = randomize_direction(ball_speed)
            play_piano_notes()
            if polygon.contains_point(ball_pos):
                bounce_count += 1
                ball_speed[0] *= 1.02
                ball_speed[1] *= 1.02
        if ball_pos[1] <= BALL_RADIUS or ball_pos[1] >= HEIGHT - BALL_RADIUS:
            ball_speed[1] = -ball_speed[1]
            ball_speed = randomize_direction(ball_speed)
            play_piano_notes()
            if polygon.contains_point(ball_pos):
                bounce_count += 1
                ball_speed[0] *= 1.02
                ball_speed[1] *= 1.02
        edges = polygon.get_edges()
        for i, edge in enumerate(edges):
            if not polygon.holes[i] and enhanced_collision_detection(ball_pos, edge):
                normal = [-(edge[1][1] - edge[0][1]), edge[1][0] - edge[0][0]]
                normal_mag = math.hypot(*normal)
                normal = [normal[0] / normal_mag, normal[1] / normal_mag]
                ball_speed = reflect_velocity(ball_speed, normal)
                polygon.holes[i] = True
                play_piano_notes()
                if polygon.contains_point(ball_pos):
                    bounce_count += 1
                    ball_speed[0] *= 1.02
                    ball_speed[1] *= 1.02
                break
        if ball_outside_polygon(ball_pos, BALL_RADIUS, polygon) and not show_end_message:
            show_end_message, end_message_start_time = True, time.time()
        polygon.rotation_angle += ROTATION_SPEED

    screen.fill(BLACK)
    if not game_over:
        title_text = font.render("How many bounces it need to escape?", True, WHITE)
        bounce_text = font.render(f"BOUNCES: {bounce_count}", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))
        screen.blit(bounce_text, (WIDTH // 2 - bounce_text.get_width() // 2, 200))
        polygon.draw(screen)
        pygame.draw.circle(screen, WHITE, ball_pos, BALL_RADIUS)
        if show_end_message:
            game_over_texts = [
                large_font.render("LIKE", True, WHITE, BLACK),
                large_font.render("COMMENT", True, WHITE, BLACK),
                large_font.render("SUBSCRIBE", True, WHITE, BLACK)
            ]
            for idx, text in enumerate(game_over_texts):
                screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 150 + 100 * idx))
            if time.time() - end_message_start_time >= 5:
                game_over = True
    else:
        running = False

    frame = pygame.surfarray.array3d(screen).transpose([1, 0, 2])
    video_writer.append_data(frame)
    pygame.display.flip()

video_writer.close()
final_audio = AudioSegment.silent(duration=0)
for segment, timestamp in audio_segments:
    silence_duration = (timestamp - start_time) * 1000
    final_audio += AudioSegment.silent(duration=silence_duration - len(final_audio)) + segment
final_audio = final_audio[:int((time.time() - start_time) * 1000)]
final_audio.export(rf'{video_dir}\{number}_ball_in_lines_sound.mp3', format="mp3")
midi_out.close()
pygame.midi.quit()
pygame.quit()
video_clip = VideoFileClip(rf'{video_dir}\{number}_ball_in_lines_sound.mp4')
audio_clip = AudioFileClip(rf'{video_dir}\{number}_ball_in_lines_sound.mp3')
final_clip = video_clip.set_audio(audio_clip)
final_clip.write_videofile(rf'{video_dir}\{number}_final_output.mp4', codec="libx264")
print("Video with sound saved successfully!")
