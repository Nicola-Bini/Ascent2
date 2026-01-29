"""Projectile/bullet handling."""
from ursina import *


class Projectile(Entity):
    """Fast-moving projectile with collision detection."""

    def __init__(self, position, direction, owner_id, projectile_id=0, speed=50, damage=25, lifetime=3.0, **kwargs):
        super().__init__(
            model='sphere',
            color=color.yellow,
            scale=0.2,
            position=position,
            collider='sphere',
            **kwargs
        )

        self.projectile_id = projectile_id
        self.owner_id = owner_id
        self.direction = Vec3(direction[0], direction[1], direction[2]).normalized()
        self.speed = speed
        self.damage = damage
        self.lifetime = lifetime
        self.spawn_time = time.time()
        self.active = True

        # Visual trail effect
        self.trail = Entity(
            parent=self,
            model='cube',
            color=color.orange,
            scale=(0.1, 0.1, 0.5),
            position=(0, 0, -0.3)
        )

    def update(self):
        """Move projectile and check lifetime."""
        if not self.active:
            return

        # Move forward
        self.position += self.direction * self.speed * time.dt

        # Check lifetime
        if time.time() - self.spawn_time > self.lifetime:
            self.despawn()

    def despawn(self):
        """Remove the projectile."""
        self.active = False
        destroy(self)

    def get_state(self):
        """Get state for network sync."""
        return {
            'projectile_id': self.projectile_id,
            'owner_id': self.owner_id,
            'position': (self.position.x, self.position.y, self.position.z),
            'direction': (self.direction.x, self.direction.y, self.direction.z)
        }


class ProjectileManager:
    """Manages all projectiles in the game."""

    def __init__(self):
        self.projectiles = {}
        self.next_id = 0

    def spawn(self, position, direction, owner_id, projectile_id=None):
        """Create a new projectile."""
        if projectile_id is None:
            projectile_id = self.next_id
            self.next_id += 1

        proj = Projectile(
            position=position,
            direction=direction,
            owner_id=owner_id,
            projectile_id=projectile_id
        )
        self.projectiles[projectile_id] = proj
        return proj

    def remove(self, projectile_id):
        """Remove a projectile by ID."""
        if projectile_id in self.projectiles:
            proj = self.projectiles[projectile_id]
            if proj.active:
                proj.despawn()
            del self.projectiles[projectile_id]

    def check_collisions(self, players, arena_bounds):
        """Check projectile collisions with players and arena."""
        hits = []
        to_remove = []

        for proj_id, proj in list(self.projectiles.items()):
            if not proj.active:
                to_remove.append(proj_id)
                continue

            # Check arena bounds
            pos = proj.position
            if (abs(pos.x) > arena_bounds[0] or
                abs(pos.y) > arena_bounds[1] or
                abs(pos.z) > arena_bounds[2]):
                to_remove.append(proj_id)
                continue

            # Check player collisions
            for player in players.values():
                if player.player_id == proj.owner_id:
                    continue  # Can't hit yourself
                if not player.is_alive:
                    continue

                # Simple distance-based collision
                dist = (player.position - proj.position).length()
                if dist < 1.5:  # Hit radius
                    hits.append({
                        'projectile_id': proj_id,
                        'target_id': player.player_id,
                        'attacker_id': proj.owner_id,
                        'damage': proj.damage
                    })
                    to_remove.append(proj_id)
                    break

        # Clean up
        for proj_id in to_remove:
            self.remove(proj_id)

        return hits

    def clear(self):
        """Remove all projectiles."""
        for proj in list(self.projectiles.values()):
            if proj.active:
                proj.despawn()
        self.projectiles.clear()
