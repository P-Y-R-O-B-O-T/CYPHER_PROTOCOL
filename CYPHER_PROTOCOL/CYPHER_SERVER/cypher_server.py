import threading
import socket
import time
import sys
import json
import base64
from cryptography.fernet import Fernet

import gc as GC
import traceback

import tracemalloc

#$$$$$$$$$$#

class CYPHER_SERVER() :
    def __init__(self, port: int, encryption_key: str, decryption_key: str, request_handler: object, debug1: bool = False, debug2: bool = False) :

        self.DEBUG1 = debug1
        self.DEBUG2 = debug2

        self.print_debug("[*] INITIALISING SERVER", self.DEBUG1)

        GC.set_threshold(0,0,0)
        GC.enable()

        self.LOCK = threading.Lock()
        self.SERVER_STATUS = True
        self.SERVER_PORT = port
        self.CLIENTS = {}

        self.REQUEST_HANDLER = request_handler

        self.self.print_debug("[*] CREATING ENCRYPTION AND DECRYPTION OBJECTS", self.DEBUG1)

        self.ENCRYPTION_KEY = encryption_key
        self.DECRYPTION_KEY = decryption_key
        self.ENCRYPTION_OBJECT = Fernet(base64.b64encode(self.ENCRYPTION_KEY.encode("ascii")))
        self.DECRYPTION_OBJECT = Fernet(base64.b64encode(self.DECRYPTION_KEY.encode("ascii")))

        self.print_debug("[*] CREATED ENCRYPTION AND DECRYPTION OBJECTS", self.DEBUG1)

        self.CONNECTIONS_TO_BE_DISCONNECTED = []

        self.print_debug("[*] CREATING SERVER SOCKET", self.DEBUG1)

        self.SERVER_SOCKET = socket.socket()

        self.print_debug("[*] CREATED SERVER SOCKET", self.DEBUG1)

        self.print_debug("[*] BINDING SERVER SOCKET TO IP AND PORT", self.DEBUG1)

        try :
            self.SERVER_SOCKET.bind(("", self.SERVER_PORT))

            self.print_debug("[*] BINDED SERVER SOCKET TO IP AND PORT", self.DEBUG1)
            self.print_debug("[*] SERVER OPEN ON PORT {0}".format(self.PORT), self.DEBUG1)

        except Exception as EXCEPTION:

            print(traceback.format_exc())

            sys.exit()

        self.SERVER_SOCKET.listen(100)
        self.SERVER_SOCKET.settimeout(1)

        self.SERVER_MAIN_THREAD = threading.Thread(target = self.server_mainloop , args = ())
        self.CONNECTION_CLOSING_THREAD = threading.Thread(target = self.connection_object_destruction_loop ,args = ())

    def server_mainloop(self) -> None :

        self.print_debug("[*] INSIDE SERVER MAIN LOOP", self.DEBUG2)

        while self.SERVER_STATUS :
            self.LOCK.acquire()
            try :
                self.add_connection_object(self.SERVER_SOCKET.accept())
            except Exception as EXCEPTION :
                
                self.print_debug("[*] NO CONNECTION RECIEVED", self.DEBUG2)

            self.LOCK.release()

        self.SERVER_SOCKET.close()

    def add_connection_object(self, sock_tuple: tuple) -> None :

        self.print_debug("[*] ADDING CONNECTION OBJECT", self.DEBUG2)

        self.CLIENTS[sock_tuple[1]] = CYPHER_CONNECTION(sock_tuple, self.ENCRYPTION_KEY, self.DECRYPTION_KEY, self.REQUEST_HANDLER, self, self.DEBUG2)

    def connection_object_destruction_loop(self) -> None :
        while self.SERVER_STATUS or (self.CLIENTS != {}) :
            time.sleep(1)
            for _ in self.CONNECTIONS_TO_BE_DISCONNECTED :

                self.print_debug("[*] {0} IS TO BE DESTROYED".format(_), self.DEBUG2)

                self.destroy_connection_object(_)

            GC.collect()
            GC.enable()

    def destroy_connection_object(self, ip_port: tuple) -> None :
        try :
            self.CLIENTS[ip_port].del_attributes()
            del self.CLIENTS[ip_port]
            self.CONNECTIONS_TO_BE_DISCONNECTED.remove(ip_port)

            self.print_debug("[*] {0} HAS BEEN DESTROYED".format(ip_port), self.DEBUG2)

        except Exception as EXCEPTION :

            #print(traceback.format_exc())

            pass

    def start_server(self) -> None :

        self.print_debug("[*] STARTING SERVER THREADS", self.DEBUG1)

        self.SERVER_MAIN_THREAD.start()
        self.CONNECTION_CLOSING_THREAD.start()

    def stop_server(self) -> None :
        self.SERVER_STATUS = False

    def add_connection_to_be_destroyed(self, ip_port: tuple) -> None :
        if ip_port not in self.CONNECTIONS_TO_BE_DISCONNECTED :

            self.print_debug("[*] ADDED {0} TO BE DESTROYED".format(ip_port), self.DEBUG2)

            self.CONNECTIONS_TO_BE_DISCONNECTED.append(ip_port)

    def destroy_all_connections(self) -> None :

        self.print_debug("[*] ADDING ALL CONNECTIONS TO BE DESTROYED", self.DEBUG2)

        for _ in self.CLIENTS :
            try :
                self.CLIENTS[_].close_connection()
            except :
                pass

    def print_debug(debug, debug_status) :
        if debug_status :
            print(debug)

#$$$$$$$$$$#

class CYPHER_CONNECTION() :
    def __init__(self, connection: object, encryption_key: str, decryption_key: str, request_handler: object, server_object: object, debug: bool = False) :
        self.DEBUG = debug
        self.SERVER_OBJECT = server_object
        self.CONNECTION = connection[0]
        self.IP_PORT = connection[1]

        self.CONNECTION_STATUS = True

        self.print_debug("[#] INITIALISING CYPHER CONNECTION OBJECT FOR {0}".format(self.IP_PORT), self.DEBUG)

        self.REQUEST_HANDLE_TRIGGER = request_handler

        self.create_encryption_decryption_objects(encryption_key, decryption_key)

        self.CONNECTION.settimeout(60)

        self.CONNECTION_THREAD = threading.Thread(target=self.connection_loop, args=())

        self.print_debug("[#] STARTING CONNECTION OBJECT THREAD FOR {0}".format(self.IP_PORT), self.DEBUG)

        self.CONNECTION_THREAD.start()

    def create_encryption_decryption_objects(self, encryption_key: str, decryption_key: str) -> None :

        self.print_debug("[#] CREATING ENCRYPTION AND DECRYPTION OBJECTS FOR {0}".format(self.IP_PORT), self.DEBUG)

        self.ENCRYPTION_OBJECT = Fernet(base64.b64encode(encryption_key.encode("ascii")))
        self.DECRYPTION_OBJECT = Fernet(base64.b64encode(decryption_key.encode("ascii")))

        self.print_debug("[#] CREATED ENCRYPTION AND DECRYPTION OBJECTS FOR {0}".format(self.IP_PORT), self.DEBUG)

    def connection_loop(self) -> None :

        self.print_debug("[#] CONNECTION LOOP", self.DEBUG)

        client_resp = [""]
        while self.CONNECTION_STATUS :
            try :
                temp_resp = self.CONNECTION.recv(1024*1024).decode("utf-8")
                client_resp[0] += temp_resp
                if chr(0) in client_resp[0] :
                    self.process_request(client_resp)
                elif temp_resp == "" :
                    break
            except Exception as EXCEPTION :

                #print(traceback.format_exc())

                break
        self.SERVER_OBJECT.add_connection_to_be_destroyed(self.IP_PORT)

    def process_request(self, client_resp: str) -> None :

        self.print_debug("[#] PROCESSING REQUEST FOR {0}".format(self.IP_PORT), self.DEBUG)

        client_resp_decrypted = self.DECRYPTION_OBJECT.decrypt(client_resp[0].encode(encoding="ascii")[:-1])
        client_responce_json = json.loads(client_resp_decrypted.decode(encoding="ascii"))
        client_resp[0] = ""

        self.print_debug("[#] CALLING REQUEST HANDLER FOR {0}".format(self.IP_PORT), self.DEBUG)

        responce_for_client = self.REQUEST_HANDLE_TRIGGER(client_responce_json, self.IP_PORT)
        responce_for_client_json = json.dumps(responce_for_client)
        responce_for_client_encrypted = self.ENCRYPTION_OBJECT.encrypt(responce_for_client_json.encode(encoding="ascii"))

        self.print_debug("[#] SENDING DATA TO CONNECTION {0}".format(self.IP_PORT), self.DEBUG)

        self.CONNECTION.send(bytes(responce_for_client_encrypted.decode("ascii")+chr(0), "utf-8"))

        self.print_debug("[#] DATA SENT TO {0}".format(self.IP_PORT), self.DEBUG)

    def close_connection(self) -> None :
        self.CONNECTION_STATUS = False

    def del_attributes(self) -> None :

        self.print_debug("[#] DELETING ATTRIBUTES OF {0}".format(self.IP_PORT), self.DEBUG)

        self.CONNECTION.close()
        self.CONNECTION_THREAD.join()

        try : del self.CONNECTION_STATUS
        except Exception as EXCEPTION : print(EXCEPTION)
        try : del self.CONNECTION
        except Exception as EXCEPTION : print(EXCEPTION)
        try : del self.IP_PORT
        except Exception as EXCEPTION : print(EXCEPTION)
        try : del self.CONNECTION_THREAD
        except Exception as EXCEPTION : print(EXCEPTION)
        try : del self.ENCRYPTION_OBJECT
        except Exception as EXCEPTION : print(EXCEPTION)
        try : del self.DECRYPTION_OBJECT
        except Exception as EXCEPTION : print(EXCEPTION)
        try : del self.SERVER_OBJECT
        except Exception as EXCEPTION : print(EXCEPTION)
        try : del self.REQUEST_HANDLE_TRIGGER
        except Exception as EXCEPRION : print(EXCEPTION)

    def print_debug(debug, debug_status) :
        if debug_status :
            print(debug)
