# chat_killer_client.py : l'exécutable lancé par un joueur. 
# Cet exécutable se détache du terminal (double fork) et crée deux nouveaux terminaux, 
# l'un affichant les messages, l'autre permettant de saisir des commandes et des messages. 
# Les commandes commencent par un !, les messages privés commencent par @toto (pour envoyer à toto), 
# ou @toto @titi @tata pour envoyer un message privé à plusieurs destinataires. Lorsque le joueur meurt, 
# toutes les fenêtres et les processus créés pour lui doivent être tués
import socket
import sys
import os
import select
import errno

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)
    server_message = client.recv(2048).decode(FORMAT)
    print("Server:", server_message)

def main():
    # create files for game
    try:
        fdr = os.open("/var/tmp/killer.log", os.O_RDWR|os.O_CREAT)
    except OSError as err:
        print("Erreur creation log \"/var/tmp/killer.log\": (%d)"%(err.errno),file=sys.stderr)
    try:
        os.mkfifo("/var/tmp/killer.fifo")
    except OSError as err:
        print("Erreur creation fifo \"/var/tmp/killer.fifo\": (%d)"%(err.errno),file=sys.stderr)
        fdw = os.open("/var/tmp/killer.fifo", os.O_RDWR)

    # Write connection info to log
    log_boot_msg = "Connected to the server. \nType messages in killer.fifo terminal, '!DISCONNECT' to exit.\nPlease choose a username."
    os.write(fdr, log_boot_msg.encode(FORMAT))

    # Open the game windows and conserve pids
    pid_ChatWindow = os.fork()
    try:
        if pid_ChatWindow == 0:
            os.execl("/usr/bin/xterm", "xterm", "-e", "cat > /var/tmp/killer.fifo")
    except FileNotFoundError:
        print("xterm not found, please ensure it's installed and the path is correct.")

    pid_GameLobby = os.fork()
    try:
        if pid_GameLobby == 0:
            os.execl("/usr/bin/xterm", "xterm", "-e", "tail -f /var/tmp/killer.log")
    except FileNotFoundError:
        print("xterm not found, please ensure it's installed and the path is correct.")

    try:
        while True:
            select.select([fdw], [], []) # Wait for user input to FIFO
            msg = os.read(fdw, 1024) # Read the FIFO
            msg = msg.decode(FORMAT).strip('b\n') # Convert bytes to str and strip 'b' and newline        
            if msg == DISCONNECT_MESSAGE:
                send(msg)
                break
            elif msg.startswith('!'):
                # Handle command message
                send(msg)
            elif '@' in msg:
                # Handle private message
                send(msg)
            else:
                send(msg)
    except KeyboardInterrupt:
        send(DISCONNECT_MESSAGE)
    finally:
        print("Disconnecting from server...")
        client.close()
        sys.exit(0)

if __name__ == "__main__":
    main()
