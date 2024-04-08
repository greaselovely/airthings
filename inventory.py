import json
import os
from pathlib import Path

inventory_file_name = "inventory.json"

def clear():
    """
    Clears the console screen based on the operating system.
    Uses 'cls' command for Windows ('nt') and 'clear' for others (e.g., Unix/Linux).
    """
    os.system("cls" if os.name == "nt" else "clear")

def safe_input(prompt, type_=str, default=None):
    """
    Prompts the user for input, converting it to a specified type. If the input is invalid, re-prompts until valid input is received.
    
    Parameters:
    - prompt: The message displayed to the user.
    - type_: The type to which the input should be converted. Defaults to str.
    - default: The default value to return if the input is invalid. Defaults to None.
    
    Returns:
    The user input converted to the specified type, or the default value if provided and conversion fails.
    """
    while True:
        try:
            return type_(input(prompt))
        except ValueError:
            print(f"[!]\tInvalid input. Expected a {type_.__name__}.")
        if default is not None:
            return default

def get_house_details(existing_houses=None):
    """
    Collects details about houses and rooms, allowing for additions to an existing inventory.
    If existing houses are provided, offers options to add more houses or rooms to existing houses.
    
    Parameters:
    - existing_houses: A dictionary representing the current inventory of houses and their rooms, if any.
    
    Returns:
    A dictionary with the updated or newly collected house and room details.
    """
    house_inventory = existing_houses if existing_houses else {}

    if existing_houses:
        add_more_houses = input("\n[?]\tDo you want to add more houses? (y/n): ").strip().lower() == 'y'
        if add_more_houses:
            num_houses = safe_input("[?]\tHow many houses do you want to add? ", int)
            for _ in range(num_houses):
                house_name = input("[?]\tEnter the name of the new house: ").strip()
                num_rooms = safe_input(f"[?]\tHow many rooms in {house_name}? ", int)
                room_inventory = {}
                for _ in range(num_rooms):
                    room_name = input(f"[?]\tEnter the name of the room in {house_name}: ").strip()
                    monitor_serial = input(f"[?]\tEnter the serial number of the monitor in {room_name}: ").strip()
                    room_inventory[room_name] = monitor_serial
                house_inventory[house_name] = room_inventory
        elif 'y' == input("\n[?]\tDo you want to add rooms to an existing house? (y/n): ").strip().lower():
            print("\n[i]\tExisting houses:")
            house_names = list(existing_houses.keys())
            for index, house_name in enumerate(house_names, start=1):
                print(f"\t{index}. {house_name}")
            house_choice = safe_input("\n[?]\tSelect the number of the house you want to add rooms to: ", int) - 1

            if 0 <= house_choice < len(house_names):
                selected_house = house_names[house_choice]
                num_rooms = safe_input(f"[?]\tHow many rooms do you want to add in {selected_house}? ", int)
                room_inventory = existing_houses.get(selected_house, {})

                for _ in range(num_rooms):
                    room_name = input(f"[?]\tEnter the name of the room in {selected_house}: ").strip()
                    monitor_serial = input(f"[?]\tEnter the serial number of the monitor in {room_name}: ").strip()
                    room_inventory[room_name] = monitor_serial

                house_inventory[selected_house] = room_inventory
            else:
                print("\n[!]\tInvalid selection.")
    else:
        num_houses = safe_input("[?]\tHow many houses do you want to monitor? ", int)
        for _ in range(num_houses):
            house_name = input("[?]\tEnter the name of the house: ").strip()
            num_rooms = safe_input(f"[?]\tHow many rooms in {house_name}? ", int)
            room_inventory = {}
            for _ in range(num_rooms):
                room_name = input(f"[?]\tEnter the name of the room in {house_name}: ").strip()
                monitor_serial = input(f"[?]\tEnter the serial number of the monitor in {room_name}: ").strip()
                room_inventory[room_name] = monitor_serial
            house_inventory[house_name] = room_inventory

    return house_inventory

def get_credentials():
    """
    Prompts the user for Airthings API credentials (client_id, client_secret) and the ntfy.sh subscription name.
    
    Returns:
    A tuple containing the client_id, client_secret, and ntfy.sh subscription name.
    """
    client_id = input("\n[?]\tEnter the client_id: ")
    client_secret = input("[?]\tEnter the client_secret: ")
    ntfy_url = input("\n[?]\tEnter the ntfy.sh subscription name: ")
    return client_id, client_secret, ntfy_url

def save_to_file(data):
    """
    Saves the provided data to a JSON file named 'inventory.json' in the script's directory.
    
    Parameters:
    - data: The data to be saved, typically including house details, credentials, and thresholds.
    """
    file_path = Path(__file__).resolve().parent / inventory_file_name
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)
    print(f"\n[i]\tData has been saved to {file_path}")

def get_thresholds():
    """
    Collects environmental thresholds from the user, specifically for temperature and battery level.
    
    Returns:
    A tuple containing the temperature threshold (as a float) and the battery level threshold (as an integer).
    """
    f_temp_threshold = safe_input("\n[?]\tEnter the Fahrenheit temperature threshold: ", float)
    battery_threshold = safe_input("[?]\tEnter the battery level threshold % (number only): ", int)

    return f_temp_threshold, battery_threshold

def main():
    """
    Main function to orchestrate the overall data collection and storage process.
    Loads existing inventory (if any), collects house details, credentials, and environmental thresholds,
    and saves the collected data to 'inventory.json'.
    """
    clear()
    file_path = Path(__file__).resolve().parent / inventory_file_name

    existing_data = {}

    if file_path.exists():
        with open(file_path, "r") as file:
            existing_data = json.load(file)
    
    house_data = get_house_details(existing_data.get("inventory") if existing_data else None)

    client_id = existing_data.get("airthings_client_id", "")
    client_secret = existing_data.get("airthings_client_secret", "")
    ntfy_url = existing_data.get("ntfy_url", "")
    if not all([client_id, client_secret, ntfy_url]):  # Prompt if any credential is missing
        client_id, client_secret, ntfy_url = get_credentials()

    f_temp_threshold = existing_data.get("f_temp_threshold", None)
    battery_threshold = existing_data.get("battery_threshold", None)
    if f_temp_threshold is None or battery_threshold is None:  # Prompt if any threshold is missing
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
