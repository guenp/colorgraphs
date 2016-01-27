from .singleton import SingletonApp
import numpy as np

__author__ = 'Guen'

class GraphServer(SingletonApp):
    def __init__(self):
        SingletonApp.__init__(self)
        self.messages=[]
        self.memory = memoryview(self.shared_mem.data())

    def create_plot_from_message(self, name, message, data):
        '''
        Create a plot from data received from socket
        and add it to the dock
        '''
        params = data + message['name'] + message['labels']
        if len(data)==2:
            w = plot1d(*params)
        elif len(data) == 3:
            w = plot2d(*params)
        else:
            "Not a valid amount of data columns provided."

    def send_array(self, arr, message=None, meta=None):
        '''
        send an array (arr, numpy.array) to the server
        send a message (message, dict) with size and content info about the array
        '''
        # convert to bytearray and write to shared memory
        d = bytearray(arr)
        self.shared_mem.lock()
        mem = memoryview(self.shared_mem.data())
        mem[:len(d)] = d
        self.shared_mem.unlock()

        if not message:
            # create and send array message
            message = {}
            message['len'] = len(d)
        if meta:
            message['meta'] = meta
        self.send_message(message)

    def send_data(self, data, message):
        message['len'] = len(bytearray(data[0]))
        self.send_array(np.concatenate(data), message)

    def handle_new_message(self, message):
        '''
        Message contains metadata.
        When message received, read buffer and graph.
        '''
        logging.debug("Received: %s" %message)
        if (type(message)==dict) and ('len' in message.keys()):
            mem = memoryview(self.shared_mem.data())
            n=0; data = []
            for label in message['labels']:
                arr = np.frombuffer(mem[n:n+message['len']],'float')
                n+=message['len']
                data.append(arr)
            name = message.pop('name') if 'name' in message.keys() else 'Graph'
            self.received = name,message,data
            self.update()
        else:
            self.received = message

    def update(self):
        self.create_plot_from_message(*self.received)