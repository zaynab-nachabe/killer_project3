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
    try:
        client_message = sock.recv(1024).decode()
        if client_message:
            # Si message reçu c'est le HEARTBEAT
            if client_message == "$HEARTBEAT":
                clients_dict[2] = f"last-heartbeat: {time.time}"
            print(f"Message du client {clients_dict[sock][0]} : {client_message}")
            # Vérifier si le message est un message privé ou destiné à tous les clients
            if client_message.startswith('@tous'):
                # Transmettre le message à tous les clients, sauf à l'expéditeur
                for client_socket, val in clients_dict.items():
                    pseudo = val[0]
                    if client_socket != server_socket and client_socket != sock:
                        client_socket.sendall(f"{pseudo}: {client_message[6:]}\n".encode())
            elif client_message.startswith('@'):
                # Trouver le destinataire du message privé
                dest_pseudo, message = client_message[1:].split(' ', 1)
                dest_socket = None
                for client_socket, val in clients_dict.items():
                    pseudo = val[0]
                    if pseudo == dest_pseudo:
                        dest_socket = client_socket
                        break
                # Envoyer le message privé au destinataire ou afficher un message d'erreur
                if dest_socket:
                    dest_socket.sendall(f"{clients_dict[sock][0]} (privé): {message}\n".encode())
                else:
                    sock.sendall(b"Le destinataire n'existe pas.\n")
            else:
                # Transmettre le message à tous les clients, sauf à l'expéditeur
                for client_socket, val in clients_dict.items():
                    pseudo = val[0]
                    if client_socket != server_socket and client_socket != sock:
                        client_socket.sendall(f"{clients_dict[sock][0]}: {client_message}\n".encode())
        else:
            # Si le client a fermé la connexion, on le retire de la liste des sockets à surveiller
            sock.close()
            clients_dict[sock][1] = "mort"
            sockets_list.remove(sock)
    except Exception as e:
        # En cas d'erreur, on ferme le socket et on le retire de la liste
        print("Erreur lors de la réception des données :", e)
        sock.close()
        clients_dict[sock][1] = "fucked up" # c'est pas chatgpt qui écrirait ça hein
        sockets_list.remove(sock)

def handle_client(connection, client_address):
    print(f"[NEW CONNECTION] {client_address} connected.")
    clients_dict[(connection, client_address)] = [None, "connected", f"last-heartbeat: {time.time()}"]
    # sockets_list = creation_socket(server)
    try:
        welcome_message = "Bienvenu sur le serveur!"
        connection.send(welcome_message.encode(FORMAT))

        connected = True
        while connected:
            readable_sockets = select.select(sockets_list, [], [], 0)[0]
            for sock in readable_sockets:
                if sock == server:
                    print('Nouveau client connecté depuis', client_address)
                    connection.sendall(b'Veuillez entrer votre pseudo sous le format : pseudo=PSEUDO')
                    pseudo = connection.recv(1024).decode().strip('=')[1]
                    if pseudo in [client[0] for client in clients_dict.values()]:
                        connection.sendall("Pseudo déjà pris!".encode(FORMAT))
                        continue
                    clients_dict[(connection, client_address)][0] = pseudo
                    sockets_list.append(connection)
                    connection.sendall("Pseudo reçu!".encode(FORMAT))
                else:
                    gestion_message(sock, server, sockets_list)
                
    except ConnectionResetError:
        print(f"[ERROR] Connection lost with {addr}")
    finally:
        conn.close()
        clients_dict[sock][1] = "disconnected"
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
