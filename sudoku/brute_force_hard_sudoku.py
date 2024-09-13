import pygame
import time as pytime  # Using 'pytime' to avoid confusion with the delay function in pygame

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Load sounds
win_pop_sound = pygame.mixer.Sound(r'C:\Users\jmask\Downloads\victorymale-version-230553.mp3')

# Constants for window size and grid size
WINDOW_WIDTH, WINDOW_HEIGHT = 720, 1280
GRID_SIZE = 540  # Keeping the grid size as 540x540, same as before
CELL_SIZE = GRID_SIZE // 9
LINE_WIDTH = 2

# Colors
BLACK = (0, 0, 0)
NEON_BLUE = (0, 255, 255)  # Neon Blue color for grid and original numbers
NEON_GREEN = (57, 255, 20)  # Neon Green color for placed numbers
NEON_RED = (255, 20, 60)    # Neon Red for numbers being tested
WHITE = (255, 255, 255)     # White for final message text

FONT = pygame.font.Font(None, 40)
BIG_FONT = pygame.font.Font(None, 80)  # Big font for the main text

# Calculating the offset to center the grid in the window
GRID_OFFSET_X = (WINDOW_WIDTH - GRID_SIZE) // 2
GRID_OFFSET_Y = (WINDOW_HEIGHT - GRID_SIZE) // 2

# Initial Sudoku grid (0 represents an empty cell)
grid = [
    [0, 0, 0, 8, 0, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 4, 3, 0],
    [5, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 7, 0, 8, 0, 0],
    [0, 0, 0, 0, 0, 0, 1, 0, 0],
    [0, 2, 0, 0, 3, 0, 0, 0, 0],
    [6, 0, 0, 0, 0, 0, 0, 7, 5],
    [0, 3, 4, 0, 0, 0, 0, 0, 0],
    [0, 0, 2, 0, 0, 0, 6, 0, 0],
]


# This will hold positions of the numbers that we place (as opposed to pre-filled numbers)
placed_numbers = []

# Function to draw the title text
def draw_title(screen):
    title_font = BIG_FONT
    title_text1 = title_font.render("BRO SOLVED SUDOKU", True, NEON_BLUE)
    title_text2 = title_font.render("WITH BRUTE FORCE", True, NEON_BLUE)
    screen.blit(title_text1, (WINDOW_WIDTH // 2 - title_text1.get_width() // 2, 100))
    screen.blit(title_text2, (WINDOW_WIDTH // 2 - title_text2.get_width() // 2, 180))

# Function to draw the final message after solving the puzzle
def draw_final_message(screen):
    title_font = pygame.font.Font(None, 70)
    title_text1 = title_font.render("LIKE SUBSCRIBE", True, NEON_BLUE)
    title_text2 = title_font.render("COMMENT WHAT TO DO NEXT", True, NEON_BLUE)
    screen.blit(title_text1, (WINDOW_WIDTH // 2 - title_text1.get_width() // 2, 100))
    screen.blit(title_text2, (WINDOW_WIDTH // 2 - title_text2.get_width() // 2, 180))

# Function to draw the watermark
def draw_watermark(screen):
    watermark_font = pygame.font.SysFont(None, 36)
    watermark_texts = [
        watermark_font.render("yt:@jbbm_motions", True, (50, 50, 50)),
        watermark_font.render("tiktok:@jbbm_motions", True, (50, 50, 50)),
        watermark_font.render("subscribe for more!", True, (50, 50, 50))
    ]
    for idx, text in enumerate(watermark_texts):
        screen.blit(text, (WINDOW_WIDTH // 2 - text.get_width() // 2, 1050 + idx * 30))

# Function to draw the Sudoku grid in the center of the window
def draw_grid(screen, grid, highlight=None, test_num=None, test_pos=None, show_title=True):
    screen.fill(BLACK)

    # Draw the grid lines
    for i in range(10):
        if i % 3 == 0:
            thickness = 4  # Bold line for 3x3 grid separators
        else:
            thickness = 1
        # Horizontal and vertical lines adjusted by GRID_OFFSET_X and GRID_OFFSET_Y
        pygame.draw.line(screen, NEON_BLUE, (GRID_OFFSET_X + i * CELL_SIZE, GRID_OFFSET_Y),
                         (GRID_OFFSET_X + i * CELL_SIZE, GRID_OFFSET_Y + GRID_SIZE), thickness)
        pygame.draw.line(screen, NEON_BLUE, (GRID_OFFSET_X, GRID_OFFSET_Y + i * CELL_SIZE),
                         (GRID_OFFSET_X + GRID_SIZE, GRID_OFFSET_Y + i * CELL_SIZE), thickness)

    # Draw the numbers in the grid
    for i in range(9):
        for j in range(9):
            if grid[i][j] != 0:
                if (i, j) in placed_numbers:
                    # Numbers that were placed by the brute-force algorithm (in neon green)
                    color = NEON_GREEN if (i, j) != highlight else NEON_RED
                else:
                    # Numbers that are part of the original grid (in neon blue)
                    color = NEON_BLUE
                text = FONT.render(str(grid[i][j]), True, color)
                screen.blit(text, (GRID_OFFSET_X + j * CELL_SIZE + CELL_SIZE // 3,
                                   GRID_OFFSET_Y + i * CELL_SIZE + CELL_SIZE // 4))

    # Draw the number being tested in Neon Red
    if test_num is not None and test_pos is not None:
        row, col = test_pos
        text = FONT.render(str(test_num), True, NEON_RED)
        screen.blit(text, (GRID_OFFSET_X + col * CELL_SIZE + CELL_SIZE // 3,
                           GRID_OFFSET_Y + row * CELL_SIZE + CELL_SIZE // 4))

    if show_title:
        # Draw the title at the top
        draw_title(screen)
    else:
        draw_final_message(screen)

    # Draw watermark
    draw_watermark(screen)


# Check if a number is valid in a given cell
def is_valid(grid, num, pos):
    row, col = pos

    # Check the row
    for i in range(9):
        if grid[row][i] == num and col != i:
            return False

    # Check the column
    for i in range(9):
        if grid[i][col] == num and row != i:
            return False

    # Check the 3x3 box
    box_x = col // 3
    box_y = row // 3
    for i in range(box_y * 3, box_y * 3 + 3):
        for j in range(box_x * 3, box_x * 3 + 3):
            if grid[i][j] == num and (i, j) != pos:
                return False

    return True


# Function to solve the Sudoku using brute force and visually show every step
def brute_force_solve(screen, grid):
    empty = find_empty(grid)
    if not empty:
        return True  # Solved

    row, col = empty

    for num in range(1, 10):
        # Show the number being tested in Neon Red
        draw_grid(screen, grid, (row, col), test_num=num, test_pos=(row, col))
        pygame.display.update()
        pygame.time.delay(1)  # Pause to visually show testing each number

        if is_valid(grid, num, (row, col)):
            grid[row][col] = num
            placed_numbers.append((row, col))  # Track the placed number
            draw_grid(screen, grid, (row, col))  # Show placement of valid number
            pygame.display.update()
            pygame.time.delay(1)  # Pause to visually show placing the number

            if brute_force_solve(screen, grid):
                return True  # Continue solving

            # If the solution is incorrect, backtrack (remove the number)
            grid[row][col] = 0
            placed_numbers.remove((row, col))  # Remove the tracked placed number
            draw_grid(screen, grid, (row, col))
            pygame.display.update()
            pygame.time.delay(1)

    return False


# Find an empty cell in the grid
def find_empty(grid):
    for i in range(9):
        for j in range(9):
            if grid[i][j] == 0:
                return (i, j)
    return None


# Main function to run the Pygame window and solve the puzzle
def main():
    # Add background music
    pygame.mixer.music.load(r"C:\Users\jmask\Downloads\music-for-arcade-style-game-146875.mp3")  # Replace with your mp3 path
    pygame.mixer.music.play(-1)  # Loop the music in the background

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Sudoku Solver")

    # Start time tracking
    start_time = pytime.time()

    running = True
    puzzle_solved = False  # Flag to track if the puzzle is solved

    while running:
        pygame.time.delay(5000)
        # Switch the title to final message after puzzle is solved
        if not puzzle_solved:
            draw_grid(screen, grid, show_title=True)
        else:
            win_pop_sound.play()
            # Show final message once solved
            draw_grid(screen, grid, show_title=False)
            pygame.display.update()
            pygame.time.delay(5000)  # Show the final message for 5 seconds
            running = False  # Exit after the final message

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not puzzle_solved:
            # Start solving the puzzle with brute force
            brute_force_solve(screen, grid)
            puzzle_solved = True  # Set the flag to true once solved

    pygame.quit()


if __name__ == "__main__":
    main()