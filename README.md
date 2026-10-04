# Custom MTR

\
\


A lightweight Python-based **custom MTR-style network monitoring tool** designed for network engineers.

The tool continuously monitors multiple IPv4 addresses, displays their live status and RTT in a terminal-based dashboard, records availability changes, and calculates total downtime.

An IP address is considered **unreachable only after three consecutive ping failures**, helping reduce false down events caused by individual packet loss.

---

## 🚀 Features

- Monitor multiple IPv4 addresses simultaneously
- Live terminal dashboard using Python `curses`
- Real-time RTT monitoring
- Reachable / unreachable status
- Detects **3 consecutive packet losses** before declaring an IP unreachable
- Records **Went Down** timestamp
- Records **Came Up** timestamp
- Calculates accumulated downtime
- Logs status changes to a log file
- Uses a separate thread for each monitored IP
- IPv4 address validation
- Handles unreachable hosts and ping timeouts
- Lightweight — uses standard Python libraries

---

## 📊 MTR-Style Dashboard

The monitoring interface displays:

```text
IP Address       Status     RTT        Went Down                 Came Up                   Total Downtime (m)
---------------------------------------------------------------------------------------------------------------
8.8.8.8          ✓          12.34      N/A                       N/A                                    0.0
1.1.1.1          ✓          18.42      N/A                       N/A                                    0.0
192.168.1.1      ✗          N/A        2026-10-04 14:32          2026-10-04 14:35                     3.0
```

The status symbols are:

```text
✓  Reachable

✗  Unreachable
```

The dashboard refreshes every second.

---

## 🧠 How It Works

The Custom MTR monitoring process works like this:

```text
                 ┌─────────────────────┐
                 │    IP Address File  │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Validate IPv4       │
                 │ Addresses           │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Create Monitoring   │
                 │ Thread per IP       │
                 └──────────┬──────────┘
                            │
                            ▼
                  ┌──────────────────┐
                  │ Send ICMP Ping   │
                  └────────┬─────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
             Success                Failure
                │                     │
                ▼                     ▼
        ┌──────────────┐      ┌──────────────┐
        │ Reachable    │      │ Increment    │
        │ + RTT        │      │ Fail Counter │
        └──────┬───────┘      └──────┬───────┘
               │                     │
               │              3 consecutive
               │                 failures
               │                     │
               │                     ▼
               │              ┌──────────────┐
               │              │ Unreachable  │
               │              └──────┬───────┘
               │                     │
               └──────────┬──────────┘
                          ▼
                 ┌─────────────────────┐
                 │ Update MTR Dashboard│
                 │ & Log Status Change │
                 └──────────┬──────────┘
                            │
                            ▼
                      Repeat every
                       1 second
```

---

## 📁 Project Structure

```text
Custom-MTR/
│
├── custom_mtr.py
├── ip_list.txt
├── reachability_log.log
└── README.md
```

---

## ⚙️ Requirements

### Operating System

The tool is designed for systems where the standard Linux `ping` command and terminal `curses` interface are available.

Recommended:

- Linux
- Python 3.x

### Python Modules

The script primarily uses Python standard-library modules:

```text
subprocess
time
datetime
sys
re
threading
curses
```

No third-party Python package is required by the script.

---

## 📝 Create IP Address List

Create a file containing the IPv4 addresses you want to monitor.

Example:

```text
8.8.8.8
1.1.1.1
192.168.1.1
192.168.1.254
10.0.0.1
```

Save it as:

```text
ip_list.txt
```

One IP address should be placed on each line.

The script validates each address before monitoring it. Invalid addresses are ignored.

---

## ▶️ Run Custom MTR

Make the script executable:

```bash
chmod +x custom_mtr.py
```

Run:

```bash
python3 custom_mtr.py ip_list.txt
```

Or:

```bash
./custom_mtr.py ip_list.txt
```

The script expects exactly one argument:

```text
python3 custom_mtr.py <ip_file>
```



---

## 🔍 Ping Logic

Each IP is pinged once per monitoring cycle.

The command used is:

```bash
ping -c 1 -W 4 <IP>
```

The script extracts the RTT from successful ping responses.

Example:

```text
8.8.8.8 → 12.43 ms
```

If the ping fails:

```text
RTT → N/A
```

---

## 🛡️ Three-Failure Detection

One of the important features of Custom MTR is that **one packet loss does not immediately mark the device as down**.

The logic is:

```text
Ping 1 → Failure
Ping 2 → Failure
Ping 3 → Failure
             ↓
        UNREACHABLE
```

But if the host responds:

```text
Ping 1 → Failure
Ping 2 → Success
             ↓
         REACHABLE
```

This helps prevent temporary packet loss from generating unnecessary downtime events.

---

## ⏱️ Downtime Tracking

When an IP transitions from reachable to unreachable, Custom MTR records:

```text
Went Down
```

When it becomes reachable again:

```text
Came Up
```

The difference between these timestamps is used to calculate downtime.

Multiple downtime periods are accumulated into:

```text
Total Downtime (m)
```



---

## 🧵 Multi-IP Monitoring

Each IP address gets its own monitoring thread.

For example:

```text
Main Process
     │
     ├── Thread → 8.8.8.8
     ├── Thread → 1.1.1.1
     ├── Thread → 192.168.1.1
     └── Thread → 10.0.0.1
```

A shared dictionary stores monitoring information, while a threading lock protects shared data.

---

## 📝 Logging

Status changes are written to:

```text
reachability_log.log
```

Example:

```text
2026-10-04 14:20: 8.8.8.8 is initially reachable ✓ (RTT: 12.31 ms)
2026-10-04 14:35: 192.168.1.1 became unreachable ✗
2026-10-04 14:38: 192.168.1.1 became reachable ✓ (RTT: 1.42 ms)
```

The log records status transitions rather than writing every individual ping result.

---

## 🖥️ Terminal Interface

The MTR-style dashboard is implemented using Python's `curses` module.

It provides:

- Live status
- Color-coded reachability
- RTT
- Down timestamp
- Recovery timestamp
- Total downtime

Reachable devices are displayed in **green**, while unreachable devices are displayed in **red**.

Press:

```text
Ctrl + C
```

to stop monitoring.

---

## 📈 Example Use Cases

### ISP Network Monitoring

Monitor:

```text
Core routers
PE routers
CE routers
BNG/BRAS
DNS servers
Gateway devices
Customer endpoints
```

### Home Network Monitoring

Monitor:

```text
Router
Raspberry Pi
NAS
DNS server
Internet gateway
```

### Lab Monitoring

Useful for EVE-NG / GNS3 environments:

```text
Router-1
Router-2
Firewall
Switch
Linux server
Management IP
```

### Connectivity Monitoring

Monitor important public endpoints:

```text
8.8.8.8
1.1.1.1
```

to help determine whether an outage is local or upstream.

---

## 🔧 Configuration

The default monitoring interval is:

```python
interval = 1
```

This means the monitoring loop runs approximately every **1 second** for each IP.

You can modify it if required:

```python
interval = 5
```

---

## 🧪 Troubleshooting

### `ping: command not found`

Install the ping utility:

```bash
sudo apt update
sudo apt install iputils-ping
```

### Terminal display is broken

Run Custom MTR from a normal interactive terminal.

### No valid IP addresses found

Check the input file:

```bash
cat ip_list.txt
```

Make sure each line contains a valid IPv4 address.

### Permission issues

Try:

```bash
python3 custom_mtr.py ip_list.txt
```

---

## 🔮 Future Improvements

Potential enhancements for future versions:

- [ ] CSV logging
- [ ] Daily/weekly/monthly availability reports
- [ ] Packet-loss percentage
- [ ] Average/min/max RTT
- [ ] ICMP packet-loss statistics
- [ ] Telegram alerts
- [ ] Email alerts
- [ ] Prometheus metrics
- [ ] Grafana dashboard
- [ ] JSON output
- [ ] Configurable ping interval
- [ ] Configurable failure threshold
- [ ] IPv6 support
- [ ] systemd service integration
- [ ] Historical uptime percentage
- [ ] Automatic log rotation

---

## 🎯 Project Goals

Custom MTR was built as a practical network monitoring utility while gaining hands-on experience with:

- Python network automation
- ICMP monitoring
- Multithreading
- RTT measurement
- Network availability monitoring
- Terminal UI development
- Linux troubleshooting
- Log management
- Failure detection logic

---

## ⚠️ Disclaimer

This project is intended for **network monitoring, learning, and authorized infrastructure management**.

Only monitor systems and IP addresses that you own or have permission to monitor.

---

## 📜 License

This project is licensed under the **MIT License**.

See the `LICENSE` file for details.

---

## 👨‍💻 Author

**Naveen Bose**

Network Security / Network Operations Engineer

GitHub: [N4V33NB0S3](https://github.com/N4V33NB0S3)

---

⭐ If you find this project useful, consider giving the repository a star.
