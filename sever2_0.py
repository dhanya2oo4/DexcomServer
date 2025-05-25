from flask import Flask, request
import requests
import webbrowser
import threading
import time
import datetime
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

# Global parameters
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = 'http://localhost:5000/callback'
AUTH_URL = 'https://sandbox-api.dexcom.com/v2/oauth2/login'
TOKEN_URL = 'https://sandbox-api.dexcom.com/v2/oauth2/token'
DATA_URL = 'https://sandbox-api.dexcom.com/v2/users/self/egvs'

# Store tokens
access_token = None
refresh_token = None
latest_data = None

def print_to_serial(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def open_browser():
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'offline_access'
    }
    url = AUTH_URL + '?' + requests.compat.urlencode(params)
    print_to_serial("Opening browser for Dexcom authentication...")
    webbrowser.open(url)

@app.route('/')
def home():
    return "Server is running. Please complete Dexcom login."

@app.route('/callback')
def callback():
    global access_token, refresh_token, latest_data
    auth_code = request.args.get('code')
    print_to_serial(f"Received authorization code: {auth_code[:10]}...")
    
    if auth_code:
        token = get_access_token(auth_code)
        if token:
            access_token = token['access_token']
            refresh_token = token.get('refresh_token')
            print_to_serial("Authentication successful! Access token obtained.")
            
            # Get initial glucose data
            latest_data = get_glucose_data(access_token)
            display_glucose_data()
            
            return "Authorization complete. Check your console for glucose readings."
        else:
            print_to_serial("Failed to retrieve access token.")
            return "Failed to retrieve access token."
    else:
        print_to_serial("No authorization code found in callback URL.")
        return "No authorization code found in the URL."

@app.route('/data')
def show_glucose_data():
    global latest_data
    if not access_token:
        return "Not authenticated. Restart and log in."
    if not latest_data:
        return "No data available."
    
    if 'egvs' in latest_data and latest_data['egvs']:
        values = latest_data['egvs']
        latest_reading = values[-1]
        return f"Glucose: {latest_reading['value']} mg/dL at {latest_reading['systemTime']}"
    return f"Error: {latest_data}"

def display_glucose_data():
    """Display glucose data on serial monitor"""
    global latest_data
    
    if not latest_data:
        print_to_serial("No glucose data available")
        return
    
    if 'error' in latest_data:
        print_to_serial(f"Error fetching glucose data: {latest_data['error']}")
        return
    
    if 'egvs' in latest_data and latest_data['egvs']:
        values = latest_data['egvs']
        if values:
            latest_reading = values[-1]
            glucose_value = latest_reading['value']
            system_time = latest_reading['systemTime']
            
            # Convert system time to readable format
            try:
                dt = datetime.datetime.fromisoformat(system_time.replace('Z', '+00:00'))
                readable_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            except:
                readable_time = system_time
            
            print_to_serial("=" * 50)
            print_to_serial(f"GLUCOSE READING")
            print_to_serial(f"Value: {round(glucose_value/18.018, 2)} mmol/L")
            print_to_serial(f"Time:  {readable_time}")
            print_to_serial(f"Total readings: {len(values)}")
            print_to_serial("=" * 50)
        else:
            print_to_serial("No glucose readings in response")
    else:
        print_to_serial("Unexpected data format received")

def get_access_token(auth_code):
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    try:
        print_to_serial("Requesting access token...")
        response = requests.post(TOKEN_URL, data=payload, headers=headers)
        response.raise_for_status()
        print_to_serial("Access token retrieved successfully")
        return response.json()
    except requests.exceptions.RequestException as e:
        print_to_serial(f"Error getting access token: {e}")
        return None

def get_glucose_data(token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    # Get data from the last 6 hours to ensure we have recent readings
    end_time = datetime.datetime.now(datetime.timezone.utc)
    start_time = end_time - datetime.timedelta(hours=6)
    
    params = {
        'startDate': start_time.strftime('%Y-%m-%dT%H:%M:%S'),
        'endDate': end_time.strftime('%Y-%m-%dT%H:%M:%S')
    }
    
    try:
        print_to_serial("Fetching glucose data from Dexcom API...")
        response = requests.get(DATA_URL, headers=headers, params=params)
        response.raise_for_status()
        print_to_serial("Glucose data retrieved successfully")
        return response.json()
    except requests.exceptions.RequestException as e:
        print_to_serial(f"Error fetching glucose data: {e}")
        return {'error': str(e), 'status_code': getattr(response, 'status_code', 'unknown')}

def refresh_access_token():
    global access_token, refresh_token
    
    if not refresh_token:
        print_to_serial("No refresh token available. Re-authentication required.")
        return False
    
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'redirect_uri': REDIRECT_URI
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        print_to_serial("Refreshing access token...")
        response = requests.post(TOKEN_URL, data=payload, headers=headers)
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data['access_token']
        refresh_token = token_data.get('refresh_token', refresh_token)
        print_to_serial("Access token refreshed successfully")
        return True
    except Exception as e:
        print_to_serial(f"Error refreshing token: {e}")
        access_token = None
        return False

def background_monitor():
    global access_token, refresh_token, latest_data
    print_to_serial("Background glucose monitor started")
    print_to_serial("   Updates every 5 minutes")
    
    while True:
        if access_token:
            try:
                print_to_serial("--- 5-Minute Update Check ---")
                latest_data = get_glucose_data(access_token)
                
                # Check if token expired
                if isinstance(latest_data, dict) and 'error' in latest_data:
                    if 'status_code' in latest_data and latest_data['status_code'] == 401:
                        print_to_serial("Token expired, attempting refresh...")
                        if refresh_access_token():
                            latest_data = get_glucose_data(access_token)
                        else:
                            print_to_serial("Token refresh failed. Please restart and re-authenticate.")
                            time.sleep(300)
                            continue
                
                # Display the glucose data
                display_glucose_data()
                
            except Exception as e:
                print_to_serial(f"Background monitor error: {e}")
        else:
            print_to_serial("Waiting for authentication...")
        
        # Wait 5 minutes (300 seconds) before next update
        print_to_serial("Next update in 5 minutes...")
        time.sleep(300)

if __name__ == '__main__':
    print_to_serial("    Starting Dexcom Glucose Monitor")
    print_to_serial(f"   Server: http://localhost:5000")
    print_to_serial(f"   Update interval: 5 minutes")
    print_to_serial("-" * 50)
    
    # Start background monitoring thread
    monitor_thread = threading.Thread(target=background_monitor, daemon=True)
    monitor_thread.start()
    
    # Open browser after 1 second delay
    threading.Timer(1, open_browser).start()
    
    # Start Flask server
    print_to_serial("Flask server starting...")
    app.run(port=5000, debug=False)