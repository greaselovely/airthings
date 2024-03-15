import json
import os
from pathlib import Path

inventory_file_name = "inventory.json"

def clear():
    """Clears the console screen."""
    os.system("cls" if os.name == "nt" else "clear")

def safe_input(prompt, type_=str, default=None):
    """
    Safely inputs data of a specified type from the user.
    Re-prompts on type error until valid input is received.
    """
    while True:
        try:
            return type_(input(prompt))
        except ValueError:
            print(f"[!]\tInvalid input. Expected a {type_.__name__}.")
        if default is not None:
            return default

def get_house_details():
    """Collects details about houses and rooms to monitor."""
    num_houses = safe_input("[?]\tHow many houses do you want to monitor? ", int)
    house_inventory = {}

    for house_num in range(1, num_houses + 1):
        house_name = input(f"[?]\tEnter the name of house {house_num}: ")
        num_rooms = safe_input(f"[?]\tHow many rooms in {house_name}? ", int)
        room_inventory = {}

        for room_num in range(1, num_rooms + 1):
            room_name = input(f"[?]\tEnter the name of room {room_num} in {house_name}: ")
            monitor_serial = input(f"[?]\tEnter the serial number of the monitor in {room_name}: ")
            room_inventory[room_name] = monitor_serial

        house_inventory[house_name] = room_inventory

    return house_inventory

def get_credentials():
    """Collects Airthings API credentials and ntfy.sh subscription name."""
    client_id = input("\n[?]\tEnter the client_id: ")
    client_secret = input("[?]\tEnter the client_secret: ")
    ntfy_url = input("\n[?]\tEnter the ntfy.sh subscription name: ")
    return client_id, client_secret, ntfy_url

def save_to_file(data):
    """Saves collected data to a JSON file."""
    file_path = Path(__file__).resolve().parent / inventory_file_name
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)
    print(f"\n[i]\tData has been saved to {file_path}")

def get_thresholds():
    """Collects environmental thresholds."""
    f_temp_threshold = safe_input("\n[?]\tEnter the Fahrenheit temperature threshold: ", float)
    battery_threshold = safe_input("[?]\tEnter the battery level threshold % (number only): ", int)

    return f_temp_threshold, battery_threshold

def main():
    """Main function to orchestrate data collection and storage."""
    clear()
    house_data = get_house_details()
    client_id, client_secret, ntfy_url = get_credentials()
    f_temp_threshold, battery_threshold = get_thresholds()
    inventory_data = {
        "inventory": house_data, 
        "airthings_client_id": client_id, 
        "airthings_client_secret": client_secret, 
        "ntfy_url": ntfy_url,
        "f_temp_threshold": f_temp_threshold,
        "battery_threshold": battery_threshold
    }
    save_to_file(inventory_data)

if __name__ == "__main__":
    main()
