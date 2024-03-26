import signal
import socket
import threading
import random
import select
import sys
import os

# Constants
UDP_PORT = 13117
BUFFER_SIZE = 1024
TCP_SOCKET = None
stop_input_event = threading.Event()
NAMES = ["Luffy", "Zoro", "Nami", "Usopp", "Sanji", "Chopper", "Robin", "Franky", "Brook", "Monica", "Ross", "Rachel", "Chandler", "Joey", "Phoebe"]
USER_INPUT=""
ANS_THREAD= None
CLIENT_NAME = None
def colored_print(text, color='\033[92m'):
    print(color + text + '\033[0m')

def listen_for_offers():
    colored_print("Client started, listening for offer requests...")
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind(("", UDP_PORT))
        while True:
            colored_print("Server successfully bound to UDP")
            data, addr = udp_socket.recvfrom(BUFFER_SIZE)
            if data:
                magic_cookie = data[:4]
                message_type = data[4:5]
                if magic_cookie == b'\xab\xcd\xdc\xba' and message_type == b'\x02':
                    server_name_raw = data[5:37]
                    server_name = server_name_raw.decode('utf-8').rstrip('\x00')
                    tcp_port = int.from_bytes(data[-2:], byteorder='big')
                    colored_print(f"Received offer from server \"{server_name}\" at address {addr[0]}, attempting to connect...")
                    return addr[0], tcp_port

def connect_to_server(server_ip, tcp_port):
    global TCP_SOCKET  # Declare TCP_SOCKET as a global variable
    TCP_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        colored_print(f"Connecting to the server {server_ip} on port {tcp_port}")
        TCP_SOCKET.connect((server_ip, tcp_port))
        colored_print("Connected successfully to the server.")
        login(TCP_SOCKET)
        colored_print("Successful login name sent to server")
    except socket.error as e:
        colored_print(f"Error connecting to the server: {e}")

def login(conn):
    global CLIENT_NAME
    if CLIENT_NAME is None:
        try:
            CLIENT_NAME = random.choice(NAMES)
            conn.send(CLIENT_NAME.encode())
        except Exception as e:
            colored_print(f"Error during login: {e}")
    else:
        conn.send(CLIENT_NAME.encode())


def handle_enough():
    # colored_print("Received 'enough' from the server. Stopping input.")
    stop_input_event.set()
    #ANS_THREAD.terminate()
    # handle_question()
def handle_winner():
    colored_print("Congratulations message received. Exiting.")
    raise socket.error  # Or handle the winning case as needed
def get_user_input():
    """Function to get user input in a separate thread."""
    global USER_INPUT
    # Read input non-blockingly
    while not stop_input_event.is_set():
        try:
        #ready, _, _ = select.select([sys.stdin], [], [], 10)  # Check if input is ready
            # print("this is the ready input: ",ready)
            #colored_print("please enter your answer:\n")
            USER_INPUT = input()
            stop_input_event.set()  # Signal to stop user input after colored_printing the message
            #USER_INPUT = input("Please enter your answer: \n")
            return
        except:
            stop_input_event.set()  # Signal to stop user input after colored_printing the message
            USER_INPUT=""
            return
def handle_question():
    """Function to capture and send user input in a separate thread."""
    global TCP_SOCKET, USER_INPUT
    # clear stop input, we just started the question
    stop_input_event.clear()
    colored_print("please enter your answer:\n")
    # Start the thread to get user input
    user_input_thread = threading.Thread(target=get_user_input)
    user_input_thread.start()

    # Wait for the stop signal or until user input is received
    stop_input_event.wait()
    user_input_thread.join()
    try:
        #send user input to the server
        TCP_SOCKET.send(USER_INPUT.encode())
    except Exception as e:
        colored_print(f"Error sending input to server: {e}")
def handle_server_messages():
    global TCP_SOCKET,ANS_THREAD
    while True:
        try:
            msg = TCP_SOCKET.recv(BUFFER_SIZE).decode("utf-8")
            if not msg:
                colored_print("Server disconnected, listening for offer requests...")
                TCP_SOCKET.close()
                TCP_SOCKET = None
                return
            # Handle different cases based on message content

            if "Welcome" in msg:
                colored_print(msg)
                continue
            elif "enough" in msg:
                # colored_print(msg)
                handle_enough()
                continue
            elif "Congratulations to the winner:" in msg:
                colored_print(msg)
                handle_winner()
                continue
            else:
                colored_print(msg)
                # if the message is the question
                ANS_THREAD = threading.Thread(target=handle_question, args=())
                ANS_THREAD.start()
                # ans_thread = threading.Thread(target=handle_question, args=())
                # ans_thread.start()


        except socket.error:
            colored_print("Server disconnected, listening for offer requests...")
            TCP_SOCKET.close()
            TCP_SOCKET = None
            return

def main():
    global ANS_THREAD
    while True:
        server_ip, tcp_port = listen_for_offers()
        connect_to_server(server_ip, tcp_port)
        # Create and start thread for handling server messages
        handle_server_messages()
        if ANS_THREAD is not None:
            ANS_THREAD.join()


if __name__ == "__main__":
    main()
