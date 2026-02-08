import os
import logging
import json
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from tic_tac_toe_game import TicTacToe
import game_logic

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-key-123")
logging.basicConfig(level=logging.INFO)

# Internal helper for AI move
def _get_next_move(board_state):
    url = os.environ.get("ENDPOINT_URL")
    key = os.environ.get("OCP_APIM_SUBSCRIPTION_KEY")
    
    if not url or not key:
        logging.warning("AI credentials missing, falling back to random move")
        import random
        from tic_tac_toe_game import TicTacToe
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
            "game_state": [i for l in board_state for i in l]
        }
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        response.raise_for_status()
        return response.json()["move"]
    except Exception as e:
        logging.error(f"AI Service Error: {e}")
        raise Exception("Failed to get move from AI server")

@app.route('/')
def index():
    if 'game' not in app.config:
        app.config['game'] = game_logic.init_game()
    return render_template('index.html')

@app.route('/make_move', methods=['POST'])
def make_move():
    data = request.get_json()
    row, col = data.get('row'), data.get('col')
    game = app.config.get('game')

    if row is None or col is None:
        return jsonify({'error': 'Missing coordinates'}), 400
    
    try:
        # Player Move (X)
        game_logic.make_move(game, row, col)
        
        # Check if game ended after player move
        if not game.is_game_over():
            # AI Move (O)
            board_state = game.board.tolist()
            move_index = _get_next_move(board_state)
            valid_moves = game.get_valid_moves()
            
            if move_index < len(valid_moves):
                ai_row, ai_col = valid_moves[int(move_index)]
                game.make_move(ai_row, ai_col)

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
    game = app.config.get('game')
    if game:
        game.reset()
    else:
        app.config['game'] = game_logic.init_game()
    return jsonify({'board': app.config['game'].board.tolist()})

if __name__ == '__main__':
    import numpy as np # Needed for fallback logic
    with app.app_context():
        if 'game' not in app.config:
            app.config['game'] = game_logic.init_game()
    app.run(debug=True, port=8000)
