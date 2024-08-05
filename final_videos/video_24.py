import pygame
import random
import time
import imageio
from pydub import AudioSegment
import os
import io

# Video number
number = 24

# Directory path
video_dir = rf'C:\Users\jmask\OneDrive\Pulpit\videos\video_{number}'
if not os.path.exists(video_dir):
    os.makedirs(video_dir)

# Load MP3 file
music_path = r'C:\Users\jmask\Downloads\09 All Star.mp3'
music = AudioSegment.from_mp3(music_path)

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Create Pygame window
WIDTH, HEIGHT = 720, 1280
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ball with Trailing Effect and Walls")

# Constants
FPS, MAX_SPEED, TRAIL_LENGTH, GRAVITY = 60, 5, 20, 0.3
BLACK, WHITE = (0, 0, 0), (255, 255, 255)
GREY = (50, 50, 50)

# Ball settings
BALL_RADIUS = 100  # Increased size of the starting ball
MIN_BALL_RADIUS = 5
SHRINK_AMOUNT = 0.98


class Ball:
    def __init__(self, position, velocity, radius):
        self.position = position
        self.velocity = velocity
        self.radius = radius
        self.collision_points = []
        self.colors = []
        self.bounce_count = 0

    def move(self):
        # Apply gravity to the vertical velocity
        self.velocity[1] += GRAVITY

        for i in range(2):
            self.position[i] += self.velocity[i]

        # Bounce off the screen edges
        if self.position[0] - self.radius <= 0 or self.position[0] + self.radius >= WIDTH:
            self.velocity[0] *= -1
        if self.position[1] - self.radius <= 0 or self.position[1] + self.radius >= HEIGHT:
            self.velocity[1] *= -1

        # Bounce off the walls
        left_wall_points, right_wall_points = get_wall_points()
        if self.bounce_off_walls(left_wall_points) or self.bounce_off_walls(right_wall_points):
            self.bounce_effect()

    def bounce_off_walls(self, wall_points):
        collision = False
        for i in range(len(wall_points)):
            p1 = wall_points[i]
            p2 = wall_points[(i + 1) % len(wall_points)]
            if self.line_circle_collision(p1, p2):
                # Reflect the ball's velocity based on the wall's normal
                normal = self.get_normal(p1, p2)
                dot = self.velocity[0] * normal[0] + self.velocity[1] * normal[1]
                self.velocity[0] -= 2 * dot * normal[0]
                self.velocity[1] -= 2 * dot * normal[1]
                collision = True
                collision_point = self.get_collision_point(p1, p2)
                self.collision_points.append(collision_point)
                self.colors.append(self.get_random_color())
                break
        return collision

    def line_circle_collision(self, p1, p2):
        # Line segment (p1, p2) to circle collision detection
        cx, cy = self.position
        r = self.radius

        px1, py1 = p1
        px2, py2 = p2

        dx, dy = px2 - px1, py2 - py1
        fx, fy = px1 - cx, py1 - cy

        a = dx * dx + dy * dy
        b = 2 * (fx * dx + fy * dy)
        c = fx * fx + fy * fy - r * r

        discriminant = b * b - 4 * a * c
        if discriminant >= 0:
            discriminant = discriminant ** 0.5

            t1 = (-b - discriminant) / (2 * a)
            t2 = (-b + discriminant) / (2 * a)

            if 0 <= t1 <= 1 or 0 <= t2 <= 1:
                return True

        return False

    def get_normal(self, p1, p2):
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        length = (dx ** 2 + dy ** 2) ** 0.5
        if length == 0:
            return 0, 0
        return -dy / length, dx / length

    def get_collision_point(self, p1, p2):
        # Find the exact point of collision on the wall
        cx, cy = self.position
        r = self.radius

        px1, py1 = p1
        px2, py2 = p2

        dx, dy = px2 - px1, py2 - py1
        fx, fy = px1 - cx, py1 - cy

        a = dx * dx + dy * dy
        b = 2 * (fx * dx + fy * dy)
        c = fx * fx + fy * fy - r * r

        discriminant = b * b - 4 * a * c
        if discriminant >= 0:
            discriminant = discriminant ** 0.5

            t1 = (-b - discriminant) / (2 * a)
            t2 = (-b + discriminant) / (2 * a)

            if 0 <= t1 <= 1:
                collision_x = px1 + t1 * dx
                collision_y = py1 + t1 * dy
                return (collision_x, collision_y)
            if 0 <= t2 <= 1:
                collision_x = px1 + t2 * dx
                collision_y = py1 + t2 * dy
                return (collision_x, collision_y)

        return (cx, cy)

    def get_random_color(self):
        return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

    def bounce_effect(self):
        global audio_segments
        self.radius = max(self.radius * SHRINK_AMOUNT, MIN_BALL_RADIUS)
        play_music_segment(self.bounce_count * 0.25)
        self.bounce_count += 1

    def draw(self, screen):
        # Draw lines from collision points to the center of the ball
        for point, color in zip(self.collision_points, self.colors):
            pygame.draw.line(screen, color, point, self.position, 2)
        pygame.draw.circle(screen, WHITE, (int(self.position[0]), int(self.position[1])), self.radius)


def play_music_segment(start_time, duration=0.25):
    segment = music[int(start_time * 1000):int(start_time * 1000 + duration * 1000)]
    audio_segments.append((segment, time.time()))

    with io.BytesIO() as f:
        segment.export(f, format="wav")
        f.seek(0)
        pygame.mixer.Sound(f).play()


def get_wall_points():
    left_wall_points = [(0, HEIGHT - 600), (0, HEIGHT - 500), (330, 1000), (330, 900)]
    right_wall_points = [(WIDTH, HEIGHT - 600), (WIDTH, HEIGHT - 500), (WIDTH - 330, 1000), (WIDTH - 330, 900)]
    return left_wall_points, right_wall_points


# Create the ball
ball = Ball([WIDTH // 2, 100], [random.choice([-MAX_SPEED, MAX_SPEED]), random.choice([-MAX_SPEED, MAX_SPEED])],
            BALL_RADIUS)

game_over, show_final_message, end_message_start_time = False, False, None
audio_segments = []

font, large_font = pygame.font.SysFont(None, 48), pygame.font.SysFont(None, 64)
video_writer = imageio.get_writer(rf'{video_dir}\{number}_ball_in_walls_sound.mp4', fps=FPS)
running, clock, start_time = True, pygame.time.Clock(), time.time()


def draw_walls():
    left_wall_points, right_wall_points = get_wall_points()
    pygame.draw.polygon(screen, WHITE, left_wall_points)
    pygame.draw.polygon(screen, WHITE, right_wall_points)
    return left_wall_points, right_wall_points


while running:
    clock.tick(FPS)

    if not game_over:
        ball.move()

    screen.fill(BLACK)
    if not game_over:
        title_text = font.render("CAN IT GET THROUGH?", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 100))

        if ball.position[1] >= HEIGHT - 100 and not show_final_message:
            end_message_start_time = time.time()
            show_final_message = True

        draw_walls()
        ball.draw(screen)

        if show_final_message:
            game_over_texts = [
                large_font.render("LIKE", True, WHITE),
                large_font.render("FOLLOW", True, WHITE),
                large_font.render("SUBSCRIBE", True, WHITE),
                large_font.render("COMMENT WHAT TO DO NEXT", True, WHITE)
            ]
            for idx, text in enumerate(game_over_texts):
                screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 300 + 100 * idx))
            if time.time() - end_message_start_time >= 3:
                game_over = True

        # Add watermark text
        watermark_font = pygame.font.SysFont(None, 36)
        watermark_texts = [
            watermark_font.render("yt:@jbbm_motions", True, GREY),
            watermark_font.render("tiktok:@jbbm_motions", True, GREY),
            watermark_font.render("subscribe for more!", True, GREY)
        ]
        for idx, text in enumerate(watermark_texts):
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 175 + idx * 30))
    else:
        running = False

    frame = pygame.surfarray.array3d(screen).transpose([1, 0, 2])
    video_writer.append_data(frame)
    pygame.display.flip()

video_writer.close()
pygame.quit()
print("Video with sound saved successfully!")
