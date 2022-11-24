import socket
import threading
import time
import random

Broad_Port = 33255
Ship_Port = 33260
ROUTER_PORT = None
ROUTER_ADDRESS = None
ROUTER_NAME = None

Temp = [12.22,
 12.221,
 12.222000000000001,
 12.223,
 12.224,
 12.225000000000001,
 12.226,
 12.227,
 12.228,
 12.229000000000001,
 12.23,
 12.231,
 12.232000000000001,
 12.233,
 12.234,
 12.235000000000001,
 12.236,
 12.237,
 12.238000000000001,
 12.239]

Pressure = [1013.2,
 1013.201,
 1013.202,
 1013.2030000000001,
 1013.2040000000001,
 1013.205,
 1013.206,
 1013.207,
 1013.2080000000001,
 1013.2090000000001,
 1013.21,
 1013.211,
 1013.212,
 1013.2130000000001,
 1013.214,
 1013.215,
 1013.216,
 1013.2170000000001,
 1013.2180000000001,
 1013.219]

class Ship:
    def __init__(self,host,port):
        self.host = host
        self.port = port

    def broadcast(self):
        print("code inside broadcast")
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = f'SHIP destroyer {self.host} {self.port} TEMPERATURE|PRESSURE'.encode('utf-8')
        print("sending Ship details to the router")

       # print(True)
        sock.sendto(message, ('<broadcast>', Broad_Port))
        print("Ship IP sent!")

    def receiveData(self):
        """Listen on own port for Router IP."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.port))
        s.listen(5)
        while True:
            conn, _ = s.accept()
            data = conn.recv(1024)
            data = data.decode('utf-8')
            split_receive = data.split(' ')            
            print(data)
            ROUTER_NAME = split_receive[1]
            ROUTER_PORT = int(split_receive[3])
            ROUTER_ADDRESS = split_receive[2]            
            address_message = "35 degree from carrier"
            conn.send(address_message.encode('UTF-8'))
            conn.close()
            time.sleep(1)    
            self.receiveInterestRouter(s)
    

    def receiveInterestRouter(self,socket):
        while True:
            conn, _ = socket.accept()
            data = conn.recv(1024)
            data = data.decode('utf-8')
            requirement = data.split("/")
            requirement = requirement[1].lower()
            if requirement == "temperature":
                address_message = str(random.choice(Temp))
                conn.send(address_message.encode('UTF-8'))
                conn.close()
                time.sleep(1)
            elif requirement ==  "pressure":
                address_message = str(random.choice(Pressure))
                conn.send(address_message.encode('UTF-8'))
                conn.close()
                time.sleep(1)
            else:
                conn.close()

def main():
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    print(host)
    node = Ship(host,Ship_Port)
    print(host)
    node.broadcast()
    node.receiveData()


if __name__ == '__main__':
    main()

