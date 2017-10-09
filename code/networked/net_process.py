# -*- coding: utf-8 -*-
"""
Created on Sat Oct 07 03:23:29 2017

@author: Malumbo
"""
import multiprocessing, socket, json
from threading import Thread
from paxos_sockets import p_sockets_serv, p_sockets_client

class Process(Thread):
    def __init__(self, role):
        super(Process, self).__init__()
        self.inbox = multiprocessing.Manager().Queue()
        
        # create a socket during initialization so to  fetch the connection info from the directory
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # connect to directory server - runs on port 9001
        self.dir_host = 'localhost'  # directory server address
        self.dir_port = 9001         # directory server port
        
        conn_str = json.dumps({'command':'register','role':role})
        print "to be sent: ", conn_str
        
        s.connect((self.dir_host, self.dir_port))
        s.sendall(conn_str)  # send test string
        print "sent the bloody string chars: "
        s.shutdown(socket.SHUT_WR)
        print "shutdown socket for writing now going into recieve part (should be a loop right)"
        
        
        in_file = s.makefile('r',0)     # open the socket as a file object, read-only, unbuffered
        conn_data = json.load(in_file)  # we expect a json string so load as dict object

        self.role = role
        self.port = int(conn_data['port'])      # now we can get our connection data from the returned dict starting with the port
        self.id = conn_data['proc_num']    # and process number for this process and then
        self.conn_info = conn_data['conn_info'] # the connection info for other processes I need to talk to.
        
        in_file.close()
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        
        self.in_serv = p_sockets_serv(self.port, self.id, self)
        self.in_serv.start()
        

    def run(self):
      try:
          # first upack the connection info before entering the body of the process
          print "started thread"
          self.body()
          print "exited body"
          self.remove()
      except EOFError:
          print "Exiting.."
          

    def getNextMessage(self):
        in_sock = self.inbox.get(block=True)
        msg = json.load(in_sock.makefile('r',0))
        return msg
        
    def sendMessage(self, dst_port, dst_proc, msg):
        p_sockets_client(json.dumps(msg), dst_port, dst_proc).start()
        
    def remove(self):
        p_sockets_client(json.dumps({'role':self.role, 'proc_num':self.id}), self.dir_port, '-1').start()

