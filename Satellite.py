import socket
import time
import rsa
import threading
import argparse
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

ROUTER_PORT = []
B_CAST_PORT = 33255
ROUTER_ADDRESS = []
ROUTER_NAME = []
MY_PORT = 33258

cells = ['A1', 'A2', 'B1', 'B2']
colour = ['GREEN', 'YELLOW', 'ORANGE', 'RED']
codes = pd.DataFrame(columns=cells)


class Satellite():
    def __init__(self,host, port, models):
        self.host = host
        self.port = port
        self.models = models
        self.publicKey, self.privateKey = rsa.newkeys(1024)
    
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
        #print("Received Router Address ",ROUTER_ADDRESS[0])
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
                print("New Router Joined with Name:", ROUTER_NAME )
            else:
                continue

    def receive_interest_router(self):
        """Listen on own port for Ship Data"""
        print("listening for interest data from Ship on:")
        print(f'{self.port}')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
        message = data.decode('utf-8')
        message_chunks = message.split(" ")
        if message_chunks[0]== "INTEREST":
                interest_chunks = message_chunks[1].split("/")
                interest = interest_chunks[1].lower()
                public_key_raw = " ".join(message_chunks[2:]).encode()
                public_key_ship = rsa.PublicKey.load_pkcs1(public_key_raw)
                #print(public_key_raw)
                if interest == "ship_safety":
                    print("Sending location interest to the ship")
                    interest_route = interest_chunks[2] + "/location"
                    location_ship = self.send_interest_ship(interest_route)
                    if location_ship=='NACK':
                        print("None of the routers are responding")
                    else:
                        max_warn = []
                        for cell in cells:
                            pred = pd.DataFrame();
                            for weather in ['Gust', 'WindS']:
                                prediction = self.models[cell][weather].forecast(steps=5).rename(weather)
                                pred = pd.concat([pred, prediction], axis=1)
                            code = 0
                            pred.reset_index(inplace=True)
                            for k in range(len(pred)):
                                wind = pred.loc[k, 'WindS'] - 19
                                gust = pred.loc[k, 'Gust'] - 40
                                codes.loc[k, cell] = max(0, wind // 8, gust // 10)
                                code = max(code, wind // 8, gust // 10)
                            max_warn.append(code)
                        print(max_warn)
                        current = max_warn[cells.index(location_ship)]
                        best = min(max_warn)
                        if colour[int(current)] == colour[int(best)]:
                            message = f'DATA {message_chunks[1]} {location_ship}'
                        else:
                            message = f'DATA {message_chunks[1]} {cells[max_warn.index(int(best))]}'
                        enc_data = rsa.encrypt(message.encode(), public_key_ship)
                        connection.send(enc_data)
                        connection.close()



    def send_interest_ship(self, interest_type):
        
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
                    message = message + self.publicKey.save_pkcs1('PEM')
                    socket_1.send(message)
                    print(f"{interest_type} sent, waiting for location")
                    data = socket_1.recv(1024)
                    if(data.startswith('NACK'.encode())):
                        print(data.decode('utf-8'))
                    else:
                        decoded_data = self.decrypt_msg(data)
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

    def send_interest_buouy(self):
        buouy_names = cells
        address_not_working = []
        for i in range(len(ROUTER_ADDRESS)):
            router_info = {(ROUTER_ADDRESS[i], ROUTER_PORT[i])}

            for router in router_info:
                try:
                    for buoy in buouy_names:
                        socket_n = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        socket_n.connect(router)
                        message = 'INTEREST ' + buoy + "/weather_summary"
                        message = message.encode()
                        socket_n.send(message)
                        print("Interest for weather sent, waiting for weather info from buoy", buoy)
                        data_received=socket_n.recv(2048)
                        #print(data_received)
                        if(data_received.startswith('NACK'.encode())):
                            print(data_received.decode('utf-8'))
                        else:
                            data_decoded = data_received.decode('utf-8')
                            data_decoded_split = data_decoded.split(" ")[2]
                            #print(data_decoded_split.split(','))
                            wind = data_decoded_split.split(',')[5]
                            gust = data_decoded_split.split(',')[6]
                            self.models[buoy]['Gust'] = self.models[buoy]['Gust'].append([float(gust)])
                            self.models[buoy]['WindS'] = self.models[buoy]['WindS'].append([float(wind)])
                        socket_n.close()
                except Exception as e:
                    print(f'Exception Occured {e}')
                    address_not_working.append(ROUTER_ADDRESS[i])
        for address in address_not_working:
            index_not_working = ROUTER_ADDRESS.index(address)
            print("Removed Address of the Router:",ROUTER_NAME[index_not_working])
            ROUTER_ADDRESS.remove(ROUTER_ADDRESS[index_not_working])
            ROUTER_NAME.remove(ROUTER_NAME[index_not_working])
            ROUTER_PORT.remove(ROUTER_PORT[index_not_working])
        return "NACK"


                


    def decrypt_msg(self, msg):
        decoded_data = rsa.decrypt(msg, self.privateKey).decode()
        return decoded_data
        

    def check_weather(self):
        while True:
            self.send_interest_buouy()
            time.sleep(10)

def main(): 

    weather22 = pd.read_csv("2022_2.csv", header=0)
    weather22 = weather22[weather22['D'] < 48]
    models = {}
    for i in cells:
        data22 = weather22.loc[weather22['ID'] == i, ['WindS', 'Gust', 'Code']]
        data = data22
        data = data.dropna()
        data.reset_index(drop=True, inplace=True)
        models[i] = {}
        for j in ['Gust', 'WindS']:
            print(f'Running {i} {j}')
            mod = SARIMAX(data[j], order=(0, 1, 2), seasonal_order=(1, 0, 1, 6))
            res = mod.fit()
            models[i][j] = res
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    Satellite_1 = Satellite(host, MY_PORT, models)
    a = input('waiting...')
    t1 = threading.Thread(target=Satellite_1.broadcast)
    t2 = threading.Thread(target=Satellite_1.listen_to_router_addr)
    t3 = threading.Thread(target=Satellite_1.check_weather)
    t4 = threading.Thread(target=Satellite_1.receive_interest_router)

    t1.start()
    t2.start()
    time.sleep(5)
    t3.start()
    t4.start()

if __name__ == '__main__':
    main()


        
