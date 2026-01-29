"""Level geometry with tunnels, obstacles, and industrial aesthetic."""
from ursina import *
import random


class Arena:
    """Large enclosed arena with tunnels and industrial structures."""

    def __init__(self, size=(200, 80, 200)):  # Even bigger arena
        self.size = size
        self.half_size = (size[0] / 2, size[1] / 2, size[2] / 2)
        self.walls = []
        self.obstacles = []

        self._create_boundary_walls()
        self._create_tunnels()
        self._create_obstacles()

    def _create_boundary_walls(self):
        """Create arena boundary with different textures for floor/walls/ceiling."""
        sx, sy, sz = self.size
        hx, hy, hz = self.half_size

        # Floor - dark metal plating with green tint
        floor_color = color.rgb(25, 35, 30)
        floor = Entity(
            model='quad',
            color=floor_color,
            scale=(sx, sz),
            position=(0, -hy, 0),
            rotation=(90, 0, 0),
            collider='box',
        )
        self.walls.append(floor)

        # Floor grid pattern
        grid_color = color.rgb(40, 55, 45)
        for i in range(-int(hx), int(hx) + 1, 15):
            line = Entity(
                model='cube',
                color=grid_color,
                scale=(0.3, 0.02, sz),
                position=(i, -hy + 0.02, 0),
            )
            self.walls.append(line)
        for i in range(-int(hz), int(hz) + 1, 15):
            line = Entity(
                model='cube',
                color=grid_color,
                scale=(sx, 0.02, 0.3),
                position=(0, -hy + 0.02, i),
            )
            self.walls.append(line)

        # Ceiling - darker with industrial panels
        ceiling_color = color.rgb(20, 25, 30)
        ceiling = Entity(
            model='quad',
            color=ceiling_color,
            scale=(sx, sz),
            position=(0, hy, 0),
            rotation=(-90, 0, 0),
            collider='box',
        )
        self.walls.append(ceiling)

        # Ceiling support beams
        beam_color = color.rgb(35, 40, 45)
        for i in range(-int(hx) + 20, int(hx), 40):
            beam = Entity(
                model='cube',
                color=beam_color,
                scale=(4, 3, sz),
                position=(i, hy - 1.5, 0),
            )
            self.walls.append(beam)

        # Walls - blue-gray tint for Z walls (front/back)
        wall_z_color = color.rgb(35, 45, 55)
        self.walls.append(Entity(
            model='quad',
            color=wall_z_color,
            scale=(sx, sy),
            position=(0, 0, hz),
            rotation=(0, 180, 0),
            collider='box',
        ))
        self.walls.append(Entity(
            model='quad',
            color=wall_z_color,
            scale=(sx, sy),
            position=(0, 0, -hz),
            collider='box',
        ))

        # Walls - rust/orange tint for X walls (left/right)
        wall_x_color = color.rgb(55, 40, 35)
        self.walls.append(Entity(
            model='quad',
            color=wall_x_color,
            scale=(sz, sy),
            position=(-hx, 0, 0),
            rotation=(0, 90, 0),
            collider='box',
        ))
        self.walls.append(Entity(
            model='quad',
            color=wall_x_color,
            scale=(sz, sy),
            position=(hx, 0, 0),
            rotation=(0, -90, 0),
            collider='box',
        ))

        # Add wall accent strips
        self._add_wall_accents()

    def _add_wall_accents(self):
        """Add glowing accent strips to walls."""
        hx, hy, hz = self.half_size
        accent_color = color.rgb(60, 100, 120)

        # Horizontal strips on walls
        positions = [
            (0, hy - 5, hz - 0.3, sx, 0.5, 0.1) for sx in [self.size[0] * 0.9],
            (0, -hy + 5, hz - 0.3, self.size[0] * 0.9, 0.5, 0.1),
            (0, hy - 5, -hz + 0.3, self.size[0] * 0.9, 0.5, 0.1),
            (0, -hy + 5, -hz + 0.3, self.size[0] * 0.9, 0.5, 0.1),
        ]

        for x, y, z, sx, sy, sz in positions:
            strip = Entity(
                model='cube',
                color=accent_color,
                scale=(sx, sy, sz),
                position=(x, y, z),
            )
            self.walls.append(strip)

    def _create_tunnels(self):
        """Create tunnel structures throughout the arena."""
        tunnel_color = color.rgb(40, 45, 50)
        inner_color = color.rgb(30, 35, 40)
        light_color = color.rgb(80, 120, 150)

        # Main central tunnel (horizontal through Z axis)
        tunnel_configs = [
            # Central cross tunnels
            {'pos': (0, 0, 0), 'size': (25, 20, 80), 'axis': 'z'},
            {'pos': (0, 0, 0), 'size': (80, 20, 25), 'axis': 'x'},

            # Corner tunnels
            {'pos': (60, 15, 60), 'size': (15, 15, 50), 'axis': 'z'},
            {'pos': (-60, 15, -60), 'size': (15, 15, 50), 'axis': 'z'},
            {'pos': (60, -15, -60), 'size': (50, 15, 15), 'axis': 'x'},
            {'pos': (-60, -15, 60), 'size': (50, 15, 15), 'axis': 'x'},

            # Elevated tunnels
            {'pos': (0, 25, 50), 'size': (40, 12, 15), 'axis': 'x'},
            {'pos': (0, -25, -50), 'size': (40, 12, 15), 'axis': 'x'},
        ]

        for config in tunnel_configs:
            self._create_tunnel_segment(
                config['pos'],
                config['size'],
                config['axis'],
                tunnel_color,
                inner_color,
                light_color
            )

    def _create_tunnel_segment(self, pos, size, axis, outer_color, inner_color, light_color):
        """Create a single tunnel segment with walls and lights."""
        x, y, z = pos
        w, h, d = size

        wall_thickness = 2

        if axis == 'z':
            # Tunnel along Z axis - create top/bottom/sides
            # Top
            self.obstacles.append(Entity(
                model='cube',
                color=outer_color,
                scale=(w, wall_thickness, d),
                position=(x, y + h/2 + wall_thickness/2, z),
            ))
            # Bottom
            self.obstacles.append(Entity(
                model='cube',
                color=outer_color,
                scale=(w, wall_thickness, d),
                position=(x, y - h/2 - wall_thickness/2, z),
            ))
            # Left
            self.obstacles.append(Entity(
                model='cube',
                color=inner_color,
                scale=(wall_thickness, h, d),
                position=(x - w/2 - wall_thickness/2, y, z),
            ))
            # Right
            self.obstacles.append(Entity(
                model='cube',
                color=inner_color,
                scale=(wall_thickness, h, d),
                position=(x + w/2 + wall_thickness/2, y, z),
            ))
            # Lights along tunnel
            for lz in range(int(z - d/2) + 10, int(z + d/2), 20):
                self.obstacles.append(Entity(
                    model='cube',
                    color=light_color,
                    scale=(w * 0.8, 0.3, 1),
                    position=(x, y + h/2, lz),
                ))

        else:  # axis == 'x'
            # Tunnel along X axis
            # Top
            self.obstacles.append(Entity(
                model='cube',
                color=outer_color,
                scale=(w, wall_thickness, d),
                position=(x, y + h/2 + wall_thickness/2, z),
            ))
            # Bottom
            self.obstacles.append(Entity(
                model='cube',
                color=outer_color,
                scale=(w, wall_thickness, d),
                position=(x, y - h/2 - wall_thickness/2, z),
            ))
            # Front
            self.obstacles.append(Entity(
                model='cube',
                color=inner_color,
                scale=(w, h, wall_thickness),
                position=(x, y, z + d/2 + wall_thickness/2),
            ))
            # Back
            self.obstacles.append(Entity(
                model='cube',
                color=inner_color,
                scale=(w, h, wall_thickness),
                position=(x, y, z - d/2 - wall_thickness/2),
            ))
            # Lights along tunnel
            for lx in range(int(x - w/2) + 10, int(x + w/2), 20):
                self.obstacles.append(Entity(
                    model='cube',
                    color=light_color,
                    scale=(1, 0.3, d * 0.8),
                    position=(lx, y + h/2, z),
                ))

    def _create_obstacles(self):
        """Create industrial obstacles."""
        # Color palette
        dark_metal = color.rgb(40, 45, 50)
        rust_metal = color.rgb(55, 40, 35)
        blue_metal = color.rgb(40, 50, 60)
        accent_teal = color.rgb(45, 70, 75)
        accent_orange = color.rgb(100, 60, 40)

        obstacle_configs = [
            # Large corner pillars
            {'pos': (70, 0, 70), 'scale': (10, 60, 10), 'color': dark_metal},
            {'pos': (-70, 0, 70), 'scale': (10, 60, 10), 'color': dark_metal},
            {'pos': (70, 0, -70), 'scale': (10, 60, 10), 'color': rust_metal},
            {'pos': (-70, 0, -70), 'scale': (10, 60, 10), 'color': rust_metal},

            # Mid-field structures
            {'pos': (40, 0, 0), 'scale': (8, 40, 8), 'color': blue_metal},
            {'pos': (-40, 0, 0), 'scale': (8, 40, 8), 'color': blue_metal},
            {'pos': (0, 0, 40), 'scale': (8, 40, 8), 'color': accent_teal},
            {'pos': (0, 0, -40), 'scale': (8, 40, 8), 'color': accent_teal},

            # Floating platforms
            {'pos': (50, 20, 50), 'scale': (20, 3, 20), 'color': dark_metal},
            {'pos': (-50, 20, -50), 'scale': (20, 3, 20), 'color': dark_metal},
            {'pos': (50, -20, -50), 'scale': (20, 3, 20), 'color': rust_metal},
            {'pos': (-50, -20, 50), 'scale': (20, 3, 20), 'color': rust_metal},

            # Cover blocks scattered around
            {'pos': (30, -30, 30), 'scale': (12, 8, 12), 'color': blue_metal},
            {'pos': (-30, -30, -30), 'scale': (12, 8, 12), 'color': blue_metal},
            {'pos': (30, 30, -30), 'scale': (12, 8, 12), 'color': accent_orange},
            {'pos': (-30, 30, 30), 'scale': (12, 8, 12), 'color': accent_orange},

            # Vertical pipes/columns
            {'pos': (20, 0, 60), 'scale': (3, 70, 3), 'color': accent_teal},
            {'pos': (-20, 0, -60), 'scale': (3, 70, 3), 'color': accent_teal},
            {'pos': (60, 0, 20), 'scale': (3, 70, 3), 'color': accent_orange},
            {'pos': (-60, 0, -20), 'scale': (3, 70, 3), 'color': accent_orange},

            # Additional mid-level platforms
            {'pos': (80, 0, 0), 'scale': (15, 4, 30), 'color': dark_metal},
            {'pos': (-80, 0, 0), 'scale': (15, 4, 30), 'color': dark_metal},
            {'pos': (0, 0, 80), 'scale': (30, 4, 15), 'color': rust_metal},
            {'pos': (0, 0, -80), 'scale': (30, 4, 15), 'color': rust_metal},

            # Small debris/cover
            {'pos': (15, -35, 15), 'scale': (6, 6, 6), 'color': dark_metal},
            {'pos': (-15, -35, -15), 'scale': (6, 6, 6), 'color': dark_metal},
            {'pos': (15, 35, -15), 'scale': (6, 6, 6), 'color': blue_metal},
            {'pos': (-15, 35, 15), 'scale': (6, 6, 6), 'color': blue_metal},
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
        margin = 15

        # Preferred spawn areas (open spaces)
        spawn_areas = [
            (50, 0, 0), (-50, 0, 0),
            (0, 0, 50), (0, 0, -50),
            (40, 25, 40), (-40, 25, -40),
            (40, -25, -40), (-40, -25, 40),
        ]

        # Try spawn areas first
        random.shuffle(spawn_areas)
        for area in spawn_areas:
            pos = Vec3(
                area[0] + random.uniform(-10, 10),
                area[1] + random.uniform(-5, 5),
                area[2] + random.uniform(-10, 10)
            )

            # Check if clear of obstacles
            too_close = False
            for obs in self.obstacles:
                dist = (Vec3(obs.position) - pos).length()
                min_dist = max(obs.scale_x, obs.scale_y, obs.scale_z) / 2 + 8
                if dist < min_dist:
                    too_close = True
                    break

            if not too_close and self.is_inside(pos, margin):
                return pos

        # Fallback
        return Vec3(
            random.uniform(-30, 30),
            random.uniform(-10, 10),
            random.uniform(-30, 30)
        )

    def get_bounds(self):
        """Get arena bounds for collision checking."""
        return self.half_size
