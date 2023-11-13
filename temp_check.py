#!/usr/bin/env python

"""
Authenticate to the Airthings API and get the latest data from a particular device.
Requires an API client created in the web gui: https://dashboard.airthings.com/integrations/api-integration
Update script with client id and device id which can be retrieved from the devices page: https://dashboard.airthings.com/devices
export the api secret to an environment variable called secret (Bash export secret="secret-key"
Requires the requests package (pip install requests into the virutal environment of container).
Python version 3.6 or above needed for f strings.
Matthew Davis July 2022

https://matthewdavis111.com/python/airthings-api-python/

"""
from pathlib import Path
import json
import logging
import requests
import os
from datetime import datetime
from requests import HTTPError

f_temp_threshold = 50.0
batt_threshold = 50

inventory = "inventory.json"

home = os.path.expanduser('~')
log_file_name = "airthings.log"
log_path = os.path.join(home, "airthings")
log_full_path = os.path.join(log_path, log_file_name)
os.makedirs(log_path, exist_ok=True)
now = datetime.now()

airthings_authorisation_url = "https://accounts-api.airthings.com/v1/token"
token_req_payload = {"grant_type": "client_credentials", "scope": "read:device:current_values",}


def log_it(room, f_temp, humi, batt):
	now = datetime.now()
	with open(log_full_path, 'a') as file:
		file.write(f"{now} - Room:{room}\tTemp:{f_temp}F\tHumidity:{humi}\tBatt:{batt}%\n")

def send_ntfy_msg(message):
	url = "https://ntfy.sh/breakfast_cabin_temp"
	message = message.encode(encoding="utf-8")
	requests.post(url, message)

def airthings_auth():
	# Request Access Token from auth server
	try:
		token_response = requests.post(airthings_authorisation_url, data=token_req_payload, allow_redirects=False, auth=(airthings_client_id, airthings_client_secret))
		token = token_response.json()["access_token"]
		return token
	except HTTPError as e:
		print(logging.error(e))


def read_from_file():
	file_path = Path(__file__).resolve().parent / inventory
	try:
		with open(file_path, "r") as file:
			data = json.load(file)
		return data
	except FileNotFoundError:
		print("File not found. Please run the main script to create the inventory file.")
		return None

def console_output(*args):
	room, c_temp, f_temp, humi, batt = args
	print(f"\t{room}:")
	print(f"\t  Temp: {f_temp}°F / {c_temp}°C")
	print(f"\t  Humidity: {humi}")
	print(f"\t  Battery: {batt}%")

def main():
	inventory_data = read_from_file()
	global airthings_client_id, airthings_client_secret

	if inventory_data:
		inventory = inventory_data["inventory"]
		airthings_client_id = inventory_data["airthings_client_id"]
		airthings_client_secret = inventory_data["airthings_client_secret"]

	token = airthings_auth()
	try:
		api_headers = {"Authorization": f"Bearer {token}"}
		for location in inventory.keys():
			# print(f"{location}:")
			for room in inventory.get(location):
				device_id = inventory.get(location).get(room)
				device_url = f"https://ext-api.airthings.com/v1/devices/{device_id}/latest-samples"
		
				response = requests.get(url=device_url, headers=api_headers)
				# print(response.json()) # use this to see what data is available.

				c_temp = response.json()['data']['temp']
				f_temp = (c_temp * 9/5) + 32
				humi = response.json()['data']['humidity']
				batt = response.json()['data']['battery']

				# console_output(room, c_temp, f_temp, humi, batt)

				log_it(room, f_temp, humi, batt)

				if f_temp <= f_temp_threshold:
					message = f"\n\nBrrr it's cold!\n{location} {room} is {f_temp}°F."
					send_ntfy_msg(message)
				
				if batt < batt_threshold:
					message = f"\n\nBattery Warning!\n{location} {room} is at {batt}%."
					send_ntfy_msg(message)
	
	except HTTPError as e:
		logging.error(e)



if __name__ == "__main__":
	main()

