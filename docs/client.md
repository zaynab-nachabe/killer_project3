# Doc du fichier chat_killer_client.py

C'est très similaire au serveur, il y a le import socket et les mêmes variables globales.

Puis ligne 17,on crée un socket avec socket.socket(socket.AF_INET, socket.SOCK_STREAM).
Ensuite, il y a ici client.connect(ADDR), c'est différent de bind car ici on se connecte au serveur et non pas on écoute.

On peut vorir avec le tuple de ADDR que l'on se connecte à la même adresse IP et au même port que le serveur. Pour des raisons pratiques, je crois que c'est écrit dans la doc du projet qu'on pourra mettre une adresse IP précise pour le serveur, un truc comme  192.168.1.1 mais je ne suis pas sûr.

Ensuite, il y a la fonction send(msg) qui permet d'envoyer un message au serveur. Elle prend en paramètre le message à envoyer et l'envoie au serveur.
Elle n'est pas hyper compliquée, elle envoie le message en utf-8 et affiche dans la console du client le message envoyé.

## Choses intéressantes à faire maintenant

Commencer par élaborer un protocole pour l'envoi du message initial avec le pseudo avec la connection. Quand le client se connecte au serveur, logiquement le serveur reçoit son adresse IP et son port. Il faudrait que le client envoie son pseudo en premier pour que le serveur puisse l'associer à son adresse IP et son port. C'est un peu comme un handshake dans le protocole TCP/IP. C'est une bonne idée de faire ça pour que le serveur puisse savoir qui est qui. On pourra ensuite dans le serveur stocker les valeurs dans un dictionnaire avec comme clé l'adresse IP et le port et comme valeur le pseudo.

Ensuite, il faudrait que le serveur puisse envoyer un message à tous les clients connectés. Pour ça, il faudrait que le serveur puisse stocker les connexions des clients dans une liste ou un dictionnaire. On pourra ensuite parcourir la liste ou le dictionnaire pour envoyer un message à tous les clients.
