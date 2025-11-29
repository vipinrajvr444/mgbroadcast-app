# service.py

import time
import plyer
import schedule
import random
from datetime import datetime
import os
import json 
from kivy.utils import platform 
from jnius import autoclass 

# --- Configuration & Data ---

# CRITICAL FIX: Get the correct writable Android User Data Directory 
if platform == 'android':
    # This uses jnius to get the exact path where main.py saves the config file
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    CONFIG_DIR = PythonActivity.getApplicationContext().getFilesDir().getAbsolutePath()
else:
    CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(CONFIG_DIR, 'mgbroadcast_config.json')
NUM_MESSAGES = 5

# Define minimum necessary default structure for safety
DEFAULT_MESSAGE_SLOT = {"name": "Default Slot", "service_time": "08:00", "header": "Hello", "body": "Default Message", "quote": "Default quote"}
DEFAULT_GLOBAL_CONFIG = {"sound": True, "vibrate": True}


# --- Service Logic ---

def load_config():
    """Reads the JSON configuration file."""
    
    default_config = {
        "global": DEFAULT_GLOBAL_CONFIG,
        "messages": [DEFAULT_MESSAGE_SLOT] * NUM_MESSAGES
    }
    
    if not os.path.exists(CONFIG_FILE):
        return default_config

    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Ensure the config has all required fields (messages)
            if 'messages' not in config or len(config['messages']) != NUM_MESSAGES:
                 return default_config 
            return config
    except (json.JSONDecodeError, FileNotFoundError):
        return default_config

def generate_full_message(message_data):
    """Generates the full message using the saved template."""
    header = message_data.get('header', "")
    body_template = message_data.get('body', "")
    quote = message_data.get('quote', "")
    day_name = datetime.now().strftime("%A") 

    # Replace placeholders
    formatted_body = body_template.replace("{day}", day_name).replace("{quote}", quote)
    
    # Emojis will work perfectly here due to UTF-8 encoding maintained throughout
    full_message = f"{header}\n\n{formatted_body}"
    return full_message


def create_notification_job(message_data, global_config):
    """Factory function to create a job that sends a notification for a specific slot."""
    def send_notification():
        full_message = generate_full_message(message_data)
        
        plyer.notification.notify(
            title=f"MGBroadcast: {message_data['name']}",
            message=full_message, 
            app_name='MGBroadcast',
            ticker=f"New message scheduled for {message_data['name']}",
            timeout=10, 
            vibrate=global_config.get('vibrate', True)
        )
        # Log to the Android system log for monitoring
        print(f"Notification triggered for '{message_data['name']}' at {datetime.now().strftime('%H:%M')}")
    return send_notification

def start_daily_schedule():
    """Loads the config and schedules all 5 messages."""
    
    config = load_config()
    global_config = config['global']
    
    print(f"Service running. Configuration loaded from: {CONFIG_FILE}")
    
    # 1. Clear any old schedule
    schedule.clear()
    
    # 2. Schedule all 5 messages
    for i, message_data in enumerate(config['messages']):
        
        # Ensure 'service_time' is available (it's added by main.py on save)
        target_time = message_data.get('service_time') 
        
        if target_time:
            # Create a unique job function for each message slot
            job = create_notification_job(message_data, global_config)
            
            # Schedule the job
            schedule.every().day.at(target_time).do(job)
            print(f"   -> Scheduled Slot {i+1} ('{message_data['name']}') for {target_time}.")
        else:
            print(f"   -> Warning: Slot {i+1} ('{message_data['name']}') skipped (No service_time found).")


    while True:
        # Check the schedule every 60 seconds
        schedule.run_pending()
        time.sleep(60)

# The service entry point
if __name__ == '__main__':
    start_daily_schedule()
