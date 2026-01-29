#!/usr/bin/env python3
"""
Automated test runner for the game.
Runs host and client instances automatically without manual clicking.
"""
import sys
import os

# Set mode from command line: 'host' or 'client'
MODE = sys.argv[1] if len(sys.argv) > 1 else 'host'
HOST_IP = sys.argv[2] if len(sys.argv) > 2 else '127.0.0.1'

print(f"[AUTO_TEST] Starting in {MODE} mode")
if MODE == 'client':
    print(f"[AUTO_TEST] Will connect to {HOST_IP}")

# Now import and patch the game
from ursina import *
from player import Player
from projectile import ProjectileManager
from arena import Arena
from networking import NetworkServer, NetworkClient, NetworkMessage, get_local_ip
from ui import MainMenu, JoinDialog, HUD, RespawnScreen
import time as pytime


class AutoTestGame:
    """Game class that auto-starts in host or client mode."""

    def __init__(self, mode='host', host_ip='127.0.0.1'):
        self.mode = mode
        self.host_ip = host_ip

        self.app = Ursina(
            title=f'Game Test - {mode.upper()}',
            borderless=False,
            size=(800, 600),
            position=(50 if mode == 'host' else 900, 100)
        )

        # Game state
        self.state = 'menu'
        self.is_host = False
        self.local_player = None
        self.remote_players = {}
        self.arena = None

        # Networking
        self.server = None
        self.client = None
        self.network_update_rate = 1/30
        self.last_network_update = 0

        # Systems
        self.projectile_manager = ProjectileManager()

        # Respawn
        self.respawn_timer = 0
        self.respawn_delay = 3.0

        # Create minimal UI
        self.hud = HUD()
        self.respawn_screen = RespawnScreen()

        # Status text
        self.status_text = Text(
            text=f'Mode: {mode.upper()}\nStarting...',
            position=(-0.85, 0.45),
            scale=1.2,
            color=color.yellow
        )

        self.log_text = Text(
            text='',
            position=(-0.85, 0.35),
            scale=0.8,
            color=color.white
        )

        self.log_messages = []

        # Lighting
        AmbientLight(color=color.rgb(100, 100, 120))
        DirectionalLight(y=2, z=3, shadows=True)

        # Input/Update handlers
        self.app.input = self.input
        self.app.update = self.update

        # Auto-start after a short delay
        self.start_delay = 1.0
        self.started = False
        self.test_actions_done = False
        self.test_start_time = None

    def log(self, msg):
        """Add a log message."""
        timestamp = pytime.strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {msg}"
        print(full_msg)
        self.log_messages.append(full_msg)
        # Keep last 10 messages
        if len(self.log_messages) > 10:
            self.log_messages = self.log_messages[-10:]
        self.log_text.text = '\n'.join(self.log_messages[-6:])

    def host_game(self):
        """Start hosting a game."""
        self.log("Starting server...")

        self.server = NetworkServer(port=5555)
        if not self.server.start():
            self.log("ERROR: Failed to start server")
            return False

        self.is_host = True
        self._start_game(player_id=0)

        local_ip = get_local_ip()
        self.log(f"Hosting on {local_ip}:5555")
        self.status_text.text = f'HOST MODE\nIP: {local_ip}:5555\nPlayer ID: 0'
        return True

    def join_game(self):
        """Join a hosted game."""
        self.log(f"Connecting to {self.host_ip}:5555...")

        self.client = NetworkClient()
        if not self.client.connect(self.host_ip, port=5555, timeout=5.0):
            self.log("ERROR: Connection failed")
            return False

        self.is_host = False
        self._start_game(player_id=self.client.player_id)
        self.log(f"Connected as Player {self.client.player_id}")
        self.status_text.text = f'CLIENT MODE\nConnected to: {self.host_ip}\nPlayer ID: {self.client.player_id}'
        return True

    def _start_game(self, player_id):
        """Initialize game world."""
        self.arena = Arena(size=(50, 30, 50))

        spawn_pos = self.arena.get_random_spawn_point()
        self.local_player = Player(
            player_id=player_id,
            is_local=True,
            position=spawn_pos
        )

        self.hud.show()
        self.hud.update_health(self.local_player.health)
        self.hud.update_stats(0, 0)
        self.hud.update_player_count(1)

        self.state = 'playing'
        self.test_start_time = pytime.time()
        self.log(f"Game started! Player at {spawn_pos}")

    def input(self, key):
        """Handle input."""
        if key == 'escape':
            self.quit_game()

        if key == 'left mouse down' and self.state == 'playing':
            if self.local_player and self.local_player.can_shoot():
                self._shoot()

    def _shoot(self):
        """Handle shooting."""
        shot_data = self.local_player.shoot()
        self.projectile_manager.spawn(
            position=shot_data['position'],
            direction=shot_data['direction'],
            owner_id=shot_data['owner_id']
        )
        self.log("Shot fired!")

        if self.is_host and self.server:
            self.server._broadcast({
                'type': NetworkMessage.PROJECTILE_SPAWN,
                'projectile': shot_data
            })
        elif self.client:
            self.client.send_shoot(shot_data)

    def update(self):
        """Main update loop."""
        # Auto-start logic
        if not self.started:
            self.start_delay -= time.dt
            if self.start_delay <= 0:
                self.started = True
                if self.mode == 'host':
                    self.host_game()
                else:
                    self.join_game()
            return

        if self.state != 'playing' or not self.local_player:
            return

        # Clamp player to arena
        if self.arena:
            self.local_player.position = self.arena.clamp_position(
                self.local_player.position
            )

        # Update HUD
        self.hud.update_health(self.local_player.health)
        self.hud.update_stats(self.local_player.kills, self.local_player.deaths)

        # Handle respawn
        if not self.local_player.is_alive:
            self.respawn_timer -= time.dt
            if self.respawn_timer <= 0:
                self._respawn_local_player()

        # Network updates
        self._process_network()

        # Collision detection (host only)
        if self.is_host:
            self._check_collisions()

        # Update player count
        total_players = 1 + len(self.remote_players)
        self.hud.update_player_count(total_players)

        # Automated test actions
        if not self.test_actions_done and self.test_start_time:
            elapsed = pytime.time() - self.test_start_time

            # Log player count periodically
            if int(elapsed) % 3 == 0 and int(elapsed) > 0:
                self.log(f"Players connected: {total_players}")

            # Move around a bit for testing
            if elapsed > 2:
                # Simulate some movement
                self.local_player.position += Vec3(
                    0.1 * pytime.time() % 1,
                    0,
                    0.1 * pytime.time() % 1
                )

            # Fire a test shot at 5 seconds
            if elapsed > 5 and elapsed < 5.1:
                self._shoot()

            # After 15 seconds, consider test done
            if elapsed > 15:
                self.test_actions_done = True
                self.log("TEST COMPLETE - Game running successfully!")
                self.log(f"Final player count: {total_players}")

    def _process_network(self):
        """Process network messages."""
        current_time = pytime.time()

        if current_time - self.last_network_update >= self.network_update_rate:
            self.last_network_update = current_time

            if self.local_player:
                state = self.local_player.get_state()

                if self.is_host and self.server:
                    self.server.broadcast_game_state({}, host_state=state)
                elif self.client:
                    self.client.send_player_update(state)

        # Process incoming
        messages = []
        if self.is_host and self.server:
            messages = self.server.get_messages()
        elif self.client:
            messages = self.client.get_messages()

        for msg in messages:
            self._handle_network_message(msg)

    def _handle_network_message(self, msg):
        """Handle network message."""
        msg_type = msg.get('type')

        if msg_type == NetworkMessage.PLAYER_JOIN:
            player_id = msg.get('player_id')
            if player_id != self.local_player.player_id:
                self._add_remote_player(player_id, msg.get('state'))
                self.log(f"Player {player_id} joined!")

        elif msg_type == NetworkMessage.PLAYER_LEAVE:
            player_id = msg.get('player_id')
            self._remove_remote_player(player_id)
            self.log(f"Player {player_id} left")

        elif msg_type == NetworkMessage.PLAYER_UPDATE:
            player_id = msg.get('player_id')
            state = msg.get('state', {})

            if player_id != self.local_player.player_id:
                if player_id not in self.remote_players:
                    self._add_remote_player(player_id, state)
                else:
                    player = self.remote_players[player_id]
                    player.set_network_state(
                        state.get('position', (0, 0, 0)),
                        state.get('rotation', (0, 0, 0))
                    )
                    player.health = state.get('health', 100)
                    player.is_alive = state.get('is_alive', True)
                    player.visible = player.is_alive

        elif msg_type == NetworkMessage.PROJECTILE_SPAWN:
            proj = msg.get('projectile', {})
            owner_id = proj.get('owner_id')
            if owner_id != self.local_player.player_id:
                self.projectile_manager.spawn(
                    position=proj.get('position', (0, 0, 0)),
                    direction=proj.get('direction', (0, 0, 1)),
                    owner_id=owner_id,
                    projectile_id=proj.get('projectile_id')
                )
                self.log(f"Remote player {owner_id} fired!")

        elif msg_type == NetworkMessage.PLAYER_HIT:
            target_id = msg.get('target_id')
            attacker_id = msg.get('attacker_id')
            damage = msg.get('damage', 25)

            if target_id == self.local_player.player_id:
                died = self.local_player.take_damage(damage, attacker_id)
                if died:
                    self._on_local_death(attacker_id)
            elif target_id in self.remote_players:
                self.remote_players[target_id].take_damage(damage, attacker_id)

        elif msg_type == NetworkMessage.PLAYER_RESPAWN:
            player_id = msg.get('player_id')
            position = msg.get('position', (0, 0, 0))
            if player_id in self.remote_players:
                self.remote_players[player_id].respawn(position)

    def _add_remote_player(self, player_id, state=None):
        """Add remote player."""
        if player_id in self.remote_players:
            return

        position = (0, 0, 0)
        if state and 'position' in state:
            position = state['position']

        player = Player(
            player_id=player_id,
            is_local=False,
            position=position
        )
        self.remote_players[player_id] = player
        self.log(f"Added remote player {player_id}")

    def _remove_remote_player(self, player_id):
        """Remove remote player."""
        if player_id in self.remote_players:
            destroy(self.remote_players[player_id])
            del self.remote_players[player_id]

    def _check_collisions(self):
        """Check projectile collisions."""
        all_players = {self.local_player.player_id: self.local_player}
        all_players.update(self.remote_players)

        bounds = self.arena.get_bounds() if self.arena else (25, 15, 25)
        hits = self.projectile_manager.check_collisions(all_players, bounds)

        for hit in hits:
            target_id = hit['target_id']
            attacker_id = hit['attacker_id']
            damage = hit['damage']

            if target_id == self.local_player.player_id:
                died = self.local_player.take_damage(damage, attacker_id)
                if died:
                    self._on_local_death(attacker_id)
            elif target_id in self.remote_players:
                self.remote_players[target_id].take_damage(damage, attacker_id)

            if self.server:
                self.server.broadcast_hit(target_id, attacker_id, damage)

    def _on_local_death(self, killer_id):
        """Handle death."""
        self.respawn_screen.show(killer_id)
        self.respawn_timer = self.respawn_delay
        self.log(f"Killed by player {killer_id}")

    def _respawn_local_player(self):
        """Respawn player."""
        self.respawn_screen.hide()
        spawn_pos = self.arena.get_random_spawn_point() if self.arena else Vec3(0, 0, 0)
        self.local_player.respawn((spawn_pos.x, spawn_pos.y, spawn_pos.z))
        self.log("Respawned!")

        if self.is_host and self.server:
            self.server.broadcast_respawn(
                self.local_player.player_id,
                (spawn_pos.x, spawn_pos.y, spawn_pos.z)
            )

    def quit_game(self):
        """Quit."""
        self.log("Quitting...")
        if self.server:
            self.server.stop()
        if self.client:
            self.client.stop()
        application.quit()

    def run(self):
        """Run the game."""
        self.app.run()


if __name__ == '__main__':
    game = AutoTestGame(mode=MODE, host_ip=HOST_IP)
    game.run()
