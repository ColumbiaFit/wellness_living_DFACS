import re
from datetime import datetime, timedelta

def parse_log_for_access_times(log_file_path):
    # Patterns to match the specific lines
    pattern_received = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}) - Received barcode: (.*)")
    pattern_unlocked = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}) - Hardware reports: Door Unlocked")

    access_times = []
    received_times = {}

    with open(log_file_path, 'r') as log_file:
        for line in log_file:
            match_received = pattern_received.match(line)
            match_unlocked = pattern_unlocked.match(line)

            if match_received:
                time_received = datetime.strptime(match_received.group(1), "%Y-%m-%d %H:%M:%S.%f")
                barcode = match_received.group(2)
                received_times[barcode] = time_received

            elif match_unlocked and received_times:
                time_unlocked = datetime.strptime(match_unlocked.group(1), "%Y-%m-%d %H:%M:%S.%f")
                # Assuming the last received barcode is the one getting unlocked
                if received_times:
                    # Calculate the difference from the last received barcode time
                    last_received_time = list(received_times.values())[-1]
                    duration = (time_unlocked - last_received_time).total_seconds()
                    access_times.append(duration)

    return access_times

def analyze_access_times(access_times):
    if not access_times:
        print("No access times found.")
        return

    min_time = min(access_times)
    max_time = max(access_times)
    avg_time = sum(access_times) / len(access_times)

    print(f"Minimum Access Time: {min_time:.2f} seconds")
    print(f"Maximum Access Time: {max_time:.2f} seconds")
    print(f"Average Access Time: {avg_time:.2f} seconds")

def main():
    log_file_path = 'dragonfly.log'
    access_times = parse_log_for_access_times(log_file_path)
    analyze_access_times(access_times)

if __name__ == "__main__":
    main()
