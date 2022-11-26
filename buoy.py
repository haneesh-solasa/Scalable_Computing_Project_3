import socket
import threading
import time
import random
import rsa
import argparse

Broad_Port = 33255
Ship_Port = 33256
ROUTER_PORT = []
ROUTER_ADDRESS = []
ROUTER_NAME = []



class Buoy:
    def __init__(self,host,port,name):
        self.host = host
        self.port = port
        self.name = name
        self.weather_data = open(f'{name}.csv', 'r')

    def broadcast(self):
        print("code inside broadcast")
        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = f'BUOY A1 {self.host} {self.port} weather_summary|AirTemp|SeaTemp|Humidity|WindSpeed|Gust'.encode('utf-8')
        print("sending Buoy details to the router")

       # print(True)
        sock.sendto(message, ('<broadcast>', Broad_Port))
        print("Buoy IP sent!")
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
            if (name[0]== "INTEREST"):
                requirement = name[1].split("/")
                requirement = requirement[1]
                line = self.weather_data.readline()
                if requirement == "weather_summary":
                    message = f'DATA A1 {line}'
                    print(f"send this info {message}")
                    conn.send(message.encode())
                    conn.close()
                    time.sleep(1)
                elif requirement ==  "AirTemp":
                    AirTemp_1 = line.split(",")
                    AirTemp = AirTemp_1[11]
                    message = f'DATA A1 {AirTemp}'
                    conn.send(message.encode())
                    conn.close()
                    time.sleep(1)
                elif requirement ==  "SeaTemp":
                    SeaTemp_1 = line.split(",")
                    SeaTemp = SeaTemp_1[12]
                    message = f'DATA A1 {SeaTemp}'
                    conn.send(message.encode())
                    conn.close()
                    time.sleep(1)
                elif requirement ==  "Humidity":
                    Humidity_1 = line.split(",")
                    Humidity = Humidity_1[13]
                    message = f'DATA A1 {Humidity}'
                    conn.send(message.encode())
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', type=str)
    args=parser.parse_args()
    name = args.name
    print(host)
    node = Buoy(host,Ship_Port,name)
    print(host)
    node.broadcast()
    node.receiveRouterDetails()
    


if __name__ == '__main__':
    main()