# chat_killer_server.py : l'exécutable lancé par le modérateur de jeu. 
# Cet exécutable lance le serveur de chat dans le terminal (reste attaché au terminal). 
# Le modérateur, via cet exécutable:
# • peut suivre toutes les discussions
# • connait tous les secrets
# • decide quand lancer la partie
# • peut suspendre temporairement ou bannir définitivement un joueur au cours de partie (c'est un modérateur)
# • vérifie que le programmeur a bien fait son travail (débogage)

import socket, os
import threading
import signal
import sys, select
import commands
import hashlib
import time
import re

# Constants
HEADER = 64
PORT = 5050
SERVER = "127.0.0.1" # socket.gethostbyname(socket.gethostname()) # get the IP address of the machine
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SHUTDOWN_MESSAGE = "!SERVER_SHUTDOWN"

clients_dict = {}

cache_info_stack = []

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
# AF_INET is the address family for IPv4, and SOCK_STREAM is the socket type for TCP

server.bind(ADDR)
# The address is a tuple containing the hostname and port number
# essentially, this is the server's address and port number that the server will listen on
# Écoute des connexions entrantes
server.listen()

print("Serveur démarré sur le port", PORT)

# Liste des sockets à surveiller pour les entrées
sockets_list = [server]

def clean_message(message):
    # Strip leading and trailing spaces and replace multiple spaces with a single space
    cleaned_message = re.sub(r'\s+', ' ', message).strip()
    final_message = re.sub(r'^\d+\s*', '', cleaned_message)
    return final_message

def how_many_connected():
    global clients_dict
    count = 0
    for key, value in clients_dict.items():
        if value[1] == "connected":
            count += 1
    return count

def creation_socket(server):
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Liaison du socket à l'adresse et au port spécifiés
    return sockets_list

def gestion_message(connection, client_address, server_socket):
    global clients_dict
    global cache_info_stack
    global sockets_list
    try:
        client_message = connection.recv(1024).decode()
        client_message = clean_message(client_message)
        if client_message:
            client_key = (connection, client_address)
            if client_key in clients_dict and clients_dict[client_key][0] is None:
                if client_message.startswith("pseudo="):
                    pseudo = client_message.split("=")[1].strip()
                    if pseudo in [client[0] for client in clients_dict.values()]:
                        connection.sendall("Pseudo déjà pris!\n".encode(FORMAT))
                    else:
                        clients_dict[(connection, client_address)] = [pseudo, "connected", f"last-heartbeat: {time.time()}"]
                        sockets_list.append(connection)
                        connection.sendall("Pseudo reçu!\n".encode(FORMAT))
                else:
                    pass
            else:
                pseudo = clients_dict[(connection, client_address)][0]  # Retrieve pseudo from dictionary
                if client_message == "$HEARTBEAT":
                    clients_dict[connection] = [pseudo, "connected", f"last-heartbeat:{time.time()}"]
                    connection.sendall(b"heartbeat received\n")
                print(f"{pseudo} : {client_message}")
                if client_message.startswith('@'):
                    dest_pseudo, message = client_message[1:].split(' ', 1)
                    dest_socket = None
                    for client_socket, val in clients_dict.items():
                        if val[0] == dest_pseudo and client_socket != connection:
                            dest_socket = client_socket[0]
                            break
                    if dest_socket:
                        dest_socket.sendall(f"{pseudo} (privé): {message}\n".encode())
                    else:
                        connection.sendall(b"Le destinataire n'existe pas.\n")
                elif client_message.startswith('!'):
                    if client_message == "!DISCONNECT":
                        connection.close()
                        clients_dict[(connection, client_address)][1] = "disconnected"
                        if (connection, client_address) in sockets_list:
                            sockets_list.remove((connection, client_address))
                    elif client_message == "!list":
                        connection.sendall(f"Nombre de joueurs connectés: {len(clients_dict)}\n".encode())
                        for client_socket, val in clients_dict.items():
                            connection.sendall(f"{val[0]} : {val[1]}\n".encode())
                    elif client_message == "!online_status":
                        for client_socket, val in clients_dict.items():
                            connection.sendall(f"Statut en ligne du joueur {val[0]}: {val[1]}\n".encode())
                    elif client_message == "!last-heartbeats":
                        for client_socket, val in clients_dict.items():
                            connection.sendall(f"Joueur: {val[0]} - Dernier battement de coeur: {val[2]}\n".encode())
                    else:
                        connection.sendall(b"Commande inconnue.\n")
                else:
                    for client_socket, val in clients_dict.items():
                        if client_socket != server_socket and client_socket != connection:
                            client_socket[0].sendall(f"{pseudo}: {client_message}\n".encode())
        else:
            pass
    except Exception as error:
        print("Erreur lors de la réception des données :", error)
        clients_dict[(connection, client_address)][1] = "fucked up"
        if (connection, client_address) in sockets_list:
            sockets_list.remove((connection, client_address))

def generate_cookie():
    """Generate a unique cookie for a player"""
    return hashlib.sha256(os.urandom(32)).hexdigest()

def cache_file(file_path):
    """Cache a file in the cache directory"""
    file_hash = hashlib.sha256(open(file_path, 'rb').read()).hexdigest()
    cached_file_path = os.path.join(CACHE_DIR, file_hash)

    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        if not os.path.exists(cached_file_path):
            with open(cached_file_path, 'wb') as cache_file:
                with open(file_path, 'rb') as original_file:
                    cache_file.write(original_file.read())
    except Exception as e:
        print(f"Error caching file {file_path}: {e}")

    return cached_file_path

def handle_client_connection(client_socket, client_address):
    """Handle communication with a client"""
    print(f"Connection established with {client_address}")

    try:
        # Receive the client's pseudo name
        player_pseudo = client_socket.recv(1024).decode().strip()
        # Add the player to the dictionary of connected players
        players[player_pseudo] = client_socket

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
            match command:
                case "!start":
                    commands.start_game()
                case command if command.startswith("@") and command.endswith("!ban"):
                    commands.ban_player(command[1:])
                case command if command.startswith("@") and command.endswith("!suspend"):
                    commands.suspend_player(command[1:])
                case command if command.startswith("@") and command.endswith("!forgive"):
                    commands.forgive_player(command[1:])
                case "!broadcast_file":
                    commands.broadcast_file(arguments)
                case command if command.startswith("@") and command.endswith("!send_file"):
                    commands.send_file(client_socket, arguments)
                case "!list":
                    commands.list_players()
                case "!reconnect":
                    commands.reconnect_player(client_socket)
                case _:
                    # Handle other types of messages (not commands)
                    commands.handle_chat_message(data)

    except Exception as e:
        print(f"Error handling client {client_address}: {e}")

    finally:
        # Remove the client from the dictionary of connected players
        if player_pseudo in players:
            del players[player_pseudo]
        # Close the client socket when done
        client_socket.close()
        print(f"Connection with {client_address} closed")

def signal_handler(sig, frame):
    """Handle graceful shutdown on SIGINT."""
    print("\n[SHUTDOWN] Server is shutting down...")
    broadcast(SHUTDOWN_MESSAGE)
    for client, info in clients_dict.items():
        client[0].close()
    server.close()
    sys.exit(0)

def how_many_players():
    """Return the number of connected players."""
    return len(players)

def broadcast_to_client(client_address, message):
    """Send a message to a specific connected client."""
    client = clients_dict.get(client_address)
    if client:
        client.send(message.encode(FORMAT))
    else:
        print(f"[ERROR] Client {client_address} not found.")

def broadcast(message):
    """Send a message to all connected clients."""
    for client, info in clients_dict.items():
        client[0].send(message.encode(FORMAT))

def check_heartbeat():
    global cache_info_stack
    global clients_dict
    try:
        for clients, info in clients_dict.items():
            last_heartbeat_of_client = info[2].split(":")[1]
            last_heartbeat_of_client = float(last_heartbeat_of_client)
            if (last_heartbeat_of_client < time.time() - 30) and clients_dict[clients][1] != "disconnected":
                print(f"Client {info[0]} is disconnected")
                clients_dict[clients][1] = "disconnected"
                cache_info_stack.append(("Disconnection", info[0], "disconnected"))
    except RuntimeError as e:
        pass

def handle_issue():
    global cache_info_stack
    issue = cache_info_stack.pop()
    if issue[0] == "Disconnection":
        print(f"Handling issue: {issue[1]} is {issue[2]}")

def handle_client(connection, client_address):
    global sockets_list
    global clients_dict
    print(f"[NEW CONNECTION] {client_address} connected.")
    clients_dict[(connection, client_address)] = [None, "connected", f"last-heartbeat: {time.time()}"]
    # sockets_list = creation_socket(server)
    try:
        welcome_message = "Bienvenu sur le serveur!"
        connection.send(welcome_message.encode(FORMAT))

        while clients_dict[(connection, client_address)][1] == "connected":
            gestion_message(connection, client_address, server)

    except ConnectionResetError:
        print(f"[ERROR] Connection lost with {client_address}")
    finally:
        connection.close()
        clients_dict[(connection, client_address)][1] = "disconnected"
        print(f"[DISCONNECTION] {client_address} disconnected.")

def start():
    server.listen()
    print(f"[LISTENING] server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        thread2 = threading.Thread(target=check_heartbeat)
        thread2.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
        # Handle inputs on the server side
        while (command := input("> ")):
            if command == "!list":
                print(f"Number of connected players: {how_many_connected()}")
                for _, info in clients_dict.keys():
                    print(f"{info[0]} : {info[1]}")
            elif command == "!online_status":
                print("Online status of players:")
                for _, info in clients_dict.keys():
                    print(f"Player status: {info[1]}")
            elif command == "!last-heartbeats":
                print("The last heartbeats of each player is:")
                for _, info in clients_dict.items():
                    print(f"Player: {info[0]} - {info[2]}")
            elif command == "!shutdown":
                broadcast(SHUTDOWN_MESSAGE)
                for client in clients_dict.keys():
                    client[0].close()
                server.close()
                sys.exit(0)
        thread.join()
        thread2.join()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    print("[STARTING] server is starting...")
    start()

