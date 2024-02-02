import serial
import time
from datetime import datetime
from easysettings import EasySettings
import logging
from logging.handlers import TimedRotatingFileHandler

# Setup logging similar to dragonfly.py
log_file_path = "dragonfly.log"
logger = logging.getLogger("LockControlLogger")
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

settings = EasySettings("settings.conf")

def listen_for_hardware_confirmation(ser):
    timeout_start = time.time()
    timeout_seconds = 5  # Adjust as necessary
    while time.time() < timeout_start + timeout_seconds:
        if ser.in_waiting > 0:
            response = ser.readline().decode().strip()
            logger.info(f'Hardware reports: {response}')
            return

def main():
    try:
        door_controller = settings.get('door_controller')
        unlock_duration = int(settings.get('unlock_duration', 5))

        logger.info(f'Opening door controller on {door_controller}...')
        with serial.Serial(door_controller, 9600, timeout=2) as ser:
            logger.info('COM port opened')
            time.sleep(1)  # Wait to ensure the COM port is open

            logger.info('Unlocking door...')
            ser.write(b'a')
            listen_for_hardware_confirmation(ser)
            time.sleep(unlock_duration)  # Wait for the duration to expire

            logger.info('Locking door...')
            ser.write(b'z')
            listen_for_hardware_confirmation(ser)
            logger.info('COM port closed')
    except Exception as e:
        logger.error(f'Error controlling the door: {e}', exc_info=True)

if __name__ == '__main__':
    main()
