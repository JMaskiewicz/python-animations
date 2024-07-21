import pygame
import pygame.midi
import random
import math
import time
import mido
import threading

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
WIDTH, HEIGHT = 600, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball with Trailing Effect and Dynamic Circles")

# Constants
FPS = 60
MAX_SPEED = 1  # Maximum initial speed of ball
TRAIL_LENGTH = 30  # Number of trail segments
GRAVITY = 0.2  # Gravity effect
CIRCLE_SHRINK_RATE = 0.5  # Rate at which circles shrink
NEW_CIRCLE_INTERVAL = 0.8  # Initial time interval in seconds to add new circle
MIN_CIRCLE_RADIUS = 5  # Minimum circle radius before disappearing
SPEED_INCREASE_FACTOR = 1.025  # Factor to increase speed after each bounce
CIRCLE_CREATION_ACCELERATION = 0.999  # Factor to decrease interval for circle creation after each bounce

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CIRCLE_COLORS = [(255, 105, 180), (255, 182, 193), (255, 240, 245), (255, 228, 225), (255, 192, 203)]
TRAIL_COLORS = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 127, 255), (0, 0, 255), (139, 0, 255)]

# Ball settings
BALL_RADIUS = 15
ball_pos = [WIDTH // 2, HEIGHT // 2]
ball_speed = [random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])]

# Circle settings
class Circle:
    def __init__(self, radius, color):
        self.radius = radius
        self.color = color

    def draw(self, screen):
        if self.radius > 0:
            pygame.draw.circle(screen, self.color, (WIDTH // 2, HEIGHT // 2), self.radius, 5)

    def update(self):
        self.radius -= CIRCLE_SHRINK_RATE

circles = [Circle(radius, random.choice(CIRCLE_COLORS)) for radius in range(300, 50, -50)][:4]  # Initialize with 4 circles

# Trail settings
trail_positions = []

left_hand_index = 0
right_hand_play_count = 0

NOTE_OFF_EVENT = pygame.USEREVENT + 1

def randomize_direction(ball_speed):
    angle = random.uniform(-math.pi / 6, math.pi / 6)  # Random angle between -30 and 30 degrees
    speed = math.hypot(ball_speed[0], ball_speed[1])  # Current speed magnitude
    new_angle = math.atan2(ball_speed[1], ball_speed[0]) + angle
    ball_speed[0] = speed * math.cos(new_angle)
    ball_speed[1] = speed * math.sin(new_angle)

def increase_speed(ball_speed):
    ball_speed[0] *= SPEED_INCREASE_FACTOR
    ball_speed[1] *= SPEED_INCREASE_FACTOR

def play_note_thread(note):
    midi_out.note_on(note, 127)
    time.sleep(0.1)  # Play the note for 100 ms
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

# Main game loop
running = True
clock = pygame.time.Clock()
last_circle_add_time = time.time()
no_circle_time = None

while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Update ball position
    ball_speed[1] += GRAVITY
    ball_pos[0] += ball_speed[0]
    ball_pos[1] += ball_speed[1]

    # Ball collision with walls
    if ball_pos[0] <= BALL_RADIUS or ball_pos[0] >= WIDTH - BALL_RADIUS:
        ball_speed[0] = -ball_speed[0]
        randomize_direction(ball_speed)
        play_piano_notes()  # Play piano notes on bounce

    if ball_pos[1] <= BALL_RADIUS or ball_pos[1] >= HEIGHT - BALL_RADIUS:
        ball_speed[1] = -ball_speed[1]
        randomize_direction(ball_speed)
        play_piano_notes()  # Play piano notes on bounce

    # Check collision with circles
    for circle in circles[:]:
        dist = math.hypot(ball_pos[0] - WIDTH // 2, ball_pos[1] - HEIGHT // 2)
        if circle.radius - BALL_RADIUS <= dist <= circle.radius + BALL_RADIUS:
            normal = [(ball_pos[0] - WIDTH // 2) / dist, (ball_pos[1] - HEIGHT // 2) / dist]
            ball_speed = reflect_velocity(ball_speed, normal)
            circles.remove(circle)
            increase_speed(ball_speed)
            NEW_CIRCLE_INTERVAL *= CIRCLE_CREATION_ACCELERATION  # Decrease interval for circle creation
            play_piano_notes()  # Play piano notes on bounce
            break

    # Update circles
    for circle in circles:
        circle.update()
    circles = [circle for circle in circles if circle.radius > MIN_CIRCLE_RADIUS]

    # Add new circle based on current interval if there are circles
    if circles:
        current_time = time.time()
        if current_time - last_circle_add_time >= NEW_CIRCLE_INTERVAL:
            new_circle = Circle(300, random.choice(CIRCLE_COLORS))
            circles.append(new_circle)
            last_circle_add_time = current_time
    else:
        if no_circle_time is None:
            no_circle_time = time.time()
        elif time.time() - no_circle_time >= 5:
            running = False

    # Update trail positions
    trail_positions.append(tuple(ball_pos))
    if len(trail_positions) > TRAIL_LENGTH:
        trail_positions.pop(0)

    # Draw everything
    screen.fill(BLACK)

    # Draw circles
    for circle in circles:
        circle.draw(screen)

    # Draw trail
    for i, pos in enumerate(trail_positions):
        color = TRAIL_COLORS[i % len(TRAIL_COLORS)]
        pygame.draw.circle(screen, color, pos, BALL_RADIUS)

    # Draw ball
    pygame.draw.circle(screen, WHITE, ball_pos, BALL_RADIUS)

    pygame.display.flip()

# Close the MIDI output
midi_out.close()
pygame.midi.quit()
pygame.quit()
