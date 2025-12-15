import collections
import copy
import pickle  # For saving/loading
import random

class QuoridorGame:
    def __init__(self):
        self.rows = 9
        self.cols = 9
        self.reset_game()

    def reset_game(self):
        self.player_positions = {1: (0, 4), 2: (8, 4)}
        self.walls_left = {1: 10, 2: 10}
        self.current_turn = 1
        self.winner = None
        self.board_graph = self._initialize_graph()
        self.placed_walls = set()
        
        # Bonus: History for Undo/Redo
        self.history = []     # Stack of previous states
        self.redo_stack = []  # Stack of undone states

    def _initialize_graph(self):
        graph = collections.defaultdict(set)
        for r in range(self.rows):
            for c in range(self.cols):
                if r > 0: graph[(r, c)].add((r - 1, c))
                if r < self.rows - 1: graph[(r, c)].add((r + 1, c))
                if c > 0: graph[(r, c)].add((r, c - 1))
                if c < self.cols - 1: graph[(r, c)].add((r, c + 1))
        return graph

    def save_state(self):
        """Pushes current state to history stack before a move."""
        state = {
            'player_positions': copy.deepcopy(self.player_positions),
            'walls_left': copy.deepcopy(self.walls_left),
            'current_turn': self.current_turn,
            'board_graph': copy.deepcopy(self.board_graph),
            'placed_walls': copy.deepcopy(self.placed_walls),
            'winner': self.winner
        }
        self.history.append(state)
        self.redo_stack.clear() # Clear redo on new move

    def restore_state(self, state):
        """Restores game to a specific state dict."""
        self.player_positions = state['player_positions']
        self.walls_left = state['walls_left']
        self.current_turn = state['current_turn']
        self.board_graph = state['board_graph']
        self.placed_walls = state['placed_walls']
        self.winner = state['winner']

    def undo(self):
        if not self.history: return False
        
        # Save current state to redo stack first
        current_state = {
            'player_positions': copy.deepcopy(self.player_positions),
            'walls_left': copy.deepcopy(self.walls_left),
            'current_turn': self.current_turn,
            'board_graph': copy.deepcopy(self.board_graph),
            'placed_walls': copy.deepcopy(self.placed_walls),
            'winner': self.winner
        }
        self.redo_stack.append(current_state)
        
        # Pop previous state
        prev_state = self.history.pop()
        self.restore_state(prev_state)
        return True

    def redo(self):
        if not self.redo_stack: return False
        
        # Save current to history
        current_state = {
             'player_positions': copy.deepcopy(self.player_positions),
             'walls_left': copy.deepcopy(self.walls_left),
             'current_turn': self.current_turn,
             'board_graph': copy.deepcopy(self.board_graph),
             'placed_walls': copy.deepcopy(self.placed_walls),
             'winner': self.winner
        }
        self.history.append(current_state)
        
        # Pop future state
        next_state = self.redo_stack.pop()
        self.restore_state(next_state)
        return True

    def save_game_to_file(self, filename="quoridor_save.pkl"):
        """Bonus: Save game to file"""
        with open(filename, 'wb') as f:
            pickle.dump(self.__dict__, f)

    def load_game_from_file(self, filename="quoridor_save.pkl"):
        """Bonus: Load game from file"""
        try:
            with open(filename, 'rb') as f:
                data = pickle.load(f)
                self.__dict__.update(data)
            return True
        except FileNotFoundError:
            return False

    
    def is_valid_pawn_move(self, current_pos, target_pos, opponent_pos):
        # ... (Same as before) ...
        neighbors = self.board_graph[current_pos]
        if target_pos in neighbors:
            if target_pos == opponent_pos: return False 
            return True
        if opponent_pos in neighbors:
            dr = opponent_pos[0] - current_pos[0]
            dc = opponent_pos[1] - current_pos[1]
            jump_dest = (opponent_pos[0] + dr, opponent_pos[1] + dc)
            if jump_dest in self.board_graph[opponent_pos] and target_pos == jump_dest: return True
            if jump_dest not in self.board_graph[opponent_pos]:
                if target_pos in self.board_graph[opponent_pos] and target_pos != current_pos: return True
        return False

    def move_pawn(self, player, r, c):
        if self.winner or player != self.current_turn: return False
        current_pos = self.player_positions[player]
        opponent = 2 if player == 1 else 1
        opponent_pos = self.player_positions[opponent]

        if self.is_valid_pawn_move(current_pos, (r, c), opponent_pos):
            self.save_state() # <--- SAVE BEFORE MODIFYING
            self.player_positions[player] = (r, c)
            self.check_win_condition()
            self.switch_turn()
            return True
        return False

    def place_wall(self, player, r, c, orientation):
        if self.winner or player != self.current_turn: return False
        if self.walls_left[player] <= 0: return False
        if not (0 <= r < 8 and 0 <= c < 8): return False
        if (r, c, 'H') in self.placed_walls or (r, c, 'V') in self.placed_walls: return False
        
        if orientation == 'H':
            if (r, c-1, 'H') in self.placed_walls or (r, c+1, 'H') in self.placed_walls: return False
        else:
            if (r-1, c, 'V') in self.placed_walls or (r+1, c, 'V') in self.placed_walls: return False

        edges_to_cut = []
        if orientation == 'H':
            p1, p2, p3, p4 = (r, c), (r+1, c), (r, c+1), (r+1, c+1)
            edges_to_cut = [(p1, p2), (p3, p4)]
        else:
            p1, p2, p3, p4 = (r, c), (r, c+1), (r+1, c), (r+1, c+1)
            edges_to_cut = [(p1, p2), (p3, p4)]

        temp_removed = []
        for u, v in edges_to_cut:
            if v in self.board_graph[u]:
                self.board_graph[u].remove(v)
                self.board_graph[v].remove(u)
                temp_removed.append((u, v))

        if self.has_path(1) and self.has_path(2):
            self.save_state() # <--- SAVE BEFORE FINALIZING
            self.placed_walls.add((r, c, orientation))
            self.walls_left[player] -= 1
            self.switch_turn()
            return True
        else:
            for u, v in temp_removed:
                self.board_graph[u].add(v)
                self.board_graph[v].add(u)
            return False

    def has_path(self, player_id):
        start_node = self.player_positions[player_id]
        goal_row = 8 if player_id == 1 else 0
        queue = collections.deque([start_node])
        visited = {start_node}
        while queue:
            curr_r, curr_c = queue.popleft()
            if curr_r == goal_row: return True
            for neighbor in self.board_graph[(curr_r, curr_c)]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return False

    def switch_turn(self):
        self.current_turn = 2 if self.current_turn == 1 else 1

    def check_win_condition(self):
        if self.player_positions[1][0] == 8: self.winner = 1
        elif self.player_positions[2][0] == 0: self.winner = 2
    
    # --- ADD THIS HELPER METHOD TO game_logic.py ---
    def _remove_edges_for_wall(self, r, c, orientation):
        """Helper to cut graph edges without rule checks (for loading/internal use)."""
        edges_to_cut = []
        if orientation == 'H':
            p1, p2, p3, p4 = (r, c), (r+1, c), (r, c+1), (r+1, c+1)
            edges_to_cut = [(p1, p2), (p3, p4)]
        else:
            p1, p2, p3, p4 = (r, c), (r, c+1), (r+1, c), (r+1, c+1)
            edges_to_cut = [(p1, p2), (p3, p4)]

        for u, v in edges_to_cut:
            if v in self.board_graph[u]:
                self.board_graph[u].remove(v)
            if u in self.board_graph[v]:
                self.board_graph[v].remove(u)


    def save_game_to_file(self, filename="quoridor_save.pkl"):
        """Saves only the essential state data."""
        try:
            state_data = {
                'player_positions': self.player_positions,
                'walls_left': self.walls_left,
                'current_turn': self.current_turn,
                'placed_walls': list(self.placed_walls), # Convert set to list
                'winner': self.winner,
                # Note: We do NOT save history or board_graph to keep file small and safe
            }
            with open(filename, 'wb') as f:
                pickle.dump(state_data, f)
            print(f"Game saved successfully to {filename}")
            return True
        except Exception as e:
            print(f"Error saving game: {e}")
            return False

    def load_game_from_file(self, filename="quoridor_save.pkl"):
        """Loads state and REBUILDS the graph from scratch."""
        try:
            with open(filename, 'rb') as f:
                data = pickle.load(f)

            # 1. Reset Board Graph to clean state
            self.board_graph = self._initialize_graph()
            
            # 2. Restore Attributes
            self.player_positions = data['player_positions']
            self.walls_left = data['walls_left']
            self.current_turn = data['current_turn']
            self.winner = data['winner']
            
            # 3. Restore Walls and Re-Cut Edges
            self.placed_walls = set() # Start clean
            for r, c, orient in data['placed_walls']:
                self.placed_walls.add((r, c, orient))
                self._remove_edges_for_wall(r, c, orient)

            # 4. Clear History (Undo/Redo implies current session only)
            self.history = []
            self.redo_stack = []
            
            print("Game loaded successfully.")
            return True
        except FileNotFoundError:
            print("Save file not found.")
            return False
        except Exception as e:
            print(f"Error loading game: {e}")
            return False