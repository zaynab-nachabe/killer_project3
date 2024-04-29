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
import sys, select
import commands
from moderateur import signal_handler, how_many_players, broadcast, broadcast_to_client
import time

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

server.bind(ADDR)
# The address is a tuple containing the hostname and port number
# essentially, this is the server's address and port number that the server will listen on
# Écoute des connexions entrantes
server.listen()

print("Serveur démarré sur le port", PORT)

# Liste des sockets à surveiller pour les entrées
sockets_list = [server]

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

def gestion_message(sock, server_socket, sockets_list):
    while True:
        try:
            client_message = sock.recv(1024).decode()
            if client_message:
                if client_message == "$HEARTBEAT":
                    clients_dict[2] = f"last-heartbeat:{time.time}"
                    sock.sendall(b"heartbeat received\n")
                print(f"Message du client {clients_dict[sock][0]} : {client_message}")
                if client_message.startswith('@'):
                    dest_pseudo, message = client_message[1:].split(' ', 1)
                    dest_socket = None
                    for client_socket, val in clients_dict.items():
                        pseudo = val[0]
                        if pseudo == dest_pseudo and client_socket != sock:
                            dest_socket = client_socket
                            break
                    if dest_socket:
                        dest_socket.sendall(f"{clients_dict[sock][0]} (privé): {message}\n".encode())
                    else:
                        sock.sendall(b"Le destinataire n'existe pas.\n")
                elif client_message.startswith('!'):
                    if client_message == "!DISCONNECT":
                        sock.close()
                        clients_dict[sock][1] = "disconnected"
                        sockets_list.remove(sock)
                    elif client_message == "!list":
                        sock.sendall(f"Nombre de joueurs connectés: {how_many_connected()}\n".encode())
                        for client_socket, val in clients_dict.items():
                            pseudo = val[0]
                            sock.sendall(f"{pseudo} : {val[1]}\n".encode())
                    elif client_message == "!online_status":
                        for client_socket, val in clients_dict.items():
                            pseudo = val[0]
                            sock.sendall(f"Statut en ligne du joueur {pseudo}: {val[1]}\n".encode())
                    elif client_message == "!last-heartbeats":
                        for client_socket, val in clients_dict.items():
                            pseudo = val[0]
                            sock.sendall(f"Joueur: {pseudo} - Dernier battement de coeur: {val[2]}\n".encode())
                    else:
                        sock.sendall(b"Commande inconnue.\n")
                else:
                    for client_socket, val in clients_dict.items():
                        pseudo = val[0]
                        if client_socket != server_socket and client_socket != sock:
                            client_socket.sendall(f"{clients_dict[sock][0]}: {client_message}\n".encode())
        except Exception as Erreur:
            print("Erreur lors de la réception des données :", Erreur)
            sock.close()
            clients_dict[sock][1] = "fucked up" # c'est pas chatgpt qui écrirait ça hein
            sockets_list.remove(sock)

def check_heartbeat(clients_dict):
    while True:
        for clients, info in clients_dict.items():
            last_heartbeat_of_client = info[2].strip(":")


def handle_client(connection, client_address):
    global sockets_list
    print(f"[NEW CONNECTION] {client_address} connected.")
    clients_dict[(connection, client_address)] = [None, "connected", f"last-heartbeat: {time.time()}"]
    # sockets_list = creation_socket(server)
    try:
        welcome_message = "Bienvenu sur le serveur!"
        connection.send(welcome_message.encode(FORMAT))

        connected = True
        while connected:
            print('Nouveau client connecté depuis', client_address)
            connection.sendall(b'Veuillez entrer votre pseudo sous le format : pseudo=PSEUDO')
            pseudo = connection.recv(1024).decode().strip('=')[1]
            if pseudo in [client[0] for client in clients_dict.values()]:
                connection.sendall("Pseudo déjà pris!".encode(FORMAT))
            clients_dict[(connection, client_address)][0] = pseudo
            sockets_list.append(connection)
            connection.sendall("Pseudo reçu!".encode(FORMAT))
            gestion_message(connection, server, sockets_list)
                
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
                    print(f"Player: {info[0]} - Last heartbeat: {info[2]}")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    print("[STARTING] server is starting...")
    start()
