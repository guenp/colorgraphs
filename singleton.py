#import std
import os, sys

# import stuff for ipc
import getpass, pickle

# Import Qt modules
from PyQt4 import QtGui
from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QSharedMemory, QIODevice, SIGNAL
from PyQt4.QtNetwork import QLocalServer, QLocalSocket

import logging

__author__ = 'Guen'

class SingletonApp(QApplication):
    '''
    Simple server based on QLocalServer, QLocalSocket, QSharedMemory
    that sends and receives messages and data with a socket connection and shared memory
    usage: python -m graphite.server
    '''
    timeout = 1000
    running_apps = []
    def __init__(self, argv=sys.argv, application_id=None, size=2**24):
        QApplication.__init__(self, argv)
        self.socket_filename = os.path.expanduser(os.path.join(os.getcwd(),'.ipc_%s' % self.generate_ipc_id()))
        self.shared_mem = QSharedMemory()
        self.shared_mem.setKey(self.socket_filename)

        if self.shared_mem.attach():
            self.is_running = True
            return

        self.is_running = False
        if not self.shared_mem.create(size):
            print >>sys.stderr, "Unable to create single instance"
            return
        # start local server
        self.server = QLocalServer(self)
        # connect signal for incoming connections
        self.connect(self.server, SIGNAL("newConnection()"), self.receive_message)
        # if socket file exists, delete it
        if os.path.exists(self.socket_filename):
            os.remove(self.socket_filename)
        # listen
        self.server.listen(self.socket_filename)
        SingletonApp.running_apps.append(self)

    def __del__(self):
        logging.debug('Detaching shared memory and closing socket connection.')
        self.shared_mem.detach()
        if not self.is_running:
            if os.path.exists(self.socket_filename):
                os.remove(self.socket_filename)

    def generate_ipc_id(self, channel=None):
        if channel:
            return '%s_%s' %(channel,getpass.get_user())
        else:
            return getpass.getuser()

    def send_message(self, message):
        if not self.is_running:
            raise Exception("Client cannot connect to IPC server. Not running.")
        socket = QLocalSocket(self)
        socket.connectToServer(self.socket_filename, QIODevice.WriteOnly)
        if not socket.waitForConnected(self.timeout):
            self.__del__()
            if not socket.waitForConnected(self.timeout):
                raise Exception(str(socket.errorString()))
        socket.write(pickle.dumps(message))
        if not socket.waitForBytesWritten(self.timeout):
            raise Exception(str(socket.errorString()))
        socket.disconnectFromServer()

    def receive_message(self):
        socket = self.server.nextPendingConnection()
        if not socket.waitForReadyRead(self.timeout):
            print >>sys.stderr, socket.errorString()
            return
        byte_array = socket.readAll()
        self.handle_new_message(pickle.loads(byte_array))

    def handle_new_message(self, message):
        logging.debug("Received: %s" %message)

# Create a class for our main window
class Main(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

def main():
    app = SingletonApp()
    if app.is_running:
    # send arguments to running instance
        app.send_message(*sys.argv)
    else: 
        MyApp = Main()
        MyApp.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()