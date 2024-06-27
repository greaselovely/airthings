# Airthings

## Overview
This project offers a comprehensive toolset to monitor environmental conditions across multiple properties using Airthings devices. It enables users to set thresholds for environmental parameters and receive notifications when these thresholds are breached. The system now integrates directly with the Airthings API to automatically fetch and organize device data.

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

### 2. Set Up Notification Channel
Establish a notification channel:
- Go to [ntfy.sh](https://ntfy.sh) and create a subscription topic.
- Note down the topic name for later use.

### 3. Create Inventory File
Run the `create_inventory.py` script to generate your `inventory.json` file. This script will:
- Fetch device information directly from the Airthings API using your credentials.
- Display the fetched device information for your review.
- Allow you to confirm if you want to use the fetched data for your inventory.
- If confirmed, it will prompt you to enter threshold values for temperature and battery level alerts.
- Save all this information to the `inventory.json` file.

To run the script:
```
python create_inventory.py
```

### 4. Schedule Monitoring Script
Set up a cron job or a scheduled task to run main.py regularly. For example, to run the script hourly, you can add the following to your crontab (on Linux or macOS):
```
0 * * * * /path/to/python /path/to/main.py
```

Replace /path/to/python and /path/to/main.py with the actual paths on your system.
What This Does

Automatically fetches and organizes device data from the Airthings API.
Monitors environmental data from Airthings devices across multiple locations.
Sends notifications if measured values fall below specified thresholds.
Generates a weekly report (sent on Sundays at 17:00) with a summary of all monitored devices.
Logs all activities and any errors for troubleshooting.

### Features

Automatic device discovery and organization using the Airthings API.
Real-time monitoring of temperature, humidity, and battery levels.
Customizable thresholds for temperature and battery level alerts.
Stale data detection and notification.
Weekly summary reports.
Detailed logging for troubleshooting and auditing.

### What This Doesn't Do

It does not graph or visualize data over time, as the Airthings dashboard already provides comprehensive graphing and analysis tools.

### Troubleshooting

Check the airthings.log file in the ~/airthings/ directory for detailed logs of the script's operation and any errors encountered.
Ensure your API credentials are correct and have the necessary permissions.
Verify that your ntfy.sh topic is correctly set up and accessible.

### Contributing
Contributions to improve the script or documentation are welcome. Please feel free to submit pull requests or open issues with your suggestions or feedback.
