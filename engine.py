import chess
import chess.engine
import chess.pgn
import threading
import os
import datetime
import time
import random

class ChessEngine:
    def __init__(self, stockfish_path="stockfish.exe", bot_level=5):
        self.board = chess.Board()
        self.stockfish_path = stockfish_path
        self.engine = None
        self.bot_level = bot_level 
        
        self.init_engine()

    def init_engine(self):
        def task():
            try:
                kwargs = {}
                if os.name == 'nt':
                    import subprocess
                    kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
                             
                self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path, **kwargs)
                self.set_bot_level(self.bot_level)
            except Exception as e:
                print(f"Stockfish init error: {e}")
        threading.Thread(target=task, daemon=True).start()

    def set_bot_level(self, level):
        self.bot_level = max(0, min(20, level))
        if not self.engine:
            return
        try:
            self.engine.configure({"Skill Level": self.bot_level})
        except Exception:
            pass

    def play_computer_move_async(self, callback):
        if not self.engine: return
        def task():
            try:
                calc_depth = max(1, self.bot_level // 2)
                calc_time = 0.1 + (self.bot_level * 0.05)
                limit = chess.engine.Limit(time=calc_time, depth=calc_depth)
                
                # Artificial delay so the bot doesn't move instantly
                time.sleep(random.uniform(0.6, 1.5))
                
                result = self.engine.play(self.board, limit)
                callback(result.move.uci())
            except Exception:
                pass
        threading.Thread(target=task, daemon=True).start()

    def get_hint_async(self, callback):
        """Fetches a quick best-move from Stockfish for the helper."""
        if not self.engine: return
        def task():
            try:
                result = self.engine.play(self.board, chess.engine.Limit(time=0.1, depth=5))
                if result and result.move:
                    callback(result.move.uci())
            except Exception:
                pass
        threading.Thread(target=task, daemon=True).start()

    def make_move(self, uci_string):
        try:
            move = chess.Move.from_uci(uci_string)
            if move in self.board.legal_moves:
                self.board.push(move)
                return True
        except Exception: 
            pass
        return False

    def get_legal_squares(self, square):
        if square is None: return []
        return [m.to_square for m in self.board.legal_moves if m.from_square == square]

    def export_pgn(self, white_name, black_name, filepath="match_export.pgn"):
        game = chess.pgn.Game()
        game.headers["Event"] = "Local Chess Match"
        game.headers["Date"] = datetime.datetime.now().strftime("%Y.%m.%d")
        game.headers["White"] = white_name
        game.headers["Black"] = black_name
        game.headers["Result"] = self.board.result()
        
        node = game
        for move in self.board.move_stack:
            node = node.add_variation(move)
            
        with open(filepath, "w") as f:
            f.write(str(game))
        return filepath

    def close(self):
        if self.engine:
            try: self.engine.quit()
            except Exception: pass