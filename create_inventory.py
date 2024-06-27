# create_inventory.py
import json
import os
from pathlib import Path
import requests

inventory_file_name = "inventory.json"

def clear():
    """
    Clears the console screen.

    This function uses the appropriate system command to clear the console
    screen based on the operating system.
    """
    os.system("cls" if os.name == "nt" else "clear")

def safe_input(prompt, type_=str, default=None):
    """
    Safely inputs data of a specified type from the user.

    This function prompts the user for input and attempts to convert it to
    the specified type. It re-prompts on type error until valid input is received.

    Args:
        prompt (str): The prompt to display to the user.
        type_ (type): The expected type of the input (default is str).
        default: The default value to return if conversion fails (default is None).

    Returns:
        The user input converted to the specified type, or the default value if provided.
    """
    while True:
        try:
            return type_(input(prompt))
        except ValueError:
            print(f"[!]\tInvalid input. Expected a {type_.__name__}.")
        if default is not None:
            return default

def get_airthings_devices(client_id, client_secret):
    """
    Fetches device information from the Airthings API.

    This function authenticates with the Airthings API using the provided
    credentials and retrieves information about all devices associated
    with the account.

    Args:
        client_id (str): The Airthings API client ID.
        client_secret (str): The Airthings API client secret.

    Returns:
        list: A list of dictionaries containing device information, or None if the request fails.
    """
    token_url = "https://accounts-api.airthings.com/v1/token"
    api_url = "https://ext-api.airthings.com/v1/devices"

    # Get access token
    token_data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "read:device:current_values"
    }
    token_response = requests.post(token_url, data=token_data)
    if token_response.status_code != 200:
        print("[!]\tFailed to obtain access token")
        return None

    access_token = token_response.json()["access_token"]

    # Get devices
    headers = {"Authorization": f"Bearer {access_token}"}
    devices_response = requests.get(api_url, headers=headers)
    if devices_response.status_code != 200:
        print("[!]\tFailed to fetch devices")
        return None

    return devices_response.json().get("devices", [])

def process_airthings_data(devices):
    """
    Processes Airthings device data and organizes it by location and room.

    This function takes the raw device data from the Airthings API and
    organizes it into a nested dictionary structure based on location and room.

    Args:
        devices (list): A list of dictionaries containing device information.

    Returns:
        dict: A nested dictionary organized by location and room, containing device information.
    """
    organized_data = {}

    for device in devices:
        if device['deviceType'].startswith('WAVE_'):
            location_name = device['location']['name']
            room_name = device['segment']['name']
            device_id = device['id']
            device_type = device['deviceType']

            if location_name not in organized_data:
                organized_data[location_name] = {}

            organized_data[location_name][room_name] = {
                'id': device_id,
                'type': device_type
            }

    return organized_data

# def get_house_details(devices):
#     """
#     Collects details about houses and rooms to monitor.

#     This function prompts the user to input information about houses and rooms,
#     and associates them with available Airthings devices.

#     Args:
#         devices (list): A list of dictionaries containing device information.

#     Returns:
#         dict: A nested dictionary containing house and room information with associated device IDs.
#     """
#     house_inventory = {}

#     print("[i]\tAvailable devices:")
#     for i, device in enumerate(devices, 1):
#         print(f"{i}. {device['deviceType']} - Serial: {device['id']}")

#     while True:
#         house_name = input("\n[?]\tEnter a house name (or press Enter to finish): ")
#         if not house_name:
#             break

#         room_inventory = {}
#         while True:
#             room_name = input(f"[?]\tEnter a room name in {house_name} (or press Enter to finish): ")
#             if not room_name:
#                 break

#             device_index = safe_input("[?]\tEnter the number of the device for this room: ", int) - 1
#             if 0 <= device_index < len(devices):
#                 room_inventory[room_name] = devices[device_index]['id']
#             else:
#                 print("[!]\tInvalid device number. Please try again.")

#         house_inventory[house_name] = room_inventory

#     return house_inventory

def get_credentials():
    """
    Collects Airthings API credentials and ntfy.sh subscription name.

    This function prompts the user to input the Airthings API client ID,
    client secret, and the ntfy.sh subscription name.

    Returns:
        tuple: A tuple containing the client ID, client secret, and ntfy.sh subscription name.
    """
    client_id = input("\n[?]\tEnter the client_id: ")
    client_secret = input("[?]\tEnter the client_secret: ")
    ntfy_url = input("\n[?]\tEnter the ntfy.sh subscription name: ")
    return client_id, client_secret, ntfy_url

def save_to_file(data):
    """
    Saves collected data to a JSON file.

    This function takes the collected inventory data and saves it to a JSON file
    in the same directory as the script.

    Args:
        data (dict): The inventory data to be saved.
    """
    file_path = Path(__file__).resolve().parent / inventory_file_name
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)
    print(f"\n[i]\tData has been saved to {file_path}")

def get_thresholds():
    """
    Collects environmental thresholds.

    This function prompts the user to input temperature and battery level thresholds.

    Returns:
        tuple: A tuple containing the temperature threshold (float) and battery threshold (int).
    """
    f_temp_threshold = safe_input("\n[?]\tEnter the Fahrenheit temperature threshold: ", float)
    battery_threshold = safe_input("[?]\tEnter the battery level threshold % (number only): ", int)
    return f_temp_threshold, battery_threshold

def main():
    """
    Main function to orchestrate data collection and storage.

    This function coordinates the process of collecting Airthings device information,
    organizing it, and saving it to a file. It also handles user interaction for
    confirming the use of the collected data.
    """
    clear()
    client_id, client_secret, ntfy_url = get_credentials()
    devices = get_airthings_devices(client_id, client_secret)
    
    if devices:
        organized_data = process_airthings_data(devices)
        print("\n[i]\tOrganized Airthings data:")
        for location, rooms in organized_data.items():
            print(f"\nLocation: {location}")
            for room, device in rooms.items():
                print(f"  Room: {room}")
                print(f"    Device ID: {device['id']}")
                print(f"    Device Type: {device['type']}")

        # Ask user if they want to use this data for the inventory
        use_data = input("\n[?]\tDo you want to use this data for your inventory? (y/n): ").lower() == 'y'

        if use_data:
            f_temp_threshold, battery_threshold = get_thresholds()
            inventory_data = {
                "inventory": organized_data, 
                "airthings_client_id": client_id, 
                "airthings_client_secret": client_secret, 
                "ntfy_url": ntfy_url,
                "f_temp_threshold": f_temp_threshold,
                "battery_threshold": battery_threshold
            }
            save_to_file(inventory_data)
        else:
            print("[i]\tUser chose not to use the Airthings data. Please manually input the inventory.")
            # Here you can call your original get_house_details() function if needed
    else:
        print("[!]\tFailed to fetch devices from Airthings API. Please check your credentials.")

if __name__ == "__main__":
    main()
