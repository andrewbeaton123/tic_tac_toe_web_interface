document.addEventListener('DOMContentLoaded', () => {
    const board = document.getElementById('board');
    const resetButton = document.getElementById('reset-button');
    const statusEl = document.getElementById('status');
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const fallbackNotif = document.getElementById('fallback-notification');
    
    let gameOver = false;
    let waiting = false;

    // Theme logic
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const savedTheme = localStorage.getItem('theme');
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.documentElement.setAttribute('data-theme', 'dark');
        setSunIcon();
    }

    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        if (currentTheme === 'dark') {
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
            setMoonIcon();
        } else {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
            setSunIcon();
        }
    });

    function setSunIcon() {
        themeIcon.innerHTML = '<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>';
    }

    function setMoonIcon() {
        themeIcon.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>';
    }

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
            
            // Handle fallback notification
            if (data.fallback) {
                fallbackNotif.classList.remove('hidden');
            } else {
                fallbackNotif.classList.add('hidden');
            }

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
            fallbackNotif.classList.add('hidden'); // Clear on reset
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
