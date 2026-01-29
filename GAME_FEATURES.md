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
  - Max speed: 50 units/s
  - Strafe/vertical multipliers: 0.8x
- **Test Results**: PENDING

### Weapon System
- **Status**: Implemented
- **Primary Weapon**:
  - Rapid fire laser
  - Speed: 70 units/s
  - Damage: 12 per hit
  - Fire rate: 0.12s cooldown
  - Color: Cyan
- **Secondary Weapon**:
  - Slow powerful missile
  - Speed: 40 units/s
  - Damage: 50 per hit
  - Fire rate: 0.8s cooldown
  - Creates explosion on impact
  - Color: Orange/Red
- **Test Results**: PENDING

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
- **Color Scheme**:
  - Floor: Dark metallic gray-green (25, 30, 28)
  - Ceiling: Very dark (18, 20, 22)
  - Z-walls: Dark blue-gray (28, 32, 42)
  - X-walls: Dark rust/brown (38, 30, 26)
  - Tunnels: Dark grays with blue accent lights
- **Test Results**: PENDING (texture issues being fixed)

### Multiplayer
- **Status**: Implemented
- **Features**:
  - Host/Join via UDP sockets
  - Real-time player position sync
  - Player count display
  - Network interpolation for smooth movement
- **Port**: 5555 (UDP)
- **Test Results**: Working (see MULTIPLAYER_DEBUG.md)

### UI/HUD
- **Status**: Implemented
- **Elements**:
  - Health bar (green)
  - Speed indicator
  - Player count
  - Server IP display (when hosting)
  - Kill/Death stats
  - Respawn screen

---

## Planned Features

### Phase 1: Audio System
- [ ] Background ambient music (industrial/electronic)
- [ ] Primary weapon sound (laser zap)
- [ ] Secondary weapon sound (missile launch)
- [ ] Explosion sounds
- [ ] Engine/thrust sounds
- [ ] Hit/damage sounds
- [ ] Menu music

### Phase 2: Visual Enhancements
- [ ] Particle effects for thrusters
- [ ] Muzzle flash on weapons
- [ ] Better explosion effects
- [ ] Screen shake on damage
- [ ] Motion blur at high speeds
- [ ] Ambient fog in tunnels

### Phase 3: Gameplay Features
- [ ] Power-ups (health, speed boost, damage boost)
- [ ] Multiple weapon types (spreadshot, homing missiles)
- [ ] Shields system
- [ ] Radar/minimap
- [ ] Score tracking and leaderboard
- [ ] Different game modes (deathmatch, team deathmatch, CTF)

### Phase 4: Level Design
- [ ] Multiple arena layouts
- [ ] Dynamic obstacles (moving platforms)
- [ ] Hazards (lava, energy fields)
- [ ] Secret areas
- [ ] Environmental lighting effects

### Phase 5: Polish
- [ ] Main menu improvements
- [ ] Settings screen (sensitivity, volume, graphics)
- [ ] Key rebinding
- [ ] Tutorial/training mode
- [ ] Bot AI for single player

---

## Test Results Log

### Test Session Template
```
Date: YYYY-MM-DD
Feature: Feature Name
Test Type: Visual/Functional/Performance
Steps:
  1. Step one
  2. Step two
Screenshots:
  - screenshot_name.png: Description
Result: PASS/FAIL
Notes: Any observations
```

### Test Sessions

#### Session 1: Arena Rendering
- **Date**: 2026-01-29
- **Feature**: Arena textures/colors
- **Issue**: Walls rendering as white/bright instead of dark colors
- **Fix Applied**: Added `unlit=True` to all arena entities
- **Result**: PENDING VERIFICATION

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
├── audio.py          # Sound effects and music (TODO)
├── test_framework.py # Basic testing utilities
├── auto_tester.py    # Automated visual testing
└── test_results/     # Screenshot test results
```

---

## Development Notes

### Color Palette (Industrial/Dark Theme)
- Background: rgb(10, 12, 18)
- Floor: rgb(25, 30, 28)
- Walls (blue): rgb(28, 32, 42)
- Walls (rust): rgb(38, 30, 26)
- Metal dark: rgb(32, 35, 38)
- Accent lights: rgb(70, 120, 150)

### Performance Targets
- 60 FPS minimum
- Network update rate: 30 Hz
- Maximum projectiles: 100 active
- Maximum players: 8

### Known Issues
1. Texture colors appearing too bright (lighting issue)
2. Some walls may not render correctly from certain angles
