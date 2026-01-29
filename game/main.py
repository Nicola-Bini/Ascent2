"""Main entry point and game loop for Descent-like 6DOF shooter."""

import sys
import os
import traceback
from datetime import datetime

# Setup automatic logging
LOG_DIR = os.path.join(os.path.dirname(__file__), "test_logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f'game_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')


class TeeOutput:
    """Write to both console and log file."""

    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for stream in self.streams:
            stream.write(text)
            stream.flush()

    def flush(self):
        for stream in self.streams:
            stream.flush()


_log_file = open(LOG_FILE, "w")
sys.stdout = TeeOutput(sys.__stdout__, _log_file)
sys.stderr = TeeOutput(sys.__stderr__, _log_file)
print(f"[LOG] Game started at {datetime.now()}")
print(f"[LOG] Logging to: {LOG_FILE}")

from ursina import *
from player import Player
from projectile import ProjectileManager
from arena import Arena
from networking import NetworkServer, NetworkClient, NetworkMessage, get_local_ip
from ui import MainMenu, JoinDialog, HUD, RespawnScreen


class Game:
    """Main game class managing all game systems."""

    def __init__(self):
        self.app = Ursina(
            title="Descent-like 6DOF",
            borderless=False,
            fullscreen=False,
            size=(1280, 720),
            forced_aspect_ratio=16 / 9,
        )
        # Force window to front on macOS
        window.center_on_screen()
        window.setForeground(True)

        # Game state
        self.state = "menu"  # menu, playing
        self.is_host = False
        self.local_player = None
        self.remote_players = {}  # player_id -> Player
        self.arena = None

        # Networking
        self.server = None
        self.client = None
        self.network_update_rate = 1 / 30  # 30 Hz
        self.last_network_update = 0

        # Systems
        self.projectile_manager = ProjectileManager()

        # Respawn
        self.respawn_timer = 0
        self.respawn_delay = 3.0

        # Create UI
        self._create_ui()

        # Lighting
        self._setup_lighting()

        # Input handler - set module-level functions
        # Note: Ursina looks for module-level input() and update() functions

    def _create_ui(self):
        """Create all UI elements."""
        print("[LOG] Creating UI elements...")

        self.main_menu = MainMenu(
            on_host=self.host_game,
            on_join=self.show_join_dialog,
            on_quit=self.quit_game,
        )
        print(f"[LOG] MainMenu created, enabled={self.main_menu.enabled}")

        self.join_dialog = JoinDialog(
            on_connect=self.join_game, on_cancel=self.cancel_join
        )

        self.hud = HUD()
        self.respawn_screen = RespawnScreen()

        # Ensure main menu is visible at start
        self.main_menu.enabled = True
        mouse.locked = False
        mouse.visible = True
        print("[LOG] UI creation complete")

    def _setup_lighting(self):
        """Setup scene lighting."""
        # Set dark background
        window.color = color.rgb(10, 10, 30)
        camera.clip_plane_far = 800

        # Create a simple dark sky sphere - large enough for 200x80x200 arena
        self.sky = Entity(
            model="sphere", scale=600, color=color.rgb(15, 15, 35), double_sided=True
        )

        # Moderate ambient light
        AmbientLight(color=color.rgb(80, 80, 100))

        print("[LOG] Lighting setup complete")

    def host_game(self):
        """Start hosting a game."""
        print("Starting server...")

        self.server = NetworkServer(port=5555)
        if not self.server.start():
            print("Failed to start server")
            return

        self.is_host = True
        self._start_game(player_id=0)

        # Show host IP
        local_ip = get_local_ip()
        self.hud.set_server_info(local_ip, 5555)
        self.hud.show_message(f"Hosting on {local_ip}:5555", 5.0)

    def show_join_dialog(self):
        """Show the join game dialog."""
        self.main_menu.hide()
        self.join_dialog.show()

    def cancel_join(self):
        """Cancel joining and return to menu."""
        self.join_dialog.hide()
        self.main_menu.show()

    def join_game(self, host_ip):
        """Join a hosted game."""
        print(f"Connecting to {host_ip}...")
        self.join_dialog.hide()

        self.client = NetworkClient()
        if not self.client.connect(host_ip, port=5555, timeout=5.0):
            print("Failed to connect to server")
            self.main_menu.show()
            self.hud.show_message("Connection failed!", 3.0)
            return

        self.is_host = False
        self._start_game(player_id=self.client.player_id)
        self.hud.show_message(f"Connected as Player {self.client.player_id}", 3.0)

    def _start_game(self, player_id):
        """Initialize game world and start playing."""
        # Hide menus
        self.main_menu.hide()
        self.join_dialog.hide()

        # Create arena - use full size that matches the tunnel/obstacle layout
        print("[LOG] Creating arena...")
        self.arena = Arena(size=(200, 80, 200))
        print(
            f"[LOG] Arena created with {len(self.arena.walls)} walls and {len(self.arena.obstacles)} obstacles"
        )

        # Create local player - spawn in corners away from central tunnels
        if player_id == 0:
            spawn_pos = Vec3(-60, 0, -60)  # Host spawns in one corner
        else:
            spawn_pos = Vec3(60, 0, 60)  # Clients spawn in opposite corner

        self.local_player = Player(
            player_id=player_id,
            is_local=True,
            position=spawn_pos,
            arena_bounds=self.arena.half_size,  # Pass bounds for clamping
        )
        print(f"[LOG] Player {player_id} spawned at {spawn_pos}")

        # Show HUD
        self.hud.show()
        self.hud.update_health(self.local_player.health)
        self.hud.update_stats(0, 0)
        self.hud.update_player_count(1)

        self.state = "playing"
        print(f"Game started as Player {player_id}")

    def quit_game(self):
        """Quit the game."""
        if self.server:
            self.server.stop()
        if self.client:
            self.client.stop()
        application.quit()

    def input(self, key):
        """Handle input events."""
        if key == "escape":
            if self.state == "playing":
                self._return_to_menu()
            elif self.join_dialog.enabled:
                self.cancel_join()

        # Forward input to player for movement and mouse tracking
        if self.state == "playing" and self.local_player:
            self.local_player.input(key)

    def _shoot_primary(self):
        """Handle primary weapon (rapid fire)."""
        if not self.local_player or not self.local_player.can_shoot_primary():
            return

        shot_data = self.local_player.shoot_primary()

        self.projectile_manager.spawn(
            position=shot_data["position"],
            direction=shot_data["direction"],
            owner_id=shot_data["owner_id"],
            weapon='primary'
        )

        if self.is_host and self.server:
            self.server._broadcast(
                {"type": NetworkMessage.PROJECTILE_SPAWN, "projectile": shot_data}
            )
        elif self.client:
            self.client.send_shoot(shot_data)

    def _shoot_secondary(self):
        """Handle secondary weapon (slow, powerful with explosion)."""
        if not self.local_player or not self.local_player.can_shoot_secondary():
            return

        shot_data = self.local_player.shoot_secondary()

        self.projectile_manager.spawn(
            position=shot_data["position"],
            direction=shot_data["direction"],
            owner_id=shot_data["owner_id"],
            weapon='secondary'
        )

        if self.is_host and self.server:
            self.server._broadcast(
                {"type": NetworkMessage.PROJECTILE_SPAWN, "projectile": shot_data}
            )
        elif self.client:
            self.client.send_shoot(shot_data)

    def update(self):
        """Main game update loop."""
        if self.state != "playing":
            return

        if not self.local_player:
            return

        # Handle continuous fire when mouse buttons are held
        if self.local_player.is_alive:
            if self.local_player.keys_held.get('left mouse', False):
                self._shoot_primary()
            if self.local_player.keys_held.get('right mouse', False):
                self._shoot_secondary()

        # Update HUD
        self.hud.update_health(self.local_player.health)
        self.hud.update_speed(self.local_player.get_speed())
        self.hud.update_stats(self.local_player.kills, self.local_player.deaths)

        # Handle respawn
        if not self.local_player.is_alive:
            self.respawn_timer -= time.dt
            if self.respawn_timer <= 0:
                self._respawn_local_player()

        # Network updates
        self._process_network()

        # Check projectile collisions (host authoritative)
        if self.is_host:
            self._check_collisions()

        # Update player count
        total_players = 1 + len(self.remote_players)
        if len(self.remote_players) > 0 and total_players != getattr(self, '_last_player_count', 0):
            print(f"[MAIN] Player count updated: {total_players}, remote_players={list(self.remote_players.keys())}")
            self._last_player_count = total_players
        self.hud.update_player_count(total_players)

    def _process_network(self):
        """Process network messages and send updates."""
        current_time = time.time()

        # Send local player state
        if current_time - self.last_network_update >= self.network_update_rate:
            self.last_network_update = current_time

            if self.local_player:
                state = self.local_player.get_state()

                if self.is_host and self.server:
                    # Host broadcasts game state
                    self.server.broadcast_game_state({}, host_state=state)
                elif self.client:
                    # Client sends own state
                    self.client.send_player_update(state)

        # Process incoming messages
        messages = []
        if self.is_host and self.server:
            messages = self.server.get_messages()
        elif self.client:
            messages = self.client.get_messages()

        if messages:
            print(f"[MAIN] Processing {len(messages)} messages (is_host={self.is_host})")
        for msg in messages:
            print(f"[MAIN] Handling message: {msg.get('type')} for player {msg.get('player_id')}")
            self._handle_network_message(msg)

    def _handle_network_message(self, msg):
        """Handle a network message."""
        msg_type = msg.get("type")

        if msg_type == NetworkMessage.PLAYER_JOIN:
            player_id = msg.get("player_id")
            print(f"[MAIN] PLAYER_JOIN: player_id={player_id}, local_player_id={self.local_player.player_id}")
            if player_id is not None and player_id != self.local_player.player_id:
                self._add_remote_player(player_id, msg.get("state"))
                self.hud.show_message(f"Player {player_id} joined", 3.0)
            else:
                print(f"[MAIN] PLAYER_JOIN skipped (same as local or None)")

        elif msg_type == NetworkMessage.PLAYER_LEAVE:
            player_id = msg.get("player_id")
            self._remove_remote_player(player_id)
            self.hud.show_message(f"Player {player_id} left", 3.0)

        elif msg_type == NetworkMessage.PLAYER_UPDATE:
            player_id = msg.get("player_id")
            state = msg.get("state", {})

            if player_id is not None and player_id != self.local_player.player_id:
                if player_id not in self.remote_players:
                    print(
                        f"[LOG] Received update for unknown player {player_id}, creating..."
                    )
                    self._add_remote_player(player_id, state)
                else:
                    player = self.remote_players[player_id]
                    player.set_network_state(
                        state.get("position", (0, 0, 0)),
                        state.get("rotation", (0, 0, 0)),
                        state.get("velocity"),  # Pass velocity for interpolation
                    )
                    player.health = state.get("health", 100)
                    player.is_alive = state.get("is_alive", True)
                    player.visible = player.is_alive

        elif msg_type == NetworkMessage.PROJECTILE_SPAWN:
            proj = msg.get("projectile", {})
            owner_id = proj.get("owner_id")

            # Don't duplicate our own projectiles
            if owner_id != self.local_player.player_id:
                self.projectile_manager.spawn(
                    position=proj.get("position", (0, 0, 0)),
                    direction=proj.get("direction", (0, 0, 1)),
                    owner_id=owner_id,
                    projectile_id=proj.get("projectile_id"),
                    weapon=proj.get("weapon", "primary"),
                )

        elif msg_type == NetworkMessage.PLAYER_HIT:
            target_id = msg.get("target_id")
            attacker_id = msg.get("attacker_id")
            damage = msg.get("damage", 25)

            # Apply damage to local player if we're the target
            if target_id == self.local_player.player_id:
                died = self.local_player.take_damage(damage, attacker_id)
                if died:
                    self._on_local_death(attacker_id)

            # Update remote player health
            elif target_id in self.remote_players:
                self.remote_players[target_id].take_damage(damage, attacker_id)

        elif msg_type == NetworkMessage.PLAYER_RESPAWN:
            player_id = msg.get("player_id")
            position = msg.get("position", (0, 0, 0))

            if player_id in self.remote_players:
                self.remote_players[player_id].respawn(position)

    def _add_remote_player(self, player_id, state=None):
        """Add a remote player to the game."""
        if player_id in self.remote_players:
            print(f"[MAIN] Remote player {player_id} already exists, skipping")
            return

        if player_id == self.local_player.player_id:
            print(f"[MAIN] Skipping creation of self (player_id={player_id})")
            return

        # Get position from state or use default
        if state and "position" in state:
            position = state["position"]
        else:
            position = (5, 0, 5)  # Default visible position

        print(f"[MAIN] Creating remote player {player_id} at {position}")

        player = Player(
            player_id=player_id,
            is_local=False,
            position=position,
            arena_bounds=self.arena.get_bounds() if self.arena else (60, 30, 60)
        )
        player.visible = True

        self.remote_players[player_id] = player
        print(f"[MAIN] Added remote player {player_id}, total remote_players={len(self.remote_players)}")

    def _remove_remote_player(self, player_id):
        """Remove a remote player from the game."""
        if player_id in self.remote_players:
            destroy(self.remote_players[player_id])
            del self.remote_players[player_id]
            print(f"Removed remote player {player_id}")

    def _check_collisions(self):
        """Check projectile collisions (host only)."""
        # Check collisions - pass remote players and local player separately
        bounds = self.arena.get_bounds() if self.arena else (60, 30, 60)
        hits = self.projectile_manager.check_collisions(
            self.remote_players, self.local_player, bounds
        )

        # Process hits
        for hit in hits:
            target_id = hit["target_id"]
            attacker_id = hit["attacker_id"]
            damage = hit["damage"]

            # Apply damage
            if target_id == self.local_player.player_id:
                died = self.local_player.take_damage(damage, attacker_id)
                if died:
                    self._on_local_death(attacker_id)
                    # Give kill to attacker
                    if attacker_id in self.remote_players:
                        pass  # Remote player gets kill notification via broadcast
            elif target_id in self.remote_players:
                self.remote_players[target_id].take_damage(damage, attacker_id)

            # Broadcast hit to all clients
            if self.server:
                self.server.broadcast_hit(target_id, attacker_id, damage)

                # Give kill credit if target died
                target = all_players.get(target_id)
                if target and not target.is_alive:
                    if attacker_id == self.local_player.player_id:
                        self.local_player.add_kill()

    def _on_local_death(self, killer_id):
        """Handle local player death."""
        self.respawn_screen.show(killer_id)
        self.respawn_timer = self.respawn_delay

    def _respawn_local_player(self):
        """Respawn the local player."""
        self.respawn_screen.hide()

        spawn_pos = self.arena.get_random_spawn_point() if self.arena else Vec3(0, 0, 0)
        self.local_player.respawn((spawn_pos.x, spawn_pos.y, spawn_pos.z))

        # Broadcast respawn
        if self.is_host and self.server:
            self.server.broadcast_respawn(
                self.local_player.player_id, (spawn_pos.x, spawn_pos.y, spawn_pos.z)
            )

    def _return_to_menu(self):
        """Return to main menu."""
        # Reset camera before destroying player
        camera.parent = scene
        camera.position = (0, 0, 0)
        camera.rotation = (0, 0, 0)

        # Cleanup
        if self.server:
            self.server.stop()
            self.server = None
        if self.client:
            self.client.stop()
            self.client = None

        if self.local_player:
            destroy(self.local_player)
            self.local_player = None

        for player in self.remote_players.values():
            destroy(player)
        self.remote_players.clear()

        if self.arena:
            for wall in self.arena.walls:
                destroy(wall)
            for obs in self.arena.obstacles:
                destroy(obs)
            self.arena = None

        self.projectile_manager.clear()

        # Reset state
        self.state = "menu"
        self.hud.hide()
        self.respawn_screen.hide()
        self.main_menu.show()

    def run(self):
        """Start the game."""
        self.app.run()


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
    try:
        game = Game()
        _game = game  # Set module-level reference for update() and input()
        game.run()
    except Exception as e:
        print(f"[ERROR] Unhandled exception: {e}")
        traceback.print_exc()
        raise
    finally:
        print(f"[LOG] Game ended at {datetime.now()}")
        _log_file.close()
