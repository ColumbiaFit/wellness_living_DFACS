import easysettings
import serial
import serial.tools.list_ports
from datetime import datetime
import subprocess
import time
import logging
from logging.handlers import TimedRotatingFileHandler
import atexit
import os
import json

# Setup logging with daily rotation and backup for 30 days
log_file_path = "dragonfly.log"
logger = logging.getLogger("DragonflyLogger")
logger.setLevel(logging.INFO)

# Custom formatter to include microseconds
class CustomFormatter(logging.Formatter):
    def format(self, record):
        # Add custom datetime with microseconds to the log record
        record.custom_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        return super().format(record)

formatter = CustomFormatter("%(custom_time)s - %(message)s")

# File handler for logging to file
file_handler = TimedRotatingFileHandler(log_file_path, when="midnight", interval=1, backupCount=30)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler for logging to stdout
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

database_file_path = "access_database.json"

# Function to be called upon exit
def on_exit():
    logger.info("Application is stopping.")

# Register the exit function
atexit.register(on_exit)

settings = easysettings.EasySettings("settings.conf")

def try_open_com_port(com_port):
    try:
        with serial.Serial(com_port, 9600, timeout=1) as ser:
            return True
    except Exception as e:
        logger.info(f"Failed to open COM port {com_port}: {e}")
        return False

def check_com_ports_and_api():
    logger.info("Checking COM port availability...")
    reader_port = settings.get('barcode_reader')
    relay_port = settings.get('door_controller')
    reader_available = try_open_com_port(reader_port)
    relay_available = try_open_com_port(relay_port)

    if reader_available and relay_available:
        logger.info("COM ports connected successfully...")
    else:
        if not reader_available:
            logger.info(f"Error: Barcode reader COM port {reader_port} is not available.")
        if not relay_available:
            logger.info(f"Error: Relay COM port {relay_port} is not available.")
        logger.info("Please run setup.py to configure the necessary settings.")
        subprocess.run(['python', 'setup.py'], check=True)
        return False

    logger.info("Checking API connection...")
    result = subprocess.run(['python', 'wellness_living.py', 'memberidtest'], capture_output=True, text=True)
    api_output = result.stdout.strip() if result.stdout else "No output received."
    logger.info(f"API Output: {api_output}")
    if "can_access': True" in api_output:
        logger.info("API connected successfully...")
        return True
    else:
        logger.info("Error: API authentication failed or invalid response.")
        subprocess.run(['python', 'setup.py'], check=True)
        return False


def read_local_database():
    if os.path.exists(database_file_path):
        with open(database_file_path, "r") as file:
            return json.load(file)
    else:
        return {}


def update_local_database(member_id, access_status, timestamp):
    database = read_local_database()
    database[member_id] = {"access_status": access_status, "timestamp": timestamp}
    with open(database_file_path, "w") as file:
        json.dump(database, file, indent=4)


def check_access_from_database(member_id):
    database = read_local_database()
    member_data = database.get(member_id)
    if member_data and (datetime.now() - datetime.strptime(member_data["timestamp"], "%Y-%m-%d %H:%M:%S.%f")).days < 30:
        return member_data["access_status"], member_data["timestamp"]
    return None, None


def process_barcode(barcode):
    settings.set('s_member', barcode)  # Adjust or remove this line as needed for proper member ID handling.
    logger.info(f"Received barcode: {barcode}")

    # Check local database first
    logger.info(f"Checking local Database for barcode {barcode}...")
    db_access_status, _ = check_access_from_database(barcode)

    if db_access_status:
        # Log the access decision based on the database
        logger.info(f"Barcode {barcode} - Access: {db_access_status} from database")
        if db_access_status == "Allowed":
            subprocess.run(['python', 'lock_control.py'], check=True)

    # Always call the API to ensure the database is updated with the latest access information
    logger.info(f"Updating access information for barcode {barcode} from API...")
    result = subprocess.run(['python', 'wellness_living.py', barcode], capture_output=True, text=True)
    api_output = result.stdout.strip() if result.stdout else "No API output received."

    # Determine access based on API call
    if "can_access': True" in api_output:
        api_access_status = "Allowed"
    else:
        api_access_status = "Denied"

    # Update the database with the latest access information from the API
    update_local_database(barcode, api_access_status, datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))

    # If API grants access, unlock the door (only if it wasn't already decided by the database)
    if api_access_status == "Allowed" and db_access_status != "Allowed":
        subprocess.run(['python', 'lock_control.py'], check=True)

    # Log the final decision
    if api_output == "No API output received.":
        logger.info(f"API Output: Unreachable, relied on database for access decision.")
    else:
        logger.info(f"API Output: {api_output}")
        logger.info(f"Barcode: {barcode} - Final Access Decision: {api_access_status}")




def listen_for_barcodes():
    if not check_com_ports_and_api():
        return

    barcode_reader = settings.get('barcode_reader')
    try:
        with serial.Serial(barcode_reader, 9600, timeout=1) as ser_barcode:
            logger.info(f"Listening for barcodes on {barcode_reader}...")
            while True:
                barcode = ser_barcode.readline().decode('utf-8').strip()
                if barcode:
                    process_barcode(barcode)
    except Exception as e:
        logger.info(f"Error listening to barcodes or serial port not accessible: {e}")
        time.sleep(10)

if __name__ == '__main__':
    logger.info("Application is starting.")
    try:
        listen_for_barcodes()
    except Exception as e:
        logger.exception("An unexpected error occurred, stopping application.")
