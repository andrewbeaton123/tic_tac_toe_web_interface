from flask import Flask, render_template, request, jsonify
import logging
import requests
import json
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
        
            
            
        game.make_move(row, col)
        winner = game.winner
        board_state = game.board.tolist()
        #
        try:

            url = "http://127.0.0.1:8000/next_move"
            headers = {"Content-Type": "application/json"}
            payload = {
            "current_player": 2,
            "game_state": board_state
                }
            try:
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                response.raise_for_status()  # Raise an exception for bad status codes
                next_move = response.json()["move"]
                logging.info(f"Next Move:{next_move}")
                game.make_move(*game.get_valid_moves()[int(next_move)])  
                final_board = game.board.tolist()
                winner = game.winner
                return jsonify({'board': final_board, 'winner': winner})
            
            except requests.exceptions.RequestException as e:
                print(f"Error sending request: {e}")
                return jsonify({"error":f"There was an error with the game server {e}"})

            
            except json.JSONDecodeError:
                print("Error decoding JSON response.")
            
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
