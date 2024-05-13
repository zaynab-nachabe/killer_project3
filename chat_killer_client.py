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

if len(sys.argv) > 1:
    PORT = int(sys.argv[1])
# Initialize the client variable to be changed later by the connect function, then used by other functions
client = None
# Server status global variable, changed with heartbeat
server_Disconnected = threading.Event()
# Flag for when the user chooses to close after a disconnect through the FIFO, changing logic of SIGCHLD handling
user_Closed = False
# Storing pseudo chosen by user
pseudo_Global = None
# threading event for cookie directory creation function ; threading event to know when to write cookie data
cookie_dir_created = threading.Event()
# Store cookie data
cookie_data = None
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
        print("Connection Refused.") 

def send(msg):
    message = msg.encode(FORMAT)
    client.send(message)

def create_cookie_dir(pseudo): # creates the cookie file for a specific pseudo as soon as pseudo is chosen
    global cookie_dir_created
    try:
        os.mkdir(f"/var/tmp/{pseudo}") # creates pseudo directory
        cookie_dir_created.set()
    except OSError as err:
        if err.errno == 17:
            pass
        else:
            print(f"Erreur creation directory \"/var/tmp/{pseudo}\": (%d)"%(err.errno),file=sys.stderr)


def FIFO_to_Server(fifo, log): # function handling the user inputs to send to server through a FIFO
    global user_Closed
    global pseudo_Global
    global listening_Thread
    global server_Disconnected
    global cookie_dir_created
    while True:
        try:
            pseudo_chosen = False
            log_PleaseChoosePseudo = "You must choose a username. Please make your choice with the following format: \n'pseudo=example'\nOtherwise, enter '!DISCONNECT' to leave the server.\n"
            os.write(log, log_PleaseChoosePseudo.encode(FORMAT))
            while True or not pseudo_chosen: # Continues to listen even if no data to send because of invalid inputs from user
                if server_Disconnected.is_set():
                    break
                select.select([fifo], [], []) # Wait for user input to FIFO
                msg = os.read(fifo, 2048) # Read the FIFO
                msg = msg.decode(FORMAT).strip('\n') # Convert bytes to str and strip newline
                if not pseudo_chosen:
                    if msg == DISCONNECT_MESSAGE:
                        send(msg)
                        break
                    elif msg.startswith("pseudo=") and msg != "pseudo=":
                        pseudo_Local = msg[7:]
                        pseudoL_stripped = pseudo_Local.strip()
                        pseudoL_stripped_replaceWS = pseudoL_stripped.replace(" ", "_")
                        if pseudoL_stripped_replaceWS.lower() != "admin":
                            pseudo_Global = pseudoL_stripped_replaceWS
                            pseudoMsgFormatted = f"pseudo={pseudo_Global}"
                            send(pseudoMsgFormatted)
                            if cookie_dir_created.wait(timeout=1):
                                pseudo_chosen = True
                                continue
                            else:
                                log_PseudoUnavailableMsg = "Pseudo unavailable. Please choose a different one.\n"
                                os.write(log, log_PseudoUnavailableMsg.encode(FORMAT))
                                continue
                        else:
                            log_InvalidPseudoMsg = "Sorry, your Pseudo is invalid. Pseudos can't contain spaces, nor be 'Admin' and it's variations.\n"
                            os.write(log, log_InvalidPseudoMsg.encode(FORMAT))
                            continue
                    else:
                        log_nonPseudoOrDisconnectErrMsg ="Sorry, you must choose a username with 'pseudo=username' or disconnect with '!DISCONNECT'.\n"
                        os.write(log, log_nonPseudoOrDisconnectErrMsg.encode(FORMAT))
                        continue
                if msg == DISCONNECT_MESSAGE:
                    send(msg)
                    break
                elif msg.startswith('!'):
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
                    reconnectingLogMsg = "Attempting to Reestablish Connection...\n"
                    os.write(log, reconnectingLogMsg.encode(FORMAT))
                    reconnected = connect_server()
                    if reconnected == False:
                        reconnectFailLogMsg = "Reconnection failed. Checking Server status ...\n"
                        os.write(log, reconnectFailLogMsg.encode(FORMAT))
                        continue
                    else:
                        reconnectTrueLogMsg = "Connection Reestablished.\n"
                        os.write(log, reconnectTrueLogMsg.encode(FORMAT))
                        listening_Thread = threading.Thread(target=receive, args=(log,client))
                        listening_Thread.daemon = True
                        listening_Thread.start()
                        break # exit this loop and return to the initial state with the new connection
                else:
                    unexpectedLogMsg = "Unexpected input. Please enter either '!close' or '!reconnect'.\n"
                    os.write(log, unexpectedLogMsg.encode(FORMAT))
                    continue
        
def receive(fd, socket):
    global cookie_dir_created
    global cookie_data
    global cookie_baked
    global pseudo_Global
    while True:
        try:
            beating_heart, _, _ = select.select([socket], [], [], 1) # Wait for server
        except ValueError:
            print("Value error")
            break
        if beating_heart:
            try:
                server_message = socket.recv(2048).decode(FORMAT)
                if not server_message:
                    log_ConnectionDroppedMsg = "Connection closed, waiting to reconnect ..."
                    os.write(fd, log_ConnectionDroppedMsg.encode(FORMAT))
                    break
                if server_message:
                    if server_message.startswith("$cookie="):
                        cookie_data = server_message[8:]
                        create_cookie_dir(pseudo_Global)
                        with open(f"/var/tmp/{pseudo_Global}/cookie", "w") as cookie_file:
                            cookie_file.write(cookie_data)
                            log_PseudoChosenChatRoomMsg = "Pseudo accepted. Profile created. Welcome to the Chat Room !\n"
                            os.write(fd, log_PseudoChosenChatRoomMsg.encode(FORMAT))
                    elif server_message.startswith("$send_cookie"):
                        log_CookieReconnectMsg = "\nAttempting to reconnect with a known pseudo, authenticating ...\n"
                        os.write(fd, log_CookieReconnectMsg.encode(FORMAT))
                        try:
                            with open(f"/var/tmp/{pseudo_Global}/cookie", "r") as file:
                                cookie_file_contents = file.read()
                                cookie_stripped = cookie_file_contents.strip()
                                socket.sendall(cookie_stripped.encode(FORMAT))
                        except:
                            log_CookieSendErrorMsg = "Error occured during cookie data retrieval and sending...\n"
                            os.write(fd, log_CookieSendErrorMsg)
                            errorMsg = "Error"
                            socket.sendall(errorMsg.encode(FORMAT))
                    elif server_message.startswith("$cookie_id_failed"):
                        log_CookieIdFailedMsg = "Authentification failed. Check spelling for the pseudo.\n"
                        os.write(fd, log_CookieIdFailedMsg)
                    elif server_message.startswith("Pseudo déjà pris!"):
                        #logic handled in FIFO function
                        pass
                    elif server_message.startswith("$HEARTBEAT?"):
                        log_sHBMsg = "$HEARTBEAT!"
                        socket.sendall(log_sHBMsg.encode(FORMAT))
                    elif server_message.startswith("$HEARTBEAT!"):
                        # Heartbeat received, no parsing necessary, connection considered active
                        pass
                    elif server_message.startswith("!SERVER_SHUTDOWN"):
                        log_ServerShutdownMsg = "Server has sent a shutdown. Disconnecting ...\n"
                        os.write(fd, log_ServerShutdownMsg.encode(FORMAT))
                        server_Disconnected.set()
                        break
                    else:
                        os.write(fd, server_message.encode(FORMAT))   
            except Exception as e:
                if e.errno == 9:
                    break
                else:
                    print('Exception occured for receive function:', e)
                    break
        else:
            heartbeatMsg = "$HEARTBEAT?"
            socket.sendall(heartbeatMsg.encode(FORMAT))
            checking_pulse, _, _ = select.select([socket], [], [], 2)
            if checking_pulse:
                continue
            else:
                heartbeatTimeoutMsg = "No Server Heartbeat Detected. Disconnecting ..."
                os.write(fd, heartbeatTimeoutMsg.encode(FORMAT))
                server_Disconnected.set()
                break

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
    print("\nUnexpected SIGINT received, cleaning up and exiting...")
    client_Cleanup()

def main():
    global cookie_dir_created
    global cookie_data
    global cookie_baked
    global pseudo_Global
    global unique_FIFO
    global unique_LOG
    global client

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
    log_boot_msg = "Connected to the server. \nType messages and commands in killer.fifo terminal.\n"
    os.write(fdr, log_boot_msg.encode(FORMAT))

    # thread for xterm crash tolerance
    open_ChatWindow()
    open_GameLobby()

    # thread for sending to server
    
    FIFO_to_Server_Thread = threading.Thread(target=FIFO_to_Server, args=(fdw,fdr))
    FIFO_to_Server_Thread.daemon = True
    FIFO_to_Server_Thread.start()
 
    # thread for writing server messages to log
    listening_Thread = threading.Thread(target=receive, args=(fdr,client))
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
