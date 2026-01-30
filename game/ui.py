"""HUD and menu UI components."""
from ursina import *


class MainMenu(Entity):
    """Main menu with Host/Join/Quit options."""

    def __init__(self, on_host, on_join, on_quit):
        super().__init__(parent=camera.ui)

        self.on_host = on_host
        self.on_join = on_join
        self.on_quit = on_quit

        # Background
        self.bg = Entity(
            parent=self,
            model='quad',
            color=color.rgb(20, 20, 30),
            scale=(2, 1),
            z=1
        )

        # Title
        self.title = Text(
            parent=self,
            text='DESCENT-LIKE 6DOF',
            scale=3,
            origin=(0, 0),
            y=0.35,
            color=color.cyan
        )

        self.subtitle = Text(
            parent=self,
            text='LAN Multiplayer Arena',
            scale=1.5,
            origin=(0, 0),
            y=0.25,
            color=color.gray
        )

        # Buttons
        button_scale = (0.3, 0.08)

        self.host_button = Button(
            parent=self,
            text='HOST GAME',
            scale=button_scale,
            y=0.05,
            color=color.azure,
            highlight_color=color.cyan,
            on_click=self._on_host_click
        )

        self.join_button = Button(
            parent=self,
            text='JOIN GAME',
            scale=button_scale,
            y=-0.08,
            color=color.orange,
            highlight_color=color.yellow,
            on_click=self._on_join_click
        )

        self.quit_button = Button(
            parent=self,
            text='QUIT',
            scale=button_scale,
            y=-0.21,
            color=color.red.tint(-0.2),
            highlight_color=color.red,
            on_click=self._on_quit_click
        )

        # Controls info
        self.controls = Text(
            parent=self,
            text='Controls: WASD=Move | Mouse=Look | Q/E=Roll | Space/Ctrl=Up/Down | LMB=Shoot | ESC=Menu',
            scale=0.8,
            origin=(0, 0),
            y=-0.38,
            color=color.light_gray
        )

    def _on_host_click(self):
        self.on_host()

    def _on_join_click(self):
        self.on_join()

    def _on_quit_click(self):
        self.on_quit()

    def show(self):
        self.enabled = True
        mouse.locked = False
        mouse.visible = True

    def hide(self):
        self.enabled = False


class JoinDialog(Entity):
    """Dialog for entering host IP to join."""

    def __init__(self, on_connect, on_cancel, default_ip="192.168.1."):
        super().__init__(parent=camera.ui)

        self.on_connect = on_connect
        self.on_cancel = on_cancel
        self.default_ip = default_ip

        # Background panel
        self.panel = Entity(
            parent=self,
            model='quad',
            color=Color(30/255, 30/255, 40/255, 230/255),
            scale=(0.5, 0.35),
            z=0.1
        )

        # Title
        self.title = Text(
            parent=self,
            text='JOIN GAME',
            scale=2,
            origin=(0, 0),
            y=0.12,
            color=color.orange
        )

        # IP input label
        self.ip_label = Text(
            parent=self,
            text='Enter Host IP:',
            scale=1,
            origin=(0, 0),
            y=0.04,
            color=color.white
        )

        # IP input field
        self.ip_input = InputField(
            parent=self,
            default_value=self.default_ip,
            scale=(0.35, 0.05),
            y=-0.03,
            limit_content_to='0123456789.',
            character_limit=15
        )

        # Buttons
        self.connect_button = Button(
            parent=self,
            text='CONNECT',
            scale=(0.15, 0.05),
            position=(-0.09, -0.11),
            color=color.green.tint(-0.2),
            highlight_color=color.green,
            on_click=self._on_connect_click
        )

        self.cancel_button = Button(
            parent=self,
            text='CANCEL',
            scale=(0.15, 0.05),
            position=(0.09, -0.11),
            color=color.red.tint(-0.2),
            highlight_color=color.red,
            on_click=self._on_cancel_click
        )

        self.enabled = False

    def _on_connect_click(self):
        ip = self.ip_input.text.strip()
        if ip:
            self.on_connect(ip)

    def _on_cancel_click(self):
        self.on_cancel()

    def show(self):
        self.enabled = True
        self.ip_input.active = True

    def hide(self):
        self.enabled = False
        self.ip_input.active = False


class GameConfigScreen(Entity):
    """Game configuration screen - set bots, vehicle, difficulty before starting."""

    def __init__(self, on_start, on_cancel):
        super().__init__(parent=camera.ui)

        self.on_start = on_start
        self.on_cancel = on_cancel

        # Try to load ship list
        self.ship_list = ['fighter']  # Default
        try:
            from models import list_all_ships, SHIPS
            self.ship_list = list_all_ships()
            self.ships_data = SHIPS
        except ImportError:
            self.ships_data = {}

        # Configuration values
        self.config = {
            'bot_count': 5,
            'difficulty': 'medium',
            'starting_ship': 'fighter',
            'friendly_fire': False,
        }

        # Background panel
        self.panel = Entity(
            parent=self,
            model='quad',
            color=Color(20/255, 25/255, 35/255, 250/255),
            scale=(0.9, 0.85),
            z=0.1
        )

        # Title
        self.title = Text(
            parent=self,
            text='GAME CONFIGURATION',
            scale=2.5,
            origin=(0, 0),
            y=0.35,
            color=color.cyan
        )

        # === BOT COUNT ===
        self.bot_label = Text(
            parent=self,
            text='Number of Bots:',
            scale=1.2,
            origin=(-0.5, 0),
            position=(-0.35, 0.22),
            color=color.white
        )

        self.bot_count_text = Text(
            parent=self,
            text='5',
            scale=1.5,
            origin=(0, 0),
            position=(0.15, 0.22),
            color=color.yellow
        )

        self.bot_minus = Button(
            parent=self,
            text='Less',
            scale=(0.07, 0.05),
            position=(-0.02, 0.22),
            color=color.red.tint(-0.3),
            on_click=self._decrease_bots
        )

        self.bot_plus = Button(
            parent=self,
            text='More',
            scale=(0.07, 0.05),
            position=(0.28, 0.22),
            color=color.green.tint(-0.3),
            on_click=self._increase_bots
        )

        # === DIFFICULTY ===
        self.diff_label = Text(
            parent=self,
            text='Difficulty:',
            scale=1.2,
            origin=(-0.5, 0),
            position=(-0.35, 0.12),
            color=color.white
        )

        self.diff_easy = Button(
            parent=self,
            text='Easy',
            scale=(0.1, 0.045),
            position=(0.0, 0.12),
            color=color.gray,
            on_click=lambda: self._set_difficulty('easy')
        )

        self.diff_medium = Button(
            parent=self,
            text='Medium',
            scale=(0.1, 0.045),
            position=(0.12, 0.12),
            color=color.azure,
            on_click=lambda: self._set_difficulty('medium')
        )

        self.diff_hard = Button(
            parent=self,
            text='Hard',
            scale=(0.1, 0.045),
            position=(0.24, 0.12),
            color=color.gray,
            on_click=lambda: self._set_difficulty('hard')
        )

        # === STARTING VEHICLE ===
        self.ship_label = Text(
            parent=self,
            text='Starting Vehicle:',
            scale=1.2,
            origin=(-0.5, 0),
            position=(-0.35, 0.01),
            color=color.white
        )

        self.ship_index = 0
        self.ship_name_text = Text(
            parent=self,
            text='Fighter',
            scale=1.3,
            origin=(0, 0),
            position=(0.12, 0.01),
            color=color.orange
        )

        self.ship_prev = Button(
            parent=self,
            text='Prev',
            scale=(0.08, 0.045),
            position=(-0.05, 0.01),
            color=color.azure,
            on_click=self._prev_ship
        )

        self.ship_next = Button(
            parent=self,
            text='Next',
            scale=(0.08, 0.045),
            position=(0.30, 0.01),
            color=color.azure,
            on_click=self._next_ship
        )

        # Ship info
        self.ship_info = Text(
            parent=self,
            text='',
            scale=0.9,
            origin=(0, 0),
            position=(0, -0.08),
            color=color.light_gray
        )
        self._update_ship_info()

        # === VEHICLE CATEGORIES (quick filters) ===
        self.cat_label = Text(
            parent=self,
            text='Filter:',
            scale=1,
            origin=(-0.5, 0),
            position=(-0.35, -0.16),
            color=color.gray
        )

        categories = [('All', None), ('Fly', 'fly'), ('Tank', 'ground'), ('Train', 'train'), ('Hover', 'hover')]
        for i, (label, movement) in enumerate(categories):
            btn = Button(
                parent=self,
                text=label,
                scale=(0.07, 0.04),
                position=(-0.12 + i * 0.09, -0.16),
                color=color.gray.tint(-0.2),
                on_click=lambda m=movement: self._filter_ships(m)
            )

        # === FRIENDLY FIRE ===
        self.ff_label = Text(
            parent=self,
            text='Friendly Fire:',
            scale=1.2,
            origin=(-0.5, 0),
            position=(-0.35, -0.25),
            color=color.white
        )

        self.ff_button = Button(
            parent=self,
            text='OFF',
            scale=(0.1, 0.045),
            position=(0.08, -0.25),
            color=color.red.tint(-0.3),
            on_click=self._toggle_friendly_fire
        )

        # === START / CANCEL BUTTONS ===
        self.start_button = Button(
            parent=self,
            text='START GAME',
            scale=(0.25, 0.07),
            position=(-0.12, -0.36),
            color=color.green.tint(-0.2),
            highlight_color=color.green,
            on_click=self._on_start
        )

        self.cancel_button = Button(
            parent=self,
            text='BACK',
            scale=(0.15, 0.07),
            position=(0.18, -0.36),
            color=color.red.tint(-0.3),
            highlight_color=color.red,
            on_click=self._on_cancel
        )

        self.enabled = False
        self.current_filter = None

    def _decrease_bots(self):
        self.config['bot_count'] = max(0, self.config['bot_count'] - 1)
        self.bot_count_text.text = str(self.config['bot_count'])

    def _increase_bots(self):
        self.config['bot_count'] = min(30, self.config['bot_count'] + 1)
        self.bot_count_text.text = str(self.config['bot_count'])

    def _set_difficulty(self, diff):
        self.config['difficulty'] = diff
        # Update button colors
        self.diff_easy.color = color.azure if diff == 'easy' else color.gray
        self.diff_medium.color = color.azure if diff == 'medium' else color.gray
        self.diff_hard.color = color.azure if diff == 'hard' else color.gray

    def _prev_ship(self):
        self.ship_index = (self.ship_index - 1) % len(self.ship_list)
        self._update_ship_display()

    def _next_ship(self):
        self.ship_index = (self.ship_index + 1) % len(self.ship_list)
        self._update_ship_display()

    def _update_ship_display(self):
        ship_id = self.ship_list[self.ship_index]
        self.config['starting_ship'] = ship_id

        # Get display name
        if ship_id in self.ships_data:
            ship_def = self.ships_data[ship_id]
            display_name = ship_def.get('name', ship_id)
            self.ship_name_text.text = display_name
        else:
            self.ship_name_text.text = ship_id.replace('_', ' ').title()

        self._update_ship_info()

    def _update_ship_info(self):
        ship_id = self.ship_list[self.ship_index]
        if ship_id in self.ships_data:
            ship = self.ships_data[ship_id]
            movement = ship.get('movement', 'fly').upper()
            hp = ship.get('health', 100)
            speed = ship.get('speed', 200)
            weapons = ship.get('weapons', [])[:2]
            weapon_str = ', '.join(w.replace('_', ' ').title() for w in weapons)
            self.ship_info.text = f'[{movement}] HP:{hp} SPD:{speed} | {weapon_str}'
        else:
            self.ship_info.text = ''

    def _filter_ships(self, movement_type):
        self.current_filter = movement_type
        if movement_type is None:
            # Show all
            try:
                from models import list_all_ships
                self.ship_list = list_all_ships()
            except:
                pass
        else:
            # Filter by movement type
            self.ship_list = [
                sid for sid, sdef in self.ships_data.items()
                if sdef.get('movement') == movement_type
            ]
            if not self.ship_list:
                self.ship_list = ['fighter']

        self.ship_index = 0
        self._update_ship_display()

    def _toggle_friendly_fire(self):
        self.config['friendly_fire'] = not self.config['friendly_fire']
        if self.config['friendly_fire']:
            self.ff_button.text = 'ON'
            self.ff_button.color = color.green.tint(-0.3)
        else:
            self.ff_button.text = 'OFF'
            self.ff_button.color = color.red.tint(-0.3)

    def _on_start(self):
        self.on_start(self.config)

    def _on_cancel(self):
        self.on_cancel()

    def show(self):
        self.enabled = True
        mouse.locked = False
        mouse.visible = True

    def hide(self):
        self.enabled = False

    def get_config(self):
        return self.config.copy()


class HUD(Entity):
    """In-game heads-up display."""

    def __init__(self):
        super().__init__(parent=camera.ui)

        # Health bar background
        self.health_bg = Entity(
            parent=self,
            model='quad',
            color=color.rgb(40, 40, 40),
            scale=(0.3, 0.03),
            position=(-0.55, -0.42),
            origin=(-0.5, 0)
        )

        # Health bar fill
        self.health_bar = Entity(
            parent=self,
            model='quad',
            color=color.green,
            scale=(0.3, 0.025),
            position=(-0.55, -0.42),
            origin=(-0.5, 0),
            z=-0.01
        )

        # Health text
        self.health_text = Text(
            parent=self,
            text='100',
            scale=1.2,
            position=(-0.55, -0.38),
            origin=(-0.5, 0),
            color=color.white
        )

        # Shield bar background
        self.shield_bg = Entity(
            parent=self,
            model='quad',
            color=color.rgb(40, 40, 40),
            scale=(0.3, 0.02),
            position=(-0.55, -0.46),
            origin=(-0.5, 0)
        )

        # Shield bar fill
        self.shield_bar = Entity(
            parent=self,
            model='quad',
            color=color.rgb(150, 50, 255),  # Purple for shield
            scale=(0, 0.015),  # Start at 0 width
            position=(-0.55, -0.46),
            origin=(-0.5, 0),
            z=-0.01
        )

        # Stats (kills/deaths)
        self.stats_text = Text(
            parent=self,
            text='K: 0  D: 0',
            scale=1,
            position=(0.55, -0.42),
            origin=(0.5, 0),
            color=color.white
        )

        # Player count
        self.player_count = Text(
            parent=self,
            text='Players: 1',
            scale=1,
            position=(0, 0.45),
            origin=(0, 0),
            color=color.cyan
        )

        # Speed indicator
        self.speed_text = Text(
            parent=self,
            text='SPD: 0',
            scale=1,
            position=(-0.55, -0.35),
            origin=(-0.5, 0),
            color=color.rgb(100, 200, 255)
        )

        # Crosshair
        self.crosshair = Entity(
            parent=self,
            model='quad',
            color=color.white,
            scale=0.008
        )
        self.crosshair_h = Entity(
            parent=self,
            model='quad',
            color=color.white,
            scale=(0.02, 0.002)
        )
        self.crosshair_v = Entity(
            parent=self,
            model='quad',
            color=color.white,
            scale=(0.002, 0.02)
        )

        # Message display
        self.message = Text(
            parent=self,
            text='',
            scale=1.5,
            position=(0, 0.3),
            origin=(0, 0),
            color=color.yellow
        )
        self.message_timer = 0

        # Server info
        self.server_info = Text(
            parent=self,
            text='',
            scale=0.8,
            position=(-0.55, 0.45),
            origin=(-0.5, 0),
            color=color.light_gray
        )

        # Ship name display (top right)
        self.ship_name = Text(
            parent=self,
            text='',
            scale=1.5,
            position=(0.55, 0.42),
            origin=(0.5, 0),
            color=color.rgb(255, 215, 0)  # Gold
        )

        # Weapons display (below ship name)
        self.weapons_text = Text(
            parent=self,
            text='',
            scale=0.9,
            position=(0.55, 0.36),
            origin=(0.5, 0),
            color=color.rgb(200, 200, 200)
        )

        # Controls hint
        self.controls_hint = Text(
            parent=self,
            text='[V] View  [/[] Ship  LMB/RMB/MMB Fire',
            scale=0.7,
            position=(0, -0.48),
            origin=(0, 0),
            color=color.rgb(120, 120, 120)
        )

        self.enabled = False

    def update_health(self, health, max_health=100):
        """Update health bar display."""
        ratio = max(0, health / max_health)
        self.health_bar.scale_x = 0.3 * ratio
        self.health_text.text = str(int(health))

        # Color based on health
        if ratio > 0.6:
            self.health_bar.color = color.green
        elif ratio > 0.3:
            self.health_bar.color = color.yellow
        else:
            self.health_bar.color = color.red

    def update_shield(self, shield, max_shield=100):
        """Update shield bar display."""
        ratio = max(0, shield / max_shield)
        self.shield_bar.scale_x = 0.3 * ratio

    def update_stats(self, kills, deaths):
        """Update kill/death display."""
        self.stats_text.text = f'K: {kills}  D: {deaths}'

    def update_speed(self, speed):
        """Update speed display."""
        self.speed_text.text = f'SPD: {int(speed)}'

    def update_ship_info(self, ship_name, weapons, movement_type='fly'):
        """Update ship name, weapons, and controls hint based on vehicle type."""
        self.ship_name.text = ship_name if ship_name else 'Unknown Ship'
        if weapons:
            weapon_names = [w.replace('_', ' ').title() for w in weapons[:3]]
            self.weapons_text.text = ' | '.join(weapon_names)
        else:
            self.weapons_text.text = 'No weapons'

        # Update controls hint based on movement type
        if movement_type in ['ground', 'hover', 'train']:
            self.controls_hint.text = 'TANK: A/D Turn  Q/E Strafe  Mouse=Turret  Space=Drift  Shift=Boost'
        else:
            self.controls_hint.text = '[V] View  [/[] Ship  Mouse=Aim  WASD+QE=Move  Shift=Boost'

    def update_player_count(self, count):
        """Update player count display."""
        self.player_count.text = f'Players: {count}'

    def show_message(self, text, duration=3.0):
        """Show a temporary message."""
        self.message.text = text
        self.message_timer = duration

    def set_server_info(self, ip, port):
        """Show server IP for host."""
        self.server_info.text = f'Hosting: {ip}:{port}'

    def update(self):
        """Update message timer."""
        if self.message_timer > 0:
            self.message_timer -= time.dt
            if self.message_timer <= 0:
                self.message.text = ''

    def show(self):
        self.enabled = True

    def hide(self):
        self.enabled = False


class RespawnScreen(Entity):
    """Screen shown when player is dead."""

    def __init__(self):
        super().__init__(parent=camera.ui)

        self.bg = Entity(
            parent=self,
            model='quad',
            color=Color(0, 0, 0, 150/255),
            scale=(2, 1),
            z=0.1
        )

        self.text = Text(
            parent=self,
            text='YOU DIED',
            scale=4,
            origin=(0, 0),
            y=0.1,
            color=color.red
        )

        self.respawn_text = Text(
            parent=self,
            text='Respawning...',
            scale=2,
            origin=(0, 0),
            y=-0.05,
            color=color.white
        )

        self.enabled = False

    def show(self, killer_name=None):
        self.enabled = True
        if killer_name:
            self.text.text = f'Killed by Player {killer_name}'
        else:
            self.text.text = 'YOU DIED'

    def hide(self):
        self.enabled = False
