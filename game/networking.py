"""Server/client networking logic using UDP."""
import socket
import threading
import json
import time
from collections import defaultdict


class NetworkMessage:
    """Message types for network communication."""
    PLAYER_JOIN = 'player_join'
    PLAYER_LEAVE = 'player_leave'
    PLAYER_UPDATE = 'player_update'
    PROJECTILE_SPAWN = 'projectile_spawn'
    PLAYER_HIT = 'player_hit'
    PLAYER_RESPAWN = 'player_respawn'
    GAME_STATE = 'game_state'
    PING = 'ping'
    PONG = 'pong'


class NetworkServer:
    """UDP server for hosting games."""

    def __init__(self, port=5555):
        self.port = port
        self.socket = None
        self.running = False
        self.clients = {}  # addr -> player_id
        self.player_states = {}  # player_id -> state dict
        self.next_player_id = 1  # 0 is reserved for host
        self.message_queue = []
        self.lock = threading.Lock()
        self.projectile_id_counter = 0

    def start(self):
        """Start the server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('0.0.0.0', self.port))
        self.socket.settimeout(0.1)
        self.running = True

        # Initialize host (player 0) in player_states so clients see them on join
        self.player_states[0] = {
            'player_id': 0,
            'position': (0, 0, 0),
            'rotation': (0, 0, 0),
            'health': 100,
            'is_alive': True
        }

        # Start receive thread
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()

        print(f"Server started on port {self.port}")
        return True

    def stop(self):
        """Stop the server."""
        self.running = False
        if self.socket:
            self.socket.close()

    def _receive_loop(self):
        """Background thread to receive messages."""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(4096)
                message = json.loads(data.decode('utf-8'))

                with self.lock:
                    self._handle_message(message, addr)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Server receive error: {e}")

    def _handle_message(self, message, addr):
        """Process incoming message."""
        msg_type = message.get('type')

        if msg_type == NetworkMessage.PLAYER_JOIN:
            # New player joining
            if addr not in self.clients:
                player_id = self.next_player_id
                self.next_player_id += 1
                self.clients[addr] = player_id
                self.player_states[player_id] = {
                    'player_id': player_id,
                    'position': (0, 0, 0),
                    'rotation': (0, 0, 0),
                    'health': 100,
                    'is_alive': True
                }
                print(f"[NET-SERVER] New player {player_id} joined from {addr}")
                print(f"[NET-SERVER] Current player_states: {list(self.player_states.keys())}")

                # Send assignment to new player
                existing = list(self.player_states.values())
                print(f"[NET-SERVER] Sending existing_players: {existing}")
                self._send_to(addr, {
                    'type': NetworkMessage.PLAYER_JOIN,
                    'player_id': player_id,
                    'existing_players': existing
                })

                # Queue join notification for host
                print(f"[NET-SERVER] Queuing PLAYER_JOIN for host main thread")
                self.message_queue.append({
                    'type': NetworkMessage.PLAYER_JOIN,
                    'player_id': player_id
                })

                # Notify other clients
                self._broadcast({
                    'type': NetworkMessage.PLAYER_JOIN,
                    'player_id': player_id
                }, exclude=addr)

        elif msg_type == NetworkMessage.PLAYER_UPDATE:
            # Player state update
            player_id = self.clients.get(addr)
            if player_id is not None:
                state = message.get('state', {})
                state['player_id'] = player_id
                self.player_states[player_id] = state

                # Queue for main thread
                self.message_queue.append({
                    'type': NetworkMessage.PLAYER_UPDATE,
                    'player_id': player_id,
                    'state': state
                })

        elif msg_type == NetworkMessage.PROJECTILE_SPAWN:
            # Player shot
            player_id = self.clients.get(addr)
            if player_id is not None:
                self.projectile_id_counter += 1
                proj_data = message.get('projectile', {})
                proj_data['owner_id'] = player_id
                proj_data['projectile_id'] = self.projectile_id_counter

                self.message_queue.append({
                    'type': NetworkMessage.PROJECTILE_SPAWN,
                    'projectile': proj_data
                })

                # Broadcast to all clients
                self._broadcast({
                    'type': NetworkMessage.PROJECTILE_SPAWN,
                    'projectile': proj_data
                })

        elif msg_type == NetworkMessage.PLAYER_RESPAWN:
            # Client respawned
            player_id = self.clients.get(addr)
            if player_id is not None:
                position = message.get('position', (0, 0, 0))

                # Update player state
                if player_id in self.player_states:
                    self.player_states[player_id]['is_alive'] = True
                    self.player_states[player_id]['position'] = position

                # Queue for main thread
                self.message_queue.append({
                    'type': NetworkMessage.PLAYER_RESPAWN,
                    'player_id': player_id,
                    'position': position
                })

                # Broadcast to all clients (including back to sender for confirmation)
                self._broadcast({
                    'type': NetworkMessage.PLAYER_RESPAWN,
                    'player_id': player_id,
                    'position': position
                })

        elif msg_type == NetworkMessage.PING:
            self._send_to(addr, {'type': NetworkMessage.PONG})

    def _send_to(self, addr, message):
        """Send message to specific address."""
        try:
            data = json.dumps(message).encode('utf-8')
            self.socket.sendto(data, addr)
        except Exception as e:
            print(f"Send error: {e}")

    def _broadcast(self, message, exclude=None):
        """Send message to all clients."""
        for addr in self.clients:
            if addr != exclude:
                self._send_to(addr, message)

    def broadcast_game_state(self, players_data, host_state=None):
        """Broadcast full game state to all clients."""
        # Include host state with player_id
        if host_state:
            host_state['player_id'] = 0  # Host is always player 0
            self.player_states[0] = host_state

        state_msg = {
            'type': NetworkMessage.GAME_STATE,
            'players': list(self.player_states.values()),
            'timestamp': time.time()
        }
        self._broadcast(state_msg)

    def broadcast_hit(self, target_id, attacker_id, damage):
        """Broadcast hit event."""
        msg = {
            'type': NetworkMessage.PLAYER_HIT,
            'target_id': target_id,
            'attacker_id': attacker_id,
            'damage': damage
        }
        self._broadcast(msg)
        self.message_queue.append(msg)

    def broadcast_respawn(self, player_id, position):
        """Broadcast respawn event."""
        msg = {
            'type': NetworkMessage.PLAYER_RESPAWN,
            'player_id': player_id,
            'position': position
        }
        self._broadcast(msg)

    def get_messages(self):
        """Get and clear message queue."""
        with self.lock:
            messages = self.message_queue.copy()
            self.message_queue.clear()
        return messages

    def get_client_count(self):
        """Get number of connected clients."""
        return len(self.clients)


class NetworkClient:
    """UDP client for joining games."""

    def __init__(self):
        self.socket = None
        self.server_addr = None
        self.running = False
        self.player_id = None
        self.message_queue = []
        self.lock = threading.Lock()
        self.connected = False

    def connect(self, host_ip, port=5555, timeout=5.0):
        """Connect to a server."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(0.1)
        self.server_addr = (host_ip, port)
        self.running = True

        # Start receive thread
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()

        # Send join request
        self._send({
            'type': NetworkMessage.PLAYER_JOIN
        })

        # Wait for response
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.player_id is not None:
                self.connected = True
                print(f"Connected to server as player {self.player_id}")
                return True
            time.sleep(0.1)

        self.stop()
        return False

    def stop(self):
        """Disconnect from server."""
        self.running = False
        self.connected = False
        if self.socket:
            self.socket.close()

    def _receive_loop(self):
        """Background thread to receive messages."""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(4096)
                message = json.loads(data.decode('utf-8'))

                with self.lock:
                    self._handle_message(message)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Client receive error: {e}")

    def _handle_message(self, message):
        """Process incoming message."""
        msg_type = message.get('type')

        if msg_type == NetworkMessage.PLAYER_JOIN:
            print(f"[NET-CLIENT] Received PLAYER_JOIN: {message}")
            if self.player_id is None and 'player_id' in message:
                # First time - this is our player ID assignment from server
                self.player_id = message['player_id']
                print(f"[NET-CLIENT] Assigned player_id={self.player_id}")

                # Queue existing players info (includes host and any other players)
                existing = message.get('existing_players', [])
                print(f"[NET-CLIENT] Existing players in message: {existing}")
                for player_state in existing:
                    pid = player_state.get('player_id')
                    print(f"[NET-CLIENT] Checking existing player {pid} (self={self.player_id})")
                    if pid != self.player_id:
                        print(f"[NET-CLIENT] Queuing PLAYER_JOIN for player {pid}")
                        self.message_queue.append({
                            'type': NetworkMessage.PLAYER_JOIN,
                            'player_id': pid,
                            'state': player_state
                        })
            elif self.player_id is not None and 'player_id' in message:
                # Another player joined after us - queue the notification
                print(f"[NET-CLIENT] Another player joined: {message.get('player_id')}")
                self.message_queue.append(message)

        elif msg_type == NetworkMessage.GAME_STATE:
            # Full state update
            players = message.get('players', [])
            print(f"[NET-CLIENT] Received GAME_STATE with {len(players)} players")
            for player_state in players:
                pid = player_state.get('player_id')
                if pid is not None and pid != self.player_id:
                    print(f"[NET-CLIENT] Queuing PLAYER_UPDATE for player {pid}")
                    self.message_queue.append({
                        'type': NetworkMessage.PLAYER_UPDATE,
                        'player_id': pid,
                        'state': player_state
                    })

        elif msg_type in (NetworkMessage.PLAYER_UPDATE, NetworkMessage.PROJECTILE_SPAWN,
                         NetworkMessage.PLAYER_HIT, NetworkMessage.PLAYER_RESPAWN,
                         NetworkMessage.PLAYER_LEAVE):
            self.message_queue.append(message)

    def _send(self, message):
        """Send message to server."""
        if self.socket and self.server_addr:
            try:
                data = json.dumps(message).encode('utf-8')
                self.socket.sendto(data, self.server_addr)
            except Exception as e:
                print(f"Send error: {e}")

    def send_player_update(self, state):
        """Send player state to server."""
        self._send({
            'type': NetworkMessage.PLAYER_UPDATE,
            'state': state
        })

    def send_shoot(self, projectile_data):
        """Send shoot event to server."""
        self._send({
            'type': NetworkMessage.PROJECTILE_SPAWN,
            'projectile': projectile_data
        })

    def send_respawn(self, position):
        """Send respawn event to server."""
        self._send({
            'type': NetworkMessage.PLAYER_RESPAWN,
            'position': position
        })

    def get_messages(self):
        """Get and clear message queue."""
        with self.lock:
            messages = self.message_queue.copy()
            self.message_queue.clear()
        return messages


def get_local_ip():
    """Get the local IP address for LAN."""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"
