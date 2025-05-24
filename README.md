# DexcomServer

DexcomServer is a Python-based server that connects to the Dexcom sandbox API, fetches glucose data, and displays it. This project is intended for development and testing purposes using Dexcom's sandbox environment.

## Features

- Connects to Dexcom sandbox API
- Fetches and displays glucose data
- Simple server setup for local development

## Prerequisites

- Python 3.7+
- Dexcom developer sandbox account (for API credentials)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/DexcomServer.git
   cd DexcomServer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Update your API credentials and any necessary configuration in the appropriate config file or environment variables as required by the code.

## Usage

Start the server:
```bash
python main.py
```
Replace `main.py` with the actual entry point if different.

Access the server in your browser or via API client as described in the code documentation.

## Project Structure

- `main.py` - Entry point for the server
- `requirements.txt` - Python dependencies
- Other modules as required

## License

This project is for educational and development use only. See [LICENSE](LICENSE) for details.

## Disclaimer

This project is not affiliated with or endorsed by Dexcom, Inc. Use at your own risk.
