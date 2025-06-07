# DexcomData

DexcomData is a Python library for monitoring continuous glucose data from the official Dexcom server. This library connects to the Dexcom API to retrieve and monitor continuous glucose monitoring (CGM) data, providing both one-time data retrieval and continuous monitoring capabilities for personal development and testing purposes.

## Features

- **OAuth2 Authentication**: Secure authentication with Dexcom API using authorization code flow
- **Glucose Data Retrieval**: Fetch historical glucose readings with customizable time ranges
- **Real-time Monitoring**: Continuous glucose monitoring with configurable update intervals
- **Unit Conversion**: Built-in conversion between mg/dL and mmol/L
- **Token Management**: Automatic token refresh handling
- **Command Line Interface**: Easy-to-use CLI for quick glucose checks
- **Callback Support**: Custom callback functions for monitoring events

## Prerequisites

- Python 3.8+ (supports Python 3.8-3.13)
- Dexcom developer account (for API credentials obtained from requesting Dexcom)
- Active Dexcom CGM system
- Internet connection for API access

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/dexcom-glucose-monitor.git
   cd dexcom-glucose-monitor
   ```

2. Install the package:
   ```bash
   pip install DexcomData
   ```

   Or for development:
   ```bash
   pip install -e .
   ```

3. Install with optional dependencies:
   ```bash
   # For development tools
   pip install DexcomData[dev]
   
   # For web interface support (if needed)
   pip install DexcomData[web]
   ```

## Configuration

1. Create a `.env` file in the project root:
   ```env
   DEXCOM_CLIENT_ID=your_client_id_here
   DEXCOM_CLIENT_SECRET=your_client_secret_here
   DEXCOM_REDIRECT_URI=http://localhost:5000/callback
   DEXCOM_BASE_URL=https://api.dexcom.jp/v2
   ```

2. Obtain API credentials from your Dexcom developer account
3. Update the environment variables with your actual credentials

**Note**: The library requires only `requests>=2.25.0` as a core dependency. Environment variable loading with `python-dotenv` is optional but recommended for easier configuration management.

## Usage

### Quick Start

```python
from DexcomData import DexcomAuth, DexcomData, format_glucose_reading
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize authentication
auth = DexcomAuth(
    client_id=os.getenv('DEXCOM_CLIENT_ID'),
    client_secret=os.getenv('DEXCOM_CLIENT_SECRET')
)

# Get authorization (opens browser)
auth.open_browser_auth()
# Follow browser prompts and enter the authorization code
auth_code = input("Enter authorization code: ")
auth.exchange_code_for_tokens(auth_code)

# Retrieve glucose data
data = DexcomData()
latest_reading = data.get_latest_reading(auth.access_token)
print(format_glucose_reading(latest_reading))
```

### Continuous Monitoring

```python
from DexcomData import DexcomMonitor

# Set up monitoring
monitor = DexcomMonitor(auth, data, update_interval=300)  # 5-minute intervals

# Optional: Set custom callback
def glucose_alert(reading):
    glucose_value = reading.get('value', 0)
    if glucose_value > 200:  # mg/dL
        print(f"HIGH GLUCOSE ALERT: {glucose_value} mg/dL")

monitor.set_callback(glucose_alert)

# Start monitoring
monitor.start_monitoring()

# Stop monitoring when done
# monitor.stop_monitoring()
```

### Command Line Usage

```bash
# Run the main script
python main.py

# Or if installed as package with console script
dexcom-monitor
```

### Unit Conversion

```python
from DexcomData import mg_dl_to_mmol_l

glucose_mg_dl = 180
glucose_mmol_l = mg_dl_to_mmol_l(glucose_mg_dl)
print(f"{glucose_mg_dl} mg/dL = {glucose_mmol_l} mmol/L")
```

## API Reference

### DexcomAuth
- `get_auth_url()`: Get OAuth2 authorization URL
- `open_browser_auth()`: Open browser for authentication
- `exchange_code_for_tokens(auth_code)`: Exchange auth code for tokens
- `refresh_access_token()`: Refresh expired access token
- `is_authenticated()`: Check authentication status

### DexcomData
- `get_glucose_data(access_token, hours_back=6)`: Retrieve glucose readings
- `get_latest_reading(access_token)`: Get most recent glucose reading
- `debug_data_availability(access_token)`: Test data availability across time ranges

### DexcomMonitor
- `start_monitoring()`: Begin continuous monitoring
- `stop_monitoring()`: Stop monitoring
- `set_callback(callback_function)`: Set custom callback for new readings
- `get_current_reading()`: Get cached latest reading

## Project Structure

```
DexcomData/
├── DexcomData/
│   ├── __init__.py          # Package initialization and exports
│   ├── DexcomDataCode.py    # Main library code
│   └── main.py              # CLI entry point
├── setup.py                 # Package configuration
├── pyproject.toml          # Modern package configuration (optional)
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
├── README.md               # This file
└── LICENSE                 # License information
```

## Error Handling

The library includes comprehensive error handling for:
- Network connectivity issues
- API rate limiting
- Token expiration and refresh
- Invalid authentication
- Missing or malformed data

## Development

For development setup:

```bash
# Clone repository
git clone https://github.com/yourusername/dexcom-glucose-monitor.git
cd dexcom-glucose-monitor

# Install in development mode
pip install -e .[dev]

# Run tests (if available)
python -m pytest tests/

# Code formatting
black DexcomData/

# Linting
flake8 DexcomData/

# Type checking
mypy DexcomData/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational and development use only. See [LICENSE](LICENSE) for details.

## Disclaimer

This project is not affiliated with or endorsed by Dexcom, Inc. This library is intended for personal use and development purposes only. Always consult with healthcare professionals for medical decisions. Use at your own risk.

## Support

For issues and questions:
- Check existing GitHub issues
- Create a new issue with detailed information
- Include error messages and system information

## Changelog

### v0.1.0
- Initial release
- OAuth2 authentication
- Basic data retrieval
- Continuous monitoring
- Unit conversion utilities