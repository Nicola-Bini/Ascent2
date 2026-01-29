"""Level geometry and obstacles."""
from ursina import *
import random


class Arena:
    """Enclosed arena with obstacles."""

    def __init__(self, size=(50, 30, 50)):
        self.size = size
        self.half_size = (size[0] / 2, size[1] / 2, size[2] / 2)
        self.walls = []
        self.obstacles = []

        self._create_boundary_walls()
        self._create_obstacles()

    def _create_boundary_walls(self):
        """Create the arena boundary walls."""
        sx, sy, sz = self.size
        hx, hy, hz = self.half_size

        # Floor - use brick texture for grid-like depth cues
        floor = Entity(
            model='plane',
            color=color.rgb(60, 60, 120),
            scale=(sx, 1, sz),
            position=(0, -hy, 0),
            rotation=(0, 0, 0),
            collider='box',
            texture='brick',
            texture_scale=(25, 25),
            unlit=True
        )
        self.walls.append(floor)

        # Ceiling
        ceiling = Entity(
            model='plane',
            color=color.rgb(80, 80, 140),
            scale=(sx, 1, sz),
            position=(0, hy, 0),
            rotation=(180, 0, 0),
            collider='box',
            texture='brick',
            texture_scale=(25, 25),
            unlit=True
        )
        self.walls.append(ceiling)

        # Walls - use textures for visibility
        # Front wall (positive Z) - blue
        self.walls.append(Entity(
            model='cube',
            color=color.azure,
            scale=(sx, sy, 1),
            position=(0, 0, hz),
            collider='box',
            texture='brick',
            texture_scale=(10, 6),
            unlit=True
        ))

        # Back wall (negative Z) - blue
        self.walls.append(Entity(
            model='cube',
            color=color.azure,
            scale=(sx, sy, 1),
            position=(0, 0, -hz),
            collider='box',
            texture='brick',
            texture_scale=(10, 6),
            unlit=True
        ))

        # Left wall (negative X) - red/orange
        self.walls.append(Entity(
            model='cube',
            color=color.orange,
            scale=(1, sy, sz),
            position=(-hx, 0, 0),
            collider='box',
            texture='brick',
            texture_scale=(10, 6),
            unlit=True
        ))

        # Right wall (positive X) - red/orange
        self.walls.append(Entity(
            model='cube',
            color=color.orange,
            scale=(1, sy, sz),
            position=(hx, 0, 0),
            collider='box',
            texture='brick',
            texture_scale=(10, 6),
            unlit=True
        ))

    def _create_obstacles(self):
        """Create obstacles for cover."""
        obstacle_configs = [
            # Central pillar - cyan
            {'pos': (0, 0, 0), 'scale': (4, 15, 4), 'color': color.cyan},

            # Corner pillars - green
            {'pos': (15, 0, 15), 'scale': (3, 12, 3), 'color': color.green},
            {'pos': (-15, 0, 15), 'scale': (3, 12, 3), 'color': color.green},
            {'pos': (15, 0, -15), 'scale': (3, 12, 3), 'color': color.lime},
            {'pos': (-15, 0, -15), 'scale': (3, 12, 3), 'color': color.lime},

            # Floating platforms - magenta/violet
            {'pos': (10, 5, 0), 'scale': (6, 1, 6), 'color': color.magenta},
            {'pos': (-10, -5, 0), 'scale': (6, 1, 6), 'color': color.magenta},
            {'pos': (0, 8, 10), 'scale': (8, 1, 4), 'color': color.violet},
            {'pos': (0, -8, -10), 'scale': (8, 1, 4), 'color': color.violet},

            # Side barriers - yellow
            {'pos': (20, 0, 5), 'scale': (2, 8, 10), 'color': color.yellow},
            {'pos': (-20, 0, -5), 'scale': (2, 8, 10), 'color': color.yellow},
        ]

        for config in obstacle_configs:
            obstacle = Entity(
                model='cube',
                color=config['color'],
                scale=config['scale'],
                position=config['pos'],
                collider='box',
                unlit=True  # Bypass lighting for guaranteed visibility
            )
            self.obstacles.append(obstacle)

    def clamp_position(self, position, margin=2):
        """Clamp a position to stay within arena bounds."""
        hx, hy, hz = self.half_size
        return Vec3(
            clamp(position.x, -hx + margin, hx - margin),
            clamp(position.y, -hy + margin, hy - margin),
            clamp(position.z, -hz + margin, hz - margin)
        )

    def is_inside(self, position, margin=0):
        """Check if a position is inside the arena."""
        hx, hy, hz = self.half_size
        return (abs(position.x) < hx - margin and
                abs(position.y) < hy - margin and
                abs(position.z) < hz - margin)

    def get_random_spawn_point(self):
        """Get a random spawn point avoiding obstacles."""
        hx, hy, hz = self.half_size
        margin = 5

        for _ in range(20):  # Try up to 20 times
            pos = Vec3(
                random.uniform(-hx + margin, hx - margin),
                random.uniform(-hy + margin, hy - margin),
                random.uniform(-hz + margin, hz - margin)
            )

            # Check if too close to obstacles
            too_close = False
            for obs in self.obstacles:
                dist = (Vec3(obs.position) - pos).length()
                min_dist = max(obs.scale_x, obs.scale_y, obs.scale_z) + 3
                if dist < min_dist:
                    too_close = True
                    break

            if not too_close:
                return pos

        # Fallback to origin area
        return Vec3(
            random.uniform(-5, 5),
            random.uniform(-3, 3),
            random.uniform(-5, 5)
        )

    def get_bounds(self):
        """Get arena bounds for collision checking."""
        return self.half_size
