from tic_tac_toe_game import TicTacToe

class InvalidMoveError(Exception):
    pass

class GameOverError(Exception):
    pass

def init_game():
    return TicTacToe(starting_player=1)

def make_move(game, row, col):   
    if game.is_game_over():
        raise GameOverError("The game is over.")
    if (row, col) not in game.get_valid_moves():
        raise InvalidMoveError("Invalid move.")
    game.make_move(row, col)
    return True