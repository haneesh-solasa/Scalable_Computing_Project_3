import socket
import threading
import time

ROUTER_PORT = 33301    # Port for listening to other peers
BCAST_PORT = 33255     # Port for broadcasting own address
INTEREST_PORT = 33310

map_dict = {}
pending_interests = {}
packet_cache = {}


def filter_ips(route):
    if route in map_dict.keys():
        return map_dict[route]


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
                actions = set(unparsed_actions.split('|'))
            else:
                actions = ''
            peer = Peer(type, name, host, port, actions)
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
        hostname = socket.gethostname()
        host = socket.gethostbyname(hostname)
        port = INTEREST_PORT
        s.bind((host, port))
        s.listen(5)
        s.setblocking(False)
        while True:
            conn, addr = s.accept()
            connection_thread = threading.Thread(target=self.process_interest_connection, args=(conn, addr))
            connection_thread.start()
            time.sleep(1)

    def process_interest_connection(self, connection, address):
        print("addr: ", address[0])
        print("connection: ", str(connection))
        data = connection.recv(1024)
        interest = data.decode('utf-8')
        print(f"Received interest: {interest}")
        if interest in pending_interests:
            pending_interests.append(connection)
        else:
            pending_interests[interest] = [connection]
            filtered_ips = self.filter_ips(interest)
            self.send_interest(filtered_ips, interest)

    def send_interest(self, possible_peers, interest):
        for peer in possible_peers:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((peer.host, peer.port))
                    print(f"Sending interest to: {peer.host}, {peer.port}")
                    s.send(interest.encode('utf-8'))
                    data = s.recv(1024)
                    self.send_back_to_interested_nodes(data, interest)
                    return
            except Exception:
                print("Exception occured, trying next peer if available")
                pass
        self.send_nack_for_interest(interest)

    def parse_interest(self, interest):
        inter = interest.split("/")
        return inter[len(inter)-1]

    def send_nack_for_interest(self, interest):
        nack = f'NACK {interest}'
        for connection in pending_interests[interest]:
            connection.send(nack.encode('UTF_8'))

    def send_back_to_interested_nodes(self, message, interest):
        for connection, address in pending_interests[interest]:
            print(f"Sending data for interest: {interest} back to: {address}")
            connection.send(message.encode('utf-8'))
            connection.close()

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


    """def route_to_pi(self, peer_list, command):
        #Send sensor data to all peers.
        sent = False
        # if command == 'ALERT':
        print("What is peer list and command :{} {}".format(peer_list, command))
        for peer in peer_list:
            print("What is peer inside peerlist", peer)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((peer, PEER_PORT))
                msg = command
                print("Idhar aaya kya", msg)
                s.send(msg.encode())
                print("Sent command", msg)
                sent = True
                ack = s.recv(1024)
                print("Acknowledgement received", ack)
                s.close()
                return ack
            except Exception:
                print("An exception occured")
                continue
   """             #self.remove_node(peer,command)

    def update_routes(self, peer):
        for action in peer.actions:
            route = f'{peer.name}/{action}'
            map_dict[route] = peer
        print("Current router table state: ", map_dict)


def main():
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    router = Router(host, ROUTER_PORT, 'router')
    t1 = threading.Thread(target=router.listen_to_broadcasts)
    t2 = threading.Thread(target=router.receive_interests)
    t1.start()
    t2.start()


if __name__ == '__main__':
    main()
