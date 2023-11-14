# airthings

## What this does do
Created to monitor environmental status for various physical properties (houses) and to notify on items below threshold.

First step; go gather your API credentials from https://dashboard.airthings.com
Second step; go get the serial numbers for each monitoring device you want to query against
Third step; go establish or get the name for a subscription topic at https://ntfy.sh

Run `create_inventory.py`

This will walk you thru creating the `inventory.json`.


This file is used by `airthings.py` for credentials, inventory and other configuration items.

Then finally, cron `airthings.py`.  I run mine every hour.

## What this doesn't do

Graph over time utilization.  Airthings already does that.