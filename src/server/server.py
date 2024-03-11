import socket
import threading
import time


ip_address=None
tcp_port=20000
clients = []
questions = {
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
    clients.append((client_socket, client_socket.getpeername()))
    # Wait for the game to be ready
    game_ready_event.wait()

    # Your game logic goes here
    # Once the game is ready, you can proceed with the game

    # Close the connection
    client_socket.close()

def start_tcp_server(server_socket, ip_address, port, game_ready_event):
    """
    Function to start the TCP server.

    Args:
        server_socket (socket.socket): The TCP socket object.
        ip_address (str): The IP address to listen on.
        port (int): The port to listen on.
        game_ready_event (threading.Event): Event indicating if the game is ready to start.
    """
    # Bind the socket to the specified IP address and port
    server_socket.bind((ip_address, port))

    # Listen for incoming connections
    server_socket.listen(5)
    print(f"TCP Server started, listening on IP address {ip_address}, port {port}")

    # Track the time when the server starts
    start_time = time.time()

    # Accept and handle incoming connections for up to 10 seconds
    while time.time() - start_time <= 10:
        # Accept incoming connections
        client_socket, client_address = server_socket.accept()

        # Start a new thread to handle the connection
        threading.Thread(target=handle_tcp_connection, args=(client_socket, game_ready_event)).start()

        # Update the start time to account for the new client connection
        start_time = time.time()

    # If no new clients joined during the last 10 seconds, start the game
    game_ready_event.set()

def send_udp_broadcast(tcp_port):
    """
    Function to send UDP broadcast with custom message format.

    Args:
        tcp_port (int): The port on the server that the client should connect to over TCP.
    """
    # Create a UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Enable broadcast
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Define the message format
    magic_cookie = b'\xab\xcd\xdc\xba'
    message_type = b'\x02'
    server_name_bytes = "KaKi".encode().ljust(32, b'\x00')  # Change "MyServer" to your desired server name
    server_port_bytes = tcp_port.to_bytes(2, byteorder='big')

    # Construct the message
    message = magic_cookie + message_type + server_name_bytes + server_port_bytes

    while True:
        # Send the message via UDP broadcast
        udp_socket.sendto(message, ('255.255.255.255', 13117))
        print(f"UDP broadcast sent with server name: {server_name_bytes.decode().strip(chr(0))}, TCP port: {tcp_port}")

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

if __name__ == "__main__":
    # Configuration
    ip_address = get_local_ip()  # IP address to listen on
    if ip_address is None:
        print("Failed to retrieve local IP address. Please check your network connection.")
        exit()
    # Find a free port for TCP server
    tcp_port = find_free_port(20000)

    # Create threading events
    game_ready_event = threading.Event()  # Event to signal when the game is ready to start

    # Create a TCP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Start the TCP server in a separate thread
    tcp_thread = threading.Thread(target=start_tcp_server, args=(server_socket, ip_address, tcp_port, game_ready_event))
    tcp_thread.start()

    # Start sending UDP broadcasts about the TCP server
    udp_thread = threading.Thread(target=send_udp_broadcast, args=(tcp_port,))
    udp_thread.start()

    # Join the UDP thread once the game is started
    udp_thread.join()
