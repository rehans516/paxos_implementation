import multiprocessing
from threading import Thread
import threading
import time
import SocketServer


class Process(Thread):
  def __init__(self, env, id):
    super(Process, self).__init__()
    self.inbox = multiprocessing.Manager().Queue()
    self.env = env
    self.id = id

  def run(self):
    try:
      self.body()
      self.env.removeProc(self.id)
    except EOFError:
      print "Exiting.."

  def getNextMessage(self):
    return self.inbox.get()

  def sendMessage(self, dst, msg):
    self.env.sendMessage(dst, msg)

  def deliver(self, msg):
    self.inbox.put(msg)

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        self.data = self.request.recv(1024).strip()
        print "%s wrote: " % self.client_address[0]
        print self.data
        self.request.send(self.data.upper())

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

if __name__ == "__main__":

    HOST = ''
    PORT_A = 9999
    PORT_B = 9876

    server_A = ThreadedTCPServer((HOST, PORT_A), ThreadedTCPRequestHandler)
    server_B = ThreadedTCPServer((HOST, PORT_B), ThreadedTCPRequestHandler)

    server_A_thread = threading.Thread(target=server_A.serve_forever)
    server_B_thread = threading.Thread(target=server_B.serve_forever)

    server_A_thread.setDaemon(True)
    server_B_thread.setDaemon(True)

    server_A_thread.start()
    server_B_thread.start()

    while 1:
        time.sleep(1)