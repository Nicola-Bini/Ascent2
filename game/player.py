"""Player ship class with 6DOF controls."""
from ursina import *
from ursina import curve
import math

class Player(Entity):
    """6DOF player ship with full movement controls."""

    def __init__(self, player_id=0, is_local=True, arena_bounds=None, **kwargs):
        super().__init__(
            model='cube',
            color=color.azure if is_local else color.orange,
            scale=(1.5, 0.75, 3) if not is_local else (1, 0.5, 2),  # Bigger for remote
            collider='box',
            unlit=True,  # Always visible regardless of lighting
            **kwargs
        )

        self.player_id = player_id
        self.is_local = is_local
        self.arena_bounds = arena_bounds  # (half_x, half_y, half_z)

        # Movement settings
        self.move_speed = 15
        self.strafe_speed = 12
        self.vertical_speed = 10
        self.roll_speed = 90  # degrees per second
        self.mouse_sensitivity = 50

        # Combat
        self.max_health = 100
        self.health = self.max_health
        self.is_alive = True
        self.respawn_time = 3.0
        self.shoot_cooldown = 0.15
        self.last_shot_time = 0

        # Stats
        self.kills = 0
        self.deaths = 0

        # Track key states locally (more reliable than held_keys)
        self.keys_held = {
            'w': False, 's': False, 'a': False, 'd': False,
            'q': False, 'e': False,
            'space': False, 'shift': False, 'control': False
        }

        # For network interpolation
        self.target_position = self.position
        self.target_rotation = self.rotation
        self.interpolation_speed = 15

        # Create ship visual details
        self._create_ship_details()

        if is_local:
            # Hide cursor for FPS-style controls
            mouse.locked = True
            mouse.visible = False

            # Initialize camera position (we update it manually each frame)
            camera.parent = scene
            camera.position = self.position + Vec3(0, 0.5, 0)
            camera.rotation = (0, 0, 0)
            camera.fov = 100  # Wider FOV for better spatial awareness

            # Hide local player model (we're inside it)
            self.visible = False
            self.cockpit.visible = False
            self.left_wing.visible = False
            self.right_wing.visible = False

    def _create_ship_details(self):
        """Add visual details to make ship recognizable."""
        # Cockpit - bright yellow for remote, cyan for local
        self.cockpit = Entity(
            parent=self,
            model='cube',
            color=color.cyan if self.is_local else color.yellow,
            scale=(0.5, 0.4, 0.6),
            position=(0, 0.4, 0.6),
            unlit=True
        )

        # Wings - contrasting color
        wing_color = color.rgb(100, 150, 255) if self.is_local else color.rgb(255, 150, 50)
        self.left_wing = Entity(
            parent=self,
            model='cube',
            color=wing_color,
            scale=(2, 0.15, 1),
            position=(-1, 0, -0.3),
            unlit=True
        )
        self.right_wing = Entity(
            parent=self,
            model='cube',
            color=wing_color,
            scale=(2, 0.15, 1),
            position=(1, 0, -0.3),
            unlit=True
        )

    def input(self, key):
        """Handle key press/release events to track key states."""
        if not self.is_local:
            return

        # Map key names to our tracking dict
        key_map = {
            'w': 'w', 's': 's', 'a': 'a', 'd': 'd',
            'q': 'q', 'e': 'e',
            'space': 'space',
            'left shift': 'shift', 'shift': 'shift',
            'left control': 'control', 'control': 'control'
        }

        # Check for key release (ends with ' up')
        if key.endswith(' up'):
            base_key = key[:-3]  # Remove ' up' suffix
            if base_key in key_map:
                self.keys_held[key_map[base_key]] = False
        else:
            # Key press
            if key in key_map:
                self.keys_held[key_map[key]] = True

    def update(self):
        """Handle input and movement for local player."""
        if not self.is_alive:
            return

        if self.is_local:
            self._handle_local_input()
        else:
            self._interpolate_to_target()

    def _handle_local_input(self):
        """Process keyboard and mouse input for 6DOF movement."""
        dt = time.dt

        # Mouse look (pitch and yaw)
        if mouse.locked:
            mv = mouse.velocity
            self.rotation_y += mv[0] * self.mouse_sensitivity
            self.rotation_x -= mv[1] * self.mouse_sensitivity
            self.rotation_x = clamp(self.rotation_x, -89, 89)

        # Use locally tracked key states (more reliable than held_keys)
        keys = self.keys_held

        # Roll (Q/E)
        q_held = 1 if keys['q'] else 0
        e_held = 1 if keys['e'] else 0
        self.rotation_z += (e_held - q_held) * self.roll_speed * dt

        # Movement input
        w_held = 1 if keys['w'] else 0
        s_held = 1 if keys['s'] else 0
        a_held = 1 if keys['a'] else 0
        d_held = 1 if keys['d'] else 0
        space_held = 1 if keys['space'] else 0
        shift_held = 1 if keys['shift'] else 0
        ctrl_held = 1 if keys['control'] else 0

        move_x = d_held - a_held  # Right - Left
        move_z = w_held - s_held  # Forward - Back
        move_y = space_held - (shift_held or ctrl_held)

        # Only move if there's input
        if move_x != 0 or move_y != 0 or move_z != 0:
            # Calculate direction based on yaw
            import math
            yaw = math.radians(self.rotation_y)

            # World-space velocity
            vel_x = (move_x * math.cos(yaw) + move_z * math.sin(yaw)) * self.move_speed
            vel_z = (-move_x * math.sin(yaw) + move_z * math.cos(yaw)) * self.move_speed
            vel_y = move_y * self.vertical_speed

            self.position += Vec3(vel_x, vel_y, vel_z) * dt

        # Clamp to arena bounds
        if self.arena_bounds:
            margin = 2
            hx, hy, hz = self.arena_bounds
            self.x = clamp(self.x, -hx + margin, hx - margin)
            self.y = clamp(self.y, -hy + margin, hy - margin)
            self.z = clamp(self.z, -hz + margin, hz - margin)

        # Update camera
        camera.position = self.position
        camera.rotation_x = self.rotation_x
        camera.rotation_y = self.rotation_y
        camera.rotation_z = self.rotation_z

    def _interpolate_to_target(self):
        """Smoothly interpolate to target position/rotation for remote players."""
        dt = time.dt

        # Position interpolation
        self.position = lerp(self.position, self.target_position,
                            self.interpolation_speed * dt)

        # Rotation interpolation
        self.rotation_x = lerp(self.rotation_x, self.target_rotation[0],
                              self.interpolation_speed * dt)
        self.rotation_y = lerp(self.rotation_y, self.target_rotation[1],
                              self.interpolation_speed * dt)
        self.rotation_z = lerp(self.rotation_z, self.target_rotation[2],
                              self.interpolation_speed * dt)

    def set_network_state(self, position, rotation):
        """Set target state for network interpolation."""
        self.target_position = Vec3(position[0], position[1], position[2])
        self.target_rotation = rotation

    def get_state(self):
        """Get current state for network transmission."""
        return {
            'player_id': self.player_id,
            'position': (self.position.x, self.position.y, self.position.z),
            'rotation': (self.rotation_x, self.rotation_y, self.rotation_z),
            'health': self.health,
            'is_alive': self.is_alive
        }

    def can_shoot(self):
        """Check if player can fire."""
        return self.is_alive and (time.time() - self.last_shot_time) >= self.shoot_cooldown

    def shoot(self):
        """Mark that player has shot (actual projectile created in main.py)."""
        self.last_shot_time = time.time()
        return {
            'position': (self.position.x, self.position.y, self.position.z),
            'direction': (self.forward.x, self.forward.y, self.forward.z),
            'owner_id': self.player_id
        }

    def take_damage(self, amount, attacker_id=None):
        """Apply damage to player."""
        if not self.is_alive:
            return False

        self.health -= amount

        # Visual feedback
        self.blink(color.red, duration=0.1)

        if self.health <= 0:
            self.die(attacker_id)
            return True  # Player died
        return False

    def die(self, killer_id=None):
        """Handle player death."""
        self.is_alive = False
        self.deaths += 1
        self.visible = False

        if self.is_local:
            mouse.locked = False
            mouse.visible = True

    def respawn(self, position=None):
        """Respawn the player."""
        self.health = self.max_health
        self.is_alive = True

        # Only make remote players visible (local player is first-person)
        if not self.is_local:
            self.visible = True

        if position:
            self.position = Vec3(position[0], position[1], position[2])
        else:
            # Default spawn at origin with some randomness
            import random
            self.position = Vec3(
                random.uniform(-10, 10),
                random.uniform(-5, 5),
                random.uniform(-10, 10)
            )

        self.rotation = Vec3(0, 0, 0)

        if self.is_local:
            mouse.locked = True
            mouse.visible = False

    def add_kill(self):
        """Increment kill count."""
        self.kills += 1
