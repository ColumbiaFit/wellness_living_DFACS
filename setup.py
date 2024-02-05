import subprocess
import easysettings
import serial.tools.list_ports
import logging

# Setup logging to track changes made during the setup process.
logger = logging.getLogger('SettingsChangeLogger')
logger.setLevel(logging.INFO)  # Set the logging level to INFO to capture all relevant messages.
handler = logging.FileHandler('settings_log.log')  # Save log messages to 'settings_log.log'.
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)  # Format log messages with time, log level, and the log message.
logger.addHandler(handler)  # Add the file handler to the logger.

# Load or initialize settings from 'settings.conf', a configuration file.
settings = easysettings.EasySettings("settings.conf")

# Helper function to format COM port input. Ensures consistency in COM port naming.
def format_com_port(port):
    # Add 'COM' prefix if not already present to match expected format.
    return f'COM{port}' if not port.startswith('COM') else port

# Lists all available COM ports on the system. Useful for identifying connected devices.
def list_available_com_ports():
    com_ports = serial.tools.list_ports.comports()  # Fetch list of all COM ports.
    available_ports = [port.device for port in com_ports]  # Extract device names from the COM port information.
    print('Available COM ports:', available_ports)  # Display the list of available COM ports.
    return available_ports  # Return the list of device names for further use.

# Updates the COM port settings based on user input. Used for configuring device connections.
def update_com_ports():
    list_available_com_ports()  # Show available COM ports to help the user choose.
    barcode_reader = format_com_port(input('Enter COM port for the barcode reader: '))
    door_controller = format_com_port(input('Enter COM port for the door controller: '))
    # Save the selected COM ports for the barcode reader and door controller in the configuration.
    settings.set('barcode_reader', barcode_reader)
    settings.set('door_controller', door_controller)
    settings.save()  # Persist the updated settings to the configuration file.

# Updates the API credentials based on user input. This is crucial for API interaction.
def update_api_credentials():
    # Prompt user for API credentials, using existing values as defaults if no input is given.
    s_login = input('Wellness Living API username (leave blank to keep current): ') or settings.get('s_login')
    s_password = input('Wellness Living API password (leave blank to keep current): ') or settings.get('s_password')
    AUTHORIZE_CODE = input('AUTHORIZE_CODE (leave blank to keep current): ') or settings.get('AUTHORIZE_CODE')
    AUTHORIZE_ID = input('AUTHORIZE_ID (leave blank to keep current): ') or settings.get('AUTHORIZE_ID')
    k_location = input('Location ID (leave blank to keep current): ') or settings.get('k_location')
    # Update the settings with new or existing values.
    settings.set('s_login', s_login)
    settings.set('s_password', s_password)
    settings.set('AUTHORIZE_CODE', AUTHORIZE_CODE)
    settings.set('AUTHORIZE_ID', AUTHORIZE_ID)
    settings.set('k_location', k_location)
    settings.save()  # Save the updated settings to the configuration file.

# Allows the user to update the door unlock duration setting.
def set_unlock_duration():
    unlock_duration = input('Enter new unlock duration in seconds (leave blank to keep current): ')
    if unlock_duration:
        settings.set('unlock_duration', unlock_duration)  # Update the unlock duration setting.
        settings.save()  # Save the change to the configuration file.
        print("Unlock duration updated to {} seconds.".format(unlock_duration))

# Tests the API connection using the current configuration.
def test_api_connection():
    member_id = input("Enter a Member ID for testing: ")
    settings.set('s_member', member_id)  # Temporarily set the member ID for testing.
    settings.save()  # Save the change for it to take effect.
    subprocess.run(['python', 'wellness_living.py'], check=True)  # Run the script to test API connection.

# Analyzes access times by running a separate script.
def analyze_access_times():
    print("Analyzing access times...")
    subprocess.run(['python', 'access_duration.py'], check=True)  # Run the script to analyze access times.

# Main menu for the setup script, providing various configuration options.
def main_menu():
    while True:  # Keep showing the menu until the user decides to exit.
        print("\nMenu:")
        print("1. Configure COM Ports")
        print("2. Configure API Credentials")
        print("3. Test API Connection")
        print("4. Set Unlock Duration")
        print("5. Analyze Access Times")
        print("6. Exit")
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
            analyze_access_times()
        elif choice == '6':
            print("Exiting setup...")
            subprocess.run(['python', 'dragonfly.py'], check=True)  # Optionally run another script upon exiting.
            break  # Exit the loop to terminate the program.

if __name__ == '__main__':
    main_menu()  # Run the main menu when the script is executed directly.
