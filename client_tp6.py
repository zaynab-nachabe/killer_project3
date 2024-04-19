import os, select, socket, sys, time

MAXBYTES = 4096

if len(sys.argv)!=3:
    print("Usage: ", sys.argv[0], "hote port")
    sys.exit(1)
1212
HOST = sys.argv[1]
PORT = int(sys.argv[2])
sockaddr = (HOST, PORT)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(sockaddr)
print("connected to: ", sockaddr)

pseudo = input('Entrez votre pseudo : ')

s.send(pseudo.encode())

print('Bienvenue sur le mini-chat!')
print('Liste des commandes supportées :')
print('@pseudo : envoyer un message à un client donné')
print('@tous : envoyer un message à tous les clients')

while True:
    rlist, wlist, xlist = select.select([0, s], [], [])

    if 0 in rlist:
        line = os.read(0, MAXBYTES)
        line = line.decode().strip() #
        if len(line) == 0:
            s.shutdown(socket.SHUT_RD)
            break
        if line.startswith('@'): #
            dest_pseudo = line[1:].strip() # 
            s.send((dest_pseudo + ' ' + line[1:]).encode()) #
        else:
            s.send(line)
    if s in rlist:
        data = s.recv(MAXBYTES)
        if len(data) == 0:
            break
        print(data.decode(), end='')
s.close()