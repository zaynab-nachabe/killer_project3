import os, commands

# create files for game
pid_files = os.fork()

if pid_files == 0:
    os.execl("/bin/touch", "touch", "/var/tmp/killer.fifo", "/var/tmp/killer.log")

# Open the game windows

pid_ChatWindow = os.fork()
commands.open_ChatWindow(pid_ChatWindow)

pid_GameLobby = os.fork()
commands.open_GameLobby(pid_GameLobby)