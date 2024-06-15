import requests
import certifi

# Use certifi's CA bundle
CERT_PATH = certifi.where()

url = 'https://accounts-api.airthings.com/v1/token'
data = {"grant_type": "client_credentials", "scope": "read:device:current_values"}

try:
    response = requests.post(url, data=data, verify=CERT_PATH)
    response.raise_for_status()
    print("Connection successful:", response.json())
except requests.exceptions.RequestException as e:
    print(f"SSL error: {e}")
