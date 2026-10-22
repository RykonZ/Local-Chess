# Local-Chess Pro

[Français](#version-française) | [English](#english-version)

---

## Version Française

Application d'échecs sur bureau développée en Python avec Pygame, intégrant la validation complète des règles, un mode multijoueur sur réseau local (LAN), un moteur d'IA configurable via Stockfish et l'exportation de parties en PGN.

### Fonctionnalités

- **Modes de jeu** :
  - **Solo local** : Deux joueurs sur le même poste.
  - **Joueur contre IA** : Intégration du moteur Stockfish avec niveau ajustable (de 0 à 20).
  - **Multijoueur LAN** : Architecture pair-à-pair / client-serveur sur sockets TCP (paramétrage de l'IP hôte et du port).
- **Interface graphique (Pygame)** :
  - Déplacement des pièces par glisser-déposer ou sélection par clic.
  - Animations de déplacement avec lissage d'interpolation quadratique.
  - Indicateurs visuels : coups légaux, dernier coup joué, échec au roi et pré-coups (premoves).
- **Contrôle du temps** : Horloges configurables (temps de départ et incrément en secondes par coup).
- **Outils de jeu** :
  - Suggestions de coups optimaux calculées par Stockfish en tâche de fond.
  - Système d'annulation de coup (*takeback*) soumis à validation mutuelle en réseau.
  - Exportation automatique ou manuelle de la partie au format standard `.pgn` (`match_export.pgn`).

### Fonctionnement et architecture

Le projet s'articule autour de trois modules indépendants :
1. `run.py` : Boucle principale de l'interface graphique (Pygame, 60 FPS), gestionnaire d'événements, horloges d'échecs et écrans de configuration (lobbies).
2. `engine.py` : Gestionnaire de l'état de l'échiquier (basé sur la bibliothèque `chess`), encapsulation de l'export PGN et communication asynchrone non-bloquante avec l'exécutable Stockfish via le protocole UCI dans des threads dédiés.
3. `network.py` : Client/serveur TCP threadé gérant la sérialisation des coups, des votes d'annulation et des signaux de fin de partie via sockets standards.

### Prérequis indispensables

- **Python** 3.10 ou version ultérieure.
- **Binaire Stockfish** : Téléchargez l'exécutable officiel [Stockfish](https://stockfishchess.org/download/) et nommez-le **`stockfish.exe`**.  
  > **Important** : Le fichier `stockfish.exe` **doit impérativement se trouver dans le dossier racine du projet** pour que le mode IA fonctionne à l'exécution et pour qu'il soit correctement embarqué lors du build.

### Installation et exécution

1. Cloner le projet :
   ```bash
   git clone [https://github.com/votre-compte/Local-Chess.git](https://github.com/votre-compte/Local-Chess.git)
   cd Local-Chess
