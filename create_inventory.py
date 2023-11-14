import json
import os
from pathlib import Path

inventory_file_name = "inventory.json"

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def get_house_details():
    num_houses = int(input("[?]\tHow many houses do you want to monitor? "))
    house_inventory = {}

    for house_num in range(1, num_houses + 1):
        house_name = input(f"[?]\tEnter the name of house {house_num}: ")
        num_rooms = int(input(f"[?]\tHow many rooms in {house_name}? "))
        room_inventory = {}

        for room_num in range(1, num_rooms + 1):
            room_name = input(f"[?]\tEnter the name of room {room_num} in {house_name}: ")
            monitor_serial = input(f"[?]\tEnter the serial number of the monitor in {room_name}: ")
            room_inventory[room_name] = monitor_serial

        house_inventory[house_name] = room_inventory

    return house_inventory

def get_credentials():
    client_id = input("\n[?]\tEnter the client_id: ")
    client_secret = input("[?]\tEnter the client_secret: ")
    ntfy_url = input("\n[?]\tEnter the ntfy.sh subscription name: ")
    return client_id, client_secret, ntfy_url

def save_to_file(data):
    file_path = Path(__file__).resolve().parent / inventory_file_name
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)
    print(f"\n[i]\tData has been saved to {file_path}")

def get_thresholds():
    f_temp_threshold = float(input("\n[?]\tEnter the Fahrenheit temperature threshold: "))
    battery_threshold = input("[?]\tEnter the battery level threshold % (number only): ")
    try:
        battery_threshold = int(battery_threshold)
    except:
        battery_threshold = battery_threshold[:-2]

    return f_temp_threshold, battery_threshold

def main():
    clear()
    house_data = get_house_details()
    client_id, client_secret, ntfy_url = get_credentials()
    f_temp_threshold, battery_threshold = get_thresholds()
    inventory_data = {"inventory": house_data, 
                      "airthings_client_id": client_id, 
                      "airthings_client_secret": client_secret, 
                      "ntfy_url": ntfy_url,
                      "f_temp_threshold": f_temp_threshold,
                      "battery_threshold": battery_threshold
                      }
  
    save_to_file(inventory_data)


if __name__ == "__main__":
	main()
