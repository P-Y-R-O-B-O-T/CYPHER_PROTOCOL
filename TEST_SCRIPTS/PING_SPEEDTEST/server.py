from CYPHER_PROTOCOL.CYPHER_SERVER.cypher_server import CYPHER_SERVER

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

# CAN CHANGE THE STRING SIZE AND SEE
# HOW IT AFFECTS THE PING AND OVERALL RECIEVING TIME
DATA = "~"*1024*1024*1

# HANDLING RESPONCES
def HANDLE_REQUEST(request: dict, ip_port: tuple) -> dict :
    global DATA
    request["DATA"] = DATA
    return request

SERVER = CYPHER_SERVER(host="127.0.0.1",
                       port=11111,
                       recv_buffer=RECV_BUFFER,
                       transmission_buffer=TRANSMISSION_BUFFER,
                       encryption_key=ENCRYPTION_KEY,
                       decryption_key=DECRYPTION_KEY,
                       request_handler=HANDLE_REQUEST,
                       timeout=TIMEOUT,
                       debug1=True,
                       debug2=True)

if __name__ == "__main__" :
    try :
        SERVER.start_server()
        input()
        SERVER.stop_server()
    except :
        SERVER.stop_server()
