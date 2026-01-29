"""Level geometry with tunnels, obstacles, and industrial aesthetic."""
from ursina import *
import random


class Arena:
    """Large enclosed arena with tunnels and industrial structures."""

    def __init__(self, size=(200, 80, 200)):
        self.size = size
        self.half_size = (size[0] / 2, size[1] / 2, size[2] / 2)
        self.walls = []
        self.obstacles = []

        self._create_boundary_walls()
        self._create_obstacles()
        self._create_tunnels()

    def _create_boundary_walls(self):
        """Create arena boundary walls with industrial colors."""
        sx, sy, sz = self.size
        hx, hy, hz = self.half_size

        # Floor - dark metallic gray-green
        self.walls.append(Entity(
            model='cube',
            color=Color(25/255, 30/255, 28/255, 1),
            scale=(sx + 2, 1, sz + 2),
            position=(0, -hy - 0.5, 0),
            collider='box',
        ))

        # Floor grid lines for depth perception (no collider - decorative)
        for i in range(-int(hx) + 20, int(hx), 40):
            self.walls.append(Entity(
                model='cube',
                color=Color(40/255, 50/255, 45/255, 1),
                scale=(1.5, 0.15, sz),
                position=(i, -hy + 0.15, 0),
            ))
        for i in range(-int(hz) + 20, int(hz), 40):
            self.walls.append(Entity(
                model='cube',
                color=Color(40/255, 50/255, 45/255, 1),
                scale=(sx, 0.15, 1.5),
                position=(0, -hy + 0.15, i),
            ))

        # Ceiling - very dark
        self.walls.append(Entity(
            model='cube',
            color=Color(18/255, 20/255, 22/255, 1),
            scale=(sx + 2, 1, sz + 2),
            position=(0, hy + 0.5, 0),
            collider='box',
        ))

        # Front wall (positive Z) - dark blue-gray industrial
        self.walls.append(Entity(
            model='cube',
            color=Color(28/255, 32/255, 42/255, 1),
            scale=(sx + 2, sy + 2, 1),
            position=(0, 0, hz + 0.5),
            collider='box',
        ))

        # Back wall (negative Z) - dark blue-gray
        self.walls.append(Entity(
            model='cube',
            color=Color(28/255, 32/255, 42/255, 1),
            scale=(sx + 2, sy + 2, 1),
            position=(0, 0, -hz - 0.5),
            collider='box',
        ))

        # Left wall (negative X) - dark rust/brown
        self.walls.append(Entity(
            model='cube',
            color=Color(38/255, 30/255, 26/255, 1),
            scale=(1, sy + 2, sz + 2),
            position=(-hx - 0.5, 0, 0),
            collider='box',
        ))

        # Right wall (positive X) - dark rust/brown
        self.walls.append(Entity(
            model='cube',
            color=Color(38/255, 30/255, 26/255, 1),
            scale=(1, sy + 2, sz + 2),
            position=(hx + 0.5, 0, 0),
            collider='box',
        ))

    def _create_tunnels(self):
        """Create tunnel structures."""
        tunnel_wall = Color(32/255, 35/255, 38/255, 1)
        tunnel_inner = Color(26/255, 28/255, 32/255, 1)
        light_strip = Color(70/255, 120/255, 150/255, 1)

        # Central horizontal tunnel (along Z axis)
        # Top
        self.obstacles.append(Entity(
            model='cube', color=tunnel_wall,
            scale=(30, 3, 100), position=(0, 12, 0),
            collider='box',
        ))
        # Bottom
        self.obstacles.append(Entity(
            model='cube', color=tunnel_wall,
            scale=(30, 3, 100), position=(0, -12, 0),
            collider='box',
        ))
        # Left side
        self.obstacles.append(Entity(
            model='cube', color=tunnel_inner,
            scale=(3, 21, 100), position=(-16.5, 0, 0),
            collider='box',
        ))
        # Right side
        self.obstacles.append(Entity(
            model='cube', color=tunnel_inner,
            scale=(3, 21, 100), position=(16.5, 0, 0),
            collider='box',
        ))
        # Lights inside tunnel (no collider - decorative only)
        for z in range(-40, 50, 20):
            self.obstacles.append(Entity(
                model='cube', color=light_strip,
                scale=(25, 0.5, 2), position=(0, 10, z),
            ))

        # Central cross tunnel (along X axis) - offset vertically
        # Top
        self.obstacles.append(Entity(
            model='cube', color=tunnel_wall,
            scale=(100, 3, 25), position=(0, 27, 0),
            collider='box',
        ))
        # Bottom
        self.obstacles.append(Entity(
            model='cube', color=tunnel_wall,
            scale=(100, 3, 25), position=(0, 3, 0),
            collider='box',
        ))
        # Front side
        self.obstacles.append(Entity(
            model='cube', color=tunnel_inner,
            scale=(100, 21, 3), position=(0, 15, 14),
            collider='box',
        ))
        # Back side
        self.obstacles.append(Entity(
            model='cube', color=tunnel_inner,
            scale=(100, 21, 3), position=(0, 15, -14),
            collider='box',
        ))

    def _create_obstacles(self):
        """Create obstacles for cover."""
        dark_metal = Color(32/255, 35/255, 38/255, 1)
        rust = Color(50/255, 38/255, 32/255, 1)
        industrial_blue = Color(30/255, 36/255, 48/255, 1)
        teal_metal = Color(32/255, 50/255, 55/255, 1)

        configs = [
            # Corner pillars - tall structures
            {'pos': (70, 0, 70), 'scale': (12, 70, 12), 'color': dark_metal},
            {'pos': (-70, 0, 70), 'scale': (12, 70, 12), 'color': dark_metal},
            {'pos': (70, 0, -70), 'scale': (12, 70, 12), 'color': rust},
            {'pos': (-70, 0, -70), 'scale': (12, 70, 12), 'color': rust},

            # Mid structures
            {'pos': (50, 0, 0), 'scale': (10, 50, 10), 'color': industrial_blue},
            {'pos': (-50, 0, 0), 'scale': (10, 50, 10), 'color': industrial_blue},
            {'pos': (0, 0, 50), 'scale': (10, 50, 10), 'color': teal_metal},
            {'pos': (0, 0, -50), 'scale': (10, 50, 10), 'color': teal_metal},

            # Platforms at various heights
            {'pos': (50, 20, 50), 'scale': (25, 4, 25), 'color': dark_metal},
            {'pos': (-50, 20, -50), 'scale': (25, 4, 25), 'color': dark_metal},
            {'pos': (50, -20, -50), 'scale': (25, 4, 25), 'color': rust},
            {'pos': (-50, -20, 50), 'scale': (25, 4, 25), 'color': rust},

            # Cover blocks
            {'pos': (35, -30, 35), 'scale': (15, 10, 15), 'color': industrial_blue},
            {'pos': (-35, -30, -35), 'scale': (15, 10, 15), 'color': industrial_blue},
            {'pos': (35, 30, -35), 'scale': (15, 10, 15), 'color': teal_metal},
            {'pos': (-35, 30, 35), 'scale': (15, 10, 15), 'color': teal_metal},
        ]

        for c in configs:
            self.obstacles.append(Entity(
                model='cube',
                color=c['color'],
                scale=c['scale'],
                position=c['pos'],
                collider='box',
            ))

    def get_random_spawn_point(self):
        """Get a random spawn point in open area."""
        # Spawn in corners away from center tunnels
        areas = [
            (60, 0, 60), (-60, 0, 60), (60, 0, -60), (-60, 0, -60),
            (60, 25, 0), (-60, 25, 0), (0, 25, 60), (0, 25, -60),
            (60, -25, 0), (-60, -25, 0), (0, -25, 60), (0, -25, -60),
        ]

        area = random.choice(areas)
        return Vec3(
            area[0] + random.uniform(-8, 8),
            area[1] + random.uniform(-5, 5),
            area[2] + random.uniform(-8, 8)
        )

    def get_bounds(self):
        """Get arena bounds."""
        return self.half_size

    def is_inside(self, position, margin=0):
        hx, hy, hz = self.half_size
        return (abs(position.x) < hx - margin and
                abs(position.y) < hy - margin and
                abs(position.z) < hz - margin)

    def clamp_position(self, position, margin=2):
        hx, hy, hz = self.half_size
        return Vec3(
            clamp(position.x, -hx + margin, hx - margin),
            clamp(position.y, -hy + margin, hy - margin),
            clamp(position.z, -hz + margin, hz - margin)
        )

    def get_collidables(self):
        """Get all entities with colliders for collision checking."""
        collidables = []
        for wall in self.walls:
            if hasattr(wall, 'collider') and wall.collider:
                collidables.append(wall)
        for obstacle in self.obstacles:
            if hasattr(obstacle, 'collider') and obstacle.collider:
                collidables.append(obstacle)
        return collidables
