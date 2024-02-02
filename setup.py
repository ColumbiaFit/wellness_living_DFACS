import subprocess
import easysettings
import serial.tools.list_ports

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
    barcode_reader = format_com_port(input('Enter COM port for the barcode reader: '))
    door_controller = format_com_port(input('Enter COM port for the door controller: '))
    settings.set('barcode_reader', barcode_reader)
    settings.set('door_controller', door_controller)
    settings.save()


def update_api_credentials():
    s_login = input('Wellness Living API username (leave blank to keep current): ') or settings.get('s_login')
    s_password = input('Wellness Living API password (leave blank to keep current): ') or settings.get('s_password')
    AUTHORIZE_CODE = input('AUTHORIZE_CODE (leave blank to keep current): ') or settings.get('AUTHORIZE_CODE')
    AUTHORIZE_ID = input('AUTHORIZE_ID (leave blank to keep current): ') or settings.get('AUTHORIZE_ID')
    k_location = input('Location ID (leave blank to keep current): ') or settings.get('k_location')

    # Only update if the user has entered a value
    settings.set('s_login', s_login)
    settings.set('s_password', s_password)
    settings.set('AUTHORIZE_CODE', AUTHORIZE_CODE)
    settings.set('AUTHORIZE_ID', AUTHORIZE_ID)
    settings.set('k_location', k_location)
    settings.save()


def set_unlock_duration():
    current_duration = settings.get('unlock_duration', 'Not set')
    print(f"Current unlock duration: {current_duration} seconds")
    new_duration = input('Enter new unlock duration in seconds (leave blank to keep current): ')
    if new_duration:
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
            break


if __name__ == '__main__':
    main_menu()
