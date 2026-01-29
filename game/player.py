"""Player ship class with 6DOF controls and momentum-based physics."""
from ursina import *
import random
import math


class Player(Entity):
    """6DOF player ship with physics-based movement. StarCraft Wraith-inspired design."""

    def __init__(self, player_id=0, is_local=True, arena_bounds=None, collidables=None, **kwargs):
        super().__init__(**kwargs)

        self.player_id = player_id
        self.is_local = is_local
        self.arena_bounds = arena_bounds
        self.collidables = collidables if collidables else []
        self.collision_radius = 2.0  # Player collision radius

        # Physics settings
        self.velocity = Vec3(0, 0, 0)
        self.max_speed = 50
        self.acceleration = 45
        self.deceleration = 5
        self.strafe_multiplier = 0.9
        self.vertical_multiplier = 0.85

        # Atmosphere/air drag - ship stops when not thrusting
        # 0 = space (no drag), 1 = heavy atmosphere, 0.3 = light atmosphere
        self.atmosphere_drag = 0.3  # Default: light planetary atmosphere

        # Rotation settings
        self.roll_speed = 120
        self.mouse_sensitivity = 40

        # Combat - Primary weapon (rapid fire) - 2x faster
        self.max_health = 100
        self.health = self.max_health
        self.is_alive = True
        self.respawn_time = 3.0
        self.primary_cooldown = 0.06  # 2x faster (was 0.12)
        self.last_primary_time = 0
        self.primary_side = 1  # Alternates between -1 (left) and 1 (right)

        # Combat - Secondary weapon (slow powerful shot) - 2x faster
        self.secondary_cooldown = 0.975  # 2x faster (was 1.95)
        self.last_secondary_time = 0
        self.secondary_side = 1

        # Combat - Spreadshot weapon (3 projectiles) - 2x faster
        self.spreadshot_cooldown = 0.2  # 2x faster (was 0.4)
        self.last_spreadshot_time = 0

        # Stats
        self.kills = 0
        self.deaths = 0

        # Power-up effects
        self.shield = 0
        self.speed_multiplier = 1.0
        self.damage_multiplier = 1.0
        self.speed_boost_end = 0
        self.damage_boost_end = 0

        # Screen shake
        self.shake_intensity = 0
        self.shake_decay = 10  # How fast shake fades
        self.shake_offset = Vec3(0, 0, 0)

        # Thruster effects
        self.thruster_particles = []
        self.thruster_emit_timer = 0
        self.thruster_emit_rate = 40  # particles per second
        self.is_thrusting = False

        # Track key states locally
        self.keys_held = {
            'w': False, 's': False, 'a': False, 'd': False,
            'q': False, 'e': False,
            'space': False, 'shift': False, 'control': False,
            'left mouse': False, 'right mouse': False, 'middle mouse': False,
            '3': False  # Alternative spreadshot key
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
            camera.rotation_x = 0
            camera.rotation_y = 0
            camera.rotation_z = 0
            camera.fov = 90
            camera.clip_plane_near = 0.1
            camera.clip_plane_far = 500
            self._hide_local_ship()

    def _create_ship_model(self):
        """Create a StarCraft Wraith-inspired ship model."""
        # Color scheme
        if self.is_local:
            main_color = Color(70/255, 85/255, 100/255, 1)  # Blue-gray (Terran)
            accent_color = Color(50/255, 120/255, 180/255, 1)  # Blue accent
            engine_color = Color(80/255, 150/255, 255/255, 1)  # Blue engine glow
        else:
            main_color = Color(120/255, 60/255, 60/255, 1)  # Red-brown (enemy)
            accent_color = Color(180/255, 80/255, 50/255, 1)  # Orange accent
            engine_color = Color(255/255, 120/255, 50/255, 1)  # Orange engine glow

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
            color=Color(40/255, 60/255, 80/255, 1) if self.is_local else Color(80/255, 50/255, 40/255, 1),
            scale=(0.8, 0.5, 1.2),
            position=(0, 0.2, 1.8),
            rotation=(15, 0, 0),
        )

        # Cockpit glass
        self.cockpit_glass = Entity(
            parent=self,
            model='cube',
            color=Color(100/255, 180/255, 220/255, 1) if self.is_local else Color(200/255, 150/255, 100/255, 1),
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
            color=Color(50/255, 55/255, 65/255, 1),
            scale=(0.6, 0.5, 1.8),
            position=(-1.0, -0.2, -1.2),
        )

        # Right engine nacelle
        self.right_engine = Entity(
            parent=self,
            model='cube',
            color=Color(50/255, 55/255, 65/255, 1),
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
            # Transform mouse input based on roll angle for intuitive controls
            roll_rad = math.radians(self.rotation_z)
            cos_roll = math.cos(roll_rad)
            sin_roll = math.sin(roll_rad)
            # Rotate the mouse delta by the inverse of the roll
            adjusted_x = mv[0] * cos_roll + mv[1] * sin_roll
            adjusted_y = -mv[0] * sin_roll + mv[1] * cos_roll
            self.rotation_y += adjusted_x * self.mouse_sensitivity
            self.rotation_x -= adjusted_y * self.mouse_sensitivity
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
            self.is_thrusting = True

            # Emit thruster particles when moving
            self.thruster_emit_timer += dt
            if self.thruster_emit_timer > 1 / self.thruster_emit_rate:
                self.thruster_emit_timer = 0
                self._emit_thruster_particle(accel.normalized())
        else:
            self.is_thrusting = False

        # Apply atmosphere drag (always active - simulates air resistance)
        # Higher drag = ship stops faster when not thrusting
        if self.atmosphere_drag > 0 and self.velocity.length() > 0.1:
            drag_force = self.atmosphere_drag * 10  # Scale for noticeable effect
            drag_amount = drag_force * dt
            if self.velocity.length() > drag_amount:
                self.velocity -= self.velocity.normalized() * drag_amount
            else:
                self.velocity = Vec3(0, 0, 0)

        # Update thruster particles
        self._update_thruster_particles()

        # Apply speed multiplier from power-ups
        effective_max_speed = self.max_speed * self.speed_multiplier

        if self.velocity.length() > effective_max_speed:
            self.velocity = self.velocity.normalized() * effective_max_speed

        # Store old position for collision resolution
        old_position = Vec3(self.position)
        self.position += self.velocity * dt

        # Check collision with obstacles
        self._check_obstacle_collision(old_position)

        # Update power-up timers
        self.update_powerups()

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

        # Update screen shake
        if self.shake_intensity > 0.01:
            # Generate random shake offset
            self.shake_offset = Vec3(
                random.uniform(-1, 1) * self.shake_intensity,
                random.uniform(-1, 1) * self.shake_intensity,
                random.uniform(-1, 1) * self.shake_intensity * 0.5
            )
            # Decay shake over time
            self.shake_intensity *= (1 - self.shake_decay * time.dt)
        else:
            self.shake_offset = Vec3(0, 0, 0)
            self.shake_intensity = 0

        camera.position = self.position + self.shake_offset
        camera.rotation_x = self.rotation_x + self.shake_offset.y * 2
        camera.rotation_y = self.rotation_y + self.shake_offset.x * 2
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
        # Fire from alternating wing weapon pods
        weapon_offset = self.right * (3.2 * self.primary_side) + self.forward * 2.0
        spawn_pos = self.position + weapon_offset
        self.primary_side *= -1  # Alternate sides
        return {
            'position': (spawn_pos.x, spawn_pos.y, spawn_pos.z),
            'direction': (self.forward.x, self.forward.y, self.forward.z),
            'owner_id': self.player_id,
            'weapon': 'primary'
        }

    def shoot_secondary(self):
        self.last_secondary_time = time.time()
        # Fire from alternating wing weapon pods
        weapon_offset = self.right * (3.2 * self.secondary_side) + self.forward * 2.0
        spawn_pos = self.position + weapon_offset
        self.secondary_side *= -1  # Alternate sides
        return {
            'position': (spawn_pos.x, spawn_pos.y, spawn_pos.z),
            'direction': (self.forward.x, self.forward.y, self.forward.z),
            'owner_id': self.player_id,
            'weapon': 'secondary'
        }

    def can_shoot_spreadshot(self):
        return self.is_alive and (time.time() - self.last_spreadshot_time) >= self.spreadshot_cooldown

    def shoot_spreadshot(self):
        """Fire spreadshot - returns 3 projectile directions from both weapon pods."""
        self.last_spreadshot_time = time.time()

        # Get forward and right vectors
        fwd = self.forward
        right = self.right

        # Calculate spread angle (15 degrees)
        spread_angle = 0.26  # ~15 degrees in radians

        # Center shot
        dir_center = (fwd.x, fwd.y, fwd.z)

        # Left shot (rotated around up axis)
        cos_a = math.cos(spread_angle)
        sin_a = math.sin(spread_angle)
        dir_left = (
            fwd.x * cos_a - right.x * sin_a,
            fwd.y,
            fwd.z * cos_a - right.z * sin_a
        )

        # Right shot
        dir_right = (
            fwd.x * cos_a + right.x * sin_a,
            fwd.y,
            fwd.z * cos_a + right.z * sin_a
        )

        # Fire from both weapon pods
        left_pod = self.position + right * -3.2 + fwd * 2.0
        right_pod = self.position + right * 3.2 + fwd * 2.0

        return {
            'positions': [(left_pod.x, left_pod.y, left_pod.z), (right_pod.x, right_pod.y, right_pod.z)],
            'directions': [dir_center, dir_left, dir_right],
            'owner_id': self.player_id,
            'weapon': 'spreadshot'
        }

    def take_damage(self, amount, attacker_id=None):
        if not self.is_alive:
            return False

        # Shield absorbs damage first
        if self.shield > 0:
            shield_absorbed = min(self.shield, amount)
            self.shield -= shield_absorbed
            amount -= shield_absorbed

            # Flash purple for shield hit
            for part in self.ship_parts:
                if part.visible:
                    original_color = part.color
                    part.color = Color(200/255, 50/255, 255/255, 1)
                    invoke(setattr, part, 'color', original_color, delay=0.1)

            if amount <= 0:
                return False

        self.health -= amount

        # Flash red on health damage
        for part in self.ship_parts:
            if part.visible:
                original_color = part.color
                part.color = color.red
                invoke(setattr, part, 'color', original_color, delay=0.1)

        # Trigger screen shake based on damage amount
        shake_amount = min(amount / 10, 3)  # Cap at 3 intensity
        self.trigger_screen_shake(shake_amount)

        if self.health <= 0:
            self.die(attacker_id)
            return True
        return False

    def apply_speed_boost(self, multiplier, duration):
        """Apply a temporary speed boost."""
        self.speed_multiplier = multiplier
        self.speed_boost_end = time.time() + duration

    def apply_damage_boost(self, multiplier, duration):
        """Apply a temporary damage boost."""
        self.damage_multiplier = multiplier
        self.damage_boost_end = time.time() + duration

    def apply_shield(self, amount):
        """Add shield points."""
        self.shield = min(100, self.shield + amount)

    def trigger_screen_shake(self, intensity):
        """Trigger screen shake effect."""
        if self.is_local:
            self.shake_intensity = max(self.shake_intensity, intensity)

    def _emit_thruster_particle(self, thrust_direction):
        """Emit a thruster particle from the back of the ship."""
        # Calculate spawn position at back of ship
        spawn_pos = self.world_position - self.forward * 1.5

        # Velocity is opposite of ship forward
        base_vel = -self.forward * 15

        # Add some randomness
        vel = base_vel + Vec3(
            random.uniform(-2, 2),
            random.uniform(-2, 2),
            random.uniform(-2, 2)
        )

        # Create particle
        particle = Entity(
            model='quad',
            position=spawn_pos,
            scale=random.uniform(0.2, 0.4),
            color=Color(100/255, 150/255, 255/255, 1),  # Blue-white
            billboard=True,
        )

        # Store particle data
        self.thruster_particles.append({
            'entity': particle,
            'velocity': vel,
            'lifetime': random.uniform(0.1, 0.2),
            'max_lifetime': 0.2,
        })

    def _update_thruster_particles(self):
        """Update all thruster particles."""
        dt = time.dt
        particles_to_remove = []

        for p in self.thruster_particles:
            # Move particle
            p['entity'].position += p['velocity'] * dt

            # Reduce lifetime
            p['lifetime'] -= dt

            # Fade out
            progress = 1 - (p['lifetime'] / p['max_lifetime'])
            alpha = 1 - progress
            p['entity'].color = color.rgba(100, 150, 255, alpha * 255)
            p['entity'].scale = (1 - progress * 0.5) * 0.3

            # Check if expired
            if p['lifetime'] <= 0:
                particles_to_remove.append(p)
                destroy(p['entity'])

        # Remove dead particles
        for p in particles_to_remove:
            self.thruster_particles.remove(p)

        # Limit max particles
        while len(self.thruster_particles) > 50:
            old = self.thruster_particles.pop(0)
            destroy(old['entity'])

    def _check_obstacle_collision(self, old_position):
        """Check and resolve collision with obstacles."""
        if not self.collidables:
            return

        player_radius = self.collision_radius

        for obstacle in self.collidables:
            if not obstacle.enabled:
                continue

            # Get obstacle bounds (AABB)
            obs_pos = obstacle.world_position
            obs_scale = obstacle.scale

            # Half extents
            hx = obs_scale.x / 2
            hy = obs_scale.y / 2
            hz = obs_scale.z / 2

            # Find closest point on AABB to player
            closest_x = clamp(self.x, obs_pos.x - hx, obs_pos.x + hx)
            closest_y = clamp(self.y, obs_pos.y - hy, obs_pos.y + hy)
            closest_z = clamp(self.z, obs_pos.z - hz, obs_pos.z + hz)

            # Calculate distance from player to closest point
            dx = self.x - closest_x
            dy = self.y - closest_y
            dz = self.z - closest_z
            dist_sq = dx * dx + dy * dy + dz * dz

            # Check collision
            if dist_sq < player_radius * player_radius:
                # Collision detected - push player out
                if dist_sq > 0.001:
                    dist = math.sqrt(dist_sq)
                    # Normal from obstacle to player
                    nx = dx / dist
                    ny = dy / dist
                    nz = dz / dist
                    # Push player out
                    penetration = player_radius - dist
                    self.x += nx * penetration
                    self.y += ny * penetration
                    self.z += nz * penetration
                    # Reflect velocity
                    normal = Vec3(nx, ny, nz)
                    dot = self.velocity.dot(normal)
                    if dot < 0:
                        self.velocity -= normal * dot * 1.5  # Bounce factor
                else:
                    # Player is exactly at closest point, use old position to determine push direction
                    self.position = old_position
                    self.velocity *= -0.5

    def update_powerups(self):
        """Update power-up timers."""
        current_time = time.time()
        if self.speed_boost_end > 0 and current_time >= self.speed_boost_end:
            self.speed_multiplier = 1.0
            self.speed_boost_end = 0
        if self.damage_boost_end > 0 and current_time >= self.damage_boost_end:
            self.damage_multiplier = 1.0
            self.damage_boost_end = 0

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

        # Reset power-ups
        self.shield = 0
        self.speed_multiplier = 1.0
        self.damage_multiplier = 1.0
        self.speed_boost_end = 0
        self.damage_boost_end = 0

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
