import time
import datetime
from dotenv import load_dotenv
import os
from pydexcom import Dexcom
import threading

# Load environment variables
load_dotenv()

# Get credentials from .env file
DEXCOM_USERNAME = os.getenv("USERNAME")
DEXCOM_PASSWORD = os.getenv("PASSWORD")

def print_to_serial(message):
    """Print formatted message to serial monitor (console)"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def display_glucose_data(dexcom_session):
    try:
        # Get current glucose reading
        current_bg = dexcom_session.get_current_glucose_reading()
        
        if current_bg:
            print_to_serial("=" * 50)
            print_to_serial("CURRENT GLUCOSE READING")
            print_to_serial(f"Value: {current_bg.value} mg/dL")
            print_to_serial(f"Trend Arrow: {current_bg.trend_arrow}")
            print_to_serial(f"Time: {current_bg.time}")
            print_to_serial("=" * 50)
        else:
            print_to_serial("No current glucose reading available")
            
    except Exception as e:
        print_to_serial(f"Error fetching glucose data: {e}")

def continuous_monitor():
    """Main monitoring function that runs every 5 minutes"""
    print_to_serial("Starting Dexcom Glucose Monitor with pydexcom")
    print_to_serial("Update interval: 5 minutes")
    print_to_serial("-" * 50)
    
    # Validate credentials
    if not DEXCOM_USERNAME or not DEXCOM_PASSWORD:
        print_to_serial("Missing DEXCOM_USERNAME or DEXCOM_PASSWORD in .env file")
        return
    
    try:
        # Initialize Dexcom session
        print_to_serial("Authenticating with Dexcom...")
        

        dexcom = Dexcom(username=DEXCOM_USERNAME, password=DEXCOM_PASSWORD, region = 'apac')
        
        print_to_serial("Authentication successful!")
        # Start continuous monitoring
        update_count = 0
        while True:
            update_count += 1
            print_to_serial(f"--- Update #{update_count} ---")
            
            # Display current glucose data
            display_glucose_data(dexcom)
            print_to_serial("Next update in 5 minutes...")
            
            # Wait 5 minutes
            time.sleep(300)  # 300 seconds = 5 minutes
            
    except Exception as e:
        print_to_serial(f"Authentication or monitoring error: {e}")


def enhanced_monitor():
    """Enhanced monitoring with device info and better error handling"""
    print_to_serial("Starting Enhanced Dexcom Monitor")
    print_to_serial("-" * 50)
    
    if not DEXCOM_USERNAME or not DEXCOM_PASSWORD:
        print_to_serial("Missing credentials in .env file")
        print_to_serial("Required: DEXCOM_USERNAME, DEXCOM_PASSWORD")
        return
    
    try:
        # Initialize with retry logic
        max_retries = 3
        dexcom = None
        
        for attempt in range(max_retries):
            try:
                print_to_serial(f"Authentication attempt {attempt + 1}/{max_retries}...")
                dexcom = Dexcom(username=DEXCOM_USERNAME, password=DEXCOM_PASSWORD, region='apac')
                print_to_serial("Authentication successful!")
                break
            except Exception as e:
                print_to_serial(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print_to_serial("Retrying in 10 seconds...")
                    time.sleep(10)
        
        if not dexcom:
            print_to_serial("All authentication attempts failed")
            return
        
        # Continuous monitoring with error recovery
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        while True:
            try:
                display_glucose_data(dexcom)
                consecutive_errors = 0  # Reset error counter on success
                
            except Exception as e:
                consecutive_errors += 1
                print_to_serial(f"Error in monitoring loop: {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    print_to_serial(f"Too many consecutive errors ({consecutive_errors})")
                    print_to_serial("Attempting to re-authenticate...")
                    try:
                        dexcom = Dexcom(username = DEXCOM_USERNAME, password = DEXCOM_PASSWORD, region = 'apac')
                        print_to_serial("Re-authentication successful!")
                        consecutive_errors = 0
                    except Exception as auth_error:
                        print_to_serial(f"Re-authentication failed: {auth_error}")
                        print_to_serial("Pausing for 15 minutes before retry...")
                        time.sleep(900)  # Wait 15 minutes
                        continue
            
            print_to_serial("Next update in 5 minutes...")
            time.sleep(300)
            
    except KeyboardInterrupt:
        print_to_serial("Monitoring stopped by user")
    except Exception as e:
        print_to_serial(f"Fatal error: {e}")

if __name__ == '__main__':
    # Choose which version to run:
    
    # Simple version:
    # continuous_monitor()
    
    # Enhanced version with better error handling:
    enhanced_monitor()