import numpy as np

class TicTacToe:
    def __init__(self, starting_player=1):
        self.board = np.zeros((3, 3), dtype=int)
        self.current_player = starting_player
        self.winner = None

    def make_move(self, row, col):
        if self.board[row, col] != 0 or self.winner is not None:
            return False
        self.board[row, col] = self.current_player
        if self.check_winner(row, col):
            self.winner = self.current_player
        elif not self.get_valid_moves():
            self.winner = 0  # Draw
        else:
            self.current_player = 3 - self.current_player
        return True

    def check_winner(self, row, col):
        # Check row
        if all(self.board[row, :] == self.current_player):
            return True
        # Check column
        if all(self.board[:, col] == self.current_player):
            return True
        # Check diagonals
        if row == col and all(np.diag(self.board) == self.current_player):
            return True
        if row + col == 2 and all(np.diag(np.fliplr(self.board)) == self.current_player):
            return True
        return False

    def get_valid_moves(self):
        return [tuple(pos) for pos in np.argwhere(self.board == 0)]

    def is_game_over(self):
        return self.winner is not None or not self.get_valid_moves()

    def reset(self):
        self.board = np.zeros((3, 3), dtype=int)
        self.current_player = 1
        self.winner = None
