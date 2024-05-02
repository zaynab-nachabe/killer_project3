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
import threading
import signal
import time

HEADER = 64
PORT = 5050
SERVER = "127.0.0.1" # socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"

# Initialize the client variable to be changed later by the connect function, then used by other functions
client = None
# Flag for when the user chooses to close after a disconnect through the FIFO, changing logic of SIGCHLD handling
user_Closed = False

# Initialize pid variables for xterms, to be changed dynamically to correct values
pid_ChatWindow = None
pid_GameLobby = None

# Retrieve information for file names
unique_pid = os.getpid()
unique_FIFO = f"killer{str(unique_pid)}.fifo"
unique_LOG = f"killer{str(unique_pid)}.log"

def connect_server():
    global ADDR
    global client
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(ADDR)
    except ConnectionRefusedError:
        print('Connection Refused')
"""
def heartbeat_client():
    global client
    try:
        while True:
            time.sleep(10)
            send("$HEARTBEAT")
            print("Sent Heartbeat")
    except KeyboardInterrupt:
        print("Ctrl+C detected. Ending heartbeat ...")
"""
def send(msg):
    message = msg.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    client.send(send_length)
    client.send(message)

def create_cookie_dir(pseudo): # creates the cookie file for a specific pseudo as soon as pseudo is chosen
    try:
        os.mkdir(f"/var/tmp/{pseudo}") # creates pseudo directory
    except OSError as err:
        print(f"Erreur creation directory \"/var/tmp/{pseudo}\": (%d)"%(err.errno),file=sys.stderr)
    try:
        fd_c = os.open(f"/var/tmp/{pseudo}/cookie", os.O_RDWR|os.O_TRUNC|os.O_CREAT) # creates cookie and leaves fd_c open, waiting to receive cookie data from server
    except OSError as err:
        print(f"Erreur creation cookie \"/var/tmp/{pseudo}/cookie\": (%d)"%(err.errno),file=sys.stderr)

def FIFO_to_Server(fifo, log): # function handling the user inputs to send to server through a FIFO
    global user_Closed
    try:
        pseudo_chosen = False
        while True or not pseudo_chosen: # Continues to listen even if no data to send because of invalid inputs from user
            select.select([fifo], [], []) # Wait for user input to FIFO
            msg = os.read(fifo, 2048) # Read the FIFO
            msg = msg.decode(FORMAT).strip('\n') # Convert bytes to str and strip newline
            if not pseudo_chosen:
                if msg == DISCONNECT_MESSAGE:
                    send(msg)
                    break
                elif msg.startswith("pseudo=") and msg != "pseudo=":
                    pseudo_player = msg[7:]
                    create_cookie_dir(pseudo_player)
                    pseudo_chosen = True
                else:
                    log_nonPseudoOrDisconnectErrMsg ="Sorry, you must choose a username with 'pseudo=username' or disconnect with '!DISCONNECT'.\n"
                    os.write(log, log_nonPseudoOrDisconnectErrMsg.encode(FORMAT))
                    continue
            if msg == DISCONNECT_MESSAGE:
                send(msg)
                break
            elif msg.startswith('!'):
                # Handle command message
                send(msg)
            else:
                send(msg)
    except KeyboardInterrupt:
        send(DISCONNECT_MESSAGE)
    finally:
        print("Disconnecting from server...")
        client.close()
        disconnectLogMessage = "You've disconnected from the server. If you would like to reconnect, enter '!reconnect'.\nOtherwise, enter '!close'.\n"
        os.write(log, disconnectLogMessage.encode(FORMAT))
        closed_flag = False
        while not closed_flag:
            select.select([fifo], [], []) # Wait for user input to FIFO
            close_dc_msg = os.read(fifo, 2048)
            close_dc_msg = close_dc_msg.decode(FORMAT).strip('\n')
            if close_dc_msg == "!close":
                print("Closing... Good Bye !")
                closingLogMsg = "Closing... Good Bye !\n"
                os.write(log, closingLogMsg.encode(FORMAT))
                user_Closed = True
                closed_flag = True
            elif close_dc_msg == "!reconnect":
                reconnectingLogMsg = "Reestablishing Connection...\n"
                os.write(log, reconnectingLogMsg.encode(FORMAT))
                connect_server()
                FIFO_to_Server(fifo, log)
            else:
                unexpectedLogMsg = "\nSorry, please enter either '!close' or '!reconnect'.\n"
                os.write(log, unexpectedLogMsg.encode(FORMAT))
                continue
        
def receive(fd):
    try:
        while True:
            try:
                select.select([client], [], []) # Wait for server
            except ValueError:
                break
            try:
                server_message = client.recv(2048).decode(FORMAT) + '\n'
            except OSError:
                if OSError.errno == 9:
                    print("Socket closed...")
                    break
            os.write(fd, server_message.encode(FORMAT))
    except Exception:
        print('Exception occured for receive function.')

# sigchld handler for both xterms, gets the pid associated with the caught SIGCHLD and reopens the correct xterm
def sigchld_xterm_handler(signum, frame):
    global pid_ChatWindow
    global pid_GameLobby
    print("One of the terminals was closed, reopening ...")
    caught_pid = os.wait()
    if caught_pid[0] == pid_GameLobby:
        open_GameLobby()
    elif caught_pid[0] == pid_ChatWindow:
        open_ChatWindow()
    
def open_ChatWindow():
    global unique_FIFO
    global pid_ChatWindow
    pid_ChatWindow = os.fork()
    try:
        if pid_ChatWindow == 0:
            try:
                os.execl("/usr/bin/xterm", "xterm", "-e", f"cat > /var/tmp/{unique_FIFO}")
            except:
                os.execl("/opt/homebrew/bin/xterm", "xterm", "-e", f"cat > /var/tmp/{unique_FIFO}")
    except FileNotFoundError:
        print("xterm not found, please ensure it's installed and the path is correct.")

def open_GameLobby():
    global unique_LOG
    global pid_GameLobby
    pid_GameLobby = os.fork()
    try:
        if pid_GameLobby == 0:
            try:
                os.execl("/usr/bin/xterm", "xterm", "-e", f"tail -f /var/tmp/{unique_LOG}")
            except:
                os.execl("/opt/homebrew/bin/xterm", "xterm", "-e", f"cat > /var/tmp/{unique_FIFO}")
    except FileNotFoundError:
        print("xterm not found, please ensure it's installed and the path is correct.")

# General clean up function for the created files
def client_Cleanup():
    global unique_FIFO
    global unique_LOG
    global pid_ChatWindow
    global pid_GameLobby
    # close xterms
    os.kill(pid_ChatWindow, signal.SIGTERM)
    os.kill(pid_GameLobby, signal.SIGTERM)
    # delete temporary files
    print("Cleaning up files ...")
    os.remove(f'/var/tmp/{unique_FIFO}')
    os.remove(f'/var/tmp/{unique_LOG}')
    print("Temporary files deleted.")
    sys.exit(0)

# terminate gracefully if there is a ctrl-c, handles signal
def gracefulclean_signalhandler(signum, frame):
    signal.signal(signal.SIGCLD, signal.SIG_DFL)
    print(f"\nUnexpected SIGINT received, cleaning up and exiting...")
    client_Cleanup()

def main():
    global unique_FIFO
    global unique_LOG

    signal.signal(signal.SIGCHLD, sigchld_xterm_handler)
    signal.signal(signal.SIGINT, gracefulclean_signalhandler)

    connect_server()
    # create files for game
    try:
        fdr = os.open(f"/var/tmp/{unique_LOG}", os.O_RDWR|os.O_APPEND|os.O_TRUNC|os.O_CREAT)
    except OSError as err:
        print(f"Erreur creation log \"/var/tmp/{unique_LOG}\": (%d)"%(err.errno),file=sys.stderr)
    try:
        os.mkfifo(f"/var/tmp/{unique_FIFO}")
        fdw = os.open(f"/var/tmp/{unique_FIFO}", os.O_RDWR)
    except OSError as err:
        print(f"Erreur creation fifo \"/var/tmp/{unique_FIFO}\": (%d)"%(err.errno),file=sys.stderr)
        fdw = os.open(f"/var/tmp/{unique_FIFO}", os.O_RDWR)
    print("Xterm terminals opened. Please interact with the program through them.")
    # Write connection info to log
    log_boot_msg = "Connected to the server. \nType messages and commands in killer.fifo terminal.\nYou must choose a username. Please make your choice with the following format: \n'pseudo=example'\nOtherwise, enter '!DISCONNECT' to leave the server.\n"
    os.write(fdr, log_boot_msg.encode(FORMAT))

    # thread for xterm crash tolerance
    open_ChatWindow()
    open_GameLobby()

    # thread for sending to server
    
    FIFO_to_Server_Thread = threading.Thread(target=FIFO_to_Server, args=(fdw,fdr))
    FIFO_to_Server_Thread.daemon = True
    FIFO_to_Server_Thread.start()

    #heartbeat_Thread = threading.Thread(target=heartbeat_client)
    #heartbeat_Thread.start()

    # thread for writing server messages to log
    listening_Thread = threading.Thread(target=receive, args=(fdr,))
    listening_Thread.daemon = True
    listening_Thread.start()
    
    # Keeps main thread active until the either captured SIGINT or user closes FIFO with !close
    while not user_Closed:
        time.sleep(1)
    # Override signal that keeps xterms open
    signal.signal(signal.SIGCLD, signal.SIG_DFL)
    # close the open files
    os.close(fdr)
    os.close(fdw)
    client_Cleanup()
    
if __name__ == "__main__":
    main()
