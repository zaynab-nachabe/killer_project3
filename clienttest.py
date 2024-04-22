import os, commands

# create files for game
pid_files = os.fork()

if pid_files == 0:
    try:
        os.execl("/usr/bin/touch", "touch", "/var/tmp/killer.fifo", "/var/tmp/killer.log")
    except FileNotFoundError:
        print("touch not found, please ensure it's installed and the path is correct.")

# Open the game windows
pid_ChatWindow = os.fork()
commands.open_ChatWindow(pid_ChatWindow)

pid_GameLobby = os.fork()
commands.open_GameLobby(pid_GameLobby)