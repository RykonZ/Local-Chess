import pygame
import chess
import sys
import os
import random
from engine import ChessEngine
from network import ChessNetwork

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except Exception: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Layout Configuration ---
SQUARE_SIZE = 84
BOARD_SIZE = SQUARE_SIZE * 8
PANEL_WIDTH = 340
TOP_MARGIN = 50
BOTTOM_MARGIN = 50
WIDTH = BOARD_SIZE + PANEL_WIDTH + 40
HEIGHT = TOP_MARGIN + BOARD_SIZE + BOTTOM_MARGIN
FPS = 60

# --- Modern Dark Theme Palette ---
COLORS = {
    "light": (235, 236, 208), "dark": (115, 149, 82), 
    "highlight": (186, 202, 68), "premove": (235, 151, 78),
    "move_from": (246, 246, 105), "move_to": (186, 202, 43), 
    "dot": (20, 85, 30, 140), "check_red": (235, 70, 70), 
    "panel_bg": (38, 36, 33), "panel_card": (48, 46, 43), 
    "text": (240, 240, 240), "subtext": (180, 180, 180), 
    "btn": (65, 63, 60), "btn_hover": (85, 83, 80), 
    "btn_accent": (129, 182, 76), "bg": (22, 21, 18),
    "hint_arrow": (33, 150, 243)
}

class AnimatedMove:
    def __init__(self, piece_img, start_pos, end_pos, duration_frames=8):
        self.piece_img = piece_img
        self.start_x, self.start_y = start_pos
        self.end_x, self.end_y = end_pos
        self.total_frames = duration_frames
        self.current_frame = 0
    def update(self):
        self.current_frame += 1
        return self.current_frame >= self.total_frames
    def get_pos(self):
        t = self.current_frame / self.total_frames
        t_ease = 1 - (1 - t) * (1 - t)
        return self.start_x + (self.end_x - self.start_x) * t_ease, self.start_y + (self.end_y - self.start_y) * t_ease

class TextInput:
    def __init__(self, x, y, w, h, label, default=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.text = default
        self.active = False
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
            elif len(self.text) < 15 and event.unicode.isprintable(): self.text += event.unicode
    def draw(self, screen, font):
        color = COLORS["btn_accent"] if self.active else COLORS["btn"]
        pygame.draw.rect(screen, color, self.rect, border_radius=6, width=2 if self.active else 1)
        pygame.draw.rect(screen, COLORS["panel_card"], self.rect.inflate(-2, -2), border_radius=6)
        screen.blit(font.render(self.label, True, COLORS["subtext"]), (self.rect.x, self.rect.y - 22))
        
        # Blinking Cursor Logic
        cursor = "|" if self.active and (pygame.time.get_ticks() % 1000 < 500) else ""
        screen.blit(font.render(self.text + cursor, True, COLORS["text"]), (self.rect.x + 10, self.rect.y + 8))

class ChessGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Local Chess Pro")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Segoe UI", 16, bold=True)
        self.small_font = pygame.font.SysFont("Segoe UI", 13, bold=True)
        self.title_font = pygame.font.SysFont("Segoe UI", 32, bold=True)
        self.header_font = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.state = "menu"
        self.mode = "single"
        
        # Properly center the inputs (center_x is the left edge of a 240px wide block)
        center_x = WIDTH // 2 - 120
        self.inputs = {
            "name": TextInput(center_x, 0, 240, 36, "Player Name:", "Player 1"),
            "ip": TextInput(center_x, 0, 240, 36, "Host IP Address:", "127.0.0.1"),
            "time": TextInput(center_x, 0, 115, 36, "Mins:", "10"),
            "inc": TextInput(center_x + 125, 0, 115, 36, "Inc (s):", "5")
        }
        
        self.single_opponent = "Human" 
        self.bot_level = 5
        self.max_takebacks = 3
        self.host_color_pref = "White"
        self.allow_helper = False
        
        self.network = None
        self.opponent_name = "Opponent"
        self.my_color = chess.WHITE
        self.engine = None
        self.pieces = {}
        self.mini_pieces = {}
        self.selected_square = None
        self.dragging_square = None
        self.premove = None
        
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.active_animation = None
        self.current_hint = None
        
        self.starting_time = 600
        self.increment = 5
        self.time_white = 600
        self.time_black = 600
        self.timeout_winner = None
        self.abandon_winner = None
        
        self.rematch_requested_by_me = False
        self.rematch_requested_by_opp = False
        
        self.takebacks_remaining = 3
        self.takeback_vote_active = False
        
        self.computer_thinking = False
        self.pending_computer_move = None
        self.pgn_saved = False
        
        self.load_assets()

    def load_assets(self):
        for p in ['wP', 'wR', 'wN', 'wB', 'wQ', 'wK', 'bP', 'bR', 'bN', 'bB', 'bQ', 'bK']:
            path = resource_path(os.path.join("assets", f"{p}.png"))
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                self.pieces[p] = pygame.transform.smoothscale(img, (SQUARE_SIZE, SQUARE_SIZE))
                self.mini_pieces[p] = pygame.transform.smoothscale(img, (22, 22))
            else:
                surf = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                color = (240, 240, 240) if p[0] == 'w' else (40, 40, 40)
                pygame.draw.circle(surf, color, (SQUARE_SIZE//2, SQUARE_SIZE//2), SQUARE_SIZE//3)
                self.pieces[p] = surf
                self.mini_pieces[p] = pygame.transform.smoothscale(surf, (22, 22))

    def format_time(self, seconds):
        return f"{int(max(0, seconds)//60):02d}:{int(max(0, seconds)%60):02d}"

    def sq_to_screen(self, sq):
        c, r = (7 - chess.square_file(sq), chess.square_rank(sq)) if self.my_color == chess.BLACK else (chess.square_file(sq), 7 - chess.square_rank(sq))
        return 20 + c * SQUARE_SIZE, TOP_MARGIN + r * SQUARE_SIZE

    def screen_to_sq(self, pos):
        x, y = pos
        if x < 20 or x >= 20 + BOARD_SIZE or y < TOP_MARGIN or y >= TOP_MARGIN + BOARD_SIZE:
            return None
        c, r = (x - 20) // SQUARE_SIZE, (y - TOP_MARGIN) // SQUARE_SIZE
        return chess.square(7 - c, r) if self.my_color == chess.BLACK else chess.square(c, 7 - r)

    def is_my_turn(self):
        if self.mode == "single" and self.single_opponent == "Human": return True
        return self.engine.board.turn == self.my_color

    def request_hint(self):
        self.current_hint = None
        if self.allow_helper and self.engine and self.is_my_turn() and not self.engine.board.is_game_over():
            self.engine.get_hint_async(lambda uci: setattr(self, 'current_hint', uci))

    def process_network_message(self, msg):
        if msg == "SYS:CONNECTED" and self.state == "join_lobby":
            self.network.send_msg(f"NAME:{self.inputs['name'].text}")
        elif msg.startswith("NAME:"):
            self.opponent_name = msg.split(":")[1]
        elif msg.startswith("START:"):
            _, mins, inc, tb, hlp, color_str = msg.split(":")
            self.starting_time = int(mins) * 60
            self.increment = int(inc)
            self.max_takebacks = int(tb)
            self.allow_helper = (hlp == "1")
            self.my_color = chess.WHITE if color_str == "W" else chess.BLACK
            self.start_match()
        elif msg.startswith("MOVE:"):
            uci = msg.split(":")[1]
            m = chess.Move.from_uci(uci)
            piece = self.engine.board.piece_at(m.from_square)
            if piece:
                self.active_animation = AnimatedMove(self.pieces[('w' if piece.color == chess.WHITE else 'b') + piece.symbol().upper()], self.sq_to_screen(m.from_square), self.sq_to_screen(m.to_square))
            if self.engine.make_move(uci):
                if self.engine.board.turn == chess.WHITE: self.time_black += self.increment
                else: self.time_white += self.increment
                self.check_premove()
                self.request_hint()
        elif msg == "TAKEBACK:REQ":
            self.takeback_vote_active = True
        elif msg == "TAKEBACK:YES":
            if len(self.engine.board.move_stack) > 0: self.engine.board.pop()
            self.premove = None
            self.request_hint()
        elif msg == "TAKEBACK:NO":
            pass 
        elif msg == "RESIGN:": 
            self.abandon_winner = self.my_color
        elif msg == "REMATCH:REQ": 
            self.rematch_requested_by_opp = True
        elif msg == "REMATCH:ACCEPT": 
            self.restart_match()
        elif msg in ["QUIT:", "DISCONNECT:"]:
            if self.state in ["host_lobby", "join_lobby", "playing"]:
                if self.network: self.network.close()
                self.state = "menu"

    def single_lobby(self):
        self.state = "single_lobby"
        self.mode = "single"
        if self.network: self.network.close()
        self.network = None

    def host_lobby(self):
        self.state = "host_lobby"
        self.mode = "host"
        if self.network: self.network.close()
        self.network = ChessNetwork(is_host=True, on_msg=self.process_network_message)

    def join_lobby(self):
        self.state = "join_lobby"
        self.mode = "join"
        if self.network: self.network.close()
        self.network = None

    def start_match(self):
        self.state = "playing"
        self.time_white = self.time_black = self.starting_time
        self.timeout_winner = self.abandon_winner = None
        self.rematch_requested_by_me = self.rematch_requested_by_opp = False
        self.takebacks_remaining = self.max_takebacks
        self.takeback_vote_active = False
        self.selected_square = self.dragging_square = self.premove = self.active_animation = self.current_hint = None
        self.computer_thinking = False
        self.pending_computer_move = None
        self.pgn_saved = False
        self.engine = ChessEngine(stockfish_path=resource_path("stockfish.exe"), bot_level=self.bot_level)
        self.request_hint()

    def restart_match(self):
        if self.engine: self.engine.close()
        if self.mode != "single": self.my_color = not self.my_color
        elif self.single_opponent == "Computer": self.my_color = not self.my_color
        self.start_match()

    def execute_move(self, from_sq, to_sq):
        move = chess.Move(from_sq, to_sq)
        piece = self.engine.board.piece_at(from_sq)
        if piece and piece.piece_type == chess.PAWN and chess.square_rank(to_sq) in (0, 7):
            move = chess.Move(from_sq, to_sq, promotion=chess.QUEEN)
            
        if move in self.engine.board.legal_moves:
            self.active_animation = AnimatedMove(self.pieces[('w' if piece.color == chess.WHITE else 'b') + piece.symbol().upper()], self.sq_to_screen(from_sq), self.sq_to_screen(to_sq))
            uci_str = move.uci()
            self.engine.make_move(uci_str)
            self.current_hint = None
            
            if self.engine.board.turn == chess.WHITE: self.time_black += self.increment
            else: self.time_white += self.increment
            
            if self.network: self.network.send_msg(f"MOVE:{uci_str}")
            return True
        return False

    def check_premove(self):
        if self.premove and self.is_my_turn():
            move = chess.Move(self.premove[0], self.premove[1])
            piece = self.engine.board.piece_at(self.premove[0])
            if piece and piece.piece_type == chess.PAWN and chess.square_rank(self.premove[1]) in (0, 7):
                move = chess.Move(self.premove[0], self.premove[1], promotion=chess.QUEEN)
            if move in self.engine.board.legal_moves:
                self.execute_move(self.premove[0], self.premove[1])
            self.premove = None

    def trigger_takeback(self):
        if self.mode == "single":
            if len(self.engine.board.move_stack) > 0:
                self.engine.board.pop()
                if self.single_opponent == "Computer" and len(self.engine.board.move_stack) > 0 and self.engine.board.turn != self.my_color:
                    self.engine.board.pop()
                self.premove = None
                self.request_hint()
        else:
            if self.takebacks_remaining > 0:
                self.takebacks_remaining -= 1
                self.network.send_msg("TAKEBACK:REQ")

    def draw_player_bar(self, is_top):
        y_pos = 0 if is_top else HEIGHT - BOTTOM_MARGIN
        is_opponent = is_top
        player_color = not self.my_color if is_opponent else self.my_color
        time_left = self.time_black if player_color == chess.BLACK else self.time_white
        
        if self.mode == "single":
            if self.single_opponent == "Computer": name = f"Stockfish (Lv {self.bot_level})" if is_opponent else self.inputs["name"].text
            else: name = "Black" if player_color == chess.BLACK else "White"
        else: name = self.opponent_name if is_opponent else self.inputs["name"].text

        self.screen.blit(self.font.render(name, True, COLORS["text"]), (20, y_pos + 15))
        
        timer_bg = pygame.Rect(20 + BOARD_SIZE - 90, y_pos + 10, 90, 34)
        pygame.draw.rect(self.screen, COLORS["btn"], timer_bg, border_radius=6)
        timer_txt = self.font.render(self.format_time(time_left), True, COLORS["text"])
        self.screen.blit(timer_txt, (timer_bg.x + timer_bg.width//2 - timer_txt.get_width()//2, timer_bg.y + 6))

    def draw_game(self):
        self.screen.fill(COLORS["bg"])
        zones = []
        mouse_pos = pygame.mouse.get_pos()
        
        self.draw_player_bar(True)
        self.draw_player_bar(False)
        
        # Draw Board
        curr_board = self.engine.board
        for r in range(8):
            for c in range(8):
                sq = chess.square(c, 7 - r) if self.my_color == chess.WHITE else chess.square(7 - c, r)
                x, y = 20 + c * SQUARE_SIZE, TOP_MARGIN + r * SQUARE_SIZE
                color = COLORS["light"] if (r + c) % 2 == 0 else COLORS["dark"]
                
                if sq == self.selected_square: color = COLORS["highlight"]
                elif curr_board.move_stack and sq in (curr_board.move_stack[-1].from_square, curr_board.move_stack[-1].to_square):
                    color = COLORS["move_to"] if sq == curr_board.move_stack[-1].to_square else COLORS["move_from"]
                
                pygame.draw.rect(self.screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))
                
                # Draw Premove Highlight
                if self.premove and sq in self.premove:
                    pygame.draw.rect(self.screen, COLORS["premove"], (x, y, SQUARE_SIZE, SQUARE_SIZE), width=4)

        # Draw Hint Arrow if allowed
        if self.allow_helper and self.current_hint and self.is_my_turn() and self.dragging_square is None:
            m = chess.Move.from_uci(self.current_hint)
            sx, sy = self.sq_to_screen(m.from_square)
            ex, ey = self.sq_to_screen(m.to_square)
            pygame.draw.line(self.screen, COLORS["hint_arrow"], (sx + SQUARE_SIZE//2, sy + SQUARE_SIZE//2), (ex + SQUARE_SIZE//2, ey + SQUARE_SIZE//2), 6)

        # Draw Pieces
        if self.engine:
            if curr_board.is_check():
                king_sq = curr_board.king(curr_board.turn)
                if king_sq is not None:
                    kx, ky = self.sq_to_screen(king_sq)
                    ov = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    ov.fill((*COLORS["check_red"], 180))
                    self.screen.blit(ov, (kx, ky))
                    
            active_sq = self.dragging_square if self.dragging_square is not None else self.selected_square
            if active_sq is not None and self.is_my_turn():
                for sq in self.engine.get_legal_squares(active_sq):
                    cx, cy = self.sq_to_screen(sq)
                    dot = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    pygame.draw.circle(dot, COLORS["dot"], (SQUARE_SIZE // 2, SQUARE_SIZE // 2), SQUARE_SIZE // 6)
                    self.screen.blit(dot, (cx, cy))
                    
            for sq in range(64):
                if sq == self.dragging_square: continue
                if self.active_animation and curr_board.move_stack and sq == curr_board.move_stack[-1].to_square: continue
                piece = curr_board.piece_at(sq)
                if piece: 
                    self.screen.blit(self.pieces[('w' if piece.color == chess.WHITE else 'b') + piece.symbol().upper()], self.sq_to_screen(sq))
                    
            if self.active_animation:
                ax, ay = self.active_animation.get_pos()
                self.screen.blit(self.active_animation.piece_img, (ax, ay))
                if self.active_animation.update(): self.active_animation = None
                
            if self.dragging_square is not None:
                piece = curr_board.piece_at(self.dragging_square)
                if piece:
                    mx, my = pygame.mouse.get_pos()
                    self.screen.blit(self.pieces[('w' if piece.color == chess.WHITE else 'b') + piece.symbol().upper()], (mx - self.drag_offset_x, my - self.drag_offset_y))

        # Side Panel
        panel_x = 20 + BOARD_SIZE + 20
        pygame.draw.rect(self.screen, COLORS["panel_bg"], (panel_x, 0, PANEL_WIDTH, HEIGHT))
        self.screen.blit(self.header_font.render("Match Moves", True, COLORS["text"]), (panel_x + 20, 20))
        
        history_rect = pygame.Rect(panel_x + 20, 60, PANEL_WIDTH - 40, HEIGHT - 200)
        pygame.draw.rect(self.screen, COLORS["panel_card"], history_rect, border_radius=8)
        
        if self.engine:
            y_offset = history_rect.y + 10
            moves = self.engine.board.move_stack
            start_idx = max(0, len(moves) - 18)
            
            temp_board = chess.Board()
            for i in range(start_idx): temp_board.push(moves[i])
            
            for i in range(start_idx, len(moves)):
                san = temp_board.san(moves[i])
                temp_board.push(moves[i])
                
                color_is_white = i % 2 == 0
                txt = f"{(i // 2) + 1}. {san}" if color_is_white else f"   {san}"
                
                col_x = history_rect.x + 15 if color_is_white else history_rect.x + 140
                y_pos = y_offset + ((i - start_idx)//2) * 25
                self.screen.blit(self.font.render(txt, True, COLORS["text"]), (col_x, y_pos))

        # Lower Panel Buttons
        btn_tb = pygame.Rect(panel_x + 20, HEIGHT - 130, PANEL_WIDTH - 40, 38)
        tb_avail = self.takebacks_remaining > 0 or self.mode == "single"
        pygame.draw.rect(self.screen, COLORS["btn_hover"] if btn_tb.collidepoint(mouse_pos) and tb_avail else COLORS["btn"], btn_tb, border_radius=6)
        t_tb = self.font.render(f"Rewind / Takeback ({self.takebacks_remaining if self.mode != 'single' else '\u221E'})", True, COLORS["text"] if tb_avail else COLORS["subtext"])
        self.screen.blit(t_tb, (btn_tb.x + btn_tb.width//2 - t_tb.get_width()//2, btn_tb.y + 9))
        if tb_avail: zones.append(("takeback", btn_tb))

        btn_resign = pygame.Rect(panel_x + 20, HEIGHT - 80, PANEL_WIDTH - 40, 38)
        pygame.draw.rect(self.screen, COLORS["check_red"] if btn_resign.collidepoint(mouse_pos) else COLORS["btn"], btn_resign, border_radius=6)
        t_res = self.font.render("Resign / Quit", True, COLORS["text"])
        self.screen.blit(t_res, (btn_resign.x + btn_resign.width//2 - t_res.get_width()//2, btn_resign.y + 9))
        zones.append(("resign", btn_resign))
        
        # Takeback Vote Overlay
        if self.takeback_vote_active:
            ov = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 200))
            self.screen.blit(ov, (20, TOP_MARGIN))
            txt = self.header_font.render("Opponent requested a Takeback", True, COLORS["text"])
            self.screen.blit(txt, (20 + BOARD_SIZE//2 - txt.get_width()//2, TOP_MARGIN + BOARD_SIZE//2 - 40))
            
            btn_y = pygame.Rect(20 + BOARD_SIZE//2 - 110, TOP_MARGIN + BOARD_SIZE//2 + 10, 100, 40)
            btn_n = pygame.Rect(20 + BOARD_SIZE//2 + 10, TOP_MARGIN + BOARD_SIZE//2 + 10, 100, 40)
            pygame.draw.rect(self.screen, COLORS["btn_accent"], btn_y, border_radius=6)
            pygame.draw.rect(self.screen, COLORS["check_red"], btn_n, border_radius=6)
            self.screen.blit(self.font.render("Accept", True, COLORS["text"]), (btn_y.x + 25, btn_y.y + 10))
            self.screen.blit(self.font.render("Deny", True, COLORS["text"]), (btn_n.x + 30, btn_n.y + 10))
            zones.extend([("tb_yes", btn_y), ("tb_no", btn_n)])

        # Game Over Overlay
        is_game_over = False
        if self.engine: is_game_over = self.engine.board.is_game_over() or self.timeout_winner is not None or self.abandon_winner is not None
        if is_game_over:
            ov = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 200))
            self.screen.blit(ov, (20, TOP_MARGIN))
            
            if self.abandon_winner is not None: result_txt, term_txt = ("White Wins!" if self.abandon_winner == chess.WHITE else "Black Wins!"), "Resignation"
            elif self.timeout_winner is not None: result_txt, term_txt = ("White Wins!" if self.timeout_winner == chess.WHITE else "Black Wins!"), "Timeout"
            else:
                out = self.engine.board.outcome()
                result_txt, term_txt = "Draw", out.termination.name.replace("_", " ").title()
                if out.winner == chess.WHITE: result_txt = "White Wins!"
                elif out.winner == chess.BLACK: result_txt = "Black Wins!"
                
            res_surf = self.title_font.render(result_txt, True, COLORS["text"])
            term_surf = self.font.render(term_txt, True, COLORS["highlight"])
            self.screen.blit(res_surf, (20 + BOARD_SIZE//2 - res_surf.get_width()//2, TOP_MARGIN + BOARD_SIZE//2 - 90))
            self.screen.blit(term_surf, (20 + BOARD_SIZE//2 - term_surf.get_width()//2, TOP_MARGIN + BOARD_SIZE//2 - 50))
            
            btn_pgn = pygame.Rect(20 + BOARD_SIZE//2 - 140, TOP_MARGIN + BOARD_SIZE//2 + 10, 280, 42)
            pygame.draw.rect(self.screen, COLORS["btn_hover"] if btn_pgn.collidepoint(mouse_pos) else COLORS["btn_accent"], btn_pgn, border_radius=6)
            pgn_txt = self.font.render("Export PGN" if not self.pgn_saved else "Saved to match_export.pgn!", True, COLORS["text"])
            self.screen.blit(pgn_txt, (btn_pgn.x + btn_pgn.width//2 - pgn_txt.get_width()//2, btn_pgn.y + 11))
            zones.append(("pgn", btn_pgn))

            btn_quit_overlay = pygame.Rect(20 + BOARD_SIZE//2 - 140, TOP_MARGIN + BOARD_SIZE//2 + 65, 280, 42)
            pygame.draw.rect(self.screen, COLORS["btn_hover"] if btn_quit_overlay.collidepoint(mouse_pos) else COLORS["check_red"], btn_quit_overlay, border_radius=6)
            q_txt = self.font.render("Quit to Main Menu", True, COLORS["text"])
            self.screen.blit(q_txt, (btn_quit_overlay.x + btn_quit_overlay.width//2 - q_txt.get_width()//2, btn_quit_overlay.y + 11))
            zones.append(("quit", btn_quit_overlay))

        return zones

    def draw_menus(self):
        self.screen.fill(COLORS["bg"])
        cx, mouse_pos, zones = WIDTH // 2, pygame.mouse.get_pos(), []
        
        if self.state == "menu":
            title = self.title_font.render("LOCAL CHESS PRO", True, COLORS["text"])
            self.screen.blit(title, (cx - title.get_width()//2, 80))
            sub = self.font.render("Select Game Mode", True, COLORS["subtext"])
            self.screen.blit(sub, (cx - sub.get_width()//2, 120))
            
            for key, y_pos, txt in [("single", 180, "Local Singleplayer"), ("host", 250, "Host Network Match"), ("join", 320, "Join Network Match")]:
                btn = pygame.Rect(cx - 130, y_pos, 260, 50)
                pygame.draw.rect(self.screen, COLORS["btn_hover"] if btn.collidepoint(mouse_pos) else COLORS["panel_card"], btn, border_radius=8)
                t_surf = self.font.render(txt, True, COLORS["text"])
                self.screen.blit(t_surf, (btn.x + 130 - t_surf.get_width()//2, btn.y + 15))
                zones.append((key, btn))
                
        elif self.state in ["host_lobby", "join_lobby", "single_lobby"]:
            title_str = "Host Match Options" if self.state == "host_lobby" else "Join Match Settings" if self.state == "join_lobby" else "Singleplayer Match"
            title = self.title_font.render(title_str, True, COLORS["text"])
            self.screen.blit(title, (cx - title.get_width()//2, 40))
            y_off = 110
            
            if self.state in ["host_lobby", "join_lobby"]:
                self.inputs["name"].rect.y = y_off
                self.inputs["name"].draw(self.screen, self.font)
                y_off += 60
                
            if self.state == "single_lobby":
                opp_rect = pygame.Rect(cx - 120, y_off, 240, 36)
                pygame.draw.rect(self.screen, COLORS["btn_hover"] if opp_rect.collidepoint(mouse_pos) else COLORS["panel_card"], opp_rect, border_radius=6)
                c_txt = self.font.render(f"Opponent: {self.single_opponent}", True, COLORS["text"])
                self.screen.blit(c_txt, (opp_rect.x + 120 - c_txt.get_width()//2, opp_rect.y + 8))
                zones.append(("opp_toggle", opp_rect))
                y_off += 50
                
            if self.state == "join_lobby":
                self.inputs["ip"].rect.y = y_off
                self.inputs["ip"].draw(self.screen, self.font)
                y_off += 60
            else:
                self.inputs["time"].rect.y = y_off
                self.inputs["time"].draw(self.screen, self.font)
                self.inputs["inc"].rect.y = y_off
                self.inputs["inc"].draw(self.screen, self.font)
                y_off += 60
                
                if self.state == "host_lobby" or (self.state == "single_lobby" and self.single_opponent == "Computer"):
                    color_rect = pygame.Rect(cx - 120, y_off, 240, 36)
                    pygame.draw.rect(self.screen, COLORS["btn_hover"] if color_rect.collidepoint(mouse_pos) else COLORS["panel_card"], color_rect, border_radius=6)
                    self.screen.blit(self.font.render(f"Play as: {self.host_color_pref}", True, COLORS["text"]), (color_rect.x + 120 - self.font.render(f"Play as: {self.host_color_pref}", True, COLORS["text"]).get_width()//2, color_rect.y + 8))
                    zones.append(("color_toggle", color_rect))
                    y_off += 45
                    
                if self.state == "single_lobby" and self.single_opponent == "Computer":
                    self.screen.blit(self.font.render(f"Opponent Bot Level (0-20): {self.bot_level}", True, COLORS["text"]), (cx - 120, y_off + 3))
                    btn_b_dec = pygame.Rect(cx + 105, y_off, 28, 24)
                    btn_b_inc = pygame.Rect(cx + 140, y_off, 28, 24)
                    pygame.draw.rect(self.screen, COLORS["btn_hover"] if btn_b_dec.collidepoint(mouse_pos) else COLORS["panel_card"], btn_b_dec, border_radius=4)
                    pygame.draw.rect(self.screen, COLORS["btn_hover"] if btn_b_inc.collidepoint(mouse_pos) else COLORS["panel_card"], btn_b_inc, border_radius=4)
                    self.screen.blit(self.font.render("-", True, COLORS["text"]), (btn_b_dec.x + 10, btn_b_dec.y + 1))
                    self.screen.blit(self.font.render("+", True, COLORS["text"]), (btn_b_inc.x + 8, btn_b_inc.y + 1))
                    zones.extend([("bot_dec", btn_b_dec), ("bot_inc", btn_b_inc)])
                    y_off += 40

                if self.state in ["single_lobby", "host_lobby"]:
                    hlp_rect = pygame.Rect(cx - 120, y_off, 20, 20)
                    pygame.draw.rect(self.screen, COLORS["btn_accent"] if self.allow_helper else COLORS["btn"], hlp_rect, border_radius=4)
                    self.screen.blit(self.font.render("Allow Stockfish Helper Lines", True, COLORS["text"]), (cx - 90, y_off))
                    zones.append(("helper_toggle", pygame.Rect(cx - 120, y_off, 240, 20)))
                    y_off += 35

                self.screen.blit(self.font.render(f"Takebacks Allowed: {self.max_takebacks}", True, COLORS["text"]), (cx - 120, y_off + 3))
                btn_h_dec = pygame.Rect(cx + 60, y_off, 28, 24)
                btn_h_inc = pygame.Rect(cx + 95, y_off, 28, 24)
                pygame.draw.rect(self.screen, COLORS["btn_hover"] if btn_h_dec.collidepoint(mouse_pos) else COLORS["panel_card"], btn_h_dec, border_radius=4)
                pygame.draw.rect(self.screen, COLORS["btn_hover"] if btn_h_inc.collidepoint(mouse_pos) else COLORS["panel_card"], btn_h_inc, border_radius=4)
                self.screen.blit(self.font.render("-", True, COLORS["text"]), (btn_h_dec.x + 10, btn_h_dec.y + 1))
                self.screen.blit(self.font.render("+", True, COLORS["text"]), (btn_h_inc.x + 8, btn_h_inc.y + 1))
                zones.extend([("tb_dec", btn_h_dec), ("tb_inc", btn_h_inc)])
                y_off += 45
                
            if self.state in ["host_lobby", "join_lobby"]:
                is_conn = self.network and self.network.connected
                status = f"Status: Connected with {self.opponent_name}" if is_conn else "Status: Waiting for connection..."
                self.screen.blit(self.font.render(status, True, COLORS["highlight"] if is_conn else COLORS["subtext"]), (cx - 120, y_off + 5))
                y_off += 45
                
            btn_action = pygame.Rect(cx - 120, y_off, 110, 40)
            btn_cancel = pygame.Rect(cx + 10, y_off, 110, 40)
            act_ready = (self.state == "single_lobby") or (self.state == "join_lobby") or (self.state == "host_lobby" and self.network and self.network.connected)
            
            pygame.draw.rect(self.screen, COLORS["btn_accent"] if act_ready else COLORS["btn"], btn_action, border_radius=6)
            pygame.draw.rect(self.screen, COLORS["check_red"], btn_cancel, border_radius=6)
            
            act_txt = "Start" if self.state in ["host_lobby", "single_lobby"] else "Connect"
            self.screen.blit(self.font.render(act_txt, True, COLORS["text"]), (btn_action.x + 30, btn_action.y + 10))
            self.screen.blit(self.font.render("Cancel", True, COLORS["text"]), (btn_cancel.x + 25, btn_cancel.y + 10))
            zones.extend([("action", btn_action), ("cancel", btn_cancel)])
            
        return zones

    def run(self):
        running = True
        click_zones = []
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            if self.state == "playing" and self.engine and not self.engine.board.is_game_over() and not self.timeout_winner and not self.abandon_winner:
                if self.engine.board.turn == chess.WHITE:
                    self.time_white -= dt
                    if self.time_white <= 0: self.time_white, self.timeout_winner = 0, chess.BLACK
                else:
                    self.time_black -= dt
                    if self.time_black <= 0: self.time_black, self.timeout_winner = 0, chess.WHITE

            if self.state == "playing" and self.mode == "single" and self.single_opponent == "Computer":
                if not self.engine.board.is_game_over() and not self.timeout_winner and not self.abandon_winner:
                    if self.engine.board.turn != self.my_color and not self.computer_thinking:
                        self.computer_thinking = True
                        self.engine.play_computer_move_async(lambda uci: setattr(self, 'pending_computer_move', uci))
                        
            if self.pending_computer_move:
                m = chess.Move.from_uci(self.pending_computer_move)
                self.execute_move(m.from_square, m.to_square)
                self.pending_computer_move = None
                self.computer_thinking = False
                self.check_premove()
                self.request_hint()

            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if self.state in ["host_lobby", "join_lobby", "single_lobby"]:
                    for inp in self.inputs.values(): inp.handle_event(event)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == "menu":
                        for act, rect in click_zones:
                            if rect.collidepoint(event.pos):
                                if act == "single": self.single_lobby()
                                elif act == "host": self.host_lobby()
                                elif act == "join": self.join_lobby()
                    elif self.state in ["host_lobby", "join_lobby", "single_lobby"]:
                        for act, rect in click_zones:
                            if rect.collidepoint(event.pos):
                                if act == "cancel":
                                    if self.network: self.network.close()
                                    self.state = "menu"
                                elif act == "opp_toggle" and self.state == "single_lobby":
                                    self.single_opponent = "Computer" if self.single_opponent == "Human" else "Human"
                                elif act == "bot_dec": self.bot_level = max(0, self.bot_level - 1)
                                elif act == "bot_inc": self.bot_level = min(20, self.bot_level + 1)
                                elif act == "helper_toggle": self.allow_helper = not self.allow_helper
                                elif act == "tb_dec": self.max_takebacks = max(0, self.max_takebacks - 1)
                                elif act == "tb_inc": self.max_takebacks = min(99, self.max_takebacks + 1)
                                elif act == "color_toggle": self.host_color_pref = ["White", "Black", "Random"][ (["White", "Black", "Random"].index(self.host_color_pref) + 1) % 3 ]
                                elif act == "action":
                                    if self.state == "join_lobby":
                                        if not self.network or not self.network.connected:
                                            self.network = ChessNetwork(is_host=False, ip=self.inputs["ip"].text, on_msg=self.process_network_message)
                                    elif self.state == "single_lobby":
                                        self.inputs['name'].text = "Player 1"
                                        if self.single_opponent == "Computer":
                                            if self.host_color_pref == "Random": self.my_color = random.choice([chess.WHITE, chess.BLACK])
                                            else: self.my_color = chess.WHITE if self.host_color_pref == "White" else chess.BLACK
                                        else: self.my_color = chess.WHITE
                                        try: 
                                            self.starting_time = int(self.inputs['time'].text) * 60
                                            self.increment = int(self.inputs['inc'].text)
                                        except ValueError: 
                                            self.starting_time, self.increment = 600, 5
                                        self.start_match()
                                    elif self.state == "host_lobby" and self.network and self.network.connected:
                                        self.network.send_msg(f"NAME:{self.inputs['name'].text}")
                                        if self.host_color_pref == "Random": self.my_color = random.choice([chess.WHITE, chess.BLACK])
                                        else: self.my_color = chess.WHITE if self.host_color_pref == "White" else chess.BLACK
                                        j_c = "W" if self.my_color == chess.BLACK else "B"
                                        mins, inc = self.inputs['time'].text, self.inputs['inc'].text
                                        h_str = "1" if self.allow_helper else "0"
                                        self.network.send_msg(f"START:{mins}:{inc}:{self.max_takebacks}:{h_str}:{j_c}")
                                        try: 
                                            self.starting_time = int(mins) * 60
                                            self.increment = int(inc)
                                        except ValueError: 
                                            self.starting_time, self.increment = 600, 5
                                        self.start_match()
                    elif self.state == "playing":
                        cz = False
                        for act, rect in click_zones:
                            if rect.collidepoint(event.pos):
                                cz = True
                                if act == "quit":
                                    if self.network: self.network.send_msg("QUIT:"); self.network.close()
                                    if self.engine: self.engine.close()
                                    self.state = "menu"
                                elif act == "resign":
                                    self.abandon_winner = not self.my_color
                                    if self.network: self.network.send_msg("RESIGN:")
                                elif act == "takeback":
                                    self.trigger_takeback()
                                elif act == "tb_yes":
                                    self.takeback_vote_active = False
                                    if len(self.engine.board.move_stack) > 0: self.engine.board.pop()
                                    self.premove = None
                                    self.network.send_msg("TAKEBACK:YES")
                                    self.request_hint()
                                elif act == "tb_no":
                                    self.takeback_vote_active = False
                                    self.network.send_msg("TAKEBACK:NO")
                                elif act == "pgn" and not self.pgn_saved:
                                    white = self.inputs["name"].text if self.my_color == chess.WHITE else self.opponent_name
                                    black = self.opponent_name if self.my_color == chess.WHITE else self.inputs["name"].text
                                    self.engine.export_pgn(white, black)
                                    self.pgn_saved = True

                        if not cz and not (self.engine.board.is_game_over() or self.timeout_winner or self.abandon_winner):
                            sq = self.screen_to_sq(event.pos)
                            if sq is not None:
                                if self.is_my_turn():
                                    if self.selected_square is not None and sq in self.engine.get_legal_squares(self.selected_square):
                                        self.execute_move(self.selected_square, sq)
                                        self.selected_square = self.dragging_square = None
                                        self.premove = None
                                    else:
                                        piece = self.engine.board.piece_at(sq)
                                        if piece and piece.color == self.my_color:
                                            self.selected_square = self.dragging_square = sq
                                            x, y = self.sq_to_screen(sq)
                                            self.drag_offset_x, self.drag_offset_y = event.pos[0] - x, event.pos[1] - y
                                        else: self.selected_square = self.dragging_square = None
                                else:
                                    # PREMOVE LOGIC
                                    piece = self.engine.board.piece_at(sq)
                                    if piece and piece.color == self.my_color:
                                        self.dragging_square = sq
                                        x, y = self.sq_to_screen(sq)
                                        self.drag_offset_x, self.drag_offset_y = event.pos[0] - x, event.pos[1] - y

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.state == "playing" and self.dragging_square is not None:
                        drop_sq = self.screen_to_sq(event.pos)
                        if drop_sq is not None and drop_sq != self.dragging_square:
                            if self.is_my_turn():
                                if self.execute_move(self.dragging_square, drop_sq): 
                                    self.selected_square = None
                            else:
                                # Save Premove
                                self.premove = (self.dragging_square, drop_sq)
                        self.dragging_square = None

            if self.state == "playing": click_zones = self.draw_game()
            else: click_zones = self.draw_menus()
            pygame.display.flip()

        if self.network: self.network.close()
        if self.engine: self.engine.close()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    gui = ChessGUI()
    gui.run()