"""Particle effects system for visual enhancements."""
from ursina import *
import random


class Particle(Entity):
    """A single particle with physics and lifetime."""

    def __init__(self, position, velocity, lifetime, size, color_start, color_end=None, **kwargs):
        super().__init__(
            model='quad',
            position=position,
            scale=size,
            color=color_start,
            billboard=True,  # Always face camera
            **kwargs
        )
        self.velocity = Vec3(velocity) if not isinstance(velocity, Vec3) else velocity
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color_start = color_start
        self.color_end = color_end if color_end else color_start
        self.start_scale = size

    def update(self):
        # Move particle
        self.position += self.velocity * time.dt

        # Apply drag
        self.velocity *= 0.98

        # Reduce lifetime
        self.lifetime -= time.dt

        # Interpolate color and scale based on lifetime
        progress = 1 - (self.lifetime / self.max_lifetime)

        # Fade out
        alpha = 1 - progress
        self.color = color.rgba(
            lerp(self.color_start.r, self.color_end.r, progress),
            lerp(self.color_start.g, self.color_end.g, progress),
            lerp(self.color_start.b, self.color_end.b, progress),
            alpha
        )

        # Shrink
        self.scale = self.start_scale * (1 - progress * 0.5)

        # Destroy when lifetime expires
        if self.lifetime <= 0:
            destroy(self)


class ParticleEmitter:
    """Emits particles with configurable properties."""

    def __init__(self):
        self.particles = []

    def emit(self, position, count=10, velocity_range=5, lifetime=0.5,
             size=0.3, color_start=color.white, color_end=None, spread=1.0):
        """Emit particles at a position."""
        for _ in range(count):
            # Random velocity direction
            vel = Vec3(
                random.uniform(-1, 1),
                random.uniform(-1, 1),
                random.uniform(-1, 1)
            ).normalized() * random.uniform(0.5, 1) * velocity_range

            # Add some spread variance
            vel += Vec3(
                random.uniform(-spread, spread),
                random.uniform(-spread, spread),
                random.uniform(-spread, spread)
            )

            # Random size variance
            actual_size = size * random.uniform(0.7, 1.3)

            # Random lifetime variance
            actual_lifetime = lifetime * random.uniform(0.8, 1.2)

            p = Particle(
                position=position,
                velocity=vel,
                lifetime=actual_lifetime,
                size=actual_size,
                color_start=color_start,
                color_end=color_end
            )
            self.particles.append(p)

    def emit_directional(self, position, direction, count=5, speed=10,
                         cone_angle=30, lifetime=0.3, size=0.2,
                         color_start=color.white, color_end=None):
        """Emit particles in a specific direction with cone spread."""
        for _ in range(count):
            # Start with the main direction
            vel = Vec3(direction).normalized()

            # Add random cone spread
            angle_rad = math.radians(random.uniform(0, cone_angle))
            rotation_angle = random.uniform(0, 360)

            # Create perpendicular vectors for cone spread
            if abs(vel.y) < 0.9:
                perp = vel.cross(Vec3(0, 1, 0)).normalized()
            else:
                perp = vel.cross(Vec3(1, 0, 0)).normalized()

            perp2 = vel.cross(perp).normalized()

            # Apply cone spread
            spread = math.sin(angle_rad)
            vel = vel * math.cos(angle_rad)
            vel += perp * spread * math.cos(math.radians(rotation_angle))
            vel += perp2 * spread * math.sin(math.radians(rotation_angle))

            vel = vel.normalized() * speed * random.uniform(0.8, 1.2)

            actual_size = size * random.uniform(0.8, 1.2)
            actual_lifetime = lifetime * random.uniform(0.9, 1.1)

            p = Particle(
                position=position,
                velocity=vel,
                lifetime=actual_lifetime,
                size=actual_size,
                color_start=color_start,
                color_end=color_end
            )
            self.particles.append(p)

    def cleanup(self):
        """Remove dead particles from tracking list."""
        self.particles = [p for p in self.particles if p.lifetime > 0 and p.enabled]


class ThrusterEffect:
    """Thruster exhaust effect that follows a ship."""

    def __init__(self, parent_entity, offset=Vec3(0, 0, -1)):
        self.parent = parent_entity
        self.offset = offset
        self.emitter = ParticleEmitter()
        self.emit_rate = 30  # particles per second
        self.emit_timer = 0
        self.active = False

        # Thruster colors
        self.color_inner = Color(100/255, 150/255, 255/255, 1)  # Blue-white
        self.color_outer = Color(50/255, 80/255, 200/255, 1)    # Darker blue

    def update(self, is_thrusting, thrust_direction=None):
        """Update the thruster effect."""
        self.emit_timer += time.dt

        if is_thrusting and self.emit_timer > 1 / self.emit_rate:
            self.emit_timer = 0

            # Calculate world position of thruster
            world_pos = self.parent.world_position + self.parent.back * 1.5

            # Emit direction is opposite of ship forward
            emit_dir = -self.parent.forward

            self.emitter.emit_directional(
                position=world_pos,
                direction=emit_dir,
                count=2,
                speed=15,
                cone_angle=15,
                lifetime=0.15,
                size=0.3,
                color_start=self.color_inner,
                color_end=self.color_outer
            )

        # Cleanup old particles
        if random.random() < 0.1:
            self.emitter.cleanup()


class MuzzleFlash(Entity):
    """Quick flash effect when firing weapons."""

    def __init__(self, position, direction, weapon_type='primary'):
        if weapon_type == 'primary':
            flash_color = Color(100/255, 200/255, 255/255, 1)  # Cyan
            flash_size = 0.8
        else:
            flash_color = Color(255/255, 150/255, 50/255, 1)   # Orange
            flash_size = 1.2

        super().__init__(
            model='quad',
            position=position,
            scale=flash_size,
            color=flash_color,
            billboard=True,
        )

        self.lifetime = 0.05  # Very short flash

    def update(self):
        self.lifetime -= time.dt
        self.scale *= 0.8  # Shrink quickly
        if self.lifetime <= 0:
            destroy(self)


class ExplosionEffect:
    """Explosion particle effect."""

    def __init__(self, position, size='medium'):
        self.emitter = ParticleEmitter()

        # Size presets
        sizes = {
            'small': {'count': 15, 'radius': 2, 'lifetime': 0.3, 'particle_size': 0.4},
            'medium': {'count': 30, 'radius': 4, 'lifetime': 0.5, 'particle_size': 0.6},
            'large': {'count': 50, 'radius': 8, 'lifetime': 0.8, 'particle_size': 1.0},
        }
        preset = sizes.get(size, sizes['medium'])

        # Core explosion - bright orange/yellow
        self.emitter.emit(
            position=position,
            count=preset['count'],
            velocity_range=preset['radius'] * 3,
            lifetime=preset['lifetime'],
            size=preset['particle_size'],
            color_start=Color(255/255, 200/255, 50/255, 1),
            color_end=Color(255/255, 80/255, 20/255, 1),
            spread=2
        )

        # Outer sparks - orange/red
        self.emitter.emit(
            position=position,
            count=preset['count'] // 2,
            velocity_range=preset['radius'] * 5,
            lifetime=preset['lifetime'] * 1.5,
            size=preset['particle_size'] * 0.5,
            color_start=Color(255/255, 100/255, 30/255, 1),
            color_end=Color(100/255, 30/255, 10/255, 1),
            spread=3
        )

        # Smoke - dark gray
        self.emitter.emit(
            position=position,
            count=preset['count'] // 3,
            velocity_range=preset['radius'],
            lifetime=preset['lifetime'] * 2,
            size=preset['particle_size'] * 1.5,
            color_start=Color(80/255, 80/255, 80/255, 1),
            color_end=Color(40/255, 40/255, 40/255, 1),
            spread=1
        )


class ProjectileTrail:
    """Trail effect that follows a projectile."""

    def __init__(self, weapon_type='primary'):
        self.emitter = ParticleEmitter()
        self.weapon_type = weapon_type

        if weapon_type == 'primary':
            self.color_start = Color(80/255, 180/255, 255/255, 1)
            self.color_end = Color(40/255, 80/255, 150/255, 1)
            self.emit_rate = 60
            self.particle_size = 0.15
        else:
            self.color_start = Color(255/255, 120/255, 40/255, 1)
            self.color_end = Color(150/255, 50/255, 20/255, 1)
            self.emit_rate = 40
            self.particle_size = 0.25

        self.emit_timer = 0

    def update(self, position, velocity):
        """Add trail particles at the projectile position."""
        self.emit_timer += time.dt

        if self.emit_timer > 1 / self.emit_rate:
            self.emit_timer = 0

            # Emit in opposite direction of movement
            emit_dir = -Vec3(velocity).normalized() if velocity else Vec3(0, 0, -1)

            self.emitter.emit_directional(
                position=position,
                direction=emit_dir,
                count=1,
                speed=2,
                cone_angle=10,
                lifetime=0.1,
                size=self.particle_size,
                color_start=self.color_start,
                color_end=self.color_end
            )


# Global particle manager
class ParticleManager:
    """Manages all particle effects in the game."""

    def __init__(self):
        self.effects = []
        self.trails = {}  # projectile_id -> ProjectileTrail

    def create_muzzle_flash(self, position, direction, weapon_type='primary'):
        """Create a muzzle flash at the firing position."""
        flash = MuzzleFlash(position, direction, weapon_type)
        self.effects.append(flash)

    def create_explosion(self, position, size='medium'):
        """Create an explosion effect."""
        explosion = ExplosionEffect(position, size)
        self.effects.append(explosion)

    def create_thruster(self, parent_entity):
        """Create a thruster effect attached to an entity."""
        thruster = ThrusterEffect(parent_entity)
        return thruster

    def get_trail(self, projectile_id, weapon_type='primary'):
        """Get or create a trail for a projectile."""
        if projectile_id not in self.trails:
            self.trails[projectile_id] = ProjectileTrail(weapon_type)
        return self.trails[projectile_id]

    def remove_trail(self, projectile_id):
        """Remove a projectile trail."""
        if projectile_id in self.trails:
            del self.trails[projectile_id]

    def cleanup(self):
        """Cleanup dead effects."""
        self.effects = [e for e in self.effects if hasattr(e, 'enabled') and e.enabled]
