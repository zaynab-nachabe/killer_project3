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

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname()) # get the IP address of the machine
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

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

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    
    connected = True
    while connected:
        msg_length = conn.recv(HEADER).decode(FORMAT) # receive the message length
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT) # receive the message
            if msg == DISCONNECT_MESSAGE:
                connected = False
            print(f"[{addr}] {msg}")
            conn.send("Message received".encode(FORMAT)) # send a message back to the client

    conn.close()

def start():
    server.listen() # The backlog parameter specifies the maximum number of queued connections
    print(f"[LISTENING] server is listening on {SERVER}")
    while True:
        conn, addr = server.accept() # Returns a new socket object and the address of the client
        # handle_client(conn, addr)
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

print("[STARTING] server is starting...")
start()