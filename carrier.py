import socket
import threading
import time
import random
import rsa

Broad_Port = 33255
Ship_Port = 33256
ROUTER_PORT = []
ROUTER_ADDRESS = []
ROUTER_NAME = []

Humidity = [70.0,70.001,70.002,70.003,70.004,70.005,70.006,70.007,70.008,70.009,70.01,70.011,70.012,70.013,70.014,70.015,70.016,70.017,70.018,70.019]

Temp = [12.22,12.221,12.222000000000001,12.223,12.224,12.225000000000001,12.226,12.227,12.228,12.229000000000001,12.23,12.231,12.232000000000001,12.233,12.234,12.235000000000001,12.23612,12.238000000000001,12.239]

Pressure = [1013.2,1013.201,1013.202,1013.2030000000001,1013.2040000000001,1013.205,1013.206,1013.207,1013.2080000000001,1013.2090000000001,1013.21,1013.211,1013.212,1013.2130000000001,1013.214,1013.215,1013.216,1013.2170000000001,1013.2180000000001,1013.219]


class Ship:
    def __init__(self,host,port):
        self.host = host
        self.port = port

    def broadcast(self):
        print("code inside broadcast")
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = f'SHIP carrier {self.host} {self.port} TEMPERATURE|HUMIDITY|PRESSURE'.encode('utf-8')
        print("sending Ship details to the router")

       # print(True)
        sock.sendto(message, ('<broadcast>', Broad_Port))
        print("Ship IP sent!")
        sock.close()
        t = threading.Thread(target = self.listen_broadcasting)
        t.start()

    def receiveRouterDetails(self):
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
            ROUTER_NAME.append(split_receive[1])
            ROUTER_PORT.append(int(split_receive[3]))
            ROUTER_ADDRESS.append(split_receive[2])            
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
            name = data.split(" ")
            if name[0]== "INTEREST":
                requirement = name[1].split("/")
                requirement = requirement[1].lower()
                public_key_raw = " ".join(name[2:]).encode()
                print(public_key_raw)
                public_key = rsa.PublicKey.load_pkcs1(public_key_raw)
                if requirement == "temperature":
                    address_message = str(random.choice(Temp))
                    message = rsa.encrypt(address_message.encode(),public_key)
                    conn.send(message)
                    conn.close()
                    time.sleep(1)
                elif requirement ==  "pressure":
                    address_message = str(random.choice(Temp))
                    message = rsa.encrypt(address_message.encode(),public_key)
                    conn.send(message)
                    conn.close()
                    time.sleep(1)
                elif requirement ==  "humidity":
                    address_message = str(random.choice(Humidity))
                    message = rsa.encrypt(address_message.encode(),public_key)
                    conn.send(message)
                    conn.close()
                    time.sleep(1)
                else:
                    conn.close()
            else:
                print(f"i received this {name}")
                conn.close()

    def listen_broadcasting(self):
        # For listening to other routers that want to join the network
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                socket.IPPROTO_UDP)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client.bind(("",Broad_Port))
        print('listening to broadcasts:')
        new_router = False
        while new_router == False:
            data,_ = client.recvfrom(1024)
            data = data.decode('utf-8')
            data_message = data.split(' ')
            type = data_message[0]
            name = data_message[1]
            host = data_message[2]
            port = int(data_message[3])
            if(type.lower() == 'router'):
                ROUTER_ADDRESS.append(host)
                ROUTER_PORT.append(int(port))
                ROUTER_NAME.append(name)
                new_router = True
            else:
                continue
        print(ROUTER_ADDRESS[1])

def main():
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    print(host)
    node = Ship(host,Ship_Port)
    print(host)
    node.broadcast()
    node.receiveRouterDetails()


if __name__ == '__main__':
    main()