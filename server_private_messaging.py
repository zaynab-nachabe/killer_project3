import socket
import select

HOST = ''   # Adresse IP du serveur, j'ai laissé vide pour accepter les connexions sur toutes les interfaces réseau
PORT = 12345  # Port sur lequel le serveur écoute

# Dictionnaire pour stocker les pseudonymes des clients
clients = {}

def creation_socket(server_socket):
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Liaison du socket à l'adresse et au port spécifiés
        server_socket.bind((HOST, PORT))
        # Écoute des connexions entrantes
        server_socket.listen()

        print("Serveur démarré sur le port", PORT)
        
        # Liste des sockets à surveiller pour les entrées
        sockets_list = [server_socket]
        return sockets_list

def gestion_message(sock, server_socket, sockets_list):
    try:
        client_message = sock.recv(1024).decode()
        if client_message:
            print(f"Message du client {clients[sock]} : {client_message}")
            
            # Vérifier si le message est un message privé ou destiné à tous les clients
            if client_message.startswith('@tous'):
                # Transmettre le message à tous les clients, sauf à l'expéditeur
                for client_socket, pseudo in clients.items():
                    if client_socket != server_socket and client_socket != sock:
                        client_socket.sendall(f"{pseudo}: {client_message[6:]}\n".encode())
            elif client_message.startswith('@'):
                # Trouver le destinataire du message privé
                dest_pseudo, message = client_message[1:].split(' ', 1)
                dest_socket = None
                for client_socket, pseudo in clients.items():
                    if pseudo == dest_pseudo:
                        dest_socket = client_socket
                        break
                # Envoyer le message privé au destinataire ou afficher un message d'erreur
                if dest_socket:
                    dest_socket.sendall(f"{clients[sock]} (privé): {message}\n".encode())
                else:
                    sock.sendall(b"Le destinataire n'existe pas.\n")
            else:
                # Transmettre le message à tous les clients, sauf à l'expéditeur
                for client_socket, pseudo in clients.items():
                    if client_socket != server_socket and client_socket != sock:
                        client_socket.sendall(f"{clients[sock]}: {client_message}\n".encode())
        else:
            # Si le client a fermé la connexion, on le retire de la liste des sockets à surveiller
            sock.close()
            del clients[sock]
            sockets_list.remove(sock)
    except Exception as e:
        # En cas d'erreur, on ferme le socket et on le retire de la liste
        print("Erreur lors de la réception des données :", e)
        sock.close()
        del clients[sock]
        sockets_list.remove(sock)
    
def handle_client():
    # Création du socket TCP
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        sockets_list = creation_socket(server_socket)

        while True:
            # Utilisation de select pour surveiller les sockets prêts à être lus
            readable_sockets, _, _ = select.select(sockets_list, [], [])

            for sock in readable_sockets:
                # Si le socket prêt à être lu est le socket du serveur, cela signifie qu'il y a une nouvelle connexion entrante
                if sock == server_socket:
                    connection, client_address = server_socket.accept()
                    print('Nouveau client connecté depuis', client_address)
    
                    # Demander le pseudo au client
                    connection.sendall(b'Veuillez entrer votre pseudo : ')
                    pseudo = connection.recv(1024).decode().strip()
                    
                    # Stocker le pseudo du client dans le dictionnaire
                    clients[connection] = pseudo
                    
                    # Ajout du nouveau socket client à la liste des sockets à surveiller
                    sockets_list.append(connection)
                # Sinon, c'est un socket client existant, on reçoit les données et on les renvoie à tous les clients
                else:
                    gestion_message(sock, server_socket, sockets_list)

if __name__ == "__main__":
    handle_client()