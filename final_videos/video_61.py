import pygame
import math

# Initialize Pygame
pygame.init()

# Create Pygame window
WIDTH, HEIGHT = 720, 1280
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame Colorful Pattern")

# Define colors
colors = [(255, 0, 0), (255, 255, 0), (0, 0, 255), (0, 255, 0), (128, 0, 128), (255, 165, 0)]  # RGB for red, yellow, blue, green, purple, orange

# Starting position and angle
center_x, center_y = WIDTH // 2, HEIGHT // 2  # Middle of the screen
angle = 0
length = 2
rotation_speed = 0.5  # degrees to rotate each frame

# Define FPS and total frames for a 40-second animation
FPS = 60
total_time = 40  # in seconds
total_frames = FPS * total_time  # total frames for 40 seconds

# Number of lines to draw
total_lines = 300
lines_per_frame = total_lines / total_frames  # how many lines to draw per frame

# Set up clock
clock = pygame.time.Clock()

# Fractional accumulator
accumulated_lines = 0.0

# Store all drawn lines
lines = []

# Run until the user asks to quit
running = True
i = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Accumulate the fractional progress
    accumulated_lines += lines_per_frame

    # Draw the pattern in steps if accumulated_lines >= 1
    while accumulated_lines >= 1:
        if i >= total_lines:
            running = False
            break

        # Set the color based on i
        color = colors[i % 6]

        # Calculate the line's new end position
        new_x = center_x + int(math.cos(math.radians(angle)) * length)
        new_y = center_y + int(math.sin(math.radians(angle)) * length)

        # Store the line data (start position, end position, color)
        lines.append(((center_x, center_y), (new_x, new_y), color))

        # Update angle and length
        angle += 61
        length += 2

        # Decrease accumulated_lines by 1
        accumulated_lines -= 1

        # Increment i
        i += 1

    # Clear the screen
    screen.fill((0, 0, 0))

    # Draw all the lines with the current rotation around the middle of the screen
    for start_pos, end_pos, color in lines:
        # Rotate the start and end positions around the center (MIDDLE)
        rotated_start_x = int(center_x + math.cos(math.radians(rotation_speed * i)) * (start_pos[0] - center_x) - math.sin(math.radians(rotation_speed * i)) * (start_pos[1] - center_y))
        rotated_start_y = int(center_y + math.sin(math.radians(rotation_speed * i)) * (start_pos[0] - center_x) + math.cos(math.radians(rotation_speed * i)) * (start_pos[1] - center_y))

        rotated_end_x = int(center_x + math.cos(math.radians(rotation_speed * i)) * (end_pos[0] - center_x) - math.sin(math.radians(rotation_speed * i)) * (end_pos[1] - center_y))
        rotated_end_y = int(center_y + math.sin(math.radians(rotation_speed * i)) * (end_pos[0] - center_x) + math.cos(math.radians(rotation_speed * i)) * (end_pos[1] - center_y))

        # Draw the rotated line
        pygame.draw.line(screen, color, (rotated_start_x, rotated_start_y), (rotated_end_x, rotated_end_y), 2)

    # Update the display
    pygame.display.flip()

    # Cap the frame rate
    clock.tick(FPS)

# Wait before exiting
pygame.time.wait(2000)

# Done! Time to quit.
pygame.quit()
