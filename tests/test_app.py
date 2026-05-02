import pytest
import typing
from unittest.mock import patch, MagicMock
from flask.testing import FlaskClient

from tic_tac_toe_web_interface.app import app

@pytest.fixture
def client() -> typing.Generator[FlaskClient, None, None]:
    """Setup a testing client for the Flask application."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def authenticated_client(client: FlaskClient) -> FlaskClient:
    """A test client that includes a mocked user token in the session."""
    with client.session_transaction() as sess:
        sess['user_token'] = {
            'access_token': 'fake-test-token',
            'name': 'Test User'
        }
    return client

def test_index_page(authenticated_client: FlaskClient) -> None:
    """Ensure the main landing page loads correctly when authenticated."""
    response = authenticated_client.get('/')
    assert response.status_code == 200
    assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data

def test_index_redirect_if_not_logged_in(client: FlaskClient) -> None:
    """Ensure unauthenticated users are redirected to /login."""
    response = client.get('/')
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

def test_reset_game(authenticated_client: FlaskClient) -> None:
    """Ensure resetting generates a clean 3x3 board."""
    response = authenticated_client.post('/reset')
    assert response.status_code == 200
    data = response.get_json()
    assert 'board' in data
    assert data['board'] == [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

@patch('tic_tac_toe_web_interface.app._get_next_move')
def test_make_move_valid(mock_get_next_move: MagicMock, authenticated_client: FlaskClient) -> None:
    """Test making a valid move and verify AI responses are handled."""
    # Mock AI to return the first index from the list of valid moves (index 0)
    mock_get_next_move.return_value = (0, False)

    # Initialize the session
    authenticated_client.post('/reset')

    # Player 1 makes a move at row 0, col 0
    response = authenticated_client.post('/make_move', json={'row': 0, 'col': 0})
    assert response.status_code == 200
    data = response.get_json()

    board = data['board']
    assert board[0][0] == 1  # Player 1's move

    # After (0,0), the first available valid move is expected to be (0,1).
    # AI (Player 2) takes this spot because mock_get_next_move returns index 0.
    assert board[0][1] == 2
    assert data['fallback'] is False
    assert data['over'] is False

def test_make_move_missing_coords(authenticated_client: FlaskClient) -> None:
    """Test error handling for missing board coordinates."""
    authenticated_client.post('/reset')
    response = authenticated_client.post('/make_move', json={})
    assert response.status_code == 400
    assert response.get_json() == {'error': 'Missing coordinates'}

def test_make_move_invalid_spot(authenticated_client: FlaskClient) -> None:
    """Test making a move on an already occupied spot."""
    with patch('tic_tac_toe_web_interface.app._get_next_move') as mock_ai:
        # Prevent the AI from accidentally placing an O on (1,1) if it was open
        mock_ai.return_value = (1, False)
        authenticated_client.post('/reset')

        # Player 1 plays at (1,1)
        authenticated_client.post('/make_move', json={'row': 1, 'col': 1})

        # Player 1 attempts to play at (1,1) again (invalid)
        response = authenticated_client.post('/make_move', json={'row': 1, 'col': 1})
        assert response.status_code == 400
        assert response.get_json() == {"error": "Invalid move."}

@patch.dict('os.environ', {
    'ENDPOINT_URL': 'http://fake-api',
    'OCP_APIM_SUBSCRIPTION_KEY': 'fake-key'
})
def test_make_move_fallback(authenticated_client: FlaskClient) -> None:
    """Test falling back to random local moves if the AI API fails."""
    # Mock requests.post to simulate an API failure
    with patch('requests.post') as mock_post:
        mock_post.side_effect = Exception("API Down")

        authenticated_client.post('/reset')
        response = authenticated_client.post('/make_move', json={'row': 2, 'col': 2})
        assert response.status_code == 200
        data = response.get_json()

        # AI should have played a fallback random move successfully
        assert data['fallback'] is True
        board_flat = [spot for row in data['board'] for spot in row]
        assert board_flat.count(2) == 1
