import pygame
import sys
from game_logic import QuoridorGame


# --- VISUAL CONSTANTS ---
SCREEN_WIDTH = 700  # Wider for better spacing
SCREEN_HEIGHT = 800
OFFSET_X = 100      # Center the board horizontally
OFFSET_Y = 100      # Center the board vertically
CELL_SIZE = 50      # Larger cells
GAP_SIZE = 12
TOTAL_CELL_SIZE = CELL_SIZE + GAP_SIZE
BOARD_PIXEL_SIZE = 9 * TOTAL_CELL_SIZE - GAP_SIZE

# --- MODERN COLOR PALETTE ---
# Backgrounds
BG_COLOR = (40, 44, 52)         # Dark Blue-Grey (VS Code style)
BOARD_BG = (33, 37, 43)         # Slightly darker for board base

# Cells
CELL_COLOR = (171, 178, 191)    # Light Grey
CELL_HIGHLIGHT = (200, 200, 200) # Lighter when hovering
GOAL_P1_COLOR = (224, 108, 117) # Soft Red tint for P1 Goal
GOAL_P2_COLOR = (97, 175, 239)  # Soft Blue tint for P2 Goal

# Players (Spherical look)
P1_COLOR = (224, 108, 117)      # Soft Red
P1_SHINE = (255, 180, 180)      # Highlight for 3D effect
P2_COLOR = (97, 175, 239)       # Soft Blue
P2_SHINE = (180, 220, 255)      # Highlight for 3D effect

# Walls
WALL_COLOR = (229, 192, 123)    # Gold/Wood color
WALL_SHADOW = (20, 20, 20)      # For depth
GHOST_WALL_COLOR = (152, 195, 121) # Soft Green

# --- ADD THESE TO YOUR COLOR CONSTANTS ---
BUTTON_COLOR = (70, 80, 100)    # Slate Blue-Grey
BUTTON_HOVER = (90, 100, 120)   # Lighter Slate
BUTTON_ACTIVE = (60, 120, 180)  # Bright Blue (for selected options)
BUTTON_SHADOW = (30, 30, 40)    # Dark Shadow
TEXT_COLOR = (220, 220, 220)    # Off-White

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

        # Enhanced Notification State
        self.notification_text = ""
        self.notification_timer = 0
        self.notification_color = (50, 200, 50) # Default Green

    def show_notification(self, text, color=(50, 200, 50)):
        self.notification_text = text
        self.notification_color = color
        self.notification_timer = 60 # 2 seconds (at 30 FPS)

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
        
        # 1. Determine Color
        if active:
            color = BUTTON_ACTIVE
        elif rect.collidepoint(mouse):
            color = BUTTON_HOVER
        else:
            color = BUTTON_COLOR
            
        # 2. Draw Shadow (Offset by 4 pixels)
        # We don't draw shadow if the button is active (pressed in)
        if not active:
            shadow_rect = pygame.Rect(x + 4, y + 4, w, h)
            pygame.draw.rect(self.screen, BUTTON_SHADOW, shadow_rect, border_radius=8)
            
            # If hovering, shift the main button up slightly for "pop" effect
            if rect.collidepoint(mouse):
                rect.y -= 2 
                rect.x -= 2
        else:
            # If active (pressed), shift button DOWN to cover shadow
            rect.y += 2
            rect.x += 2

        # 3. Draw Main Button
        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        
        # 4. Draw Text (Centered)
        # Using white or off-white for better contrast
        self.draw_text(text, self.font, TEXT_COLOR, rect.centerx, rect.centery)
        
        return rect

    def run_menu(self):
        # 1. Fill with the new Dark Blue-Grey background
        self.screen.fill(BG_COLOR)
        
        # 2. Draw Title with a Shadow for depth
        title_text = "QUORIDOR"
        # Shadow (Offset by 3px)
        self.draw_text(title_text, self.title_font, (20, 20, 20), SCREEN_WIDTH//2 + 3, 100 + 3)
        # Main Text (White/Gold)
        self.draw_text(title_text, self.title_font, (229, 192, 123), SCREEN_WIDTH//2, 100)
        
        # 3. Mode Selection Buttons
        # We check collision and click inside the draw_button call logic roughly, 
        # but here we need to capture the rect to check clicks explicitly.
        
        # Mode: PvP
        pvp_rect = self.draw_button("Human vs Human", 200, 250, 300, 60, active=(self.mode == 'PvP'))
        if pvp_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
            self.mode = 'PvP'
            
        # Mode: PvAI
        ai_rect = self.draw_button("Human vs AI", 200, 330, 300, 60, active=(self.mode == 'PvAI'))
        if ai_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
            self.mode = 'PvAI'

        # 4. Difficulty Buttons (Only show if PvAI is selected)
        if self.mode == 'PvAI':
            self.draw_text("AI Difficulty", self.font, (150, 160, 170), SCREEN_WIDTH//2, 430)
            
            # Three smaller buttons in a row
            easy_rect = self.draw_button("Easy", 120, 460, 140, 50, active=(self.difficulty == 'Easy'))
            if easy_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
                self.difficulty = 'Easy'
                
            med_rect = self.draw_button("Medium", 280, 460, 140, 50, active=(self.difficulty == 'Medium'))
            if med_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
                self.difficulty = 'Medium'

            hard_rect = self.draw_button("Hard", 440, 460, 140, 50, active=(self.difficulty == 'Hard'))
            if hard_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
                self.difficulty = 'Hard'

        # 5. Start Game Button (Big Green/Gold button at bottom)
        start_rect = self.draw_button("START GAME", 225, 600, 250, 70)
        
        if start_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
            self.game.reset_game()
            if self.mode == 'PvAI':
                # Re-initialize AI with chosen difficulty
                from ai_agent import QuoridorAI 
                self.ai = QuoridorAI(self.game, player_id=2, difficulty=self.difficulty)
            else:
                self.ai = None
            self.state = 'GAME'
            pygame.time.delay(200) # Prevent accidental double clicks

    def get_smart_coords(self, mouse_pos):
        """
        Determines if mouse is hovering over a cell (Move) or a gap (Wall).
        """
        x, y = mouse_pos
        
        # 1. Update: Use separate X and Y offsets
        x -= OFFSET_X
        y -= OFFSET_Y
        
        # 2. Update: Use new board pixel size constant
        if x < 0 or y < 0 or x > BOARD_PIXEL_SIZE or y > BOARD_PIXEL_SIZE:
            return None, None, None, None

        col = x // TOTAL_CELL_SIZE
        row = y // TOTAL_CELL_SIZE
        rel_x = x % TOTAL_CELL_SIZE
        rel_y = y % TOTAL_CELL_SIZE

        # Tolerance for "snapping"
        GAP_TOLERANCE = 15 
        
        # 3. Check for Vertical Wall Gap (Near right edge of cell)
        if rel_x > (CELL_SIZE - GAP_TOLERANCE):
            # Ensure we aren't at the very right edge of the board (invalid wall)
            if col < 8: 
                return int(row), int(col), 'wall', 'V'
            
        # 4. Check for Horizontal Wall Gap (Near bottom edge of cell)
        if rel_y > (CELL_SIZE - GAP_TOLERANCE):
            # Ensure we aren't at the very bottom edge (invalid wall)
            if row < 8:
                return int(row), int(col), 'wall', 'H'

        # 5. Cell Hover
        if rel_x < CELL_SIZE and rel_y < CELL_SIZE:
            return int(row), int(col), 'cell', None

        return int(row), int(col), 'gap', None

    def run_game(self):
        # 1. AI Turn Handling
        # We process this before drawing so the AI moves immediately if ready
        if self.mode == 'PvAI' and self.game.current_turn == 2 and not self.game.winner:
            # Force a display update so the user sees their own move before the AI thinks
            pygame.display.flip() 
            
            # Small delay for natural feel
            pygame.time.delay(100) 
            pygame.event.pump() # Process internal events so window doesn't freeze
            
            action = self.ai.get_move()
            if action:
                if action[0] == 'move':
                    self.game.move_pawn(2, action[1], action[2])
                elif action[0] == 'wall':
                    # AI might suggest invalid wall, so we try; if fails, fallback happens in AI logic
                    self.game.place_wall(2, action[1], action[2], action[3])
        
        # 2. Draw
        self.screen.fill(BG_COLOR) # Use the new Dark Blue-Grey background
        self.draw_board_grid()
        self.draw_placed_items()
        self.draw_hud() # Includes the new notification overlay

        # 3. Smart Hover Logic
        mouse_pos = pygame.mouse.get_pos()
        r, c, type_, orient = self.get_smart_coords(mouse_pos)
        
        if not self.game.winner and r is not None:
            if type_ == 'wall' and orient:
                # Draw the Green Ghost Wall
                self.draw_ghost_wall(r, c, orient)
                
            elif type_ == 'cell':
                # Highlight cell (Using updated OFFSET_X/Y and CELL_HIGHLIGHT)
                cx = OFFSET_X + c * TOTAL_CELL_SIZE
                cy = OFFSET_Y + r * TOTAL_CELL_SIZE
                
                # Draw a rounded highlight border
                rect = pygame.Rect(cx, cy, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, CELL_HIGHLIGHT, rect, 3, border_radius=8)

        # 4. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
                
            if event.type == pygame.KEYDOWN:
                # Consolidated Key Checks
                if event.key == pygame.K_z: 
                    if self.mode == 'PvAI':
                        # In AI mode, we must undo TWICE to get back to Human turn
                        # (Undo AI move + Undo Player move)
                        if len(self.game.history) >= 2:
                            self.game.undo() # Undo AI
                            self.game.undo() # Undo Human
                            self.show_notification("UNDO (2 Steps)", color=(200, 200, 50))
                        else:
                             self.show_notification("CANNOT UNDO", color=(200, 50, 50))
                    else:
                        # In PvP, we only undo once (to the other human's turn)
                        if self.game.undo(): 
                            self.show_notification("UNDO")
                
                if event.key == pygame.K_y: 
                    if self.mode == 'PvAI':
                        # Redo twice to keep sync
                        if len(self.game.redo_stack) >= 2:
                            self.game.redo()
                            self.game.redo()
                            self.show_notification("REDO (2 Steps)")
                    else:
                        if self.game.redo(): 
                            self.show_notification("REDO")
                
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
                        
                if event.key == pygame.K_m: 
                    self.state = 'MENU' # Back to Menu

            if event.type == pygame.MOUSEBUTTONDOWN and not self.game.winner:
                if self.mode == 'PvAI' and self.game.current_turn == 2: continue

                if event.button == 1:
                    success = False # Track if the move worked
                    
                    if type_ == 'cell':
                        success = self.game.move_pawn(self.game.current_turn, r, c)
                    elif type_ == 'wall':
                        success = self.game.place_wall(self.game.current_turn, r, c, orient)
                    
                    # VISUAL FEEDBACK
                    if not success:
                        # ERROR: Red Notification
                        self.show_notification("Invalid Move!", color=(220, 60, 60))
                    else:
                        # SUCCESS: Optional sound or subtle effect
                        pass

                # Right Click to Rotate (Quality of Life)
                elif event.button == 3:
                    # Toggle V <-> H
                    self.wall_orientation = 'H' if self.wall_orientation == 'V' else 'V'
                    self.show_notification(f"Orientation: {self.wall_orientation}", color=(100, 100, 200))

    def draw_board_grid(self):
        # 1. Draw Board Background Base
        rect = pygame.Rect(OFFSET_X - 10, OFFSET_Y - 10, 
                           BOARD_PIXEL_SIZE + 20, BOARD_PIXEL_SIZE + 20)
        pygame.draw.rect(self.screen, BOARD_BG, rect, border_radius=15)

        # 2. Draw Coordinates (1-9 and A-I)
        coord_font = pygame.font.SysFont('Consolas', 18, bold=True)
        
        # Draw Letters (Columns A-I)
        letters = "ABCDEFGHI"
        for c in range(9):
            x = OFFSET_X + c * TOTAL_CELL_SIZE + CELL_SIZE // 2
            text = coord_font.render(letters[c], True, (100, 100, 100))
            text_rect = text.get_rect(center=(x, OFFSET_Y - 30))
            self.screen.blit(text, text_rect)
            
        # Draw Numbers (Rows 1-9)
        for r in range(9):
            y = OFFSET_Y + r * TOTAL_CELL_SIZE + CELL_SIZE // 2
            text = coord_font.render(str(r + 1), True, (100, 100, 100))
            text_rect = text.get_rect(center=(OFFSET_X - 30, y))
            self.screen.blit(text, text_rect)

        # 3. Draw Cells
        for r in range(9):
            for c in range(9):
                x = OFFSET_X + c * TOTAL_CELL_SIZE
                y = OFFSET_Y + r * TOTAL_CELL_SIZE
                
                # Default color
                color = CELL_COLOR
                
                # Tint Goal Rows slightly
                if r == 0: color = (120, 140, 160) # P2 Target Zone
                if r == 8: color = (160, 120, 120) # P1 Target Zone
                
                # Mouse Hover Highlight
                mouse_pos = pygame.mouse.get_pos()
                hr, hc, type_, _ = self.get_smart_coords(mouse_pos)
                if type_ == 'cell' and hr == r and hc == c:
                    color = CELL_HIGHLIGHT

                # Draw Rounded Rect
                pygame.draw.rect(self.screen, color, (x, y, CELL_SIZE, CELL_SIZE), border_radius=8)

    def draw_placed_items(self):
        # 1. Draw All Placed Walls
        # We iterate through the set of walls stored in the game logic
        for r, c, orient in self.game.placed_walls:
            # Use the Gold/Wood color defined in our modern palette
            self.draw_single_wall(r, c, orient, WALL_COLOR)

        # 2. Draw the Pawns (Players)
        self.draw_pawns()

    def draw_pawns(self):
        # We need this function too, using the new offsets and 3D look
        for pid, (r, c) in self.game.player_positions.items():
            cx = OFFSET_X + c * TOTAL_CELL_SIZE + CELL_SIZE // 2
            cy = OFFSET_Y + r * TOTAL_CELL_SIZE + CELL_SIZE // 2
            radius = CELL_SIZE // 2 - 8
            
            # Base Color
            color = P1_COLOR if pid == 1 else P2_COLOR
            pygame.draw.circle(self.screen, color, (cx, cy), radius)
            
            # "Shine" (Reflection) - Top left offset for 3D effect
            shine_color = P1_SHINE if pid == 1 else P2_SHINE
            pygame.draw.circle(self.screen, shine_color, (cx - 5, cy - 5), radius // 3)
            
            # Dark Outline for contrast
            pygame.draw.circle(self.screen, (30, 30, 30), (cx, cy), radius, 2)

    def draw_single_wall(self, r, c, orient, color, is_ghost=False):
        x = OFFSET_X + c * TOTAL_CELL_SIZE
        y = OFFSET_Y + r * TOTAL_CELL_SIZE
        
        if orient == 'V':
            wx = x + CELL_SIZE
            wy = y
            w, h = GAP_SIZE, (2 * CELL_SIZE) + GAP_SIZE
        else: # 'H'
            wx = x
            wy = y + CELL_SIZE
            w, h = (2 * CELL_SIZE) + GAP_SIZE, GAP_SIZE
        
        # 1. Draw Shadow (Offset by 3 pixels)
        if not is_ghost:
            shadow_rect = pygame.Rect(wx + 3, wy + 3, w, h)
            pygame.draw.rect(self.screen, WALL_SHADOW, shadow_rect, border_radius=4)

        # 2. Draw Main Wall
        if is_ghost:
            # Ghost needs surface for transparency
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            s.fill((*color, 150)) # Add alpha channel
            self.screen.blit(s, (wx, wy))
        else:
            pygame.draw.rect(self.screen, color, (wx, wy, w, h), border_radius=4)
            # Add a subtle highlight line on top
            pygame.draw.line(self.screen, (255, 255, 255), (wx + 2, wy + 2), (wx + w - 2, wy + 2), 1)

    def draw_single_wall(self, r, c, orient, color, is_ghost=False):
        # 1. Calculate Grid Position using new Offsets
        x = OFFSET_X + c * TOTAL_CELL_SIZE
        y = OFFSET_Y + r * TOTAL_CELL_SIZE
        
        # 2. Determine Wall Dimensions based on Orientation
        if orient == 'V':
            # Vertical wall is to the RIGHT of column c
            wx = x + CELL_SIZE
            wy = y
            w, h = GAP_SIZE, (2 * CELL_SIZE) + GAP_SIZE
        else: # 'H'
            # Horizontal wall is BELOW row r
            wx = x
            wy = y + CELL_SIZE
            w, h = (2 * CELL_SIZE) + GAP_SIZE, GAP_SIZE
        
        # 3. Draw Shadow (gives depth)
        # We offset the shadow by 3 pixels. We don't draw shadows for ghosts.
        if not is_ghost:
            shadow_rect = pygame.Rect(wx + 3, wy + 3, w, h)
            pygame.draw.rect(self.screen, WALL_SHADOW, shadow_rect, border_radius=4)

        # 4. Draw Main Wall
        if is_ghost:
            # Ghost walls need transparency, so we use a separate Surface
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            s.fill((*color, 150)) # Add alpha (transparency) to the RGB color
            self.screen.blit(s, (wx, wy))
        else:
            # Real walls are solid
            pygame.draw.rect(self.screen, color, (wx, wy, w, h), border_radius=4)
            
            # Optional: Add a subtle 1px white highlight on top for extra 3D pop
            pygame.draw.line(self.screen, (255, 255, 255), (wx + 2, wy + 2), (wx + w - 2, wy + 2), 1)

    def draw_ghost_wall(self, r, c, orient):
        # Delegate to the main wall function, passing the specific Ghost Color and Flag
        self.draw_single_wall(r, c, orient, GHOST_WALL_COLOR, is_ghost=True)

    def draw_hud(self):
        # --- 1. TOP HEADER (Turn Info) ---
        turn_color = P1_COLOR if self.game.current_turn == 1 else P2_COLOR
        turn_text = f"PLAYER {self.game.current_turn}'S TURN"
        
        # Badge Dimensions
        badge_w, badge_h = 240, 50
        badge_x = SCREEN_WIDTH // 2 - badge_w // 2
        badge_y = 25
        
        # Badge Shadow & Background
        pygame.draw.rect(self.screen, (20, 20, 30), (badge_x + 4, badge_y + 4, badge_w, badge_h), border_radius=25)
        pygame.draw.rect(self.screen, turn_color, (badge_x, badge_y, badge_w, badge_h), border_radius=25)
        self.draw_text(turn_text, self.font, (255, 255, 255), SCREEN_WIDTH // 2, badge_y + badge_h // 2)

        # --- 2. BOTTOM FOOTER (Stats & Controls) ---
        # Footer Background
        pygame.draw.rect(self.screen, BOARD_BG, (0, SCREEN_HEIGHT - 90, SCREEN_WIDTH, 90))
        
        # Wall Counts (Aligned nicely)
        self.draw_text(f"P1 Walls: {self.game.walls_left[1]}", self.font, P1_COLOR, 150, SCREEN_HEIGHT - 60)
        self.draw_text(f"P2 Walls: {self.game.walls_left[2]}", self.font, P2_COLOR, SCREEN_WIDTH - 150, SCREEN_HEIGHT - 60)
        
        # FORMALIZED CONTROLS TEXT
        # Removed "Rotate" since it's automatic. Added Save/Load/Undo clearly.
        controls_text = "Left Click: Interact   •   S: Save Game   •   L: Load Game   •   Z: Undo"
        self.draw_text(controls_text, pygame.font.SysFont('Arial', 14), (170, 180, 190), SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30)

        # --- 3. NOTIFICATION POP-UP (Toast) ---
        if self.notification_timer > 0:
            self.notification_timer -= 1
            pop_w, pop_h = 300, 60
            pop_x = SCREEN_WIDTH // 2 - pop_w // 2
            pop_y = 100 
            
            # Shadow & Box
            pygame.draw.rect(self.screen, (0, 0, 0), (pop_x + 4, pop_y + 4, pop_w, pop_h), border_radius=15)
            pygame.draw.rect(self.screen, self.notification_color, (pop_x, pop_y, pop_w, pop_h), border_radius=15)
            self.draw_text(self.notification_text, self.font, (255, 255, 255), SCREEN_WIDTH // 2, pop_y + pop_h // 2)

        # --- 4. WINNER OVERLAY ---
        if self.game.winner:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((20, 20, 25))
            self.screen.blit(overlay, (0,0))
            
            win_msg = f"PLAYER {self.game.winner} WINS!"
            win_col = P1_COLOR if self.game.winner == 1 else P2_COLOR
            
            self.draw_text(win_msg, self.title_font, (0, 0, 0), SCREEN_WIDTH//2 + 4, SCREEN_HEIGHT//2 - 20 + 4)
            self.draw_text(win_msg, self.title_font, win_col, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20)
            
            # Updated Menu Button
            menu_rect = self.draw_button("Return to Menu", SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 50, 200, 50, active=True)
            
            # Check for click on the "Return to Menu" button
            if pygame.mouse.get_pressed()[0] and menu_rect.collidepoint(pygame.mouse.get_pos()):
                self.state = 'MENU'

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