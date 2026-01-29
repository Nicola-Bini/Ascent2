# Ascent 2

A Descent-inspired 6DOF (Six Degrees of Freedom) multiplayer space shooter built with Ursina/Panda3D.

## Quick Start

**One-liner to clone, setup, and run:**
```bash
git clone https://github.com/Nicola-Bini/Ascent2.git && cd Ascent2 && python3 -m venv game_env && source game_env/bin/activate && pip install -r requirements.txt && python game/main.py
```

## Manual Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Nicola-Bini/Ascent2.git
   cd Ascent2
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv game_env
   source game_env/bin/activate  # On macOS/Linux
   # or
   game_env\Scripts\activate     # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the game:**
   ```bash
   python game/main.py
   ```

## Controls

| Key | Action |
|-----|--------|
| W/S | Forward/Backward thrust |
| A/D | Strafe left/right |
| Space | Move up |
| Shift/Ctrl | Move down |
| Q/E | Roll left/right |
| Mouse | Look/aim |
| Left Click | Primary weapon (rapid fire laser) |
| Right Click | Secondary weapon (missile) |
| Middle Click | Spreadshot |

## Features

- **Full 6DOF Movement**: Fly in any direction with momentum-based physics
- **Multiple Weapons**: Primary laser, secondary missile with explosions, spreadshot
- **Multiplayer**: Host/Join games via UDP networking
- **Industrial Arena**: Tunnels, platforms, and cover blocks
- **Power-ups**: Health, Speed boost, Damage boost, Shield
- **Bot AI**: Practice against bots in single player
- **Minimap**: Radar display showing players and power-ups
- **Procedural Audio**: Generated sound effects and ambient music

## Multiplayer

- **Host a game**: Select "Host Game" from the menu
- **Join a game**: Select "Join Game" and enter the host's IP address
- **Default port**: 5555 (UDP)

## Requirements

- Python 3.8+
- Ursina 7.0.0 (automatically installed via requirements.txt)

## Inspiration

- **Descent** (1995): 6DOF movement, tunnel environments
- **StarCraft** (1998): Ship design aesthetics
- **Doom/Quake**: Fast-paced multiplayer combat

## Documentation

See [GAME_FEATURES.md](GAME_FEATURES.md) for detailed feature documentation and development notes.
