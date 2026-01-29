# Game Features Documentation

## Overview
A Descent-inspired 6DOF (Six Degrees of Freedom) multiplayer space shooter built with Ursina/Panda3D.

## Inspiration Sources
- **Descent** (1995): 6DOF movement, tunnel environments, mining ship aesthetic
- **StarCraft** (1998): Ship design (Wraith-inspired), industrial aesthetics
- **Doom** (1993): Fast-paced combat, industrial/dark atmosphere
- **Quake** (1996): Multiplayer deathmatch, momentum-based movement

---

## Current Features

### Movement System
- **Status**: Implemented
- **Description**: Full 6DOF movement with momentum-based physics
- **Controls**:
  - W/S: Forward/Backward thrust
  - A/D: Strafe left/right
  - Space: Move up
  - Shift/Control: Move down
  - Q/E: Roll left/right
  - Mouse: Look/aim
- **Physics**:
  - Acceleration: 45 units/s²
  - Deceleration: 5 units/s² (space friction)
  - Max speed: 50 units/s (affected by speed boost)
  - Strafe/vertical multipliers: 0.9x/0.85x

### Weapon System
- **Status**: Implemented
- **Primary Weapon**:
  - Rapid fire laser
  - Speed: 70 units/s
  - Damage: 12 per hit (affected by damage boost)
  - Fire rate: 0.12s cooldown
  - Color: Yellow-green projectile, cyan muzzle flash
- **Secondary Weapon**:
  - Slow powerful missile
  - Speed: 40 units/s
  - Damage: 50 per hit (affected by damage boost)
  - Fire rate: 1.5s cooldown
  - Creates explosion on impact
  - Color: Orange-red projectile and flash

### Arena/Level
- **Status**: Implemented
- **Size**: 200 x 80 x 200 units
- **Features**:
  - Industrial aesthetic with dark colors
  - Central tunnel system (Z and X axis)
  - Corner pillars
  - Mid-level platforms
  - Cover blocks at various heights
  - Grid lines on floor for depth perception
- **Color Scheme** (using normalized RGBA format):
  - Floor: Dark metallic gray-green (25, 30, 28)
  - Ceiling: Very dark (18, 20, 22)
  - Z-walls: Dark blue-gray (28, 32, 42)
  - X-walls: Dark rust/brown (38, 30, 26)
  - Tunnels: Dark grays with blue accent lights
- **Rendering**: Full ambient lighting with `Color(1, 1, 1, 1)`

### Multiplayer
- **Status**: Implemented
- **Features**:
  - Host/Join via UDP sockets
  - Real-time player position sync
  - Player count display
  - Network interpolation for smooth movement
- **Port**: 5555 (UDP)

### Audio System
- **Status**: Implemented
- **Sound Effects**:
  - Laser fire (primary weapon) - descending pitch synth
  - Missile launch (secondary weapon) - rumble with whoosh
  - Explosion - bass boom with noise burst
  - Hit/damage - metallic impact
- **Music**:
  - Menu music - arpeggio pattern
  - Game ambient - evolving pad with bass pulse
- **Implementation**: Procedurally generated WAV files

### Particle Effects
- **Status**: Implemented
- **Effects**:
  - Muzzle flash on weapon fire (cyan for primary, orange for secondary)
  - Explosion particles (fire, sparks, smoke layers)
  - Size variants: small, medium, large explosions
- **Features**:
  - Billboard particles (always face camera)
  - Color interpolation over lifetime
  - Physics-based velocity and drag

### Power-Ups System
- **Status**: Implemented
- **Types**:
  - **Health** (Green): +25 HP, 15s respawn
  - **Speed** (Blue): 1.5x speed for 10s, 20s respawn
  - **Damage** (Orange): 2x damage for 10s, 25s respawn
  - **Shield** (Purple): +50 shield points, 30s respawn
- **Features**:
  - Animated (rotating, bobbing, glowing)
  - Strategic spawn locations
  - Auto-respawn after collection
  - Shield absorbs damage before health

### Minimap/Radar
- **Status**: Implemented
- **Features**:
  - Top-down view in top-right corner
  - Local player (green) with direction indicator
  - Other players (red dots)
  - Power-ups (colored by type)
  - Arena structures displayed
- **Real-time updates** synced with game state

### UI/HUD
- **Status**: Implemented
- **Elements**:
  - Health bar (green, color changes based on level)
  - Shield bar (purple)
  - Speed indicator
  - Player count
  - Server IP display (when hosting)
  - Kill/Death stats
  - Crosshair
  - Respawn screen
  - Message notifications for power-up collection

---

## Planned Features

### Phase 1: Additional Weapons
- [ ] Spreadshot (fires 3 projectiles)
- [ ] Homing missiles
- [ ] Plasma cannon (charge attack)

### Phase 2: Visual Enhancements
- [ ] Thruster particle effects on player ship
- [ ] Projectile trails with particles
- [ ] Screen shake on damage
- [ ] Motion blur at high speeds
- [ ] Ambient fog in tunnels

### Phase 3: Gameplay Features
- [ ] Multiple weapon loadouts
- [ ] Score tracking and leaderboard
- [ ] Different game modes (deathmatch, team DM, CTF)
- [ ] Bot AI for single player

### Phase 4: Level Design
- [ ] Multiple arena layouts
- [ ] Dynamic obstacles (moving platforms)
- [ ] Hazards (lava, energy fields)
- [ ] Secret areas

### Phase 5: Polish
- [ ] Settings screen (sensitivity, volume, graphics)
- [ ] Key rebinding
- [ ] Tutorial/training mode
- [ ] Better ship models

---

## File Structure
```
game/
├── main.py           # Main game loop and initialization
├── player.py         # Player entity with movement and weapons
├── arena.py          # Level geometry and obstacles
├── networking.py     # Multiplayer networking (UDP)
├── projectile.py     # Projectile and explosion systems
├── ui.py             # HUD and menu systems
├── audio.py          # Sound generation and management
├── particles.py      # Particle effects system
├── powerups.py       # Power-up collectibles
├── minimap.py        # Minimap/radar display
├── test_framework.py # Basic testing utilities
├── auto_tester.py    # Automated visual testing
├── sounds/           # Generated audio files
└── test_results/     # Screenshot test results
```

---

## Testing

### Automated Testing
The game includes an automated testing framework (`auto_tester.py`) that can:
- Launch the game
- Simulate input via AppleScript (macOS)
- Take screenshots at specified intervals
- Save test results as JSON

### Running Tests
```bash
cd game
python auto_tester.py menu      # Test menu display
python auto_tester.py host      # Test hosting
python auto_tester.py movement  # Test movement
python auto_tester.py shooting  # Test weapons
python auto_tester.py all       # Run all tests
```

---

## Development Notes

### Color System (Ursina 7.0.0)
**Important**: Use `Color(r/255, g/255, b/255, 1)` format instead of `color.rgb(r, g, b)`.
The `color.rgb()` function does not work correctly in Ursina 7.0.0 and causes white textures.

Example:
```python
# Correct - use normalized RGBA values
color=Color(25/255, 30/255, 28/255, 1)

# Incorrect - causes white rendering in Ursina 7.0.0
color=color.rgb(25, 30, 28)
```

### Color Palette (Industrial/Dark Theme)
- Background: Color(10/255, 12/255, 18/255, 1)
- Floor: Color(25/255, 30/255, 28/255, 1)
- Walls (blue): Color(28/255, 32/255, 42/255, 1)
- Walls (rust): Color(38/255, 30/255, 26/255, 1)
- Metal dark: Color(32/255, 35/255, 38/255, 1)
- Accent lights: Color(70/255, 120/255, 150/255, 1)

### Performance Targets
- 60 FPS minimum
- Network update rate: 30 Hz
- Maximum projectiles: 100 active
- Maximum players: 8

### Recent Changes
- **Fixed texture colors**: Replaced `color.rgb()` with `Color(r/255, g/255, b/255, 1)` format
- Removed `unlit=True` flags (caused white rendering in Ursina 7.0.0)
- Set ambient light to `Color(1, 1, 1, 1)` for proper scene illumination
- Implemented procedural audio generation
- Added particle effects for weapons
- Implemented power-up system with 4 types
- Added minimap showing arena and entities
