import subprocess
import easysettings
import serial.tools.list_ports
import logging

# Setup logging for settings changes
logger = logging.getLogger('SettingsChangeLogger')
logger.setLevel(logging.INFO)
handler = logging.FileHandler('settings_log.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Load settings from configuration file
settings = easysettings.EasySettings("settings.conf")

def format_com_port(port):
    return f'COM{port}' if not port.startswith('COM') else port

def list_available_com_ports():
    com_ports = serial.tools.list_ports.comports()
    available_ports = [port.device for port in com_ports]
    print('Available COM ports:', available_ports)
    return available_ports

def update_com_ports():
    list_available_com_ports()
    old_barcode_reader = settings.get('barcode_reader')
    old_door_controller = settings.get('door_controller')
    barcode_reader = format_com_port(input('Enter COM port for the barcode reader: '))
    door_controller = format_com_port(input('Enter COM port for the door controller: '))

    if barcode_reader != old_barcode_reader:
        logger.info(f"Barcode reader COM port changed from {old_barcode_reader} to {barcode_reader}")
    if door_controller != old_door_controller:
        logger.info(f"Door controller COM port changed from {old_door_controller} to {door_controller}")

    settings.set('barcode_reader', barcode_reader)
    settings.set('door_controller', door_controller)
    settings.save()

def update_api_credentials():
    # Store old values for comparison
    old_values = {
        's_login': settings.get('s_login'),
        's_password': settings.get('s_password'),
        'AUTHORIZE_CODE': settings.get('AUTHORIZE_CODE'),
        'AUTHORIZE_ID': settings.get('AUTHORIZE_ID'),
        'k_location': settings.get('k_location')
    }

    # Update settings with potential new values
    new_values = {
        's_login': input('Wellness Living API username (leave blank to keep current): ') or old_values['s_login'],
        's_password': input('Wellness Living API password (leave blank to keep current): ') or old_values['s_password'],
        'AUTHORIZE_CODE': input('AUTHORIZE_CODE (leave blank to keep current): ') or old_values['AUTHORIZE_CODE'],
        'AUTHORIZE_ID': input('AUTHORIZE_ID (leave blank to keep current): ') or old_values['AUTHORIZE_ID'],
        'k_location': input('Location ID (leave blank to keep current): ') or old_values['k_location']
    }

    for key, value in new_values.items():
        if old_values[key] != value:
            logger.info(f"{key} changed from {old_values[key]} to {value}")
            settings.set(key, value)
    settings.save()

def set_unlock_duration():
    old_duration = settings.get('unlock_duration', 'Not set')
    new_duration = input('Enter new unlock duration in seconds (leave blank to keep current): ')
    if new_duration and new_duration != old_duration:
        logger.info(f"Unlock duration changed from {old_duration} to {new_duration}")
        settings.set('unlock_duration', new_duration)
        settings.save()
        print(f"Unlock duration updated to {new_duration} seconds.")
    else:
        print("Unlock duration remains unchanged.")

def test_api_connection():
    member_id = input("Enter a Member ID for testing: ")
    settings.set('s_member', member_id)  # Update s_member for testing
    settings.save()
    process = subprocess.Popen(['python', 'wellness_living.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    print("Output:\n", stdout.decode())
    if stderr:
        print("Errors:\n", stderr.decode())

def main_menu():
    while True:
        print("\nMenu:")
        print("1. Configure COM Ports")
        print("2. Configure API Credentials")
        print("3. Test API Connection")
        print("4. Set Unlock Duration")
        print("5. Exit")
        choice = input("Enter choice: ")
        if choice == '1':
            update_com_ports()
        elif choice == '2':
            update_api_credentials()
        elif choice == '3':
            test_api_connection()
        elif choice == '4':
            set_unlock_duration()
        elif choice == '5':
            print("Exiting setup...")
            logger.info("Exited setup.py via menu option")
            # Call dragonfly.py upon exiting
            subprocess.run(['python', 'dragonfly.py'], check=True)
            break

if __name__ == '__main__':
    main_menu()
