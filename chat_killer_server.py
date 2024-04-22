# chat_killer_server.py : l'exécutable lancé par le modérateur de jeu. 
# Cet exécutable lance le serveur de chat dans le terminal (reste attaché au terminal). 
# Le modérateur, via cet exécutable:
# • peut suivre toutes les discussions
# • connait tous les secrets
# • decide quand lancer la partie
# • peut suspendre temporairement ou bannir définitivement un joueur au cours de partie (c'est un modérateur)
# • vérifie que le programmeur a bien fait son travail (débogage)

import socket
import threading
import signal
import sys
import commands


HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname()) # get the IP address of the machine
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SHUTDOWN_MESSAGE = "!SERVER_SHUTDOWN"


"""
-- Documentation of clients_dict --
The clients_dict dictionary is used to store information about connected clients.
The client when they first connect to the server share their username with the server.
We store that username in the clients_dict dictionary with the client's address as the key.
The goal is for us to use the simplest data structure to manipulate the messages sent by the clients:
- To all the clients connected to the server
- To a specific client
- To the server (moderator)
"""
clients_dict = {}


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
# AF_INET is the address family for IPv4, and SOCK_STREAM is the socket type for TCP

server.bind(ADDR) # The address is a tuple containing the hostname and port number
# essentially, this is the server's address and port number that the server will listen on

def broadcast_to_client(client_address, message):
    """Send a message to a specific connected client."""
    client = clients_dict.get(client_address)
    if client:
        client.send(message.encode(FORMAT))
    else:
        print(f"[ERROR] Client {client_address} not found.")

def broadcast(message):
    """Send a message to all connected clients."""
    for client in clients_dict.values():
        client.send(message.encode(FORMAT))

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    clients_dict[addr] = conn
    try:
        welcome_message = "Welcome to the chat server!"
        conn.send(welcome_message.encode(FORMAT))

        connected = True
        while connected:
            msg_length = conn.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                msg = conn.recv(msg_length).decode(FORMAT)
                if msg == DISCONNECT_MESSAGE:
                    connected = False
                print(f"[{addr}] {msg}")
                conn.send("Message received".encode(FORMAT))
    except ConnectionResetError:
        print(f"[ERROR] Connection lost with {addr}")
    finally:
        conn.close()
        clients_dict.pop(addr, None)
        print(f"[DISCONNECTION] {addr} disconnected.")

def start():
    server.listen()
    print(f"[LISTENING] server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

def signal_handler(sig, frame):
    """Handle graceful shutdown on SIGINT."""
    print("\n[SHUTDOWN] Server is shutting down...")
    broadcast(SHUTDOWN_MESSAGE)
    for client in clients_dict.values():
        client.close()
    server.close()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    print("[STARTING] server is starting...")
    start()