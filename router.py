import socket
import threading
import time

ROUTER_PORT = 33301    # Port for listening to other peers
BCAST_PORT = 33255     # Port for broadcasting own address

map_dict = {}
pending_interests = {}
packet_cache = {}


def filter_ips(route):
    if route in map_dict.keys():
        return map_dict[route]


def parse_interest(self, interest):
    inter = interest.split("/")
    return inter[len(inter)-1]


def send_nack_for_interest(self, interest):
     nack = f'NACK {interest}'
     for connection in pending_interests[interest]:
        connection.send(nack.encode('UTF_8'))
        connection.close()


def send_back_to_interested_nodes(self, message, interest):
    for connection in pending_interests[interest]:
        print(f"Sending data for interest: {interest}")
        connection.send(message.encode('utf-8'))
        connection.close()


def update_routes(self, peer):
    for action in peer.actions:
        route = f'{peer.name}/{action}'
        if route in map_dict:
           map_dict[route].add(peer)
        else:
            map_dict[route] = set(peer)
    print("Current router table state: ", map_dict)


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

    def broadcastIP(self):
        """Broadcast the host IP."""
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                socket.IPPROTO_UDP)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        server.settimeout(0.5)
        message = f'HOST {self.host} PORT {self.port}'.encode('utf-8')
        print("What is the message", message)
        while True:
            server.sendto(message, ('<broadcast>', BCAST_PORT))
            # print("Host IP sent!")
            print(f"Broadcasting my IP {self.host}:{self.port}")
            time.sleep(10)

    def listen_to_broadcasts(self):
        """Update peers list on receipt of their address broadcast."""
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,
                                socket.IPPROTO_UDP)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client.bind(("", BCAST_PORT))
        print('listening to broadcasts...')
        while True:
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
                self.update_routes(peer)
            else:
                print('Known peer connected, updating actions')
                self.peers.remove(peer)
                self.peers.add(peer)
                print('Currently known peers:', self.peers)
            self.respond_to_new_node(peer)
            time.sleep(2)

    def receive_interests(self):
        """Listen on own port for other peer data."""
        print("listening for interest data")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.port))
        s.listen(5)
        while True:
            conn, addr = s.accept()
            connection_thread = threading.Thread(target=self.process_interest_connection, args=(conn, addr))
            connection_thread.start()
            time.sleep(1)
        s.close()

    def process_interest_connection(self, connection, address):
        print("addr: ", address[0])
        data = connection.recv(1024)
        interest = data.decode('utf-8')
        print(f"Received interest: {interest}")
        if interest in pending_interests:
            pending_interests[interest].append(connection)
        else:
            pending_interests[interest] = [connection]
            filtered_ips = filter_ips(interest)
            self.send_interest(filtered_ips, interest)

    def send_interest(self, possible_peers, interest):
        for peer in possible_peers:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((peer.host, peer.port))
                    print(f"Sending interest to: {peer.host}, {peer.port}")
                    s.send(interest.encode('utf-8'))
                    data = s.recv(1024)
                    parsed_data = data.decode('utf-8')
                    print(parsed_data)
                    self.send_back_to_interested_nodes(parsed_data, interest)
                    return
            except Exception as e:
                print(f"Exception occured {e}, trying next peer if available")
                pass
        self.send_nack_for_interest(interest)

    def respond_to_new_node(self, peer):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((peer.host, peer.port))
            address_message = f'ROUTER {self.name} {self.host} {self.port}'
            s.send(address_message.encode('utf-8'))

    def remove_node(self, node, command):
        try:
            print("REMOVING NODE", node)
            if node in map_dict[command]:
                map_dict[command].remove(node)
            print("UPDATED MAP DICT", map_dict)
        except:
            print("ERROR IN REMOVING NODE")


def main():
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    router = Router(host, ROUTER_PORT, 'router1')
    t1 = threading.Thread(target=router.listen_to_broadcasts)
    t2 = threading.Thread(target=router.receive_interests)
    t1.start()
    t2.start()


if __name__ == '__main__':
    main()
