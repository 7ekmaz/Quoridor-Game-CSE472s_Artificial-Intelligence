import pygame
import sys
from game_logic import QuoridorGame
from ai_agent import QuoridorAI

# Constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 750 # Increased for better UI
BOARD_SIZE = 500
OFFSET = 50
CELL_SIZE = 40
GAP_SIZE = 10
TOTAL_CELL_SIZE = CELL_SIZE + GAP_SIZE

# Colors
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GRAY = (200, 200, 200)
RED = (200, 60, 60)
BLUE = (60, 60, 200)
GREEN = (50, 200, 50)
HOVER_COLOR = (100, 255, 100)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 149, 237)

class QuoridorGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Quoridor Ultimate")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 20)
        self.title_font = pygame.font.SysFont('Arial', 40, bold=True)
        
        self.game = QuoridorGame()
        self.ai = None
        
        # State: 'MENU', 'GAME', 'GAME_OVER'
        self.state = 'MENU'
        self.mode = 'PvP' # or 'PvAI'
        self.difficulty = 'Medium'
        self.wall_orientation = 'V' 

        self.notification_text = ""
        self.notification_timer = 0

    def show_notification(self, text):
        self.notification_text = text
        self.notification_timer = 60  # Show for 60 frames (approx 2 seconds)

    def draw_text(self, text, font, color, x, y, align="center"):
        surf = font.render(text, True, color)
        rect = surf.get_rect()
        if align == "center": rect.center = (x, y)
        elif align == "left": rect.topleft = (x, y)
        self.screen.blit(surf, rect)
        return rect

    def draw_button(self, text, x, y, w, h, active=False):
        mouse = pygame.mouse.get_pos()
        rect = pygame.Rect(x, y, w, h)
        color = BUTTON_HOVER if rect.collidepoint(mouse) or active else BUTTON_COLOR
        pygame.draw.rect(self.screen, color, rect, border_radius=5)
        self.draw_text(text, self.font, WHITE, x + w//2, y + h//2)
        return rect

    def run_menu(self):
        self.screen.fill(BLACK)
        self.draw_text("QUORIDOR", self.title_font, WHITE, SCREEN_WIDTH//2, 100)
        
        # Mode Selection
        if self.draw_button("Human vs Human", 150, 200, 300, 50, self.mode == 'PvP').collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
            self.mode = 'PvP'
            
        if self.draw_button("Human vs AI", 150, 270, 300, 50, self.mode == 'PvAI').collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
            self.mode = 'PvAI'

        # Difficulty (Only if AI)
        if self.mode == 'PvAI':
            self.draw_text("AI Difficulty:", self.font, GRAY, SCREEN_WIDTH//2, 350)
            if self.draw_button("Easy", 100, 380, 100, 40, self.difficulty == 'Easy').collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
                self.difficulty = 'Easy'
            if self.draw_button("Medium", 250, 380, 100, 40, self.difficulty == 'Medium').collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
                self.difficulty = 'Medium'
            if self.draw_button("Hard", 400, 380, 100, 40, self.difficulty == 'Hard').collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
                self.difficulty = 'Hard'

        # Start Button
        if self.draw_button("START GAME", 200, 500, 200, 60).collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
            self.game.reset_game()
            if self.mode == 'PvAI':
                self.ai = QuoridorAI(self.game, player_id=2, difficulty=self.difficulty)
            else:
                self.ai = None
            self.state = 'GAME'
            pygame.time.delay(200) # Debounce

    def get_smart_coords(self, mouse_pos):
        """
        Determines if mouse is hovering over a cell (Move) or a gap (Wall).
        Automatically sets orientation based on proximity to gap.
        """
        x, y = mouse_pos
        x -= OFFSET
        y -= OFFSET
        
        # Check bounds
        if x < 0 or y < 0 or x > BOARD_SIZE or y > BOARD_SIZE:
            return None, None, None, None

        col = x // TOTAL_CELL_SIZE
        row = y // TOTAL_CELL_SIZE
        rel_x = x % TOTAL_CELL_SIZE
        rel_y = y % TOTAL_CELL_SIZE

        # Tolerance for "snapping" to a gap (15 pixels)
        GAP_TOLERANCE = 15 
        
        # 1. Check for Vertical Wall Gap (Between columns)
        # If we are near the right edge of a cell, we are near the vertical gap of this col
        if rel_x > (CELL_SIZE - GAP_TOLERANCE):
            return int(row), int(col), 'wall', 'V'
            
        # 2. Check for Horizontal Wall Gap (Between rows)
        if rel_y > (CELL_SIZE - GAP_TOLERANCE):
            return int(row), int(col), 'wall', 'H'

        # 3. Otherwise, it's a cell hover
        if rel_x < CELL_SIZE and rel_y < CELL_SIZE:
            return int(row), int(col), 'cell', None

        return int(row), int(col), 'gap', None # Just empty gap space

    def run_game(self):
        # 1. AI Turn Handling
        if self.mode == 'PvAI' and self.game.current_turn == 2 and not self.game.winner:
            # Simple delay to make it feel natural
            pygame.display.flip() 
            pygame.time.delay(500)
            
            action = self.ai.get_move()
            if action:
                if action[0] == 'move':
                    self.game.move_pawn(2, action[1], action[2])
                elif action[0] == 'wall':
                    # AI might suggest invalid wall, so we try; if fails, fallback happens in AI logic
                    # ideally AI logic is perfect, but for safety:
                    self.game.place_wall(2, action[1], action[2], action[3])
        
        # 2. Draw
        self.screen.fill(BLACK)
        self.draw_board_grid()
        self.draw_placed_items()
        self.draw_hud()

        # 3. Smart Hover Logic
        mouse_pos = pygame.mouse.get_pos()
        r, c, type_, orient = self.get_smart_coords(mouse_pos)
        
        if not self.game.winner and r is not None:
            if type_ == 'wall' and orient:
                self.draw_ghost_wall(r, c, orient)
            elif type_ == 'cell':
                # Highlight cell
                cx = OFFSET + c * TOTAL_CELL_SIZE
                cy = OFFSET + r * TOTAL_CELL_SIZE
                pygame.draw.rect(self.screen, (50, 50, 50), (cx, cy, CELL_SIZE, CELL_SIZE), 2)

        # 4. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_z: self.game.undo() # Undo
                if event.key == pygame.K_y: self.game.redo() # Redo
                if event.key == pygame.K_s: self.game.save_game_to_file() # Save
                if event.key == pygame.K_l: self.game.load_game_from_file() # Load
                if event.key == pygame.K_m: self.state = 'MENU' # Back to Menu

            if event.type == pygame.MOUSEBUTTONDOWN and not self.game.winner:
                # Disable P2 input if AI mode
                if self.mode == 'PvAI' and self.game.current_turn == 2: continue

                if event.button == 1: # Left Click handles BOTH now based on hover
                    if type_ == 'cell':
                        self.game.move_pawn(self.game.current_turn, r, c)
                    elif type_ == 'wall':
                        self.game.place_wall(self.game.current_turn, r, c, orient)
        
            if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s: 
                        if self.game.save_game_to_file():
                            self.show_notification("GAME SAVED")
                        else:
                            self.show_notification("SAVE FAILED")
                            
                    if event.key == pygame.K_l: 
                        if self.game.load_game_from_file():
                            self.show_notification("GAME LOADED")
                        else:
                            self.show_notification("LOAD FAILED")

    def draw_board_grid(self):
        for r in range(9):
            for c in range(9):
                x = OFFSET + c * TOTAL_CELL_SIZE
                y = OFFSET + r * TOTAL_CELL_SIZE
                color = GRAY
                if r == 0: color = (180, 180, 200) # P2 Goal Zone
                if r == 8: color = (200, 180, 180) # P1 Goal Zone
                pygame.draw.rect(self.screen, color, (x, y, CELL_SIZE, CELL_SIZE))

    def draw_placed_items(self):
        # Walls
        for r, c, orient in self.game.placed_walls:
            self.draw_single_wall(r, c, orient, (139, 69, 19)) # Brown
            
        # Pawns
        for pid, (r, c) in self.game.player_positions.items():
            cx = OFFSET + c * TOTAL_CELL_SIZE + CELL_SIZE//2
            cy = OFFSET + r * TOTAL_CELL_SIZE + CELL_SIZE//2
            color = RED if pid == 1 else BLUE
            pygame.draw.circle(self.screen, color, (cx, cy), CELL_SIZE//2 - 4)

    def draw_single_wall(self, r, c, orient, color):
        x = OFFSET + c * TOTAL_CELL_SIZE
        y = OFFSET + r * TOTAL_CELL_SIZE
        
        if orient == 'V':
            wx = x + CELL_SIZE
            wy = y
            w, h = GAP_SIZE, (2 * CELL_SIZE) + GAP_SIZE
        else:
            wx = x
            wy = y + CELL_SIZE
            w, h = (2 * CELL_SIZE) + GAP_SIZE, GAP_SIZE
        
        pygame.draw.rect(self.screen, color, (wx, wy, w, h))

    def draw_ghost_wall(self, r, c, orient):
        x = OFFSET + c * TOTAL_CELL_SIZE
        y = OFFSET + r * TOTAL_CELL_SIZE
        if orient == 'V':
            wx = x + CELL_SIZE; wy = y
            w, h = GAP_SIZE, (2 * CELL_SIZE) + GAP_SIZE
        else:
            wx = x; wy = y + CELL_SIZE
            w, h = (2 * CELL_SIZE) + GAP_SIZE, GAP_SIZE
            
        s = pygame.Surface((w, h))
        s.set_alpha(100) # Transparency
        s.fill(GREEN)
        self.screen.blit(s, (wx, wy))

    def draw_hud(self):
        turn_txt = f"Turn: {'RED' if self.game.current_turn == 1 else 'BLUE'}"
        self.draw_text(turn_txt, self.font, WHITE, 100, 620)
        
        self.draw_text(f"Red Walls: {self.game.walls_left[1]}", self.font, RED, 300, 620)
        self.draw_text(f"Blue Walls: {self.game.walls_left[2]}", self.font, BLUE, 500, 620)
        
        info = "Z: Undo | Y: Redo | S: Save | L: Load | M: Menu"
        self.draw_text(info, pygame.font.SysFont('Arial', 16), GRAY, SCREEN_WIDTH//2, 660)

        if self.game.winner:
            self.draw_text(f"PLAYER {self.game.winner} WINS!", self.title_font, (255, 215, 0), SCREEN_WIDTH//2, SCREEN_HEIGHT//2)

        # --- Notification Overlay ---
        if self.notification_timer > 0:
            self.notification_timer -= 1
            # Draw a semi-transparent box
            box_rect = pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 30, 200, 60)
            s = pygame.Surface((200, 60))
            s.set_alpha(200)
            s.fill((0, 0, 0))
            self.screen.blit(s, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 30))
            
            # Draw Text
            self.draw_text(self.notification_text, self.font, (0, 255, 0), SCREEN_WIDTH//2, SCREEN_HEIGHT//2)

    def main_loop(self):
        while True:
            if self.state == 'MENU':
                self.run_menu()
            elif self.state == 'GAME':
                self.run_game()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            pygame.display.flip()
            self.clock.tick(30)

if __name__ == "__main__":
    gui = QuoridorGUI()
    gui.main_loop()