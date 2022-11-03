"""This module contains implementations of Connectors. The ZeroMQ connecter is
the one currently used by the Nebula Node.js server."""

import json
# import logging
import queue
# import zerorpc
# import zmq
import socketio
import asyncio

from . import pipeline


# class _ZeroRPC(object):
#     """Helper class for the ZeroRPCConnector."""
    
#     def __init__(self):
#         self._update = None
#         self._get = None
#         self._set = None
#         self._reset = None
    
#     def _set_callbacks(self, update=None, get=None, set=None, reset=None):
#         if update:
#             self._update = update
#         if get:
#             self._get = get
#         if set:
#             self._set = set
#         if reset:
#             self._reset = reset
            
#     def update(self, data):
#         if self._update:
#             return self._update(data)
    
#     def get(self, data):
#         if self._get:
#             return self._get(data)
        
#     def set(self, data):
#         if self._set:
#             return self._set(data)
        
#     def reset(self):
#         if self._reset:
#             return self._reset()
            
    
    
# class ZeroRPCConnector(pipeline.Connector):
#     """A zerorpc implementation of a connector. Not currently used by the
#     visualization controller anymore."""
    
#     def __init__(self, proto="tcp", host="*", port=5555):
#         self.obj = _ZeroRPC()
#         self.socket = zerorpc.Server(self.obj)
#         self.socket.bind("%s://%s:%d" % (proto, host, port))
        
#     def set_callbacks(self, **kwargs):
#         self.obj._set_callbacks(**kwargs)
        
#     def start(self):
#         self.socket.run()
        
        
        
# class ZeroMQConnector(pipeline.Connector):
#     """A connector implementation based just on ZeroMQ sockets. A pair socket
#     is created and listens for an incoming connection. Once the connection
#     is created, messages are sent in an RPC like fashion in the format:
    
#     {
#         "func": <function name>,
#         "contents": <function call arguments>,
#     }
    
#     """
    
#     def __init__(self, proto="tcp", host="*", port=5555):
#         print("New zmq connection")
#         self._update = None
#         self._get = None
#         self._set = None
#         self._reset = None
        
#         context = zmq.Context()
#         self._socket = context.socket(zmq.PAIR)
#         self._socket.bind("%s://%s:%d" % (proto, host, port))
#         self._push_queue = queue.Queue()
        
#     def set_callbacks(self, update=None, get=None, set=None, reset=None):
#         if update:
#             self._update = update
            
#         if get:
#             self._get = get
           
#         if set:
#             self._set = set
         
#         if reset:
#             self._reset = reset
        
#     def start(self):
#         while True:
#             # Check if we have any data to push
#             try:
#                 data = self._push_queue.get_nowait()
#                 self._socket.send_json({"func": "update", "contents": data})
#             except queue.Empty:
#                 pass
            
#             # Check if we have a new message
#             if self._socket.poll(timeout=200) == zmq.POLLIN:
#                 # We have a new request
#                 data = self._socket.recv_json()

#                 # Make sure the request has the right format
#                 if "func" not in data:
#                     raise TypeError("Malformed socket request, missing func")
                
#                 func = data["func"]
               
#                 funcs = {"update": self._update,
#                          "get": self._get,
#                          "set": self._set,
#                          "reset": self._reset}
                
#                 # Make sure the function they are calling is defined
#                 if func not in funcs:
#                     raise TypeError("%s function not defined in connector" % func)
                
#                 func_call = funcs[func]
             
#                 # Make sure the callback is set
#                 if not func_call:
#                     raise TypeError("%s callback not set" % func)
                
#                 if func == "reset":
#                     response = func_call()
#                 else:
#                     if "contents" not in data:
#                         raise TypeError("Malformed socket request, missing contents")
                    
#                     contents = data["contents"]
#                     response = func_call(contents)
                   
#                 data["contents"] = response
#                 self._socket.send_json(data)
            
#     def push_update(self, data):
#         self._push_queue.put(data)                
                

#This is the new connector utilizing Socket.io.  Functions similarly to the zeroMQ connector
class SocketIOConnector (pipeline.Connector):

    sio = socketio.AsyncClient()

    def __init__(self, port=5555):
        self._update = None
        self._get = None
        self._set = None
        self._reset = None

        self._push_queue = queue.Queue()

    async def makeConnection(self, port=5555):
        proto="tcp"

        host="://127.0.0.1:"

        url = proto+ host + str(port)
        await SocketIOConnector.sio.connect(url)
        
        SocketIOConnector.sio.on("msg", self.handle_message)
        # SocketIOConnector.sio.start_background_task(self.start)
        await SocketIOConnector.sio.wait()
    
    def set_callbacks(self, update=None, get=None, set=None, reset=None):
        if update:
            self._update = update
            
        if get:
            self._get = get
            
        if set:
            self._set = set
            
        if reset:
            self._reset = reset
            
    """
    async def start(self):
        # logging.debug("STARTING")
        while True:
            # Check if we have any data to push
            try:
                data = self._push_queue.get_nowait()
                await self.sio.send(data)
            except queue.Empty:
                pass
            await self.sio.sleep(0)
        
    ###           
    def push_update(self, data):
        self._push_queue.put(data)
        # logging.debug(f'pushing data')
    """
    
    async def handle_message(self, data): 
        # We have a new request
        
        # Make sure the request has the right format
        if "func" not in data:
            raise TypeError("Malformed socket request, missing func")
        
        func = data["func"]
        
        funcs = {"update": self._update,
                    "get": self._get,
                    "set": self._set,
                    "reset": self._reset}
        
        # Make sure the function they are calling is defined
        if func not in funcs:
            raise TypeError("%s function not defined in connector" % func)
        
        func_call = funcs[func]
        
        # Make sure the callback is set
        if not func_call:
            raise TypeError("%s callback not set" % func)
        
        if func == "reset":
            response = func_call()
            
        else:
            if "contents" not in data:
                raise TypeError("Malformed socket request, missing contents")
            
            contents = data["contents"]
            response = func_call(contents)
            
        data["contents"] = response
        await self.sio.send(data)
        # self.push_update(data)
                
    
    