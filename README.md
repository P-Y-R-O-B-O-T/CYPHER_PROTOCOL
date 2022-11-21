# CYPHER_PROTOCOL

![](ZZZ/ZZZ.jpg)

* [PROJECT LINK GITHUB](https://github.com/P-Y-R-O-B-O-T/CYPHER_PROTOCOL)
* [PROJECT LINK PYPI](https://pypi.org/project/cypher-protocol-P-Y-R-O-B-O-T/)

* This is a type of communication protocol made for computers using TCP sockets.

* This is a highly secure and trust worthy protocol made using tcp sockets. It uses aggressively secure encryption AES-128 bit algorithm both the ways for a tight security

# ISSUES WITH OTHER PROTOCOLS

* Other protocols give errors when some error occurs and we have to handle it manually to remove it or to continue the process in the same sequence but CYPHER_PROTOCOL does that error handling automatically and the programmers are more free to focus on the flow instead of error handling.

* Whenever some error occurs in recieving data or sending data it resolves it automatically.

* Whenever it notices a disconnection from server it automatically re-connects to the server.

# COMPATIBLITY

* CYPHER_PROTOCOL works with Linux, OS-X, and Windows (OS INDEPENDENT).

* But it may give better experience on linux.

# INSTALLATION

> Install it using pip.

* Goto [PYPI](https://pypi.org/project/cypher-protocol-P-Y-R-O-B-O-T/1.0.6/)

# HOW TO USE ?

* Encryption key is a 32 character encryption key for the server and decryption key for client
* Decryption key is a 32 character decryption key for server and encryption key for the client
* Altough encryption and decryption key can be kept same for any reason
* request_processor in server initialisation is a method/function that user have to define and it is used to process the request recieved from client
* responce_processor in client initialisation is a method/function that user have to define and it is used to process the responce recieved from server

* Server's request handler recieves the request in the form :

```
{
"PATH": str,
"OPERATION": str,
"DATA": YOUR_DATA_HERE,
"METADATA": dict
}
```

* But it can also be modified as per needs

* "PATH" is like the path we see in http protocol and here it is "/" by default
* "OPERATION" is operation we have to perform like "UPDATE", "DELETE", "READ", "CREATE" etc. Also you can create your own type of operation if you want to, its just for convenience
* "DATA" contains data that you want to share between the server and the client
* "METADATA" contains data that you may need to use, its completely optional

## SERVER

```python
import time
import traceback
from CYPHER_PROTOCOL.CYPHER_SERVER.cypher_server import CYPHER_SERVER

SEQUENCE = []
NUMBER = 0

def request_processor(data: dict, ip_port: tuple) -> dict :
    global SEQUENCE
    global NUMBER
    print(data)

    if data["PATH"] == "/SEQUENCE" :
        if data["OPERATION"] == "UPDATE" :
            SEQUENCE.append(data["DATA"])
            if len(SEQUENCE) > 10 :
                SEQUENCE.pop(0)
            responce = {"PATH": data["PATH"], "OPERATION": data["OPERATION"], "METADATA": data["METADATA"]}
            responce["DATA"] = "UPDATED"
            return responce
        elif data["OPERATION"] == "READ" :
            responce = {"PATH": data["PATH"], "OPERATION": data["OPERATION"], "METADATA": data["METADATA"]}
            responce["DATA"] = SEQUENCE
            return responce
    elif data["PATH"] == "/NUMBER" :
        if data["OPERATION"] == "UPDATE" :
            NUMBER = data["DATA"]
            responce = {"PATH": data["PATH"], "OPERATION": data["OPERATION"], "METADATA": data["METADATA"]}
            responce["DATA"] = "UPDATED"
            return responce
        elif data["OPERATION"] == "READ" :
            responce = {"PATH": data["PATH"], "OPERATION": data["OPERATION"], "METADATA": data["METADATA"]}
            responce["DATA"] = NUMBER
            return responce

SERVER_OBJECT = CYPHER_SERVER(12345, "2ZpK1CdQfm0s1EZ1SIhYfV7MHdJf8X3U", "2ZpK1CdQfm0s1EZ1SIhYfV7MHdJf8X3U", request_processor)
SERVER_OBJECT.start_server()

time.sleep(60*5)

SERVER_OBJECT.stop_server()
```

## CLIENT

```python
import threading
import time
import random
from CYPHER_PROTOCOL.CYPHER_CLIENT.cypher_client import CYPHER_CLIENT

def responce_processor(responce: dict) :
    print(responce)

def request_maker() :
    global CLIENT_OBJECT
    while True :
        request = {"PATH": "/SEQUENCE", "OPERATION": "UPDATE", "DATA": random.randint(0,1000), "METADATA": {}}

        CLIENT_OBJECT.make_request(path = request["PATH"], operation = request["OPERATION"], data = request["DATA"], metadata = request["METADATA"])

        time.sleep(1)

        request = {"PATH": "/SEQUENCE", "OPERATION": "READ", "METADATA": {}}

        CLIENT_OBJECT.make_request(path = request["PATH"], operation = request["OPERATION"], metadata = request["METADATA"])

        #$$$$$$$$$$#

        request = {"PATH": "/NUMBER", "OPERATION": "UPDATE", "DATA": random.randint(0,1000), "METADATA": {}}

        CLIENT_OBJECT.make_request(path = request["PATH"], operation = request["OPERATION"], data = request["DATA"], metadata = request["METADATA"])

        time.sleep(1)

        request = {"PATH": "/NUMBER", "OPERATION": "READ", "METADATA": {}}

        CLIENT_OBJECT.make_request(path = request["PATH"], operation = request["OPERATION"], metadata = request["METADATA"])

CLIENT_OBJECT = CYPHER_CLIENT("127.0.0.1", 12345, "2ZpK1CdQfm0s1EZ1SIhYfV7MHdJf8X3U", "2ZpK1CdQfm0s1EZ1SIhYfV7MHdJf8X3U", responce_processor)

CLIENT_OBJECT.connect()

THREAD = threading.Thread(target=request_maker, args=())

THREAD.start()
```
