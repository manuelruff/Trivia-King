import socket
import threading
import time


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
    print(f"TCP connection established with {client_socket.getpeername()}")

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

def send_udp_broadcast(port, message):
    """
    Function to send UDP broadcast.

    Args:
        port (int): The port to send the broadcast to.
        message (bytes): The message to send.
    """
    # Create a UDP socket
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Enable broadcast
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    while True:
        # Send the message via UDP broadcast
        udp_socket.sendto(message, ('<broadcast>', port))
        print(f"UDP broadcast sent: {message}")

        # Wait for one second before sending the next broadcast
        time.sleep(1)


if __name__ == "__main__":
    # Configuration
    ip_address = "172.1.0.4"  # IP address to listen on

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
    udp_thread = threading.Thread(target=send_udp_broadcast, args=(ip_address, tcp_port, b"TCP server info"))
    udp_thread.start()

    # Join the UDP thread once the game is started
    udp_thread.join()
