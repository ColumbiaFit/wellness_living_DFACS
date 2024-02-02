import easysettings
import serial
from datetime import datetime
import subprocess
import time

settings = easysettings.EasySettings("settings.conf")

def process_barcode(barcode):
    settings.set('s_member', barcode)
    settings.save()
    result = subprocess.run(['python', 'wellness_living.py'], capture_output=True, text=True)
    output = result.stdout
    if "can_access': True" in output:
        access_status = "Allowed"
        print(f"{datetime.now()} - Barcode: {barcode} - Access: {access_status}")
        # Call lock_control.py instead of using unlock_door function
        subprocess.run(['python', 'lock_control.py'], check=True)
    else:
        access_status = "Denied"
        print(f"{datetime.now()} - Barcode: {barcode} - Access: {access_status}")

def listen_for_barcodes():
    while True:
        try:
            barcode_reader = settings.get('barcode_reader')
            with serial.Serial(barcode_reader, 9600, timeout=1) as ser_barcode:
                print(f"Listening for barcodes on {barcode_reader}...")
                while True:
                    barcode = ser_barcode.readline().decode('utf-8').strip()
                    if barcode:
                        print(f"{datetime.now()} - Received barcode: {barcode}")
                        process_barcode(barcode)
        except Exception as e:
            print(f"{datetime.now()} - Error listening to barcodes or serial port not accessible: {e}")
            time.sleep(10)

if __name__ == '__main__':
    listen_for_barcodes()
