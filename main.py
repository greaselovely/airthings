import os
import json
import logging
import requests
from pathlib import Path
from inventory import clear
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

# Use custom CA bundle path
CERT_PATH = '/usr/local/share/ca-certificates/extra/cert_trust-decrypt.crt'

print(f"Using CA Bundle at: {CERT_PATH}")

inventory = "inventory.json"
log_file_name = "airthings.log"
home = os.path.expanduser('~')
log_path = os.path.join(home, "airthings")
log_full_path = os.path.join(log_path, log_file_name)
os.makedirs(log_path, exist_ok=True)

airthings_authorisation_url = "https://accounts-api.airthings.com/v1/token"
token_req_payload = {"grant_type": "client_credentials", "scope": "read:device:current_values"}

# Logging configuration
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler = RotatingFileHandler(log_full_path, maxBytes=524288, backupCount=5)
log_handler.setFormatter(log_formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

def send_ntfy_msg(ntfy_topic: str, message: str):
    url = f"https://ntfy.sh/{ntfy_topic}"
    headers = {'Content-Type': 'text/plain; charset=utf-8'}
    try:
        response = requests.post(url, data=message.encode('utf-8'), headers=headers, verify=CERT_PATH)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send message to {ntfy_topic}: {e}")

def airthings_auth():
    try:
        token_response = requests.post(airthings_authorisation_url, data=token_req_payload, allow_redirects=False, auth=(airthings_client_id, airthings_client_secret), verify=CERT_PATH)
        token_response.raise_for_status()
        token = token_response.json().get("access_token")
        return token
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to obtain Airthings access token: {e}")
        return None

def read_inventory(file_name):
    file_path = Path(__file__).resolve().parent / file_name
    with open(file_path, "r") as file:
        return json.load(file)

def convert_timestamp_to_time(timestamp):
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

def is_data_stale(timestamp: int, freshness_threshold_seconds: int = 3600) -> bool:
    current_time = datetime.now(timezone.utc).timestamp()
    data_age_seconds = current_time - timestamp
    return data_age_seconds >= freshness_threshold_seconds

def console_output(location, room, c_temp, f_temp, humi, batt):
    print(f"\t{location} {room}:")
    print(f"\t  Temp: {f_temp}°F / {c_temp}°C")
    print(f"\t  Humidity: {humi}%")
    print(f"\t  Battery: {batt}%")

def fetch_device_data(device_id, api_headers):
    device_url = f"https://ext-api.airthings.com/v1/devices/{device_id}/latest-samples"
    response = requests.get(url=device_url, headers=api_headers, verify=CERT_PATH)
    response.raise_for_status()
    return response.json()['data']

def process_device_data(location, room, device_data, thresholds, ntfy_url, is_sunday):
    global sunday_report
    timestamp, c_temp, humi, batt = device_data['time'], device_data['temp'], device_data['humidity'], device_data['battery']
    
    stale_message = ""
    if is_data_stale(timestamp, thresholds['freshness_threshold_seconds']):
        stale_message = f"{location} {room} is not reporting."
    
    f_temp = (c_temp * 9 / 5) + 32
    f_temp = float(f"{f_temp:0.2f}")
    console_output(location, room, c_temp, f_temp, humi, batt)
    logging.info(f"{location} {room} - Temp:{f_temp} Humidity:{humi} Batt:{batt}")

    if f_temp <= thresholds['f_temp_threshold']:
        message = f"Brrr it's cold!\n{location} {room} is {f_temp}°F."
        send_ntfy_msg(ntfy_url, message)
    
    if batt < thresholds['batt_threshold']:
        message = f"Battery Warning!\n{location} {room} is at {batt}%."
        send_ntfy_msg(ntfy_url, message)

    if is_sunday:
        sunday_report += f"{location} {room} is {f_temp}°F, battery is {batt}%\n"
    
    return stale_message

def main():
    global airthings_client_id, airthings_client_secret, sunday_report
    inventory_data = read_inventory('inventory.json')
    
    if not inventory_data:
        logging.error("Inventory data is not available. Please check the file.")
        return
    send_ntfy_msg(inventory_data["ntfy_url"], "Script Started...")
    
    airthings_client_id, airthings_client_secret = inventory_data["airthings_client_id"], inventory_data["airthings_client_secret"]

    thresholds = {
        'freshness_threshold_seconds': 3600,
        'f_temp_threshold': inventory_data["f_temp_threshold"],
        'batt_threshold': inventory_data["battery_threshold"]
    }

    token = airthings_auth()
    api_headers = {"Authorization": f"Bearer {token}"}
    now = datetime.now()
    is_sunday = now.weekday() == 6 and now.hour == 17 and now.minute == 0
    
    stale_data_messages = []
    sunday_report = "Weekly Report\n"

    try:
        for location, rooms in inventory_data["inventory"].items():
            for room, device_id in rooms.items():
                device_data = fetch_device_data(device_id, api_headers)
                
                stale_message = process_device_data(location, room, device_data, thresholds, inventory_data["ntfy_url"], is_sunday)

                if stale_message:
                    stale_data_messages.append(stale_message)
        
        if is_sunday:
            send_ntfy_msg(inventory_data["ntfy_url"], sunday_report)

        if stale_data_messages:
            consolidated_message = "Stale Data Notification:\n" + "\n".join(stale_data_messages)
            send_ntfy_msg(inventory_data["ntfy_url"], consolidated_message)

    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching device data: {e}")

if __name__ == "__main__":
    main()
