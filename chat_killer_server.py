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
from moderateur import signal_handler, how_many_players, broadcast, broadcast_to_client

# Constants
HEADER = 64
PORT = 5050
SERVER = "127.0.0.1" # socket.gethostbyname(socket.gethostname()) # get the IP address of the machine
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SHUTDOWN_MESSAGE = "!SERVER_SHUTDOWN"

clients_dict = {}


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
# AF_INET is the address family for IPv4, and SOCK_STREAM is the socket type for TCP

server.bind(ADDR) # The address is a tuple containing the hostname and port number
# essentially, this is the server's address and port number that the server will listen on

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
        # Handle inputs on the server side
        command = input("> ")
        if command == "list":
            print(f"Number of connected players: {how_many_players()}")
        elif command == "online_status":
            print("Online status of players:")
            for player in clients_dict.keys():
                print(f"Player: {player}")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    print("[STARTING] server is starting...")
    start()
