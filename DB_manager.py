import json
import os
import sys
import subprocess
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

# Setup logging similar to dragonfly.py but for DB_manager
log_file_path = "database_log.log"
logger = logging.getLogger("DBManagerLogger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S.%f')
file_handler = TimedRotatingFileHandler(log_file_path, when="midnight", interval=1, backupCount=30)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

database_file_path = "access_database.json"
queue_file_path = "queue.json"

def read_queue():
    if os.path.exists(queue_file_path):
        with open(queue_file_path, "r") as file:
            return json.load(file)
    else:
        return []

def save_queue(queue):
    with open(queue_file_path, "w") as file:
        json.dump(queue, file, indent=4)

def read_database():
    if os.path.exists(database_file_path):
        with open(database_file_path, "r") as file:
            return json.load(file)
    else:
        return {}

def update_database(member_id, access_status):
    database = read_database()
    database[member_id] = {"access_status": access_status, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")}
    with open(database_file_path, "w") as file:
        json.dump(database, file, indent=4)
    logger.info(f"Database updated with {member_id}: {access_status}")

def process_queue():
    queue = read_queue()
    if not queue:
        logger.info("Queue is empty, no action required.")
        return

    for member_id in queue[:]:  # Copy the queue list for safe iteration
        logger.info(f"Processing queue item for member ID: {member_id}")
        try:
            # Call wellness_living.py script with member_id as command-line argument
            result = subprocess.run(['python', 'wellness_living.py', member_id], capture_output=True, text=True, check=True)
            if result.stdout:
                access_status = "Allowed" if "can_access': True" in result.stdout else "Denied"
                update_database(member_id, access_status)
                queue.remove(member_id)  # Remove from queue after successful update
                logger.info(f"Member ID {member_id} synced with API and database updated.")
            else:
                logger.error(f"Failed to sync member ID {member_id} with API. No output received.")
        except subprocess.CalledProcessError as e:
            logger.error(f"API call for member ID {member_id} failed with error: {e}")

    save_queue(queue)  # Save any remaining items back to the queue

if __name__ == "__main__":
    logger.info("DB_manager starting.")
    process_queue()
    logger.info("DB_manager finished.")
