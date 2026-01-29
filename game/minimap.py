"""Minimap/radar display showing arena layout and player positions."""
from ursina import *
import math


class Minimap(Entity):
    """Top-down minimap showing arena and entities."""

    def __init__(self, arena_bounds, size=0.2, position=(0.38, 0.35)):
        super().__init__(parent=camera.ui)

        self.arena_bounds = arena_bounds
        self.map_size = size
        self.position = Vec2(*position)

        # Calculate scale factor (world units to minimap units)
        hx, hy, hz = arena_bounds
        self.scale_factor = size / max(hx * 2, hz * 2)

        # Background
        self.background = Entity(
            parent=self,
            model='quad',
            color=color.rgba(20, 20, 30, 200),
            scale=size,
            z=0.01
        )

        # Border
        self.border = Entity(
            parent=self,
            model='quad',
            color=color.rgba(80, 100, 120, 255),
            scale=size + 0.01,
            z=0.02
        )

        # Arena boundary outline
        self._create_arena_outline()

        # Player marker (always centered, arrow shape)
        self.player_marker = Entity(
            parent=self,
            model='quad',
            color=color.rgb(50, 255, 50),
            scale=0.015,
            z=-0.01
        )

        # Direction indicator (shows which way player is facing)
        self.direction_indicator = Entity(
            parent=self,
            model='quad',
            color=color.rgb(100, 255, 100),
            scale=(0.008, 0.02),
            z=-0.01
        )

        # Container for other player markers
        self.other_players = {}

        # Container for power-up markers
        self.powerup_markers = {}

        # Container for structure markers
        self._create_structure_markers()

    def _create_arena_outline(self):
        """Create minimap boundary indicators."""
        hx, hy, hz = self.arena_bounds
        s = self.scale_factor

        # Arena boundary lines (scaled to minimap)
        border_color = color.rgba(60, 80, 100, 200)
        line_width = 0.003

        # Top border
        Entity(
            parent=self,
            model='quad',
            color=border_color,
            scale=(self.map_size, line_width),
            position=(0, self.map_size / 2 - line_width / 2),
            z=-0.005
        )
        # Bottom border
        Entity(
            parent=self,
            model='quad',
            color=border_color,
            scale=(self.map_size, line_width),
            position=(0, -self.map_size / 2 + line_width / 2),
            z=-0.005
        )
        # Left border
        Entity(
            parent=self,
            model='quad',
            color=border_color,
            scale=(line_width, self.map_size),
            position=(-self.map_size / 2 + line_width / 2, 0),
            z=-0.005
        )
        # Right border
        Entity(
            parent=self,
            model='quad',
            color=border_color,
            scale=(line_width, self.map_size),
            position=(self.map_size / 2 - line_width / 2, 0),
            z=-0.005
        )

    def _create_structure_markers(self):
        """Create markers for arena structures on the minimap."""
        s = self.scale_factor
        structure_color = color.rgba(50, 60, 70, 180)

        # Central tunnel (along Z axis) - represented as a rectangle
        Entity(
            parent=self,
            model='quad',
            color=structure_color,
            scale=(30 * s, 100 * s),
            position=(0, 0),
            z=-0.003
        )

        # Corner pillars
        pillar_positions = [(70, 70), (-70, 70), (70, -70), (-70, -70)]
        for px, pz in pillar_positions:
            Entity(
                parent=self,
                model='quad',
                color=structure_color,
                scale=(12 * s, 12 * s),
                position=(px * s, pz * s),
                z=-0.003
            )

        # Mid structures
        mid_positions = [(50, 0), (-50, 0), (0, 50), (0, -50)]
        for px, pz in mid_positions:
            Entity(
                parent=self,
                model='quad',
                color=structure_color,
                scale=(10 * s, 10 * s),
                position=(px * s, pz * s),
                z=-0.003
            )

    def world_to_minimap(self, world_pos):
        """Convert world position to minimap position."""
        s = self.scale_factor
        return Vec2(world_pos.x * s, world_pos.z * s)

    def update_player(self, position, rotation_y):
        """Update the local player marker position and rotation."""
        # Player is always at center, but we rotate the direction indicator
        # Actually, let's make the map rotate with player for better orientation
        map_pos = self.world_to_minimap(position)

        # Clamp to minimap bounds
        half_size = self.map_size / 2 - 0.01
        map_pos.x = clamp(map_pos.x, -half_size, half_size)
        map_pos.y = clamp(map_pos.y, -half_size, half_size)

        self.player_marker.position = (map_pos.x, map_pos.y)

        # Update direction indicator
        self.direction_indicator.position = self.player_marker.position
        self.direction_indicator.rotation_z = -rotation_y

        # Offset the direction indicator forward
        rad = math.radians(rotation_y)
        offset = 0.015
        self.direction_indicator.position = (
            map_pos.x + math.sin(rad) * offset,
            map_pos.y + math.cos(rad) * offset
        )

    def update_other_player(self, player_id, position, is_alive=True):
        """Update or create marker for another player."""
        if player_id not in self.other_players:
            # Create new marker
            marker = Entity(
                parent=self,
                model='quad',
                color=color.rgb(255, 50, 50),  # Red for enemies
                scale=0.012,
                z=-0.01
            )
            self.other_players[player_id] = marker
        else:
            marker = self.other_players[player_id]

        if is_alive:
            marker.visible = True
            map_pos = self.world_to_minimap(Vec3(position[0], 0, position[2]) if isinstance(position, tuple) else position)
            half_size = self.map_size / 2 - 0.01
            map_pos.x = clamp(map_pos.x, -half_size, half_size)
            map_pos.y = clamp(map_pos.y, -half_size, half_size)
            marker.position = (map_pos.x, map_pos.y)
        else:
            marker.visible = False

    def remove_other_player(self, player_id):
        """Remove a player marker."""
        if player_id in self.other_players:
            destroy(self.other_players[player_id])
            del self.other_players[player_id]

    def update_powerup(self, powerup_id, position, powerup_type, active=True):
        """Update or create marker for a power-up."""
        if powerup_id not in self.powerup_markers:
            # Color based on type
            colors = {
                'health': color.rgb(50, 255, 50),
                'speed': color.rgb(50, 150, 255),
                'damage': color.rgb(255, 100, 50),
                'shield': color.rgb(200, 50, 255),
            }
            marker_color = colors.get(powerup_type, color.white)

            marker = Entity(
                parent=self,
                model='quad',
                color=marker_color,
                scale=0.008,
                z=-0.008
            )
            self.powerup_markers[powerup_id] = marker
        else:
            marker = self.powerup_markers[powerup_id]

        if active:
            marker.visible = True
            map_pos = self.world_to_minimap(Vec3(position[0], 0, position[2]) if isinstance(position, tuple) else position)
            half_size = self.map_size / 2 - 0.01
            map_pos.x = clamp(map_pos.x, -half_size, half_size)
            map_pos.y = clamp(map_pos.y, -half_size, half_size)
            marker.position = (map_pos.x, map_pos.y)
        else:
            marker.visible = False

    def remove_powerup(self, powerup_id):
        """Remove a power-up marker."""
        if powerup_id in self.powerup_markers:
            destroy(self.powerup_markers[powerup_id])
            del self.powerup_markers[powerup_id]

    def show(self):
        """Show the minimap."""
        self.enabled = True

    def hide(self):
        """Hide the minimap."""
        self.enabled = False

    def cleanup(self):
        """Clean up all markers."""
        for marker in self.other_players.values():
            destroy(marker)
        self.other_players.clear()

        for marker in self.powerup_markers.values():
            destroy(marker)
        self.powerup_markers.clear()
