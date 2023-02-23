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
    def __init__(self,
                 port: int,
                 encryption_key: str,
                 decryption_key: str,
                 request_handler: object,
                 host: str = "",
                 recv_buffer: int = 1024*1024*8,
                 transmission_buffer: int = 1024*1024*2,
                 timeout: int = 120,
                 debug1: bool = False,
                 debug2: bool = False) -> None :
        """
        port :                port at which the server will be open

        encryption_key :      key to encrypt responce that will be sent to client

        decryption_key :      key to decrypt request coming from client

        request_handler :     user defined function to handle request
                              takes 2 arguments, data: dictionary and ip_port: tuple; return dictionary

        host :                loopback interface [at what loopback interface
                              the service will be available] default value is ""

        recv_buffer :         bytes recieved in one recv() call;
                              max limit depends on system

        transmission_buffer : bytes transmitted/sent in one send()/sendall() call
                              max limit currently is 1024*1024*1 as limited by python

        timeout :             socket recv() timeout; if this occur
                              the server disconnects the client

        debug1 :              print level 1 debug statements; default is False

        debug2 :              print level 2 debug statements; default is False

        """

        self.HOST = host
        # DEBUG FLAGS
        self.DEBUG1 = debug1
        self.DEBUG2 = debug2
        # self.RECV_BUFFER IS LIMIT OF BYTES THAT CAN
        # BE RECIEVED IN ONE SINGLE connection.recv() CALL
        self.RECV_BUFFER = recv_buffer
        # self.TRANSMISSION_BUFFER IS LIMIT OF BYTES THAT CAN
        # BE TRANSMITTED IN ONE SINGLE connection.send() CALL
        #
        # CURRENTLY WE DON'T RECOMMEND
        # TO PUT THIS ABOVE 1024*1024*1 AS
        # THERE IS PACKET LOSS DUE TO BUG
        # IN PYTHON SOCKET LIBRARY ITSELF
        self.TRANSMISSION_BUFFER = transmission_buffer
        # SOCKET TIMEOUT LIMIT
        self.TIMEOUT = timeout

        self.print_debug("[*] INITIALISING SERVER", self.DEBUG1)

        # GARGACE COLLECTION SETTING
        GC.set_threshold(0,0,0)
        GC.enable()

        # SERVER IS HANDLING MANY THINGS IN PARALLEL
        # SO NEED A LOCK TO AVOID RACE CONDITIONS
        # WHILE ACCESSING self.CLIENTS AND
        # self.CLIENTS_TO_BE_DISCONNECTED
        self.LOCK = threading.Lock()
        # SERVER RUNS UNTIL SERVER FLAG IS TRUE
        self.SERVER_STATUS = True
        self.SERVER_PORT = port
        # self.CLIENTS CONTAINS ALL CLIENT_CONNECTION
        # OBJECTS IN FORMAT (IP, PORT) : CYPHER_CONNECTION OBJECT
        self.CLIENTS = {}
        # self.REQUEST_HANDLER IS REFERENCE FOR
        # CALLING USER DEFINED FUNCTION FOR
        # PROCESSING/HANDLING REQUEST
        #
        # USER DEFINES FUNCTION AND PROCESSES REQUEST ACCORDINGLY
        self.REQUEST_HANDLER = request_handler

        self.print_debug("[*] CREATING ENCRYPTION AND DECRYPTION OBJECTS", self.DEBUG1)

        self.ENCRYPTION_KEY = encryption_key
        self.DECRYPTION_KEY = decryption_key

        self.print_debug("[*] CREATED ENCRYPTION AND DECRYPTION OBJECTS", self.DEBUG1)

        # ONCE SOME ERROR IS ENCOUNTER OR TIMEOUT FACED
        # OR CLIENT CLOSED CONNECTION [PEER CLOSED CONNECTION]
        # THEN THEIR (IP, PORT) ARE PUT HERE THEN CLOSED AND DELETED BY THE THREAD
        self.CONNECTIONS_TO_BE_DISCONNECTED = []

        self.print_debug("[*] CREATING SERVER SOCKET", self.DEBUG1)

        # INITIALISING SOCKET
        self.SERVER_SOCKET = socket.socket()

        # TRYING TO PUT SOCKET IN REUSABLE STATE
        try :
            self.SERVER_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self.print_debug("[*] SOCKET IS IN REUSABLE STATE", self.DEBUG1)

        except : self.print_debug("[*] SOCKET IS NOT IN REUSABLE STATE", self.DEBUG1)

        self.print_debug("[*] CREATED SERVER SOCKET", self.DEBUG1)

        self.print_debug("[*] BINDING SERVER SOCKET TO IP AND PORT", self.DEBUG1)

        # TRY
        #     BIND SOCKET TO HOST[LOOPBACK INTERFACE]
        # EXCEPT EXCEPTION OCCUR
        #     PRINT TRACEBACK
        #     EXIT PROGRAM
        try :
            self.SERVER_SOCKET.bind((self.HOST, self.SERVER_PORT))

            self.print_debug("[*] BINDED SERVER SOCKET TO IP AND PORT", self.DEBUG1)
            self.print_debug("[*] SERVER OPEN ON PORT {0}".format(self.SERVER_PORT), self.DEBUG1)

        except Exception as EXCEPTION:
            self.print_debug(traceback.format_exc(), self.DEBUG2)
            sys.exit()

        # LISTENING TO 1000 SOCKETS AT A TIME
        # CAN KEEP 1000 SOCKETS IN BUFFER BEFORE REFUSING A NEW CONNECTION
        self.SERVER_SOCKET.listen(1000)
        # SERVER SOCKET TIMEOUT
        self.SERVER_SOCKET.settimeout(1)

        # CREATING THREADS FOR SERVER ONE IS MAINTHREAD WHICH ACCEPTS NEW CONNECTIONS
        # AND ONE IS CONNECTION CLOSING THREAD WHICH CLOSES CONNECTIONS AND
        # CLEAR MEMORY BY DELETING THEM FROM self.CONNECTIONS
        self.SERVER_MAIN_THREAD = threading.Thread(target=self.server_mainloop, args=())
        self.CONNECTION_CLOSING_THREAD = threading.Thread(target=self.connection_object_destruction_loop,
                                                          args=())

    def server_mainloop(self) -> None :

        self.print_debug("[*] INSIDE SERVER MAIN LOOP", self.DEBUG2)

        # WHILE self.SERVER_STATUS FLAG
        #     AQUIRE LOCK OVER self.CONNECTIONS
        #     TRY
        #         RECV NEW CONNECTION AND CALL
        #     EXCEPT EXCEPTION OCCUR
        #         PRINT DEBUG LEVEL 2
        #     RELEASE LOCK
        # IF SERVER_STATUS FLAG IS SET TO FALSE THE LOOP STOPS AND THE SERVER ALSO STOPS
        while self.SERVER_STATUS :
            self.LOCK.acquire()
            try : self.add_connection_object(self.SERVER_SOCKET.accept())
            except Exception as EXCEPTION :
                
                self.print_debug("[*] NO CONNECTION RECIEVED", self.DEBUG2)

            self.LOCK.release()

        self.SERVER_SOCKET.close()

    def add_connection_object(self,
                              sock_tuple: tuple) -> None :
        # RECIEVES (CONNECTION, (IP, PORT))
        # THAN CREATES CYPHER_CONNECTION OBJECT
        # IN self.CLIENTS BY PASSING sock_tuple
        # AND OTHER VALID PARAMETERS
        # self.CLIENTS[sock_tuple[1]]

        self.print_debug("[*] ADDING CONNECTION OBJECT", self.DEBUG2)

        self.CLIENTS[sock_tuple[1]] = CYPHER_CONNECTION(sock_tuple,
                                                        self.ENCRYPTION_KEY,
                                                        self.DECRYPTION_KEY,
                                                        self.REQUEST_HANDLER,
                                                        self,
                                                        self.RECV_BUFFER,
                                                        self.TRANSMISSION_BUFFER,
                                                        self.TIMEOUT,
                                                        self.DEBUG2)

    def connection_object_destruction_loop(self) -> None :
        # WHILE self.SERVER_STATUS OR self.CLIENTS NOT EMPTY
        #     WAIT 1
        #     FOR CLIENT IN self.CONNECTIONS_TO_BE_DISCONNECTED
        #         CALL self.destroy_connection_object TO DESTROY CONNECTION OBJECT
        while self.SERVER_STATUS or (self.CLIENTS != {}) :
            time.sleep(1)
            for _ in self.CONNECTIONS_TO_BE_DISCONNECTED :

                self.print_debug("[*] {0} IS TO BE DESTROYED".format(_), self.DEBUG2)

                self.destroy_connection_object(_)

            GC.collect()
            GC.enable()

    def destroy_connection_object(self,
                                  ip_port: tuple) -> None :
        # TRY
        #     CALL CONNECTION OBJECT'S del_attributes TO DELETE DATA MEMBERS OF CONNECTION OBJECT
        #     REMOVE CONNECTION ID FROM self.CONNECTIONS_TO_BE_DISCONNECTED
        # EXCEPT EXCEPTION OCCUR
        #     PASS
        try :
            self.CLIENTS[ip_port].del_attributes()
            del self.CLIENTS[ip_port]
            self.CONNECTIONS_TO_BE_DISCONNECTED.remove(ip_port)

            self.print_debug("[*] {0} HAS BEEN DESTROYED".format(ip_port), self.DEBUG2)

        except Exception as EXCEPTION :

            self.print_debug(traceback.format_exc(), self.DEBUG2)

            pass

    def start_server(self) -> None :
        """
        call it to start the server
        """
        # START THE self.SERVER_MAIN_THREAD AND self.CONNECTION_CLOSING_THREAD
        self.print_debug("[*] STARTING SERVER THREADS", self.DEBUG1)

        self.SERVER_MAIN_THREAD.start()
        self.CONNECTION_CLOSING_THREAD.start()

    def stop_server(self) -> None :
        """
        call it to stop the server
        """
        # STOP SERVER BY SETTING self.SERVER_STATUS FLAG TO FALSE
        self.SERVER_STATUS = False

    def add_connection_to_be_destroyed(self,
                                       ip_port: tuple) -> None :
        # CALLED BY CONNECTION_OBJECT TO REQUEST FOR CLOSING OF CONNECTION
        #
        # IF ip_port NOT IN self.CONNECTIONS_TO_BE_DISCONNECTED
        #     APPEND ip_port TO self.CONNECTIONS_TO_BE_DISCONNECTED
        if ip_port not in self.CONNECTIONS_TO_BE_DISCONNECTED :

            self.print_debug("[*] ADDED {0} TO BE DESTROYED".format(ip_port), self.DEBUG2)

            self.CONNECTIONS_TO_BE_DISCONNECTED.append(ip_port)

    def destroy_all_connections(self) -> None :
        """
        call it to destroy all active connections
        """
        # CALLING CONNECTION OBJECT'S close_connection
        # FOR ALL ACTIVE CONNECTIONS TO CLOSE THEM

        self.print_debug("[*] ADDING ALL CONNECTIONS TO BE DESTROYED", self.DEBUG2)

        for _ in self.CLIENTS :
            try : self.CLIENTS[_].close_connection()
            except : pass

    def print_debug(self,
                    debug: str,
                    debug_status: bool) -> None :
        if debug_status : print(debug)

#$$$$$$$$$$#

class CYPHER_CONNECTION() :
    def __init__(self,
                 connection: object,
                 encryption_key: str,
                 decryption_key: str,
                 request_handler: object,
                 server_object: object,
                 recv_buffer: int,
                 transmission_buffer: int,
                 timeout: int,
                 debug: bool = False) -> None :

        self.DEBUG = debug
        # SERVER REFERENCE FOR CALLING METHOD TO CLOSE CONNECTION
        self.SERVER_OBJECT = server_object
        # RECIEVED CONNECTION FOR CLIENT
        # THIS WILL BE USED TO EXCHANGE DATA
        self.CONNECTION = connection[0]
        # IP AND PORT OF CONNECTION
        self.IP_PORT = connection[1]

        # BUFFER SIZES FOR SENDING MESSAGES
        self.RECV_BUFFER = recv_buffer
        self.TRANSMISSION_BUFFER = transmission_buffer

        # self.CONNECTION_STATUS IS FLAG
        # TO KEEP CONNECTION ALIVE
        # IF THIS BECOMES FALSE THEN CONNECTION IS CLOSED
        # BY ADDING IP_OPRT TO SERVER'S CLIENTS_TO_BE_DISCONNECTED
        self.CONNECTION_STATUS = True

        self.print_debug("[#] INITIALISING CYPHER CONNECTION OBJECT FOR {0}".format(self.IP_PORT),
                         self.DEBUG)

        # CALLED WHEN RECIEVE A REQUEST
        # TAKES 2 ARGUMENTS, REQUEST AND RESPONCE
        self.REQUEST_HANDLE_TRIGGER = request_handler

        # CREATING FERNET OBJECTS TO ENCRYPT AND DECRYPT MESSAGES
        self.create_encryption_decryption_objects(encryption_key, decryption_key)

        # CONNECTION TIMEOUT, TIMEOUT OCCURS;
        # CONNECTION IS CLOSED BY ADDING IP_PORT
        # TO SERVER'S CLIENTS_TO_BE_DISCONNECTED
        self.CONNECTION.settimeout(timeout)

        # THERAD FOR RECIEVING REQUEST FROM CLIENT
        self.CONNECTION_THREAD = threading.Thread(target=self.connection_loop, args=())

        self.print_debug("[#] STARTING CONNECTION OBJECT THREAD FOR {0}".format(self.IP_PORT),
                         self.DEBUG)

        # START RECIEVING MESSAGES
        self.CONNECTION_THREAD.start()

    def create_encryption_decryption_objects(self,
                                             encryption_key: str,
                                             decryption_key: str) -> None :
        # CREATING DECRYPTION AND ENCRYPTION OBJECTS
        # TO ENCRYPT RESPONCE AND DECRYPT REQUEST

        self.print_debug("[#] CREATING ENCRYPTION AND DECRYPTION OBJECTS FOR {0}".format(self.IP_PORT),
                         self.DEBUG)

        self.ENCRYPTION_OBJECT = Fernet(base64.b64encode(encryption_key.encode("ascii")))
        self.DECRYPTION_OBJECT = Fernet(base64.b64encode(decryption_key.encode("ascii")))

        self.print_debug("[#] CREATED ENCRYPTION AND DECRYPTION OBJECTS FOR {0}".format(self.IP_PORT),
                         self.DEBUG)

    def connection_loop(self) -> None :

        self.print_debug("[#] CONNECTION LOOP", self.DEBUG)

        # STORAGE FOR SERVER RESPONCE
        # HERE IT IS LIST AS STRINGS ARE IMMUTABLE
        # BUT LIST ARE MUTABLE
        # WE CAN PASS LISTS AS REFERENCE
        client_resp = [""]

        # WHILE self.CONNECTION_RESPONCE
        #     TRY
        #         RECIEVE IN CHUNKS AS SPECIFIED BY USER
        #         CONCAT TO client_resp[0]
        #         IF CHR(0) IN client_resp[0]
        #             CALL self.process_request TO PROCESS REQUEST
        #         IF EMPTY RESPONCE
        #             BREAK TO CLOSE CONNECTION
        #     EXCEPT EXCEPTION OCCURS
        #         BREAK
        # CALL self.SERVER_OBJECT.add_connection_to_be_destroyed TO CLOSE CONNECTION
        while self.CONNECTION_STATUS :
            try :
                temp_resp = self.CONNECTION.recv(self.RECV_BUFFER).decode("utf-8")
                client_resp[0] += temp_resp
                if chr(0) in client_resp[0] :
                    self.process_request(client_resp)
                elif temp_resp == "" :
                    break
            except Exception as EXCEPTION :

                #print(traceback.format_exc())

                break
        self.SERVER_OBJECT.add_connection_to_be_destroyed(self.IP_PORT)

    def process_request(self,
                        client_resp: str) -> None :
        # DECRYPT REQUEST
        # CONVERT JSON TO PYTHONIC STRUCTURES
        # SET client_resp[0] TO ""
        # CALL self.REQUEST_HANDLE_TRIGGER TO PROCESS REQUEST
        # CONVERT DATA RETURNED BY self.REQUEST_HANDLER_TRIGGER TO JSON FORMAT AND THEN ENCRYPT IT
        # CONVERT TO BYTES AND SEND IN BUFFERS AS SPECIFIED BY USER

        self.print_debug("[#] PROCESSING REQUEST FOR {0}".format(self.IP_PORT),
                         self.DEBUG)

        client_resp_decrypted = self.DECRYPTION_OBJECT.decrypt(client_resp[0].encode(encoding="ascii")[:-1])
        client_responce_json = json.loads(client_resp_decrypted.decode(encoding="ascii"))
        client_resp[0] = ""

        self.print_debug("[#] CALLING REQUEST HANDLER FOR {0}".format(self.IP_PORT), self.DEBUG)

        responce_for_client = self.REQUEST_HANDLE_TRIGGER(client_responce_json, self.IP_PORT)
        responce_for_client_json = json.dumps(responce_for_client)
        responce_for_client_encrypted = self.ENCRYPTION_OBJECT.encrypt(responce_for_client_json.encode(encoding="ascii"))

        self.print_debug("[#] SENDING DATA TO CONNECTION {0}".format(self.IP_PORT), self.DEBUG)

        responce = bytes(responce_for_client_encrypted.decode("ascii")+chr(0), "utf-8")
        for _ in range(0, len(responce), self.TRANSMISSION_BUFFER) :
            self.CONNECTION.send(responce[_:_+self.TRANSMISSION_BUFFER])

        self.print_debug("[#] DATA SENT TO {0}".format(self.IP_PORT), self.DEBUG)

    def close_connection(self) -> None :
        self.CONNECTION_STATUS = False

    def del_attributes(self) -> None :
        # CLOSE CONNECTION SAFELY AND WAIT FOR CONNECTION THREAD TO COMPLETE
        # DELETE ALL DATA MEMBERS

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
        except Exception as EXCEPTION : print(EXCEPTION)
        try : del self.RECV_BUFFER
        except Exception as EXCEPTION : print(EXCEPTION)
        try : del self.TRANSMISSION_BUFFER
        except Exception as EXCEPTION : print(EXCEPTION)

    def print_debug(self,
                    debug: str,
                    debug_status: bool) -> None :
        if debug_status : print(debug)
