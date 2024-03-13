import socket

# Constants
UDP_PORT = 13117
BUFFER_SIZE = 1024
TCP_SOCKET = None  # Initialize TCP_SOCKET as a global variable

def listen_for_offers():
    print("Client started, listening for offer requests...")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind(("", UDP_PORT))
        while True:
            print("Server successfully bound to UDP")
            data, addr = udp_socket.recvfrom(BUFFER_SIZE)
            if data:
                magic_cookie = data[:4]
                message_type = data[4:5]
                if magic_cookie == b'\xab\xcd\xdc\xba' and message_type == b'\x02':
                    server_name_raw = data[5:37]
                    server_name = server_name_raw.decode('utf-8').rstrip('\x00')
                    tcp_port = int.from_bytes(data[-2:], byteorder='big')
                    print(f"Received offer from server \"{server_name}\" at address {addr[0]}, attempting to connect...")
                    return addr[0], tcp_port

def connect_to_server(server_ip, tcp_port):
    global TCP_SOCKET  # Declare TCP_SOCKET as a global variable
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        print(f"Connecting to the server {server_ip} on port {tcp_port}")
        tcp_socket.connect((server_ip, tcp_port))
        TCP_SOCKET = tcp_socket
        print("Connected successfully to the server.")
        login(TCP_SOCKET)
        print("Successful login name sent to server")
    except socket.error as e:
        print(f"Error connecting to the server: {e}")

def login(conn):
    username = input("Please enter username: \n")
    conn.send(username.encode())

def handle_server_messages():
    global TCP_SOCKET  # Declare TCP_SOCKET as a global variable
    while True:
        try:
            message = TCP_SOCKET.recv(BUFFER_SIZE).decode("utf-8")
            if not message:
                print("Server disconnected, listening for offer requests...")
                TCP_SOCKET.close()
                TCP_SOCKET = None  # Reset TCP_SOCKET to None
                return
            print(message)
            ans = input("Please enter your answer: ")
            TCP_SOCKET.send(ans.encode())
        except socket.error:
            print("Server disconnected, listening for offer requests...")
            TCP_SOCKET.close()
            TCP_SOCKET = None  # Reset TCP_SOCKET to None
            return

def main():
    server_ip, tcp_port = listen_for_offers()
    connect_to_server(server_ip, tcp_port)
    handle_server_messages()

if __name__ == "__main__":
    main()
