import socket
import threading
import time
import random
import queue

IP_ADDRESS = None
TCP_PORT = 20000
CLIENTS = []
CLIENT_NAMES = {}
QUESTIONS = {
    "Mount Everest is the tallest mountain in the world.": True,
    "The Great Wall of China is visible from space.": False,
    "The Pacific Ocean is the largest ocean on Earth.": True,
    "Auroras occur only at the North Pole.": False,
    "The Nile River is the longest river in the world.": True,
    "Sharks are mammals.": False,
    "The human body has four lungs.": False,
    "The capital of France is Paris.": True,
    "Oxygen is the most abundant element in the Earth's atmosphere.": False,
    "Diamonds are made of carbon.": True,
    "Mount Kilimanjaro is located in South America.": False,
    "The Statue of Liberty was a gift from France to the United States.": True,
    "The moon orbits the Earth once a month.": True,
    "A decagon has ten sides.": True,
    "The chemical symbol for water is H2O2.": False,
    "The human body has five senses.": True,
    "Mars is the largest planet in the solar system.": False,
    "The capital of Japan is Kyoto.": False,
    "The Earth is approximately 4.5 billion years old.": True,
    "Whales are fish.": False,
    "Photosynthesis is the process by which plants convert sunlight into energy.": True,
    "The Amazon Rainforest is located in Africa.": False,
    "Penguins can fly.": False,
    "The speed of light is approximately 300,000 kilometers per second.": True,
    "The Pythagorean theorem states that the square of the hypotenuse of a right triangle is equal to the sum of the squares of the other two sides.": True,
    "Saltwater freezes at a lower temperature than freshwater.": False,
    "The capital of Australia is Sydney.": False,
    "The human skeleton is made up of 206 bones.": True,
    "The Earth revolves around the sun.": True,
    "The chemical symbol for gold is Ag.": False
}
SERVER_NAME = "KaKi"
ANSWER_QUEUE = queue.Queue()
SERVER_SOCKETSERVER_SOCKET=None
GAME_READY_EVENT=None
TCP_THREAD=None
UDP_THREAD=None

def find_free_port(start_port, max_attempts=100):
    """
    Function to find a free port within a specified range of attempts.

    Args:
        start_port (int): The starting port number to begin the search.
        max_attempts (int, optional): Maximum number of attempts to find a free port.
                                       Defaults to 100.

    Returns:
        int: The first free port found within the specified range.

    Raises:
        OSError: If no free port is found within the specified range of attempts.
    """
    for port in range(start_port, start_port + max_attempts):
        try:
            # Attempt to bind to the current port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return port  # Return the port if binding is successful
        except OSError:
            pass
    # If no free port is found within the specified range of attempts, raise an OSError
    raise OSError("Unable to find a free port")

def handle_tcp_connection(client_socket, game_ready_event):
    """
    Function to handle TCP connections.

    Args:
        client_socket (socket.socket): The socket object representing the TCP connection.
        game_ready_event (threading.Event): Event indicating if the game is ready to start.
    """
    print("Server started, listening on IP address {}")
    print(f"TCP connection established with {client_socket.getpeername()}")
    # Add the client information to the list of connected clients
    CLIENTS.append((client_socket, client_socket.getpeername()))
    CLIENT_NAMES[client_socket.getpeername()] = client_socket.recvfrom(1024)[0].decode()
    print(f"Client {CLIENT_NAMES[client_socket.getpeername()]} has joined the game")
    # Wait for the game to be ready
    game_ready_event.wait()
    # Cancel the timeout after the loop
    SERVER_SOCKET.settimeout(None)
    # Your game logic goes here
    # Once the game is ready, you can proceed with the game
    start_game()
    # Close the connection
    client_socket.close()

def create_random_question():
    """
    Function to randomly select a question from the available questions.
    Returns:
        tuple: A tuple containing the randomly selected question and its answer.
    """
    global QUESTIONS  # Access the global variable containing the questions
    all_questions = list(QUESTIONS.keys())  # Get a list of all question
    rand_question = random.choice(all_questions)  # Choose a random question
    return (rand_question, QUESTIONS[rand_question])  # Return the chosen question and its answer

def check_correct(client_ans, ans):
    if ans == "T":
        if client_ans in ('t', '1', 'y'):
            return True
        else:
            return False
    else:
        if client_ans in ('f', '0', 'n'):
            return True
    return False

def receive_answers_from_client(client_socket):
    while True:
        try:
            answer = client_socket.recv(1024).decode().strip()
            if not answer:
                break
            ANSWER_QUEUE.put((client_socket.getpeername(), answer))
        except Exception as e:
            print(f"Error receiving answer from {client_socket.getpeername()}: {e}")
            break

def start_game():
    message = f"Welcome to the {SERVER_NAME} server, where we are answering trivia questions\n"
    count = 1
    for client in CLIENTS:
        message += f"Player {count}: {CLIENT_NAMES[client[1]]} \n"
        count += 1
    try:
        for client_socket, _ in CLIENTS:
            try:
                client_socket.send(message.encode('utf-8'))
            except Exception as e:
                print(f"Error sending message to {client_socket.getpeername()}: {e}")
        print(message)
    except Exception as e:
        print(f"Error sending message to clients: {e}")

    # flag for finishing game
    game_finished = False
    # Now we need to start sending questions
    while not game_finished:
        question, answer = create_random_question()
        # Send the question to everyone
        try:
            for client_socket, _ in CLIENTS:
                try:
                    client_socket.send(question.encode('utf-8'))
                except Exception as e:
                    print(f"Error sending message to {client_socket.getpeername()}: {e}")
            print(question)
        except Exception as e:
            print(f"Error sending question to clients: {e}")
        # We will empty the queue
        ANSWER_QUEUE.empty()
        for client in CLIENTS:
            # We will start a thread for each client to receive the answer
            threading.Thread(target=receive_answers_from_client, args=(client[0],)).start()
        # Wait for a correct answer
        timeout = 10  # Timeout in seconds
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                client_answer = ANSWER_QUEUE.get(timeout=timeout)
                if check_correct(client_answer[1], answer):
                    game_finished = True
                    break
            except queue.Empty:
                # No answer received within the timeout period
                print("No correct answer received within the timeout period")
                break
    # Send the correct answer to everyone
    try:
        message = f"{CLIENT_NAMES[client_answer[0]]} is correct! Alice wins!"
        for client_socket, _ in CLIENTS:
            try:
                client_socket.send(message.encode('utf-8'))
            except Exception as e:
                print(f"Error sending message to {client_socket.getpeername()}: {e}")
    except Exception as e:
        print(f"Error sending correct answer to clients: {e}")

def start_tcp_server():
    """
    Function to start the TCP server.

    Args:
        game_ready_event (threading.Event): Event indicating if the game is ready to start.
    """
    # Bind the socket to the specified IP address and port
    SERVER_SOCKET.bind((IP_ADDRESS, TCP_PORT))
    # Listen for incoming connections
    SERVER_SOCKET.listen(5)
    print(f"TCP Server started, listening on IP address {IP_ADDRESS}, port {TCP_PORT}")
    # Set the timeout for accepting connections
    SERVER_SOCKET.settimeout(10)

    # Accept and handle incoming connections for up to 10 seconds
    while True:
        # Accept incoming connections
        try:
            client_socket, client_address = SERVER_SOCKET.accept()
            print(f"New connection from {client_address}")
            # Start a new thread to handle the connection
            threading.Thread(target=handle_tcp_connection, args=(client_socket, GAME_READY_EVENT)).start()

        except socket.timeout:
            break
    # Cancel the timeout after the loop
    SERVER_SOCKET.settimeout(None)
    print("Game ready!")
    # If no new clients joined during the last 10 seconds, start the game
    GAME_READY_EVENT.set()

def send_udp_broadcast():
    """
    Function to send UDP broadcast with custom message format.
    """
    # Create a UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Enable broadcast
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Define the message format
    magic_cookie = b'\xab\xcd\xdc\xba'
    message_type = b'\x02'
    server_name_bytes = SERVER_NAME.encode('utf-8').ljust(32, b'\x00')  # Change "KaKi" to your desired server name
    server_port_bytes = TCP_PORT.to_bytes(2, byteorder='big')

    # Construct the message
    message = magic_cookie + message_type + server_name_bytes + server_port_bytes

    while True:
        # Send the message via UDP broadcast
        udp_socket.sendto(message, ('255.255.255.255', 13117))
        # print(f"UDP broadcast sent with server name: {server_name_bytes.decode().strip(chr(0))}, TCP port: {TCP_PORT}")

        # Wait for one second before sending the next broadcast
        time.sleep(1)

def get_local_ip():
    """
    Get the local IP address of the computer.
    """
    # Create a temporary socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            # Connect to a remote server (Google's public DNS server)
            s.connect(("8.8.8.8", 80))
            # Get the local IP address
            local_ip = s.getsockname()[0]
        except Exception as e:
            print(f"Error getting local IP address: {e}")
            local_ip = None
    return local_ip

def main():
    global IP_ADDRESS, TCP_PORT, SERVER_SOCKET, GAME_READY_EVENT, TCP_THREAD, UDP_THREAD
    # Configuration
    IP_ADDRESS = get_local_ip()  # IP address to listen on
    if IP_ADDRESS is None:
        print("Failed to retrieve local IP address. Please check your network connection.")
        exit()
    # Find a free port for TCP server
    TCP_PORT = find_free_port(20000)

    # Create threading events
    GAME_READY_EVENT = threading.Event()  # Event to signal when the game is ready to start

    # Create a TCP socket
    SERVER_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Start the TCP server in a separate thread
    TCP_THREAD = threading.Thread(target=start_tcp_server, args=())
    TCP_THREAD.start()

    # Start sending UDP broadcasts about the TCP server
    UDP_THREAD = threading.Thread(target=send_udp_broadcast, args=())
    UDP_THREAD.start()

    # Join the UDP thread once the game is started
    UDP_THREAD.join()


if __name__ == "__main__":
    main()