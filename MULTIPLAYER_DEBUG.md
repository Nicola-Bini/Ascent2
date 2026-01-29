# Multiplayer Debug Documentation

## Problem Reported
- Game connects but doesn't show other players
- Player count shows "Players 1" despite multiple connections

## Root Cause Analysis

### Bug #1: Client PLAYER_JOIN Handler Overwrites Own ID (CRITICAL)
**File:** `game/networking.py` lines 273-284

When a client receives a `PLAYER_JOIN` message about ANOTHER player joining, it incorrectly overwrites its own `player_id`:

```python
if msg_type == NetworkMessage.PLAYER_JOIN:
    if 'player_id' in message:
        self.player_id = message['player_id']  # BUG: Overwrites own ID!
```

**What happens:**
1. Client A connects, gets assigned player_id=1
2. Client B connects, server broadcasts PLAYER_JOIN with player_id=2 to Client A
3. Client A's `_handle_message` receives this and sets `self.player_id = 2`
4. Client A now thinks it's player 2!
5. All subsequent GAME_STATE processing filters out player 2's state (because `pid == self.player_id`)
6. Client A never sees any other players

### Bug #2: Host Not Included in Existing Players
**File:** `game/networking.py` lines 76-95

When a client joins, the server sends `existing_players` from `self.player_states`, but the host (player 0) is NOT in `player_states` until `broadcast_game_state()` is called with `host_state`.

```python
# Server sends this on join:
'existing_players': list(self.player_states.values())  # Missing host!
```

The host's state is only added here (main.py:296):
```python
self.server.broadcast_game_state({}, host_state=state)  # Adds player 0
```

So if a client joins before the first broadcast tick, they don't know about the host.

## Fixes Applied

### Fix #1: Proper PLAYER_JOIN Handling
Modified `networking.py` to check if already assigned before processing:

```python
if msg_type == NetworkMessage.PLAYER_JOIN:
    if self.player_id is None and 'player_id' in message:
        # First time - this is our assignment
        self.player_id = message['player_id']
        for player_state in message.get('existing_players', []):
            self.message_queue.append({...})
    elif self.player_id is not None:
        # Another player joined - just queue the notification
        self.message_queue.append(message)
```

### Fix #2: Initialize Host in player_states
Modified `networking.py` server to include host state from the start:

```python
def start(self):
    # ... socket setup ...
    # Initialize host state so it's included in existing_players
    self.player_states[0] = {
        'player_id': 0,
        'position': (0, 0, 0),
        'rotation': (0, 0, 0),
        'health': 100,
        'is_alive': True
    }
```

## Architecture Overview

### Player Count Calculation
**File:** `game/main.py` line 280-281
```python
total_players = 1 + len(self.remote_players)
self.hud.update_player_count(total_players)
```

### Message Flow
```
HOST                          CLIENT
  |                              |
  |<-- PLAYER_JOIN request ------|
  |                              |
  |--- PLAYER_JOIN response ---->| (player_id + existing_players)
  |                              |
  |--- GAME_STATE (30Hz) ------->| (all player states)
  |                              |
  |<-- PLAYER_UPDATE ------------|  (client sends own state)
```

### Key Files
- `game/networking.py` - UDP server/client, message handling
- `game/main.py` - Game loop, player management, network processing
- `game/ui.py` - HUD with player count display (line 239-247)
- `game/player.py` - Player entity with state serialization

### Remote Player Creation
Happens in `main.py:_add_remote_player()` (lines 381-400) when:
1. PLAYER_JOIN message received for another player
2. PLAYER_UPDATE received for unknown player_id

## Testing
1. Start host: Run game, click "Host Game"
2. Start client: Run game, enter host IP, click "Connect"
3. Verify: Both should show "Players: 2"
4. Verify: Each player should see the other as an orange ship

---

## Issue #2: Key Release Not Detected (Input Handling)

### Problem
- Pressing W then S caused permanent cancellation (couldn't move forward/backward)
- `held_keys` dictionary wasn't registering key releases
- Once both W and S were pressed, `move_z = 1 - 1 = 0` permanently

### Root Cause
**File:** `game/player.py`

The code relied on Ursina's global `held_keys` dictionary, which wasn't updating properly because:
1. Key events need to flow through Entity's `input()` method to be reliably tracked
2. The global `held_keys` can have stale values depending on how input is handled
3. There was also a bug: `held_keys['s']` instead of `held_keys.get('s', 0)` which would crash if 's' was never pressed

### Fix Applied
Added local key state tracking in the Player entity:

1. Added `self.keys_held` dictionary to track key states locally
2. Added `input(self, key)` method to Player class that:
   - Detects key presses (e.g., `'w'`)
   - Detects key releases (e.g., `'w up'`)
   - Updates `self.keys_held` accordingly
3. Changed `_handle_local_input()` to use `self.keys_held` instead of global `held_keys`

```python
# Player now tracks its own key states
self.keys_held = {
    'w': False, 's': False, 'a': False, 'd': False,
    'q': False, 'e': False,
    'space': False, 'shift': False, 'control': False
}

def input(self, key):
    # Handle key release (ends with ' up')
    if key.endswith(' up'):
        base_key = key[:-3]
        self.keys_held[mapped_key] = False
    else:
        self.keys_held[mapped_key] = True
```

### Why This Works
In Ursina, Entity subclasses with an `input(self, key)` method can receive input events. However, when `app.input` is overridden (as in main.py), entity input methods are NOT automatically called.

**Additional fix needed in main.py:**
The Game's `input` method must forward key events to the player:

```python
def input(self, key):
    # ... escape and shooting handling ...

    # Forward input to player for movement key tracking
    if self.state == "playing" and self.local_player:
        self.local_player.input(key)
```

This ensures:
- Events are delivered directly to the Player entity
- Both press and release events are explicitly handled
- No dependency on global `held_keys` state

---

## Debugging Session: Multiplayer Still Not Working

### Debug Logging Added
Added extensive logging with prefixes:
- `[NET-SERVER]` - Server-side networking events
- `[NET-CLIENT]` - Client-side networking events
- `[MAIN]` - Main game loop message processing

### How to Debug
1. Run host game, check terminal for `[NET-SERVER]` logs
2. Run client game, check terminal for `[NET-CLIENT]` logs
3. Look for:
   - `[NET-SERVER] New player X joined` - Client connected to server
   - `[NET-SERVER] Sending existing_players` - Server sending player list
   - `[NET-CLIENT] Assigned player_id=X` - Client got ID assigned
   - `[NET-CLIENT] Queuing PLAYER_JOIN for player 0` - Client knows about host
   - `[MAIN] Processing X messages` - Messages being processed in game loop
   - `[MAIN] Creating remote player X` - Remote player entity created

### Expected Flow
```
HOST:                                    CLIENT:
Server started
                                         Sends PLAYER_JOIN
[NET-SERVER] New player 1 joined
[NET-SERVER] Sending existing_players
                                         [NET-CLIENT] Assigned player_id=1
                                         [NET-CLIENT] Queuing PLAYER_JOIN for 0
[MAIN] Processing 1 messages             [MAIN] Processing 1 messages
[MAIN] PLAYER_JOIN: player_id=1          [MAIN] PLAYER_JOIN: player_id=0
[MAIN] Creating remote player 1          [MAIN] Creating remote player 0
```

---

## Issue #3: update() Not Being Called

### Problem
Debug logs showed messages being queued but never processed. `[MAIN-DEBUG]` messages never appeared.

### Root Cause
**File:** `game/main.py`

The code was setting `self.app.update = self.update` but Ursina doesn't call methods assigned this way. Ursina looks for **module-level** `update()` and `input()` functions.

### Fix Applied
Added module-level functions that delegate to the Game instance:

```python
# Module-level game instance (set in __main__)
_game = None

def update():
    """Module-level update function called by Ursina every frame."""
    if _game:
        _game.update()

def input(key):
    """Module-level input function called by Ursina for key events."""
    if _game:
        _game.input(key)

if __name__ == "__main__":
    game = Game()
    _game = game  # Set module-level reference
    game.run()
```

This ensures Ursina finds and calls the update/input functions properly.
