"""Level geometry with tunnels, obstacles, and industrial aesthetic."""
from ursina import *
import random


class Arena:
    """Massive enclosed arena with tunnels and industrial structures."""

    def __init__(self, size=(4000, 1600, 4000)):  # 20x bigger
        self.size = size
        self.half_size = (size[0] / 2, size[1] / 2, size[2] / 2)
        self.walls = []
        self.obstacles = []

        self._create_boundary_walls()
        self._create_obstacles()
        self._create_tunnels()
        self._create_space_stations()

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
        # Spaced every 400 units for the larger arena
        for i in range(-int(hx) + 400, int(hx), 800):
            self.walls.append(Entity(
                model='cube',
                color=Color(40/255, 50/255, 45/255, 1),
                scale=(30, 3, sz),
                position=(i, -hy + 3, 0),
            ))
        for i in range(-int(hz) + 400, int(hz), 800):
            self.walls.append(Entity(
                model='cube',
                color=Color(40/255, 50/255, 45/255, 1),
                scale=(sx, 3, 30),
                position=(0, -hy + 3, i),
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
        """Create multiple tunnel systems throughout the arena."""
        tunnel_wall = Color(32/255, 35/255, 38/255, 1)
        tunnel_inner = Color(26/255, 28/255, 32/255, 1)
        light_strip = Color(70/255, 120/255, 150/255, 1)
        red_light = Color(150/255, 50/255, 50/255, 1)
        green_light = Color(50/255, 150/255, 70/255, 1)

        # Central mega-tunnel (along Z axis)
        self._create_tunnel_segment(0, 0, 0, 'z', 2000, 300, 60, tunnel_wall, tunnel_inner, light_strip)

        # Perpendicular tunnel at center (along X axis) - higher
        self._create_tunnel_segment(0, 300, 0, 'x', 2000, 250, 50, tunnel_wall, tunnel_inner, red_light)

        # Lower tunnel network
        self._create_tunnel_segment(-800, -400, 0, 'z', 1500, 200, 40, tunnel_wall, tunnel_inner, green_light)
        self._create_tunnel_segment(800, -400, 0, 'z', 1500, 200, 40, tunnel_wall, tunnel_inner, green_light)

        # Diagonal tunnels (using angled obstacles)
        self._create_tunnel_segment(-600, 200, -600, 'z', 1200, 150, 35, tunnel_wall, tunnel_inner, light_strip)
        self._create_tunnel_segment(600, 200, 600, 'z', 1200, 150, 35, tunnel_wall, tunnel_inner, light_strip)

        # Vertical shaft tunnels
        self._create_vertical_shaft(1200, 0, 1200, 800, 200, tunnel_wall, tunnel_inner, red_light)
        self._create_vertical_shaft(-1200, 0, -1200, 800, 200, tunnel_wall, tunnel_inner, red_light)
        self._create_vertical_shaft(1200, 0, -1200, 800, 200, tunnel_wall, tunnel_inner, green_light)
        self._create_vertical_shaft(-1200, 0, 1200, 800, 200, tunnel_wall, tunnel_inner, green_light)

    def _create_tunnel_segment(self, x, y, z, axis, length, width, height, wall_color, inner_color, light_color):
        """Create a tunnel segment along specified axis."""
        hw = width / 2
        hh = height / 2

        if axis == 'z':
            # Top
            self.obstacles.append(Entity(
                model='cube', color=wall_color,
                scale=(width, 10, length), position=(x, y + hh + 5, z),
                collider='box',
            ))
            # Bottom
            self.obstacles.append(Entity(
                model='cube', color=wall_color,
                scale=(width, 10, length), position=(x, y - hh - 5, z),
                collider='box',
            ))
            # Left side
            self.obstacles.append(Entity(
                model='cube', color=inner_color,
                scale=(10, height, length), position=(x - hw - 5, y, z),
                collider='box',
            ))
            # Right side
            self.obstacles.append(Entity(
                model='cube', color=inner_color,
                scale=(10, height, length), position=(x + hw + 5, y, z),
                collider='box',
            ))
            # Lights
            for lz in range(int(z - length/2 + 100), int(z + length/2), 200):
                self.obstacles.append(Entity(
                    model='cube', color=light_color,
                    scale=(width - 20, 2, 10), position=(x, y + hh - 5, lz),
                ))
        else:  # axis == 'x'
            # Top
            self.obstacles.append(Entity(
                model='cube', color=wall_color,
                scale=(length, 10, width), position=(x, y + hh + 5, z),
                collider='box',
            ))
            # Bottom
            self.obstacles.append(Entity(
                model='cube', color=wall_color,
                scale=(length, 10, width), position=(x, y - hh - 5, z),
                collider='box',
            ))
            # Front side
            self.obstacles.append(Entity(
                model='cube', color=inner_color,
                scale=(length, height, 10), position=(x, y, z + hw + 5),
                collider='box',
            ))
            # Back side
            self.obstacles.append(Entity(
                model='cube', color=inner_color,
                scale=(length, height, 10), position=(x, y, z - hw - 5),
                collider='box',
            ))
            # Lights
            for lx in range(int(x - length/2 + 100), int(x + length/2), 200):
                self.obstacles.append(Entity(
                    model='cube', color=light_color,
                    scale=(10, 2, width - 20), position=(lx, y + hh - 5, z),
                ))

    def _create_vertical_shaft(self, x, y, z, height, width, wall_color, inner_color, light_color):
        """Create a vertical tunnel shaft."""
        hw = width / 2

        # Four walls of the shaft
        self.obstacles.append(Entity(
            model='cube', color=wall_color,
            scale=(width, height, 10), position=(x, y, z + hw + 5),
            collider='box',
        ))
        self.obstacles.append(Entity(
            model='cube', color=wall_color,
            scale=(width, height, 10), position=(x, y, z - hw - 5),
            collider='box',
        ))
        self.obstacles.append(Entity(
            model='cube', color=inner_color,
            scale=(10, height, width), position=(x + hw + 5, y, z),
            collider='box',
        ))
        self.obstacles.append(Entity(
            model='cube', color=inner_color,
            scale=(10, height, width), position=(x - hw - 5, y, z),
            collider='box',
        ))

        # Light rings
        for ly in range(int(y - height/2 + 50), int(y + height/2), 150):
            self.obstacles.append(Entity(
                model='cube', color=light_color,
                scale=(width - 20, 5, 5), position=(x, ly, z + hw - 10),
            ))
            self.obstacles.append(Entity(
                model='cube', color=light_color,
                scale=(width - 20, 5, 5), position=(x, ly, z - hw + 10),
            ))

    def _create_space_stations(self):
        """Create space station structures."""
        station_color = Color(45/255, 50/255, 55/255, 1)
        accent_color = Color(60/255, 80/255, 100/255, 1)

        # Four major space stations in quadrants
        station_positions = [
            (1400, 400, 1400),
            (-1400, 400, -1400),
            (1400, -400, -1400),
            (-1400, -400, 1400),
        ]

        for pos in station_positions:
            # Main hub
            self.obstacles.append(Entity(
                model='cube', color=station_color,
                scale=(300, 150, 300), position=pos,
                collider='box',
            ))
            # Spokes extending outward
            for angle_offset in [(200, 0, 0), (-200, 0, 0), (0, 0, 200), (0, 0, -200)]:
                spoke_pos = (pos[0] + angle_offset[0] * 1.5, pos[1], pos[2] + angle_offset[2] * 1.5)
                self.obstacles.append(Entity(
                    model='cube', color=accent_color,
                    scale=(80 if angle_offset[0] != 0 else 40, 60, 40 if angle_offset[0] != 0 else 80),
                    position=spoke_pos,
                    collider='box',
                ))

    def _create_obstacles(self):
        """Create obstacles for cover throughout the arena."""
        dark_metal = Color(32/255, 35/255, 38/255, 1)
        rust = Color(50/255, 38/255, 32/255, 1)
        industrial_blue = Color(30/255, 36/255, 48/255, 1)
        teal_metal = Color(32/255, 50/255, 55/255, 1)
        purple_metal = Color(45/255, 35/255, 55/255, 1)

        # Giant pillars throughout the arena
        pillar_positions = [
            (1000, 0, 0), (-1000, 0, 0), (0, 0, 1000), (0, 0, -1000),
            (700, 0, 700), (-700, 0, 700), (700, 0, -700), (-700, 0, -700),
            (1500, 0, 500), (-1500, 0, 500), (1500, 0, -500), (-1500, 0, -500),
            (500, 0, 1500), (-500, 0, 1500), (500, 0, -1500), (-500, 0, -1500),
        ]

        for i, pos in enumerate(pillar_positions):
            color = [dark_metal, rust, industrial_blue, teal_metal][i % 4]
            height = random.randint(600, 1400)
            width = random.randint(80, 200)
            self.obstacles.append(Entity(
                model='cube',
                color=color,
                scale=(width, height, width),
                position=pos,
                collider='box',
            ))

        # Floating platforms at various heights
        platform_configs = [
            # Upper platforms
            {'pos': (800, 500, 800), 'scale': (400, 30, 400), 'color': dark_metal},
            {'pos': (-800, 500, -800), 'scale': (400, 30, 400), 'color': dark_metal},
            {'pos': (800, 500, -800), 'scale': (350, 30, 350), 'color': rust},
            {'pos': (-800, 500, 800), 'scale': (350, 30, 350), 'color': rust},
            # Mid platforms
            {'pos': (1200, 0, 0), 'scale': (300, 40, 500), 'color': industrial_blue},
            {'pos': (-1200, 0, 0), 'scale': (300, 40, 500), 'color': industrial_blue},
            {'pos': (0, 0, 1200), 'scale': (500, 40, 300), 'color': teal_metal},
            {'pos': (0, 0, -1200), 'scale': (500, 40, 300), 'color': teal_metal},
            # Lower platforms
            {'pos': (600, -500, 600), 'scale': (350, 30, 350), 'color': purple_metal},
            {'pos': (-600, -500, -600), 'scale': (350, 30, 350), 'color': purple_metal},
            {'pos': (600, -500, -600), 'scale': (300, 30, 300), 'color': teal_metal},
            {'pos': (-600, -500, 600), 'scale': (300, 30, 300), 'color': teal_metal},
        ]

        for c in platform_configs:
            self.obstacles.append(Entity(
                model='cube',
                color=c['color'],
                scale=c['scale'],
                position=c['pos'],
                collider='box',
            ))

        # Asteroid-like debris clusters
        debris_centers = [
            (400, 200, 1600), (-400, 200, -1600),
            (1600, -200, 400), (-1600, -200, -400),
            (1800, 600, 0), (-1800, 600, 0),
            (0, -600, 1800), (0, -600, -1800),
        ]

        for center in debris_centers:
            # Create cluster of smaller rocks
            for _ in range(random.randint(5, 10)):
                offset = (
                    random.uniform(-200, 200),
                    random.uniform(-150, 150),
                    random.uniform(-200, 200)
                )
                size = random.uniform(40, 120)
                self.obstacles.append(Entity(
                    model='cube',
                    color=rust if random.random() > 0.5 else dark_metal,
                    scale=(size, size * random.uniform(0.6, 1.4), size * random.uniform(0.6, 1.4)),
                    position=(center[0] + offset[0], center[1] + offset[1], center[2] + offset[2]),
                    collider='box',
                ))

        # Cover blocks scattered around
        for _ in range(40):
            x = random.uniform(-1800, 1800)
            y = random.uniform(-700, 700)
            z = random.uniform(-1800, 1800)
            # Avoid center area
            if abs(x) < 400 and abs(z) < 400:
                continue
            size = random.uniform(60, 150)
            color = random.choice([dark_metal, rust, industrial_blue, teal_metal, purple_metal])
            self.obstacles.append(Entity(
                model='cube',
                color=color,
                scale=(size, size * random.uniform(0.5, 2), size),
                position=(x, y, z),
                collider='box',
            ))

    def get_random_spawn_point(self):
        """Get a random spawn point in open area."""
        # Spawn points distributed throughout the larger arena
        areas = [
            # Corners
            (1500, 0, 1500), (-1500, 0, 1500), (1500, 0, -1500), (-1500, 0, -1500),
            # Mid edges
            (1500, 300, 0), (-1500, 300, 0), (0, 300, 1500), (0, 300, -1500),
            (1500, -300, 0), (-1500, -300, 0), (0, -300, 1500), (0, -300, -1500),
            # Upper areas
            (800, 600, 800), (-800, 600, 800), (800, 600, -800), (-800, 600, -800),
            # Lower areas
            (800, -600, 800), (-800, -600, 800), (800, -600, -800), (-800, -600, -800),
        ]

        area = random.choice(areas)
        return Vec3(
            area[0] + random.uniform(-100, 100),
            area[1] + random.uniform(-50, 50),
            area[2] + random.uniform(-100, 100)
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
