import socket
import threading
import time
import pygtrie
import json

ROUTER_PORT = 33301    # Port for listening to other peers
BCAST_PORT = 33255     # Port for broadcasting own address

routes = pygtrie.StringTrie()
pending_interests = {}
packet_cache = {}
stop_threads = False

def filter_ips(route):
    if bool(routes.longest_prefix(route)):
        return routes.longest_prefix(route).value


def parse_interest(interest):
    inter = interest.split("/")
    return inter[len(inter)-1]


def send_nack_for_interest(interest):
     nack = f'NACK {interest}'
     for connection in pending_interests[interest]:
        connection.send(nack.encode('UTF_8'))
        connection.close()


def send_back_to_interested_nodes(message, interest):
    for connection in pending_interests[interest]:
        print(f"Sending data for interest: {interest}")
        connection.send(message)
        connection.close()
    del pending_interests[interest]


def update_routes(peer):
    for route_node in routes.prefixes(peer.name):
        route = route_node.key.split('/')[1]
        if route not in peer.actions:
            routes[route].remove(peer)
    for action in peer.actions:
        route = f'{peer.name}/{action}'
        if route in routes:
           routes[route].add(peer)
        else:
            routes[route] = set()
            routes[route].add(peer)
    print("Current router table state: ", routes.keys())


class Peer:
    def __init__(self, type, name, host, port, actions):
        self.type = type
        self.name = name
        self.host = host
        self.port = port
        self.actions = actions

    def __repr__(self):
        return f'Node type: {self.type}, name: {self.name}, address: {self.host}:{self.port}, available actions: {self.actions}'

    def __eq__(self, other):
        return self.type == other.type and self.name == other.name and self.host == other.host and self.port == other.port

    def __hash__(self):
        return hash((self.type, self.name, self.host, self.port))


class Router:
    def __init__(self, host, port, name):
        self.host = host
        self.port = port
        self.peers = set()
        self.name = name
        self.connecting = True


    def join_network(self):
        """Broadcast the host IP."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(0.5)
        message = f'ROUTER {self.name} {self.host} {self.port}'.encode('utf-8')
        print("Joining network with message: ", message)
        s.sendto(message, ('<broadcast>', BCAST_PORT))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
            s2.bind((self.host, self.port))
            s2.listen(5)
            s2.settimeout(1)
            while self.connecting:
                conn, addr = s2.accept()
                connection_thread = threading.Thread(target=self.process_join_response(), args=conn)
                connection_thread.start()
        s.close()

    def process_join_response(self, connection):
        data = connection.recv(1024)
        data_message = data.decode('utf-8')
        type = data_message[0]
        name = data_message[1]
        host = data_message[2]
        port = int(data_message[3])
        if len(data_message) > 4:
            unparsed_actions = data_message[4]
            actions = set(unparsed_actions.lower().split('|'))
        else:
            actions = ''
        peer = Peer(type, name.lower(), host, port, actions)
        if peer not in self.peers:
            self.peers.add(peer)
            print('Known peers:', self.peers)
            update_routes(peer)
        else:
            print('Known peer connected, updating actions')
            self.peers.remove(peer)
            self.peers.add(peer)
            print('Currently known peers:', self.peers)
        connection.close()


    def listen_to_broadcasts(self):
        """Update peers list on receipt of their address broadcast."""
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                socket.IPPROTO_UDP)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client.bind(("", BCAST_PORT))
        print('listening to broadcasts...')
        while not stop_threads:
            try:
                data, _ = client.recvfrom(1024)
                print("received message:", data.decode('utf-8'))
                data = data.decode('utf-8')
                data_message = data.split(' ')
                type = data_message[0]
                name = data_message[1]
                host = data_message[2]
                port = int(data_message[3])
                if len(data_message) > 4:
                    unparsed_actions = data_message[4]
                    actions = set(unparsed_actions.lower().split('|'))
                else:
                    actions = ''
                peer = Peer(type, name.lower(), host, port, actions)
                if peer not in self.peers:
                    self.peers.add(peer)
                    print('Known peers:', self.peers)
                    update_routes(peer)
                else:
                    print('Known peer connected, updating actions')
                    self.peers.remove(peer)
                    self.peers.add(peer)
                    print('Currently known peers:', self.peers)
                self.respond_to_new_node(peer)
                time.sleep(2)
            except KeyboardInterrupt:
                client.close()
                break
            except Exception as e:
                print(f'Exception occured while listening to broadcasts: {e}')
        client.close()
        print('Stopping')

    def receive_interests(self):
        """Listen on own port for other peer data."""
        print("listening for interest data")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.port))
        s.listen(5)
        while not stop_threads:
            try:
                conn, addr = s.accept()
                connection_thread = threading.Thread(target=self.process_interest_connection, args=(conn, addr))
                connection_thread.start()
                time.sleep(1)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f'Exception occured while receiving interest: {e}')
        s.close()

    def process_interest_connection(self, connection, address):
        print("addr: ", address[0])
        data = connection.recv(1024)
        interest = data.decode('utf-8')
        route = interest.split[' '][0]
        print(f"Received interest: {interest}")
        if interest.startswith('peers'):
            self.return_peers(connection)
        else :
            if interest in pending_interests:
                pending_interests[interest].append(connection)
            else:
                pending_interests[interest] = [connection]
                filtered_ips = filter_ips(route)
                self.send_interest(filtered_ips, interest)

    def send_interest(self, possible_peers, interest):
        for peer in possible_peers:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((peer.host, peer.port))
                    print(f"Sending interest to: {peer.host}, {peer.port}")
                    s.send(interest.encode('utf-8'))
                    data = s.recv(1024)
                    send_back_to_interested_nodes(data, interest)
                    return
            except Exception as e:
                print(f"Exception occured {e}, trying next peer if available")
                pass
        send_nack_for_interest(interest)

    def respond_to_new_node(self, peer):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((peer.host, peer.port))
            address_message = f'ROUTER {self.name} {self.host} {self.port}'
            s.send(address_message.encode('utf-8'))

    def return_peers(self, connection):
        message = f'PEERS ['
        for peer in self.peers:
            message += json.dumps(peer.__dict__) + ', '
        message = message.removesuffix(', ') + ']'
        connection.send(message.encode())
        connection.close()

    def fetch_peers(self):
        while not stop_threads:
            peers_to_add = []
            for peer in self.peers:
                if peer.type == 'ROUTER':
                    fetched_peers = self.send_peers_request(peer)
                    for possible_peer in fetched_peers:
                        if not possible_peer in self.peers:
                            peers_to_add.append(possible_peer)
            for peer in peers_to_add:
                self.peers.add(peer)
                update_routes(peer)
            time.sleep(15)

    def send_peers_request(self, peer):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((peer.host, peer.port))
            s.send('peers'.encode())
            data = s.recv(2048)
            raw = data.decode('utf-8')
            fetched_peers_json = json.loads(' '.join(raw.split(' ')[1:]))
            fetched_peers_decoded = []
            for peer_json in fetched_peers_json:
                peer = Peer(peer_json.type, peer_json.name, peer_json.host, peer_json.port, peer_json.actions)
                fetched_peers_decoded.append(peer)
            return fetched_peers_decoded


    def remove_node(self, route, command):
        try:
            print("REMOVING NODE", route)
            if route in routes[command]:
                routes[command].remove(route)
            print("UPDATED MAP DICT", routes)
        except:
            print("ERROR IN REMOVING NODE")


def main():
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    router = Router(host, ROUTER_PORT, 'router1')
    t1 = threading.Thread(target=router.listen_to_broadcasts)
    t2 = threading.Thread(target=router.receive_interests)
    t3 = threading.Thread(target=router.fetch_peers)
    router.join_network()
    time.sleep(10)
    t1.start()
    t2.start()
    t3.start()
if __name__ == '__main__':
    main()
