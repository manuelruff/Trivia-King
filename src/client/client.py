import socket
import select
import sys

# Constants
UDP_PORT = 13117
BUFFER_SIZE = 1024
SERVER_IP = "172.1.0.4"
TCP_PORT = 5678


def listen_for_offers():
    print("Client started, listening for offer requests...")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind(("", UDP_PORT))

        while True:
            data, addr = udp_socket.recvfrom(BUFFER_SIZE)
            if data:
                print(f"Received offer from server \"Mystic\" at address {addr[0]}, attempting to connect...")
                global TCP_PORT
                TCP_PORT = int.from_bytes(data[-2:], byteorder='big')  # Assuming the last 2 bytes contain the TCP port
                return addr[0]  # Return the server IP to connect via TCP


def connect_to_server(server_ip):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
        try:
            tcp_socket.connect((server_ip, TCP_PORT))
            print("Connected successfully to the server.")
            handle_server_messages(tcp_socket)
        except socket.error as e:
            print("Error connecting to the server:", e)
            listen_for_offers()


def handle_server_messages(tcp_socket):
    while True:
        ready_sockets, _, _ = select.select([tcp_socket, sys.stdin], [], [])
        for sock in ready_sockets:
            if sock == tcp_socket:
                message = sock.recv(BUFFER_SIZE).decode("utf-8")
                if not message:
                    print("Server disconnected, listening for offer requests...")
                    tcp_socket.close()
                    return listen_for_offers()
                print(message)
            else:
                msg = sys.stdin.readline()
                tcp_socket.sendall(msg.encode())


def main():
    server_ip = listen_for_offers()
    connect_to_server(server_ip)


if __name__ == "__main__":
    main()
