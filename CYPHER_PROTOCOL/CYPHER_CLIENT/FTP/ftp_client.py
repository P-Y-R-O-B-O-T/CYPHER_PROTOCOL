import threading
import time
import random
import os
import mimetypes
from ..cypher_client import CYPHER_CLIENT

#$$$$$$$$$$#

class FTP_CLIENT(CYPHER_CLIENT) :
    def __init__(self,
                 file_responce_trigger: object,
                 recv_chunk_size: int = 1024*1024*1,
                 transmission_chunk_size: int = 1024*1024*1,
                 **init_data) -> None :

        super().__init__(responce_handler=self.responce_processor, **init_data)

        self.RECV_CHUNK_SIZE = recv_chunk_size
        self.TRANSMISSION_CHUNK_SIZE = transmission_chunk_size

        self.FIRST_FETCH = True
        self.CHAR_POSITION = 0
        self.FILES_TO_FETCH = []
        self.WRITE = True

        self.DOWNLOAD_PATH = ""

        self.TRIGGER = file_responce_trigger

    def responce_processor(self,
                           responce: dict) -> None :
        if responce["OPERATION"] == "READ" :
            if type(responce["DATA"]) is list : self.FILES_TO_FETCH = responce["DATA"]
            else :
                self.process_file_data(responce)
                if self.TRIGGER != None : self.TRIGGER(responce)
        elif responce["OPERATION"] == "WRITE" :
            if self.TRIGGER != None : self.TRIGGER(responce)
        elif responce["OPERATION"] == "LISTITEMS" :
            if self.TRIGGER != None : self.TRIGGER(responce)
        elif responce["OPERATION"] == "DELETE" :
            if self.TRIGGER != None : self.TRIGGER(responce)

    def process_file_data(self,
                          responce: dict) -> None :
        if os.path.isfile(os.path.join(self.DOWNLOAD_PATH, responce["PATH"])) :
            if (responce["DATA"] != "") or (responce["DATA"] != "b''") :
                if self.WRITE : self.write_to_file(responce)
                self.CHAR_POSITION += self.RECV_CHUNK_SIZE
            if (responce["DATA"] == "") or (responce["DATA"] == "b''") :
                self.FILES_TO_FETCH.pop(0)
                self.CHAR_POSITION = 0

    def create_directory(self) -> None :
        for _ in self.FILES_TO_FETCH :
            if not os.path.isfile(os.path.join(self.DOWNLOAD_PATH, _)) :
                dir_file_sep_position = 0
                _ = "./"+_
                for __ in range(len(_)-1, -1,-1) :
                    if _[__] == "/" :
                        dir_file_sep_position = __
                        break
                if not os.path.isdir(os.path.join(self.DOWNLOAD_PATH, _[:dir_file_sep_position])) :
                    os.makedirs(os.path.join(self.DOWNLOAD_PATH, _[:dir_file_sep_position]))
            self.create_file(_)

    def create_file(self,
                    file: str) -> None :
        file_obj = open(os.path.join(self.DOWNLOAD_PATH, file), "wb")
        try :
            file_obj.write(b'')
            file_obj.flush()
        except : pass # self.FILES_TO_FETCH = []
        finally : file_obj.close()

    def write_to_file(self,
                      responce: dict) -> None :
        file_obj = open(os.path.join(self.DOWNLOAD_PATH, responce["PATH"]), "ab")
        try :
            file_obj.write(b''.fromhex(responce["DATA"]))
            file_obj.flush()
        except : pass # self.FILES_TO_FETCH = []
        finally : file_obj.close()

    def fetch_file_s(self,
                     path: str,
                     download_path: str,
                     write: bool = True) -> None :
        self.WRITE = write
        self.DOWNLOAD_PATH = download_path
        self.make_request(path=path, operation="READ")
        if self.WRITE : self.create_directory()

        while self.FILES_TO_FETCH != [] :
            self.make_request(path=self.FILES_TO_FETCH[0],
                              operation="READ",
                              data=self.CHAR_POSITION)

    def upload_file_s(self,
                      path: str,
                      server_path: str) -> None :
        dir_list = []
        if os.path.isdir(path) :
            for addrs, dirs, files in os.walk(path) :
                for file in files :
                    dir_list.append(os.path.join(addrs, file))
        elif os.path.isfile(path) : dir_list.append(path)

        for _ in dir_list :
            file_obj = open(os.path.join("", _), "rb")
            file_data = [file_obj.read(self.TRANSMISSION_CHUNK_SIZE).hex(), 0]
            while file_data[0] != "" :
                try : file_size = os.path.getsize(_)
                except : break

                self.make_request(path=os.path.join(server_path, _),
                                  operation="WRITE", data=file_data,
                                  metadata={"FILESIZE": file_size,
                                            "UPLOADED": file_obj.tell()})
                file_data[1] += 1
                try : file_data[0] = file_obj.read(self.TRANSMISSION_CHUNK_SIZE).hex()
                except : file_data[0] = ""
            file_obj.close()

    def get_dir_content(self,
                        path: str) -> None :
        self.make_request(path=path, operation="LISTITEMS")

    def delete_file_folder(self,
                           path: str) -> None :
        self.make_request(path=path, operation="DELETE")
