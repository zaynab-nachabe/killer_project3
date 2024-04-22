from modulateur import players, player_status
import os, signal, hashlib

def start_game():
    """Start the game"""
    global game_started
    if not game_started:
        game_started = True
        print("The game has started.")
    else:
        print("The game has already started. No new players can join.")


def ban_player(player_name):
    """Ban a player from the game"""
    if player_name in players:
        print(f"Player {player_name} has been banned.")
        # Get the player's socket
        player_socket = players[player_name]
        # Close the player's socket
        player_socket.close()
        # Remove the player from the game
        del players[player_name]
        # Notify other players about the ban
        for name, socket in players.items():
            if name != player_name:  # Exclude the banned player
                message = f"Player {player_name} has been banned from the game."
                # Send the message to the player
                socket.sendall(message.encode())
    else:
        print(f"Player {player_name} is not currently in the game.")


def suspend_player(player_name):
    """Suspend a player"""
    if player_name in players:
        print(f"Player {player_name} has been suspended.")
        # Get the player's socket
        player_socket = players[player_name]
        # Send a suspend command to the player's terminal
        suspend_command = "!suspend"  # Define a custom command to suspend the player
        player_socket.sendall(suspend_command.encode())
    else:
        print(f"Player {player_name} is not currently in the game.")


def forgive_player(player_name):
    """Forgive a suspended player"""
    if player_name in players:
        pass
    else:
        
        print(f"Suspension forgiven for player {player_name}")
        # Send SIGCONT signal to the player's terminal
        os.kill(player_status[player_name]['pid'], signal.SIGCONT)



def broadcast_file(file_path):
    """Broadcast a file to all players"""
    if not os.path.exists(file_path):
        print(f"File '{file_path}' does not exist.")
        return

    # Read the file contents
    with open(file_path, 'rb') as file:
        file_data = file.read()

    # Generate a hash of the file data to uniquely identify it
    file_hash = hashlib.sha256(file_data).hexdigest()

    # Check if the file is already cached
    cached_file_path = os.path.join(CACHE_DIR, file_hash)
    if not os.path.exists(cached_file_path):
        # Cache the file if it's not already cached
        with open(cached_file_path, 'wb') as cache_file:
            cache_file.write(file_data)

    # Iterate over all player sockets and send the file
    for player_socket in players.values():
        try:
            # Send the file hash to indicate the file to be retrieved
            player_socket.sendall(file_hash.encode())
            ack = player_socket.recv(1024).decode()
            if ack == "READY":
                with open(cached_file_path, 'rb') as cached_file:
                    while True:
                        data = cached_file.read(1024)
                        if not data:
                            break
                        player_socket.sendall(data)
            else:
                print(f"Player {player_socket} not ready to receive file.")
        except Exception as e:
            print(f"Error broadcasting file to player: {e}")

    print("File broadcasted to all players.")




def send_file(client_socket, arguments):
    """Send a file to a specific player"""
    # Implement file sending logic here
    pass


def list_players():
    """List all players"""
    # Implement player listing logic here
    pass

def reconnect_player(client_socket):
    """Reconnect a player after a server crash"""
    # Implement player reconnection logic here
    pass


def handle_chat_message(message):
    """Handle a chat message"""
    # Implement chat message handling logic here
    pass