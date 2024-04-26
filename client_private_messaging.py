import socket
import select
import sys

HOST = 'localhost'  # Adresse IP du serveur
PORT = 12345        # Port sur lequel le serveur écoute

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        # Connexion au serveur
        client_socket.connect((HOST, PORT))
        print("Bienvenu au chat multi_client!")
        print(b'Bienvenue sur le serveur!\n')
        print(b'Liste des commandes supportees :\n')
        print(b'@tous : envoyer un message a tous les clients\n')
        print(b'@pseudo : envoyer un message prive a un client\n\n')
        while True:
            # select pour surveiller les entrées sur le terminal et le socket client
            readable_sockets, _, _ = select.select([sys.stdin, client_socket], [], [])

            for sock in readable_sockets:
                # si l'entrée est le socket client = il y a des données à recevoir du serveur
                if sock == client_socket:
                    server_message = sock.recv(1024).decode()
                    if server_message:
                        print(server_message)
                    else:
                        print("Le serveur a fermé la connexion")
                        return
                # Sinon, c'est une entrée sur le terminal, on lit l'entrée utilisateur et on l'envoie au serveur
                else:
                    user_input = sys.stdin.readline().strip()
                    if user_input:
                        client_socket.sendall(user_input.encode())
                    else:
                        print("Entrée invalide")

if __name__ == "__main__":
    main()
