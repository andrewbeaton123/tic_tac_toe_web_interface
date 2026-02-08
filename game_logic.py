from tic_tac_toe_game import TicTacToe

def init_game():
    return TicTacToe(starting_player=1)

def make_move(game, row, col):   
    if not game.is_game_over() and (row, col) in game.get_valid_moves():
        game.make_move(row, col)
        return True
    return False