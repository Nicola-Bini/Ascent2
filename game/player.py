"""Player ship class with 6DOF controls and momentum-based physics."""
from ursina import *
import random


class Player(Entity):
    """6DOF player ship with physics-based movement."""

    def __init__(self, player_id=0, is_local=True, arena_bounds=None, **kwargs):
        # Realistic ship colors - dark metallic with accent lights
        if is_local:
            ship_color = color.rgb(60, 65, 75)  # Dark gunmetal
        else:
            ship_color = color.rgb(80, 45, 45)  # Dark red-brown for enemies

        super().__init__(
            model='cube',
            color=ship_color,
            scale=(1.5, 0.75, 3) if not is_local else (1, 0.5, 2),
            collider='box',
            **kwargs
        )

        self.player_id = player_id
        self.is_local = is_local
        self.arena_bounds = arena_bounds

        # Physics settings
        self.velocity = Vec3(0, 0, 0)  # Current velocity vector
        self.max_speed = 50  # Maximum speed
        self.acceleration = 45  # Acceleration rate (increased)
        self.deceleration = 5  # Lower drag for more drift
        self.strafe_multiplier = 0.9  # Strafe nearly as fast
        self.vertical_multiplier = 0.85  # Vertical nearly as fast

        # Rotation settings
        self.roll_speed = 120  # degrees per second
        self.mouse_sensitivity = 40
        self.rotation_velocity = Vec3(0, 0, 0)  # For smooth rotation

        # Combat - Primary weapon (rapid fire)
        self.max_health = 100
        self.health = self.max_health
        self.is_alive = True
        self.respawn_time = 3.0
        self.primary_cooldown = 0.12  # Fast fire rate
        self.last_primary_time = 0

        # Combat - Secondary weapon (slow powerful shot)
        self.secondary_cooldown = 1.5  # Slow fire rate
        self.last_secondary_time = 0
        self.secondary_damage = 50  # High damage

        # Stats
        self.kills = 0
        self.deaths = 0

        # Track key states locally
        self.keys_held = {
            'w': False, 's': False, 'a': False, 'd': False,
            'q': False, 'e': False,
            'space': False, 'shift': False, 'control': False,
            'left mouse': False, 'right mouse': False
        }

        # For network interpolation
        self.target_position = self.position
        self.target_rotation = self.rotation
        self.target_velocity = Vec3(0, 0, 0)
        self.interpolation_speed = 15

        # Create ship visual details
        self._create_ship_details()

        if is_local:
            mouse.locked = True
            mouse.visible = False
            camera.parent = scene
            camera.position = self.position
            camera.rotation = (0, 0, 0)
            camera.fov = 100

            # Hide local player model
            self.visible = False
            self.cockpit.visible = False
            self.left_wing.visible = False
            self.right_wing.visible = False
            self.engine_glow.visible = False

    def _create_ship_details(self):
        """Add visual details with realistic colors."""
        # Cockpit - dim cyan glow for local, orange for enemies
        cockpit_color = color.rgb(40, 80, 90) if self.is_local else color.rgb(120, 70, 30)
        self.cockpit = Entity(
            parent=self,
            model='cube',
            color=cockpit_color,
            scale=(0.5, 0.4, 0.6),
            position=(0, 0.4, 0.6),
        )

        # Wings - darker metallic
        wing_color = color.rgb(50, 55, 65) if self.is_local else color.rgb(70, 40, 40)
        self.left_wing = Entity(
            parent=self,
            model='cube',
            color=wing_color,
            scale=(2, 0.15, 1),
            position=(-1, 0, -0.3),
        )
        self.right_wing = Entity(
            parent=self,
            model='cube',
            color=wing_color,
            scale=(2, 0.15, 1),
            position=(1, 0, -0.3),
        )

        # Engine glow
        engine_color = color.rgb(100, 150, 255) if self.is_local else color.rgb(255, 100, 50)
        self.engine_glow = Entity(
            parent=self,
            model='cube',
            color=engine_color,
            scale=(0.4, 0.3, 0.2),
            position=(0, 0, -1.2),
        )

    def input(self, key):
        """Handle key press/release events."""
        if not self.is_local:
            return

        key_map = {
            'w': 'w', 's': 's', 'a': 'a', 'd': 'd',
            'q': 'q', 'e': 'e',
            'space': 'space',
            'left shift': 'shift', 'shift': 'shift',
            'left control': 'control', 'control': 'control',
            'left mouse down': 'left mouse',
            'right mouse down': 'right mouse',
        }

        release_map = {
            'left mouse up': 'left mouse',
            'right mouse up': 'right mouse',
        }

        # Handle mouse button releases
        if key in release_map:
            self.keys_held[release_map[key]] = False
            return

        # Handle mouse button presses
        if key in key_map:
            self.keys_held[key_map[key]] = True
            return

        # Handle keyboard releases
        if key.endswith(' up'):
            base_key = key[:-3]
            if base_key in key_map:
                self.keys_held[key_map[base_key]] = False
        elif key in key_map:
            self.keys_held[key_map[key]] = True

    def update(self):
        """Handle input and movement."""
        if not self.is_alive:
            return

        if self.is_local:
            self._handle_local_input()
        else:
            self._interpolate_to_target()

    def _handle_local_input(self):
        """Process input with physics-based movement."""
        dt = time.dt

        # Mouse look (pitch and yaw)
        if mouse.locked:
            mv = mouse.velocity
            self.rotation_y += mv[0] * self.mouse_sensitivity
            self.rotation_x -= mv[1] * self.mouse_sensitivity
            self.rotation_x = clamp(self.rotation_x, -89, 89)

        keys = self.keys_held

        # Roll (Q/E)
        roll_input = (1 if keys['e'] else 0) - (1 if keys['q'] else 0)
        self.rotation_z += roll_input * self.roll_speed * dt

        # Calculate input direction
        forward_input = (1 if keys['w'] else 0) - (1 if keys['s'] else 0)
        strafe_input = (1 if keys['d'] else 0) - (1 if keys['a'] else 0)
        vertical_input = (1 if keys['space'] else 0) - (1 if (keys['shift'] or keys['control']) else 0)

        # Use entity's built-in direction vectors - these properly account for all rotations
        # including roll, giving true Descent-style 6DOF movement
        ship_forward = self.forward  # Direction ship is facing
        ship_right = self.right      # Ship's right side
        ship_up = self.up            # Ship's top

        # Calculate desired acceleration in ship's local space
        accel = Vec3(0, 0, 0)
        if forward_input != 0:
            accel += ship_forward * forward_input * self.acceleration
        if strafe_input != 0:
            accel += ship_right * strafe_input * self.acceleration * self.strafe_multiplier
        if vertical_input != 0:
            accel += ship_up * vertical_input * self.acceleration * self.vertical_multiplier

        # Apply acceleration to velocity
        if accel.length() > 0:
            self.velocity += accel * dt
        else:
            # Apply drag when no input
            drag = self.deceleration * dt
            if self.velocity.length() > drag:
                self.velocity -= self.velocity.normalized() * drag
            else:
                self.velocity = Vec3(0, 0, 0)

        # Clamp to max speed
        if self.velocity.length() > self.max_speed:
            self.velocity = self.velocity.normalized() * self.max_speed

        # Apply velocity to position
        self.position += self.velocity * dt

        # Bounce off arena bounds
        if self.arena_bounds:
            margin = 2
            hx, hy, hz = self.arena_bounds

            if abs(self.x) > hx - margin:
                self.x = clamp(self.x, -hx + margin, hx - margin)
                self.velocity.x *= -0.5  # Bounce with energy loss

            if abs(self.y) > hy - margin:
                self.y = clamp(self.y, -hy + margin, hy - margin)
                self.velocity.y *= -0.5

            if abs(self.z) > hz - margin:
                self.z = clamp(self.z, -hz + margin, hz - margin)
                self.velocity.z *= -0.5

        # Update camera
        camera.position = self.position
        camera.rotation_x = self.rotation_x
        camera.rotation_y = self.rotation_y
        camera.rotation_z = self.rotation_z

    def _interpolate_to_target(self):
        """Smoothly interpolate to target state for remote players."""
        dt = time.dt

        # Position interpolation with velocity prediction
        self.position = lerp(self.position, self.target_position,
                            self.interpolation_speed * dt)

        # Velocity interpolation
        self.velocity = lerp(self.velocity, self.target_velocity,
                            self.interpolation_speed * dt)

        # Rotation interpolation
        self.rotation_x = lerp(self.rotation_x, self.target_rotation[0],
                              self.interpolation_speed * dt)
        self.rotation_y = lerp(self.rotation_y, self.target_rotation[1],
                              self.interpolation_speed * dt)
        self.rotation_z = lerp(self.rotation_z, self.target_rotation[2],
                              self.interpolation_speed * dt)

    def set_network_state(self, position, rotation, velocity=None):
        """Set target state for network interpolation."""
        self.target_position = Vec3(position[0], position[1], position[2])
        self.target_rotation = rotation
        if velocity:
            self.target_velocity = Vec3(velocity[0], velocity[1], velocity[2])

    def get_state(self):
        """Get current state for network transmission."""
        return {
            'player_id': self.player_id,
            'position': (self.position.x, self.position.y, self.position.z),
            'rotation': (self.rotation_x, self.rotation_y, self.rotation_z),
            'velocity': (self.velocity.x, self.velocity.y, self.velocity.z),
            'health': self.health,
            'is_alive': self.is_alive
        }

    def can_shoot_primary(self):
        """Check if player can fire primary weapon."""
        return self.is_alive and (time.time() - self.last_primary_time) >= self.primary_cooldown

    def can_shoot_secondary(self):
        """Check if player can fire secondary weapon."""
        return self.is_alive and (time.time() - self.last_secondary_time) >= self.secondary_cooldown

    def shoot_primary(self):
        """Fire primary weapon (rapid fire)."""
        self.last_primary_time = time.time()
        return {
            'position': (self.position.x, self.position.y, self.position.z),
            'direction': (self.forward.x, self.forward.y, self.forward.z),
            'owner_id': self.player_id,
            'weapon': 'primary'
        }

    def shoot_secondary(self):
        """Fire secondary weapon (slow, powerful)."""
        self.last_secondary_time = time.time()
        return {
            'position': (self.position.x, self.position.y, self.position.z),
            'direction': (self.forward.x, self.forward.y, self.forward.z),
            'owner_id': self.player_id,
            'weapon': 'secondary'
        }

    def take_damage(self, amount, attacker_id=None):
        """Apply damage to player."""
        if not self.is_alive:
            return False

        self.health -= amount
        self.blink(color.red, duration=0.1)

        if self.health <= 0:
            self.die(attacker_id)
            return True
        return False

    def die(self, killer_id=None):
        """Handle player death."""
        self.is_alive = False
        self.deaths += 1
        self.visible = False
        self.velocity = Vec3(0, 0, 0)

        if self.is_local:
            mouse.locked = False
            mouse.visible = True

    def respawn(self, position=None):
        """Respawn the player."""
        self.health = self.max_health
        self.is_alive = True
        self.velocity = Vec3(0, 0, 0)

        if not self.is_local:
            self.visible = True

        if position:
            self.position = Vec3(position[0], position[1], position[2])
        else:
            self.position = Vec3(
                random.uniform(-20, 20),
                random.uniform(-10, 10),
                random.uniform(-20, 20)
            )

        self.rotation = Vec3(0, 0, 0)

        if self.is_local:
            mouse.locked = True
            mouse.visible = False

    def add_kill(self):
        """Increment kill count."""
        self.kills += 1

    def get_speed(self):
        """Get current speed for HUD display."""
        return self.velocity.length()
