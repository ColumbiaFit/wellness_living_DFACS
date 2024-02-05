import re
from datetime import datetime

# Compile regex patterns for matching log lines
pattern_received = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}) - Received barcode: (.*)")
pattern_unlocked = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6}) - Hardware reports: Door Unlocked")

def parse_log_for_access_times(log_file_path):
    access_times = []  # List to hold access times
    log_entries = []  # List to hold log entries

    # Open the log file and read it into a list
    with open(log_file_path, 'r') as log_file:
        log_entries = log_file.readlines()

    # Reverse the log entries to process from the end of the file
    log_entries.reverse()

    for index, line in enumerate(log_entries):
        match_unlocked = pattern_unlocked.match(line)
        if match_unlocked:
            # Find the nearest preceding "Received barcode" entry
            for prev_line in log_entries[index:]:
                match_received = pattern_received.match(prev_line)
                if match_received:
                    time_unlocked = datetime.strptime(match_unlocked.group(1), "%Y-%m-%d %H:%M:%S.%f")
                    time_received = datetime.strptime(match_received.group(1), "%Y-%m-%d %H:%M:%S.%f")
                    # Calculate the difference in seconds
                    duration = (time_unlocked - time_received).total_seconds()
                    access_times.append(duration)
                    break  # Stop looking back after finding the matching "Received barcode"

    return access_times

def analyze_access_times(access_times):
    if not access_times:
        print("No access times found.")
        return

    # Calculate min, max, and average times
    min_time = min(access_times)
    max_time = max(access_times)
    avg_time = sum(access_times) / len(access_times)

    # Print the calculated times
    print(f"Minimum Access Time: {min_time:.2f} seconds")
    print(f"Maximum Access Time: {max_time:.2f} seconds")
    print(f"Average Access Time: {avg_time:.2f} seconds")

def main():
    log_file_path = 'dragonfly.log'  # Path to your log file
    access_times = parse_log_for_access_times(log_file_path)
    analyze_access_times(access_times)

if __name__ == "__main__":
    main()
