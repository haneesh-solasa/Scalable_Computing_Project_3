import argparse
import socket
import time
import traceback

ROUTER_PORT = 33888

def send_interest(ship_name):
    
    #Need the information of Router. For now hardcoding it.
    router_info = {('10.35.70.6', ROUTER_PORT)}

    for router in router_info:
        try:
            socket_1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_1.connect(router)
            message = ship_name + '/' + 'summary'
            socket_1.send(message.encode())
            print("Ship Name sent : Waiting for summary information of ship")
            acknowledgement = socket.recv(1024)
            print("Acknowledgement", acknowledgement)
            socket_1.close()
        except:
            print("Could not connect to the router")

def recv_data():
    socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    socket2.bind((host,ROUTER_PORT))
    socket2.listen(5)
    while True:
        conn, addr = socket2.accept()
        summary = conn.recv(1024)
        summary_info = summary.decode('utf-8')
        print("Ship Summary: ",summary_info)
        action = call_action(summary_info)

        send_to_router(conn,addr[0],action)
        conn.close()
        time.sleep(5)

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
    while True:
        parser = argparse.ArgumentParser()
        parser.add_argument('--shipname', help='Which Ship do you want to communicate? Carrier/Destroyer/Cruiser', required=True)
        args = parser.parse_args()


    
        Ship_names=['carrier','destroyer','cruiser']

        if args.shipname.lower() not in  Ship_names:
            print("Which Ship do you want to communicate? Carrier/Destroyer/Cruiser")
            exit(1)
        else:
            ship_name = args.shipname
            ship_name_lower = args.shipname.lower()
        
        send_interest(ship_name_lower)
        time.sleep(10)
        recv_data()

if __name__ == '__main__':
    main()


        