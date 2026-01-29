"""Level geometry and obstacles with realistic industrial/space station aesthetic."""
from ursina import *
import random


class Arena:
    """Large enclosed arena with industrial obstacles."""

    def __init__(self, size=(120, 60, 120)):  # Much bigger arena
        self.size = size
        self.half_size = (size[0] / 2, size[1] / 2, size[2] / 2)
        self.walls = []
        self.obstacles = []

        self._create_boundary_walls()
        self._create_obstacles()

    def _create_boundary_walls(self):
        """Create the arena boundary walls with industrial look."""
        sx, sy, sz = self.size
        hx, hy, hz = self.half_size

        # Floor - dark metal plating
        floor = Entity(
            model='plane',
            color=color.rgb(35, 40, 45),  # Dark steel gray
            scale=(sx, 1, sz),
            position=(0, -hy, 0),
            rotation=(0, 0, 0),
            collider='box',
            texture='brick',
            texture_scale=(30, 30),
        )
        self.walls.append(floor)

        # Add floor grid lines for depth perception
        for i in range(-int(hx), int(hx) + 1, 10):
            line = Entity(
                model='cube',
                color=color.rgb(50, 55, 60),
                scale=(0.2, 0.01, sz),
                position=(i, -hy + 0.01, 0),
            )
            self.walls.append(line)
        for i in range(-int(hz), int(hz) + 1, 10):
            line = Entity(
                model='cube',
                color=color.rgb(50, 55, 60),
                scale=(sx, 0.01, 0.2),
                position=(0, -hy + 0.01, i),
            )
            self.walls.append(line)

        # Ceiling - slightly lighter with supports
        ceiling = Entity(
            model='plane',
            color=color.rgb(30, 35, 40),
            scale=(sx, 1, sz),
            position=(0, hy, 0),
            rotation=(180, 0, 0),
            collider='box',
            texture='brick',
            texture_scale=(30, 30),
        )
        self.walls.append(ceiling)

        # Walls with industrial color coding
        # Front/Back walls - blue-gray (cold direction)
        wall_blue = color.rgb(40, 50, 70)
        self.walls.append(Entity(
            model='cube',
            color=wall_blue,
            scale=(sx, sy, 1),
            position=(0, 0, hz),
            collider='box',
            texture='brick',
            texture_scale=(24, 12),
        ))
        self.walls.append(Entity(
            model='cube',
            color=wall_blue,
            scale=(sx, sy, 1),
            position=(0, 0, -hz),
            collider='box',
            texture='brick',
            texture_scale=(24, 12),
        ))

        # Left/Right walls - rust/warm tones
        wall_rust = color.rgb(70, 50, 40)
        self.walls.append(Entity(
            model='cube',
            color=wall_rust,
            scale=(1, sy, sz),
            position=(-hx, 0, 0),
            collider='box',
            texture='brick',
            texture_scale=(24, 12),
        ))
        self.walls.append(Entity(
            model='cube',
            color=wall_rust,
            scale=(1, sy, sz),
            position=(hx, 0, 0),
            collider='box',
            texture='brick',
            texture_scale=(24, 12),
        ))

        # Add wall accent lights (dim glowing strips)
        self._add_wall_lights()

    def _add_wall_lights(self):
        """Add accent lighting strips to walls."""
        hx, hy, hz = self.half_size

        # Horizontal light strips on walls
        light_color = color.rgb(80, 100, 120)
        strip_positions = [
            # Z walls
            (0, hy - 3, hz - 0.5, 'z'),
            (0, -hy + 3, hz - 0.5, 'z'),
            (0, hy - 3, -hz + 0.5, 'z'),
            (0, -hy + 3, -hz + 0.5, 'z'),
            # X walls
            (hx - 0.5, hy - 3, 0, 'x'),
            (-hx + 0.5, hy - 3, 0, 'x'),
            (hx - 0.5, -hy + 3, 0, 'x'),
            (-hx + 0.5, -hy + 3, 0, 'x'),
        ]

        for x, y, z, axis in strip_positions:
            if axis == 'z':
                scale = (self.size[0] * 0.8, 0.3, 0.1)
            else:
                scale = (0.1, 0.3, self.size[2] * 0.8)

            strip = Entity(
                model='cube',
                color=light_color,
                scale=scale,
                position=(x, y, z),
            )
            self.walls.append(strip)

    def _create_obstacles(self):
        """Create industrial obstacles for cover and navigation."""
        # Colors - industrial palette
        dark_metal = color.rgb(45, 50, 55)
        rust_metal = color.rgb(60, 45, 40)
        blue_metal = color.rgb(45, 55, 70)
        accent_orange = color.rgb(120, 70, 40)
        accent_cyan = color.rgb(50, 80, 90)

        obstacle_configs = [
            # Central structure - large industrial tower
            {'pos': (0, 0, 0), 'scale': (8, 40, 8), 'color': dark_metal},
            {'pos': (0, 22, 0), 'scale': (12, 2, 12), 'color': rust_metal},  # Top platform
            {'pos': (0, -22, 0), 'scale': (12, 2, 12), 'color': rust_metal},  # Bottom platform

            # Corner structures
            {'pos': (40, 0, 40), 'scale': (6, 30, 6), 'color': blue_metal},
            {'pos': (-40, 0, 40), 'scale': (6, 30, 6), 'color': blue_metal},
            {'pos': (40, 0, -40), 'scale': (6, 30, 6), 'color': rust_metal},
            {'pos': (-40, 0, -40), 'scale': (6, 30, 6), 'color': rust_metal},

            # Mid-level platforms
            {'pos': (25, 10, 0), 'scale': (15, 2, 15), 'color': dark_metal},
            {'pos': (-25, -10, 0), 'scale': (15, 2, 15), 'color': dark_metal},
            {'pos': (0, 15, 30), 'scale': (20, 2, 10), 'color': blue_metal},
            {'pos': (0, -15, -30), 'scale': (20, 2, 10), 'color': blue_metal},

            # Side barriers / cover
            {'pos': (50, 0, 20), 'scale': (4, 20, 25), 'color': rust_metal},
            {'pos': (-50, 0, -20), 'scale': (4, 20, 25), 'color': rust_metal},
            {'pos': (20, 0, 50), 'scale': (25, 20, 4), 'color': blue_metal},
            {'pos': (-20, 0, -50), 'scale': (25, 20, 4), 'color': blue_metal},

            # Floating debris / smaller obstacles
            {'pos': (30, 5, 30), 'scale': (5, 5, 5), 'color': dark_metal},
            {'pos': (-30, -5, -30), 'scale': (5, 5, 5), 'color': dark_metal},
            {'pos': (35, -8, -25), 'scale': (4, 4, 4), 'color': rust_metal},
            {'pos': (-35, 8, 25), 'scale': (4, 4, 4), 'color': rust_metal},

            # Vertical pipes/columns
            {'pos': (15, 0, 25), 'scale': (2, 50, 2), 'color': accent_cyan},
            {'pos': (-15, 0, -25), 'scale': (2, 50, 2), 'color': accent_cyan},
            {'pos': (25, 0, -15), 'scale': (2, 50, 2), 'color': accent_orange},
            {'pos': (-25, 0, 15), 'scale': (2, 50, 2), 'color': accent_orange},

            # Low cover blocks
            {'pos': (10, -25, 10), 'scale': (8, 6, 8), 'color': dark_metal},
            {'pos': (-10, -25, -10), 'scale': (8, 6, 8), 'color': dark_metal},
            {'pos': (10, 25, -10), 'scale': (8, 6, 8), 'color': blue_metal},
            {'pos': (-10, 25, 10), 'scale': (8, 6, 8), 'color': blue_metal},
        ]

        for config in obstacle_configs:
            obstacle = Entity(
                model='cube',
                color=config['color'],
                scale=config['scale'],
                position=config['pos'],
                collider='box',
            )
            self.obstacles.append(obstacle)

            # Add edge highlights to larger obstacles
            if min(config['scale']) > 3:
                self._add_edge_highlight(obstacle, config)

    def _add_edge_highlight(self, obstacle, config):
        """Add subtle edge highlights to obstacles."""
        sx, sy, sz = config['scale']
        highlight_color = color.rgb(70, 80, 90)

        # Only add to top edges of platforms
        if sy < sx and sy < sz:  # It's a platform
            edge = Entity(
                parent=obstacle,
                model='cube',
                color=highlight_color,
                scale=(1.02, 0.1, 1.02),
                position=(0, 0.5, 0),
            )

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
        margin = 10

        for _ in range(30):  # Try up to 30 times
            pos = Vec3(
                random.uniform(-hx + margin, hx - margin),
                random.uniform(-hy + margin, hy - margin),
                random.uniform(-hz + margin, hz - margin)
            )

            # Check if too close to obstacles
            too_close = False
            for obs in self.obstacles:
                dist = (Vec3(obs.position) - pos).length()
                min_dist = max(obs.scale_x, obs.scale_y, obs.scale_z) + 5
                if dist < min_dist:
                    too_close = True
                    break

            if not too_close:
                return pos

        # Fallback to a corner area
        corner = random.choice([
            (30, 0, 30), (-30, 0, 30), (30, 0, -30), (-30, 0, -30)
        ])
        return Vec3(corner[0], corner[1], corner[2])

    def get_bounds(self):
        """Get arena bounds for collision checking."""
        return self.half_size
