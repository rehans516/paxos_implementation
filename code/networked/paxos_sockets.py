# -*- coding: utf-8 -*-
"""
Created on Fri Oct 06 23:04:26 2017

@author: Malumbo
"""
import socket
from threading import Thread

class p_sockets_client(Thread):
    def __init__(self, msg, dst_host, dst_port, dst_proc):
        super(p_sockets_client, self).__init__()
        self.msg, self.dst_host, self.dst_port, self.dst_proc = msg, dst_host, dst_port, dst_proc
        
    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # connect to server
        sock.connect((self.dst_host, self.dst_port))
        
        try:
            sock.sendall(self.msg)  # send the msg
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
        except:
            print "%s :connection closed abruptly", self.dst_proc


class p_sockets_serv(Thread):
    def __init__(self, port, proc_num, proc):
        super(p_sockets_serv, self).__init__()
        self.port, self.proc_num = port, proc_num
        self.proc, self.host = proc, 'localhost'
        self.keep_alive = True
        
    def run(self):
        serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        serv_sock.bind((self.host, self.port))
        serv_sock.listen(5) # and listen for connections
        
        while (self.keep_alive):
            cli_sock, addr = serv_sock.accept()
            self.proc.inbox.put(cli_sock,block=True)

    def shutdown(self):
        self.keep_alive = False;