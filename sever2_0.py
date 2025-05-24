from flask import Flask, request
import requests
import webbrowser
import threading
import time
from dotenv import load_dotenv
import os
app = Flask(__name__)
load_dotenv()

# global parameters
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = 'http://localhost:5000/callback'
AUTH_URL = 'https://sandbox-api.dexcom.com/v2/oauth2/login'
#AUTH_URL = 'https://api.dexcom.jp/v2/oauth2/login?client_id={your_client_id}&redirect_uri={your_redirect_uri}&response_type=code&scope=offline_access&state={your_state_value}'
TOKEN_URL = 'https://sandbox-api.dexcom.com/v2/oauth2/token'
#TOKEN_UEL = 'https://api.dexcom.jp/v2/oauth2/token'
DATA_URL = 'https://sandbox-api.dexcom.com/v2/users/self/egvs'
#DATA_URL = "https://api.dexcom.jp/v3/users/self/egvs"

# Store tokens
access_token = None
refresh_token = None

def open_browser():
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'offline_access'
    }
    url = AUTH_URL + '?' + requests.compat.urlencode(params) #open the url with client id and local ip 
    webbrowser.open(url)

@app.route('/')
def home():
    return "Server is running. Please complete Dexcom login."

@app.route('/callback')
def callback(): #only for the first time to get the access and refresh token, calling it again means a new refresh token is issued everytime, doesnt make sense
    global access_token, refresh_token, latest_data
    auth_code = request.args.get('code')
    print(f"Received code: {auth_code}")
    
    if auth_code:
        token = get_access_token(auth_code)
        if token:
            access_token = token['access_token']
            refresh_token = token.get('refresh_token')
            latest_data = get_glucose_data(access_token)
            return "Authorization complete. Visit /data to view glucose data."
        else:
            return "Failed to retrieve access token."
    else:
        return "No authorization code found in the URL."

@app.route('/data')
def show_glucose_data():
    global latest_data
    if not access_token:
        return "Not authenticated. Restart and log in."
    if not latest_data:
        print("Debug, latest_data is None/empty")
        return "No data available."
    
    if 'egvs' in latest_data: #call latest_data to refresh when the
        values = latest_data['egvs']
        return f"Glucose value: {values[-1]['value']} mg/dL at {values[-1]['systemTime']}"
    return f"Error: {latest_data}"

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
        response = requests.post(TOKEN_URL, data=payload, headers=headers)
        print("Response Status Code:", response.status_code)
        print("Response Text:", response.text)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return None

def get_glucose_data(token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    params = {
        'startDate': '2023-01-01T00:00:00',
        'endDate': '2023-01-01T10:00:00'
    }
    response = requests.get(DATA_URL, headers=headers, params=params)
    try:
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {'error': str(e), 'body': response.text}

latest_data = None

def background_run(): #cache latest data
    global access_token, refresh_token, latest_data
    while True: #refresh every 5 mins
        if access_token:
            print("fetching glucose data")
            try:
                latest_data = get_glucose_data(access_token)
                if 'error' in latest_data and '401' in latest_data['error']:
                    refresh_access_token()
                    if access_token:
                        latest_data = get_glucose_data(access_token)
        
                print(f"Latest dataa: {latest_data}")
            except Exception as e:
                print(f"Error fetching data:{e}")
        else:
            print("no token")
        print("BG Running")
        time.sleep(300)    
    
def refresh_access_token():
    global access_token, refresh_token
    
    payload ={'client_id': CLIENT_ID,
     'client_secret': CLIENT_SECRET,
     'grant_type': 'refresh_token',
     'refresh_token': refresh_token, 
     'redirect_uri': REDIRECT_URI}
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        response = requests.post(TOKEN_URL, data=payload, headers=headers)
        print("Refresh response:", response.text)
        response.raise_for_status()
        token_data = response.json()
        access_token = token_data['access_token']
        refresh_token = token_data.get('refresh_token', refresh_token)
        print('access token refreshed')
        return access_token    
    except Exception as e:
        print(f"Error occurred: {e}")
        access_token = None #force re-auth if cant refresh
        
if __name__ == '__main__':
    print("Starting Flask server at http://localhost:5000 ...")
    threading.Thread(None, None, background_run, True).start()
    threading.Timer(1, open_browser).start()
    app.run(port=5000)