import argparse
import socket
import time
import traceback
import rsa
import threading

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
        socket_0.close()
        t= threading.Thread(target = self.listen_broadcasting)
        t.start()

    def listen_to_router_addr(self):
        socket4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        hostname = socket.gethostname()
        host = socket.gethostbyname(hostname)
        print("Listening to Router Address on ", self.host + ':' + str(MY_PORT))
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
        print("Received Router Port ",ROUTER_PORT[0])
        print("Received Router Address ",ROUTER_ADDRESS[0])
        print("Received Router Name ",ROUTER_NAME[0])

    def listen_broadcasting(self):
        # For listening to other routers that want to join the network
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                socket.IPPROTO_UDP)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client.bind(("",B_CAST_PORT))
        print('listening to broadcasts for new routers:')
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
                print("New Router Joined with Address:", ROUTER_ADDRESS )
            else:
                continue

    def receive_interest_router(self):
        """Listen on own port for Ship Data"""
        print("listening for interest data from Ship on:")
        print(f'{self.host}:{self.port}')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.port))
        s.listen(5)
        while True:
            try:
                conn, addr = s.accept()
                connection_thread = threading.Thread(target=self.process_interest_connection, args=(conn, addr))
                connection_thread.start()
                time.sleep(5)
            except TimeoutError:
                pass
            except Exception as e:
                pass
                print(f'Exception occured while receiving interest: {e}')

    
    def process_interest_connection(self, connection, address):
        #print("addr: ", address[0])
        
        data = connection.recv(1024)
        #print(data)
        interest = data.decode('utf-8')
        name = interest.split(" ")
        if name[0]== "INTEREST":
                requirement = name[1].split("/")
                requirement = requirement[1].lower()
                public_key_raw = " ".join(name[2:]).encode()
                public_key_ship = rsa.PublicKey.load_pkcs1(public_key_raw)
                #print(public_key_raw)
                if(requirement == "ship_safety"):
                    print("Sending location interest to the ship")
                    interest_type = name[1].split("/")[2] + "/location"
                    location_ship = send_interest_ship(interest_type)
                    if(location_ship=='NACK'):
                        print("None of the routers are responding")
                    else:
                        print(location_ship)
                        
                        enc_data = rsa.encrypt("Data hello hello".encode(),public_key_ship)
                        connection.send(enc_data)
                        connection.close()



def send_interest_ship(interest_type):
    
    #Getting info from broadcast message from router
    address_not_working = []
    for i in range(len(ROUTER_ADDRESS)):
        router_info = {(ROUTER_ADDRESS[i], ROUTER_PORT[i])}

        for router in router_info:
            try:
                socket_1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                socket_1.connect(router)
                message = 'INTEREST ' + interest_type + ' ' 
                message=message.encode()
                message = message + publicKey.save_pkcs1('PEM')
                socket_1.send(message)
                print("Interest for Location sent, waiting for location")
                data = socket_1.recv(1024)
                if(data.startswith('NACK'.encode())):
                    print(data.decode('utf-8'))
                else:
                    decoded_data = decrypt_msg(data)
                    print(decoded_data)
                    split_decoded_data = decoded_data.split(" ")
                    if(len(split_decoded_data)>1):
                        cell = split_decoded_data[2]
                        socket_1.close()
                        return cell

                socket_1.close()
            
            except Exception as e:
                print('Exception Occured', e)
                address_not_working.append(ROUTER_ADDRESS[i])
    for address in address_not_working:
        index_not_working = ROUTER_ADDRESS.index(address)
        print("Removed Address:",ROUTER_ADDRESS[index_not_working])
        ROUTER_ADDRESS.remove(ROUTER_ADDRESS[index_not_working])
        ROUTER_NAME.remove(ROUTER_NAME[index_not_working])
        ROUTER_PORT.remove(ROUTER_PORT[index_not_working])
    return "NACK"

def send_interest_buouy():
    buouy_names = ['A1','A2','B1','B2']
    with open("weather.csv", encoding = 'utf-8', mode='a') as f:
        address_not_working = []

        for i in range(len(ROUTER_ADDRESS)):
            router_info = {(ROUTER_ADDRESS[i], ROUTER_PORT[i])}

            for router in router_info:
                try:
                    socket_n = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    socket_n.connect(router)
                    for buouy in buouy_names:
                        message = 'INTEREST ' + buouy + "/weather_summary"
                        message = message.encode()
                        socket_n.send(message)
                        print("Interest for weather sent, waiting for weather info from buoy", buouy)
                        data_received=socket_n.recv(1024)
                        if(data_received.startswith('NACK'.encode())):
                            print(data_received.decode('utf-8'))
                        else:
                            data_decoded = data_received.decode('utf-8')
                            data_decoded_split = data_decoded.split(" ")[2]
                            f.write(data_decoded_split)
                except Exception as e:
                    print('Exception Occured', e)
                    address_not_working.append(ROUTER_ADDRESS[i])
    for address in address_not_working:
        index_not_working = ROUTER_ADDRESS.index(address)
        print("Removed Address:",ROUTER_ADDRESS[index_not_working])
        ROUTER_ADDRESS.remove(ROUTER_ADDRESS[index_not_working])
        ROUTER_NAME.remove(ROUTER_NAME[index_not_working])
        ROUTER_PORT.remove(ROUTER_PORT[index_not_working])
    return "NACK"


                


def decrypt_msg(msg):
    decoded_data = rsa.decrypt(msg,privateKey).decode()
    return decoded_data
        

def check_weather():
    while True:
        send_interest_buouy()
        time.sleep(10)

def main(): 

    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    Satellite_1 = Satellite(host,MY_PORT)


    t1 = threading.Thread(target = Satellite_1.broadcast)
    t2 = threading.Thread(target = Satellite_1.listen_to_router_addr)
    t3 = threading.Thread(target=check_weather)
    t4 = threading.Thread(target = Satellite_1.receive_interest_router)

    t1.start()
    t2.start()
    time.sleep(5)
    t3.start()
    t4.start()

if __name__ == '__main__':
    main()


        