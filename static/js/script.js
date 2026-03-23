document.addEventListener('DOMContentLoaded', () => {
    const board = document.getElementById('board');
    const resetButton = document.getElementById('reset-button');
    const statusEl = document.getElementById('status');
    let gameOver = false;
    let waiting = false;

    resetButton.addEventListener('click', resetGame);

    // Generate the board
    for (let i = 0; i < 9; i++) {
        const cell = document.createElement('div');
        cell.classList.add('cell');
        cell.dataset.index = i;
        cell.addEventListener('click', handleCellClick);
        board.appendChild(cell);
    }

    function setStatus(html) {
        statusEl.innerHTML = html;
    }

    function setWaiting(isWaiting) {
        waiting = isWaiting;
        board.classList.toggle('disabled', isWaiting);
    }

    function updateBoard(boardState) {
        const cells = document.querySelectorAll('.cell');
        for (let i = 0; i < cells.length; i++) {
            const row = Math.floor(i / 3);
            const col = i % 3;
            const value = boardState[row][col];
            cells[i].textContent = value === 1 ? 'X' : value === 2 ? 'O' : '';
            cells[i].dataset.value = value === 1 ? 'x' : value === 2 ? 'o' : '';
        }
    }

    function handleCellClick(event) {
        if (gameOver || waiting) return;

        const index = event.target.dataset.index;
        const row = Math.floor(index / 3);
        const col = index % 3;

        setWaiting(true);
        setStatus('AI is thinking\u2026');

        fetch('/make_move', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ row, col })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                setStatus(`<span class="error">${data.error}</span>`);
                setWaiting(false);
                return;
            }
            updateBoard(data.board);
            if (data.winner !== null) {
                gameOver = true;
                if (data.winner === 0) {
                    setStatus("It\u2019s a <strong>draw</strong>! Click New Game to play again.");
                } else {
                    const symbol = data.winner === 1 ? 'X' : 'O';
                    const who = data.winner === 1 ? 'You win!' : 'AI wins!';
                    setStatus(`<strong>${who}</strong> ${symbol} takes it. Click New Game to play again.`);
                }
            } else {
                setStatus('Your turn \u2014 you are <strong>X</strong>');
            }
            setWaiting(false);
        })
        .catch(error => {
            console.error('Error:', error);
            setStatus('<span class="error">Network error. Please try again.</span>');
            setWaiting(false);
        });
    }

    function resetGame() {
        fetch('/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        })
        .then(response => response.json())
        .then(data => {
            updateBoard(data.board);
            gameOver = false;
            setWaiting(false);
            setStatus('Your turn \u2014 you are <strong>X</strong>');
        })
        .catch(error => console.error('Error:', error));
    }

    // Initialize the board state
    resetGame();
});
