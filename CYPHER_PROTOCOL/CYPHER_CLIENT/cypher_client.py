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
    def __init__(self,
                 ip: str,
                 port: int,
                 encryption_key: str,
                 decryption_key: str,
                 responce_handler: object,
                 offline_signal_processor: object = None,
                 online_signal_processor: object = None,
                 recv_buffer: int = 1024*1024*8,
                 transmission_buffer: int = 1024*1024*2,
                 timeout: int = 60) -> None :
        """
        ip :                       ipaddr of host to connect [ipv4 currently]

        port :                     port at which the host is serving or the service is available

        encryption_key :           key to encrypt request that will be sent to server

        decryption_key :           key to decrypt responce coming from server

        responce_handler :         user defined function to handle responce
                                   takes only one argument which is dictionary request_handler(responce: dict)

        offline_signal_processor : method which is called when client is offline
                                   takes no argument : offline_signal_processor()
                                   returns nothing

        online_signal_processor :  method which is called when client connects to server successfully
                                   takes no argument : online_signal_processor()
                                   returns nothing

        recv_buffer :              bytes recieved in one recv() call; max limit depends on system

        transmission_buffer :      bytes transmitted/sent in one send()/sendall() call
                                   max limit currently is 1024*1024*1 as limited by python

        timeout :                  socket recv() timeout; if this occur the client reconnects to server
        """

        GC.set_threshold(0,0,0)
        GC.enable()

        self.IP = ip
        self.PORT = port

        # self.RESPONCE_HANDLE_TRIGGER IS REFERENCE FOR
        # CALLING THE USER DEFINED FUNCTION WHICH IS
        # RESPONSIBLE FOR HANDLING DATA RECIEVED FROM SERVER
        #
        # USER DEFINES THIS FUNCTION AND PROCESSES DATA ACCORDINGLY
        self.RESPONCE_HANDLE_TRIGGER = responce_handler
        # self.OFFLINE_SIGNAL_PROCESSOR REFERENCE FOR
        # CALLING THE USER DEFINED FUNCTION WHICH IS
        # CALLED WHEN CLIENT FACES SOME CONNECTION ISSUE
        #
        # THIS SIGNALIZE USER THAT THERE IS SOME CONNECTION ISSUE
        # THEN THE USER CAN ACT ACCORDINGLY
        self.OFFLINE_SIGNAL_PROCESSOR = offline_signal_processor
        # self.ONLINE_SIGNAL_PROCESSOR IS REFERENCE FOR
        # CALLING USER DEFINED FUNCTION WHICH IS
        # CALLED WHEN CLIENT CONNECTS TO SERVER WITHOUT ANY PROBLEMS
        #
        # THIS SIGNNALIZE USER THAT IT HAS BEEN CONNECTED TO THE SERVER
        self.ONLINE_SIGNAL_PROCESSOR = online_signal_processor

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

        # LOCK FOR MULTITHREADED SUPPORT [CURRENTLY NOT AVAILABLE]
        self.LOCK = threading.Lock()

        # CREATING ENCRYPTION AND DECRYPTION OBJECTS THAT WILL
        # DECRYPT RESPONCES AND ENCRYPT REQUESTS
        self.ENCRYPTION_KEY = encryption_key
        self.DECRYPTION_KEY = decryption_key
        self.ENCRYPTION_OBJECT = Fernet(base64.b64encode(self.ENCRYPTION_KEY.encode("ascii")))
        self.DECRYPTION_OBJECT = Fernet(base64.b64encode(self.DECRYPTION_KEY.encode("ascii")))

        # self.CONNECTED IS CONNECTION STATUS FLAG
        # WHICH INDICATES WHEATHER IT IS CONNECTED OR NOT
        self.CONNECTED = False

        # self.CYPHER_STATUS IS FLAG WHICH INDICATES OUR WILL
        #
        # IF WE WANT TO BE CONNECTED TO THE SERVER THIS IS TRUE
        # ELSE IT IS SET TO FALSE WHILE WE CALL self.close_connection()
        #
        # THIS ALSO HELPS WHILE WE ARE TRYING TO RECONNECT TO SERVER AND
        # NOT BEING ABLE TO CONNECT [WE CAN STOP RECONNECTING WHEN USER CALLS self.close_connection()]
        self.CYPHER_STATUS = True

    def connect(self) -> None :
        """
        call it to connect to server

        this connects the client to server
        you do not need call it manually as
        while making a request if client is
        offline it automatically calls this
        """
        # IF CONNECTED IS TRUE MEANS
        # self.CONNECTION HAD EXISTED BEFORE
        # SO CLOSE IT ELSE DO NOTHING
        if self.CONNECTED == True :
            self.CONNECTION.close()
            del self.CONNECTION
        self.signalize_offline()

        # SETTING CONNECTION FLAG TO FALSE TO PERFORM RECONNECTION PROCESS
        self.CONNECTED = False

        # WHILE NOT CONNECTED
        #     IF WILL STATUS IS TRUE
        #         TRY CONNECT AND SET CONNECTION FLAG TRUE
        #         EXCEPT PASS IF EXCEPTION OCCUR
        #     ELSE BREAK
        #     SLEEP FOR 1 SEC FOR STABILITY AND NOT TO FLOOD SERVER
        while not self.CONNECTED :
            if self.CYPHER_STATUS :
                try :
                    self.CONNECTION = socket.socket()
                    self.CONNECTION.connect((self.IP, self.PORT))
                    self.CONNECTION.settimeout(self.TIMEOUT)
                    self.CONNECTED = True
                except Exception as EXCEPTION :
                    pass
            else : break
            time.sleep(1)

        # COLLECT GARBAGE
        GC.collect()
        GC.enable()

        if self.CONNECTED :
            self.signalize_online()

    def make_request(self,
                     path: str = "/",
                     operation: str = "NONE",
                     data: dict = {},
                     metadata: dict = {}) -> None :
        """
        path :      path of request at which the server will recieve request
                    default is "/"

        operation : type of operation to perform like CRUD, etc...
                    default is "NONE"

        data :      data to send to server
                    default is empty dictionary {}

        metadata :  metadata to exchange to/from server
                    default is empty dictionary {}
        """
        # _data WILL BE SENT TO SERVER SO ADDING DATA TO IT
        data_ = {}
        data_["PATH"] = path
        data_["OPERATION"] = operation
        data_["DATA"] = data
        data_["METADATA"] = metadata

        # CONVERTING _data TO JSON FORMAT AND ENCRYPTING IT
        data_json = json.dumps(data_)
        data_encrypted = self.ENCRYPTION_OBJECT.encrypt(data_json.encode(encoding="ascii"))

        # WHILE WILL FLAG TRY TO SEND REQUEST UNTIL IT IS SENT TO SERVER
        while self.CYPHER_STATUS :
            # TRY
            #     CONVERT DATA TO BYTES AND SEND TO SERVER IN CHUNKSIZES AS SPECIFIED BY USER
            # EXCEPT IF EXCEPTION OCCURS
            #     CALL self.connect() TO RE-CONNECT TO SERVER
            #     THEN CONTINUE TO MAKE REQUEST AGAIN
            try :
                request = bytes(data_encrypted.decode(encoding="ascii")+chr(0), "utf-8")
                for _ in range(0, len(request), self.TRANSMISSION_BUFFER) :
                    self.CONNECTION.send(request[_:_+self.TRANSMISSION_BUFFER])
            except :
                self.connect()
                continue

            # STORAGE FOR SERVER RESPONCE
            # HERE IT IS LIST AS STRINGS ARE IMMUTABLE
            # BUT LIST ARE MUTABLE
            # WE CAN PASS LISTS AS REFERENCE
            server_resp = [""]

            # FLAG REPRESENTING WHEATHE ERROR OCCURED WHILE RECIEVING RESPONCE
            error_occured_at_recieving = False

            # WHILE WE NOT RECIEVE THE DELIMITER FOR OUR REQUEST (chr(0))
            while chr(0) not in server_resp[0] :
                # TRY
                #     RECIEVING IN CHUNKS AS SPECIFIED BY USER
                #     IF NOT EMPTY RESPONCE
                #         CONCAT TO server_resp[0]
                #     IF EMPTY RESPONCE
                #         SET error_occured_at_recieving flag to True
                #         BREAK OUT OF LOOP
                # EXCEPT IF EXCEPTION OCCURS
                #     SET error_occured_at_recieving flag to True
                #     BREAK OUT OF LOOP
                try :
                    temp_resp = self.CONNECTION.recv(self.RECV_BUFFER).decode("utf-8")
                    if temp_resp != "" :
                        server_resp[0] += temp_resp
                    if temp_resp == "" :
                        error_occured_at_recieving = True
                        break
                except Exception as EXCEPTION :
                    error_occured_at_recieving = True
                    break
            # IF ERROR OCCURED AT RECIEVING THEN
            #     CALL self.connect() TO RE-CONNECT TO SERVER
            #     THEN CONTINUE TO MAKE REQUEST AGAIN
            if error_occured_at_recieving :
                self.connect()
                continue
            # IF RESPONCE RECIEVED PROPERLY
            #     CALL self.handle_responce
            #     BREAK OUT OF LOOP
            self.handle_responce(server_resp) 
            break

    def handle_responce(self,
                        server_resp: str) -> None :
        # TRY
        #     DECRYPT RESPONCE
        # EXCEPT EXCEPTION OCCURS
        #     RETURN
        # CONVERT JSON TO PYTHONIC DATA STRUCTURES
        # CALL self.RESPONCE_HANDLE_TRIGGER
        try :
            server_resp_decrypted = self.DECRYPTION_OBJECT.decrypt(server_resp[0].encode(encoding="ascii")[:-1])
        except Exception as EXCEPTION : return

        server_responce_json = json.loads(server_resp_decrypted.decode(encoding="ascii"))
        self.RESPONCE_HANDLE_TRIGGER(server_responce_json)

    def close_connection(self) -> None :
        # TO CLOSE CONNECTION ALL WE NEED
        # TO DO IS SET FLAGS TO FALSE AND
        # CALL self.CONNECTION.close()
        self.CYPHER_STATUS = False
        self.CONNECTED = False
        self.CONNECTION.close()

    def signalize_offline(self) -> None :
        # IF CONNECTED
        #     CALL self.OFFLINE_SIGNAL_PROCESSOR
        if self.CONNECTED == True :
            if self.OFFLINE_SIGNAL_PROCESSOR != None :
                self.OFFLINE_SIGNAL_PROCESSOR()

    def signalize_online(self) -> None :
        # IF CONNECTED
        #     CALL self.ONLINE_SIGNAL_PROCESSOR
        if self.CONNECTED == True :
            if self.ONLINE_SIGNAL_PROCESSOR != None :
                self.ONLINE_SIGNAL_PROCESSOR()
