import socket
import select
import sys

# Constants
UDP_PORT = 13117
BUFFER_SIZE = 1024

def listen_for_offers():
    print("Client started, listening for offer requests...")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:  # Create a UDP socket
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind(("", UDP_PORT))  # Listen on all interfaces for UDP broadcasts on UDP_PORT
        while True:
            print("server successfully bind to UDP")
            data, addr = udp_socket.recvfrom(BUFFER_SIZE)  # Wait for a broadcast message
            #print("the data recived is: ", data)
            if data:
                # Ensure the data begins with the "magic cookie" and message type for a valid offer
                magic_cookie = data[:4]
                message_type = data[4:5]
                if magic_cookie == b'\xab\xcd\xdc\xba' and message_type == b'\x02':
                    # Extract the name of the server
                    server_name_raw = data[5:37]  # Extract the server name part
                    # Decode the server name, remove trailing null bytes, and decode as UTF-8
                    server_name = server_name_raw.decode('utf-8').rstrip('\x00')
                    # Extract TCP port from the message; adjust slice indices as per your protocol
                    tcp_port = int.from_bytes(data[-2:], byteorder='big')
                    print(tcp_port, "this is the tcp port")
                    print(f"Received offer from server \"{server_name}\" at address {addr[0]}, attempting to connect...")
                    return addr[0], tcp_port  # Return server IP and TCP port for further processing



def connect_to_server(server_ip, tcp_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
        try:
            print(f"Connecting to the server {server_ip} on port {tcp_port}")
            tcp_socket.connect((server_ip, tcp_port))
            print("Connected successfully to the server.")
            handle_server_messages(tcp_socket)
        except socket.error as e:
            print(f"Error connecting to the server: {e}")

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
    server_ip, tcp_port = listen_for_offers()  # Get server IP and port from UDP broadcast
    connect_to_server(server_ip, tcp_port)


if __name__ == "__main__":
    main()
