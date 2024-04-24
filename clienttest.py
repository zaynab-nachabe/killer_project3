import client_commands as c_cmds
import os
import sys
import errno
# create files for game
pid_files = os.fork()

if pid_files == 0:
    try:
        os.open("/var/tmp/killer.log", os.O_RDONLY|os.O_CREAT)
    except OSError as err:
        print("Erreur creation log \"/var/tmp/killer.log\": (%d)"%(err.errno),file=sys.stderr)
    try:
        os.mkfifo("/var/tmp/killer.fifo")
    except OSError as err:
        print("Erreur creation fifo \"/var/tmp/killer.fifo\": (%d)"%(err.errno),file=sys.stderr)
    sys.exit(0)
else:
    os.wait()
# Open the game windows
pid_ChatWindow = os.fork()
c_cmds.open_ChatWindow(pid_ChatWindow)
pid_GameLobby = os.fork()
c_cmds.open_GameLobby(pid_GameLobby)