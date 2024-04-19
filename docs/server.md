# I am going to document a bit the server.py that I put online this morning. It has to be in French unfortunately

J'ai import les modules socket et threading
Le module threading en gros dans la video permet de ne pas faire de blocage dans le programme. C'est a dire que si on a une boucle infinie, on peut lancer une autre boucle infinie en meme temps. C'est ce que j'ai fait pour le serveur et le client.

Après j'ai mis des variables globales pour le serveur.
HEADER c'est la taille du message que le client va envoyer. C'est un entier de 64 bits. En gros, il doit envoyer en premier un message en 64 bits pour dire la taille du message qu'il va envoyer.
PORT c'est le port sur lequel le serveur va écouter. J'ai mis 5050 mais on peut mettre n'importe quel port.
SERVER c'est l'adresse IP du serveur. J'ai mis socket.gethostbyname(socket.gethostname()) pour que le serveur écoute sur l'adresse IP de la machine sur laquelle il est lancé. En gros ça permet de mettre l'adresse IP automatiquement, celle que la machine du serveur a sur le réseau en local.
ADDR c'est le tuple (SERVER, PORT) qui permet de dire au serveur sur quelle adresse IP et sur quel port il doit écouter.
FORMAT c'est le format dans lequel le message doit être envoyé. J'ai mis 'utf-8' mais on peut mettre n'importe quel format, dans la vidéo il met ça comme si c'était une convention.
DISCONNECT_MESSAGE c'est le message que le client doit envoyer pour se déconnecter. J'ai mis 'DISCONNECT' mais on peut mettre n'importe quel message. En gros ça permet de dire au serveur que le client veut se déconnecter. C'est un peu comme un mot de passe pour se déconnecter.

Après j'ai créé un socket avec socket.socket(socket.AF_INET, socket.SOCK_STREAM) qui permet de créer un socket en utilisant le protocole TCP/IP. En gros ça permet de dire au serveur qu'il va utiliser le protocole TCP/IP pour communiquer avec les clients.

Après j'ai bind le socket à l'adresse ADDR avec server.bind(ADDR). En gros ça permet de dire au serveur sur quelle adresse IP et sur quel port il doit écouter.

Puis, il y a la fonction handle_client() elle gère les nouvelles connections en créant un nouveau thread pour chaque client qui se connecte. Pour la faire simple, elle reçoit les messages des clients et les affiche dans la console du serveur. Si le client envoie le message DISCONNECT_MESSAGE, elle ferme la connexion avec le client.

La fonction start() permet de démarrer le serveur. Elle écoute sur le port PORT et attend les nouvelles connections. Quand un client se connecte, elle appelle la fonction handle_client() pour gérer la connexion avec le client.

Enfin, j'ai mis un print(f"[LISTENING] Server is listening on {SERVER}") pour dire au serveur qu'il écoute sur l'adresse IP de la machine sur laquelle il est lancé.
