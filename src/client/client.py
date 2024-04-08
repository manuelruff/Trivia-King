import socket
import threading
import random
import keyboard

# Constants
UDP_PORT = 13117
BUFFER_SIZE = 1024
TCP_SOCKET = None
stop_input_event = threading.Event()
NAMES = ["Luffy", "Zoro", "Nami", "Usopp", "Sanji", "Chopper", "Robin", "Franky", "Brook", "Monica", "Ross", "Rachel",
         "Chandler", "Joey", "Phoebe", "Yossi", "Gal", "Omri", "Manuel", "Sydney", "Sweeney",
         "Goku", "Vegeta", "Piccolo", "Gohan", "Krillin", "Trunks", "Goten", "Bulma", "Chi-Chi", "Frieza"]
COLORS = ['\033[92m', '\033[94m', '\033[95m', '\033[96m', '\033[32m', '\033[34m', '\033[35m', '\033[36m', '\033[92m',
          '\033[94m', '\033[95m', '\033[96m']
USER_INPUT = ""
ANS_THREAD = None
CLIENT_NAME = None
CLIENT_COLOR = None


def colored_print(text):
    """
    This function prints the provided text in a random color from the COLORS list.
    :param text:
    """
    global CLIENT_COLOR
    if CLIENT_COLOR is None:
        CLIENT_COLOR = random.choice(COLORS)
        print(CLIENT_COLOR + text + '\033[0m')
    else:
        print(CLIENT_COLOR + text + '\033[0m')

def listen_for_offers():
    """
    This function listens for incoming UDP broadcast messages containing offer
    requests from game servers. When an offer request is received, the function
    validates the message and extracts the server name and TCP port. It then
    attempts to connect to the game server.
    @return: tuple: A tuple containing the IP address and TCP port of the game server
               to which a connection will be attempted.
    """
    # Print a message indicating that the client is listening for offer requests
    colored_print("Client started, listening for offer requests...")

    # Create a UDP socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        # Enable broadcast and reuse address options for the socket
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind the socket to any available address and the specified UDP port
        udp_socket.bind(("", UDP_PORT))

        # Continuously listen for offer requests
        while True:
            # Print a message indicating that the server successfully bound to UDP
            # colored_print("Server successfully bound to UDP")

            # Receive data and address from the socket
            data, addr = udp_socket.recvfrom(BUFFER_SIZE)

            # If data is received
            if data:
                # Extract magic cookie and message type from the received data
                magic_cookie = data[:4]
                message_type = data[4:5]

                # Check if the received data is a valid offer message
                if magic_cookie == b'\xab\xcd\xdc\xba' and message_type == b'\x02':
                    # Extract server name and TCP port from the offer message
                    server_name_raw = data[5:37]
                    server_name = server_name_raw.decode('utf-8').rstrip('\x00')
                    tcp_port = int.from_bytes(data[-2:], byteorder='big')

                    # Print a message indicating the offer received and attempt to connect to the server
                    colored_print(
                        f"Received offer from server \"{server_name}\" at address {addr[0]}, attempting to connect...")

                    # Return the server address and TCP port for connection
                    return addr[0], tcp_port


def connect_to_server(server_ip, tcp_port):
    """
    This function attempts to establish a TCP connection to a game server
    identified by the provided IP address and TCP port. Upon successful
    connection, it sends login information to the server.

    @param server_ip: (str): The IP address of the game server.
    @param tcp_port: (int): The TCP port of the game server.
    """
    global TCP_SOCKET  # Declare TCP_SOCKET as a global variable
    TCP_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Print a message indicating the attempt to connect to the server
        #colored_print(f"Connecting to the server {server_ip} on port {tcp_port}")

        # Connect to the server using the provided IP address and TCP port
        TCP_SOCKET.connect((server_ip, tcp_port))

        # Print a message indicating successful connection to the server
        colored_print("Connected successfully to the server.")

        # Send login information to the server
        login(TCP_SOCKET)

        # Print a message indicating successful login name sent to the server
        #colored_print("Successful login name sent to server")
    except socket.error as e:
        # Print an error message if connection to the server fails
        colored_print(f"Error connecting to the server: {e}")


def login(conn):
    """
    This function sends the client's name to the game server for login. If the
    global variable CLIENT_NAME is not set, a random name is generated from the
    NAMES list and sent to the server. If CLIENT_NAME is already set, it sends
    the existing name to the server.
    @param conn: (socket.socket): The socket connection to the game server.
    """
    global CLIENT_NAME  # Declare CLIENT_NAME as a global variable
    if CLIENT_NAME is None:
        try:
            # Generate a random client name if CLIENT_NAME is not set
            CLIENT_NAME = random.choice(NAMES)

            # Print the selected client name
            colored_print(f"******************** Name: {CLIENT_NAME} ********************")

            # Send the client name to the server
            conn.send(CLIENT_NAME.encode())
        except Exception as e:
            # Print an error message if an exception occurs during login
            colored_print(f"Error during login: {e}")
    else:
        # Send the existing client name to the server if it's already set
        conn.send(CLIENT_NAME.encode())


def handle_server_messages():
    """
    This function continuously listens for messages from the game server over
    the established TCP connection. It handles various types of messages such
    as welcome messages, messages indicating that enough answers have been received,
    messages indicating correct answers, messages announcing the winner, and questions.
    """
    global TCP_SOCKET, ANS_THREAD, GAME_WON
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
            elif "enough" in msg:
                # colored_print(msg)
                handle_enough()
            elif "is correct!" in msg:
                colored_print(msg)
            elif "Congratulations to the winner:" in msg:
                colored_print(msg)
            elif "Leaderboard:" in msg:
                print(msg)
                handle_winner()
            # handle questions
            else:
                colored_print(msg)
                # if the message is the question
                # clear stop input, we just started the question
                stop_input_event.clear()
                ANS_THREAD = threading.Thread(target=handle_question, args=())
                ANS_THREAD.start()


        except socket.error:
            colored_print("Server disconnected, listening for offer requests...")
            TCP_SOCKET.close()
            TCP_SOCKET = None
            return


def handle_enough():
    """
    This function is called whenever the server indicates that enough answers have been received.
    """
    stop_input_event.set()


def handle_winner():
    """
    This function is called whenever a winner is announced by the server.
    """
    # colored_print("Congratulations message received. Exiting.")
    raise socket.error  # Or handle the winning case as needed


def handle_question():
    """
    This function is called whenever a question is received from the server. It
    """
    # the function handle with questions it gets from the server
    global TCP_SOCKET, USER_INPUT
    colored_print("please enter your answer:\n")
    keyboard.wait(10)
    stop_input_event.set()


# the function that responsible for the client answer typing
def on_key_event(event):
    """
    This function is called whenever a key is pressed. It sends the key to the server.
    :param event: the evernt that happens
    """
    if stop_input_event.is_set():
        return
    try:
        TCP_SOCKET.send(event.name.encode())
        stop_input_event.set()
    except Exception as e:
        colored_print(f"Error sending input to server: {e}")


def main():
    """
    The main function of the client program. It listens for offer requests from game servers,
    """
    global ANS_THREAD
    # Register the callback function for key events
    keyboard.on_press(on_key_event)
    while True:
        ANS_THREAD = None
        server_ip, tcp_port = listen_for_offers()
        connect_to_server(server_ip, tcp_port)
        # the main logic with the server
        handle_server_messages()


if __name__ == "__main__":
    main()
