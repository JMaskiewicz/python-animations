import pygame
import random
import math
import time
import colorsys

# Constants
WIDTH, HEIGHT = 720, 1280
INITIAL_BALL_RADIUS = 10
FPS = 60
POLYGON_THICKNESS = 8
ROTATION_SPEED = 0.01  # Slow rotation speed
SUBSTEPS = 10  # Increase this for finer collision checks
BALL_COUNT = 2
SPARK_COUNT = 2  # Reduced number of sparks generated on collision
NUM_POLYGONS = 14  # Number of polygons to draw
POLYGON_GAP = 20  # Gap between each polygon in radius
GRAVITY = 0.25  # Stronger gravity effect on sparks

# Load sound
pop_sound = pygame.mixer.Sound(r'C:\Users\jmask\Downloads\pop-39222.mp3')

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Load sound
pop_sound = pygame.mixer.Sound(r'C:\Users\jmask\Downloads\Voicy_Stop Short.mp3')
class Ball:
    def __init__(self, x, y, radius, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.speed_x = -6
        self.speed_y = -6
        self.alive = True
        self.gravity = GRAVITY  # Small gravity effect

    def move(self, substeps):
        for _ in range(substeps):
            self.x += self.speed_x / substeps
            self.y += self.speed_y / substeps

            # Apply gravity to the vertical speed
            self.speed_y += self.gravity / substeps

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
            return False
        for i, point in enumerate(rotated_points):
            next_point = rotated_points[(i + 1) % len(rotated_points)]

            if i in gap_indices:
                # Check if the ball's edge is hitting the gap
                if self.is_edge_in_gap(point, next_point):
                    return True  # Return True if ball's edge is in the gap

            if self.is_collision(point, next_point):
                self.resolve_collision(point, next_point)
                break
        return False

    def check_collision_with_ball(self, other_ball):
        if not self.alive or not other_ball.alive:
            return False
        dx = other_ball.x - self.x
        dy = other_ball.y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance < self.radius + other_ball.radius:
            self.resolve_collision(other_ball, dx, dy, distance)
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

    def is_edge_in_gap(self, point, next_point):
        """ Check if the edge of the ball is in the gap area between two points. """
        closest_distance = self.point_to_line_distance(self.x, self.y, point, next_point)
        return closest_distance <= self.radius

    def point_to_line_distance(self, px, py, line_start, line_end):
        """ Calculate the shortest distance from a point to a line segment. """
        line_dx = line_end[0] - line_start[0]
        line_dy = line_end[1] - line_start[1]
        length_squared = line_dx * line_dx + line_dy * line_dy
        if length_squared == 0:
            return math.sqrt((px - line_start[0]) ** 2 + (py - line_start[1]) ** 2)  # Point on line
        t = ((px - line_start[0]) * line_dx + (py - line_start[1]) * line_dy) / length_squared
        t = max(0, min(1, t))
        projection_x = line_start[0] + t * line_dx
        projection_y = line_start[1] + t * line_dy
        return math.sqrt((px - projection_x) ** 2 + (py - projection_y) ** 2)

    def resolve_collision(self, point, next_point):
        pop_sound.play()

        # Calculate the edge vector
        edge_vector = (next_point[0] - point[0], next_point[1] - point[1])
        edge_length = math.sqrt(edge_vector[0] ** 2 + edge_vector[1] ** 2)
        edge_unit_vector = (edge_vector[0] / edge_length, edge_vector[1] / edge_length)

        # Ball's movement vector
        move_vector = (self.speed_x, self.speed_y)
        move_length = math.sqrt(move_vector[0] ** 2 + move_vector[1] ** 2)
        move_unit_vector = (move_vector[0] / move_length, move_vector[1] / move_length)

        # Vector from the edge start point to the ball's current position
        ball_to_point = (self.x - point[0], self.y - point[1])

        # Project ball_to_point onto the edge
        projection = ball_to_point[0] * edge_unit_vector[0] + ball_to_point[1] * edge_unit_vector[1]
        closest_point = (
            point[0] + edge_unit_vector[0] * projection,
            point[1] + edge_unit_vector[1] * projection
        )

        # Check the closest distance from the ball's path to the edge
        closest_distance = self.point_to_line_distance(self.x, self.y, point, next_point)

        # Calculate the distance the ball will move in this update
        move_distance = math.sqrt(self.speed_x ** 2 + self.speed_y ** 2)

        # Check if the ball intersects the edge during its movement
        if closest_distance <= self.radius and projection >= 0 and projection <= edge_length:
            collision_time = (self.radius - closest_distance) / move_distance
            self.x -= self.speed_x * collision_time
            self.y -= self.speed_y * collision_time

            # Reflect the ball's velocity vector
            collision_normal = (self.x - closest_point[0], self.y - closest_point[1])
            collision_length = math.sqrt(collision_normal[0] ** 2 + collision_normal[1] ** 2)
            collision_normal = (collision_normal[0] / collision_length, collision_normal[1] / collision_length)

            dot_product = self.speed_x * collision_normal[0] + self.speed_y * collision_normal[1]
            self.speed_x -= 2 * dot_product * collision_normal[0]
            self.speed_y -= 2 * dot_product * collision_normal[1]

            # Add randomness to the reflection
            random_angle = random.uniform(-0.3, 0.3)  # Adjust this range to control randomness
            cos_angle = math.cos(random_angle)
            sin_angle = math.sin(random_angle)

            new_speed_x = self.speed_x * cos_angle - self.speed_y * sin_angle
            new_speed_y = self.speed_x * sin_angle + self.speed_y * cos_angle

            self.speed_x = new_speed_x
            self.speed_y = new_speed_y

            # Overlap correction
            overlap_distance = self.radius - closest_distance
            if overlap_distance > 0:
                self.x += collision_normal[0] * overlap_distance
                self.y += collision_normal[1] * overlap_distance

            # Prevent the ball from getting stuck inside the polygon
            self.x += collision_normal[0] * self.radius
            self.y += collision_normal[1] * self.radius

            return True  # Valid collision

        return False  # No collision

# Spark class for creating the sparks when polygons are destroyed
class Spark:
    def __init__(self, x, y, vx, vy, color):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.alive = True

    def move(self):
        if self.y < HEIGHT:  # Keep moving until it reaches the bottom
            self.vy += GRAVITY  # Apply gravity to the vertical velocity
            self.x += self.vx
            self.y += self.vy
        else:
            self.alive = False  # Mark as not alive if it reaches the bottom

    def draw(self, screen):
        if self.alive:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 3)


def create_polygon_with_gap(center, radius, sides, gap_size, gap_start_angle=0, rotation_offset=0):
    points = []
    gap_indices = set()
    angle_increment = 2 * math.pi / sides

    # Adjust the starting angle by the rotation offset
    adjusted_gap_start_angle = (gap_start_angle + rotation_offset) % (2 * math.pi)

    # Calculate the index of the starting point for the gap based on the adjusted angle
    gap_start_index = int(adjusted_gap_start_angle / angle_increment) % sides

    for i in range(sides):
        angle = i * angle_increment
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        points.append((x, y))

        # Create a gap starting from the calculated index
        if gap_start_index <= i < gap_start_index + gap_size:
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

def create_sparks_from_polygon_edges(points, color, sparks):
    for i in range(len(points)):
        start_point = points[i]
        end_point = points[(i + 1) % len(points)]
        spark_count_per_edge = SPARK_COUNT  # Number of sparks per edge
        for _ in range(spark_count_per_edge):
            t = random.random()
            spark_x = start_point[0] + t * (end_point[0] - start_point[0])
            spark_y = start_point[1] + t * (end_point[1] - start_point[1])
            vx = random.uniform(-1, 1)  # Horizontal velocity
            vy = random.uniform(1, 3)  # Initial downward velocity
            new_spark = Spark(spark_x, spark_y, vx, vy, color)
            sparks.append(new_spark)

def main():
    show_end_message = False
    center = (WIDTH // 2, HEIGHT // 2)
    initial_radius = min(WIDTH, HEIGHT) // 2 - 25
    sides = 1000
    gap_size = sides // 8
    angle_offset = 0  # Initial angle offset
    font, large_font = pygame.font.SysFont(None, 48), pygame.font.SysFont(None, 64)

    polygons = []
    directions = []  # To store the direction of each polygon

    # Initialize polygons with consistent directions
    for i in range(NUM_POLYGONS):
        radius = initial_radius - i * POLYGON_GAP
        if radius > 0:
            direction = -1 if i % 2 == 0 else 1  # Alternating directions: left (-1), right (1)
            directions.append(direction)
            points, gap_indices = create_polygon_with_gap(center, radius, sides, gap_size, gap_start_angle=0)
            polygons.append((points, gap_indices, radius))

    balls = spawn_balls(center)
    sparks = []
    start_time = time.time()
    hue = 0  # Start hue value
    running = True
    # wait for 3 seconds
    while time.time() - start_time < 3:
        screen.fill(BLACK)
        pygame.display.flip()
        clock.tick(FPS)

    while running:
        current_time = time.time()

        screen.fill(BLACK)

        # Calculate the current color from the hue
        hue = (hue + 1) % 360  # Increment hue, wrap around at 360
        title_color = colorsys.hsv_to_rgb(hue / 360, 1, 1)  # Convert hue to RGB
        title_color = tuple(int(c * 255) for c in title_color)  # Convert to RGB values in range 0-255

        title_text = font.render("Ball Trying to Escape!", True, title_color)
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 150))

        # Increment angle_offset to rotate polygons
        angle_offset += ROTATION_SPEED

        # Move and check collision for each ball
        for ball in balls:
            ball.move(SUBSTEPS)
            if not ball.alive:
                # Remove this ball and spawn two new balls at the center
                balls.remove(ball)
                balls.extend(spawn_balls(center))
                break

            # Iterate backwards when modifying lists to avoid index issues
            for idx in range(len(polygons) - 1, -1, -1):
                points, gap_indices, radius = polygons[idx]
                direction = directions[idx]

                # Rotate the polygon using its stable direction
                rotated_points = rotate_polygon(points, center, direction * angle_offset)

                # Check if the ball's edge is hitting the gap
                in_gap = ball.check_collision_with_polygon(rotated_points, gap_indices)
                if in_gap:
                    # Create sparks from the polygon edges before removing the polygon
                    polygon_hue = (hue + idx * (360 / NUM_POLYGONS)) % 360
                    polygon_color = colorsys.hsv_to_rgb(polygon_hue / 360, 1, 1)
                    polygon_color = tuple(int(c * 255) for c in polygon_color)
                    create_sparks_from_polygon_edges(rotated_points, polygon_color, sparks)
                    polygons.pop(idx)
                    directions.pop(idx)

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
            if not spark.alive:
                sparks.remove(spark)

        # Check if all polygons are removed to show the end message
        if not polygons:
            start_end_time = time.time()
            show_end_message = True

        # Draw the polygons with hue-based color
        for i, (points, gap_indices, radius) in enumerate(polygons):
            polygon_hue = (hue + i * (360 / NUM_POLYGONS)) % 360
            polygon_color = colorsys.hsv_to_rgb(polygon_hue / 360, 1, 1)
            polygon_color = tuple(int(c * 255) for c in polygon_color)

            rotated_points = rotate_polygon(points, center, directions[i] * angle_offset)
            for j, point in enumerate(rotated_points):
                next_point = rotated_points[(j + 1) % len(rotated_points)]
                if j not in gap_indices:
                    pygame.draw.line(screen, polygon_color, point, next_point, POLYGON_THICKNESS)

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

            if current_time - start_end_time >= 3:
                running = False

        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

    pygame.quit()

if __name__ == "__main__":
    main()