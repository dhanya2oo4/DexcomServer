from flask import Flask, request, jsonify
import requests
import threading
import time
import datetime
from dotenv import load_dotenv
import os
import json

app = Flask(__name__)
load_dotenv()

# Global parameters - UPDATE THESE FOR RENDER
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
# Change to render url
REDIRECT_URI = os.getenv("REDIRECT_URI", 'https://your-app-name.onrender.com/callback')

# actl urls
AUTH_URL = 'https://api.dexcom.com/v2/oauth2/login'  
TOKEN_URL = 'https://api.dexcom.com/v2/oauth2/token'  
DATA_URL = 'https://api.dexcom.com/v2/users/self/egvs'  

# Store tokens and data
access_token = None
refresh_token = None
latest_data = None
last_update = None

def print_to_serial(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    #log to a file for debugging on Render
    try:
        with open('/tmp/glucose_log.txt', 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass

@app.route('/')
def home():
    if access_token:
        return f"""
        <h2>Dexcom Glucose Monitor</h2>
        <p>Status: Authenticated</p>
        <p>Last update: {last_update or 'Never'}</p>
        <p><a href="/data">View Current Data</a></p>
        <p><a href="/api/glucose">API Endpoint for ESP32</a></p>
        """
    else:
        params = {
            'client_id': CLIENT_ID,
            'redirect_uri': REDIRECT_URI,
            'response_type': 'code',
            'scope': 'offline_access'
        }
        auth_url = AUTH_URL + '?' + requests.compat.urlencode(params)
        return f"""
        <h2>Dexcom Glucose Monitor</h2>
        <p>Status: Not authenticated</p>
        <p><a href="{auth_url}" target="_blank">Click here to authenticate with Dexcom</a></p>
        <p>After authentication, you'll be redirected back here.</p>
        """

@app.route('/callback')
def callback():
    #OAuth callback
    global access_token, refresh_token, latest_data, last_update
    auth_code = request.args.get('code')
    print_to_serial(f"Received authorization code: {auth_code[:10] if auth_code else 'None'}...")
    
    if auth_code:
        token = get_access_token(auth_code)
        if token:
            access_token = token['access_token']
            refresh_token = token.get('refresh_token')
            print_to_serial("Authentication successful! Access token obtained.")
            
            # Get initial glucose data
            latest_data = get_glucose_data(access_token)
            last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            display_glucose_data()
            
            return """
            <h2>Authentication Complete!</h2>
            <p>Your Dexcom account is now connected.</p>
            <p>The app will automatically fetch glucose data every 5 minutes.</p>
            <p><a href="/">Return to Home</a></p>
            <p><a href="/api/glucose">API Endpoint for ESP32</a></p>
            """
        else:
            print_to_serial("Failed to retrieve access token.")
            return "<h2>Authentication Failed </h2><p>Failed to retrieve access token.</p><p><a href='/'>Try Again</a></p>"
    else:
        print_to_serial("No authorization code found in callback URL.")
        return "<h2>Authentication Failed </h2><p>No authorization code found.</p><p><a href='/'>Try Again</a></p>"

@app.route('/data')
def show_glucose_data():
    global latest_data, last_update
    if not access_token:
        return "<h2>Not Authenticated</h2><p><a href='/'>Go to Home to authenticate</a></p>"
    
    if not latest_data:
        return "<h2>No Data Available</h2><p>Waiting for first glucose reading</p>"
    
    if 'egvs' in latest_data and latest_data['egvs']:
        values = latest_data['egvs']
        latest_reading = values[-1]
        glucose_mg = latest_reading['value']
        glucose_mmol = round(glucose_mg / 18.018, 1)
        timestamp = latest_reading['systemTime']
        
        try:
            dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            readable_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            readable_time = timestamp
            
        return f"""
        <h2>Latest Glucose Reading</h2>
        <p><strong>Glucose:</strong> {glucose_mmol} mmol/L ({glucose_mg} mg/dL)</p>
        <p><strong>Time:</strong> {readable_time}</p>
        <p><strong>Last Update:</strong> {last_update}</p>
        <p><strong>Total Readings:</strong> {len(values)}</p>
        <p><a href="/api/glucose">JSON API for ESP32</a></p>
        <p><a href="/">Back to Home</a></p>
        """
    
    return f"<h2>Error</h2><p>{latest_data}</p>"

@app.route('/api/glucose')
def api_glucose():
    if not access_token:
        return jsonify({'error': 'Not authenticated', 'status': 'error'}), 401
    
    if not latest_data:
        return jsonify({'error': 'No data available', 'status': 'waiting'}), 202
    
    if 'egvs' in latest_data and latest_data['egvs']:
        values = latest_data['egvs']
        latest_reading = values[-1]
        glucose_mg = latest_reading['value']
        glucose_mmol = round(glucose_mg / 18.018, 2)
        timestamp = latest_reading['systemTime']
        
        return jsonify({
            'status': 'success',
            'glucose_mmol': glucose_mmol,
            'glucose_mg': glucose_mg,
            'timestamp': timestamp,
            'last_update': last_update,
            'total_readings': len(values)
        })
    
    return jsonify({'error': 'Invalid data format', 'status': 'error'}), 500

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'authenticated': bool(access_token),
        'last_update': last_update,
        'timestamp': datetime.datetime.now().isoformat()
    })

def display_glucose_data(): #display in render logs
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
            
            try:
                dt = datetime.datetime.fromisoformat(system_time.replace('Z', '+08:00'))
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
    global access_token, refresh_token, latest_data, last_update
    print_to_serial("Background glucose monitor started")
    print_to_serial("Updates every 5 minutes")
    
    while True:
        if access_token:
            try:
                print_to_serial("--- 5-Minute Update Check ---")
                latest_data = get_glucose_data(access_token)
                
                # Check if token expired
                if isinstance(latest_data, dict) and 'error' in latest_data:
                    if 'status_code' in latest_data and str(latest_data['status_code']) == '401':
                        print_to_serial("Token expired, attempting refresh...")
                        if refresh_access_token():
                            latest_data = get_glucose_data(access_token)
                        else:
                            print_to_serial("Token refresh failed. Re-authentication required.")
                            time.sleep(300)
                            continue
                
                # Update timestamp and display data
                last_update = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                display_glucose_data()
                
            except Exception as e:
                print_to_serial(f"Background monitor error: {e}")
        else:
            print_to_serial("Waiting for authentication...")
        
        # Wait 5 minutes (300 seconds) before next update
        print_to_serial("Next update in 5 minutes...")
        time.sleep(300)

if __name__ == '__main__':
    print_to_serial("Starting Dexcom Glucose Monitor for Render")
    print_to_serial("Update interval: 5 minutes")
    print_to_serial("-" * 50)
    
    # Start background monitoring thread
    monitor_thread = threading.Thread(target=background_monitor, daemon=True)
    monitor_thread.start()
    
    # Get port from environment (Render requirement)
    port = int(os.environ.get('PORT', 5000))
    
    # Start Flask server
    print_to_serial(f"Flask server starting on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)