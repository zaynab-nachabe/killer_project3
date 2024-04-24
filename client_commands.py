import os

def open_ChatWindow(pid):
    try:
        if pid == 0:
            os.execl("/usr/bin/xterm", "xterm", "-e", "cat > /var/tmp/killer.fifo")
    except FileNotFoundError:
        print("xterm not found, please ensure it's installed and the path is correct.")

def open_GameLobby(pid):
    try:
        if pid == 0:
            os.execl("/usr/bin/xterm", "xterm", "-e", "tail -f /var/tmp/killer.log")
    except FileNotFoundError:
        print("xterm not found, please ensure it's installed and the path is correct.")