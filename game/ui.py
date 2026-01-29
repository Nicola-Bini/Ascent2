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

    def __init__(self, on_connect, on_cancel):
        super().__init__(parent=camera.ui)

        self.on_connect = on_connect
        self.on_cancel = on_cancel

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
            default_value='192.168.1.',
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

    def update_stats(self, kills, deaths):
        """Update kill/death display."""
        self.stats_text.text = f'K: {kills}  D: {deaths}'

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
