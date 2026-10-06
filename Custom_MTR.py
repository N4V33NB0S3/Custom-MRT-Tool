#Author: Naveen Bose

"""This tool monitors multiple IP addresses with ping, displaying live latency updates,
went down/came up timestamps, and total downtime in an animated table similar to MTR.
An IP is considered unreachable only after three consecutive packet losses."""

import subprocess
import time
from datetime import datetime
import sys
import re
import threading
import curses

def is_valid_ip(ip):
    """Validate IPv4 address format."""
    ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return bool(re.match(ip_pattern, ip))

def read_ip_file(file_path):
    """Read IP addresses from the input file."""
    try:
        with open(file_path, 'r') as file:
            ips = [line.strip() for line in file if line.strip() and is_valid_ip(line.strip())]
        if not ips:
            print("Error: No valid IP addresses found in the input file.")
            sys.exit(1)
        return ips
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

def ping_once(ip):
    """Send a single ping to the IP and return status and RTT."""
    try:
        cmd = ['ping', '-c', '1', '-W', '4', ip]  
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stdout, stderr = process.communicate(timeout=10)
        
        # Parse RTT if ping is successful
        rtt = None
        if process.returncode == 0:
            match = re.search(r'time=(\d+\.\d+)', stdout)
            if match:
                rtt = float(match.group(1))
        return {'success': process.returncode == 0, 'rtt': rtt}
    except subprocess.TimeoutExpired:
        return {'success': False, 'rtt': None}
    except Exception:
        return {'success': False, 'rtt': None}

def get_status_symbol(state):
    """Return tick or cross based on state (color handled by curses)."""
    return '✓' if state == 'reachable' else '✗'

def monitor_ip(ip, log_file, interval, lock, status_dict):
    """Monitor a single IP, updating status, RTT, state change times, and total downtime.
    An IP is marked unreachable only after three consecutive packet losses."""
    state = None
    down_start = None  # Track start of current downtime period
    first_down = False  # Flag to track first "Went Down" event
    while True:
        result = ping_once(ip)
        current_time = datetime.now()
        timestamp = current_time.strftime('%Y-%m-%d %H:%M')  # HH:MM format
        
        with lock:
            current = status_dict.get(ip, {
                'state': 'unknown',
                'rtt': None,
                'fail_count': 0,
                'went_down': 'N/A',
                'came_up': 'N/A',
                'total_downtime': 0
            })
            fail_count = 0 if result['success'] else current['fail_count'] + 1
            new_state = state

            # Determine new state based on three consecutive failures or a single success
            if result['success']:
                new_state = 'reachable'
            elif fail_count >= 3:
                new_state = 'unreachable'

            # Update downtime and timestamps
            if new_state != state and new_state != 'unknown':
                if new_state == 'unreachable' and state is not None:
                    down_start = current_time
                    current['went_down'] = timestamp
                    first_down = True  # Mark first "Went Down"
                elif new_state == 'reachable' and state == 'unreachable' and first_down:
                    if down_start:
                        downtime_seconds = (current_time - down_start).total_seconds()
                        current['total_downtime'] += downtime_seconds
                        down_start = None
                    current['came_up'] = timestamp

            # Update status dictionary
            status_dict[ip] = {
                'state': new_state or current['state'],
                'rtt': result['rtt'],
                'fail_count': fail_count,
                'went_down': current['went_down'],
                'came_up': current['came_up'] if not first_down or new_state != 'reachable' else timestamp if new_state != state else current['came_up'],
                'total_downtime': current['total_downtime']
            }

            # No ongoing downtime accumulation here; handled by state transition
        
        # Log status changes
        if new_state != state and new_state != 'unknown':
            symbol = get_status_symbol(new_state)
            if state is None:
                message = f"{timestamp}: {ip} is initially {new_state} {symbol}"
            else:
                message = f"{timestamp}: {ip} became {new_state} {symbol}"
            
            if result['success'] and result['rtt'] is not None:
                message += f" (RTT: {result['rtt']:.2f} ms)"
            
            with lock:
                with open(log_file, 'a') as f:
                    f.write(message + '\n')
            
            state = new_state
        
        time.sleep(interval)

def draw_table(stdscr, ips, status_dict, lock, log_file):
    """Draw and update the table in the terminal using curses."""
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Green for reachable
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)    # Red for unreachable
    
    stdscr.timeout(1000)  # Refresh every 1 second
    curses.curs_set(0)    # Hide cursor
    
    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        
        # Draw header
        header = f"{'IP Address':<16} {'Status':<10} {'RTT':<10} {'Went Down':<25} {'Came Up':<25} {'Total Downtime (m)':<18}"
        if max_y > 1 and max_x > len(header):
            stdscr.addstr(0, 0, header[:max_x-1], curses.A_BOLD)
        
        # Draw table rows
        for i, ip in enumerate(ips):
            if i + 2 >= max_y:  # Avoid drawing beyond terminal height
                break
            with lock:
                status_info = status_dict.get(ip, {
                    'state': 'unknown',
                    'rtt': None,
                    'went_down': 'N/A',
                    'came_up': 'N/A',
                    'total_downtime': 0,
                    'fail_count': 0
                })
                state = status_info['state']
                rtt = status_info['rtt']
                went_down = status_info['went_down']
                came_up = status_info['came_up']
                total_downtime = status_info['total_downtime']
            
            symbol = get_status_symbol(state)
            color = curses.color_pair(1) if state == 'reachable' else curses.color_pair(2)
            rtt_str = f"{rtt:.2f}" if rtt is not None else "N/A"
            went_down_str = went_down if went_down else "N/A"
            came_up_str = came_up if came_up else "N/A"
            downtime_minutes = total_downtime / 60.0
            downtime_str = f"{downtime_minutes:.1f}" if total_downtime else "0.0"
            row = f"{ip:<16} {symbol:<10} {rtt_str:<10} {went_down_str:<25} {came_up_str:<25} {downtime_str:>18}"
            
            try:
                if max_x > len(row):
                    stdscr.addstr(i + 2, 0, f"{ip:<16}", curses.A_NORMAL)
                    stdscr.addstr(i + 2, 16, f"{symbol:<10}", color | curses.A_NORMAL)
                    stdscr.addstr(i + 2, 26, f"{rtt_str:<10}", curses.A_NORMAL)
                    stdscr.addstr(i + 2, 36, f"{went_down_str:<25}", curses.A_NORMAL)
                    stdscr.addstr(i + 2, 61, f"{came_up_str:<25}", curses.A_NORMAL)
                    stdscr.addstr(i + 2, 86, f"{downtime_str:>18}", curses.A_NORMAL)
                else:
                    stdscr.addstr(i + 2, 0, row[:max_x-1], curses.A_NORMAL)
            except curses.error:
                pass  # Ignore errors if terminal is too small
        
        # Draw footer
        footer = f"Logging to {log_file}. Press Ctrl+C to stop."
        if max_y > len(ips) + 3 and max_x > len(footer):
            try:
                stdscr.addstr(len(ips) + 3, 0, footer[:max_x-1], curses.A_DIM)
            except curses.error:
                pass
        
        stdscr.refresh()
        
        try:
            stdscr.getch()  # Non-blocking check for input
        except curses.error:
            pass

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 ping_monitor.py <ip_file>")
        sys.exit(1)

    ip_file = sys.argv[1]
    log_file = "reachability_log.log"
    interval = 1  

    ips = read_ip_file(ip_file)
    print(f"Loaded {len(ips)} IP addresses from {ip_file}")
    print(f"Logging status changes to {log_file}")
    print("Starting monitoring...")

    lock = threading.Lock()
    status_dict = {}  # Shared dictionary to store status, RTT, timestamps, and downtime
    threads = []

    for ip in ips:
        thread = threading.Thread(target=monitor_ip, args=(ip, log_file, interval, lock, status_dict))
        thread.daemon = True
        thread.start()
        threads.append(thread)

    # Start curses interface
    try:
        curses.wrapper(draw_table, ips, status_dict, lock, log_file)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()