# config.py
import os
import platform

# File paths
AMBULANCE_FILE = 'ambulance.csv'
NETWORK_FILE = 'location_network.csv'
PRIORITY_FILE = 'call_priority.csv'
CALLS_FILE = 'calls.csv'

# Determine log file path based on OS
if platform.system() == 'Linux' and os.path.exists('/var/log'):
    LOG_FILE = '/var/log/ambulance_call_log.csv'
else:
    # For Windows, Mac, or Linux without /var/log access
    LOG_FILE = 'ambulance_call_log.csv'
    print(f"Note: Using local log file: {LOG_FILE}")