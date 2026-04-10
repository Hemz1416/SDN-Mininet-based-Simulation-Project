# SDN-Mininet-based-Simulation-Project
Implemented an SDN-based solution using Mininet and an OpenFlow controller (Ryu/POX), demonstrating controller–switch interaction, flow rule design, and network behavior, 
Based on the following topics :
ARP Handeling in SDN Networks

# Problem statment
Implement ARP request and reply handling using the sdn controller.

Expectation :
1. Intercept ARP packets
2. Generate ARP responses
3. Enable host discovery
4. Validate communication

# Solution
## Key Requirements Implemented
* **Mininet Topology:** Single switch connected to 3 hosts (`h1`, `h2`, `h3`).
* **Ryu OpenFlow Controller:** Manages the network logic via OpenFlow 1.3.
* **Explicit Match-Action Rules:** `packet_in` events are parsed to identify ARP traffic.
* **Native ARP Generation:** The controller crafts and sends ARP replies (`packet_out`) on behalf of known hosts.
* **Network Behavior Control:** Specific host blocking (e.g., dropping ARP requests destined for `10.0.0.3`).

---

## ⚙️ Setup & Execution Steps

### Prerequisites
This project was developed and validated on **Ubuntu 20.04 LTS** natively using Python 3.8 to ensure stable Ryu compatibility. 
Ensure you have the following installed:
```bash
sudo apt install mininet wireshark tshark python3-pip
pip3 install ryu
