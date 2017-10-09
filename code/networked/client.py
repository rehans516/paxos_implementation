# -*- coding: utf-8 -*-
"""
Created on Thu Oct 05 11:13:18 2017

@author: Malumbo
"""
import time
from process import Process
from message import RequestMessage
from utils import Command

NUM_REQUESTS = 10

class Client(Process):
  def __init__(self, env, i, config, config_num):
    pid = "client %d.%d" % (config_num,i)
    Process.__init__(self, env, pid)
    self.config = config
    self.config_num = config_num
    self.env.addProc(self)
    
  def body(self):
    print "About to start: ", self.id
    for i in range(NUM_REQUESTS):
        for r in self.config.replicas:
            cmd = Command(self.id,0,"operation %d.%d" % (self.config_num,i))
            self.sendMessage(r,RequestMessage(self.id,cmd))
            time.sleep(1)
