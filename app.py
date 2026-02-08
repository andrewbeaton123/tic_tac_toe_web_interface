import os
import logging
import json
import requests
import pickle
import base64
import numpy as np
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from tic_tac_toe_game import TicTacToe
import game_logic

load_dotenv()

app = Flask(__name__)
# Use a consistent secret key for sessions
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-key-789456123")
logging.basicConfig(level=logging.INFO)

def get_game():
    """Retrieve or initialize game from session."""
    if 'game_state' not in session:
        game = game_logic.init_game()
        save_game(game)
        return game
    
    try:
        # Decode and unpickle the game object from the session
        game_data = base64.b64decode(session['game_state'])
        return pickle.loads(game_data)
    except Exception as e:
        logging.error(f"Failed to load game from session: {e}")
        game = game_logic.init_game()
        save_game(game)
        return game

def save_game(game):
    """Serialize and save game to session."""
    game_data = pickle.dumps(game)
    session['game_state'] = base64.b64encode(game_data).decode('utf-8')

def _get_next_move(board_state):
    url = os.environ.get("ENDPOINT_URL")
    key = os.environ.get("OCP_APIM_SUBSCRIPTION_KEY")
    
    if not url or not key:
        logging.warning("AI credentials missing, falling back to random move")
        import random
        temp_game = TicTacToe()
        temp_game.board = np.array(board_state)
        moves = temp_game.get_valid_moves()
        return random.choice(range(len(moves))) if moves else 0

    try:
        headers = {
            "Content-Type": "application/json",
            "ocp-apim-subscription-key": key
        }
        payload = {
            "current_player": 2,
            "game_state": [int(i) for l in board_state for i in l]
        }
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()["move"]
    except Exception as e:
        logging.error(f"AI Service Error: {e}")
        # Fallback to random if external service fails
        import random
        temp_game = TicTacToe()
        temp_game.board = np.array(board_state)
        moves = temp_game.get_valid_moves()
        return random.choice(range(len(moves))) if moves else 0

@app.route('/')
def index():
    # Ensure a fresh game for a new page load if desired, 
    # or just let get_game handle it
    get_game()
    return render_template('index.html')

@app.route('/make_move', methods=['POST'])
def make_move():
    data = request.get_json()
    row, col = data.get('row'), data.get('col')
    game = get_game()

    if row is None or col is None:
        return jsonify({'error': 'Missing coordinates'}), 400
    
    try:
        # Player Move (X)
        game_logic.make_move(game, row, col)
        
        # AI Move (O) if game not over
        if not game.is_game_over():
            board_state = game.board.tolist()
            move_index = _get_next_move(board_state)
            valid_moves = game.get_valid_moves()
            
            if move_index < len(valid_moves):
                ai_row, ai_col = valid_moves[int(move_index)]
                game.make_move(ai_row, ai_col)

        save_game(game)
        return jsonify({
            'board': game.board.tolist(),
            'winner': game.winner,
            'over': game.is_game_over()
        })

    except game_logic.InvalidMoveError as e:
        return jsonify({"error": str(e)}), 400
    except game_logic.GameOverError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.exception("Move execution failed")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/reset', methods=['POST'])
def reset():
    game = game_logic.init_game()
    save_game(game)
    return jsonify({'board': game.board.tolist()})

if __name__ == '__main__':
    app.run(debug=True, port=8000)
