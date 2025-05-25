from flask import Flask, render_template, request, jsonify
import logging
from tic_tac_toe_game import TicTacToe  # Import your TicTacToe class

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/make_move', methods=['POST'])
def make_move():
    data = request.get_json()
    row, col = data['row'], data['col']
    
    # For simplicity, we'll use a global game instance
    global game
    if not game.is_game_over() and (row, col) in game.get_valid_moves():
        try:
            #if game.current_player == 2:

            game.make_move(row, col)
            winner = game.winner
            board_state = game.board.tolist()
            return jsonify({'board': board_state, 'winner': winner})
        except ValueError as e:
            logging.error(f"Invalid move: {e}")
            return jsonify({'error': str(e)}), 400
    
    return jsonify({'error': "Move not valid or game over"}), 400

@app.route('/reset', methods=['POST'])
def reset():
    logging.info("Board Reset Started")
    global game
    game.reset()
    #game.board.tolist()
    return jsonify({'board': game.board.tolist()})

if __name__ == '__main__':
    game = TicTacToe(starting_player=1)
    app.run(debug=True)
