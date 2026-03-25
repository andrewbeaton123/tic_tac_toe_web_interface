# Tic Tac Toe Web Interface

A simple web-based Tic Tac Toe game built with Python.

## Features

- Play Tic Tac Toe in your browser
- Interactive and user-friendly interface
- Single-player and/or two-player modes (customize as needed)
- Clean, readable codebase
- **Input Validation:** The application now includes input validation to ensure that the row and column inputs are valid integers within the allowed range.

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/tic_tac_toe_web_interface.git
    cd tic_tac_toe_web_interface
    ```

2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Ensure API endpoint is running for opponent

4. Ensure that ngrok endpoint is running in the same location as the api

5. Ensure Azure API authentication is enabled with the current ngrok address

## Usage

1. Run the application:
    ```bash
    python app.py
    ```
2. Open your browser and go to `http://localhost:8000`

## Project Structure

```
tic_tac_toe_web_interface/
├── app.py
├── static/
├── templates/
├── requirements.txt
└── README.md
```

## Contributing

Contributions are welcome! Please open issues or submit pull requests.

## License

This project is licensed under the MIT License.
