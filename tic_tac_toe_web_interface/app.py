import os
import logging
import random
import requests
import pickle
import base64
import numpy as np
from typing import Any
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from tic_tac_toe_game import TicTacToe

load_dotenv()
app = Flask(__name__)
# Use a consistent secret key for sessions
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-key-789456123")
logging.basicConfig(level=logging.INFO)


def init_game() -> TicTacToe:
    return TicTacToe(1)


def get_game() -> TicTacToe:
    """Retrieve or initialize game from session."""
    if 'game_state' not in session:
        game = init_game()
        save_game(game)
        return game

    try:
        # Decode and unpickle the game object from the session
        game_data = base64.b64decode(session['game_state'])
        return pickle.loads(game_data)
    except Exception as e:
        logging.error(f"Failed to load game from session: {e}")
        game = init_game()
        save_game(game)
        return game


def save_game(game: TicTacToe) -> None:
    """Serialize and save game to session."""
    game_data = pickle.dumps(game)
    session['game_state'] = base64.b64encode(game_data).decode('utf-8')


def _random_move(board_state: list[list[int]]) -> int:
    """Return a random valid move index for the given board state."""
    temp_game = TicTacToe(1, board=np.array(board_state))
    moves = temp_game.get_valid_moves().tolist()
    return random.choice(range(len(moves))) if moves else 0


def _get_next_move(board_state: list[list[int]]) -> tuple[int, bool]:
    """Call the AI service and return a (move_index, fallback_flag) tuple."""
    url = os.environ.get("ENDPOINT_URL")
    key = os.environ.get("OCP_APIM_SUBSCRIPTION_KEY")

    if not url or not key:
        logging.warning("AI credentials missing, falling back to random move")
        return _random_move(board_state), True

    try:
        headers = {
            "Content-Type": "application/json",
            "ocp-apim-subscription-key": key
        }
        payload = {
            "current_player": 2,
            "game_state": [int(i) for position in board_state for i in position]
        }
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()["move"], False
    except Exception as e:
        logging.error(f"AI Service Error: {e}")
        return _random_move(board_state), True


@app.route('/')
def index() -> Any:
    logging.info("Handling request to '/'")
    return render_template('index.html')


@app.route('/make_move', methods=['POST'])
def make_move() -> Any:
    data = request.get_json()
    row, col = data.get('row'), data.get('col')
    game = get_game()

    if row is None or col is None:
        return jsonify({'error': 'Missing coordinates'}), 400

    if game.is_game_over():
        return jsonify({"error": "The game is over."}), 400

    try:
        # Turn Validation: Ensure it's player 1's turn
        if game.current_player != 1:
            logging.warning(f"Rejecting move: current_player is {game.current_player}, expected 1")
            return jsonify({"error": "It is not your turn."}), 400

        # Player Move (X)
        game.make_move(row, col)

        # AI Move (O) if game not over
        fallback = False
        if not game.is_game_over():
            board_state = game.board.tolist()
            move_index, fallback = _get_next_move(board_state)
            valid_moves = game.get_valid_moves().tolist()

            # Ensure the move_index is valid, otherwise force a random move
            if move_index >= len(valid_moves):
                logging.warning(f"AI service returned invalid index {move_index}, falling back to local random move")
                move_index = _random_move(board_state)
                fallback = True

            ai_row, ai_col = valid_moves[int(move_index)]
            game.make_move(ai_row, ai_col)

        save_game(game)

        # In the original UI logic, winner=null means ongoing, winner=0 means draw, winner=X means player X won.
        # The imported TicTacToe uses 0 for no winner / draw, and 1 or 2 for player wins.
        winner = None
        if game.is_game_over():
            winner = int(game.winner) if game.winner != 0 else 0

        return jsonify({
            'board': game.board.tolist(),
            'winner': winner,
            'over': game.is_game_over(),
            'fallback': fallback
        })

    except ValueError:
        return jsonify({"error": "Invalid move."}), 400
    except Exception:
        logging.exception("Move execution failed")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/reset', methods=['POST'])
def reset() -> Any:
    logging.info("Handling request to '/reset'")
    game = init_game()
    save_game(game)
    return jsonify({'board': game.board.tolist()})


if __name__ == '__main__':
    logging.info("Starting Flask app on port 8001...")
    # Explicitly bind to 127.0.0.1 for local development
    app.run(debug=True, host='127.0.0.1', port=8001)
