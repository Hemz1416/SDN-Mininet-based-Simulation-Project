# ARP Handling in SDN Networks

## Overview

This project implements a **Software Defined Networking (SDN)** based ARP Proxy using **Mininet** as the network emulator and the **Ryu OpenFlow controller** (OpenFlow 1.3). Instead of flooding ARP requests across the entire network, the controller intelligently intercepts ARP packets, builds a dynamic ARP table, generates replies directly, and enforces host-level access control by blocking specific IPs.

This is a practical demonstration of how an SDN controller can replace traditional broadcast-heavy ARP behavior with centralized, programmable packet handling.

---

## Problem Statement

The objective of this project is to implement an SDN-based solution using Mininet and a Ryu OpenFlow controller to manage ARP requests and replies. The controller must explicitly:
- Intercept ARP packets sent to the controller
- Learn host MAC addresses dynamically
- Generate native ARP responses without flooding (when the MAC is known)
- Flood ARP requests only when the destination is unknown
- Block ARP requests destined for a specific IP (`10.0.0.3`) to demonstrate programmatic access control

---

## How It Works

The `ArpProxyApp` Ryu controller application handles the following logic:

| Event | Controller Action |
|---|---|
| New host sends ARP | Learn IP → MAC mapping, store in `arp_table` |
| ARP Request for **known** IP | Controller generates ARP Reply directly (`[INTERCEPT]`) |
| ARP Request for **unknown** IP | Flood the request to all ports (`[MISS]`) |
| ARP Request for **blocked** IP (`10.0.0.3`) | Drop the packet silently (`[BLOCKED]`) |
| Non-ARP packet | Flood to all ports |

### Log Prefixes (Controller Output)
- `[LEARNED]` — A new IP-to-MAC mapping has been discovered
- `[INTERCEPT]` — Controller is generating an ARP Reply on behalf of the destination host
- `[MISS]` — Destination MAC is unknown; flooding the ARP request
- `[BLOCKED]` — ARP request for the blocked IP was dropped

---

## Project Structure

```
SDN-Mininet-based-Simulation-Project/
│
├── arp_proxy.py      # Ryu SDN Controller — ARP Proxy Application
└── README.md         # Project documentation
```

---

## Prerequisites

Ensure the following tools are installed on your **Linux (Ubuntu)** environment:

- **Python 3**
- **Mininet** — Network emulator
- **Ryu SDN Framework** — OpenFlow controller
- **Open vSwitch (OVS)** — Software switch (comes with Mininet)
- **Wireshark / tshark** *(optional)* — For packet capture and inspection

### Installation Commands

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Mininet
sudo apt install -y mininet

# Install Ryu
pip install ryu

# Install tshark (optional, for packet capture)
sudo apt install -y tshark
```

---

## Setup & Execution

Open **three separate terminal windows** and follow the steps below in order.

---

### Terminal 1 — Start the Ryu Controller

Navigate to the project directory and launch the ARP Proxy application:

```bash
ryu-manager arp_proxy.py
```

You should see Ryu load the app and instantiate `ArpProxyApp` and `OFPHandler`:

<img width="845" height="150" alt="image" src="https://github.com/user-attachments/assets/3f4883dd-f27e-4238-8245-495b51a8d2fe" />


---

### Terminal 2 — Start the Mininet Topology

Create a single-switch topology with **3 hosts** using simple MAC addresses and connect it to the remote Ryu controller:

```bash
sudo mn --topo single,3 --mac --controller remote,ip=127.0.0.1,port=6653 --switch ovsk,protocols=OpenFlow13
```

This creates:
- `h1` → `10.0.0.1`
- `h2` → `10.0.0.2`
- `h3` → `10.0.0.3` *(blocked IP)*
- `s1` → OpenFlow switch connected to the Ryu controller

<img width="940" height="226" alt="image" src="https://github.com/user-attachments/assets/56e6bb11-8b85-4904-ae07-f8b1787c2891" />


---

## Testing the Network

Run the following commands inside the **Mininet CLI** (Terminal 2).

---

### Test 1 — Ping between h1 and h2 (Allowed Hosts)

```
mininet> h1 ping -c 2 h2
```

Since `h2`'s MAC is not yet known to the controller at the time of the first ARP request, the controller floods the packet (`[MISS]`). The ping results in `Destination Host Unreachable` as the ARP resolution does not complete via flooding in this topology:

<img width="940" height="204" alt="image" src="https://github.com/user-attachments/assets/47524edc-5709-46bf-9f81-6eaf45bafc91" />


Meanwhile, the controller logs show `h1`'s MAC was learned, and `h2` is unknown — triggering repeated flooding:

<img width="813" height="120" alt="image" src="https://github.com/user-attachments/assets/249973b8-e3ad-44e6-bd5a-f31767a9f1e8" />


---

### Test 2 — Ping to Blocked Host (h1 → h3)

```
mininet> h1 ping -c 2 h3
```

**Expected behavior:** Ping fails. The controller drops all ARP requests targeting `10.0.0.3` and logs `[BLOCKED]`:

<img width="940" height="210" alt="image" src="https://github.com/user-attachments/assets/c67baa11-3132-4a29-aa69-4885b9e23145" />


The controller terminal confirms the block:

<img width="838" height="109" alt="image" src="https://github.com/user-attachments/assets/f8704bcc-4785-4a79-ad29-26eaf509d120" />


---

### Test 3 — iperf Bandwidth Test (h1 → h2)

```
mininet> iperf h1 h2
```

Since ARP resolution for `h2` fails (no route established), iperf also cannot connect. The test exits with `Exception: Could not connect to iperf on port 5001`. Running `mn -c` afterward cleanly removes all Mininet state:

<img width="940" height="493" alt="image" src="https://github.com/user-attachments/assets/edd6fadd-5fd0-44ee-8ae3-849ea1f77807" />


The controller continues to log repeated `[MISS]` events during the iperf attempt, confirming that `h2` remains unresolved:

<img width="780" height="161" alt="image" src="https://github.com/user-attachments/assets/9ba98de5-e4b1-48ea-b86b-1a95ea0397a8" />


---

## Key Concepts Demonstrated

### ARP Proxy
Traditional ARP floods requests across all ports every time a host wants to resolve a MAC address. This controller acts as an **ARP Proxy** — it intercepts requests, checks its own ARP table, and responds directly, eliminating unnecessary broadcast traffic when the MAC is already known.

### Programmatic Access Control
By setting `self.blocked_ip = "10.0.0.3"` in the controller, all ARP requests targeting that IP are silently dropped. This demonstrates how SDN allows fine-grained, software-defined network policies without any hardware configuration.

### OpenFlow 1.3
The application uses **OpenFlow 1.3** (`OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]`). A default table-miss flow entry is installed at startup that sends all unmatched packets to the controller, enabling packet-in handling for every new flow.

---

## Topology Diagram

```
           [ Ryu Controller ]
                  |
            (OpenFlow 1.3)
                  |
              [ s1 (OVS) ]
             /     |      \
           h1     h2      h3
       10.0.0.1 10.0.0.2 10.0.0.3
                         (BLOCKED)
```

---

## Cleanup

To stop Mininet and clean up any leftover network state:

```bash
sudo mn -c
```

To stop the Ryu controller, press `Ctrl+C` in Terminal 1.

---

## Technologies Used

| Tool | Purpose |
|---|---|
| **Mininet** | Virtual network emulation |
| **Ryu** | SDN OpenFlow controller framework |
| **OpenFlow 1.3** | Switch-controller communication protocol |
| **Open vSwitch (OVS)** | Software-based OpenFlow switch |
| **Python 3** | Controller application language |
| **tshark / Wireshark** | Packet capture and analysis |

---

## References

- [Mininet Documentation](http://mininet.org/)
- [Ryu SDN Framework](https://ryu-sdn.org/)
- [OpenFlow Specification](https://opennetworking.org/software-defined-standards/specifications/)
- [Open vSwitch](https://www.openvswitch.org/)
