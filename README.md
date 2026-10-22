# Local-Chess Pro

[Français](#version-française) | [English](#english-version)

---

## Version Française

Jeu d'échecs développée en Python avec Pygame, intégrant la validation complète des règles, un mode multijoueur en réseau local, un moteur d'IA configurable via Stockfish et l'exportation de parties en PGN.

---

### Fonctionnalités

- **Modes de jeu** :
  - **Solo local** : Deux joueurs sur la même machine.
  - **Joueur contre IA** : Intégration du moteur Stockfish avec niveau de difficulté ajustable (de 0 à 20).
  - **Multijoueur LAN** : Architecture pair-à-pair / client-serveur sur sockets TCP.
- **Interface graphique (Pygame)** :
  - Déplacement des pièces par glisser-déposer ou sélection par clic.
  - Animations de déplacement avec lissage d'interpolation quadratique.
  - Indicateurs visuels : coups légaux, dernier coup joué, échec au roi et pré-coups.
- **Contrôle du temps** : Horloges configurables (temps de départ et incrément en secondes par coup).
- **Outils de jeu** :
  - Suggestions de coups optimaux calculées par Stockfish en tâche de fond.
  - Système d'annulation de coup soumis à validation mutuelle en réseau.
  - Exportation automatique ou manuelle de la partie au format standard `.pgn` (`match_export.pgn`).

---

### Architecture & Fonctionnement

Le projet s'articule autour de trois modules principaux :

1. **`run.py`** : Point d'entrée de l'application. Gère la boucle événementielle Pygame en 60 FPS, le rendu graphique, le cycle de vie du jeu (menus, lobbies, plateau actif) et les interactions utilisateur.
2. **`engine.py`** : Moteur logique de la bibliothèque `chess`. Gère l'exportation PGN et la communication asynchrone non-bloquante avec l'exécutable Stockfish via le protocole UCI dans des threads dédiés.
3. **`network.py`** : Gestionnaire réseau TCP multithreadé gérant la sérialisation des coups, les votes d'annulation et la synchronisation entre hôte et client via des sockets standards.

---

### Prérequis

- **Python** : Version 3.10 ou supérieure.
- **Binaire Stockfish** : Téléchargez l'exécutable officiel [Stockfish](https://stockfishchess.org/download/) et nommez le fichier **`stockfish.exe`**.
  
> **CRITIQUE** : Le fichier **`stockfish.exe` doit être placé directement dans le dossier racine du projet** (`Local-Chess/stockfish.exe`). Il est indispensable au bon fonctionnement du jeu contre l'IA, des suggestions, et à l'inclusion dans le build exécutable.

---

### Configuration & Installation (Setup)

1. **Cloner le dépôt** :
   ```bash
   git clone https://github.com/votre-compte/Local-Chess.git
   cd Local-Chess
   ```

2. **Créer et activer un environnement virtuel** :
   ```bash
   python -m venv venv
   # Sous Windows (PowerShell) :
   .\venv\Scripts\Activate.ps1
   # Sous Windows (CMD) :
   venv\Scripts\activate.bat
   # Sous Linux / macOS :
   source venv/bin/activate
   ```

3. **Installer les dépendances Python** :
   ```bash
   pip install -r requirements.txt
   ```

4. **Placer Stockfish** :
   Copiez l'exécutable `stockfish.exe` à la racine du projet (au même niveau que `run.py`).

5. **Lancer l'application** :
   ```bash
   python run.py
   ```

---

### Procédure de compilation

L'application utilise une résolution dynamique des chemins (`sys._MEIPASS`) pour accéder aux ressources (`assets/`) et à l'exécutable `stockfish.exe` une fois compilée.

Pour générer un fichier exécutable autonome sous Windows avec **PyInstaller** :

```bash
pyinstaller --noconfirm --onedir --windowed --name "Local-Chess" --add-data "assets;assets" --add-binary "stockfish.exe;." run.py
```

L'application compilée sera disponible dans le dossier `dist/Local-Chess/Local-Chess.exe`.

---

### Transparence IA

Des outils d'intelligence artificielle générative ont été utilisés comme support pour l'accélération du développement, la structuration de l'architecture et l'optimisation du code.

---
---

## English Version

Chess game built in Python using Pygame, featuring legal move validation, local network multiplayer, a configurable AI engine via Stockfish, and PGN export capability.

---

### Features

- **Game Modes**:
  - **Local Singleplayer**: Pass-and-play on a single machine.
  - **Player vs Computer**: Stockfish engine integration with adjustable skill levels (0 to 20).
  - **LAN Multiplayer**: Peer-to-peer / client-server setup over TCP sockets.
- **User Interface (Pygame)**:
  - Drag-and-drop or click-to-move piece handling.
  - Smooth move animations with quadratic easing.
  - Visual cues for legal moves, previous move, check status, and premoves.
- **Time Controls**: Configurable base timer and per-move increment.
- **Game Utilities**:
  - Stockfish-powered move suggestions calculated asynchronously.
  - Move rewind / takeback requests.
  - Match history exported directly to standard PGN (`match_export.pgn`).

---

### Architecture & Mechanics

The application consists of three main modules:

1. **`run.py`**: Primary application entry point. Handles the Pygame event loop in 60 FPS, UI rendering, state transitions (menus, lobbies, active board), and user interactions.
2. **`engine.py`**: Encapsulates board rules using `python-chess`, handles PGN export routines, and coordinates asynchronous, non-blocking UCI communication with the Stockfish engine in dedicated threads.
3. **`network.py`**: Threaded TCP socket manager handling move serialization, takeback votes, and match synchronization between client and host.

---

### Prerequisites

- **Python**: Version 3.10 or higher.
- **Stockfish Binary**: Download the official [Stockfish](https://stockfishchess.org/download/) executable and ensure it is named **`stockfish.exe`**.

> **CRITICAL**: The **`stockfish.exe` file must be placed directly in the project root directory** (`Local-Chess/stockfish.exe`). It is required for the AI opponent, move hints, and for bundling into the final build.

---

### Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/Local-Chess.git
   cd Local-Chess
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   # Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # Windows (CMD):
   venv\Scripts\activate.bat
   # Linux / macOS:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Add Stockfish**:
   Place the downloaded `stockfish.exe` file into the root folder (alongside `run.py`).

5. **Run the application**:
   ```bash
   python run.py
   ```

---

### Build Process

The application implements dynamic path resolution (`sys._MEIPASS`) to locate assets and external binaries when packaged into an executable.

To build a standalone Windows executable using **PyInstaller**:

```bash
pyinstaller --noconfirm --onedir --windowed --name "Local-Chess" --add-data "assets;assets" --add-binary "stockfish.exe;." run.py
```

The output build will be placed in `dist/Local-Chess/Local-Chess.exe`.

---

### AI Disclosure

Generative AI tooling was utilized during the development lifecycle to assist with code scaffolding, architectural design, and optimization.
