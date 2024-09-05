import pygame
import sys
import time

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 720, 1280
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Bouncing Squares with Trail and Frames')

# Initialize font
font = pygame.font.SysFont(None, 48)
large_font = pygame.font.SysFont(None, 64)

# Colors
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Square properties
square_size = 40
frame_size = 4  # Size of the black frame

# Initial positions of the moving squares (corners of the screen)
square1_pos = [0, 0]  # Top-left
square2_pos = [WIDTH - square_size, 0]  # Top-right
square3_pos = [0, HEIGHT - square_size]  # Bottom-left
square4_pos = [WIDTH - square_size, HEIGHT - square_size]  # Bottom-right

# Initial position of the stationary white square
stationary_square_pos = [WIDTH // 2 - square_size // 2, HEIGHT // 2 - square_size // 2]

# Velocities of the squares
square1_vel = [6, 6]  # Moving to the bottom-right
square2_vel = [-7, 7]  # Moving to the bottom-left
square3_vel = [6, -6]  # Moving to the top-right
square4_vel = [-6, -6]  # Moving to the top-left

# Speed increase factor
speed_increase_factor = 1.001

# Load sound
pop_sound = pygame.mixer.Sound(r'C:\Users\jmask\Downloads\pop-39222.mp3')

# Trail setup
trail_surface = pygame.Surface((WIDTH, HEIGHT))
trail_surface.set_alpha(100)  # Transparency for trail fading
trail_surface.fill(BLACK)

clock = pygame.time.Clock()
FPS = 60

start_time = time.time()
show_end_message = False
end_message_start_time = None

def check_collision_and_resolve(square1_pos, square2_pos, square1_vel, square2_vel, size):
    if (square1_pos[0] < square2_pos[0] + size and
            square1_pos[0] + size > square2_pos[0] and
            square1_pos[1] < square2_pos[1] + size and
            square1_pos[1] + size > square2_pos[1]):

        overlap_x = (square1_pos[0] + size) - square2_pos[0]
        overlap_y = (square1_pos[1] + size) - square2_pos[1]

        if overlap_x < overlap_y:
            # Adjust positions to avoid overlap
            if square1_vel[0] > 0:  # Moving right
                square1_pos[0] -= overlap_x // 2
                square2_pos[0] += overlap_x // 2
            else:  # Moving left
                square1_pos[0] += overlap_x // 2
                square2_pos[0] -= overlap_x // 2

            # Swap and increase velocities
            square1_vel[0], square2_vel[0] = -square1_vel[0] * speed_increase_factor, -square2_vel[0] * speed_increase_factor
        else:
            # Adjust positions to avoid overlap
            if square1_vel[1] > 0:  # Moving down
                square1_pos[1] -= overlap_y // 2
                square2_pos[1] += overlap_y // 2
            else:  # Moving up
                square1_pos[1] += overlap_y // 2
                square2_pos[1] -= overlap_y // 2

            # Swap and increase velocities
            square1_vel[1], square2_vel[1] = -square1_vel[1] * speed_increase_factor, -square2_vel[1] * speed_increase_factor

        # Play sound on collision
        pop_sound.play()

    return square1_vel, square2_vel

# Main loop
running = True
time.sleep(1)
while running:
    screen.fill(BLACK)  # Clear screen with black
    clock.tick(FPS)

    # Draw the trail first
    screen.blit(trail_surface, (0, 0))

    # Move squares
    for i in range(2):
        square1_pos[i] += square1_vel[i]
        square2_pos[i] += square2_vel[i]
        square3_pos[i] += square3_vel[i]
        square4_pos[i] += square4_vel[i]

    # Bounce logic for each square off the walls
    for pos, vel in zip([square1_pos, square2_pos, square3_pos, square4_pos],
                        [square1_vel, square2_vel, square3_vel, square4_vel]):
        if pos[0] <= 0 or pos[0] >= WIDTH - square_size:
            vel[0] *= -1
            pop_sound.play()  # Play sound on wall bounce
        if pos[1] <= 0 or pos[1] >= HEIGHT - square_size:
            vel[1] *= -1
            pop_sound.play()  # Play sound on wall bounce

    # Check for collisions between squares and resolve them
    square1_vel, square2_vel = check_collision_and_resolve(square1_pos, square2_pos, square1_vel, square2_vel, square_size)
    square1_vel, square3_vel = check_collision_and_resolve(square1_pos, square3_pos, square1_vel, square3_vel, square_size)
    square1_vel, square4_vel = check_collision_and_resolve(square1_pos, square4_pos, square1_vel, square4_vel, square_size)
    square2_vel, square3_vel = check_collision_and_resolve(square2_pos, square3_pos, square2_vel, square3_vel, square_size)
    square2_vel, square4_vel = check_collision_and_resolve(square2_pos, square4_pos, square2_vel, square4_vel, square_size)
    square3_vel, square4_vel = check_collision_and_resolve(square3_pos, square4_pos, square3_vel, square4_vel, square_size)

    # Check for collisions with the stationary white square
    for pos, vel in zip([square1_pos, square2_pos, square3_pos, square4_pos],
                        [square1_vel, square2_vel, square3_vel, square4_vel]):
        vel, _ = check_collision_and_resolve(pos, stationary_square_pos, vel, [0, 0], square_size)

    # Draw moving squares with black frames
    for pos, color in zip([square1_pos, square2_pos, square3_pos, square4_pos],
                          [RED, BLUE, GREEN, YELLOW]):
        pygame.draw.rect(screen, BLACK, (pos[0] - frame_size, pos[1] - frame_size,
                                         square_size + 2 * frame_size, square_size + 2 * frame_size))
        pygame.draw.rect(screen, color, (*pos, square_size, square_size))

        # Leave a trail by drawing the squares and their frames on the trail surface
        pygame.draw.rect(trail_surface, BLACK, (pos[0] - frame_size, pos[1] - frame_size,
                                                square_size + 2 * frame_size, square_size + 2 * frame_size))
        pygame.draw.rect(trail_surface, color, (*pos, square_size, square_size))

    # Draw the stationary white square
    pygame.draw.rect(screen, BLACK, (stationary_square_pos[0] - frame_size, stationary_square_pos[1] - frame_size,
                                     square_size + 2 * frame_size, square_size + 2 * frame_size))
    pygame.draw.rect(screen, WHITE, (*stationary_square_pos, square_size, square_size))

    title_text = font.render("BLUE DESTROYED SIMULATION", True, WHITE)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 125))

    # Add watermark text
    watermark_font = pygame.font.SysFont(None, 36)
    watermark_texts = [
        watermark_font.render("yt:@jbbm_motions", True, (100, 100, 100)),
        watermark_font.render("tiktok:@jbbm_motions", True, (100, 100, 100)),
        watermark_font.render("subscribe for more!", True, (100, 100, 100))
    ]
    for idx, text in enumerate(watermark_texts):
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 1000 + idx * 30))

    # Check if it's time to show the end message
    if time.time() - start_time > 50:
        show_end_message = True
        if end_message_start_time is None:
            end_message_start_time = time.time()

    # Draw end message if needed
    if show_end_message:
        game_over_text1 = large_font.render("LIKE", True, WHITE)
        game_over_text2 = large_font.render("FOLLOW", True, WHITE)
        game_over_text3 = large_font.render("SUBSCRIBE", True, WHITE)
        game_over_text4 = large_font.render("COMMENT WHAT TO DO NEXT", True, WHITE)
        screen.blit(game_over_text1, (WIDTH // 2 - game_over_text1.get_width() // 2, HEIGHT // 2 - 150))
        screen.blit(game_over_text2, (WIDTH // 2 - game_over_text2.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(game_over_text3, (WIDTH // 2 - game_over_text3.get_width() // 2, HEIGHT // 2 + 50))
        screen.blit(game_over_text4, (WIDTH // 2 - game_over_text4.get_width() // 2, HEIGHT // 2 + 150))

        # Update the display to show the end message
        pygame.display.flip()

        # Check if the 3-second period is over
        if time.time() - end_message_start_time >= 3:
            running = False

    else:
        # Update the display normally
        pygame.display.flip()

# Clean up
pygame.quit()
sys.exit()
