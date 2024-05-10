import os, sys
import signal, socket, threading, hashlib
import re, errno, time

# Constants
HEADER = 64
PORT = 5050
SERVER = '127.0.0.1'
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SHUTDOWN_MESSAGE = "!SERVER_SHUTDOWN"

clients_dict = {}
cache_info_stack = []

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)
server.listen()
sockets_list = [server]

print(f"Serveur démarré sur le port {PORT}")

def clean_message(message):
    cleaned_message = re.sub(r'\s+', ' ', message).strip()
    final_message = re.sub(r'^\d+\s*', '', cleaned_message)
    return final_message

def how_many_connected():
    global clients_dict
    return sum(1 for value in clients_dict.values() if value[1] == "connected")

def handle_private_message(client_message, pseudo, connection):
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
                
def handle_command(client_message, connection, client_address):
    if client_message == "!DISCONNECT":
        socket_to_remove = (connection, client_address)
        connection.close()
        clients_dict[(connection, client_address)][1] = "disconnected"
        print("Sockets list before:", sockets_list)
        if socket_to_remove in sockets_list:
            sockets_list.remove(socket_to_remove)
            print("socket removed")
            #print("Sockets list after:", sockets_list)
            #print("Current clients dict:", clients_dict)
        else:
            print("socket not caught")
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

def broadcast(msg):
    global clients_dict
    for client, info in clients_dict.items():
        if info[1] == "connected":
            client[0].send(msg.encode(FORMAT))

def reconnection(server_socket, pseudo, client_message, connection):
    print('reconnect test here 2')
    for client_socket, val in clients_dict.items():
        if client_socket != server_socket and client_socket != connection:
            if val[1] == "connected":  # Check if client is still connected
                client_socket[0].sendall(f"{pseudo}: {client_message}\n".encode())

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
                        clients_dict[client_key] = [pseudo, "connected", f"last-heartbeat: {time.time()}"]
                        connection.sendall("Pseudo reçu!\n".encode(FORMAT))
                        connection.sendall("$cookie=test_data\n".encode(FORMAT))
                else:
                    pass
            else:
                pseudo = clients_dict[client_key][0]
                if client_message == "$HEARTBEAT":
                    clients_dict[client_key] = [pseudo, "connected", f"last-heartbeat:{time.time()}"]
                    connection.sendall(b"heartbeat received\n")
                elif client_message.startswith('@'):
                    # Handle message privé
                    handle_private_message(client_message, pseudo, connection)
                elif client_message.startswith('!'):
                    # Handle command
                    handle_command(client_message, connection, client_address)
                else:
                    # Reconnection
                    reconnection(server_socket, pseudo, client_message, connection)
        else:
            pass
    except Exception as error:
        print(f"Error receiving data: {error}")
        if error.errno == errno.EBADF:
            print("Socket closed. Ignoring further processing.")
        clients_dict[client_key][1] = "disconnected"


def signal_handler(sig, frame):
    """Handle graceful shutdown on SIGINT."""
    print("\n[SHUTDOWN] Server is shutting down...")
    broadcast(SHUTDOWN_MESSAGE)
    for client, info in clients_dict.items():
        client[0].close()
    server.close()
    sys.exit(0)

def handle_client(connection, client_address):
    global clients_dict
    print(f"[NEW CONNECTION] {client_address} connected.")
    clients_dict[(connection, client_address)] = [None, "connected", f"last-heartbeat: {time.time()}"]
    try:
        welcome_message = "Bienvenue sur le serveur!"
        connection.send(welcome_message.encode(FORMAT))
        while clients_dict[(connection, client_address)][1] == "connected":
            gestion_message(connection, client_address, server)
    except ConnectionResetError:
        print(f"[ERROR] Connection perdu avec {client_address}")
    finally:
        connection.close()
        clients_dict[(connection, client_address)][1] = "disconnected"
        print(f"[DISCONNECTION] {client_address} disconnected.")

def start():
    global clients_dict
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {len(clients_dict)}")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    print("[STARTING] Server is starting...")
    start()