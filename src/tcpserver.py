import logging
import socket
import select
import threading
import time
from helper import *

class server():
    def __init__(self,file, listening_port, address_for_acks, port_for_acks):
        #Input Based
        self.file = file
        self.lis_port = listening_port
        self.lis_addr = ("0.0.0.0", self.lis_port)
        self.send_ip = address_for_acks
        self.send_port = port_for_acks
        self.send_addr = (self.send_ip,self.send_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.lis_addr)
        #Packet Maintains
        self.seq_num=0
        self.ack_num = 0
        self.window = 0
        self.buffer = []
        self.received = []
        self.sended = []

    #collect packets, after, organize and write
    def run(self):
        #start listening
        rs = threading.Thread(target=self.recv_station, daemon=True )
        rs.start()
        if self.select_repeat():
            if self.list_to_file():
                pass
            else:
                logging.error(f"list to file was unsucessful")
        else:
            logging.error(f"Selective repeat was unsucessful")
    #take the list of packets
    def list_to_file(self):
        cont_data = []
        only_one = []
        already = []
        try:
            #checks for validity
            for i in self.received:
                if i[0]:
                    if i[6] == 0:
                        cont_data.append(i)
            #checks for doubles
            for i in cont_data:
                if i[3] in already:
                    pass
                else:
                    already.append(i[3])
                    result_list = i[3:4] + i[9:10]
                    only_one.append(result_list)
            #sort in order of seq_num
            sorted_array = sorted(only_one, key=lambda x: x[0])
            #writen into file after sorted
            with open(self.file, 'wb') as file:
                for i in sorted_array:
                    file.write(i[1])
            return True
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return False

    #recv packet, if checksum valid, append buffer(ack) & recieved(file)
    def recv_station(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(MSS)
                data_info = parse_packet(data)
                if data_info[0]:
                    self.received.append(data_info)
                    self.buffer.append(data)  # shift, tab to resend last ack, not ignore
            except socket.error as e:
                logging.error(f"Socket error: {e}")
            except Exception as e:
                logging.error(f"An error occurred: {e}")

    #Select repeat; of expecting ack
    def select_repeat(self):
        addr = self.send_addr
        length = 0
        last_ack= b''
        try:
            while True:
                if len(self.buffer) != length:
                    length = len(self.buffer)
                    for i in range(len(self.buffer)-1):
                        try:
                            packet = parse_packet(self.buffer[i])
                            #if allowing invalid packets, send last ack; line 66 adjustment
                            #else would be skipped
                            if not packet[0]:
                                self.sock.sendto(last_ack, addr)
                            #if not expected ack,dont update but send ack and save
                            elif packet[3]!=self.ack_num:
                                un_num = packet[3]+1
                                unord_ack = self.build_ordered_msg(un_num,"", ACK)
                                if packet[6] != FIN:
                                    self.sock.sendto(unord_ack, addr)
                            #if expected ack, update ack
                            elif packet[3] == self.ack_num:
                                self.buffer.pop(i)
                                #change ack to ack_num
                                self.ack_num = packet[3]+1
                                #if fin send fin back and leave
                                if packet[6] == FIN:
                                    msg = self.build_msg("", FIN)
                                    self.sock.sendto(msg, addr)
                                    return True
                                #if syn send ack syn
                                elif packet[6]== SYN:
                                    msg = self.build_msg("",(ACK and SYN))
                                    self.sock.sendto(msg, addr)
                                #if ack then pass
                                elif packet[6] ==  ACK:
                                    pass
                                #send an ack message
                                else:
                                    msg = self.build_msg("", ACK)
                                    last_ack=msg
                                    self.sock.sendto(last_ack, addr)
                        except IndexError:
                            # Handle index error when accessing buffer elements
                            logging.error("IndexError: Buffer index out of range")
                        except Exception as e:
                            logging.error(f"An error occurred: {e}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")
    #uses create_packet by inputing the already known variables.
    def build_msg(self,data="", flags=0):
        packet = create_packet(self.lis_port, self.send_port,
         self.seq_num, self.ack_num, self.window, flags, data)
        self.seq_num += 1
        return packet

    #create_packet inputing already known vars, out of order
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
