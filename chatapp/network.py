from scapy.all import ARP, Ether, srp
from contextlib import closing
import socket, threading

def find_client(interface, ports: (int, int)):
    'finds a client on the network using the interface and ports provided.'
    
    arp = ARP(pdst=interface)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether/arp
    
    result = srp(packet, timeout=3, verbose=0)[0]

    clients = []

    for sent, received in result:
        clients.append(received.psrc)

    clients = check_ports(clients, ports[0], ports[1])

    return clients


def check_socket(host: str, port: int, clients: [(str, int)]) -> None:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            if sock.connect_ex((host, port)) == 0:
                clients.append((host, port))
    
def check_ports(clients: [str], port_low, port_high) -> [(str, int)]:
        'checks if port is open on clients'

        open_clients = []

        # Check all clients in parallel

        threads = []
        for client in clients:
            for port in range(port_low, port_high + 1):
                thread = threading.Thread(target=check_socket, args=(client, port, open_clients))
                thread.start()
                threads.append(thread)
        
        for thread in threads:
            thread.join()
        
        return open_clients