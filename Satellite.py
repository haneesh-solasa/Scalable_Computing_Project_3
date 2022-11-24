import argparse
import socket
import time
import traceback
import rsa

ROUTER_PORT = []
B_CAST_PORT = 33255
ROUTER_ADDRESS = []
ROUTER_NAME = []
MY_PORT = 33258
publicKey, privateKey = rsa.newkeys(512)


class Satellite():
    def __init__(self,host,port):
        self.host = host
        self.port = port
    
    def broadcast(self):
        socket_0 = socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
        socket_0.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        socket_0.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message = f'Satellite satellite1 {self.host} {self.port} ship_safety'.encode('utf-8')
        socket_0.sendto(message,('<broadcast>',B_CAST_PORT))

    def listen_to_router(self):
        socket4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        hostname = socket.gethostname()
        host = socket.gethostbyname(hostname)
        socket4.bind((self.host,MY_PORT))
        socket4.listen(5)
        conn ,_ = socket4.accept()
        data = conn.recv(1024)
        data = data.decode('utf-8')
        conn.close()
        socket4.close()
        split_receive = data.split(' ')
        ROUTER_PORT.append(int(split_receive[3]))
        ROUTER_ADDRESS.append(split_receive[2])
        ROUTER_NAME.append(split_receive[1])
        print(ROUTER_PORT)
        print(ROUTER_ADDRESS)
        print(ROUTER_NAME)

    def listen_broadcasting():
        # For listening to other routers that want to join the network
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                socket.IPPROTO_UDP)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client.bind(("",B_CAST_PORT))
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
def send_interest(ship_name):
    
    #Getting info from broadcast message from router
    for i in len(ROUTER_ADDRESS):
        router_info = {(ROUTER_ADDRESS[i], ROUTER_PORT[i])}

        for router in router_info:
            try:
                socket_1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                socket_1.connect(router)
                message = ship_name + '/' + 'temperature '
                message=message.encode()
                message = message + publicKey.save_pkcs1('PEM')
                socket_1.send(message)
                print("Ship Name sent : Waiting for summary information of ship")
                data = socket_1.recv(1024)
                decoded_data = decrypt_msg(data)
                print(decoded_data)
                socket_1.close()
            except Exception as e:
                print('Exception Occured', e)

def decrypt_msg(msg):
    decoded_data = rsa.decrypt(msg,privateKey).decode()
    return decoded_data

def call_action(summary):
    return "Functionality yet to be added"

def send_to_router(conn,raddr,action):
    try:
        message = action
        conn.send(message.encode())

    except:
        print(traceback.format_exc())
        print('Exception Occured:', Exception)
        



def main(): 

    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    Satellite_1 = Satellite(host,MY_PORT)
    Satellite_1.broadcast()
    Satellite_1.listen_to_router()
    Ship_names=['carrier','destroyer','cruiser']
    while True:

        print('Which Ship do you want to communicate? Carrier/Destroyer/Cruiser')
        x=input()
        if x.lower() not in  Ship_names:
            print("Which Ship do you want to communicate? Carrier/Destroyer/Cruiser")
            exit(1)
        else:
            ship_name = x
            ship_name_lower = x.lower()
                 
        send_interest(ship_name_lower)

        time.sleep()


if __name__ == '__main__':
    main()


        