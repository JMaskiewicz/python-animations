import pygame
import colorsys
import random
import time

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
shrink_factor = 1  # Shrink factor for each bounce (used for smooth shrinking)
square_speed_increase = 1.001  # Speed increase for each bounce
hue_shift_square = 0  # Starting hue for the large square outline
hue_shift_text = 0  # Separate starting hue for the text
border_radius = 20  # Border radius for rounded corners

# Small black square properties
small_square_size = 40  # Size of the small bouncing square
small_square_x, small_square_y = WIDTH // 2, HEIGHT // 2  # Start small square in the center
dx, dy = 6, 8  # Speed in x and y directions
gravity = 0.1  # Gravity constant that accelerates the square downwards
hue_trail = 0  # Starting hue for the trail

# Keep track of trail pixels that have been covered
filled_pixels = set()  # Using a set for efficient pixel tracking

# Calculate the number of pixels that need to be filled (in large square)
num_pixels_to_fill = int(large_square_size * large_square_size)

large_font = pygame.font.SysFont(None, 64)

# Main loop
running = True
clock = pygame.time.Clock()
start_time = time.time()
show_end_message = False

while running:
    current_time = time.time()
    elapsed_time = current_time - start_time

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
    # Keep track of all pixels the small square passes over
    for x in range(int(small_square_x), int(small_square_x + small_square_size)):
        for y in range(int(small_square_y), int(small_square_y + small_square_size)):
            if large_square_x <= x < large_square_x + large_square_size and large_square_y <= y < large_square_y + large_square_size:
                filled_pixels.add((x, y))

    # Draw each pixel covered by the small square
    for (tx, ty) in filled_pixels:
        pygame.draw.rect(window, (0, 0, 0), (tx, ty, 1, 1))

    # Check if all pixels have been filled
    if len(filled_pixels) >= num_pixels_to_fill:
        show_end_message = True

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
        random.choice(collision_sounds).play()

    elif small_square_x + small_square_size >= large_square_x + large_square_size:
        dx = -dx * square_speed_increase  # Invert direction and increase speed
        small_square_x = large_square_x + large_square_size - small_square_size  # Reposition outside the boundary
        random.choice(collision_sounds).play()

    if small_square_y <= large_square_y:
        dy = -dy * square_speed_increase  # Invert direction and increase speed
        small_square_y = large_square_y  # Reposition outside the boundary
        random.choice(collision_sounds).play()

    elif small_square_y + small_square_size >= large_square_y + large_square_size:
        dy = -dy * square_speed_increase  # Invert direction and increase speed
        small_square_y = large_square_y + large_square_size - small_square_size  # Reposition outside the boundary
        random.choice(collision_sounds).play()

    # End message after game over
    if show_end_message:
        game_over_text = large_font.render(f"All pixels filled in {int(elapsed_time)} seconds!", True, BLACK)
        window.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2))

        # Stop the game after a short delay
        if current_time - elapsed_time >= 3:
            running = False

    # Add watermark text
    for idx, text in enumerate(watermark_texts):
        window.blit(text, (WIDTH // 2 - text.get_width() // 2, 1050 + idx * 30))

    # Update display and control the frame rate
    pygame.display.flip()
    clock.tick(60)

    # Handle quit event
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

# Quit Pygame
pygame.quit()
