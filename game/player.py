"""Player ship class with 6DOF controls and momentum-based physics."""
from ursina import *
import random


class Player(Entity):
    """6DOF player ship with physics-based movement. StarCraft Wraith-inspired design."""

    def __init__(self, player_id=0, is_local=True, arena_bounds=None, **kwargs):
        super().__init__(**kwargs)

        self.player_id = player_id
        self.is_local = is_local
        self.arena_bounds = arena_bounds

        # Physics settings
        self.velocity = Vec3(0, 0, 0)
        self.max_speed = 50
        self.acceleration = 45
        self.deceleration = 5
        self.strafe_multiplier = 0.9
        self.vertical_multiplier = 0.85

        # Rotation settings
        self.roll_speed = 120
        self.mouse_sensitivity = 40

        # Combat - Primary weapon (rapid fire)
        self.max_health = 100
        self.health = self.max_health
        self.is_alive = True
        self.respawn_time = 3.0
        self.primary_cooldown = 0.12
        self.last_primary_time = 0

        # Combat - Secondary weapon (slow powerful shot)
        self.secondary_cooldown = 1.5
        self.last_secondary_time = 0

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
        self.target_rotation = Vec3(0, 0, 0)
        self.target_velocity = Vec3(0, 0, 0)
        self.interpolation_speed = 15

        # Create StarCraft-inspired ship model
        self._create_ship_model()

        if is_local:
            mouse.locked = True
            mouse.visible = False
            camera.parent = scene
            camera.position = self.position
            camera.rotation = (0, 0, 0)
            camera.fov = 100
            self._hide_local_ship()

    def _create_ship_model(self):
        """Create a StarCraft Wraith-inspired ship model."""
        # Color scheme
        if self.is_local:
            main_color = color.rgb(70, 85, 100)  # Blue-gray (Terran)
            accent_color = color.rgb(50, 120, 180)  # Blue accent
            engine_color = color.rgb(80, 150, 255)  # Blue engine glow
        else:
            main_color = color.rgb(120, 60, 60)  # Red-brown (enemy)
            accent_color = color.rgb(180, 80, 50)  # Orange accent
            engine_color = color.rgb(255, 120, 50)  # Orange engine glow

        # Main fuselage - elongated body
        self.fuselage = Entity(
            parent=self,
            model='cube',
            color=main_color,
            scale=(1.2, 0.6, 3.5),
            position=(0, 0, 0),
        )

        # Cockpit - angled front section
        self.cockpit = Entity(
            parent=self,
            model='cube',
            color=color.rgb(40, 60, 80) if self.is_local else color.rgb(80, 50, 40),
            scale=(0.8, 0.5, 1.2),
            position=(0, 0.2, 1.8),
            rotation=(15, 0, 0),
        )

        # Cockpit glass
        self.cockpit_glass = Entity(
            parent=self,
            model='cube',
            color=color.rgb(100, 180, 220) if self.is_local else color.rgb(200, 150, 100),
            scale=(0.5, 0.3, 0.6),
            position=(0, 0.35, 2.0),
            rotation=(20, 0, 0),
        )

        # Left wing - swept back
        self.left_wing = Entity(
            parent=self,
            model='cube',
            color=main_color,
            scale=(3, 0.15, 1.8),
            position=(-1.8, 0, -0.5),
            rotation=(0, 0, -8),
        )

        # Right wing - swept back
        self.right_wing = Entity(
            parent=self,
            model='cube',
            color=main_color,
            scale=(3, 0.15, 1.8),
            position=(1.8, 0, -0.5),
            rotation=(0, 0, 8),
        )

        # Left wing tip / weapon pod
        self.left_weapon = Entity(
            parent=self,
            model='cube',
            color=accent_color,
            scale=(0.5, 0.4, 1.5),
            position=(-3.2, 0.1, -0.3),
        )

        # Right wing tip / weapon pod
        self.right_weapon = Entity(
            parent=self,
            model='cube',
            color=accent_color,
            scale=(0.5, 0.4, 1.5),
            position=(3.2, 0.1, -0.3),
        )

        # Tail fin - vertical stabilizer
        self.tail_fin = Entity(
            parent=self,
            model='cube',
            color=main_color,
            scale=(0.15, 1.2, 1.0),
            position=(0, 0.6, -1.5),
        )

        # Left engine nacelle
        self.left_engine = Entity(
            parent=self,
            model='cube',
            color=color.rgb(50, 55, 65),
            scale=(0.6, 0.5, 1.8),
            position=(-1.0, -0.2, -1.2),
        )

        # Right engine nacelle
        self.right_engine = Entity(
            parent=self,
            model='cube',
            color=color.rgb(50, 55, 65),
            scale=(0.6, 0.5, 1.8),
            position=(1.0, -0.2, -1.2),
        )

        # Left engine glow
        self.left_glow = Entity(
            parent=self,
            model='cube',
            color=engine_color,
            scale=(0.4, 0.35, 0.2),
            position=(-1.0, -0.2, -2.1),
        )

        # Right engine glow
        self.right_glow = Entity(
            parent=self,
            model='cube',
            color=engine_color,
            scale=(0.4, 0.35, 0.2),
            position=(1.0, -0.2, -2.1),
        )

        # Store all parts for visibility toggling
        self.ship_parts = [
            self.fuselage, self.cockpit, self.cockpit_glass,
            self.left_wing, self.right_wing,
            self.left_weapon, self.right_weapon,
            self.tail_fin,
            self.left_engine, self.right_engine,
            self.left_glow, self.right_glow
        ]

    def _hide_local_ship(self):
        """Hide ship model for first-person view."""
        for part in self.ship_parts:
            part.visible = False

    def _show_ship(self):
        """Show ship model (for remote players or respawn)."""
        for part in self.ship_parts:
            part.visible = True

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

        if key in release_map:
            self.keys_held[release_map[key]] = False
            return

        if key in key_map:
            self.keys_held[key_map[key]] = True
            return

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

        if mouse.locked:
            mv = mouse.velocity
            self.rotation_y += mv[0] * self.mouse_sensitivity
            self.rotation_x -= mv[1] * self.mouse_sensitivity
            self.rotation_x = clamp(self.rotation_x, -89, 89)

        keys = self.keys_held

        roll_input = (1 if keys['e'] else 0) - (1 if keys['q'] else 0)
        self.rotation_z += roll_input * self.roll_speed * dt

        forward_input = (1 if keys['w'] else 0) - (1 if keys['s'] else 0)
        strafe_input = (1 if keys['d'] else 0) - (1 if keys['a'] else 0)
        vertical_input = (1 if keys['space'] else 0) - (1 if (keys['shift'] or keys['control']) else 0)

        # Use entity's built-in direction vectors for proper 6DOF
        ship_forward = self.forward
        ship_right = self.right
        ship_up = self.up

        accel = Vec3(0, 0, 0)
        if forward_input != 0:
            accel += ship_forward * forward_input * self.acceleration
        if strafe_input != 0:
            accel += ship_right * strafe_input * self.acceleration * self.strafe_multiplier
        if vertical_input != 0:
            accel += ship_up * vertical_input * self.acceleration * self.vertical_multiplier

        if accel.length() > 0:
            self.velocity += accel * dt
        else:
            drag = self.deceleration * dt
            if self.velocity.length() > drag:
                self.velocity -= self.velocity.normalized() * drag
            else:
                self.velocity = Vec3(0, 0, 0)

        if self.velocity.length() > self.max_speed:
            self.velocity = self.velocity.normalized() * self.max_speed

        self.position += self.velocity * dt

        # Bounce off arena bounds
        if self.arena_bounds:
            margin = 2
            hx, hy, hz = self.arena_bounds

            if abs(self.x) > hx - margin:
                self.x = clamp(self.x, -hx + margin, hx - margin)
                self.velocity.x *= -0.5

            if abs(self.y) > hy - margin:
                self.y = clamp(self.y, -hy + margin, hy - margin)
                self.velocity.y *= -0.5

            if abs(self.z) > hz - margin:
                self.z = clamp(self.z, -hz + margin, hz - margin)
                self.velocity.z *= -0.5

        camera.position = self.position
        camera.rotation_x = self.rotation_x
        camera.rotation_y = self.rotation_y
        camera.rotation_z = self.rotation_z

    def _interpolate_to_target(self):
        """Smoothly interpolate to target state for remote players."""
        dt = time.dt
        lerp_factor = min(1.0, self.interpolation_speed * dt)

        # Position interpolation with velocity prediction
        predicted_pos = self.target_position + self.target_velocity * dt * 2
        self.position = lerp(self.position, predicted_pos, lerp_factor)

        # Velocity interpolation
        self.velocity = lerp(self.velocity, self.target_velocity, lerp_factor)

        # Rotation interpolation
        self.rotation_x = lerp(self.rotation_x, self.target_rotation[0], lerp_factor)
        self.rotation_y = lerp(self.rotation_y, self.target_rotation[1], lerp_factor)
        self.rotation_z = lerp(self.rotation_z, self.target_rotation[2], lerp_factor)

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
        return self.is_alive and (time.time() - self.last_primary_time) >= self.primary_cooldown

    def can_shoot_secondary(self):
        return self.is_alive and (time.time() - self.last_secondary_time) >= self.secondary_cooldown

    def shoot_primary(self):
        self.last_primary_time = time.time()
        return {
            'position': (self.position.x, self.position.y, self.position.z),
            'direction': (self.forward.x, self.forward.y, self.forward.z),
            'owner_id': self.player_id,
            'weapon': 'primary'
        }

    def shoot_secondary(self):
        self.last_secondary_time = time.time()
        return {
            'position': (self.position.x, self.position.y, self.position.z),
            'direction': (self.forward.x, self.forward.y, self.forward.z),
            'owner_id': self.player_id,
            'weapon': 'secondary'
        }

    def take_damage(self, amount, attacker_id=None):
        if not self.is_alive:
            return False

        self.health -= amount

        # Flash red on hit
        for part in self.ship_parts:
            if part.visible:
                original_color = part.color
                part.color = color.red
                invoke(setattr, part, 'color', original_color, delay=0.1)

        if self.health <= 0:
            self.die(attacker_id)
            return True
        return False

    def die(self, killer_id=None):
        self.is_alive = False
        self.deaths += 1
        self.velocity = Vec3(0, 0, 0)

        for part in self.ship_parts:
            part.visible = False

        if self.is_local:
            mouse.locked = False
            mouse.visible = True

    def respawn(self, position=None):
        self.health = self.max_health
        self.is_alive = True
        self.velocity = Vec3(0, 0, 0)

        if not self.is_local:
            self._show_ship()

        if position:
            self.position = Vec3(position[0], position[1], position[2])
        else:
            self.position = Vec3(
                random.uniform(-30, 30),
                random.uniform(-15, 15),
                random.uniform(-30, 30)
            )

        self.rotation = Vec3(0, 0, 0)

        if self.is_local:
            mouse.locked = True
            mouse.visible = False

    def add_kill(self):
        self.kills += 1

    def get_speed(self):
        return self.velocity.length()
