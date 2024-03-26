import csv
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
TCP_SOCKET=None
UDP_SOCKET=None
GAME_READY_EVENT= threading.Event()  # Event to signal when the game is ready to start
TCP_THREAD=None
UDP_THREAD=None

CSV_FILE = "players_data.csv"
# Initialize user data dictionary
USER_DATA = {}
#function to collect data
# Function to update user data dictionary
def update_user_data(username, won):
    if username in USER_DATA:
        USER_DATA[username]["games_played"] += 1
        if won:
            USER_DATA[username]["games_won"] += 1
    else:
        USER_DATA[username] = {"games_played": 1, "games_won": int(won)}

# Function to calculate the percentage of games won for each user
def calculate_win_percentage():
    for username, data in USER_DATA.items():
        games_played = data["games_played"]
        games_won = data["games_won"]
        win_percentage = (games_won / games_played) * 100 if games_played > 0 else 0
        USER_DATA[username]["win_percentage"] = win_percentage

# Function to write user data to CSV file
def write_user_data_to_csv():
    try:
        with open(CSV_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Username", "Games Played", "Games Won", "Win Percentage"])
            # Sort user data by win percentage (from high to low)
            sorted_user_data = sorted(USER_DATA.items(), key=lambda x: x[1]["win_percentage"], reverse=True)
            for username, data in sorted_user_data:
                writer.writerow([username, data["games_played"], data["games_won"], data["win_percentage"]])
    except FileNotFoundError:
        # If the file doesn't exist, create a new one
        create_csv_file()

# Function to create a new CSV file
def create_csv_file():
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Username", "Games Played", "Games Won", "Win Percentage"])

def print_leaderboard():
    try:
        with open("players_data.csv", mode='r') as file:
            reader = csv.reader(file)
            leaderboard = list(reader)

            # Print the top 3 entries of the leaderboard
            print("Leaderboard:")
            print("{:<5} {:<20} {:<15} {:<15} {:<15}".format("Place", "Username", "Games Played", "Games Won", "Win Percentage"))
            for i, row in enumerate(leaderboard[:3], start=1):
                place = str(i) + "."
                username = row[0]
                games_played = row[1]
                games_won = row[2]
                win_percentage = row[3]

                # Set color based on position
                if i == 1:
                    color = "\033[33m"  # Gold
                elif i == 2:
                    color = "\033[37m"  # Silver
                elif i == 3:
                    color = "\033[38;5;208m"  # Bronze
                else:
                    color = "\033[0m"  # White

                print(f"{color}{place:<5} {username:<20} {games_played:<15} {games_won:<15} {win_percentage:<15}\033[0m")
    except FileNotFoundError:
        print("No leaderboard data available.")

######################################################

def colored_print(text, color='\033[36m'):
    print(color + text + '\033[0m')
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
            colored_print(f"Error getting local IP address: {e}")
            local_ip = None
    return local_ip
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
    if ans:
        if client_ans in ('t', '1', 'y'):
            return True
        else:
            return False
    else:
        if client_ans in ('f', '0', 'n'):
            return True
    return False
def handle_tcp_connection(client_socket, game_ready_event):
    """
    Function to handle TCP connections.

    Args:
        client_socket (socket.socket): The socket object representing the TCP connection.
        game_ready_event (threading.Event): Event indicating if the game is ready to start.
    """
    colored_print("Server started, listening on IP address {}")
    colored_print(f"TCP connection established with {client_socket.getpeername()}")
    # Add the client information to the list of connected clients
    CLIENTS.append((client_socket, client_socket.getpeername()))
    CLIENT_NAMES[client_socket.getpeername()] = client_socket.recvfrom(1024)[0].decode()
    colored_print(f"Client {CLIENT_NAMES[client_socket.getpeername()]} has joined the game")
    # Wait for the game to be ready
    game_ready_event.wait()
def receive_answers_from_client(client_socket):
    client_socket.settimeout(10)  # Set a timeout of 10 seconds for receiving data
    try:
        # Wait for incoming data (answer) or timeout
        answer = client_socket.recv(1024).decode().strip()
        if answer:
            ANSWER_QUEUE.put((client_socket.getpeername(), answer))
    except socket.timeout:
        # Timeout occurred
        try:
            client_socket.send("enough".encode("utf-8"))
        except Exception as e:
            colored_print(f"Error sending message to {client_socket.getpeername()}: {e}")
        pass
    except Exception as e:
        return

def send_message_to_clients(message,print_message=True):
    for client_socket, _ in CLIENTS:
        try:
            client_socket.send(message.encode('utf-8'))
        except Exception as e:
            colored_print(f"Error sending message to {client_socket.getpeername()}: {e}")
    if print_message:
        colored_print(message)
def send_start_game_message():
    message = f"Welcome to the {SERVER_NAME} server, where we are answering trivia questions\n"
    count = 1
    for client in CLIENTS:
        message += f"Player {count}: {CLIENT_NAMES[client[1]]} \n"
        count += 1
    send_message_to_clients(message)

def start_game():
    # Send a message to all clients that the game is starting
    send_start_game_message()
    # flag for finishing game
    game_finished = False
    # Now we need to start sending questions
    while not game_finished:
        question, answer = create_random_question()
        # Send the question to everyone
        send_message_to_clients(question)
        # We will empty the queue
        ANSWER_QUEUE.empty()
        # We will start a thread for each client to receive the answer
        for client in CLIENTS:
            threading.Thread(target=receive_answers_from_client, args=(client[0],)).start()
        # Wait for a correct answer
        timeout = 10  # Timeout in seconds
        start_time = time.time()
        # we check how manyt clients sent an answare and stop when they all sent it
        client_count=len(CLIENTS)
        while time.time() - start_time < timeout:
            try:
                client_answer = ANSWER_QUEUE.get(timeout=timeout)
                if check_correct(client_answer[1], answer):
                    game_finished = True
                    break
                else:
                    client_count-=1
                # all the clients sent a wring answare
                if client_count==0:
                    break
            except queue.Empty:
                # No answer received within the timeout period
                colored_print("No correct answer received within the timeout period")
                break
    # Send the correct answer to everyone
    message1 = f"{CLIENT_NAMES[client_answer[0]]} is correct! {CLIENT_NAMES[client_answer[0]]} wins!\n"
    message2= f"Game over!\nCongratulations to the winner: {CLIENT_NAMES[client_answer[0]]}\n"
    send_message_to_clients(message1,False)
    send_message_to_clients(message2,False)
    colored_print("Game over,sending out offer requests...")
    # disconnecting all clients
    disconnect_clients()
    # finish the game
    GAME_READY_EVENT.clear()
    # send udp broadcast again
    start_threads()
def client_connect():
    # Accept incoming connection
    client_socket, client_address = TCP_SOCKET.accept()
    colored_print(f"New connection from {client_address}")
    # Start a new thread to handle the connection
    threading.Thread(target=handle_tcp_connection, args=(client_socket, GAME_READY_EVENT)).start()
def tcp_connect_clients():
    """
    Function to start getting connections
    Args:
        game_ready_event (threading.Event): Event indicating if the game is ready to start.
    """
    global TCP_SOCKET
    count_clients=0
    while True:
        try:
            client_connect()
            # Set the timeout for accepting new connections
            TCP_SOCKET.settimeout(10)
            count_clients+=1
        except socket.timeout:
            # if no clients connected we continue o wait
            if count_clients==0:
                continue
            # If at least one client has connected, break the loop and proceed with the game
            break
    # Cancel the timeout after the loop
    TCP_SOCKET.settimeout(None)
    colored_print("Game ready!")
    # If no new clients joined during the last 10 seconds, start the game
    GAME_READY_EVENT.set()
    # Once the game is ready, you can proceed with the game
    start_game()
def send_udp_broadcast():
    """
    Function to send UDP broadcast with custom message format.
    """
    # Define the message format
    magic_cookie = b'\xab\xcd\xdc\xba'
    message_type = b'\x02'
    server_name_bytes = SERVER_NAME.encode('utf-8').ljust(32, b'\x00')  # Change "KaKi" to your desired server name
    server_port_bytes = TCP_PORT.to_bytes(2, byteorder='big')

    # Construct the message
    message = magic_cookie + message_type + server_name_bytes + server_port_bytes

    while not GAME_READY_EVENT.is_set():
        try:
            # Send the message via UDP broadcast
            UDP_SOCKET.sendto(message, ('255.255.255.255', 13117))
            # colored_print(f"UDP broadcast sent with server name: {server_name_bytes.decode().strip(chr(0))}, TCP port: {TCP_PORT}")
        except Exception as e:
            colored_print(f"Error sending UDP broadcast: {e}")
            # Handle the error as needed (e.g., retry, exit, etc.)
        # Wait for one second before sending the next broadcast
        time.sleep(1)
def disconnect_clients():
    """
    Function to disconnect all connected clients.
    """
    for client_socket, _ in CLIENTS:
        try:
            # Close the client socket
            client_socket.close()
        except Exception as e:
            colored_print(f"Error closing client socket: {e}")

    # Clear the list of connected clients
    CLIENTS.clear()
    # Clear the dictionary of client names
    CLIENT_NAMES.clear()
def start_threads():
    # Start the TCP server in a separate thread
    TCP_THREAD = threading.Thread(target=tcp_connect_clients, args=())
    TCP_THREAD.start()

    # Start sending UDP broadcasts about the TCP server
    UDP_THREAD = threading.Thread(target=send_udp_broadcast, args=())
    UDP_THREAD.start()
def tcp_setup():
    global IP_ADDRESS, TCP_PORT, TCP_SOCKET
    try:
        # Find a free port for TCP server
        TCP_PORT = find_free_port(20000)
    except OSError:
        colored_print("Error finding a free port for the TCP server")
        exit()
    # Create a TCP socket
    TCP_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Bind the socket to the specified IP address and port
        TCP_SOCKET.bind((IP_ADDRESS, TCP_PORT))
    except Exception as e:
        colored_print(f"Error binding TCP socket to IP address {IP_ADDRESS}, port {TCP_PORT}")
        exit()
    try:
        # Listen for incoming connections
        TCP_SOCKET.listen(10)
    except Exception as e:
        colored_print("Error listening for incoming connections")
        exit()
    colored_print(f"TCP Server started, listening on IP address {IP_ADDRESS}, port {TCP_PORT}")
def udp_setup():
    global UDP_SOCKET
    try:
        # Create a UDP socket
        UDP_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except Exception as e:
        colored_print(f"Error creating UDP socket: {e}")
        exit()
    try:
        # Enable broadcast
        UDP_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    except Exception as e:
        colored_print(f"Error enabling broadcast for UDP socket: {e}")
        exit()
def main():
    global IP_ADDRESS, TCP_PORT, TCP_SOCKET, GAME_READY_EVENT, TCP_THREAD, UDP_THREAD,UDP_SOCKET
    # Configuration
    IP_ADDRESS = get_local_ip()  # IP address to listen on
    if IP_ADDRESS is None:
        colored_print("Failed to retrieve local IP address. Please check your network connection.")
        exit()
    # Create threading events
    # setup the TCP server
    tcp_setup()
    # setup the UDP server
    udp_setup()
    # Start the TCP server connections and UDP broadcast threads
    start_threads()

if __name__ == "__main__":
    main()