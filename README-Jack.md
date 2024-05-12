# Compte Rendu de Projet par Jack Massey

## Membres de l'équipe
- **Jack Massey** - Travail sur les fonctionnalités côté serveur.
- **Justin Diter** - Gestion du client.
- **Zaynab Nachabe** - Collaboration sur le développement serveur.

## Vue d'ensemble du projet
Ce projet visait à établir un système robuste de communication client-serveur. Les fonctionnalités clés mises en place comprennent la transmission de messages, les commandes serveur et la tolérance aux pannes côté client.

### Fonctionnalités principales
- **Communication Serveur-Client :** Mise en place d’un chemin de communication stable pour l’envoi et la réception de messages.
- **Tolérance aux pannes :** Implémentée côté client pour gérer efficacement les éventuelles défaillances du système.
- **Système de commandes :** Introduction de commandes serveur telles que `!list`, `!suspend`, `!ban`, et `!forgive`.

### Implémentations supplémentaires
- **Système de Heartbeat :** Bien que initialement incomplet lors de notre démonstration, cette fonctionnalité a été finalisée pour la soumission du projet, assurant des vérifications continues de la connexion entre le client et le serveur.
- **Système de cookies :** Permet aux clients de se reconnecter en utilisant la commande `!reconnect`, maintenant la continuité de la session.
- **Messagerie privée :** Système entièrement fonctionnel pour la gestion des messages privés des utilisateurs.
- **Méthodes de fermeture du serveur :** Méthodes intégrées pour éteindre le serveur de manière gracieuse soit par la commande `!shutdown` soit par `^C`, qui notifie tous les utilisateurs connectés avant l'arrêt.

### Défis et limitations
- **Transfert de fichiers :** La capacité d'envoyer des fichiers n'a pas encore été mise en œuvre.
- **Implémentation des règles du jeu :** Manque actuellement l'intégration de règles spécifiques au jeu.
- **Gestion des pannes côté serveur :** La tolérance aux pannes du serveur lors des reconnexions reste partiellement fonctionnelle.

### Pile technologique
- **Threading :** Utilisation de la bibliothèque de threads pour gérer plusieurs connexions clients simultanément et gérer les opérations côté serveur telles que les heartbeats et le traitement des commandes.

## Conclusion
Ce projet a réussi à mettre en place plusieurs fonctionnalités essentielles pour une communication efficace entre le serveur et le client et la gestion des commandes. Bien que certains domaines nécessitent un développement supplémentaire, les bases établies fournissent une solide fondation pour des améliorations futures.
