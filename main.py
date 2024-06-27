import os
import json
import logging
import requests
from pathlib import Path
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

inventory = "inventory.json"
log_file_name = "airthings.log"
home = os.path.expanduser('~')
log_path = os.path.join(home, "airthings")
log_full_path = os.path.join(log_path, log_file_name)
os.makedirs(log_path, exist_ok=True)
now = datetime.now()

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
    """
    Send a notification message to a specified ntfy.sh topic.

    Args:
        ntfy_topic (str): The ntfy.sh topic to send the message to.
        message (str): The message content to be sent.

    Raises:
        RequestException: If there's an error sending the message.
    """
    url = f"https://ntfy.sh/{ntfy_topic}"
    headers = {'Content-Type': 'text/plain; charset=utf-8'}
    
    try:
        response = requests.post(url, data=message.encode('utf-8'), headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send message to {ntfy_topic}: {e}")

def airthings_auth():
    """
    Authenticate with the Airthings API and obtain an access token.

    Returns:
        str: The access token if successful, None otherwise.

    Raises:
        RequestException: If there's an error during the authentication process.
    """
    try:
        token_response = requests.post(airthings_authorisation_url, data=token_req_payload, allow_redirects=False, auth=(airthings_client_id, airthings_client_secret))
        token_response.raise_for_status()
        token = token_response.json().get("access_token")
        return token
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to obtain Airthings access token: {e}")
        return None

def read_from_file(file_name):
    """
    Read and parse JSON data from a file.

    Args:
        file_name (str): The name of the file to read from.

    Returns:
        dict: The parsed JSON data.
    """
    file_path = Path(__file__).resolve().parent / file_name
    with open(file_path, "r") as file:
        return json.load(file)

def convert_timestamp_to_time(timestamp):
    """
    Convert a UNIX timestamp to a formatted date-time string.

    Args:
        timestamp (int): The UNIX timestamp to convert.

    Returns:
        str: The formatted date-time string.
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

def is_data_stale(timestamp: int, freshness_threshold_seconds: int = 3600) -> bool:
    """
    Check if the data is stale based on its timestamp.

    Args:
        timestamp (int): The timestamp of the data.
        freshness_threshold_seconds (int): The threshold in seconds to consider data stale.

    Returns:
        bool: True if the data is stale, False otherwise.
    """
    current_time = datetime.now(timezone.utc).timestamp()
    data_age_seconds = current_time - timestamp
    return data_age_seconds >= freshness_threshold_seconds

def console_output(location, room, c_temp, f_temp, humi, batt):
    """
    Print formatted output to the console.

    Args:
        location (str): The location name.
        room (str): The room name.
        c_temp (float): Temperature in Celsius.
        f_temp (float): Temperature in Fahrenheit.
        humi (float): Humidity percentage.
        batt (float): Battery percentage.
    """
    print(f"\t{location} {room}:")
    print(f"\t  Temp: {f_temp}°F / {c_temp}°C")
    print(f"\t  Humidity: {humi}%")
    print(f"\t  Battery: {batt}%")

def fetch_device_data(device_id, api_headers):
    """
    Fetch the latest data for a specific device from the Airthings API.

    Args:
        device_id (str): The ID of the device to fetch data for.
        api_headers (dict): The headers to use for the API request.

    Returns:
        dict: The latest data for the device.

    Raises:
        RequestException: If there's an error fetching the device data.
    """
    device_url = f"https://ext-api.airthings.com/v1/devices/{device_id}/latest-samples"
    response = requests.get(url=device_url, headers=api_headers)
    response.raise_for_status()
    return response.json()['data']

def process_device_data(location, room, device_data, thresholds, ntfy_url, is_sunday, sunday_report):
    """
    Process the data for a single device, checking thresholds and generating reports.

    Args:
        location (str): The location name.
        room (str): The room name.
        device_data (dict): The data for the device.
        thresholds (dict): The threshold values for various metrics.
        ntfy_url (str): The ntfy.sh URL for sending notifications.
        is_sunday (bool): Whether it's Sunday (for weekly reports).
        sunday_report (str): The ongoing Sunday report string.

    Returns:
        str: The updated Sunday report string.
    """
    timestamp, c_temp, humi, batt = device_data['time'], device_data['temp'], device_data['humidity'], device_data['battery']
    
    if is_data_stale(timestamp, thresholds['freshness_threshold_seconds']):
        message = f"Data for {location} {room} is stale."
        send_ntfy_msg(ntfy_url, message)
    
    f_temp = (c_temp * 9/5) + 32
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
    
    return sunday_report

def main():
    """
    The main function that orchestrates the Airthings data fetching and processing.
    """
    global airthings_client_id, airthings_client_secret
    inventory_data = read_from_file('inventory.json')
    
    if not inventory_data:
        logging.error("Inventory data is not available. Please check the file.")
        return

    airthings_client_id = inventory_data["airthings_client_id"]
    airthings_client_secret = inventory_data["airthings_client_secret"]

    thresholds = {
        'freshness_threshold_seconds': 3600,
        'f_temp_threshold': inventory_data["f_temp_threshold"],
        'batt_threshold': inventory_data["battery_threshold"]
    }

    token = airthings_auth()
    if not token:
        logging.error("Failed to obtain Airthings token. Exiting.")
        return

    api_headers = {"Authorization": f"Bearer {token}"}
    now = datetime.now()
    is_sunday = now.weekday() == 6 and now.hour == 17 and now.minute == 0
    sunday_report = "Weekly Report\n"
    
    try:
        for location, rooms in inventory_data["inventory"].items():
            for room, device_info in rooms.items():
                if device_info['type'].startswith('WAVE_'):
                    device_id = device_info['id']
                    device_data = fetch_device_data(device_id, api_headers)
                    sunday_report = process_device_data(location, room, device_data, thresholds, inventory_data["ntfy_url"], is_sunday, sunday_report)
        
        if is_sunday:
            send_ntfy_msg(inventory_data["ntfy_url"], sunday_report)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching device data: {e}")

if __name__ == "__main__":
    main()
