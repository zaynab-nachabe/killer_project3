import socket
import os
import hashlib
import commands

# Define the host and port for the server
HOST = '127.0.0.1'  # Localhost
PORT = 42042

# Define the cache directory
CACHE_DIR = '/var/tmp/cache/'

# Create the cache directory if it does not exist
os.makedirs(CACHE_DIR, exist_ok=True)

# Initialize a dictionary to store player cookies
player_cookies = {}

# Initialize a dictionary to store player status
player_status = {}

#Initialize a list of the connected players (I might change this doesn't seem practical)
players = []

#Initialize game_started as false
game_started = False


def generate_cookie():
    """Generate a unique cookie for a player"""
    return hashlib.sha256(os.urandom(32)).hexdigest()


def cache_file(file_path):
    """Cache a file in the cache directory"""
    file_hash = hashlib.sha256(open(file_path, 'rb').read()).hexdigest()
    cached_file_path = os.path.join(CACHE_DIR, file_hash)
    if not os.path.exists(cached_file_path):
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cached_file_path, 'wb') as cache_file:
            with open(file_path, 'rb') as original_file:
                cache_file.write(original_file.read())
    return cached_file_path


def handle_client_connection(client_socket, client_address):
    """Handle communication with a client"""
    print(f"Connection established with {client_address}")

    try:
        # Main loop for receiving and processing client messages
        while True:
            # Receive data from the client
            data = client_socket.recv(1024).decode().strip()
            if not data:
                break  # Exit the loop if no data is received

            # Parse the received command
            command_parts = data.split(maxsplit=1)
            command = command_parts[0]
            arguments = command_parts[1] if len(command_parts) > 1 else None

            # Handle different commands
            if command == "!start":
                commands.start_game()
            elif command.startswith("@") and command.endswith("!ban"):
                commands.ban_player(command[1:])
            elif command.startswith("@") and command.endswith("!suspend"):
                commands.suspend_player(command[1:])
            elif command.startswith("@") and command.endswith("!forgive"):
                commands.forgive_player(command[1:])
            elif command == "!broadcast_file":
                commands.broadcast_file(arguments)
            elif command.startswith("@") and command.endswith("!send_file"):
                commands.send_file(client_socket, arguments)
            elif command == "!list":
                commands.list_players()
            elif command == "!reconnect":
                commands.reconnect_player(client_socket)
            else:
                # Handle other types of messages (not commands)
                commands.handle_chat_message(data)

    except Exception as e:
        print(f"Error handling client {client_address}: {e}")

    finally:
        # Close the client socket when done
        client_socket.close()
        print(f"Connection with {client_address} closed")


def main():
    # Create a TCP/IP socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # Bind the socket to the address and port
        server_socket.bind((HOST, PORT))

        # Listen for incoming connections
        server_socket.listen()

        print(f"Server listening on {HOST}:{PORT}")

        try:
            # Main loop for accepting client connections
            while True:
                # Accept a new client connection
                client_socket, client_address = server_socket.accept()
                # Handle the client connection in a separate thread or process
                handle_client_connection(client_socket, client_address)
        except KeyboardInterrupt:
            print("Server shutting down...")


if __name__ == "__main__":
    main()
