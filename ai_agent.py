import random
import collections
import time

class QuoridorAI:
    def __init__(self, game, player_id=2, difficulty='Hard'):
        self.game = game
        self.player_id = player_id
        self.opponent_id = 1 if player_id == 2 else 2
        self.difficulty = difficulty
        self.my_goal = 0 if player_id == 2 else 8
        self.opp_goal = 8 if player_id == 2 else 0
        
        # Optimization: Store standard openings
        self.move_count = 0

    def get_move(self):
        start_time = time.time()
        self.move_count += 1
        print(f"AI Thinking... (Diff: {self.difficulty})")
        
        if self.difficulty == 'Easy':
            return self.random_move()
        elif self.difficulty == 'Medium':
             return self.minimax_root(depth=1, beam_width=10)
        else:
            # HARD MODE:
            # Uses Beam Search with Depth 3
            # Beam Width 4 means we only investigate the 4 best-looking moves deep down
            return self.minimax_root(depth=3, beam_width=4)

    def minimax_root(self, depth, beam_width):
        # 1. Generate ALL valid moves
        all_moves = self.get_all_valid_moves(self.player_id)
        if not all_moves: return None
        
        # 2. Pre-Sort Moves (Heuristic Pruning)
        # We score moves superficially to pick the best candidates
        scored_moves = []
        for move in all_moves:
            # Quick simulate
            self.apply_move(move, self.player_id)
            score = self.evaluate_state_quick() # Fast non-recursive score
            self.undo_move(move, self.player_id)
            scored_moves.append((score, move))
            
        # Sort best first
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        
        # 3. Select only the top N candidates (The "Beam")
        best_candidates = [m[1] for m in scored_moves[:beam_width]]
        
        # 4. Run Deep Minimax on only these candidates
        best_val = -float('inf')
        best_move = best_candidates[0] # Default fallback
        
        alpha = -float('inf')
        beta = float('inf')

        for move in best_candidates:
            self.apply_move(move, self.player_id)
            val = self.minimax(depth - 1, False, alpha, beta, beam_width)
            self.undo_move(move, self.player_id)
            
            print(f"Move {move} Score: {val}") # Debug info
            
            if val > best_val:
                best_val = val
                best_move = move
            
            alpha = max(alpha, best_val)
        
        return best_move

    def minimax(self, depth, is_maximizing, alpha, beta, beam_width):
        if depth == 0 or self.game.winner:
            return self.evaluate_state_deep()

        player = self.player_id if is_maximizing else self.opponent_id
        
        # Generate moves
        moves = self.get_all_valid_moves(player)
        if not moves: return self.evaluate_state_deep()

        # BEAM FILTERING INSIDE RECURSION
        # To keep it fast, we also limit branches inside the tree
        # But we use a wider beam for pawns (they are cheap) and narrow for walls
        if depth > 1:
            scored_moves = []
            for move in moves:
                self.apply_move(move, player)
                score = self.evaluate_state_quick()
                self.undo_move(move, player)
                scored_moves.append((score, move))
            
            # Sort: Max wants high score, Min wants low score
            scored_moves.sort(key=lambda x: x[0], reverse=is_maximizing)
            moves = [m[1] for m in scored_moves[:beam_width]]

        if is_maximizing:
            max_eval = -float('inf')
            for move in moves:
                self.apply_move(move, player)
                eval_score = self.minimax(depth - 1, False, alpha, beta, beam_width)
                self.undo_move(move, player)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha: break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                self.apply_move(move, player)
                eval_score = self.minimax(depth - 1, True, alpha, beta, beam_width)
                self.undo_move(move, player)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha: break
            return min_eval

    def evaluate_state_quick(self):
        """Fast evaluation for sorting moves (Distance Only)."""
        if self.game.winner == self.player_id: return 10000
        if self.game.winner == self.opponent_id: return -10000
        
        my_dist = self.bfs_distance(self.game.player_positions[self.player_id], self.my_goal)
        opp_dist = self.bfs_distance(self.game.player_positions[self.opponent_id], self.opp_goal)
        
        # Penalize blocking yourself
        if my_dist >= 999: return -5000
        if opp_dist >= 999: return 5000
        
        return (opp_dist - my_dist)

    def evaluate_state_deep(self):
        """Detailed evaluation for leaf nodes."""
        if self.game.winner == self.player_id: return 10000
        if self.game.winner == self.opponent_id: return -10000
        
        my_pos = self.game.player_positions[self.player_id]
        opp_pos = self.game.player_positions[self.opponent_id]
        
        my_dist = self.bfs_distance(my_pos, self.my_goal)
        opp_dist = self.bfs_distance(opp_pos, self.opp_goal)
        
        if my_dist >= 999: return -5000 
        if opp_dist >= 999: return 5000

        # Base Score
        score = (opp_dist - my_dist) * 100
        
        # BONUS 1: Path Complexity
        # If I force opponent to take a long winding path, that is good.
        # (Implicitly handled by distance, but we weight it heavily)
        
        # BONUS 2: Center Control
        # Being in the middle (col 3-5) is safer than edges
        if 3 <= my_pos[1] <= 5: score += 10
        
        # BONUS 3: Wall Conservation
        # Having walls left is valuable for the endgame
        score += self.game.walls_left[self.player_id] * 5
        
        return score

    def get_all_valid_moves(self, player_id):
        moves = []
        cur_r, cur_c = self.game.player_positions[player_id]
        opp_id = 1 if player_id == 2 else 2
        opp_pos = self.game.player_positions[opp_id]
        
        # 1. Pawn Moves
        neighbors = self.game.board_graph[(cur_r, cur_c)]
        for r, c in neighbors:
            target = None
            if (r, c) == opp_pos:
                # Jump Logic
                dr, dc = r - cur_r, c - cur_c
                jump_dest = (r + dr, c + dc)
                if jump_dest in self.game.board_graph[(r, c)]:
                    target = jump_dest
                else:
                    for nr, nc in self.game.board_graph[(r, c)]:
                        if (nr, nc) != (cur_r, cur_c):
                            moves.append(('move', nr, nc, cur_r, cur_c))
            else:
                target = (r, c)
            
            if target:
                moves.append(('move', target[0], target[1], cur_r, cur_c))

        # 2. Wall Moves - SMART FILTERING
        # Only check walls that might block the opponent's SHORTEST PATH
        if self.game.walls_left[player_id] > 0:
            opp_path = self.get_shortest_path_nodes(opp_id)
            
            # Identify "Cut Points"
            # We check the first 5 steps of the opponent. 
            # Trying to block them further away is usually useless.
            urgent_steps = opp_path[:6] 
            
            checked_walls = set()
            
            for i in range(len(urgent_steps) - 1):
                u, v = urgent_steps[i], urgent_steps[i+1]
                blocking_walls = self.get_walls_blocking_edge(u, v)
                
                for w in blocking_walls:
                    if w not in checked_walls:
                        if self.is_valid_wall_sim(w[0], w[1], w[2]):
                            moves.append(('wall', w[0], w[1], w[2]))
                        checked_walls.add(w)

        return moves

    
    def apply_move(self, move, player):
        if move[0] == 'move':
            self.game.player_positions[player] = (move[1], move[2])
        elif move[0] == 'wall':
            r, c, o = move[1], move[2], move[3]
            self.game.placed_walls.add((r, c, o))
            self.game.walls_left[player] -= 1
            self.cut_edges(r, c, o)

    def undo_move(self, move, player):
        if move[0] == 'move':
            self.game.player_positions[player] = (move[3], move[4])
        elif move[0] == 'wall':
            r, c, o = move[1], move[2], move[3]
            self.game.placed_walls.remove((r, c, o))
            self.game.walls_left[player] += 1
            self.restore_edges(r, c, o)

    def cut_edges(self, r, c, orientation):
        if orientation == 'H': pairs = [((r,c), (r+1,c)), ((r,c+1), (r+1,c+1))]
        else: pairs = [((r,c), (r,c+1)), ((r+1,c), (r+1,c+1))]
        for u, v in pairs:
            if v in self.game.board_graph[u]:
                self.game.board_graph[u].remove(v); self.game.board_graph[v].remove(u)

    def restore_edges(self, r, c, orientation):
        if orientation == 'H': pairs = [((r,c), (r+1,c)), ((r,c+1), (r+1,c+1))]
        else: pairs = [((r,c), (r,c+1)), ((r+1,c), (r+1,c+1))]
        for u, v in pairs:
            if not self.is_edge_blocked_by_any_wall(u, v):
                self.game.board_graph[u].add(v); self.game.board_graph[v].add(u)

    def is_edge_blocked_by_any_wall(self, u, v):
        r1, c1 = u; r2, c2 = v
        if c1 == c2 and abs(r1 - r2) == 1:
            rm = min(r1, r2)
            if (rm, c1, 'H') in self.game.placed_walls or (rm, c1-1, 'H') in self.game.placed_walls: return True
        if r1 == r2 and abs(c1 - c2) == 1:
            cm = min(c1, c2)
            if (r1, cm, 'V') in self.game.placed_walls or (r1-1, cm, 'V') in self.game.placed_walls: return True
        return False

    def is_valid_wall_sim(self, r, c, o):
        if not (0 <= r < 8 and 0 <= c < 8): return False
        if (r, c, 'H') in self.game.placed_walls or (r, c, 'V') in self.game.placed_walls: return False
        if o == 'H':
            if (r, c-1, 'H') in self.game.placed_walls or (r, c+1, 'H') in self.game.placed_walls: return False
        else:
            if (r-1, c, 'V') in self.game.placed_walls or (r+1, c, 'V') in self.game.placed_walls: return False
        
        self.cut_edges(r, c, o)
        p1 = self.bfs_distance(self.game.player_positions[1], 8) < 900
        p2 = self.bfs_distance(self.game.player_positions[2], 0) < 900
        self.restore_edges(r, c, o)
        return p1 and p2

    def bfs_distance(self, start_pos, goal_row):
        queue = collections.deque([(start_pos, 0)])
        visited = {start_pos}
        while queue:
            (r, c), dist = queue.popleft()
            if r == goal_row: return dist
            for n in self.game.board_graph[(r, c)]:
                if n not in visited:
                    visited.add(n)
                    queue.append((n, dist + 1))
        return 999
        
    def get_shortest_path_nodes(self, player_id):
        start = self.game.player_positions[player_id]
        goal_row = 8 if player_id == 1 else 0
        queue = collections.deque([[start]])
        visited = {start}
        while queue:
            path = queue.popleft()
            curr = path[-1]
            if curr[0] == goal_row: return path
            for neighbor in self.game.board_graph[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append(new_path)
        return []

    def get_walls_blocking_edge(self, u, v):
        walls = []
        r1, c1 = u; r2, c2 = v
        if c1 == c2: 
            min_r = min(r1, r2)
            walls.append((min_r, c1, 'H')); walls.append((min_r, c1 - 1, 'H'))
        elif r1 == r2:
            min_c = min(c1, c2)
            walls.append((r1, min_c, 'V')); walls.append((r1 - 1, min_c, 'V'))
        return walls

    def random_move(self):
        moves = self.get_all_valid_moves(self.player_id)
        return random.choice(moves) if moves else None