import os, signal, sys, time
from acceptor import Acceptor
from leader import Leader
from message import RequestMessage
from process import Process
from replica import Replica
from utils import *

NUM_ACCEPTORS = 3
NUM_REPLICAS = 2
NUM_LEADERS = 2
NUM_REQUESTS = 10
NUM_CONFIGS = 2

class Env:
  def __init__(self):
    self.procs = {}

  def sendMessage(self, dst, msg):
    if dst in self.procs:
      self.procs[dst].deliver(msg)

  def addProc(self, proc):
    self.procs[proc.id] = proc
    proc.start()

  def removeProc(self, pid):
    del self.procs[pid]

  def run(self):
    initialconfig = Config([], [], [])
    c = 0

    for i in range(NUM_REPLICAS):
      pid = "replica %d" % i
      Replica(self, pid, initialconfig)
      initialconfig.replicas.append(pid)
    for i in range(NUM_ACCEPTORS):
      pid = "acceptor %d.%d" % (c,i)
      Acceptor(self, pid)
      initialconfig.acceptors.append(pid)
    for i in range(NUM_LEADERS):
      pid = "leader %d.%d" % (c,i)
      Leader(self, pid, initialconfig)
      initialconfig.leaders.append(pid)
    for i in range(NUM_REQUESTS):
      pid = "client %d.%d" % (c,i)
      for r in initialconfig.replicas:
        cmd = Command(pid,0,"operation %d.%d" % (c,i))
        self.sendMessage(r,RequestMessage(pid,cmd))
        time.sleep(1)

    for c in range(1, NUM_CONFIGS):
      # Create new configuration
      config = Config(initialconfig.replicas, [], [])
      for i in range(NUM_ACCEPTORS):
        pid = "acceptor %d.%d" % (c,i)
        Acceptor(self, pid)
        config.acceptors.append(pid)
      for i in range(NUM_LEADERS):
        pid = "leader %d.%d" % (c,i)
        Leader(self, pid, config)
        config.leaders.append(pid)
      # Send reconfiguration request
      for r in config.replicas:
        pid = "master %d.%d" % (c,i)
        cmd = ReconfigCommand(pid,0,str(config))
        self.sendMessage(r, RequestMessage(pid, cmd))
        time.sleep(1)
      for i in range(WINDOW-1):
        pid = "master %d.%d" % (c,i)
        for r in config.replicas:
          cmd = Command(pid,0,"operation noop")
          self.sendMessage(r, RequestMessage(pid, cmd))
          time.sleep(1)
      for i in range(NUM_REQUESTS):
        pid = "client %d.%d" % (c,i)
        for r in config.replicas:
          cmd = Command(pid,0,"operation %d.%d"%(c,i))
          self.sendMessage(r, RequestMessage(pid, cmd))
          time.sleep(1)

  def terminate_handler(self, signal, frame):
    self._graceexit()

  def _graceexit(self, exitcode=0):
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(exitcode)

def main():
  e = Env()
  e.run()
  signal.signal(signal.SIGINT, e.terminate_handler)
  signal.signal(signal.SIGTERM, e.terminate_handler)
  signal.pause()


if __name__=='__main__':
  main()
