"""Power-up system for collectible bonuses."""
from ursina import *
import random
import math


class PowerUp(Entity):
    """Base class for collectible power-ups."""

    TYPES = {
        'health': {
            'color': color.rgb(50, 255, 50),     # Green
            'effect_color': color.rgb(100, 255, 100),
            'duration': 0,  # Instant
            'respawn_time': 15,
            'description': '+25 Health',
        },
        'speed': {
            'color': color.rgb(50, 150, 255),   # Blue
            'effect_color': color.rgb(100, 200, 255),
            'duration': 10,
            'respawn_time': 20,
            'description': '1.5x Speed',
        },
        'damage': {
            'color': color.rgb(255, 100, 50),   # Orange
            'effect_color': color.rgb(255, 150, 100),
            'duration': 10,
            'respawn_time': 25,
            'description': '2x Damage',
        },
        'shield': {
            'color': color.rgb(200, 50, 255),   # Purple
            'effect_color': color.rgb(230, 100, 255),
            'duration': 0,  # Until depleted
            'respawn_time': 30,
            'description': '+50 Shield',
        },
    }

    def __init__(self, powerup_type, position, powerup_id=0):
        type_data = self.TYPES.get(powerup_type, self.TYPES['health'])

        super().__init__(
            model='cube',
            color=type_data['color'],
            scale=1.5,
            position=position,
            collider='box',
        )

        self.powerup_type = powerup_type
        self.powerup_id = powerup_id
        self.type_data = type_data
        self.active = True
        self.bob_offset = random.random() * math.pi * 2
        self.spawn_position = Vec3(position)

        # Create inner glow
        self.glow = Entity(
            parent=self,
            model='cube',
            color=type_data['effect_color'],
            scale=0.7,
        )

        # Create rotating ring
        self.ring = Entity(
            parent=self,
            model='cube',
            color=type_data['color'],
            scale=(2, 0.1, 2),
        )

    def update(self):
        """Animate the power-up."""
        if not self.active:
            return

        # Rotate
        self.rotation_y += 60 * time.dt
        self.rotation_x += 30 * time.dt

        # Bob up and down
        bob = math.sin(time.time() * 2 + self.bob_offset) * 0.3
        self.y = self.spawn_position.y + bob

        # Pulse glow
        pulse = (math.sin(time.time() * 4) + 1) / 2
        self.glow.scale = 0.5 + pulse * 0.3

    def collect(self, player):
        """Apply power-up effect to player."""
        if not self.active:
            return None

        self.active = False
        effect = self._apply_effect(player)
        destroy(self)
        return effect

    def _apply_effect(self, player):
        """Apply the specific power-up effect."""
        if self.powerup_type == 'health':
            old_health = player.health
            player.health = min(100, player.health + 25)
            return {'type': 'health', 'amount': player.health - old_health}

        elif self.powerup_type == 'speed':
            player.apply_speed_boost(1.5, self.type_data['duration'])
            return {'type': 'speed', 'multiplier': 1.5, 'duration': self.type_data['duration']}

        elif self.powerup_type == 'damage':
            player.apply_damage_boost(2.0, self.type_data['duration'])
            return {'type': 'damage', 'multiplier': 2.0, 'duration': self.type_data['duration']}

        elif self.powerup_type == 'shield':
            player.apply_shield(50)
            return {'type': 'shield', 'amount': 50}

        return None


class PowerUpSpawner:
    """Manages power-up spawning and respawning."""

    def __init__(self, arena_bounds):
        self.arena_bounds = arena_bounds
        self.powerups = {}  # id -> PowerUp
        self.respawn_queue = []  # (respawn_time, type, position, id)
        self.next_id = 0

        # Spawn initial power-ups
        self._create_spawn_points()
        self._spawn_initial_powerups()

    def _create_spawn_points(self):
        """Create spawn point locations throughout the arena."""
        hx, hy, hz = self.arena_bounds

        # Spawn points at strategic locations
        self.spawn_points = [
            # Corners
            Vec3(-hx + 20, 0, -hz + 20),
            Vec3(hx - 20, 0, -hz + 20),
            Vec3(-hx + 20, 0, hz - 20),
            Vec3(hx - 20, 0, hz - 20),

            # Center areas at different heights
            Vec3(0, -hy + 10, 0),
            Vec3(0, 0, 0),
            Vec3(0, hy - 10, 0),

            # Mid-points
            Vec3(-hx + 30, 10, 0),
            Vec3(hx - 30, 10, 0),
            Vec3(0, 10, -hz + 30),
            Vec3(0, 10, hz - 30),

            # Platform areas
            Vec3(40, 15, 40),
            Vec3(-40, 15, -40),
            Vec3(40, -15, -40),
            Vec3(-40, -15, 40),
        ]

    def _spawn_initial_powerups(self):
        """Spawn initial set of power-ups."""
        types = ['health', 'health', 'speed', 'damage', 'shield']
        random.shuffle(self.spawn_points)

        for i, ptype in enumerate(types):
            if i < len(self.spawn_points):
                self._spawn_powerup(ptype, self.spawn_points[i])

    def _spawn_powerup(self, powerup_type, position):
        """Spawn a power-up at the given position."""
        powerup_id = self.next_id
        self.next_id += 1

        powerup = PowerUp(powerup_type, position, powerup_id)
        self.powerups[powerup_id] = powerup

        return powerup

    def update(self):
        """Update respawn timers."""
        current_time = time.time()

        # Check respawn queue
        new_queue = []
        for respawn_time, ptype, pos, pid in self.respawn_queue:
            if current_time >= respawn_time:
                # Respawn the power-up
                self._spawn_powerup(ptype, pos)
            else:
                new_queue.append((respawn_time, ptype, pos, pid))

        self.respawn_queue = new_queue

    def check_collection(self, player):
        """Check if player collected any power-ups."""
        collected = []
        player_pos = player.position
        collection_radius = 3.0

        for powerup_id, powerup in list(self.powerups.items()):
            if not powerup.active:
                continue

            distance = (powerup.position - player_pos).length()
            if distance < collection_radius:
                effect = powerup.collect(player)
                if effect:
                    collected.append(effect)

                    # Queue respawn
                    respawn_time = time.time() + powerup.type_data['respawn_time']
                    self.respawn_queue.append((
                        respawn_time,
                        powerup.powerup_type,
                        powerup.spawn_position,
                        powerup_id
                    ))

                # Remove from active powerups
                if powerup_id in self.powerups:
                    del self.powerups[powerup_id]

        return collected

    def get_state(self):
        """Get state for network sync."""
        return {
            pid: {
                'type': p.powerup_type,
                'position': (p.position.x, p.position.y, p.position.z),
                'active': p.active
            }
            for pid, p in self.powerups.items()
        }

    def cleanup(self):
        """Destroy all power-ups."""
        for powerup in self.powerups.values():
            destroy(powerup)
        self.powerups.clear()
        self.respawn_queue.clear()


class PowerUpEffect:
    """Visual effect indicator for active power-ups."""

    def __init__(self, player, effect_type, duration=0):
        self.player = player
        self.effect_type = effect_type
        self.duration = duration
        self.start_time = time.time()
        self.active = True

        # Visual indicator based on type
        type_data = PowerUp.TYPES.get(effect_type, {})
        effect_color = type_data.get('effect_color', color.white)

        # Create visual effect around player
        self.effect_entity = Entity(
            parent=player,
            model='sphere',
            color=color.rgba(effect_color.r, effect_color.g, effect_color.b, 0.3),
            scale=2.5,
        )

    def update(self):
        """Update the effect."""
        if self.duration > 0:
            elapsed = time.time() - self.start_time
            if elapsed >= self.duration:
                self.active = False
                destroy(self.effect_entity)
                return False

            # Pulse effect
            pulse = (math.sin(time.time() * 4) + 1) / 2
            self.effect_entity.scale = 2 + pulse * 0.5

        return True

    def remove(self):
        """Remove the effect."""
        self.active = False
        if self.effect_entity:
            destroy(self.effect_entity)
