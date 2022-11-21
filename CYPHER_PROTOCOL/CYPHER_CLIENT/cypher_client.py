import threading
import socket
import time
import sys
import json
import base64
from cryptography.fernet import Fernet

import gc as GC
import traceback

#$$$$$$$$$$#

class CYPHER_CLIENT() :
    def __init__(self, ip: str, port: int, encryption_key: str, decryption_key: str, responce_handler: object, offline_signal_processor: object = None, online_signal_processor: object = None) :

        #print("[*] INITIALISING CYPHER CLIENT")

        GC.set_threshold(0,0,0)
        GC.enable()

        self.IP = ip
        self.PORT = port

        self.RESPONCE_HANDLE_TRIGGER = responce_handler
        self.OFFLINE_SIGNAL_PROCESSOR = offline_signal_processor
        self.ONLINE_SIGNAL_PROCESSOR = online_signal_processor

        self.LOCK = threading.Lock()

        #print("[*] CREATING ENCRYPTION AND DECRYPTION OBJECTS")

        self.ENCRYPTION_KEY = encryption_key
        self.DECRYPTION_KEY = decryption_key
        self.ENCRYPTION_OBJECT = Fernet(base64.b64encode(self.ENCRYPTION_KEY.encode("ascii")))
        self.DECRYPTION_OBJECT = Fernet(base64.b64encode(self.DECRYPTION_KEY.encode("ascii")))

        #print("[*] CREATED ENCRYPTION AND DECRYPTION OBJECTS")

        self.CONNECTED = False
        self.CYPHER_STATUS = True

        #print("[*] INITIALISED CYPHER CLIENT")

    def connect(self) -> None :
        if self.CONNECTED == True :
            self.CONNECTION.close()
            del self.CONNECTION
        self.signalize_offline()

        self.CONNECTED = False

        #print("[*] TRYING TO CONNECT TO SERVER")

        while not self.CONNECTED :
            if self.CYPHER_STATUS :
                try :
                    self.CONNECTION = socket.socket()
                    self.CONNECTION.connect((self.IP, self.PORT))
                    self.CONNECTION.settimeout(60)
                    self.CONNECTED = True
                except Exception as EXCEPTION :

                    #print(EXCEPTION)

                    pass
            else :
                break
            time.sleep(1)

        GC.collect()
        GC.enable()

        self.signalize_online()

        if self.CONNECTED :

            #print("[*] CONNECTED TO SERVER")

            pass

    def make_request(self, path: str = "/", operation: str = "NONE", data: dict = {}, metadata: dict = {}) -> None :
        data_ = {}
        data_["PATH"] = path
        data_["OPERATION"] = operation
        data_["DATA"] = data
        data_["METADATA"] = metadata

        data_json = json.dumps(data_)
        data_encrypted = self.ENCRYPTION_OBJECT.encrypt(data_json.encode(encoding="ascii"))

        while self.CYPHER_STATUS :

            #print("[@] SENDING REQUEST")

            try :
                self.CONNECTION.send(bytes(data_encrypted.decode(encoding="ascii")+chr(0), "utf-8"))
            except :
                self.connect()
                continue

            #print("[@] REQUEST SENT")

            server_resp = [""]

            #print("[$] RECIEVING DATA FROM SERVER")

            error_occured_at_recieving = False

            while chr(0) not in server_resp[0] :
                try :
                    temp_resp = self.CONNECTION.recv(1024*1024).decode("utf-8")
                    if temp_resp != "" :
                        server_resp[0] += temp_resp
                    if temp_resp == "" :
                        error_occured_at_recieving = True
                        break
                except Exception as EXCEPTION :

                    #print(traceback.format_exc())

                    error_occured_at_recieving = True
                    break

            if error_occured_at_recieving :
                self.connect()
                continue

            #print("[$] RECIEVED DATA FROM SERVER")

            self.handle_responce(server_resp)

            break

    def handle_responce(self, server_resp: str) -> None :
        try :
            server_resp_decrypted = self.DECRYPTION_OBJECT.decrypt(server_resp[0].encode(encoding="ascii")[:-1])
        except Exception as EXCEPTION :
            return
        server_responce_json = json.loads(server_resp_decrypted.decode(encoding="ascii"))
        self.RESPONCE_HANDLE_TRIGGER(server_responce_json)

    def close_connection(self) -> None :

        #print("[~] CLOSING CONNECTION")

        self.CYPHER_STATUS = False
        self.CONNECTED = False
        self.CONNECTION.close()

        #print("[~] CONNECTION CLOSED")

    def signalize_offline(self) -> None :
        if self.CONNECTED == True :
            if self.OFFLINE_SIGNAL_PROCESSOR != None :
                self.OFFLINE_SIGNAL_PROCESSOR()

    def signalize_online(self) -> None :
        if self.CONNECTED == True :
            if self.ONLINE_SIGNAL_PROCESSOR != None :
                self.ONLINE_SIGNAL_PROCESSOR()
