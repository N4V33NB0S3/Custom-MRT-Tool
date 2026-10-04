# Custom MTR



A lightweight Python-based **custom MTR-style network monitoring tool** designed for network engineers to monitor multiple network devices simultaneously and measure actual service downtime.

The tool continuously monitors multiple IPv4 addresses, displays their live reachability status and RTT in a terminal-based dashboard, records availability changes, and calculates total downtime.

An IP address is considered **unreachable only after three consecutive ping failures**, helping reduce false down events caused by individual packet loss.

---

## 🚀 Why I Built This

This tool was created for a real-world ISP network operations requirement during **firmware upgrade activities on Provider Edge (PE) devices**.

Firmware upgrades are often **planned service-affecting activities** where individual PE devices may become temporarily unreachable while the upgrade or reboot is in progress.

In a multi-vendor network environment, it was important to accurately determine:

- When each device actually went down
- When each device came back up
- How long each device was unreachable
- Whether the observed downtime matched the expected maintenance window
- The downtime of multiple devices simultaneously

Instead of manually pinging devices or checking them individually, I developed **Custom MTR** to provide a live centralized view of the reachability status of multiple PE devices.

### Multi-Vendor Environment

The tool was useful for monitoring devices from different network vendors, including:

```text
Nokia
Huawei
Juniper
Cisco
Arista
```

This makes the tool vendor-independent because it monitors the **IP reachability of the device**, rather than relying on vendor-specific CLI commands.

---

## 🎯 Real-World Use Case

### PE Firmware Upgrade Monitoring

A typical maintenance activity could involve multiple Provider Edge devices:

```text
                ISP Network
                    │
       ┌────────────┼────────────┐
       │            │            │
    Nokia          Huawei      Juniper
      PE             PE           PE
    10.1.1.1       10.1.1.2     10.1.1.3
       │            │            │
       └────────────┼────────────┘
                    │
              Custom MTR
                    │
             Live Monitoring
```

Before starting the maintenance activity, the management IP addresses of the devices are added to an input file.

```text
10.1.1.1
10.1.1.2
10.1.1.3
10.1.1.4
10.1.1.5
```

Custom MTR then continuously monitors all devices.

When a device becomes unreachable:

```text
PE-01 → Reachable
PE-01 → Packet loss
PE-01 → Packet loss
PE-01 → Packet loss
             ↓
       Device DOWN
```

The tool records the **Went Down** timestamp.

When the device becomes reachable again:

```text
PE-01 → Unreachable
PE-01 → Reachable
             ↓
        Device UP
```

The **Came Up** timestamp is recorded and the downtime is calculated.

---

## 📊 Example Maintenance Monitoring

During a firmware upgrade activity, the dashboard can provide a view such as:

```text
IP Address       Status     RTT        Went Down                 Came Up                   Total Downtime (m)
---------------------------------------------------------------------------------------------------------------
10.1.1.1         ✓          2.31       N/A                       N/A                                    0.0
10.1.1.2         ✗          N/A        2026-10-04 02:15          2026-10-04 02:23                     8.0
10.1.1.3         ✓          1.84       2026-10-04 02:20          2026-10-04 02:27                     7.0
10.1.1.4         ✗          N/A        2026-10-04 02:31          2026-10-04 02:42                    11.0
10.1.1.5         ✓          3.12       N/A                       N/A                                    0.0
```

This gives the operations team an immediate view of the impact of the maintenance activity.

---

## 🚀 Features

- Monitor multiple IPv4 addresses simultaneously
- Designed for multi-vendor network environments
- Live MTR-style terminal dashboard
- Real-time RTT monitoring
- Reachable / unreachable status
- Detects **3 consecutive packet losses** before declaring an IP unreachable
- Records **Went Down** timestamp
- Records **Came Up** timestamp
- Calculates accumulated downtime
- Logs status changes
- Uses a separate thread for each monitored IP
- IPv4 address validation
- Handles unreachable hosts and ping timeouts
- Lightweight and dependency-free apart from the operating system's `ping` utility

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

## 🛡️ Three-Failure Detection

The tool does not immediately declare a device down after a single lost packet.

Instead, it requires **three consecutive failures**:

```text
Ping 1 → Failure
Ping 2 → Failure
Ping 3 → Failure
             ↓
       DEVICE UNREACHABLE
```

This is particularly useful during network monitoring because transient packet loss should not automatically be interpreted as a service outage.

A successful response resets the reachability state:

```text
Ping 1 → Failure
Ping 2 → Success
             ↓
          REACHABLE
```

---

## ⏱️ Downtime Calculation

When a monitored device transitions from reachable to unreachable:

```text
Went Down → 02:15
```

When it becomes reachable again:

```text
Came Up → 02:23
```

The tool calculates:

```text
Downtime = Came Up - Went Down
```

Example:

```text
Went Down : 02:15
Came Up   : 02:23

Total Downtime = 8 minutes
```

Multiple downtime periods are accumulated for the same device.

---

## 🧵 Multi-IP Monitoring

Each IP address is monitored using its own thread.

```text
                    Custom MTR
                        │
          ┌─────────────┼─────────────┐
          │             │             │
       Thread 1      Thread 2      Thread 3
          │             │             │
       Nokia PE      Huawei PE    Juniper PE
       10.1.1.1      10.1.1.2     10.1.1.3
```

This allows multiple network devices to be monitored concurrently rather than sequentially.

---

## 📝 Logging

Status changes are written to:

```text
reachability_log.log
```

Example:

```text
2026-10-04 02:15: 10.1.1.2 became unreachable ✗
2026-10-04 02:23: 10.1.1.2 became reachable ✓ (RTT: 2.14 ms)
```

The log can be retained as a record of the observed device downtime during a maintenance activity.

---

## 📁 Project Structure

```text
Custom-MTR/
│
├── custom_mtr.py
├── ip_list.txt
├── reachability_log.log
├── LICENSE
└── README.md
```

---

## ⚙️ Requirements

### Operating System

Recommended:

- Linux
- Python 3.x
- ICMP/ping support
- Interactive terminal

### Python Modules

The script uses Python standard-library modules:

```text
subprocess
time
datetime
sys
re
threading
curses
```

No external Python packages are required.

---

## 📝 Create IP Address List

Create a file containing the management IP addresses of the devices you want to monitor.

Example:

```text
10.1.1.1
10.1.1.2
10.1.1.3
10.1.1.4
10.1.1.5
```

Save it as:

```text
ip_list.txt
```

One IPv4 address should be placed on each line.

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

---

## 🔍 Ping Logic

Each IP is monitored using:

```bash
ping -c 1 -W 4 <IP>
```

The RTT is extracted from successful responses.

Example:

```text
10.1.1.1 → 1.82 ms
```

If the device does not respond:

```text
RTT → N/A
```

---

## 🖥️ Terminal Interface

The MTR-style dashboard provides:

- Live device status
- RTT
- Went Down timestamp
- Came Up timestamp
- Total downtime
- Color-coded reachability

Reachable devices are displayed in **green**.

Unreachable devices are displayed in **red**.

Press:

```text
Ctrl + C
```

to stop monitoring.

---

## 🔧 Configuration

The default monitoring interval is:

```python
interval = 1
```

You can change it if required:

```python
interval = 5
```

---

## 📈 Where This Tool Is Useful

### ISP Operations

- Provider Edge monitoring
- Firmware upgrade activities
- Planned maintenance
- Service-affecting activities
- Network migration activities
- Device reboot monitoring
- Post-maintenance validation

### Multi-Vendor Networks

The tool can monitor devices from different vendors simultaneously:

```text
┌───────────┐
│   Nokia   │
└─────┬─────┘
      │
┌───────────┐
│  Huawei   │
└─────┬─────┘
      │
┌───────────┐
│  Juniper  │
└─────┬─────┘
      │
┌───────────┐
│   Cisco   │
└─────┬─────┘
      │
┌───────────┐
│  Arista   │
└─────┬─────┘
      │
      ▼
 Custom MTR
```

Because monitoring is based on IP reachability, the tool does not depend on vendor-specific commands.

---

## 🔮 Future Improvements

Potential enhancements:

- [ ] CSV downtime reports
- [ ] Daily/weekly/monthly availability reports
- [ ] Packet-loss percentage
- [ ] Average/min/max RTT
- [ ] Telegram alerts
- [ ] Email alerts
- [ ] Prometheus metrics
- [ ] Grafana dashboard
- [ ] JSON output
- [ ] Configurable monitoring interval
- [ ] Configurable failure threshold
- [ ] IPv6 support
- [ ] systemd service integration
- [ ] Historical uptime percentage
- [ ] Automatic log rotation
- [ ] Maintenance-window reports
- [ ] Automated SLA/availability calculation

---

## 🎯 Project Objective

The primary objective of Custom MTR is to provide a simple, vendor-independent method of measuring **actual network device downtime during planned maintenance activities**.

The tool was developed from a practical ISP network operations requirement and can be used to monitor multiple Provider Edge devices during service-affecting activities.

It provides an immediate operational view of:

```text
Device Availability
       +
    RTT
       +
 Went Down
       +
  Came Up
       +
Total Downtime
```

This makes it easier to validate the actual impact of a maintenance activity and retain an operational record of observed downtime.

---

## ⚠️ Disclaimer

This project is intended for:

- Network monitoring
- Authorized infrastructure management
- Network engineering labs
- Maintenance activity monitoring
- Educational purposes

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
