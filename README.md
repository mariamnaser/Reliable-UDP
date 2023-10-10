# Reliable UDP File Transfer System

## Overview
 This program consists of two Python scripts: `tcpserver.py` and `tcpclient.py`, designed to facilitate reliable file transfer over a UDP-based protocol that mimics the functionality of TCP. The server (`tcpserver.py`) receives and reconstructs files sent by the client (`tcpclient.py`).


## Server:`tcpserver.py`

### Usage
To use `tcpserver.py`, run the following command:
```
python3 tcpserver.py <file> <listening_port> <address_for_acks> <port_for_acks>
```
- `<file>`: The name of the file to be created from received data.
- `<listening_port>`: The port on which the server listens for incoming packets.
-  `<address_for_acks>`: The IP address to which acknowledgment packets are sent.
-  `<port_for_acks>`: The port for sending acknowledgment packets.

### How it works  
1. The server binds to the specified listening port and waits for incoming packets.
2. It continuously listens for incoming packets in a separate thread, verifying their checksum.
3. The server maintains a sliding window mechanism to organize received packets and acknowledges them accordingly.
4. When all packets are received and organized, it reconstructs the original file in the correct order.
5. Finally, the server sends an acknowledgment with the FIN flag to signal the end of transmission.

### Key Functions
- `run()`:Main function to start the server, handling packet reception and organization.
- `list_to_file()`: Organizes and writes received packets into the output file.
- `recv_station()`: Listens for incoming packets and adds them to the received list.
- `select_repeat()`: Manages sliding window acknowledgment, using a selective repeat approach.
- `build_msg(data="", flags=0)`: Creates a packet with the provided data and flags.



## Client: `tcpclient.py`

### Usage
To use `tcpclient.py`, run the following command:
```
python3 tcpclient.py <file> <address_of_udpl> <port_number_of_udpl> <window_size> <ack_port_number>
```
- `<file>`: The name of the file to send to the server.
- `<address_of_udpl>`: The IP address of the proxy receiving the data.
- `<port_number_of_udpl>`: The listening port of the proxy for incoming packets.
-  `<window_size>`: The size of the sliding window for managing packet transmission.
-  `<ack_port_number>`: The port on which the client listens for acknowledgments from the server.

### How it works  
1. The client reads the specified file, divides it into packets, and listens for acknowledgments from the server.
2. It uses a sliding window mechanism to manage packet transmission
3. It adjusts the resending protocol based on network conditions.
4. After sending all data packets, the client sends a packet with the FIN flag to signal the end of transmission.

### Key Functions
- `run()`: Main function to start the client, managing the sliding window for sending data packets.
- `file_to_list()`: Reads and divides the specified file into packets.
- `listen_ack()`: Listens for acknowledgment packets from the server.
- `sliding_window()`: Manages the sliding window mechanism for sending data packets.
- `build_msg(data="", flags=0)`: Creates a packet with the provided data and flags.
## Note
- IMPORTANT: This program does not account if the client puts in a certain type of file but the receiver places a different type.
  - For example: (client: input.jpg receiver: input.txt)
- clean.sh can be used for testing to compare files and delete the created file
### Error Handling
- Both files handles retransmission
- Error logging in done throughout both functions
- Checksum validation is preformed on all received acknowledgment packets.

### Manipulation & Rights
This program was created to be used with the proxy that was given. To use this without the proxy, switch the information to that of the server, you can then reduce the inputs to no longer need the redundancy of providing the listening port multiple times. The code is commented throughout to assist in understand what it is doing.
The proxy has been provided by professor, and TA team. I had no part in it.

### Test
Terminal One:
```
./newudpl -i localhost:6000 -o localhost:5050
```
Terminal Two:
```
python3 tcpserver.py output.txt 5050 localhost 6000
```
Terminal Three:
```
python3 tcpclient.py input.txt localhost 41192 2 6000
```
**Note:** 41192 is the defult port for proxy
## Summary
This program allows you to transfer files reliably over a UDP-like protocol, ensuring that data is received and reconstructed in the correct order. Please ensure that the `helper.py` script is available in the same directory for both `tcpserver.py` and `tcpclient.py` to work correctly.
