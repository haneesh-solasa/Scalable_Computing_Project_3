import socket
import threading
import time
import rsa
import argparse

BCAST_PORT = 33255
MY_PORT = 33327


joining = True


class Router:
    def __init__(self, name, host, port):
        self.name = name
        self.host = host
        self.port = port

    def __repr__(self):
        return f'Router: {self.name} {self.host}:{self.port}'

    def __str__(self):
        return f'Router: {self.name}'

    def __eq__(self, other):
        return self.host == other.host and self.port == other.port

    def __hash__(self):
        return hash((self.host, self.port))

class Ship:

    def __init__(self, host, port, name, location, actions):
        self.host = host
        self.port = port
        self.name = name
        self.location = location
        self.actions = actions
        self.routers = set()
        public_key, private_key = rsa.newkeys(1024)
        self.public_key = public_key
        self.private_key = private_key

    def join_network(self):
        """Broadcast the host IP."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        actions = '|'.join(self.actions)
        message = f'SHIP {self.name} {self.host} {self.port} {actions}'.encode('utf-8')
        print("Joining network")
        s.sendto(message, ('<broadcast>', BCAST_PORT))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
            s2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s2.bind((self.host, self.port))
            s2.listen(5)
            s2.settimeout(2)
            while joining:
                try:
                    conn, addr = s2.accept()
                    connection_thread = threading.Thread(target=self.process_join_response, args=[conn])
                    connection_thread.start()
                except TimeoutError:
                    pass
                except Exception:
                    pass
        s.close()

    def process_join_response(self, c   onnection):
        data = connection.recv(1024)
        data_message = data.decode('utf-8')
        if not data_message.startswith('INTEREST'):
            data_message = data_message.split(' ')
            type = data_message[0]
            name = data_message[1]
            host = data_message[2]
            port = int(data_message[3])
            if type == 'ROUTER':
                router = Router(name, host, port)
                self.routers.add(router)
        connection.close()

    def listen_to_broadcasts(self):
        """Update peers list on receipt of their address broadcast."""
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                socket.IPPROTO_UDP)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client.bind(("", BCAST_PORT))
        print('listening to broadcasts...')
        while True:
            try:
                data, _ = client.recvfrom(1024)
                print("received advertisement")
                data = data.decode('utf-8')
                data_message = data.split(' ')
                type = data_message[0]
                name = data_message[1]
                host = data_message[2]
                port = int(data_message[3])
                if type == 'ROUTER':
                    router = Router(name, host, port)
                    self.routers.add(router)
                    self.respond_to_new_router(router)
            except TimeoutError:
                pass
            except KeyboardInterrupt:
                client.close()
                break
            except Exception as e:
                pass
                print(f'Exception occured while listening to broadcasts: {e}')
        client.close()
        print('Stopping')

    def respond_to_new_router(self, router):
        time.sleep(1.5)
        actions = '|'.join(self.actions)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((router.host, router.port))
            address_message = f'SHIP {self.name} {self.host} {self.port} {actions}'
            s.send(address_message.encode('utf-8'))

    def listen_to_interests(self):
        print("listening for interest data")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.host, self.port))
        s.listen(5)
        while True:
            try:
                conn, addr = s.accept()
                connection_thread = threading.Thread(target=self.process_interest_connection, args=[conn])
                connection_thread.start()
                time.sleep(1)
            except TimeoutError:
                pass
            except Exception as e:
                pass
                print(f'Exception occured while receiving interest: {e}')
        print('Closing')
        s.close()

    def process_interest_connection(self, connection):
        raw_data = connection.recv(1024)
        data = raw_data.decode('utf-8')
        if data.startswith('INTEREST'):
            interest_parts = data.split(' ')
            route = interest_parts[1].split('/')[1]
            print(f"Received interest: {route}")
            public_key_raw = ' '.join(interest_parts[2:]).encode()
            public_key = rsa.PublicKey.load_pkcs1(public_key_raw)
            if route == 'location':
                self.send_location(connection, public_key)
            else:
                self.send_NACK(connection, route)

    def send_location(self, connection, public_key):
        message = f'DATA {self.name}/location {self.location}'.encode()
        encrypted_message = rsa.encrypt(message, public_key)
        connection.send(encrypted_message)
        connection.close()

    def send_NACK(self, connection, route):
        nack = f'NACK {self.name}/{route}'.encode()
        connection.send(nack)
        connection.close()

    def send_interest(self, route):
        routers_to_delete = []
        message = f'INTEREST {route} '.encode()
        message_with_pk = message + self.public_key.save_pkcs1('PEM')
        for router in self.routers:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.connect((router.host, router.port))
                    print(f'Sending interest {message} to router {router.name}')
                    s.send(message_with_pk)
                    data = s.recv(1024)
                    if data.startswith('NACK'.encode()):
                        continue
                    else:
                        self.process_interest_response(data)
                        self.remove_routers(routers_to_delete)
                        return
                except Exception as e:
                    print(f'Error while trying to send interest: {e}')
                    routers_to_delete.append(router)
        print('unable to send interest')
        self.remove_routers(routers_to_delete)

    def process_interest_response(self, data):
        decrypted_data = rsa.decrypt(data, self.private_key)
        message_parts = decrypted_data.decode('utf-8').split(' ')
        print(message_parts[2])
        self.location = message_parts[2]
        pass


    def remove_routers(self, routers_to_delete):
        for router in routers_to_delete:
            try:
                print("REMOVING NODE", router)
                self.routers.remove(router)
            except Exception:
                print("ERROR IN REMOVING NODE")

    def check_safety(self):
        while True:
            self.send_interest(f'Satellite1/ship_safety/{self.name}')
            time.sleep(10)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', help='Name of the router', type=str)
    parser.add_argument('--loc', help='Location where the ship starts', type=str)
    args = parser.parse_args()
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    ship = Ship(host, MY_PORT, args.name, args.loc, ['location'])
    global joining
    t1 = threading.Thread(target=ship.join_network)
    t1.start()
    time.sleep(5)
    joining = False
    t1.join()
    t2 = threading.Thread(target=ship.listen_to_broadcasts)
    t3 = threading.Thread(target=ship.listen_to_interests)
    t4 = threading.Thread(target=ship.check_safety)
    t2.start()
    t3.start()
    t4.start()




if __name__ == '__main__':
    main()
