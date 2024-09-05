import pygame
import random
import math
import time
import imageio
from pydub import AudioSegment
import os
import colorsys
import io
import pygame
import math
import random
import colorsys
import time
import io
from pydub import AudioSegment



# Constants
WIDTH, HEIGHT = 720, 1280
INITIAL_BALL_RADIUS = 10
FPS = 60
POLYGON_THICKNESS = 8
ROTATION_SPEED = 0.01  # Slow rotation speed
SUBSTEPS = 10  # Increase this for finer collision checks
BALL_COUNT = 3
SPARK_COUNT = 10  # Number of sparks generated on collision

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Load sound
pop_sound = pygame.mixer.Sound(r'C:\Users\jmask\Downloads\pop-39222.mp3')

# Ball class
class Ball:
    def __init__(self, x, y, radius, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.speed_x = random.choice([-4, -3, -2, 2, 3, 4])
        self.speed_y = random.choice([-4, -3, -2, 2, 3, 4])
        self.alive = True

    def move(self, substeps):
        for _ in range(substeps):
            self.x += self.speed_x / substeps
            self.y += self.speed_y / substeps

            # Check if the ball hits the edge of the screen and mark it as not alive
            if self.x - self.radius < 0 or self.x + self.radius > WIDTH:
                self.alive = False
            if self.y - self.radius < 0 or self.y + self.radius > HEIGHT:
                self.alive = False

    def draw(self, screen):
        if self.alive:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def check_collision_with_polygon(self, rotated_points, gap_indices):
        if not self.alive:
            return
        for i, point in enumerate(rotated_points):
            if i in gap_indices:
                continue

            next_point = rotated_points[(i + 1) % len(rotated_points)]
            if self.is_collision(point, next_point):
                self.resolve_collision(point, next_point)
                break

    def check_collision_with_ball(self, other_ball):
        if not self.alive or not other_ball.alive:
            return False
        dx = other_ball.x - self.x
        dy = other_ball.y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance < self.radius + other_ball.radius:
            self.resolve_ball_collision(other_ball, dx, dy, distance)
            return True
        return False

    def is_collision(self, point, next_point):
        # Calculate the perpendicular distance from the ball center to the edge
        edge_vector = (next_point[0] - point[0], next_point[1] - point[1])
        ball_to_point = (self.x - point[0], self.y - point[1])

        edge_length = math.sqrt(edge_vector[0] ** 2 + edge_vector[1] ** 2)
        edge_unit_vector = (edge_vector[0] / edge_length, edge_vector[1] / edge_length)

        projection = ball_to_point[0] * edge_unit_vector[0] + ball_to_point[1] * edge_unit_vector[1]
        closest_point = (
            point[0] + edge_unit_vector[0] * projection,
            point[1] + edge_unit_vector[1] * projection
        )

        distance_to_edge = math.sqrt((closest_point[0] - self.x) ** 2 + (closest_point[1] - self.y) ** 2)

        if distance_to_edge < self.radius:
            # Check if the closest point is actually on the edge segment
            if projection >= 0 and projection <= edge_length:
                return True
        return False

    def resolve_collision(self, point, next_point):
        pop_sound.play()

        # Reflect the ball's velocity based on the collision with the edge
        edge_vector = (next_point[0] - point[0], next_point[1] - point[1])
        ball_to_point = (self.x - point[0], self.y - point[1])

        edge_length = math.sqrt(edge_vector[0] ** 2 + edge_vector[1] ** 2)
        edge_unit_vector = (edge_vector[0] / edge_length, edge_vector[1] / edge_length)

        projection = ball_to_point[0] * edge_unit_vector[0] + ball_to_point[1] * edge_unit_vector[1]
        closest_point = (
            point[0] + edge_unit_vector[0] * projection,
            point[1] + edge_unit_vector[1] * projection
        )

        collision_normal = (self.x - closest_point[0], self.y - closest_point[1])
        collision_length = math.sqrt(collision_normal[0] ** 2 + collision_normal[1] ** 2)
        collision_normal = (collision_normal[0] / collision_length, collision_normal[1] / collision_length)

        dot_product = self.speed_x * collision_normal[0] + self.speed_y * collision_normal[1]
        self.speed_x -= 2 * dot_product * collision_normal[0]
        self.speed_y -= 2 * dot_product * collision_normal[1]

        # Move the ball out of collision
        overlap_distance = self.radius - collision_length
        self.x += collision_normal[0] * overlap_distance
        self.y += collision_normal[1] * overlap_distance

    def resolve_ball_collision(self, other_ball, dx, dy, distance):
        pop_sound.play()

        # Normal vector
        nx = dx / distance
        ny = dy / distance

        # Tangent vector
        tx = -ny
        ty = nx

        # Dot product tangent
        dpTan1 = self.speed_x * tx + self.speed_y * ty
        dpTan2 = other_ball.speed_x * tx + other_ball.speed_y * ty

        # Dot product normal
        dpNorm1 = self.speed_x * nx + self.speed_y * ny
        dpNorm2 = other_ball.speed_x * nx + other_ball.speed_y * ny

        # Conservation of momentum in 1D
        m1 = (dpNorm1 * (self.radius - other_ball.radius) + 2 * other_ball.radius * dpNorm2) / (self.radius + other_ball.radius)
        m2 = (dpNorm2 * (other_ball.radius - self.radius) + 2 * self.radius * dpNorm1) / (self.radius + other_ball.radius)

        self.speed_x = tx * dpTan1 + nx * m1
        self.speed_y = ty * dpTan1 + ny * m1
        other_ball.speed_x = tx * dpTan2 + nx * m2
        other_ball.speed_y = ty * dpTan2 + ny * m2

        # Separate the balls to avoid overlap
        overlap = 0.5 * (self.radius + other_ball.radius - distance + 1)
        self.x -= overlap * nx
        self.y -= overlap * ny
        other_ball.x += overlap * nx
        other_ball.y += overlap * ny

# Spark class for creating the rainbow sparks when balls collide
class Spark:
    def __init__(self, x, y, vx, vy, color, lifespan=20):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifespan = lifespan

    def move(self):
        self.x += self.vx
        self.y += self.vy
        self.lifespan -= 1

    def draw(self, screen):
        if self.lifespan > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 3)

def create_polygon_with_gap(center, radius, sides, gap_size):
    points = []
    gap_indices = set()
    angle_increment = 2 * math.pi / sides
    gap_start = random.randint(0, sides - gap_size)

    for i in range(sides):
        angle = i * angle_increment
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        points.append((x, y))

        if gap_start <= i < gap_start + gap_size:
            gap_indices.add(i)

    return points, gap_indices

def rotate_polygon(points, center, angle):
    """ Rotate the entire polygon by a given angle around the center. """
    rotated_points = []
    for point in points:
        rotated_point = rotate_point(point, center, angle)
        rotated_points.append(rotated_point)
    return rotated_points

def rotate_point(point, center, angle):
    """ Rotate a point around a center by a given angle. """
    temp_x = point[0] - center[0]
    temp_y = point[1] - center[1]

    # Apply rotation
    rotated_x = temp_x * math.cos(angle) - temp_y * math.sin(angle)
    rotated_y = temp_y * math.cos(angle) + temp_x * math.sin(angle)

    # Translate back
    return (rotated_x + center[0], rotated_y + center[1])

def spawn_balls(center):
    """ Spawns three balls in a small triangle formation at the center. """
    balls = []
    angle_between_balls = math.pi * 2 / BALL_COUNT
    small_radius = INITIAL_BALL_RADIUS * 3  # Distance between balls in the triangle

    for i in range(BALL_COUNT):
        angle = i * angle_between_balls
        x = center[0] + small_radius * math.cos(angle)
        y = center[1] + small_radius * math.sin(angle)
        color = [random.randint(50, 255) for _ in range(3)]
        ball = Ball(x, y, INITIAL_BALL_RADIUS, color)
        balls.append(ball)

    return balls

def main():
    show_end_message = False
    center = (WIDTH // 2, HEIGHT // 2)
    polygon_radius = min(WIDTH, HEIGHT) // 2 - 50
    sides = 1000
    gap_size = sides // 15
    angle_offset = 0
    font, large_font = pygame.font.SysFont(None, 48), pygame.font.SysFont(None, 64)

    points, gap_indices = create_polygon_with_gap(center, polygon_radius, sides, gap_size)
    balls = spawn_balls(center)
    sparks = []
    start_time = time.time()
    hue = 0  # Start hue value
    running = True
    while running:
        current_time = time.time()
        screen.fill(BLACK)

        # Calculate the current color from the hue
        hue = (hue + 1) % 360  # Increment hue, wrap around at 360
        color = colorsys.hsv_to_rgb(hue / 360, 1, 1)  # Convert hue to RGB
        color = tuple(int(c * 255) for c in color)  # Convert to RGB values in range 0-255

        title_text = font.render("ESCAPING BALLS TRIPLE", True, color)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 150))

        # Add watermark text
        watermark_font = pygame.font.SysFont(None, 36)
        watermark_texts = [
            watermark_font.render("yt:@jbbm_motions", True, (40, 40, 40)),
            watermark_font.render("tiktok:@jbbm_motions", True, (40, 40, 40)),
            watermark_font.render("subscribe for more!", True, (40, 40, 40))
        ]
        for idx, text in enumerate(watermark_texts):
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 1050 + idx * 30))

        # Check if 3 seconds have passed to show the end message
        if current_time - start_time > 45 and not show_end_message:
            show_end_message = True
            end_message_start_time = current_time

        # Rotate the polygon
        angle_offset += ROTATION_SPEED
        rotated_points = rotate_polygon(points, center, angle_offset)

        # Draw the polygon with thickness
        for i, point in enumerate(rotated_points):
            next_point = rotated_points[(i + 1) % len(rotated_points)]
            if i not in gap_indices:
                pygame.draw.line(screen, WHITE, point, next_point, POLYGON_THICKNESS)

        # Move and check collision for each ball
        for ball in balls:
            ball.move(SUBSTEPS)
            if not ball.alive:
                # Remove this ball and spawn three new balls at the center
                balls.remove(ball)
                balls.extend(spawn_balls(center))
                break
            ball.check_collision_with_polygon(rotated_points, gap_indices)

            # Check for ball-to-ball collisions
            for other_ball in balls:
                if ball != other_ball and ball.check_collision_with_ball(other_ball):
                    # Create sparks at the collision point
                    collision_x = (ball.x + other_ball.x) / 2
                    collision_y = (ball.y + other_ball.y) / 2
                    for _ in range(SPARK_COUNT):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(1, 4)
                        vx = speed * math.cos(angle)
                        vy = speed * math.sin(angle)
                        color = [random.randint(50, 255) for _ in range(3)]
                        sparks.append(Spark(collision_x, collision_y, vx, vy, color))

            ball.draw(screen)

        # Draw and update sparks
        for spark in sparks[:]:
            spark.move()
            spark.draw(screen)
            if spark.lifespan <= 0:
                sparks.remove(spark)

        # Show the end message and exit after 3 seconds
        if show_end_message:
            game_over_texts = [
                large_font.render("LIKE", True, WHITE),
                large_font.render("FOLLOW", True, WHITE),
                large_font.render("SUBSCRIBE", True, WHITE),
                large_font.render("COMMENT WHAT TO DO NEXT", True, WHITE)
            ]
            for idx, text in enumerate(game_over_texts):
                screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 100 + 100 * idx))

            if current_time - end_message_start_time >= 3:
                running = False  # Stop the game loop after showing the end message for 3 seconds

        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    pygame.quit()

if __name__ == "__main__":
    main()
