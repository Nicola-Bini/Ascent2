"""Projectile/bullet handling with primary and secondary weapons."""
from ursina import *
import random


class Projectile(Entity):
    """Fast-moving projectile with collision detection."""

    def __init__(self, position, direction, owner_id, projectile_id=0,
                 speed=60, damage=15, lifetime=3.0, weapon='primary', collidables=None, **kwargs):
        # Different visuals for each weapon type
        if weapon == 'secondary':
            proj_color = Color(255/255, 100/255, 50/255, 1)  # Orange-red
            proj_scale = (0.5, 0.5, 0.5)
            proj_model = 'sphere'
            trail_scale = (0.3, 0.3, 1.2)
        elif weapon == 'spreadshot':
            proj_color = Color(150/255, 200/255, 255/255, 1)  # Light blue
            proj_scale = (0.12, 0.12, 0.12)
            proj_model = 'sphere'
            trail_scale = (0.06, 0.06, 0.3)
        else:
            # Primary laser - long thick beam (3x bigger)
            proj_color = Color(100/255, 255/255, 150/255, 1)  # Bright green laser
            proj_scale = (1.05, 1.05, 9.0)  # 3x thicker and longer
            proj_model = 'cube'
            trail_scale = (0.75, 0.75, 4.5)

        super().__init__(
            model=proj_model,
            color=proj_color,
            scale=proj_scale,
            position=position,
            collider='box' if weapon == 'primary' else 'sphere',
            **kwargs
        )

        self.projectile_id = projectile_id
        self.owner_id = owner_id
        self.direction = Vec3(direction[0], direction[1], direction[2]).normalized()
        self.speed = speed
        self.damage = damage
        self.lifetime = lifetime
        self.weapon = weapon
        self.spawn_time = time.time()
        self.active = True
        self.collidables = collidables if collidables else []
        self.proj_radius = proj_scale[0] if isinstance(proj_scale, tuple) else proj_scale * 0.5
        self.hit_obstacle = False
        self.hit_position = None

        # Orient projectile to face direction of travel (for elongated shapes)
        if weapon == 'primary':
            self.look_at(self.position + self.direction)

        # Visual trail effect
        if weapon == 'secondary':
            trail_color = Color(255/255, 150/255, 50/255, 1)
        elif weapon == 'spreadshot':
            trail_color = Color(100/255, 150/255, 255/255, 1)
        else:
            trail_color = Color(150/255, 200/255, 80/255, 1)
        self.trail = Entity(
            parent=self,
            model='cube',
            color=trail_color,
            scale=trail_scale,
            position=(0, 0, -trail_scale[2] * 0.5)
        )

    def update(self):
        """Move projectile and check lifetime."""
        if not self.active:
            return

        self.position += self.direction * self.speed * time.dt

        # Check collision with obstacles - set flag but don't despawn (let manager handle it)
        if self._check_obstacle_collision():
            self.hit_obstacle = True
            self.hit_position = Vec3(self.position)
            return

        if time.time() - self.spawn_time > self.lifetime:
            self.despawn()

    def _check_obstacle_collision(self):
        """Check if projectile hit an obstacle."""
        if not self.collidables:
            return False

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

            # Find closest point on AABB to projectile
            closest_x = clamp(self.x, obs_pos.x - hx, obs_pos.x + hx)
            closest_y = clamp(self.y, obs_pos.y - hy, obs_pos.y + hy)
            closest_z = clamp(self.z, obs_pos.z - hz, obs_pos.z + hz)

            # Calculate distance from projectile to closest point
            dx = self.x - closest_x
            dy = self.y - closest_y
            dz = self.z - closest_z
            dist_sq = dx * dx + dy * dy + dz * dz

            # Check collision (using projectile radius)
            if dist_sq < self.proj_radius * self.proj_radius:
                return True

        return False

    def despawn(self, create_explosion=False, hit_obstacle=False):
        """Remove the projectile, optionally with explosion."""
        if not self.active:
            return
        self.active = False
        self.hit_obstacle = hit_obstacle  # Flag for external code to check
        destroy(self)

    def get_state(self):
        """Get state for network sync."""
        return {
            'projectile_id': self.projectile_id,
            'owner_id': self.owner_id,
            'position': (self.position.x, self.position.y, self.position.z),
            'direction': (self.direction.x, self.direction.y, self.direction.z),
            'weapon': self.weapon
        }


class Explosion(Entity):
    """Visual explosion effect."""

    def __init__(self, position, size=3.0, duration=0.5, **kwargs):
        super().__init__(
            model='sphere',
            color=Color(255/255, 200/255, 50/255, 1),
            scale=0.1,
            position=position,
            **kwargs
        )

        self.max_size = size
        self.duration = duration
        self.spawn_time = time.time()
        self.active = True

        # Inner bright core
        self.core = Entity(
            parent=self,
            model='sphere',
            color=Color(255/255, 255/255, 200/255, 1),
            scale=0.6
        )

        # Start expansion animation
        self.animate_scale(size, duration=duration * 0.3, curve=curve.out_expo)
        self.animate_color(Color(255/255, 100/255, 30/255, 1), duration=duration * 0.5)

        # Schedule fadeout
        invoke(self._fade_out, delay=duration * 0.3)

    def _fade_out(self):
        """Fade out and destroy."""
        self.animate_color(Color(255/255, 50/255, 20/255, 0), duration=self.duration * 0.7)
        self.animate_scale(self.max_size * 1.5, duration=self.duration * 0.7)
        invoke(self._destroy, delay=self.duration * 0.7)

    def _destroy(self):
        """Clean up."""
        self.active = False
        destroy(self)


class ProjectileManager:
    """Manages all projectiles in the game."""

    def __init__(self, collidables=None):
        self.projectiles = {}
        self.explosions = []
        self.next_id = 0
        self.collidables = collidables if collidables else []

    def set_collidables(self, collidables):
        """Set the list of collidable obstacles."""
        self.collidables = collidables

    def spawn(self, position, direction, owner_id, projectile_id=None, weapon='primary'):
        """Create a new projectile."""
        if projectile_id is None:
            projectile_id = self.next_id
            self.next_id += 1

        # Different stats for each weapon type (speeds 3x faster)
        if weapon == 'secondary':
            speed = 120  # Slower missile (was 40)
            damage = 100  # Direct hit kills (100 = full health)
            lifetime = 4.0  # Longer range
        elif weapon == 'spreadshot':
            speed = 195  # Medium speed (was 65)
            damage = 8  # Less damage per projectile (but 3 projectiles)
            lifetime = 2.0  # Medium range
        else:
            speed = 700  # Ultra fast laser (2x faster)
            damage = 12  # Less damage
            lifetime = 1.5

        proj = Projectile(
            position=position,
            direction=direction,
            owner_id=owner_id,
            projectile_id=projectile_id,
            speed=speed,
            damage=damage,
            lifetime=lifetime,
            weapon=weapon,
            collidables=self.collidables
        )
        self.projectiles[projectile_id] = proj
        return proj

    def create_explosion(self, position, size=3.0):
        """Create an explosion effect at position."""
        exp = Explosion(position=position, size=size)
        self.explosions.append(exp)

        # Create particle-like debris
        for _ in range(8):
            debris = Entity(
                model='cube',
                color=Color(255/255, random.randint(100, 200)/255, 50/255, 1),
                scale=random.uniform(0.1, 0.3),
                position=position
            )
            # Random direction
            direction = Vec3(
                random.uniform(-1, 1),
                random.uniform(-1, 1),
                random.uniform(-1, 1)
            ).normalized()
            speed = random.uniform(5, 15)
            duration = random.uniform(0.3, 0.6)

            debris.animate_position(
                position + direction * speed,
                duration=duration,
                curve=curve.out_expo
            )
            debris.animate_scale(0, duration=duration)
            debris.animate_color(color.rgba(255, 100, 50, 0), duration=duration)
            invoke(lambda d=debris: destroy(d), delay=duration)

        return exp

    def remove(self, projectile_id):
        """Remove a projectile by ID."""
        if projectile_id in self.projectiles:
            proj = self.projectiles[projectile_id]
            if proj.active:
                proj.despawn()
            del self.projectiles[projectile_id]

    def check_collisions(self, players, local_player, arena_bounds):
        """Check projectile collisions with players and arena.

        Returns tuple: (player_hits, obstacle_hits)
        - player_hits: list of dicts with projectile_id, target_id, attacker_id, damage, weapon
        - obstacle_hits: list of dicts with position, weapon (for sound/effects)
        """
        hits = []
        obstacle_hits = []
        to_remove = []

        # Combine local player with remote players for collision checking
        all_players = dict(players)
        if local_player:
            all_players[local_player.player_id] = local_player

        for proj_id, proj in list(self.projectiles.items()):
            if not proj.active:
                to_remove.append(proj_id)
                continue

            # Check if projectile hit an obstacle (set by projectile's update)
            if proj.hit_obstacle:
                obstacle_hits.append({
                    'position': proj.hit_position,
                    'weapon': proj.weapon
                })
                to_remove.append(proj_id)

                # Create explosion for secondary weapon hitting obstacles (3x bigger)
                if proj.weapon == 'secondary':
                    self.create_explosion(proj.hit_position, size=72.0)
                    # Splash damage to nearby players
                    splash_radius = 15.0
                    splash_damage = proj.damage * 0.5
                    for player in all_players.values():
                        if player.player_id == proj.owner_id:
                            continue
                        if not player.is_alive:
                            continue
                        splash_dist = (player.position - proj.hit_position).length()
                        if splash_dist < splash_radius:
                            damage_mult = 1.0 - (splash_dist / splash_radius)
                            actual_damage = int(splash_damage * damage_mult)
                            if actual_damage > 0:
                                hits.append({
                                    'projectile_id': proj_id,
                                    'target_id': player.player_id,
                                    'attacker_id': proj.owner_id,
                                    'damage': actual_damage,
                                    'weapon': 'splash',
                                    'position': proj.hit_position
                                })
                continue

            # Check arena bounds
            pos = proj.position
            hit_wall = False
            if (abs(pos.x) > arena_bounds[0] or
                abs(pos.y) > arena_bounds[1] or
                abs(pos.z) > arena_bounds[2]):
                hit_wall = True
                to_remove.append(proj_id)

                # Create explosion for secondary weapon hitting walls (3x bigger)
                if proj.weapon == 'secondary':
                    self.create_explosion(pos, size=72.0)
                    obstacle_hits.append({
                        'position': Vec3(pos),
                        'weapon': proj.weapon
                    })
                    # Splash damage to nearby players
                    splash_radius = 15.0
                    splash_damage = proj.damage * 0.5
                    for player in all_players.values():
                        if player.player_id == proj.owner_id:
                            continue
                        if not player.is_alive:
                            continue
                        splash_dist = (player.position - pos).length()
                        if splash_dist < splash_radius:
                            damage_mult = 1.0 - (splash_dist / splash_radius)
                            actual_damage = int(splash_damage * damage_mult)
                            if actual_damage > 0:
                                hits.append({
                                    'projectile_id': proj_id,
                                    'target_id': player.player_id,
                                    'attacker_id': proj.owner_id,
                                    'damage': actual_damage,
                                    'weapon': 'splash',
                                    'position': Vec3(pos)
                                })
                continue

            # Check player collisions
            for player in all_players.values():
                if player.player_id == proj.owner_id:
                    continue
                if not player.is_alive:
                    continue

                # Distance-based collision
                dist = (player.position - proj.position).length()
                # Laser has 3x bigger hitbox
                hit_radius = 2.0 if proj.weapon == 'secondary' else 4.5 if proj.weapon == 'primary' else 1.5

                if dist < hit_radius:
                    hits.append({
                        'projectile_id': proj_id,
                        'target_id': player.player_id,
                        'attacker_id': proj.owner_id,
                        'damage': proj.damage,
                        'weapon': proj.weapon,
                        'position': Vec3(proj.position)
                    })
                    to_remove.append(proj_id)

                    # Create explosion for secondary weapon (3x bigger) with splash damage
                    if proj.weapon == 'secondary':
                        self.create_explosion(proj.position, size=84.0)  # 3x bigger explosion
                        # Splash damage to nearby players
                        splash_radius = 15.0
                        splash_damage = proj.damage * 0.5  # 50% damage for splash
                        for other_player in all_players.values():
                            if other_player.player_id == player.player_id:
                                continue  # Already hit directly
                            if other_player.player_id == proj.owner_id:
                                continue  # Don't damage self
                            if not other_player.is_alive:
                                continue
                            splash_dist = (other_player.position - proj.position).length()
                            if splash_dist < splash_radius:
                                # Damage falls off with distance
                                damage_mult = 1.0 - (splash_dist / splash_radius)
                                actual_damage = int(splash_damage * damage_mult)
                                if actual_damage > 0:
                                    hits.append({
                                        'projectile_id': proj_id,
                                        'target_id': other_player.player_id,
                                        'attacker_id': proj.owner_id,
                                        'damage': actual_damage,
                                        'weapon': 'splash',
                                        'position': Vec3(proj.position)
                                    })
                    break

        # Clean up
        for proj_id in to_remove:
            self.remove(proj_id)

        # Clean up finished explosions
        self.explosions = [e for e in self.explosions if e.active]

        return hits, obstacle_hits

    def clear(self):
        """Remove all projectiles and explosions."""
        for proj in list(self.projectiles.values()):
            if proj.active:
                proj.despawn()
        self.projectiles.clear()

        for exp in self.explosions:
            if exp.active:
                destroy(exp)
        self.explosions.clear()
