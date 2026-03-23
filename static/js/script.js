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

    function setStatus(html, isThinking = false) {
        statusEl.innerHTML = html;
        if (isThinking) {
            statusEl.classList.add('thinking');
        } else {
            statusEl.classList.remove('thinking');
        }
    }

    function setWaiting(isWaiting) {
        waiting = isWaiting;
        board.classList.toggle('disabled', isWaiting);
        board.classList.toggle('ai-thinking', isWaiting);
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

    // A simple client-side check to highlight the winning sequence
    // Since the API only returns the winner ID, we calculate the winning cells here
    // for visual flair.
    function highlightWinningLine(boardState) {
        const lines = [
            // Rows
            [[0, 0], [0, 1], [0, 2]],
            [[1, 0], [1, 1], [1, 2]],
            [[2, 0], [2, 1], [2, 2]],
            // Cols
            [[0, 0], [1, 0], [2, 0]],
            [[0, 1], [1, 1], [2, 1]],
            [[0, 2], [1, 2], [2, 2]],
            // Diags
            [[0, 0], [1, 1], [2, 2]],
            [[0, 2], [1, 1], [2, 0]]
        ];

        let winningCells = [];
        for (const line of lines) {
            const [a, b, c] = line;
            const v1 = boardState[a[0]][a[1]];
            const v2 = boardState[b[0]][b[1]];
            const v3 = boardState[c[0]][c[1]];
            
            if (v1 !== 0 && v1 === v2 && v1 === v3) {
                winningCells = line;
                break;
            }
        }

        if (winningCells.length > 0) {
            const cells = document.querySelectorAll('.cell');
            board.classList.add('game-over');
            winningCells.forEach(([r, c]) => {
                const index = r * 3 + c;
                cells[index].classList.add('win-highlight');
            });
        }
    }

    function handleCellClick(event) {
        if (gameOver || waiting) return;

        // If cell is already taken, do nothing
        if (event.target.textContent !== '') return;

        const index = event.target.dataset.index;
        const row = Math.floor(index / 3);
        const col = index % 3;

        setWaiting(true);
        setStatus('AI evaluating moves', true);

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
                    setStatus("Match ended in a <strong>Draw</strong>");
                    board.classList.add('game-over'); // Fades all cells slightly
                } else {
                    const symbol = data.winner === 1 ? 'X' : 'O';
                    const who = data.winner === 1 ? 'You win' : 'AI wins';
                    setStatus(`<strong>${who}</strong> (${symbol})`);
                    highlightWinningLine(data.board);
                }
                resetButton.textContent = 'Play Again';
            } else {
                setStatus('Your turn \u2014 you are <strong>X</strong>');
            }
            setWaiting(false);
        })
        .catch(error => {
            console.error('Error:', error);
            setStatus('<span class="error">Network error</span>');
            setWaiting(false);
        });
    }

    function resetGame() {
        // Clear win highlights early for UX snappiness
        board.classList.remove('game-over');
        document.querySelectorAll('.cell').forEach(c => c.classList.remove('win-highlight'));
        
        setStatus('Initializing game', true);

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
            resetButton.textContent = 'New Game';
        })
        .catch(error => {
            console.error('Error:', error);
            setStatus('<span class="error">Network error initializing</span>');
            setWaiting(false);
        });
    }

    // Initialize the board state
    resetGame();
});
