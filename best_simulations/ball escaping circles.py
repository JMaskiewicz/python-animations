import pygame
import colorsys
import random
import time

from final_videos.video_81 import show_end_message

# Initialize Pygame
pygame.init()

# Create Pygame window
WIDTH, HEIGHT = 720, 1280
window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bouncing Black Square with Gravity and Shrinking")

# Load sounds
pop_sound_1 = pygame.mixer.Sound(r'C:\Users\jmask\Downloads\breaking-glass-83809.mp3')
pop_sound_2 = pygame.mixer.Sound(r'C:\Users\jmask\Downloads\glass-shatter-7-95202.mp3')
pop_sound_3 = pygame.mixer.Sound(r'C:\Users\jmask\Downloads\glass-breaking-93803.mp3')

# List of sounds
collision_sounds = [pop_sound_1, pop_sound_2, pop_sound_3]

# Define colors based on hue
def get_hue_color(hue):
    """Convert hue to RGB color."""
    color = colorsys.hsv_to_rgb(hue, 1, 1)  # Convert HSV to RGB
    return tuple(int(c * 255) for c in color)

# Font setup for the title (make the text smaller)
font = pygame.font.SysFont("Arial", 40)

# Watermark font setup
watermark_font = pygame.font.SysFont(None, 36)
watermark_texts = [
    watermark_font.render("yt:@jbbm_motions", True, (200, 200, 200)),
    watermark_font.render("tiktok:@jbbm_motions", True, (200, 200, 200)),
    watermark_font.render("subscribe for more!", True, (200, 200, 200))
]

BLACK = (0, 0, 0)

# Large square properties
max_large_size = min(WIDTH, HEIGHT) * 0.9  # Maximum size for the outer square
large_square_size = max_large_size
large_square_x, large_square_y = (WIDTH - large_square_size) // 2, (HEIGHT - large_square_size) // 2  # Start centered
shrink_factor = 0.99  # Shrink factor for each bounce (used for smooth shrinking)
square_speed_increase = 1.001  # Speed increase for each bounce
shrink_speed = 0.25  # Speed at which the large square shrinks
min_large_size = 30  # Minimum size for the large square
hue_shift_square = 0  # Starting hue for the large square outline
hue_shift_text = 0  # Separate starting hue for the text
shrinking = False  # Flag to indicate shrinking
border_radius = 20  # Border radius for rounded corners

# Small black square properties
small_square_size = 40  # Size of the small bouncing square
small_square_x, small_square_y = WIDTH // 2, HEIGHT // 2  # Start small square in the center
dx, dy = 5, 7  # Speed in x and y directions
gravity = 0.15  # Gravity constant that accelerates the square downwards
hue_trail = 0  # Starting hue for the trail

# Trail properties
trail = []  # List to store the trail of small squares
trail_length = 6  # Number of squares in the trail

large_font = pygame.font.SysFont(None, 64)

# Main loop
running = True
clock = pygame.time.Clock()
start_time = time.time()
show_end_message = False

while running:
    current_time = time.time()
    elapsed_time = current_time - start_time

    if current_time - start_time > 50 and not show_end_message:
        show_end_message = True
        end_message_start_time = current_time

    window.fill((255, 255, 255))  # Clear the screen with a white background

    # Get the current hue color for the large square border
    large_square_color = get_hue_color(hue_shift_square)

    # 1. Outer hue-shifting border (slightly larger than the black border)
    pygame.draw.rect(window, large_square_color,
                     (large_square_x - 20, large_square_y - 20, large_square_size + 40, large_square_size + 40),
                     15, border_radius=border_radius)

    # 2. Larger black border inside the outer hue-shifting border
    pygame.draw.rect(window, (0, 0, 0),
                     (large_square_x - 10, large_square_y - 10, large_square_size + 20, large_square_size + 20),
                     15, border_radius=border_radius)

    # 3. Inner hue-shifting border (inside the black border, equidistant to match the outer one)
    pygame.draw.rect(window, large_square_color,
                     (large_square_x, large_square_y, large_square_size, large_square_size),
                     15, border_radius=border_radius)

    # Update hue for the large square
    hue_shift_square += 0.005  # Large square hue shift rate
    if hue_shift_square > 1:
        hue_shift_square = 0

    # Title text with hue-shifting border effect (smaller font)
    title_text_1 = "BOUNCING SQUARE GETS FASTER"
    title_text_2 = "AS THE SQUARE SHRINKS"
    bottom_text = "WAIT TILL THE END!"

    # Render the text multiple times for the hue-shifting border effect (Title at the top)
    for offset in range(5, 0, -1):
        hue_border_color = get_hue_color(hue_shift_text + offset * 0.02)
        title_surface_1 = font.render(title_text_1, True, hue_border_color)
        title_surface_2 = font.render(title_text_2, True, hue_border_color)
        bottom_surface = font.render(bottom_text, True, hue_border_color)

        window.blit(title_surface_1, (WIDTH // 2 - title_surface_1.get_width() // 2 + offset, 90 + offset))
        window.blit(title_surface_2, (WIDTH // 2 - title_surface_2.get_width() // 2 + offset, 140 + offset))
        window.blit(bottom_surface, (WIDTH // 2 - bottom_surface.get_width() // 2 + offset, HEIGHT - 90 + offset))

    # Black text on top of the hue borders (for clear text)
    title_surface_1 = font.render(title_text_1, True, (0, 0, 0))
    title_surface_2 = font.render(title_text_2, True, (0, 0, 0))
    bottom_surface = font.render(bottom_text, True, (0, 0, 0))

    window.blit(title_surface_1, (WIDTH // 2 - title_surface_1.get_width() // 2, 90))
    window.blit(title_surface_2, (WIDTH // 2 - title_surface_2.get_width() // 2, 140))
    window.blit(bottom_surface, (WIDTH // 2 - bottom_surface.get_width() // 2, HEIGHT - 90))

    # Update the hue for the text
    hue_shift_text += 0.005  # Slower hue shift for text
    if hue_shift_text > 1:
        hue_shift_text = 0

    # Update the trail of the small black square
    trail.append((small_square_x, small_square_y, hue_trail))
    if len(trail) > trail_length:
        trail.pop(0)

    # Draw each square in the trail with a small black border and hue color inside
    for i, (tx, ty, trail_hue) in enumerate(trail):
        trail_color = get_hue_color(trail_hue)
        # Draw the black border for the trail squares
        pygame.draw.rect(window, (0, 0, 0), (tx, ty, small_square_size, small_square_size), 2)
        # Draw the trail square with hue color inside, leaving a small black border
        pygame.draw.rect(window, trail_color, (tx + 2, ty + 2, small_square_size - 4, small_square_size - 4), 0)

    # Draw the small black square with rounded corners
    pygame.draw.rect(window, (0, 0, 0), (small_square_x, small_square_y, small_square_size, small_square_size), 0)

    # Update small square position with gravity effect
    small_square_x += dx
    small_square_y += dy
    dy += gravity  # Apply gravity to the vertical speed

    # Check for boundary collisions with the large square
    if small_square_x <= large_square_x:
        dx = -dx * square_speed_increase  # Invert direction and increase speed
        small_square_x = large_square_x  # Reposition outside the boundary
        trail_length += 1  # Increase trail length on bounce
        random.choice(collision_sounds).play()
        shrinking = True  # Trigger shrinking on bounce
        shrink_target = max(large_square_size * shrink_factor, min_large_size)  # Set target size
        large_square_x = (WIDTH - large_square_size) // 2  # Re-center large square

    elif small_square_x + small_square_size >= large_square_x + large_square_size:
        trail_length += 1  # Increase trail length on bounce
        dx = -dx * square_speed_increase  # Invert direction and increase speed
        small_square_x = large_square_x + large_square_size - small_square_size  # Reposition outside the boundary
        random.choice(collision_sounds).play()
        shrinking = True  # Trigger shrinking on bounce
        shrink_target = max(large_square_size * shrink_factor, min_large_size)  # Set target size
        large_square_x = (WIDTH - large_square_size) // 2  # Re-center large square

    if small_square_y <= large_square_y:
        trail_length += 1  # Increase trail length on bounce
        dy = -dy * square_speed_increase  # Invert direction and increase speed
        small_square_y = large_square_y  # Reposition outside the boundary
        random.choice(collision_sounds).play()
        shrinking = True  # Trigger shrinking on bounce
        shrink_target = max(large_square_size * shrink_factor, min_large_size)  # Set target size
        large_square_y = (HEIGHT - large_square_size) // 2  # Re-center large square

    elif small_square_y + small_square_size >= large_square_y + large_square_size:
        trail_length += 1  # Increase trail length on bounce
        dy = -dy * square_speed_increase  # Invert direction and increase speed
        small_square_y = large_square_y + large_square_size - small_square_size  # Reposition outside the boundary
        random.choice(collision_sounds).play()
        shrinking = True  # Trigger shrinking on bounce
        shrink_target = max(large_square_size * shrink_factor, min_large_size)  # Set target size
        large_square_y = (HEIGHT - large_square_size) // 2  # Re-center large square

    # Handle smooth shrinking of the large square
    if shrinking:
        if large_square_size > shrink_target:
            large_square_size -= shrink_speed  # Shrink gradually
            large_square_x = (WIDTH - large_square_size) // 2  # Re-center during shrinking
            large_square_y = (HEIGHT - large_square_size) // 2
        else:
            shrinking = False  # Stop shrinking when target size is reached

    # Update hue for the trail
    hue_trail += 0.02
    if hue_trail > 1:
        hue_trail = 0

    # Add watermark text
    for idx, text in enumerate(watermark_texts):
        window.blit(text, (WIDTH // 2 - text.get_width() // 2, 1050 + idx * 30))

    # End message after game over
    if show_end_message:
        game_over_text1 = large_font.render("LIKE", True, BLACK)
        game_over_text2 = large_font.render("FOLLOW", True, BLACK)
        game_over_text3 = large_font.render("SUBSCRIBE", True, BLACK)
        game_over_text4 = large_font.render("COMMENT WHAT TO DO NEXT", True, BLACK)
        window.blit(game_over_text1, (WIDTH // 2 - game_over_text1.get_width() // 2, HEIGHT // 2 - 150))
        window.blit(game_over_text2, (WIDTH // 2 - game_over_text2.get_width() // 2, HEIGHT // 2 - 50))
        window.blit(game_over_text3, (WIDTH // 2 - game_over_text3.get_width() // 2, HEIGHT // 2 + 50))
        window.blit(game_over_text4, (WIDTH // 2 - game_over_text4.get_width() // 2, HEIGHT // 2 + 150))

        if current_time - end_message_start_time >= 3:
            running = False


    # Update display and control the frame rate
    pygame.display.flip()
    clock.tick(60)

    # Handle quit event
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

# Quit Pygame
pygame.quit()
