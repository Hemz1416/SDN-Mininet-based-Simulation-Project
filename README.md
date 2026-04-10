# ARP Handling in SDN Networks

## Problem Statement
The objective of this project is to implement an SDN-based solution using Mininet and a Ryu OpenFlow controller to manage ARP requests and replies. The controller must explicitly intercept ARP packets, learn host MAC addresses, generate native ARP responses, and enable host discovery. Additionally, the project demonstrates network behavior control by explicitly allowing standard communication while blocking specific hosts based on programmed flow rules.

## Setup & Execution Steps

### Prerequisites
Ensure the following tools are installed on your Linux (Ubuntu) environment:
* **Mininet**
* **Ryu SDN Controller**
* **Wireshark** / **tshark**

### Execution
To run the project and observe the network behavior, open three separate terminal windows:

**1. Start the Ryu Controller (Terminal 1)**
Navigate to the project directory and run the controller script:
```bash
ryu-manager arp_proxy.py
