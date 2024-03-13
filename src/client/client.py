import socket
import threading
import random

# Constants
UDP_PORT = 13117
BUFFER_SIZE = 1024
TCP_SOCKET = None
stop_input_event = threading.Event()
NAMES = ["Luffy", "Zoro", "Nami", "Usopp", "Sanji", "Chopper", "Robin", "Franky", "Brook", "Monica", "Ross", "Rachel", "Chandler", "Joey", "Phoebe"]
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
    try:
        default_name = random.choice(NAMES)
        conn.send(default_name.encode())
    except Exception as e:
        print(f"Error during login: {e}")

# def handle_server_messages():
#     global TCP_SOCKET  # Declare TCP_SOCKET as a global variable
#     while True:
#         try:
#             hello_msg = TCP_SOCKET.recv(BUFFER_SIZE).decode("utf-8")
#             msg = TCP_SOCKET.recv(BUFFER_SIZE).decode("utf-8")
#             if not hello_msg:
#                 print("Server disconnected, listening for offer requests...")
#                 TCP_SOCKET.close()
#                 TCP_SOCKET = None  # Reset TCP_SOCKET to None
#                 return
#             print(msg)
#             # ans = input("Please enter your answer: ")
#             # TCP_SOCKET.send(ans.encode())
#             input_thread = threading.Thread(target=handle_user_input, args=(), daemon=True)
#             input_thread.start()
#             if "enough" in msg:
#                 print("Received 'enough' from the server. Stopping input.")
#                 stop_input_event.set()  # Signal to stop user input after printing the message
#                 break  # Exit the loop after handling "enough"
#             if "Congratulations to the winner:" in msg:
#                 raise socket.error
#         except socket.error:
#             print("Server disconnected, listening for offer requests...")
#             TCP_SOCKET.close()
#             TCP_SOCKET = None  # Reset TCP_SOCKET to None
#             return

# all the "private" handle messages
def handle_enough():
    print("Received 'enough' from the server. Stopping input.")
    stop_input_event.set()
def handle_winner():
    print("Congratulations message received. Exiting.")
    raise socket.error  # Or handle the winning case as needed
def handle_question():
    """Function to capture and send user input in a separate thread."""
    global TCP_SOCKET
    if not stop_input_event.is_set():
        try:
            user_input = input("Please enter your answer: \n")
            # Check if stop signal is received before sending input
            if not stop_input_event.is_set():
                TCP_SOCKET.send(user_input.encode())
        except Exception as e:
            print(f"Error sending input to server: {e}")
def handle_server_messages():
    global TCP_SOCKET
    while True:
        try:
            msg = TCP_SOCKET.recv(BUFFER_SIZE).decode("utf-8")
            if not msg:
                print("Server disconnected, listening for offer requests...")
                TCP_SOCKET.close()
                TCP_SOCKET = None
                return
            # Handle different cases based on message content
            if "Welcome" in msg:
                print(msg)
            elif "enough" in msg:
                print(msg)
                handle_enough()
            elif "Congratulations to the winner:" in msg:
                print(msg)
                handle_winner()
            else:
                # if the message is the question
                ans_thread = threading.Thread(target=handle_question(), args=(), daemon=True)
                ans_thread.start()
                ans_thread.join()

        except socket.error:
            print("Server disconnected, listening for offer requests...")
            TCP_SOCKET.close()
            TCP_SOCKET = None
            return

def main():
    server_ip, tcp_port = listen_for_offers()
    connect_to_server(server_ip, tcp_port)
    # Create and start thread for handling server messages
    handle_server_messages()

if __name__ == "__main__":
    main()
