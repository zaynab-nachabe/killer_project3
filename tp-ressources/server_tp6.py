import os, select, socket, sys, time

MAXBYTES = 4096

if len(sys.argv)!= 2:
    print('Usage:', sys.argv[0], 'port')
    sys.exit(1)

PORT = int(sys.argv[1])
sockaddr = ('', PORT)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # IPv4, TCP
s.bind(sockaddr)
s.listen(5)
print('Serveur démarré sur le port', PORT)

clients = []

while True:
    rlist, wlist, xlist = select.select([s, sys.stdin], [], [])
    for sock in rlist:
        if sock == s :
            client_socket, client_addr = sock.accept()
            print('Nouveau client connecté depuis', client_addr)
            clients.append(client_socket)
            client_socket.send(b'Bienvenue sur le serveur!\n')
            client_socket.send(b'Liste des commandes supportees :\n')
            client_socket.send(b'@tous : envoyer un message a tous les clients\n')
            client_socket.send(b'wall : envoyer un message a tous les clients\n')
            client_socket.send(b'kick : bannir un client\n')
            client_socket.send(b'shutdown n : terminer avec delai\n')

        if sock == sys.stdin:
            line = sys.stdin.readline()
            if line.startswith('wall '):
                message = line[5:].strip()
                for client in clients:
                    client.send(message.encode())
            elif line.startswith('kick '):
                client_to_kick = line[5:].strip()
                for i, client in enumerate(clients):
                    if client.getpeername()[0] == client_to_kick:
                        clients.pop(i)
                        client.send(b'Vous avez ete banni du serveur.\n')
                        client.close()
                        break
            elif line.startswith('shutdown '):
                delay = int(line[9:].strip())
                for client in clients:
                    client.send(('Le serveur va s\'arrêter dans ' + str(delay) + ' secondes.\n').encode())
                time.sleep(delay)
                break
            else:
                print('Commande inconnue.')