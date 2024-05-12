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
import sys
import time
import errno
import random

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

private_message = False
game_started = False

cookie_dictionary = {}

def bake_cookie_id():
    cookie_id = random.randint(1000000000,9999999999)
    return cookie_id

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

def parse_private_message(client_message):
    # check how many pseudoes are in the message
    # parse until the word doesn't start with @
    pseudo = []
    message_split = client_message.split(' ')
    while message_split[0].startswith('@'):
        pseudo.append(message_split[0][1:])
        message_split = message_split[1:]
    message = ' '.join(message_split)
    return pseudo, message

def gestion_message(connection, client_address, server_socket):
    global clients_dict
    global cache_info_stack
    global sockets_list
    global cookie_dictionary
    global private_message
    try:
        private_message = False
        client_message = connection.recv(1024).decode()
        #print("Clients dict:", clients_dict)
        if client_message:
            client_key = (connection, client_address)
            # if suspended, send a message to the client and not share the message with other clients
            if clients_dict[client_key][3] == "suspended":
                connection.sendall("Vous avez été suspendu. Vous ne pouvez pas envoyer de messages tant que vous n'êtes pas excusé. (forgive(n))\n".encode(FORMAT))
            elif clients_dict[client_key][3] == "banned":
                connection.sendall("Vous avez été banni. Vous ne pouvez pas envoyer de messages.\n".encode(FORMAT))
            elif client_key in clients_dict and clients_dict[client_key][0] is None and clients_dict[client_key][3] == "alive":
                if client_message.startswith("pseudo="):
                    pseudo = client_message.split("=")[1].strip()
                    if pseudo in [var[0] for key, var in clients_dict.items()]:
                        # extract the client_key of the client with the same pseudo
                        copycatconn, copycataddr = None, None
                        copycatsocket = None
                        for client_key, client_values in clients_dict.items():
                            if client_values[0] == pseudo:
                                copycatconn, copycataddr = client_key
                                copycatsocket = (copycatconn, copycataddr)
                        # if the user was disconnected and tries to reconnect with the same pseudo
                        if clients_dict[copycatsocket][1] == "disconnected":
                            # cookie identification
                            connection.sendall("$send_cookie\n".encode(FORMAT))
                            clients_cookie = connection.recv(1024).decode()
                            if clients_cookie == DISCONNECT_MESSAGE:
                                socket_to_remove = (connection, client_address)
                                connection.close()
                                clients_dict[(connection, client_address)][1] = "disconnected"
                                if socket_to_remove in sockets_list:
                                    sockets_list.remove(socket_to_remove)
                            if clients_cookie != cookie_dictionary[pseudo]:
                                connection.sendall("$cookie_id_failed\n".encode(FORMAT))
                                connection.sendall("Identification échouée\n".encode(FORMAT))
                            else:
                                # delete the each_client from the dictionary
                                del clients_dict[copycatsocket]
                                clients_dict[client_key][0] = pseudo
                                clients_dict[client_key][1] = "connected"
                                clients_dict[client_key][2] = f"last-heartbeat: {time.time()}"
                                connection.sendall("Reconnexion réussie!\n".encode(FORMAT))
                        else:
                            connection.sendall("Pseudo déjà pris!\n".encode(FORMAT))
                    else:
                        clients_dict[(connection, client_address)] = [pseudo, "connected", f"last-heartbeat: {time.time()}", "alive"]
                        sockets_list.append((connection, client_address))
                        cookie = bake_cookie_id()
                        cookie_dictionary[pseudo] = str(cookie)
                        connection.sendall(f"$cookie={cookie}\n".encode(FORMAT))
                else:
                    pass
            else:
                pseudo = clients_dict[(connection, client_address)][0]  # Retrieve pseudo from dictionary
                if client_message == "$HEARTBEAT":
                    clients_dict[connection][2] = f"last-heartbeat:{time.time()}"
                    connection.sendall("$HEARTBEAT\n".encode(FORMAT))
                    print(f"Received heartbeat from {pseudo}")
                if client_message.startswith('@'):
                    private_message = True
                    if len(client_message.split(' ')) < 2:
                        connection.sendall("Veuillez spécifier le destinataire et le message.\n".encode(FORMAT))
                    else:
                        pseudo_list, message = parse_private_message(client_message)
                        for pseudo_destinataire in pseudo_list:
                            for clients_key, clients_values in clients_dict.items():
                                if clients_values[0] == pseudo_destinataire:
                                    conn, addr = clients_key
                                    if clients_values[1] == "connected":
                                        conn.sendall(f"Message privé de {pseudo}: {message}\n".encode(FORMAT))
                                    else:
                                        connection.sendall(f"Le joueur {pseudo_destinataire} n'est pas connecté.\n".encode(FORMAT))
                            # if the pseudo doesn't exist in the dictionary
                            if pseudo_destinataire not in [var[0] for key, var in clients_dict.items()]:
                                connection.sendall(f"Le joueur {pseudo_destinataire} n'existe pas.\n".encode(FORMAT))
                elif client_message.startswith('!'):
                    if client_message == "!DISCONNECT":
                        socket_to_remove = (connection, client_address)
                        connection.close()
                        clients_dict[(connection, client_address)][1] = "disconnected"
                        if socket_to_remove in sockets_list:
                            sockets_list.remove(socket_to_remove)
                    elif client_message == "!list":
                        connection.sendall(f"Nombre de joueurs connectés: {len(clients_dict)}\n".encode(FORMAT))
                        for client_socket, val in clients_dict.items():
                            connection.sendall(f"{val[0]} : {val[1]}\n".encode(FORMAT))
                    elif client_message == "!online_status":
                        for client_socket, val in clients_dict.items():
                            connection.sendall(f"Statut en ligne du joueur {val[0]}: {val[1]}\n".encode(FORMAT))
                    elif client_message == "!last-heartbeats":
                        for client_socket, val in clients_dict.items():
                            connection.sendall(f"Joueur: {val[0]} - Dernier battement de coeur: {val[2]}\n".encode(FORMAT))
                else:
                    if private_message is False:
                        for client_socket, val in clients_dict.items():
                            conn, addr = client_socket
                            if client_socket != server_socket and client_socket != connection:
                                if val[1] == "connected":  # Check if client is still connected
                                    conn.sendall(f"{pseudo}: {client_message}\n".encode(FORMAT))
        else:
            pass
    except Exception as error:
        print("Erreur lors de la réception des données :", error)
        if error.errno == errno.EBADF:
        # Handle "Bad file descriptor" error gracefully
            print("File descriptor:", connection.fileno())
            print("Socket closed. Ignoring further processing.")
        clients_dict[(connection, client_address)][1] = "fucked up"
        #if (connection, client_address) in sockets_list:
        #    sockets_list.remove((connection, client_address))

def signal_handler(sig, frame):
    """Handle graceful shutdown on SIGINT."""
    print("\n[SHUTDOWN] Server is shutting down...")
    for client, info in clients_dict.items():
        if info[1] == "connected":
            client[0].send(SHUTDOWN_MESSAGE.encode(FORMAT))
            client[0].close()
    # gracefully close the server socket
    server.close()
    sys.exit(0)

def how_many_players():
    """Return the number of connected players."""
    return len(players)

def check_heartbeat():
    global cache_info_stack
    global clients_dict
    while True:
        time.sleep(5)
        try:
            for clients, info in clients_dict.items():
                if info[0] is None:
                    continue
                else:
                    last_heartbeat_of_client = info[2].split(":")[1]
                    last_heartbeat_of_client = float(last_heartbeat_of_client)
                    if (last_heartbeat_of_client < time.time() - 15) and clients_dict[clients][1] != "disconnected":
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
    global game_started
    print(f"[NEW CONNECTION] {client_address} connected.")
    if game_started:
        connection.sendall("La partie a déjà commencé. Tenter de vous connecter avec votre ancien pseudo. \n".encode(FORMAT))
        
    clients_dict[(connection, client_address)] = [None, "connected", f"last-heartbeat: {time.time()}", "alive"]
    # sockets_list = creation_socket(server)
    try:
        if game_started is False:
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

def handle_server_input():
    global clients_dict
    global game_started
    while True:
        command = input("Enter a command: ")
        if command == "!list":
            print(f"Number of connected players: {how_many_connected()}")
            for _, info in clients_dict.keys():
                if info[1] == "connected":
                    print(f"Player: {info[0]} - {info[1]}")
        elif command == "!online_status":
            print("Online status of players:")
            for _, info in clients_dict.keys():
                print(f"Player status: {info[1]}")
        elif command == "!last-heartbeats":
            print("The last heartbeats of each player is:")
            for _, info in clients_dict.items():
                print(f"Player: {info[0]} - {info[2]}")
        elif command == "!shutdown":
            for client in clients_dict.keys():
                if clients_dict[client][1] == "connected":
                    client[0].sendall(SHUTDOWN_MESSAGE.encode(FORMAT))
                    client[0].close()
            server.close()
            sys.exit(0)
        elif command == "!start":
            game_started = True
            print("Game started.")
        # !suspend <pseudo> <reason>
        elif command.startswith("!suspend"):
            if len(command.split(' ')) > 2:
                command, pseudo, reason = command.split(' ', 2)
            else:
                command, pseudo = command.split(' ', 1)
            if pseudo in [client[0] for client in clients_dict.values()]:
                for client_socket, val in clients_dict.items():
                    if val[0] == pseudo:
                        # send a $suspend message to the client
                        client_socket[0].sendall(f"$SUSPEND\n".encode(FORMAT))
                        if len(command.split(' ')) > 2:
                            client_socket[0].sendall(f"Vous avez été suspendu pour la raison suivante: {reason}\n".encode(FORMAT))
                        else:
                            client_socket[0].sendall(f"Vous avez été suspendu.\n".encode(FORMAT))
                        clients_dict[client_socket][3] = "suspended" 
            else:
                print("Le joueur n'existe pas.")
        # !ban <pseudo> <reason>
        elif command.startswith("!ban"):
            if len(command.split(' ')) > 2:
                command, pseudo, reason = command.split(' ', 2)
            else:
                command, pseudo = command.split(' ', 1)
            if pseudo in [client[0] for client in clients_dict.values()]:
                for client_socket, val in clients_dict.items():
                    if val[0] == pseudo:
                        # send a $ban message to the client
                        client_socket[0].sendall(f"$BAN\n".encode(FORMAT))
                        if len(command.split(' ')) > 2:
                            client_socket[0].sendall(f"Vous avez été banni pour la raison suivante: {reason}\n".encode(FORMAT))
                        else:
                            client_socket[0].sendall(f"Vous avez été banni.\n".encode(FORMAT))
                        clients_dict[client_socket][3] = "banned"
            else:
                print("Le joueur n'existe pas.")
        # !forgive <pseudo>
        elif command.startswith("!forgive"):
            command, pseudo = command.split(' ', 1)
            if pseudo in [client[0] for client in clients_dict.values()]:
                for client_socket, val in clients_dict.items():
                    if val[0] == pseudo:
                        clients_dict[client_socket][3] = "alive"
                        if val[1] == "connected":
                            # send a $forgive message to the client
                            client_socket[0].sendall(f"$FORGIVE\n".encode(FORMAT))
                            client_socket[0].sendall("Vous avez été excusé. Vous pouvez envoyer des messages.\n".encode(FORMAT))
                        elif val[1] == "disconnected":
                            print("Le joueur est déconnecté mais n'est plus suspendu.")
            else:
                print("Le joueur n'existe pas.")
        elif command == "!help" or command == "!commands":
            print("Liste des commandes disponibles:")
            print("!list : liste les joueurs connectés")
            print("!online_status : affiche le statut en ligne de chaque joueur")
            print("!last-heartbeats : affiche les derniers battements de coeur de chaque joueur")
            print("!shutdown : arrête le serveur")
            print("!start : démarre la partie et empêche les nouveaux joueurs de se connecter")
            print("!suspend <pseudo> <raison> : suspend un joueur")
            print("!ban <pseudo> <raison> : banni un joueur")
            print("!forgive <pseudo> : excuser un joueur")
        else:
            print("Commande inconnue.")

# function to send to connected clients heartbeats
def send_heartbeats():
    global clients_dict
    while True:
        time.sleep(5)
        for client, info in clients_dict.items():
            if info[0] is not None and info[1] == "connected":
                client[0].sendall("$HEARTBEAT\n".encode(FORMAT))
                print(f"Sent heartbeat to {info[0]}")

def checkifgameisdone():
    global clients_dict
    global game_started
    while True:
        if game_started:
            if how_many_connected() == 0:
                print("Game is done.")
                game_started = False
        time.sleep(5)

def main():
    global clients_dict
    server.listen()
    print(f"[LISTENING] server is listening on {SERVER}")
    # thread2 = threading.Thread(target=check_heartbeat)
    # thread2.daemon = True
    # thread2.start()
    # thread4 = threading.Thread(target=send_heartbeats)
    # thread4.daemon = True
    # thread4.start()
    thread3 = threading.Thread(target=handle_server_input)
    thread3.daemon = True
    thread3.start()
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.daemon = True
        thread.start()
        print()
        print(f"[ACTIVE CONNECTIONS] {how_many_connected()}")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    print("[STARTING] server is starting...")
    main()

