# -*- coding: utf-8 -*-
"""
Created on Fri Oct 06 12:10:47 2017

@author: Malumbo

The directory keeps track of connected processes and provides a simple discovery mechanism.
When a new process starts, it registers itself with the directory and fetches connection info
about other processes of interest.

The connection info is contained in table procs as follows:
    procs = []

In any communication session with the directory, a process sends one of two commands:
    1. register[role] where role is one of 'client', 'replica', 'leader', 'scout', 'commander', 'acceptor'
    2. update[process_num, role]
    3. remove[process_num, role]
    
The directory responds as follows
    1. If the process' command was 'register' it generates a process number for process and inserts the process' 
       information into the table of processes. Then it returns the process number, a port number at which the process 
       must be reachable and connection data of all other processes of interest.
    2. If the command was 'update' the directory simply returns connection data of all other processes of interest.
    
The directory runs a serversocket on port 9001. On start-up each process must send a request to port 9001 from an ephemeral socket.

"""
import socket, json
from collections import namedtuple

class PaxosDirectory(object):
    def __init__(self):
        #now process ids are dot seperated numbers with left part representing process role and right part
        # representing the number of the process starting at 0. E.g. the second replica would have proc_num = 1.1
        # while the third client would have proc_num = 0.2. So we must keep track of how many of each role 
        # are registered.
        self.CLIENT = 0
        self.REPLICA = 1
        self.LEADER = 2
        self.ACCEPTOR = 3
        self.COMMANDER = 4
        self.SCOUT = 5
        
        self.num_clients = self.num_replicas = self.num_leaders = self.num_scouts = self.num_commanders = self.num_acceptors = 0
        
        # set up the process information table as a dictionary of namedtuples indexed by the process numbers.
        self.PaxosProcess = namedtuple('PaxosProcess', ['proc_num', 'port'])
        self.PaxosProcs = {self.CLIENT:[], self.REPLICA:[], self.LEADER:[], self.ACCEPTOR:[], self.COMMANDER:[], self.SCOUT:[]}
        
        # max port is the smallest legal port number not assigned so far. We always assign this to the next process and increment it.
        self.maxPort = 9002
        
        #bind the socket to localhost and a well-known port 9001
        self.host = 'localhost'  # can leave this blank on the server side
        self.port = 9001
        
        
    def start(self):
        #create an INET, STREAMing socket
        serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        serv_sock.bind((self.host, self.port))
        serv_sock.listen(5) # and listen for connections
        
        while (1):
            print "listening ... "
            cli_sock, addr = serv_sock.accept()
            print "recieved connection from {0}", addr 
            self.handle_connection(cli_sock)
    
    
    def handle_connection(self, in_sock):
        in_file = in_sock.makefile('r',0) # open the socket as a file object, read-only, unbuffered
        cli_data = json.load(in_file) #
#        json_str = ''
#        in_size = 1
#        
#        while in_size > 0:
#            in_data = in_sock.recv(1024)
#            json_str += in_data
#            in_size = len(in_data)
#            print in_data + ": " + str(in_size)
#            
#        print "json string", json_str
#        cli_data = json.loads(json_str) # 
        
        print "read the request into json object for the connection ...", cli_data

        role = int(cli_data['role'])
        
        if cli_data['command'] == 'register':
            role_count = self.get_role_count(role)
            proc_num = str(role) + '.' + str(role_count)
            port = self.maxPort
            # now add the stuff to the process table
            self.PaxosProcs[role].append(self.PaxosProcess(proc_num, port))
            # get the info that the requesting process needs
            conn_data = self.get_connection_data(role)
            conn_data['proc_num'] = proc_num
            conn_data['port'] = port
            conn_info = json.dumps(conn_data)
            
            self.maxPort += 1
            self.increment_role_count(role)
            
        elif cli_data['command'] == 'update':
            # if proc is not in the table tell it to register by returning an error
            proc_num = cli_data['proc_num']
            
            if self.is_registered(proc_num, role):
                conn_info = json.dumps(self.get_connection_data(role))
            else:
                conn_info = json.dumps({'error':'unregistered'})
                
        elif cli_data['command'] == 'remove':
            proc_num = cli_data['proc_num']
            if self.remove(proc_num, role):
                conn_info = json.dumps({'info':'removed'})
            else:
                conn_info = json.dumps({'error':'unregistered'})
        
        in_sock.sendall(conn_info)
        print "result dispatched..."
        in_file.close()
        in_sock.shutdown(socket.SHUT_RDWR)
        in_sock.close()
        
        
    def is_registered(self, proc, role):
        for p in self.PaxosProcs[role]:
            if p.proc_num == proc:
                return True
        
        return False
    
    
    def remove(self, proc, role):
        for p in self.PaxosProcs[role]:
            if p.proc_num == proc:
                self.PaxosProcs[role].remove(p)
                return True
        
        return False
    
    
    def get_connection_data(self, role):
        roles_to_fetch = [] # which roles does the requesting process need to know about
        conn_info = {'conn_info':{}}
        
        if role == self.CLIENT:
            roles_to_fetch = [self.REPLICA]
        elif role == self.REPLICA:
            roles_to_fetch = [self.LEADER]
        elif role == self.LEADER:
            roles_to_fetch = [self.REPLICA,self.COMMANDER,self.SCOUT,self.ACCEPTOR]
        elif role == self.ACCEPTOR:
            pass # acceptors need not know of any other processes they just wait info from leaders, commanders, scouts
        elif role == self.COMMANDER:
            roles_to_fetch = [self.REPLICA,self.ACCEPTOR]
        elif role == self.SCOUT:
            roles_to_fetch = [self.ACCEPTOR]
        else:
            return -1
        
        # get the connection data as dictionaries
        for r in roles_to_fetch:
            lst = self.PaxosProcs[r]
            if len(lst) > 0:
                conn_info['conn_info'][r] = lst
                
        return conn_info
    
        
    def get_role_count(self, role):
        if role == self.CLIENT:
            return self.num_clients
        elif role == self.REPLICA:
            return self.num_replicas
        elif role == self.LEADER:
            return self.num_leaders 
        elif role == self.ACCEPTOR:
            return self.num_acceptors
        elif role == self.COMMANDER:
            return self.num_commanders
        elif role == self.SCOUT:
            return self.num_scouts
        else:
            return -1
        
        
    def increment_role_count(self, role):
        if role == self.CLIENT:
            self.num_clients += 1
        elif role == self.REPLICA:
            self.num_replicas += 1
        elif role == self.LEADER:
            self.num_leaders += 1
        elif role == self.ACCEPTOR:
            self.num_acceptors += 1 
        elif role == self.COMMANDER:
            self.num_commanders += 1
        elif role == self.SCOUT:
            self.num_scouts += 1
            
def main():
  e = PaxosDirectory()
#  stacktracer.trace_start("trace.html")
  e.start()


if __name__=='__main__':
  main()
    
