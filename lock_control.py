import serial
import time
from datetime import datetime
from easysettings import EasySettings

# Load settings from the configuration file
settings = EasySettings("settings.conf")


def main():
    try:
        door_controller = settings.get('door_controller')
        unlock_duration = int(settings.get('unlock_duration', 5))

        print(f'{datetime.now()} - Opening door controller on {door_controller}...')
        with serial.Serial(door_controller, 9600) as ser:
            print(f'{datetime.now()} - COM port opened')
            time.sleep(1)  # Wait for 1 second to ensure the COM port is open

            print(f'{datetime.now()} - Unlocking door...')
            ser.write(b'a')  # ASCII command to unlock the door
            time.sleep(unlock_duration)  # Wait for the duration to expire
            print(f'{datetime.now()} - Locking door...')
            ser.write(b'z')  # ASCII command to lock the door
            # The serial port is automatically closed when exiting the 'with' block
            print(f'{datetime.now()} - COM port closed')
    except Exception as e:
        print(f'{datetime.now()} - Error controlling the door: {e}')


if __name__ == '__main__':
    main()
