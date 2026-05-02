import os
import logging
import random
import requests
import pickle
import base64
import numpy as np
import msal
from typing import Any, cast
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
from tic_tac_toe_game import TicTacToe

load_dotenv()
app = Flask(__name__)
# Use a consistent secret key for sessions
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-key-789456123")
logging.basicConfig(level=logging.INFO)

# Azure Entra Config
CLIENT_ID = os.environ.get("AZURE_CLIENT_ID")
CLIENT_SECRET = os.environ.get("AZURE_CLIENT_SECRET")
TENANT_ID = os.environ.get("AZURE_TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
# The scope you defined: api://<CLIENT_ID>/users
API_SCOPE = os.environ.get("API_SCOPE")
SCOPE = [API_SCOPE] if API_SCOPE else ["User.Read"]

def _build_msal_app() -> msal.ConfidentialClientApplication:
    return msal.ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY,
        client_credential=CLIENT_SECRET)

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
        return cast(TicTacToe, pickle.loads(game_data))
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
    moves = temp_game.get_valid_moves()
    # moves is a numpy array of [row, col] pairs
    return random.choice(range(len(moves))) if len(moves) > 0 else 0


def _get_next_move(board_state: list[list[int]]) -> tuple[int, bool]:
    """Call the AI service and return a (move_index, fallback_flag) tuple."""
    url = os.environ.get("ENDPOINT_URL")

    # In User Identity flow, we use the JWT from the session
    token_dict = session.get("user_token")
    if not token_dict:
        logging.warning("No user token found in session, AI move will fail")
        return _random_move(board_state), True

    access_token = token_dict.get("access_token")

    if not url or not access_token:
        logging.warning("AI credentials or token missing, falling back to random move")
        return _random_move(board_state), True

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        # Some Azure APIM configurations still require the subscription key
        key = os.environ.get("OCP_APIM_SUBSCRIPTION_KEY")
        if key:
            headers["ocp-apim-subscription-key"] = key

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
    if not session.get("user_token"):
        return redirect(url_for("login"))
    return render_template('index.html')


@app.route("/login")
def login() -> Any:
    msal_app = _build_msal_app()
    redirect_uri = url_for("authorized", _external=True)
    logging.info(f"Generated Redirect URI for Login: {redirect_uri}")
    auth_url = msal_app.get_authorization_request_url(
        SCOPE,
        redirect_uri=redirect_uri)
    return redirect(auth_url)


@app.route("/getAToken")  # Must match the Redirect URI in Entra
def authorized() -> Any:
    redirect_uri = url_for("authorized", _external=True)
    logging.info(f"Generated Redirect URI for Callback: {redirect_uri}")

    if request.args.get('error'):
        return f"Login Error: {request.args.get('error_description')}"

    if request.args.get('code'):
        msal_app = _build_msal_app()
        result = msal_app.acquire_token_by_authorization_code(
            request.args['code'],
            scopes=SCOPE,
            redirect_uri=redirect_uri)
        if "error" in result:
            logging.error(f"MSAL Error: {result.get('error')}, Description: {result.get('error_description')}")
            return f"Login failure: {result.get('error_description')}"

        # MINIMIZE SESSION SIZE: Flask sessions are stored in cookies (max 4KB).
        # We only store what we strictly need for the UI and the API call.
        session["user_token"] = {
            "access_token": result.get("access_token"),
            "name": result.get("id_token_claims", {}).get("name")
        }
    return redirect(url_for("index"))


@app.route('/logout')
def logout() -> Any:
    # Clear session and redirect to Microsoft logout for a clean slate
    session.clear()
    tenant = os.environ.get("AZURE_TENANT_ID")
    return redirect(
        f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/logout"
        f"?post_logout_redirect_uri={url_for('index', _external=True)}"
    )

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
        logging.info(f"Player moved to {row}, {col}")

        # AI Move (O) if game not over
        fallback = False
        if not game.is_game_over():
            board_state = game.board.tolist()
            move_index, fallback = _get_next_move(board_state)
            valid_moves = game.get_valid_moves()

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
            winner = int(game.winner) if game.winner else 0

        return jsonify({
            'board': game.board.tolist(),
            'winner': winner,
            'over': game.is_game_over(),
            'fallback': fallback
        })

    except ValueError as e:
        logging.error(f"ValueError in make_move: {e}")
        return jsonify({"error": "Invalid move."}), 400
    except Exception as e:
        logging.exception(f"Unexpected Exception in make_move: {e}")
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
