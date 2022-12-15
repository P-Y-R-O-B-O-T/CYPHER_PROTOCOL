from ..cypher_server import CYPHER_SERVER
import os
import threading
import sys

#$$$$$$$$$$#

class FTP_SERVER(CYPHER_SERVER) :
    def __init__(self, path: str,
                 recv_chunk_size: int = 1024*1024*1,
                 transmission_chunk_size: int = 1024*1024*1,
                 **init_data) -> None :

        super().__init__(request_handler=self.file_data, **init_data)

        self.RECV_CHUNK_SIZE = recv_chunk_size
        self.TRANSMISSION_CHUNK_SIZE = transmission_chunk_size

        self.PATH = path

        #while True :
        #    if self.PATH[-1] == "/" : self.PATH = self.PATH[:-1]
        #    else : break
            
        if not os.path.isdir(self.PATH) :
            try : os.makedirs(self.PATH)
            except Exception as EXCEPTION :
                print(EXCEPTION)
                sys.exit()

    def file_data(self,
                  request: dict,
                  ip_port: tuple) -> dict :
        responce = {"PATH": request["PATH"],
                    "DATA": "DONE",
                    "OPERATION": request["OPERATION"],
                    "METADATA": {}}

        if ".." in request["PATH"] : return responce

        if request["OPERATION"] == "READ" : self.process_read_request(request, responce)
        elif request["OPERATION"] == "WRITE" : self.handle_write_request(request, responce)
        elif request["OPERATION"] == "LISTITEMS" : self.handle_listitem_reuqest(request, responce)
        elif request["OPERATION"] == "DELETE" : self.handle_delete_request(request, responce)
        else : request["DATA"] == "NONE"

        return responce

    def process_read_request(self,
                             request: dict,
                             responce: dict) -> None :
        if os.path.isfile(os.path.join(self.PATH, request["PATH"])) :
            if type(request["DATA"]) is int :
                try :
                    file_obj = open(os.path.join(self.PATH, request["PATH"]), "rb")
                    file_obj.seek(request["DATA"])
                    responce["DATA"] = file_obj.read(self.TRANSMISSION_CHUNK_SIZE).hex()
                    responce["METADATA"] = {"FILESIZE": os.path.getsize(os.path.join(self.PATH,
                                                                                     request["PATH"])),
                                            "DOWNLOADED": file_obj.tell()}
                except :
                    responce["DATA"] = ""
                    responce["METADATA"] = {"FILESIZE": 1, "DOWNLOADED": 1}
                finally :
                    try : file_obj.close()
                    except : pass
            else :
                dir_list = []
                dir_list.append(request["PATH"])
                responce["DATA"] = dir_list
        elif os.path.isdir(os.path.join(self.PATH, request["PATH"])) :
            dir_list = []
            for addrs, dirs, files in os.walk(os.path.join(self.PATH, request["PATH"])) :
                for file in files :
                    dir_list.append(os.path.join(addrs, file)[len(self.PATH)+1:])
            responce["DATA"] = dir_list
        else : responce["DATA"] = "NONE"

    def handle_write_request(self,
                             request: dict,
                             responce: dict) -> None :
        if request["DATA"][1] == 0 :
            try : self.create_directory(request["PATH"])
            except : responce["DATA"] = "NONE"
        try : self.write_to_file(request)
        except : responce["DATA"] = "NONE"

    def handle_listitem_reuqest(self,
                                request: dict,
                                responce: dict) -> None :
        try : responce["DATA"] = os.listdir(os.path.join(self.PATH, request["PATH"]))
        except : responce["DATA"] = None

    def handle_delete_request(self,
                              request: dict,
                              responce: dict) -> None :
        if os.path.isdir(os.path.join(self.PATH, request["PATH"])) :
            os.system("rm -r "+os.path.join(self.PATH, request["PATH"]))
        elif os.path.isfile(os.path.join(self.PATH, request["PATH"])) :
            os.system("rm "+os.path.join(self.PATH, request["PATH"]))
        else : responce["DATA"] = "DO NOT EXIST"

    def create_directory(self,
                         file: str) -> None :
        if not os.path.isfile(os.path.join(self.PATH, file)) :
            dir_file_sep_position = 0
            for _ in range(len(file)-1, -1, -1) :
                if file[_] == "/" :
                    dir_file_sep_position = _
                    break
            if not os.path.isdir(os.path.join(self.PATH, file[:dir_file_sep_position])) :
                os.makedirs(os.path.join(self.PATH, file[:dir_file_sep_position]))
        self.create_file(file)

    def create_file(self,
                    file: str) -> None :
        file_obj = open(os.path.join(self.PATH, file), "wb")
        try :
            file_obj.write(b'')
            file_obj.flush()
        except : pass
        finally :
            try : file_obj.close()
            except : pass

    def write_to_file(self,
                      request: dict) -> None :
        file_obj = open(os.path.join(self.PATH, request["PATH"]), "ab")
        try :
            file_obj.write(b''.fromhex(request["DATA"][0]))
            file_obj.flush()
        except : pass
        finally :
            try : file_obj.close()
            except : pass
