import pygame
import sys
import time

pygame.init()
pygame.mixer.init()

# --- Constants ---
WIDTH, HEIGHT = 800, 600
FPS = 60
TIMER_DURATION = 30 * 60  # 30 minutes in seconds

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GREEN = (200, 255, 200) # For puzzle background
COMPLETED_PUZZLE_COLOR = (0, 200, 0) # Darker green for completed puzzle indicator
UNCOMPLETED_PUZZLE_COLOR = (150, 150, 150) # Grey for uncompleted puzzle indicator
RED = (255, 0, 0) # For error messages
BLUE = (50, 50, 200) # For button background
DARK_BLUE = (20, 20, 150) # For button hover
GOLD = (255, 215, 0) # For congratulatory text
HINT_BOX_COLOR = (255, 255, 220) # Light yellow for hint box

# --- Setup ---
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("ChemEscape - Lab Escape Game")
clock = pygame.time.Clock()

# Fonts
font = pygame.font.SysFont('arial', 20)
small_font = pygame.font.SysFont('arial', 14) # Smaller font for puzzle indicators
large_font = pygame.font.SysFont('arial', 40, bold=True) # For congratulations message
title_font = pygame.font.SysFont('arial', 60, bold=True) # For game title # FIX: Changed SysSysFont to SysFont
stats_font = pygame.font.SysFont('arial', 28) # For end screen stats

# Puzzle Question Font
try:
    comic_sans_font = pygame.font.SysFont('Comic Sans MS', 24, bold=True) # Larger and bold for questions
    hint_font = pygame.font.SysFont('Comic Sans MS', 20) # Slightly smaller for hints
except:
    comic_sans_font = pygame.font.SysFont('arial', 24, bold=True) # Fallback if Comic Sans isn't available
    hint_font = pygame.font.SysFont('arial', 20) # Fallback for hints

# --- Assets ---
lab_bg = pygame.image.load("assets/lab.png")
character_img = pygame.image.load("assets/character.png")
pygame.mixer.music.load("assets/music.ogg")
pygame.mixer.music.play(-1)

# --- Character Setup ---
char_x, char_y = 50, 500  # Initial character position
char_speed = 4

# --- Puzzle System ---
puzzles = [
    {"id": 1, "question": "Rearrange the symbols for Boron, Nitrogen, Carbon, Argon and Oxygen to form the name of which element?\nHint: It is pretty common.", "answer": "Carbon"},
    {"id": 2, "question": "If a substance sublimated, then precipitated, then melted, then froze; which state of matter was it in the most times?", "answer": "Solid", "hint": "There are only 3 possibilities"},
    {"id": 3, "question": "If we reacted Sodium Hydoxide (NaOH) with Hydrochloric Acid (HCl), we would get water and what other common substance?", "answer": "Salt", "hint": "It has four letters and you would find it in fish and chips."},
    {"id": 4, "question": "As you heat a substance its particles gain what type of energy? Take the first letter of the name of this type of energy and write the name of the element that has it as a symbol.", "answer": "Potassium", "hint": "Bananas"},
    {"id": 5, "question": "Spell the word formed from these chemical element symbols: Carbon, Americium, Phosphorus.", "answer": "Camp", "hint": "It happened in Term 1"},
    {"id": 6, "question": "What turns red in an acid, blue in a base and green in water? ", "answer": "Universal Indicator", "hint": "Bigger than a solar system indicator."},
    {"id": 7, "question": "If a substance behaves as both a solid and a liquid depending on what is done to it, what type of substance is it?", "answer": "Non-Newtonian", "hint": "It’s not non-einsteinian"},
    {"id": 8, "question": "If you put an empty can upside down in ice water it will collapse because the ________ outside the can is greater than it is inside.", "answer": "Pressure", "hint": "You might feel it if you start to run out of time in this game."},
    {"id": 9, "question": "Combustion is the chemical reaction occurs when a substance reacts with which element?", "answer": "Oxygen", "hint": "Breathe"},
    {"id": 10, "question": "What four letter word is shared by both softball and soap?", "answer": "Base", "hint": "Not the type of guitar or the fish"},
]

puzzle_positions = [(150, 150), (300, 120), (450, 140), (600, 150),
                    (160, 300), (300, 350), (450, 330), (600, 300),
                    (250, 500), (500, 500)]

solved_puzzles = [False] * len(puzzles)
hint_delays = [0] * len(puzzles) # Time when hint can appear
incorrect_attempts_count = [0] * len(puzzles) # New: track incorrect attempts per puzzle

input_active = False
user_input = ''
current_puzzle = None
start_time = 0 # Will be set when game starts
end_time = 0 # Will be set when game ends successfully
total_incorrect_attempts = 0 # New: total incorrect answers across all puzzles

game_over = False # New state for game completion
escape_code_active = False # New state for escape code input
escape_code_input = ''
escape_code_message = '' # For correct/incorrect messages

# CHANGED THE FINAL PUZZLE MESSAGE
ESCAPE_CODE_PROMPT = "Take the first letter of each of your answers. Find out the atomic numbers of each of the elements with the symbol corresponding to these letters and add them together. What is the answer?"
ESCAPE_CODE = "190" # The actual escape code

# --- Escape Door Setup ---
DOOR_X, DOOR_Y = 650, 500 # Example coordinates, adjust as needed
DOOR_WIDTH, DOOR_HEIGHT = 100, 100 # Example size, adjust as needed
door_rect = pygame.Rect(DOOR_X, DOOR_Y, DOOR_WIDTH, DOOR_HEIGHT)

# --- Game State ---
game_state = "START_SCREEN" # "START_SCREEN", "PLAYING", "GAME_OVER", "END_SCREEN"

# --- Text Wrapping Function ---
def wrap_text(surface, text, font_obj, max_width):
    words = text.split(' ')
    wrapped_lines = []
    current_line = []
    current_line_width = 0

    for word in words:
        test_line = " ".join(current_line + [word])
        # Use a dummy surface to measure text width without actually rendering
        # Using a dummy color (BLACK) here doesn't affect width calculation
        test_width = font_obj.render(test_line, True, BLACK).get_width() 

        if test_width < max_width:
            current_line.append(word)
        else:
            if current_line:
                wrapped_lines.append(" ".join(current_line))
            current_line = [word]
            
            if font_obj.render(word, True, BLACK).get_width() >= max_width and len(current_line) == 1:
                wrapped_lines.append(word)
                current_line = [] 
    
    if current_line:
        wrapped_lines.append(" ".join(current_line))
    
    return wrapped_lines


# --- Game Functions ---
def draw_timer():
    elapsed = time.time() - start_time
    remaining = max(0, TIMER_DURATION - int(elapsed))
    minutes = remaining // 60
    seconds = remaining % 60
    timer_text = font.render(f"Time Left: {minutes:02}:{seconds:02}", True, BLACK)
    screen.blit(timer_text, (10, 10))

def draw_input_box(input_text, x_pos, y_pos, width=500, height=30):
    pygame.draw.rect(screen, WHITE, (x_pos, y_pos, width, height))
    txt_surface = font.render(input_text, True, BLACK)
    screen.blit(txt_surface, (x_pos + 5, y_pos + 5))

def draw_hint_box(puzzle_box_x, puzzle_box_y, puzzle_box_height):
    global current_puzzle
    if current_puzzle is None:
        return

    i = current_puzzle["id"] - 1
    # Check if hint should appear (2 or more incorrect attempts AND delay passed)
    if incorrect_attempts_count[i] >= 2 and hint_delays[i] and time.time() >= hint_delays[i]:
        hint_text_content = "Hint: " + current_puzzle["hint"]

        # Hint box dimensions and position
        hint_box_width = puzzle_box_width # Same width as puzzle box
        hint_box_height = 80 # Fixed height for the hint box
        hint_box_x = puzzle_box_x
        # Position below input box, with more spacing (input box is at puzzle_box_y + puzzle_box_height + 10)
        hint_box_y = puzzle_box_y + puzzle_box_height + 10 + 30 + 10 # puzzle_box_y + puzzle_box_height + input_box_height + spacing

        # Draw the hint box background
        pygame.draw.rect(screen, HINT_BOX_COLOR, (hint_box_x, hint_box_y, hint_box_width, hint_box_height))
        pygame.draw.rect(screen, BLACK, (hint_box_x, hint_box_y, hint_box_width, hint_box_height), 2) # Border

        # Wrap and draw the hint text
        wrapped_hint_lines = wrap_text(screen, hint_text_content, hint_font, hint_box_width - 20) # 20px padding
        
        hint_text_y_offset = hint_box_y + 10 # Padding from top of hint box
        for line in wrapped_hint_lines:
            line_surface = hint_font.render(line, True, BLACK)
            line_rect = line_surface.get_rect(centerx=hint_box_x + hint_box_width // 2)
            screen.blit(line_surface, (line_rect.x, hint_text_y_offset))
            hint_text_y_offset += hint_font.get_linesize()


def draw_puzzle_completion_box():
    # Increased size for better fit
    box_width = 150 # Increased width
    box_height = 200 # Increased height
    box_x = WIDTH - box_width - 10 # 10 pixels from right edge
    box_y = 10 # 10 pixels from top edge

    pygame.draw.rect(screen, WHITE, (box_x, box_y, box_width, box_height), 0, 5) # Filled rectangle with rounded corners
    pygame.draw.rect(screen, BLACK, (box_x, box_y, box_width, box_height), 2, 5) # Border

    title_text = small_font.render("Puzzles Solved:", True, BLACK) # More descriptive title
    screen.blit(title_text, (box_x + 10, box_y + 5))

    indicator_size = 18 # Slightly larger indicators
    padding = 8 # Increased padding
    
    # ADJUSTMENT HERE: More vertical spacing after the title and adjust for numbers
    start_y = box_y + title_text.get_height() + 20 # Increased spacing from 15 to 20
    start_x = box_x + padding  # Define start_x here

    puzzles_per_row = 3
    row_gap = 10 # Increased vertical gap between rows

    for i in range(len(puzzles)):
        color = COMPLETED_PUZZLE_COLOR if solved_puzzles[i] else UNCOMPLETED_PUZZLE_COLOR
        puzzle_num_text = small_font.render(str(puzzles[i]["id"]), True, BLACK)

        col = i % puzzles_per_row
        row = i // puzzles_per_row
        
        indicator_x = start_x + (col * (indicator_size + padding + 10))
        # Ensure number text is placed above the square, and the square itself starts from start_y
        # Adjusted y-offset to prevent overlap with title
        indicator_y = start_y + (row * (indicator_size + row_gap + puzzle_num_text.get_height() + 5)) # Added 5 for extra space

        # Draw the square indicator
        pygame.draw.rect(screen, color, (indicator_x, indicator_y, indicator_size, indicator_size))
        pygame.draw.rect(screen, BLACK, (indicator_x, indicator_y, indicator_size, indicator_size), 1) # Border

        # Draw the puzzle number above the square
        num_text_width, num_text_height = puzzle_num_text.get_size()
        screen.blit(puzzle_num_text, (indicator_x + indicator_size // 2 - num_text_width // 2, indicator_y - num_text_height - 2))


def check_collision():
    global current_puzzle, input_active, user_input, escape_code_active, escape_code_input, escape_code_message

    char_rect = character_img.get_rect(topleft=(char_x, char_y))
    puzzle_interaction_radius = 20

    # Check for puzzle collision
    colliding_with_unsolved_puzzle = False
    for i, (px, py) in enumerate(puzzle_positions):
        if not solved_puzzles[i]:
            puzzle_rect = pygame.Rect(px - puzzle_interaction_radius,
                                      py - puzzle_interaction_radius,
                                      puzzle_interaction_radius * 2,
                                      puzzle_interaction_radius * 2)

            if char_rect.colliderect(puzzle_rect):
                colliding_with_unsolved_puzzle = True
                if not input_active or (current_puzzle is not None and current_puzzle["id"] - 1 != i):
                    current_puzzle = puzzles[i]
                    input_active = True
                    escape_code_active = False # Deactivate escape code input if a puzzle is activated
                    user_input = ''
                break

    if not colliding_with_unsolved_puzzle and input_active and current_puzzle:
        input_active = False
        current_puzzle = None
        user_input = ''

    # Check for escape door collision (only if all puzzles are solved)
    if all(solved_puzzles):
        if char_rect.colliderect(door_rect):
            # Only activate escape code input if not already active and not already focused on a puzzle
            if not input_active and not escape_code_active:
                escape_code_active = True
                escape_code_input = ''
                escape_code_message = ESCAPE_CODE_PROMPT
        # We REMOVED the block that turned off escape_code_active when not colliding
        # This allows the escape code box to stay open once triggered, until answered or another puzzle is hit.
    else: # If not all puzzles solved, ensure escape code input is off
        escape_code_active = False
        escape_code_input = ''
        escape_code_message = ''


def handle_puzzle_input():
    global input_active, user_input, solved_puzzles, current_puzzle, total_incorrect_attempts
    
    if current_puzzle is None:
        input_active = False
        return

    i = current_puzzle["id"] - 1
    if user_input.strip().lower() == current_puzzle["answer"].strip().lower():
        solved_puzzles[i] = True
        current_puzzle = None
        input_active = False
        user_input = ''
        incorrect_attempts_count[i] = 0 # Reset incorrect attempts for this puzzle
        hint_delays[i] = 0 # Reset hint delay once solved
    else:
        user_input = ''
        incorrect_attempts_count[i] += 1 # Increment incorrect attempts for this puzzle
        total_incorrect_attempts += 1 # Increment total incorrect attempts
        
        # Set hint delay to current time immediately after 2nd incorrect attempt
        if incorrect_attempts_count[i] == 2:
            hint_delays[i] = time.time() # Hint appears immediately
        elif incorrect_attempts_count[i] > 2:
             # If more than 2 incorrect attempts, ensure hint_delays[i] is set
             # This means if it was already set (from the 2nd attempt), it stays set.
             # If for some reason it got unset, this would set it again immediately.
             if hint_delays[i] == 0: 
                hint_delays[i] = time.time()


def handle_escape_code_input():
    global escape_code_active, escape_code_input, escape_code_message, game_over, end_time, total_incorrect_attempts
    if escape_code_input.strip() == ESCAPE_CODE: # Exact match, case-sensitive if needed, but numbers so okay
        escape_code_message = "Congratulations! You have escaped the Lab!"
        game_over = True # Signal to transition to end screen
        # We DO NOT set escape_code_active = False here immediately.
        # This allows the "Congratulations!" message to be visible in the box for a moment.
        end_time = time.time() # Record end time
    else:
        escape_code_message = "Incorrect Code. Try again."
        escape_code_input = '' # Clear input on incorrect attempt
        total_incorrect_attempts += 1 # Count incorrect attempt for final code too


# --- Start Screen Function ---
def draw_start_screen():
    screen.fill(BLACK) # Black background for start screen

    # Game Title
    title_text = title_font.render("ChemEscape", True, WHITE)
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
    screen.blit(title_text, title_rect)

    # Instructions Box
    instructions_box_width = WIDTH - 100 # 50 pixels padding on each side
    instructions_box_x = 50
    instructions_box_y = HEIGHT // 2 - 120 # Adjust start Y
    
    text_y_offset_calc = 10 # Padding from top of instructions_surface for calculation
    
    instructions_list = [
        "Welcome to ChemEscape! You are trapped in a mysterious lab.",
        "To escape, you must solve 10 chemistry puzzles.",
        "Walk your character (the green square) to a puzzle (small circles) to activate it.",
        "Type your answer in the box that appears and press ENTER.",
        "Hints will appear in a separate box after 2 incorrect attempts on a puzzle.",
        "You can move away from a puzzle to leave it unsolved for later.",
        "Once all puzzles are solved, find the exit door at the bottom-right and enter the escape code.",
        "Good luck and escape the lab!"
    ]
    
    for line_text in instructions_list:
        wrapped_lines = wrap_text(screen, line_text, font, instructions_box_width - 30)
        if wrapped_lines:
            text_y_offset_calc += len(wrapped_lines) * font.get_linesize()
            text_y_offset_calc += 5
        else:
            text_y_offset_calc += font.get_linesize() + 5

    instructions_box_height = text_y_offset_calc + 10

    instructions_surface = pygame.Surface((instructions_box_width, instructions_box_height), pygame.SRCALPHA)
    instructions_surface.fill((0, 0, 0, 150))

    text_y_offset = 10
    for line_text in instructions_list:
        bullet_point = "• "
        wrapped_lines = wrap_text(instructions_surface, line_text, font, instructions_box_width - 30)
        
        if wrapped_lines:
            bullet_surface = font.render(bullet_point, True, WHITE)
            instructions_surface.blit(bullet_surface, (5, text_y_offset))
            
            for i, wrapped_line in enumerate(wrapped_lines):
                line_surface = font.render(wrapped_line, True, WHITE)
                instructions_surface.blit(line_surface, (5 + bullet_surface.get_width(), text_y_offset))
                text_y_offset += font.get_linesize()
            text_y_offset += 5
        else:
            text_y_offset += font.get_linesize() + 5

    screen.blit(instructions_surface, (instructions_box_x, instructions_box_y))

    # Start Button
    start_button_text = font.render("Start Game", True, WHITE)
    start_button_rect = pygame.Rect(WIDTH // 2 - 75, HEIGHT - 100, 150, 50)

    mouse_pos = pygame.mouse.get_pos()
    button_color = BLUE
    if start_button_rect.collidepoint(mouse_pos):
        button_color = DARK_BLUE

    pygame.draw.rect(screen, button_color, start_button_rect, border_radius=10)
    text_rect = start_button_text.get_rect(center=start_button_rect.center)
    screen.blit(start_button_text, text_rect)

    return start_button_rect

# --- End Screen Function ---
def draw_end_screen():
    screen.fill(BLACK) # Black background for end screen

    # Overlay for a nice effect
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    # Congratulations message
    congrats_text = large_font.render("Congratulations!", True, GOLD)
    escaped_text = large_font.render("You have escaped the lab!", True, WHITE)
    
    congrats_rect = congrats_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
    escaped_rect = escaped_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
    
    screen.blit(congrats_text, congrats_rect)
    screen.blit(escaped_text, escaped_rect)

    # Time Taken
    time_taken_seconds = int(end_time - start_time)
    minutes = time_taken_seconds // 60
    seconds = time_taken_seconds % 60
    time_text = stats_font.render(f"Time Taken: {minutes:02}:{seconds:02}", True, WHITE)
    time_rect = time_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
    screen.blit(time_text, time_rect)

    # Incorrect Answers
    incorrect_text = stats_font.render(f"Incorrect Attempts: {total_incorrect_attempts}", True, WHITE)
    incorrect_rect = incorrect_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70))
    screen.blit(incorrect_text, incorrect_rect)

    # End Game Button
    end_button_text = font.render("End Game", True, WHITE)
    end_button_rect = pygame.Rect(WIDTH // 2 - 75, HEIGHT - 100, 150, 50)

    mouse_pos = pygame.mouse.get_pos()
    button_color = BLUE
    if end_button_rect.collidepoint(mouse_pos):
        button_color = DARK_BLUE

    pygame.draw.rect(screen, button_color, end_button_rect, border_radius=10)
    text_rect = end_button_text.get_rect(center=end_button_rect.center)
    screen.blit(end_button_text, text_rect)

    return end_button_rect


# --- Main Game Loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if game_state == "START_SCREEN":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    start_button_rect = draw_start_screen() # Ensure button is drawn before checking collision
                    if start_button_rect.collidepoint(event.pos):
                        game_state = "PLAYING"
                        start_time = time.time() # Start the timer when the game begins
        
        elif game_state == "PLAYING":
            if input_active: # If a puzzle is active
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        handle_puzzle_input()
                    elif event.key == pygame.K_BACKSPACE:
                        user_input = user_input[:-1]
                    else:
                        user_input += event.unicode
            
            elif escape_code_active: # If the escape code input is active
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        handle_escape_code_input()
                    elif event.key == pygame.K_BACKSPACE:
                        escape_code_input = escape_code_input[:-1]
                    else:
                        escape_code_input += event.unicode
        
        elif game_state == "END_SCREEN":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    end_button_rect = draw_end_screen() # Ensure button is drawn before checking collision
                    if end_button_rect.collidepoint(event.pos):
                        running = False # Quit the game

    if game_state == "START_SCREEN":
        start_button_rect = draw_start_screen() # Draw start screen and get button rect
    
    elif game_state == "PLAYING":
        screen.blit(lab_bg, (0, 0))
        screen.blit(character_img, (char_x, char_y))
        draw_timer()
        draw_puzzle_completion_box()

        # --- Character Movement (Always active in PLAYING state) ---
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]: char_x -= char_speed
        if keys[pygame.K_RIGHT]: char_x += char_speed
        if keys[pygame.K_UP]: char_y -= char_speed
        if keys[pygame.K_DOWN]: char_y += char_speed

        char_x = max(0, min(WIDTH - character_img.get_width(), char_x))
        char_y = max(0, min(HEIGHT - character_img.get_height(), char_y))

        check_collision()  

        # Define puzzle box dimensions for consistent positioning
        puzzle_box_width = WIDTH * 0.7
        puzzle_box_height = HEIGHT * 0.4
        puzzle_box_x = (WIDTH - puzzle_box_width) // 2
        puzzle_box_y = (HEIGHT - puzzle_box_height) // 2 - 50


        if input_active and current_puzzle:
            puzzle_bg_rect = pygame.Rect(puzzle_box_x, puzzle_box_y, puzzle_box_width, puzzle_box_height)
            pygame.draw.rect(screen, LIGHT_GREEN, puzzle_bg_rect)
            pygame.draw.rect(screen, BLACK, puzzle_bg_rect, 2) # Add border

            raw_question_lines = current_puzzle["question"].split("\n")
            
            text_wrap_width = puzzle_box_width - 40
            y_offset = puzzle_box_y + 20
            
            for segment in raw_question_lines:
                wrapped_lines = wrap_text(screen, segment, comic_sans_font, text_wrap_width)
                
                for line in wrapped_lines:
                    q_text = comic_sans_font.render(line, True, BLACK)
                    screen.blit(q_text, (puzzle_box_x + 20, y_offset))
                    y_offset += comic_sans_font.get_linesize()
                
                if "\n" in current_puzzle["question"] and raw_question_lines.index(segment) < len(raw_question_lines) - 1:
                     y_offset += 10

            input_box_y = puzzle_box_y + puzzle_box_height + 10
            input_box_width = puzzle_box_width
            input_box_x = puzzle_box_x
            draw_input_box(user_input, input_box_x, input_box_y, input_box_width, 30)

            # Draw hint box only if conditions are met
            draw_hint_box(puzzle_box_x, puzzle_box_y, puzzle_box_height)


        # Draw escape code input if active (only if all puzzles are solved)
        if escape_code_active and all(solved_puzzles):
            # Reusing puzzle box dimensions for consistency
            code_box_width = WIDTH * 0.7 
            code_box_height = HEIGHT * 0.4
            code_box_x = (WIDTH - code_box_width) // 2
            code_box_y = (HEIGHT - code_box_height) // 2 - 50

            pygame.draw.rect(screen, LIGHT_GREEN, (code_box_x, code_box_y, code_box_width, code_box_height))
            pygame.draw.rect(screen, BLACK, (code_box_x, code_box_y, code_box_width, code_box_height), 2)

            # Determine message color
            msg_color = BLACK
            if escape_code_message == ESCAPE_CODE_PROMPT:
                msg_color = BLACK
            elif "Congratulations" in escape_code_message:
                msg_color = (0, 150, 0) # Green for success
            else:
                msg_color = RED # Red for incorrect

            wrapped_escape_prompt_lines = wrap_text(screen, escape_code_message, comic_sans_font, code_box_width - 40)
            
            prompt_y_offset = code_box_y + 20
            for line in wrapped_escape_prompt_lines:
                prompt_text = comic_sans_font.render(line, True, msg_color)
                prompt_text_x = code_box_x + (code_box_width - prompt_text.get_width()) // 2
                screen.blit(prompt_text, (prompt_text_x, prompt_y_offset))
                prompt_y_offset += comic_sans_font.get_linesize() + 5

            # Only draw input box if not game over yet
            if not game_over: # Added this check
                input_box_y = prompt_y_offset + 10
                input_box_width_inner = code_box_width - 40
                input_box_x_inner = code_box_x + 20
                draw_input_box(escape_code_input, input_box_x_inner, input_box_y, input_box_width_inner)
            # If game_over, the input box is no longer needed, and the main loop will handle the state change.
        
        # New: State transition check after all drawing and logic for PLAYING state
        if game_over:
            game_state = "END_SCREEN"

    elif game_state == "END_SCREEN":
        end_button_rect = draw_end_screen()

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
