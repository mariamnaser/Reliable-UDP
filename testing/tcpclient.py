import logging
import socket
import select
import threading
import time
import sys
from helper import *

class client():
    def __init__(self, file,proxy_ip,proxy_port, windowsize,ack_port):
        #Input Based
        self.file = file
        self.proxy_port = proxy_port
        self.proxy=(proxy_ip, proxy_port)
        self.window = windowsize
        self.lis_port = ack_port
        self.lis_addr = ("0.0.0.0", self.lis_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.lis_addr)
        #Weighting RTT
        self.rtt = 1
        self.alpha = 0.5
        #Packet Maintains
        self.seq_num=0
        self.ack_num=0
        self.buffer = []
        self.incoming_acks = []
        self.file_list = []

    #if file to list works, listen and start the sliding window
    def run(self):
        if self.file_to_list():
            rs = threading.Thread(target=self.listen_ack, daemon=True)
            rs.start()
            self.sliding_window()
        else:
            logging.error("Issue with File")

    def file_to_list(self):
        try:
            with open(self.file, 'rb') as file:
                while True:
                    data = file.read(MSS-20)
                    if not data:
                        return True
                    self.file_list.append(data)
        except FileNotFoundError as e:
            logging.error(f"Error: File '{self.file}' not found: {e}")
            return False
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return False

    #listens for ack; if checksum valid add to list, else log and ignore
    def listen_ack(self):
        while True:
            data, addr = self.sock.recvfrom(MSS)
            data_info = parse_packet(data)
            seq_num_acked = int(data_info[4])-1
            if data_info[0]:
                if seq_num_acked not in self.incoming_acks:
                    self.incoming_acks.append(seq_num_acked)
                    self.ack_num += 1
            else:
                logging.error(f"Checksum is Invalid for {data}")

    def sliding_window(self):
        #insure window size is reasonable, and adjust if not
        if self.window <= 0:
            logging.error("Window size =< 0")
            self.window = 3
        if self.window > len(self.file_list):
            logging.error("Window > #packets")
            self.window = min(len(self.file_list), len(self.file_list) // 2)
        #handshake
        hand = []
        hand.append([self.seq_num,self.build_msg("", SYN), time.time()])
        hand.append([self.seq_num,self.build_msg("", ACK), time.time()])
        for i in range(2):
            self.sock.sendto(hand[0][1], self.proxy)
            while hand[0][0] not in self.incoming_acks:
                self.sock.sendto(hand[0][1], self.proxy)
                time.sleep(self.rtt)
            if hand[0][0] in self.incoming_acks:
                hand.pop(0)

        #sending window
        #adds the window num of packets to buffer
        for pane in range(self.window):
            self.buffer.append([self.seq_num,self.build_msg(self.file_list[pane]), time.time()])
        #send out the inital packet
        for item in self.buffer:
            self.sock.sendto(item[1], self.proxy)
        #for every packet that hasn't been sent.
        for i in range(self.window, len(self.file_list)):
            pack_send = self.file_list[i]
            # check if buffer[0] has been acked
            #if buffer[0] not acked eval the checksum and resend if timed out
            while self.buffer[0][0] not in self.incoming_acks:
                if (time.time() - self.buffer[0][2])>= (2*(self.rtt)):
                    if self.buffer[0][2] <= -1:
                        self.buffer[0][2] = self.buffer[0][2] - 1
                        if self.buffer[0][2] < -100:
                            logging.warning(f"Packet {self.buffer[0][0]} has been sent 100 times.")
                    else:
                        self.buffer[0][2] = -1
                    self.sock.sendto(self.buffer[0][1],self.proxy)
                    time.sleep(self.rtt)
            #if it has within the rtt recalculate rtt pop(0), and amend another
            if self.buffer[0][0] in self.incoming_acks:
                if not (self.buffer[0][2] <=  -1):
                    sample = time.time() - self.buffer[0][2]
                    self.rtt= (1-self.alpha)*self.rtt+self.alpha*sample
                self.buffer.pop(0)
                msg = self.build_msg(pack_send)
                self.buffer.append([self.seq_num-1, msg, time.time()])
                self.sock.sendto(msg,self.proxy)
        #send FIN
        msg_fin = self.build_msg("", FIN)
        self.buffer.append([self.seq_num-1, msg_fin, time.time()])
        self.sock.sendto(msg_fin,self.proxy)
        #send any packets remaining in buffer till all the packets have been recieved
        while len(self.buffer)!=0:
            if self.buffer[0][0] in self.incoming_acks:
                self.buffer.pop(0)
            elif (time.time() - self.buffer[0][2])>= (self.rtt):
                if self.buffer[0][2] <= -1:
                    self.buffer[0][2] = self.buffer[0][2] - 1
                    time.sleep(self.rtt)
                    if self.buffer[0][2] < -100:
                        logging.warning(f"Packet {self.buffer[0][0]} has been sent 100 times.")
                else:
                        self.buffer[0][2] = -1
                self.sock.sendto(self.buffer[0][1],self.proxy)

    #uses create_packet by inputing the already known variables.
    def build_msg(self, data="", flags=0):
        packet = create_packet(self.lis_port, self.proxy_port,
         self.seq_num, self.ack_num, self.window, flags, data)
        self.seq_num += 1
        return packet

if __name__ == "__main__":
    input_args = sys.argv
    setup_logging("client_errors.txt")
    val_input = validate_input(input_args)
    if val_input:
        file = input_args[1]
        ip = input_args[2]
        port = int(input_args[3])
        window = int(input_args[4])
        ack_port = int(input_args[5])
        start_time = time.time()
        tcpclient = client(file, ip, port, window, ack_port)
        tcpclient.run()
        endtime = time.time() - start_time
        logging.warning(f"This toke {endtime}")
    else:
        logging.error("Inputs are not enought")
### For Basic Testing you can uncomment the following and comment out
# the if name block
"""
file = "faa.txt"
proxy_ip = "127.0.0.1"
proxy_port = 41192
windowsize = 2
ack_port = 6000
tcpclient = client(file,proxy_ip,proxy_port, windowsize,ack_port)
tcpclient.run()
"""
