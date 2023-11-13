import json
from pathlib import Path

def get_house_details():
    num_houses = int(input("How many houses do you want to monitor? "))
    house_inventory = {}

    for house_num in range(1, num_houses + 1):
        house_name = input(f"Enter the name of house {house_num}: ")
        num_rooms = int(input(f"How many rooms in {house_name}? "))
        room_inventory = {}

        for room_num in range(1, num_rooms + 1):
            room_name = input(f"Enter the name of room {room_num} in {house_name}: ")
            monitor_serial = input(f"Enter the serial number of the monitor in {room_name}: ")
            room_inventory[room_name] = monitor_serial

        house_inventory[house_name] = room_inventory

    return house_inventory

def get_credentials():
    client_id = input("Enter the client_id: ")
    client_secret = input("Enter the client_secret: ")
    return client_id, client_secret

def save_to_file(data):
    file_path = Path(__file__).resolve().parent / "inventory.json"
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)
    print(f"Data has been saved to {file_path}")

def read_from_file():
    file_path = Path(__file__).resolve().parent / "inventory.json"
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print("File not found. Please run the main script to create the inventory file.")
        return None

if __name__ == "__main__":
    house_data = get_house_details()
    client_id, client_secret = get_credentials()

    inventory_data = {"inventory": house_data, "airthings_client_id": client_id, "airthings_client_secret": client_secret}
    
    save_to_file(inventory_data)
