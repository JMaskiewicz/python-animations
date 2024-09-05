import pygame
import random
import math
import time
import colorsys
import gc
import numpy as np
from numba import jit

# Constants
WIDTH, HEIGHT = 720, 1280
INITIAL_BALL_RADIUS = 8
FPS = 60
POLYGON_THICKNESS = 8
ROTATION_SPEED = 0.02  # Slow rotation speed
SUBSTEPS = 1  # Increase this for finer collision checks
BALL_COUNT = 2
SPARK_COUNT = 4  # Number of sparks generated on collision
MAX_BALLS = 1000  # Limit the number of active balls
MAX_SPARKS = 100  # Limit the number of active sparks

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
clock = pygame.time.Clock()

# Load sound
pop_sound = pygame.mixer.Sound(r'C:\Users\jmask\Downloads\pop-39222.mp3')

# Define sparks list globally
sparks = []

# Optimized movement function using Numba
@jit(nopython=True)
def optimized_move(position, speed, substeps):
    for _ in range(substeps):
        position += speed / substeps
    return position

# Ball class
class Ball:
    def __init__(self, x, y, radius, color):
        self.position = np.array([x, y], dtype=float)
        self.radius = radius
        self.color = color
        self.speed = np.array([random.choice([-4, -3, -2, 2, 3, 4]),
                               random.choice([-4, -3, -2, 2, 3, 4])], dtype=float)
        self.alive = True

    def move(self, substeps):
        for _ in range(substeps):
            self.position += self.speed / substeps
            # Check if the ball hits the edge of the screen and mark it as not alive
            if self.position[0] - self.radius < 0 or self.position[0] + self.radius > WIDTH:
                self.alive = False
            if self.position[1] - self.radius < 0 or self.position[1] + self.radius > HEIGHT:
                self.alive = False

    def draw(self, screen):
        if self.alive:
            pygame.draw.circle(screen, self.color, self.position.astype(int), self.radius)

    def check_collision_with_polygon(self, rotated_points, gap_indices, polygon_color):
        if not self.alive:
            return
        for i, point in enumerate(rotated_points):
            if i in gap_indices:
                continue

            next_point = rotated_points[(i + 1) % len(rotated_points)]
            if self.is_collision(point, next_point):
                self.resolve_collision(point, next_point, polygon_color)
                break

    def check_collision_with_ball(self, other_ball):
        if not self.alive or not other_ball.alive:
            return False
        diff = other_ball.position - self.position
        distance_squared = np.dot(diff, diff)
        radius_sum = self.radius + other_ball.radius
        if distance_squared < radius_sum ** 2:
            distance = np.sqrt(distance_squared)
            self.resolve_ball_collision(other_ball, diff, distance)
            return True
        return False

    def is_collision(self, point, next_point):
        edge_vector = (next_point[0] - point[0], next_point[1] - point[1])
        ball_to_point = self.position - np.array(point)

        edge_length_squared = edge_vector[0] ** 2 + edge_vector[1] ** 2
        if edge_length_squared == 0:
            return False

        projection = (ball_to_point[0] * edge_vector[0] + ball_to_point[1] * edge_vector[1]) / edge_length_squared
        projection = max(0, min(1, projection))

        closest_point = (
            point[0] + projection * edge_vector[0],
            point[1] + projection * edge_vector[1]
        )

        distance_squared = (self.position[0] - closest_point[0]) ** 2 + (self.position[1] - closest_point[1]) ** 2
        return distance_squared < self.radius ** 2

    def resolve_collision(self, point, next_point, spark_color):
        global sparks
        pop_sound.play()

        # Edge vector and collision normal calculation
        edge_vector = (next_point[0] - point[0], next_point[1] - point[1])
        ball_to_point = self.position - np.array(point)

        edge_length = math.sqrt(edge_vector[0] ** 2 + edge_vector[1] ** 2)
        edge_unit_vector = (edge_vector[0] / edge_length, edge_vector[1] / edge_length)

        projection = ball_to_point[0] * edge_unit_vector[0] + ball_to_point[1] * edge_unit_vector[1]
        closest_point = (
            point[0] + edge_unit_vector[0] * projection,
            point[1] + edge_unit_vector[1] * projection
        )

        collision_normal = self.position - np.array(closest_point)
        collision_length = np.linalg.norm(collision_normal)
        collision_normal = collision_normal / collision_length

        dot_product = np.dot(self.speed, collision_normal)
        self.speed -= 2 * dot_product * collision_normal

        overlap_distance = self.radius - collision_length
        self.position += collision_normal * overlap_distance

        # Generate sparks using the provided spark_color
        for _ in range(SPARK_COUNT):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3)  # Lower speed to make them more visible
            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)
            sparks.append(Spark(self.position[0], self.position[1], vx, vy, spark_color))

    def resolve_ball_collision(self, other_ball, diff, distance):
        pop_sound.play()

        nx = diff[0] / distance
        ny = diff[1] / distance

        tx = -ny
        ty = nx

        dpTan1 = self.speed[0] * tx + self.speed[1] * ty
        dpTan2 = other_ball.speed[0] * tx + other_ball.speed[1] * ty

        dpNorm1 = self.speed[0] * nx + self.speed[1] * ny
        dpNorm2 = other_ball.speed[0] * nx + other_ball.speed[1] * ny

        m1 = (dpNorm1 * (self.radius - other_ball.radius) + 2 * other_ball.radius * dpNorm2) / (self.radius + other_ball.radius)
        m2 = (dpNorm2 * (other_ball.radius - self.radius) + 2 * self.radius * dpNorm1) / (self.radius + other_ball.radius)

        self.speed[0] = tx * dpTan1 + nx * m1
        self.speed[1] = ty * dpTan1 + ny * m1
        other_ball.speed[0] = tx * dpTan2 + nx * m2
        other_ball.speed[1] = ty * dpTan2 + ny * m2

        overlap = 0.5 * (self.radius + other_ball.radius - distance + 1)
        self.position[0] -= overlap * nx
        self.position[1] -= overlap * ny
        other_ball.position[0] += overlap * nx
        other_ball.position[1] += overlap * ny

# Spatial Grid class for optimizing collision detection
class SpatialGrid:
    def __init__(self, width, height, cell_size):
        self.cell_size = cell_size
        self.grid = {}
        self.width = width
        self.height = height

    def _get_cell(self, x, y):
        return int(x // self.cell_size), int(y // self.cell_size)

    def add_ball(self, ball):
        cell = self._get_cell(ball.position[0], ball.position[1])
        if cell not in self.grid:
            self.grid[cell] = []
        self.grid[cell].append(ball)

    def get_nearby_balls(self, ball):
        cell = self._get_cell(ball.position[0], ball.position[1])
        nearby_balls = []
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                nearby_cell = (cell[0] + dx, cell[1] + dy)
                if nearby_cell in self.grid:
                    nearby_balls.extend(self.grid[nearby_cell])
        return nearby_balls

    def clear(self):
        self.grid.clear()

# Spark class for creating the rainbow sparks when balls collide
class Spark:
    def __init__(self, x, y, vx, vy, color, lifespan=40):  # Increased lifespan for visibility
        self.position = np.array([x, y], dtype=float)
        self.velocity = np.array([vx, vy], dtype=float)
        self.color = color
        self.lifespan = lifespan

    def move(self):
        self.position += self.velocity
        self.lifespan -= 1

    def draw(self, screen):
        if self.lifespan > 0:
            pygame.draw.circle(screen, self.color, self.position.astype(int), 5)  # Increased size for visibility

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
    rotated_points = []
    for point in points:
        rotated_point = rotate_point(point, center, angle)
        rotated_points.append(rotated_point)
    return rotated_points

def rotate_point(point, center, angle):
    temp_x = point[0] - center[0]
    temp_y = point[1] - center[1]

    rotated_x = temp_x * math.cos(angle) - temp_y * math.sin(angle)
    rotated_y = temp_y * math.cos(angle) + temp_x * math.sin(angle)

    return (rotated_x + center[0], rotated_y + center[1])

def spawn_balls(center, count=BALL_COUNT):
    balls = []
    angle_between_balls = math.pi * 2 / count
    small_radius = INITIAL_BALL_RADIUS * 3

    for i in range(count):
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
    smaller_polygon_radius = polygon_radius // 2
    middle_polygon_radius = (polygon_radius + smaller_polygon_radius) // 2
    sides = 100
    gap_size_small = sides // 4
    gap_size = sides // 4
    angle_offset_large = 0
    angle_offset_middle = 0
    angle_offset_small = 0
    font, large_font = pygame.font.SysFont(None, 38), pygame.font.SysFont(None, 64)

    points_large, gap_indices_large = create_polygon_with_gap(center, polygon_radius, sides, gap_size)
    points_middle, gap_indices_middle = create_polygon_with_gap(center, middle_polygon_radius, sides, gap_size)
    points_small, gap_indices_small = create_polygon_with_gap(center, smaller_polygon_radius, sides, gap_size_small)

    balls = spawn_balls(center, count=5)
    global sparks
    start_time = time.time()
    hue_large = 0
    hue_middle = 120  # Different starting hue for variety
    hue_small = 240  # Different starting hue for variety
    running = True

    grid = SpatialGrid(WIDTH, HEIGHT, 100)
    # wait for 1 second before starting the game
    time.sleep(1)
    while running:
        current_time = time.time()
        screen.fill(BLACK)

        # Increment hues with different speeds
        hue_large = (hue_large + 1) % 360
        hue_middle = (hue_middle + 0.5) % 360  # Slower hue change for middle polygon
        hue_small = (hue_small + 0.25) % 360  # Even slower hue change for small polygon

        # Convert hues to RGB colors
        color_large = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(hue_large / 360, 1, 1))
        color_middle = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(hue_middle / 360, 1, 1))
        color_small = tuple(int(c * 255) for c in colorsys.hsv_to_rgb(hue_small / 360, 1, 1))

        title_text = font.render("ESCAPING BALL SPAWNS NEW IN THE CENTER!", True, WHITE)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 150))

        watermark_font = pygame.font.SysFont(None, 36)
        watermark_texts = [
            watermark_font.render("yt:@jbbm_motions", True, (40, 40, 40)),
            watermark_font.render("tiktok:@jbbm_motions", True, (40, 40, 40)),
            watermark_font.render("subscribe for more!", True, (40, 40, 40))
        ]
        for idx, text in enumerate(watermark_texts):
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 1050 + idx * 30))

        if current_time - start_time > 50 and not show_end_message:
            show_end_message = True
            end_message_start_time = current_time

        for spark in sparks[:]:
            spark.move()
            spark.draw(screen)
            if spark.lifespan <= 0:
                sparks.remove(spark)

        # Rotate the polygons
        angle_offset_large += ROTATION_SPEED
        angle_offset_middle -= ROTATION_SPEED * 0.8  # Slightly slower rotation
        angle_offset_small -= ROTATION_SPEED * 0.6  # Even slower rotation

        rotated_points_large = rotate_polygon(points_large, center, angle_offset_large)
        rotated_points_middle = rotate_polygon(points_middle, center, angle_offset_middle)
        rotated_points_small = rotate_polygon(points_small, center, angle_offset_small)

        # Draw the polygons with the changing colors
        for i, point in enumerate(rotated_points_large):
            next_point = rotated_points_large[(i + 1) % len(rotated_points_large)]
            if i not in gap_indices_large:
                pygame.draw.line(screen, color_large, point, next_point, POLYGON_THICKNESS)

        for i, point in enumerate(rotated_points_middle):
            next_point = rotated_points_middle[(i + 1) % len(rotated_points_middle)]
            if i not in gap_indices_middle:
                pygame.draw.line(screen, color_middle, point, next_point, POLYGON_THICKNESS)

        for i, point in enumerate(rotated_points_small):
            next_point = rotated_points_small[(i + 1) % len(rotated_points_small)]
            if i not in gap_indices_small:
                pygame.draw.line(screen, color_small, point, next_point, POLYGON_THICKNESS)

        grid.clear()

        for ball in balls:
            ball.move(SUBSTEPS)
            if not ball.alive:
                balls.remove(ball)
                balls.extend(spawn_balls(center, count=3))
                break
            ball.check_collision_with_polygon(rotated_points_large, gap_indices_large, color_large)
            ball.check_collision_with_polygon(rotated_points_middle, gap_indices_middle, color_middle)
            ball.check_collision_with_polygon(rotated_points_small, gap_indices_small, color_small)
            grid.add_ball(ball)

        for ball in balls:
            nearby_balls = grid.get_nearby_balls(ball)
            for other_ball in nearby_balls:
                if ball != other_ball and ball.check_collision_with_ball(other_ball):
                    collision_x = (ball.position[0] + other_ball.position[0]) / 2
                    collision_y = (ball.position[1] + other_ball.position[1]) / 2
                    for _ in range(SPARK_COUNT):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(1, 3)
                        vx = speed * math.cos(angle)
                        vy = speed * math.sin(angle)
                        color = [random.randint(50, 255) for _ in range(3)]
                        sparks.append(Spark(collision_x, collision_y, vx, vy, color))

            ball.draw(screen)

        for spark in sparks[:]:
            spark.move()
            spark.draw(screen)
            if spark.lifespan <= 0:
                sparks.remove(spark)

        if len(balls) > MAX_BALLS:
            balls = balls[:MAX_BALLS]

        if len(sparks) > MAX_SPARKS:
            sparks = sparks[:MAX_SPARKS]

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
                running = False

        pygame.display.flip()
        clock.tick(FPS)

        gc.collect()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    pygame.quit()


import cProfile

if __name__ == "__main__":
    cProfile.run('main()')
