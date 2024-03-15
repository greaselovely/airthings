# Airthings Environmental Monitor

## Overview
This project offers a toolset to monitor environmental conditions across multiple properties using Airthings devices. It enables users to set thresholds for environmental parameters and receive notifications when these thresholds are breached.

## Prerequisites
Before you start, ensure you have the following:
- An Airthings account with at least one device set up.
- Python 3.6 or higher installed on your system.
- Access to a terminal or command prompt.
- The `requests` package installed in your Python environment (`pip install requests`).

## Getting Started

### 1. Gather API Credentials
Obtain your API credentials from the Airthings dashboard:
- Navigate to [Airthings API Integration](https://dashboard.airthings.com/integrations/api-integration) to create an API client.
- Note down the `client_id` and `client_secret`.

### 2. Collect Device Serial Numbers
List the serial numbers of all Airthings devices you wish to monitor. You can find these numbers on the [Devices](https://dashboard.airthings.com/devices) page of your Airthings dashboard.

### 3. Set Up Notification Channel
Establish a notification channel:
- Go to [ntfy.sh](https://ntfy.sh) and create a subscription topic.
- Note down the topic name for later use.

### 4. Create Inventory File
Run the `create_inventory.py` script to generate your `inventory.json` file. This script will guide you through entering:
- The names and number of properties.
- Room names within each property.
- Serial numbers of the Airthings devices in each room.
- Your Airthings API credentials.
- The ntfy.sh subscription topic name.
- Threshold values for temperature and battery level alerts.

### 5. Schedule Monitoring Script
Set up a cron job or a scheduled task to run `main.py` regularly. For example, to run the script hourly, you can add the following to your crontab (on Linux or macOS):
```bash
0 * * * * /path/to/python /path/to/main.py
```
Replace `/path/to/python` and `/path/to/main.py` with the actual paths on your system.

## What This Does
- Monitors environmental data from Airthings devices across multiple locations.
- Sends notifications if measured values fall below specified thresholds.

## What This Doesn't Do
- It does not graph or visualize data over time, as the Airthings dashboard already provides comprehensive graphing and analysis tools.

## Contributing
Contributions to improve the script or documentation are welcome. Please feel free to submit pull requests or open issues with your suggestions or feedback.
