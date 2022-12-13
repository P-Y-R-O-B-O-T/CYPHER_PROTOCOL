from CYPHER_PROTOCOL.CYPHER_CLIENT.cypher_client import CYPHER_CLIENT
import time

# MAX BYTES THAT WOULD BE RECIEVED IN ONE SINGLE recv() CALL
# MAX LIMIT DEPENDS ON SYSTEM SPECS
RECV_BUFFER = 1024*1024*8

# MAX BYTES THAT WOULD BE TRANSMITTED IN ONE SINGLE send() CALL
# MAX LIMIT OF BYTES DEPENDS ON SYSTEM/PYTHON
TRANSMISSION_BUFFER = 1024*1024*1

# ENCRYPTION_KEY and DECRYPTION_KEY CAN BE SAME OR DIFFERENT                                     
# JUST KEEP IN MIND :                                                                            
# ENCRYPTION_KEY OF SERVER IS DECRYPTION_KEY OF CLIENT                                           
# DECRYPTION_KEY OF SERVER IS ENCRYPTION_KEY OF CLIENT                                           
#                                                                                                
# WE ARE KEEPING BOTH SAME FOR SOME SIMPLICITY
ENCRYPTION_KEY = "2ZpK1CdQfm0s1EZ1SIhYfV7MHdJf8X3U"
DECRYPTION_KEY = "2ZpK1CdQfm0s1EZ1SIhYfV7MHdJf8X3U"

# SERVER TIMEOUT PERIOD; CLIENT IS DISCONNECTED IF
# CLIENT DOES NOT SEND ANY REQUEST IN THIS PERIOD
TIMEOUT = 60*1

REQ_TIME = time.time()
INIT_TIME = time.time()

# HANDLING RESPONCES
def HANDLE_RESPONCE(responce: dict) -> None :
    global REQ_TIME
    print("[$] TIME :", time.time()-REQ_TIME)

# FUNCTION TO LET US KNOW WHEN WE ARE ONLINE
def ONLINE_SIGNAL_PROCESSOR() -> None :
    print("[!] You are online")

# FUNCTION TO LET US KNOW WHEN WE ARE OFFLINE
def OFFLINE_SIGNAL_PROCESSOR() -> None :
    print("[!] You are offline")

CLIENT = CYPHER_CLIENT(ip="127.0.0.1",
                       port=11111,
                       recv_buffer=RECV_BUFFER,
                       transmission_buffer=TRANSMISSION_BUFFER,
                       encryption_key=ENCRYPTION_KEY,
                       decryption_key=DECRYPTION_KEY,
                       responce_handler=HANDLE_RESPONCE,
                       timeout=TIMEOUT)

def TEST() -> None :
    global CLIENT
    global REQ_TIME
    global INIT_TIME

    CLIENT.connect()

    INIT_TIME = time.time()

    for _ in range(1024) :
        REQ_TIME = time.time()
        CLIENT.make_request()

    print("[@] TOTAL TIME TAKEN :", time.time()-INIT_TIME)

if __name__ == "__main__" :
    TEST()
