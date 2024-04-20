from modulateur import players, player_status
import os, signal

def start_game():
    """Start the game"""
    global game_started
    if not game_started:
        game_started = True
        print("The game has started.")
    else:
        print("The game has already started. No new players can join.")

def ban_player_message(player_name):
    """send a message to the player getting banned"""
    banning_message = "Vous avez été banni du jeu."
    player_status[player_name]['socket'].send(banning_message.encode()) # send the message to the player
    # I have to check with you guys how this is supposed to be implemented.

def ban_player(player_name):
    """Ban a player from the game"""
    if player_name in players:
        print(f"Player {player_name} has been banned.")
        # Send a message to the player getting banned
        ban_player_message(player_name)
        # Remove the player from the list of players
        players.remove(player_name)
    else:
        print(f"Player {player_name} is not currently in the game.")

def suspend_player(player_name):
    """Suspend a player"""
    # Implement player suspension logic
    print(f"Player {player_name} has been suspended")
    # Send SIGSTOP signal to the player's terminal
    os.kill(player_status[player_name]['pid'], signal.SIGSTOP)

def forgive_player_message(player_name):
    """Send a message to the player getting forgiven"""
    forgiving_message = "Votre suspension a été levée. Vous pouvez maintenant jouer. Ne recommencez pas."
    player_status[player_name]['socket'].send(forgiving_message.encode()) # send the message to the player

def forgive_player(player_name):
    """Forgive a suspended player"""
    # Implement player forgiveness logic here
    # Send a message to the player getting forgiven
    if player_name in players:
        forgive_player_message(player_name)
        print(f"Suspension forgiven for player {player_name}")
        # Send SIGCONT signal to the player's terminal
        os.kill(player_status[player_name]['pid'], signal.SIGCONT)
    else:
        print(f"Player {player_name} is not currently in the game.")

def broadcast_file(file_path):
    """Broadcast a file to all players"""
    # Implement file broadcasting logic here
    pass


def send_file(client_socket, arguments):
    """Send a file to a specific player"""
    # Implement file sending logic here
    pass


def list_players():
    """List all players"""
    # So that's when we do the !list command
    print("List of players:")
    for player in players:
        formatted_username = '@' + player.username
        print(formatted_username)


def reconnect_player(client_socket):
    """Reconnect a player after a server crash"""
    # That's when we do the !reconnect command
    # Implement player reconnection logic here
    pass


def handle_chat_message(message): 
    """Handle a chat message"""
    # Implement chat message handling logic here
    pass
