#!/usr/bin/env python3

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
        message = f'HOST {self.host} PORT {self.port} ACTION Speed '.encode('utf-8')
        print(message)
        while True:
            print(True)
            sock.sendto(message, ('<broadcast>', Broad_Port))
            # print("Host IP sent!")
            time.sleep(10)
        
def main():
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    print(host)
    node = Ship(host,Ship_Port)
    print(host)
    node.broadcast()
    time.sleep(3)


if __name__ == '__main__':
    main()