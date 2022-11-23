import argparse
import socket
import time
import traceback

ROUTER_PORT = None
B_CAST_PORT = 33255
ROUTER_ADDRESS = None
MY_PORT = 33258


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
        global ROUTER_PORT
        global ROUTER_ADDRESS
        socket4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        hostname = socket.gethostname()
        host = socket.gethostbyname(hostname)
        socket4.bind((self.host,MY_PORT))
        socket4.listen(5)
        conn ,_ = socket4.accept()
        data = conn.recv(1024)
        data = data.decode('utf-8')
        conn.close()
        split_receive = data.split(' ')
        ROUTER_PORT = int(split_receive[3])
        ROUTER_ADDRESS = split_receive[2]
        print(ROUTER_PORT)
        print(ROUTER_ADDRESS)


def send_interest(ship_name):
    
    #Getting info from broadcast message from router
    router_info = {(ROUTER_ADDRESS, ROUTER_PORT)}

    for router in router_info:
        try:
            socket_1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_1.connect(router)
            message = ship_name + '/' + 'temperature'
            socket_1.send(message.encode())
            print("Ship Name sent : Waiting for summary information of ship")
            #acknowledgement = socket.recv(1024)
            #print("Acknowledgement", acknowledgement.decode('utf-8'))
            #recv_data()
            data = socket_1.recv(1024)
            print(data.decode('utf-8'))
        except Exception as e:
            print('Could not send acknowledgement', e)

# def recv_data():
#     socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     hostname = socket.gethostname()
#     host = socket.gethostbyname(hostname)
#     socket2.bind((host,MY_PORT))
#     socket2.listen(5)
#     while True:
#         conn, addr = socket2.accept()
#         summary = conn.recv(1024)
#         summary_info = summary.decode('utf-8')
#         print("Ship Summary: ",summary_info)
#         #action = call_action(summary_info)

#         #send_to_router(conn,addr[0],action)
#         conn.close()
#         time.sleep(100)

def call_action(summary):
    return "Functionality yet to be added"

def send_to_router(conn,raddr,action):
    try:
        message = action
        conn.send(message.encode())

    except:
        print(traceback.format_exc())
        print('Could not send acknowledgement', Exception)
        



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--shipname', help='Which Ship do you want to communicate? Carrier/Destroyer/Cruiser', required=True)
    args = parser.parse_args()
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    Satellite_1 = Satellite(host,MY_PORT)
    Satellite_1.broadcast()
    Satellite_1.listen_to_router()
    Ship_names=['carrier','destroyer','cruiser']
    
    if args.shipname.lower() not in  Ship_names:
        print("Which Ship do you want to communicate? Carrier/Destroyer/Cruiser")
        exit(1)
    else:
        ship_name = args.shipname
        ship_name_lower = ship_name.lower()
    
    while True:               
        send_interest(ship_name_lower)
        time.sleep(10)


if __name__ == '__main__':
    main()


        