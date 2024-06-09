import os
import json
import logging
import requests
from pathlib import Path
from inventory import clear
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
token_req_payload = {"grant_type": "client_credentials", "scope": "read:device:current_values",}

# Logging configuration
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler = RotatingFileHandler(log_full_path, maxBytes=524288, backupCount=5)
log_handler.setFormatter(log_formatter)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)

def send_ntfy_msg(ntfy_topic: str, message: str):
    """
    Sends a message to a specified ntfy.sh topic.
    
    Parameters:
    - ntfy_topic (str): The topic name on ntfy.sh to which the message will be sent.
    - message (str): The message content to send.
    
    This function constructs the full URL for the ntfy.sh topic and sends the message
    as a POST request. The message is encoded in UTF-8, and appropriate content-type
    headers are included in the request.
    """
    url = f"https://ntfy.sh/{ntfy_topic}"
    headers = {'Content-Type': 'text/plain; charset=utf-8'}
    
    try:
        response = requests.post(url, data=message.encode('utf-8'), headers=headers)
        response.raise_for_status()  # Raises stored HTTPError, if one occurred.
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send message to {ntfy_topic}: {e}")

def airthings_auth():
    """
    Request an access token from the Airthings authorization server.

    This function attempts to obtain an access token using the Airthings client ID and secret.
    It posts a request to the Airthings authorization URL with the necessary payload.

    Returns:
        str: The access token as a string if the request is successful.
        None: If the request fails due to any exception, None is returned.

    Raises:
        Logs an error message if the request fails for any reason.
    """
    try:
        token_response = requests.post(airthings_authorisation_url, data=token_req_payload, allow_redirects=False, auth=(airthings_client_id, airthings_client_secret))
        token_response.raise_for_status()  # This will raise an exception for HTTP errors.
        token = token_response.json().get("access_token")
        return token
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to obtain Airthings access token: {e}")
        return None

def read_inventory(file_name):
    """
    Reads and returns the contents of a JSON file located in the same directory as this script.

    This function attempts to open and read the specified JSON file, parsing its contents into a dictionary.
    
    Args:
        file_name (str): The name of the file to read. The file should be located in the same directory as this script.
    
    Returns:
        dict: The contents of the JSON file parsed into a dictionary.
        
    Raises:
        FileNotFoundError: If the specified file does not exist.
        json.JSONDecodeError: If the file content is not valid JSON.
    """
    file_path = Path(__file__).resolve().parent / file_name
    with open(file_path, "r") as file:
        return json.load(file)

def convert_timestamp_to_time(timestamp):
    """
    Convert a UNIX timestamp to a formatted string representation.
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

def is_data_stale(timestamp: int, freshness_threshold_seconds: int = 3600) -> bool:
    """
    Check if the data, based on the given timestamp, is considered stale.
    A data point is stale if its age is greater than or equal to the freshness threshold.
    The timestamp is assumed to be in UNIX format (seconds since the epoch).
    
    :param timestamp: The timestamp of the data.
    :param freshness_threshold_seconds: The threshold in seconds to consider data stale (default is 3600 seconds or 1 hour).
    :return: True if the data is stale, False otherwise.
    """
    current_time = datetime.now(timezone.utc).timestamp() # Current time in UTC as a timestamp
    data_age_seconds = current_time - timestamp # Calculate the age of the data in seconds
    
    # Optionally, convert and print the timestamp for debugging or logging
    # print(f"Data timestamp: {convert_timestamp_to_time(timestamp)}")
    
    # Determine if the data is stale
    return data_age_seconds >= freshness_threshold_seconds

def console_output(location, room, c_temp, f_temp, humi, batt):
    """
    Prints out environmental data for a given location and room.

    This function formats and displays temperature (in both Fahrenheit and Celsius),
    humidity, and battery level for a specific location and room.

    Args:
        location (str): The name of the location.
        room (str): The name of the room within the location.
        c_temp (float or int): The temperature in degrees Celsius.
        f_temp (float or int): The temperature in degrees Fahrenheit.
        humi (float or int): The humidity percentage.
        batt (float or int): The battery level percentage.

    """
    print(f"\t{location} {room}:")
    print(f"\t  Temp: {f_temp}°F / {c_temp}°C")
    print(f"\t  Humidity: {humi}%")
    print(f"\t  Battery: {batt}%")

def fetch_device_data(device_id, api_headers):
    """
    Fetches the latest samples for a device from the Airthings API.
    
    Args:
        device_id (str): The unique identifier for the Airthings device.
        api_headers (dict): Authorization headers for the API request.
    
    Returns:
        dict: The latest data samples from the device.
    """
    device_url = f"https://ext-api.airthings.com/v1/devices/{device_id}/latest-samples"
    response = requests.get(url=device_url, headers=api_headers)
    response.raise_for_status()  # This will raise an exception for HTTP errors.
    return response.json()['data']

def process_device_data(location, room, device_data, thresholds, ntfy_url, is_sunday):
    """
    Processes and logs data for a single device, sending notifications if necessary.

    Args:
        location (str): The location of the device.
        room (str): The room where the device is located.
        device_data (dict): The latest data samples from the device.
        thresholds (dict): Thresholds for temperature and battery.
        ntfy_url (str): The URL for sending notifications.
        is_sunday (bool): Whether it's time for the weekly report.
        sunday_report (str): The weekly report string, accumulating information.
    
    Returns:
        str: Updated sunday_report.
    """
    global sunday_report
    timestamp, c_temp, humi, batt = device_data['time'], device_data['temp'], device_data['humidity'], device_data['battery']
    
    stale_message = ""
    if is_data_stale(timestamp, thresholds['freshness_threshold_seconds']):
        stale_message = f"{location} {room} is not reporting."
    
    f_temp = (c_temp * 9 / 5) + 32
    f_temp = float(f"{f_temp:0.2f}")  # Keep float to two decimals
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
    """
    Main function to orchestrate the flow of reading inventory data,
    fetching and processing Airthings device data, handling temperature
    conversions, checking data freshness, and sending notifications as necessary.
    """
    global airthings_client_id, airthings_client_secret, sunday_report
    inventory_data = read_inventory('inventory.json')  # Ensure this function accepts a filename argument
    
    if not inventory_data:
        logging.error("Inventory data is not available. Please check the file.")
        return
    send_ntfy_msg("Script Started...")
    
    airthings_client_id, airthings_client_secret = inventory_data["airthings_client_id"], inventory_data["airthings_client_secret"]

    thresholds = {
        'freshness_threshold_seconds': 3600,  # Freshness threshold in seconds
        'f_temp_threshold': inventory_data["f_temp_threshold"],
        'batt_threshold': inventory_data["battery_threshold"]
    }

    token = airthings_auth()  # Ensure this is defined to handle token fetching
    api_headers = {"Authorization": f"Bearer {token}"}
    now = datetime.now()
    is_sunday = now.weekday() == 6 and now.hour == 17 and now.minute == 0  # Check for Sunday at 17:00
    
    stale_data_messages = []  # Initialize an empty list to hold stale data messages
    sunday_report = "Weekly Report\n"  # Initialize sunday_report outside of the loop

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