import logging
import socket
import select
import threading
import time
from helper import *

MSS = 500
class server():
    def __init__(self,file, listening_port, address_for_acks, port_for_acks):
        #based on input
        self.file = file
        self.lis_port = listening_port
        self.lis_addr = ("0.0.0.0", self.lis_port)
        self.send_ip = address_for_acks
        self.send_port = port_for_acks
        self.send_addr = (self.send_ip,self.send_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.lis_addr)
        #Needed Variables
        self.seq_num=0
        self.ack_num = 0
        self.window = 5
        self.buffer = []
        self.received = []
        self.sended = []
        self.con_comp = False
    def run(self):
        #self.handshake()
        rs = threading.Thread(target=self.recv_station, daemon=True )
        rs.start()
        if self.select_repeat():
            if self.list_to_file():
                print("DONE")
    def list_to_file(self):
        cont_data = []
        only_one = []
        already = []
        for i in self.received:
            if i[0]:
                if i[6] == 0:
                    cont_data.append(i)
        for i in cont_data:
            if i[3] in already:
                pass
            else:
                already.append(i[3])
                result_list = i[3:4] + i[9:10]
                only_one.append(result_list)
        sorted_array = sorted(only_one, key=lambda x: x[0])
        # Assuming self.file contains the file path
        with open(self.file, 'wb') as file:
            for i in sorted_array:
                file.write(i[1])

    def recv_station(self):
        while not self.con_comp:
            data, addr = self.sock.recvfrom(MSS)
            data_info = parse_packet(data)
            if data_info[0]:
                self.buffer.append(data)
                self.received.append(data_info)
    def select_repeat(self):
        #new incoming
        addr = self.send_addr
        length = 0
        last_ack= b''
        while not self.con_comp:
            if len(self.buffer) != length:
                length = len(self.buffer)
                for i in range(len(self.buffer)-1):
                    packet = parse_packet(self.buffer[i])
                    if not packet[0]:
                        self.sock.sendto(last_ack, addr)
                    #if not what expected ack but don't unpdate ack num
                    elif packet[3]!=self.ack_num:
                        un_num = packet[3]+1
                        unord_ack = self.build_ordered_msg(un_num,"", ACK)
                        if packet[6] != FIN:
                            self.sock.sendto(unord_ack, addr)
                    #if expected ack, update ack
                    elif packet[3] == self.ack_num:
                        self.buffer.pop(i)
                        #Valid and = to ack_num
                        self.ack_num = packet[3]+1
                        #if it is right but fin is not
                        if packet[6] == FIN:
                            msg = self.build_msg("", FIN)
                            self.sock.sendto(msg, addr)
                            return True
                        elif packet[6]== SYN:
                            msg = self.build_msg("",(ACK and SYN))
                            self.sock.sendto(msg, addr)
                        elif packet[6] ==  ACK:
                            pass
                        else:
                            msg = self.build_msg("", ACK)
                            last_ack=msg
                            self.sock.sendto(last_ack, addr)

    def build_msg(self,data="", flags=0):
        packet = create_packet(self.lis_port, self.send_port,
         self.seq_num, self.ack_num, self.window, flags, data)
        self.seq_num += 1
        return packet
    def build_ordered_msg(self,num, data="", flags=0):
        packet = create_packet(self.lis_port, self.send_port,
         self.seq_num, num, self.window, flags, data)
        self.seq_num += 1
        return packet



if __name__ == "__main__":
    input_args = sys.argv
    setup_logging(f"server_errors.txt")
    val_input = validate_input(input_args)
    if val_input:
        file = input_args[1]
        port = int(input_args[2])
        ip = input_args[3]
        ack_port = int(input_args[4])
        start_time = time.time()
        tcpserver = server(file, port, ip, ack_port)
        tcpserver.run()
        endtime = time.time() - start_time
        logging.warning(f"This toke {endtime}; client login time unknown")
    else:
        logging.error("Input Error")

####################################################################
### For Basic Testing you can uncomment the following and comment out
# the if name block
#Run the proxy like so for this testing
#./newudpl -i localhost:6000 -o localhost:5050
"""
setup_logging("server_Log.txt")
file = "file.txt"
listening_port = 5050
address_for_acks = "127.0.0.1"
port_for_acks = 6000

tcpserver = server(file, listening_port, address_for_acks, port_for_acks)
tcpserver.run()
"""
