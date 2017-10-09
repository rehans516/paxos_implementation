# -*- coding: utf-8 -*-
"""
Created on Sat Oct 07 03:23:29 2017

@author: Malumbo
"""
import multiprocessing, socket, json
from threading import Thread
from paxos_sockets import p_sockets_serv, p_sockets_client
from net_process import Process

NUM_REQUESTS = 10

class Client(Process):
  def __init__(self, role):
    print "About to start: New process"
    Process.__init__(self, role)
    print "Started, process_id: ", self.id
    
  def body(self):
    print "Entered main loop"
    print "port: ", self.port
    print "conn_info: ", self.conn_info

