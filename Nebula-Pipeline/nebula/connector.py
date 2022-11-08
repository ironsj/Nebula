import json
import queue
import socketio
import asyncio

from . import pipeline

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