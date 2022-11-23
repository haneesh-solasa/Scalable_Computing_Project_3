import socket
import threading
import time

Broad_Port = 33255
Ship_Port = 33256

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

    def receiveData(self):
        """Listen on own port for Router IP."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.port))
        s.listen(5)
        while True:
            conn, _ = s.accept()
            data = conn.recv(1024)
            data = data.decode('utf-8')
            print(data)
            address_message = "35 degree from carrier"
            conn.send(address_message.encode('UTF-8'))
            conn.close()
            time.sleep(1)

'''    def Listen_for_request_from_router(self):
        print("listening from router")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, Ship_Port))
        s.listen(5)
        conn, addr = s.accept()
        data = conn.recv(1024)
        print(data)'''



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