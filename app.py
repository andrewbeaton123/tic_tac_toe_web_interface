from flask import Flask, render_template, request, jsonify, current_app
import logging
import requests
import json
from tic_tac_toe_game import TicTacToe  # Import your TicTacToe class
from tic_tac_toe_web_interface import game_logic

from dotenv import load_dotenv
import os

load_dotenv()


app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    if 'game' not in app.config:
        app.config['game'] = game_logic.init_game()
    return render_template('index.html')

@app.route('/make_move', methods=['POST'])
def make_move():
    data = request.get_json()
    row, col = data['row'], data['col']
    game = app.config['game'] #Get the game from the application context
    # Input Validation
    if not isinstance(row, int) or not isinstance(col, int):
        return jsonify({'error': 'Row and column must be integers'}), 400
    if not 0 <= row <= 2 or not 0 <= col <= 2:
        return jsonify({'error': 'Row and column must be between 0 and 2'}), 400

    # For simplicity, we'll use a global game instance
    #global game
    if game_logic.make_move(game,row,col):


        winner = game.winner
        board_state = game.board.tolist()
        #
        winner = game.winner
        board_state = game.board.tolist()
        #
        try:

            url = os.environ.get("ENDPOINT_URL")#"http://127.0.0.1:8000/next_move" # URL for the AI's next move
            headers = {"Content-Type": "application/json",
                       "ocp-apim-subscription-key":os.environ.get("OCP_APIM_SUBSCRIPTION_KEY")} # Setting the header for JSON communication and Authentication
            
            payload = {
            "current_player": 2,
            "game_state": [i for l in board_state for i in l]#[i for i in  for l  in board_state]
                } # Payload with the current game state


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
                logging.exception(f"Error sending request: {e}")
                return jsonify({"error":f"There was an error with the game server {e}"})

            except json.JSONDecodeError:
                logging.exception("Error decoding JSON response.")

        except ValueError as e:
            logging.error(f"Invalid move: {e}")
            return jsonify({'error': str(e)}), 400

    return jsonify({'error': "Move not valid or game over"}), 400

@app.route('/reset', methods=['POST'])
def reset():
    logging.info("Board Reset Started")
    game = app.config['game']
    #global game
    game.reset()
    #game.board.tolist()
    return jsonify({'board': game.board.tolist()})

if __name__ == '__main__':
    #game = TicTacToe(starting_player=1)
    with app.app_context():
        app.config['game'] = game_logic.init_game()
    app.run(debug=True)
