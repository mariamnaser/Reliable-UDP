import struct
import socket
import threading
import random
import logging
import sys
import os
HEADER_CONTENTS = '!HHIIHHHH'
HEADER_LENGTH = 20
SYN = 0x02
ACK = 0x10
FIN = 0x01
MSS = 500

#Print a line of characters across the console.
def print_line(width=50, character='-'):
    line = character * width
    print(line)

#Error Logging
def setup_logging(file='error_log.txt'):
    logging.basicConfig(filename = file, level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

#validates ip
def valid_ip(ip):
    try:
        if not ip:
            logging.error("IP address is empty.")
            return False
        if ip.lower() == "localhost":
            return True
        socket.inet_pton(socket.AF_INET, ip)
        return True
    except (socket.error, ValueError):
        logging.error("Invalid IP address format or socket issues occurred.")
        return False

#validates port
def valid_port(port):
    try:
        port = int(port)
        if port < 1 or port > 65535:
            logging.error("Port Out of Range")
            return False
        return True
    except ValueError:
        logging.error("Port number is an invalid integer")
        return False

#checks inputs
def validate_input(input_args):
    type = input_args[0]
    file = input_args[1]
    if type.startswith("tcpclient"):
        if len(input_args) == 6:
            ip = input_args[2]
            port = input_args[3]
            window = int(input_args[4])
            ack_port = input_args[5]
            if os.path.exists(file):
                if valid_ip(ip) and valid_port(port):
                    if window > 0:
                        if valid_port(ack_port):
                            return True
                    else:
                        logging.error("Window can not be a 0 or negative number")
            else:
                logging.error(f"The file '{file_path}' does not exist.")
        else:
            logging.error("Wrong number of inputs")
        return False
    elif type.startswith("tcpserver"):
        if len(input_args) == 5:
            port = input_args[2]
            ip = input_args[3]
            ack_port = input_args[4]
            if file:
                if valid_ip(ip) and valid_port(port) and valid_port(ack_port):
                    return True
            else:
                logging.error("File input is empty")
        return False

#calculate checksum
def calculate_tcp_checksum(data):
    if len(data) % 2 != 0:
        data += b'\x00'
    total = 0
    for i in range(0, len(data), 2):
        word = struct.unpack('!H', data[i:i+2])[0]
        total += word
        if total > 0xFFFF:
            total = (total & 0xFFFF) + 1
    checksum = ~total & 0xFFFF
    return checksum

#create the packet
def create_packet(source_port, dest_port, SEQ, ACK_N, window, flags=0, data=b""):
    data_offset = 5
    urgent_pointer = 0
    data_offset_flags = (data_offset << 12) | flags
    # Calculate the TCP checksum
    if type(data) != bytes:
        data = data.encode()
    checksum_data = struct.pack('!HHLLHHH',
                                source_port,
                                dest_port,
                                SEQ,
                                ACK_N,
                                data_offset_flags,# Data Offset and Flags (16 bits)
                                window,           # Window (16 bits)
                                urgent_pointer    # Urgent Pointer (16 bits)
                                ) + data         # Include data in the checksum calculation

    checksum = calculate_tcp_checksum(checksum_data)

    # Update the checksum field in the TCP header
    tcp_header = struct.pack('!HHLLHHHH',
                             source_port,      # Source Port (16 bits)
                             dest_port,        # Destination Port (16 bits)
                             SEQ,              # Sequence Number (32 bits) - Use SEQ
                             ACK_N,              # Acknowledgment Number (32 bits) - Use ACK_N
                             data_offset_flags,# Data Offset and Flags (16 bits)
                             window,           # Window (16 bits)
                             checksum,         # Checksum (16 bits) - Updated with the calculated checksum
                             urgent_pointer    # Urgent Pointer (16 bits)
                             )

    # Create the packet with the updated checksum
    packet = tcp_header + data
    return packet

#open the packets
def parse_packet(packet):
    try:
        # Unpack the fixed-size TCP header fields
        source_port, dest_port, seq_num, ack_num, data_offset_flags, window, checksum, urgent_pointer = struct.unpack('!HHLLHHHH', packet[:20])
        # Extract the individual fields from data_offset_flags
        data_offset = (data_offset_flags >> 12) & 0xF
        flags = data_offset_flags & 0xFFF

        # Calculate data length
        data_length = len(packet) - (data_offset * 4)

        # Extract data
        data = packet[data_offset * 4:]

        # Calculate the checksum of the received packet
        packet_without_checksum = packet[:16] + b'\x00\x00' + packet[18:]  # Set checksum field to 0 for calculation
        received_checksum = checksum
        calculated_checksum = calculate_tcp_checksum(packet_without_checksum)

        # Verify the checksum
        is_checksum_valid = received_checksum == calculated_checksum

        # Interpret TCP flags
        flag_meanings = flags

        source_port = int(source_port)
        dest_port = int(dest_port)
        seq_num = int(seq_num)
        ack_num = int(ack_num)
        window = int(window)
        data_length = int(data_length)
        result = [
            is_checksum_valid,
            source_port,
            dest_port,
            seq_num,
            ack_num,
            data_offset,
            flag_meanings,
            window,
            data_length,
            data,
        ]
        return result
    except struct.error as e:
        return ["Error: " + str(e)]
