"""Bot AI for single player practice."""
from ursina import *
import random
import math

# Try to import ship factory, fallback to basic model if not available
try:
    from .models import ShipFactory, get_ship
    HAS_SHIP_FACTORY = True
except ImportError:
    try:
        from models import ShipFactory, get_ship
        HAS_SHIP_FACTORY = True
    except ImportError:
        HAS_SHIP_FACTORY = False

# Bot visual scale multiplier
BOT_SCALE = 20.0


class BotState:
    """Possible bot states."""
    IDLE = 'idle'
    PATROL = 'patrol'
    CHASE = 'chase'
    ATTACK = 'attack'
    EVADE = 'evade'


class Bot(Entity):
    """AI-controlled enemy ship."""

    def __init__(self, bot_id, position, arena_bounds, difficulty='medium', ship_id=None, **kwargs):
        super().__init__(**kwargs)

        self.bot_id = bot_id
        self.player_id = bot_id  # Alias for collision system compatibility
        self.arena_bounds = arena_bounds
        self.difficulty = difficulty
        self.ship_id = ship_id
        self.position = Vec3(position) if not isinstance(position, Vec3) else position

        # Set difficulty parameters (base values, may be overridden by ship)
        self._set_difficulty(difficulty)

        # Combat stats (base values)
        self.max_health = 100
        self.health = self.max_health
        self.is_alive = True
        self.last_shot_time = 0
        self.collision_radius = 2.0 * BOT_SCALE  # Hitbox scaled with bot size

        # Movement type
        self.movement_type = 'fly'  # Default, may be overridden by ship
        self.ground_y = 0  # For ground/hover units
        self.jump_cooldown = 0
        self.is_jumping = False

        # Default weapons (will be overridden by ship definition)
        self.ship_weapons = ['laser']
        self.current_weapon_index = 0

        # Movement
        self.velocity = Vec3(0, 0, 0)
        self.target_position = None
        self.target_entity = None

        # AI state
        self.state = BotState.PATROL
        self.state_timer = 0
        self.patrol_point = self._get_random_patrol_point()

        # Create visual model (uses ship_id if available)
        self._create_model()

    def _set_difficulty(self, difficulty):
        """Set AI parameters based on difficulty."""
        # Detection ranges scaled for 20x bigger arena (4000 units)
        if difficulty == 'easy':
            self.speed = 80
            self.turn_speed = 60
            self.accuracy = 0.4  # 40% accuracy
            self.reaction_time = 1.0
            self.aggression = 0.3
            self.fire_rate = 1.5  # Slower shooting
            self.detection_range = 1200  # 20x for bigger arena
        elif difficulty == 'hard':
            self.speed = 160
            self.turn_speed = 150
            self.accuracy = 0.85
            self.reaction_time = 0.2
            self.aggression = 0.8
            self.fire_rate = 0.5  # Medium-fast shooting
            self.detection_range = 2400  # 20x for bigger arena
        else:  # medium
            self.speed = 120
            self.turn_speed = 100
            self.accuracy = 0.6
            self.reaction_time = 0.5
            self.aggression = 0.5
            self.fire_rate = 0.8  # Medium shooting
            self.detection_range = 1600  # 20x for bigger arena

    def _create_model(self):
        """Create the bot's visual model using ship factory or fallback."""
        if HAS_SHIP_FACTORY and self.ship_id:
            # Use ship factory to create model
            model_data = ShipFactory.create(self, self.ship_id, BOT_SCALE)
            self.model_container = model_data['container']
            self.parts = model_data['parts']
            ship_def = model_data.get('definition', {})

            # Apply ship stats
            if ship_def:
                self.max_health = ship_def.get('health', 100)
                self.health = self.max_health
                base_scale = ship_def.get('scale', 1.0)
                self.collision_radius = 2.0 * BOT_SCALE * base_scale

                # Override speed/turn from ship definition
                self.speed = ship_def.get('speed', self.speed)
                self.turn_speed = ship_def.get('turn_speed', self.turn_speed)

                # Store ship weapons
                self.ship_weapons = ship_def.get('weapons', ['laser'])
                self.current_weapon_index = 0

                # Movement type
                self.movement_type = ship_def.get('movement', 'fly')
                if self.movement_type == 'hover':
                    self.ground_y = ship_def.get('hover_height', 50)
                elif self.movement_type == 'ground':
                    self.ground_y = 0
                elif self.movement_type == 'train':
                    self.ground_y = 0
                    # Trains are extra fast
                    self.speed *= 3
                elif self.movement_type == 'jump':
                    self.jump_force = ship_def.get('jump_force', 300)
                    self.jump_cooldown_time = ship_def.get('jump_cooldown', 2.0)
                elif self.movement_type == 'climb':
                    self.climb_speed = ship_def.get('climb_speed', 60)

                print(f"[BOT] {self.bot_id} using {ship_def.get('name')}: weapons={self.ship_weapons}")
        else:
            # Fallback: Create basic red bot model
            self.model_container = Entity(parent=self, scale=BOT_SCALE)

            # Main body - red tinted to distinguish from player
            self.body = Entity(
                parent=self.model_container,
                model='cube',
                color=Color(150/255, 50/255, 50/255, 1),
                scale=(1.2, 0.4, 2),
            )

            # Wings
            self.left_wing = Entity(
                parent=self.model_container,
                model='cube',
                color=Color(120/255, 40/255, 40/255, 1),
                scale=(2, 0.1, 1),
                position=(-1.2, 0, 0),
            )
            self.right_wing = Entity(
                parent=self.model_container,
                model='cube',
                color=Color(120/255, 40/255, 40/255, 1),
                scale=(2, 0.1, 1),
                position=(1.2, 0, 0),
            )

            # Cockpit
            self.cockpit = Entity(
                parent=self.model_container,
                model='cube',
                color=Color(80/255, 30/255, 30/255, 1),
                scale=(0.6, 0.3, 0.8),
                position=(0, 0.2, 0.5),
            )

            # Engine glow
            self.engine = Entity(
                parent=self.model_container,
                model='cube',
                color=Color(255/255, 100/255, 50/255, 1),
                scale=(0.4, 0.2, 0.3),
                position=(0, 0, -1.2),
            )

            self.parts = [self.body, self.left_wing, self.right_wing, self.cockpit, self.engine]

    def _get_random_patrol_point(self):
        """Get a random point within the arena for patrolling."""
        hx, hy, hz = self.arena_bounds
        margin = 200  # Scaled for 20x bigger arena

        # Y position depends on movement type
        if self.movement_type == 'ground':
            y_pos = -hy + 50 + self.ground_y
        elif self.movement_type == 'hover':
            y_pos = -hy + 50 + self.ground_y + random.uniform(-20, 20)
        elif self.movement_type == 'jump':
            y_pos = -hy + 50  # Ground level
        else:  # fly, climb
            y_pos = random.uniform(-hy + margin, hy - margin)

        return Vec3(
            random.uniform(-hx + margin, hx - margin),
            y_pos,
            random.uniform(-hz + margin, hz - margin)
        )

    def update(self):
        """Update bot AI and movement."""
        if not self.is_alive:
            return

        dt = time.dt

        # Update state timer
        self.state_timer += dt

        # State machine
        if self.state == BotState.PATROL:
            self._update_patrol(dt)
        elif self.state == BotState.CHASE:
            self._update_chase(dt)
        elif self.state == BotState.ATTACK:
            self._update_attack(dt)
        elif self.state == BotState.EVADE:
            self._update_evade(dt)

        # Apply movement
        self._apply_movement(dt)

        # Clamp to arena bounds
        self._clamp_to_bounds()

    def _update_patrol(self, dt):
        """Patrol behavior - move between random points."""
        if self.patrol_point is None or (self.position - self.patrol_point).length() < 50:
            self.patrol_point = self._get_random_patrol_point()
            self.state_timer = 0

        # Move towards patrol point
        self._move_towards(self.patrol_point, dt)

        # Check for player
        if self.target_entity and self.target_entity.is_alive:
            dist = (self.target_entity.position - self.position).length()
            if dist < self.detection_range:
                self.state = BotState.CHASE
                self.state_timer = 0

    def _update_chase(self, dt):
        """Chase behavior - pursue the target."""
        if not self.target_entity or not self.target_entity.is_alive:
            self.state = BotState.PATROL
            return

        target_pos = self.target_entity.position
        dist = (target_pos - self.position).length()

        # Move towards target
        self._move_towards(target_pos, dt)

        # Switch to attack if close enough
        if dist < self.detection_range * 0.6:
            self.state = BotState.ATTACK
            self.state_timer = 0

        # Give up chase if too far
        if dist > self.detection_range * 1.5:
            self.state = BotState.PATROL
            self.state_timer = 0

    def _update_attack(self, dt):
        """Attack behavior - shoot at target while maintaining distance."""
        if not self.target_entity or not self.target_entity.is_alive:
            self.state = BotState.PATROL
            return

        target_pos = self.target_entity.position
        dist = (target_pos - self.position).length()

        # Aim at target
        self._look_at_target(target_pos, dt)

        # Maintain optimal distance (scaled for 20x bigger arena/bots)
        optimal_dist = 400
        if dist < optimal_dist * 0.7:
            # Too close, back up
            away_dir = (self.position - target_pos).normalized()
            self._move_towards(self.position + away_dir * 200, dt)  # Scaled for arena
        elif dist > optimal_dist * 1.3:
            # Too far, get closer
            self._move_towards(target_pos, dt)
        else:
            # Good distance, strafe
            strafe_dir = self.right * (1 if random.random() > 0.5 else -1)
            self._move_towards(self.position + strafe_dir * 100, dt)  # Scaled for arena

        # Evade if low health
        if self.health < self.max_health * 0.3 and random.random() < self.aggression:
            self.state = BotState.EVADE
            self.state_timer = 0

        # Lost target
        if dist > self.detection_range * 1.5:
            self.state = BotState.PATROL
            self.state_timer = 0

    def _update_evade(self, dt):
        """Evade behavior - retreat and recover."""
        if not self.target_entity:
            self.state = BotState.PATROL
            return

        # Move away from target
        away_dir = (self.position - self.target_entity.position).normalized()
        evade_point = self.position + away_dir * 500  # Scaled for arena
        self._move_towards(evade_point, dt)

        # Return to attack after some time
        if self.state_timer > 3.0 or self.health > self.max_health * 0.5:
            self.state = BotState.CHASE
            self.state_timer = 0

    def _move_towards(self, target, dt):
        """Move towards a target position."""
        direction = (target - self.position)

        # For ground/hover units, only move in XZ plane
        if self.movement_type in ['ground', 'hover', 'jump', 'train']:
            direction.y = 0

        if direction.length() < 0.1:
            return

        direction = direction.normalized()

        # Accelerate towards target
        target_velocity = direction * self.speed
        if self.movement_type in ['ground', 'hover', 'jump', 'train']:
            target_velocity.y = self.velocity.y  # Preserve vertical velocity

        self.velocity = lerp(self.velocity, target_velocity, dt * 3)

        # Rotate to face movement direction (only yaw for ground units)
        if self.velocity.length() > 0.1:
            look_target = self.position + Vec3(self.velocity.x, 0, self.velocity.z)
            if self.movement_type in ['ground', 'hover', 'jump', 'train']:
                self._look_at_target_horizontal(look_target, dt)
            else:
                self._look_at_target(self.position + self.velocity, dt)

    def _look_at_target_horizontal(self, target, dt):
        """Rotate to face target (yaw only, for ground units)."""
        direction = (target - self.position)
        direction.y = 0
        if direction.length() < 0.1:
            return
        direction = direction.normalized()

        target_yaw = math.degrees(math.atan2(direction.x, direction.z))
        self.rotation_y = lerp(self.rotation_y, target_yaw, dt * self.turn_speed / 60)

    def _look_at_target(self, target, dt):
        """Rotate to face a target position."""
        direction = (target - self.position)
        if direction.length() < 0.1:
            return

        direction = direction.normalized()

        # Calculate target rotation
        target_yaw = math.degrees(math.atan2(direction.x, direction.z))
        target_pitch = math.degrees(math.asin(-direction.y))

        # Smoothly rotate
        self.rotation_y = lerp(self.rotation_y, target_yaw, dt * self.turn_speed / 60)
        self.rotation_x = lerp(self.rotation_x, target_pitch, dt * self.turn_speed / 60)

    def _apply_movement(self, dt):
        """Apply velocity to position based on movement type."""
        self.position += self.velocity * dt

        # Handle movement type specific behavior
        if self.movement_type == 'ground':
            # Stick to ground level
            self.y = -self.arena_bounds[1] + 50 + self.ground_y
            self.velocity.y = 0
            # Keep level
            self.rotation_x = 0

        elif self.movement_type == 'hover':
            # Hover at fixed height above ground
            target_y = -self.arena_bounds[1] + 50 + self.ground_y
            self.y = lerp(self.y, target_y, dt * 2)
            self.velocity.y *= 0.9  # Dampen vertical movement
            self.rotation_x = 0

        elif self.movement_type == 'jump':
            # Apply gravity when not grounded
            ground_level = -self.arena_bounds[1] + 50
            if self.y > ground_level:
                self.velocity.y -= 200 * dt  # Gravity
            else:
                self.y = ground_level
                self.velocity.y = 0
                self.is_jumping = False

            # Random jump when in combat
            if self.state == BotState.ATTACK and not self.is_jumping:
                self.jump_cooldown -= dt
                if self.jump_cooldown <= 0 and random.random() < 0.02:
                    self.velocity.y = getattr(self, 'jump_force', 300)
                    self.is_jumping = True
                    self.jump_cooldown = getattr(self, 'jump_cooldown_time', 2.0)

            self.rotation_x = 0

        elif self.movement_type == 'climb':
            # Climbing units can move on any surface
            # For now, similar to fly but can stick to walls
            pass

        elif self.movement_type == 'train':
            # Trains stick to ground, move fast, turn fast
            self.y = -self.arena_bounds[1] + 50 + self.ground_y
            self.velocity.y = 0
            self.rotation_x = 0

    def _clamp_to_bounds(self):
        """Keep bot within arena bounds."""
        if not self.arena_bounds:
            return

        hx, hy, hz = self.arena_bounds
        margin = 50  # Scaled for arena

        self.x = clamp(self.x, -hx + margin, hx - margin)
        self.z = clamp(self.z, -hz + margin, hz - margin)

        # Y clamping depends on movement type
        if self.movement_type in ['ground', 'jump', 'train']:
            ground_level = -hy + 50
            self.y = max(self.y, ground_level)
            self.y = min(self.y, hy - margin)
        elif self.movement_type == 'hover':
            ground_level = -hy + 50 + self.ground_y
            self.y = clamp(self.y, ground_level - 20, hy - margin)
        else:  # fly, climb
            self.y = clamp(self.y, -hy + margin, hy - margin)

    def can_shoot(self):
        """Check if bot can fire."""
        return self.is_alive and (time.time() - self.last_shot_time) >= self.fire_rate

    def try_shoot(self):
        """Attempt to shoot at target. Returns shot data if successful."""
        if not self.can_shoot() or not self.target_entity:
            return None

        if self.state != BotState.ATTACK:
            return None

        # Check if target is in front
        to_target = (self.target_entity.position - self.position).normalized()
        facing_dot = to_target.dot(self.forward)

        if facing_dot < 0.5:  # Not facing target enough (lowered for larger arena)
            return None

        # Calculate distance to target for aim spread
        dist_to_target = (self.target_entity.position - self.position).length()

        # Apply accuracy - always have some spread, more when missing
        # Base spread increases with distance (harder to aim far away)
        base_spread = dist_to_target * 0.05  # 5% of distance as base spread

        if random.random() > self.accuracy:
            # Miss - larger spread
            spread = base_spread * random.uniform(1.5, 3.0)
        else:
            # Hit attempt - smaller spread but still not perfect
            spread = base_spread * random.uniform(0.2, 0.6)

        # Apply random offset to aim direction
        miss_offset = Vec3(
            random.uniform(-spread, spread),
            random.uniform(-spread, spread),
            random.uniform(-spread, spread)
        )
        aim_point = self.target_entity.position + miss_offset
        direction = (aim_point - self.position).normalized()

        self.last_shot_time = time.time()

        # Select weapon from ship's weapons (randomly cycle through them)
        if hasattr(self, 'ship_weapons') and self.ship_weapons and len(self.ship_weapons) > 0:
            # Randomly pick a weapon, favoring primary
            if random.random() < 0.7:
                weapon = self.ship_weapons[0]  # 70% chance primary
            else:
                weapon = random.choice(self.ship_weapons)
        else:
            weapon = 'laser'

        return {
            'position': (self.position.x, self.position.y, self.position.z),
            'direction': (direction.x, direction.y, direction.z),
            'owner_id': self.bot_id,
            'weapon': weapon
        }

    def set_target(self, entity):
        """Set the bot's target entity."""
        self.target_entity = entity

    def take_damage(self, amount, attacker_id=None):
        """Apply damage to the bot."""
        if not self.is_alive:
            return False

        self.health -= amount

        # Flash red - store original colors first to avoid closure issues
        original_colors = [(part, Color(part.color.r, part.color.g, part.color.b, part.color.a)) for part in self.parts]
        for part in self.parts:
            part.color = color.red

        # Restore colors after delay
        def restore_colors():
            for part, orig_color in original_colors:
                if part and hasattr(part, 'color'):
                    part.color = orig_color

        invoke(restore_colors, delay=0.1)

        # Become more aggressive when hit
        if self.state == BotState.PATROL:
            self.state = BotState.CHASE

        if self.health <= 0:
            self.die()
            return True
        return False

    def die(self):
        """Bot death."""
        self.is_alive = False
        self.velocity = Vec3(0, 0, 0)
        for part in self.parts:
            part.visible = False

    def respawn(self, position=None):
        """Respawn the bot."""
        if position:
            self.position = Vec3(position) if not isinstance(position, Vec3) else position
        else:
            self.position = self._get_random_patrol_point()

        self.health = self.max_health
        self.is_alive = True
        self.state = BotState.PATROL
        self.velocity = Vec3(0, 0, 0)

        for part in self.parts:
            part.visible = True

    def get_state(self):
        """Get bot state for display/network."""
        return {
            'bot_id': self.bot_id,
            'position': (self.position.x, self.position.y, self.position.z),
            'rotation': (self.rotation_x, self.rotation_y, self.rotation_z),
            'health': self.health,
            'is_alive': self.is_alive,
            'state': self.state
        }


class BotManager:
    """Manages multiple bots in the game."""

    def __init__(self, arena_bounds, difficulty='medium'):
        self.arena_bounds = arena_bounds
        self.difficulty = difficulty
        self.bots = {}
        self.next_bot_id = 1000  # Start bot IDs high to avoid player ID conflicts
        self.respawn_queue = []
        self.respawn_delay = 5.0
        self.bot_ship_ids = {}  # Track which ship each bot uses

    def spawn_bot(self, position=None, ship_id=None):
        """Spawn a new bot with optional ship type."""
        bot_id = self.next_bot_id
        self.next_bot_id += 1

        # Pick random ship if none specified
        if ship_id is None and HAS_SHIP_FACTORY:
            ship_id = ShipFactory.get_random_ship()

        if position is None:
            hx, hy, hz = self.arena_bounds
            # For ground/hover units, spawn on ground level
            if HAS_SHIP_FACTORY and ship_id:
                ship_def = get_ship(ship_id)
                movement = ship_def.get('movement', 'fly') if ship_def else 'fly'
                if movement == 'ground' or movement == 'train':
                    y_pos = -hy + 100  # Near ground
                elif movement == 'hover':
                    y_pos = -hy + 100 + ship_def.get('hover_height', 50)
                elif movement in ['jump', 'climb']:
                    y_pos = -hy + 150  # Slightly above ground
                else:
                    y_pos = random.uniform(-hy + 100, hy - 100)
            else:
                y_pos = random.uniform(-hy + 100, hy - 100)

            position = Vec3(
                random.uniform(-hx + 300, hx - 300),
                y_pos,
                random.uniform(-hz + 300, hz - 300)
            )

        bot = Bot(bot_id, position, self.arena_bounds, self.difficulty, ship_id=ship_id)
        self.bots[bot_id] = bot
        self.bot_ship_ids[bot_id] = ship_id

        ship_name = ship_id if ship_id else "default"
        print(f"[BOT] Spawned bot {bot_id} ({ship_name}) at {position}")
        return bot

    def spawn_bots(self, count, ship_ids=None):
        """Spawn multiple bots with optional ship type list."""
        for i in range(count):
            ship_id = ship_ids[i % len(ship_ids)] if ship_ids else None
            self.spawn_bot(ship_id=ship_id)

    def set_target_for_all(self, target_entity):
        """Set the same target for all bots."""
        for bot in self.bots.values():
            bot.set_target(target_entity)

    def update(self):
        """Update all bots and handle respawning."""
        current_time = time.time()

        # Update bots
        for bot in self.bots.values():
            bot.update()

        # Handle respawn queue
        new_queue = []
        for respawn_time, bot_id in self.respawn_queue:
            if current_time >= respawn_time:
                if bot_id in self.bots:
                    self.bots[bot_id].respawn()
                    print(f"[BOT] Respawned bot {bot_id}")
            else:
                new_queue.append((respawn_time, bot_id))
        self.respawn_queue = new_queue

    def get_bot_shots(self):
        """Get shots from all bots that want to fire."""
        shots = []
        for bot in self.bots.values():
            shot = bot.try_shoot()
            if shot:
                shots.append(shot)
        return shots

    def handle_bot_death(self, bot_id):
        """Handle a bot dying - queue respawn."""
        if bot_id in self.bots:
            respawn_time = time.time() + self.respawn_delay
            self.respawn_queue.append((respawn_time, bot_id))
            print(f"[BOT] Bot {bot_id} died, respawning in {self.respawn_delay}s")

    def damage_bot(self, bot_id, damage, attacker_id=None):
        """Apply damage to a specific bot."""
        if bot_id in self.bots:
            died = self.bots[bot_id].take_damage(damage, attacker_id)
            if died:
                self.handle_bot_death(bot_id)
            return died
        return False

    def get_all_bots(self):
        """Get all bots as a dict."""
        return self.bots

    def cleanup(self):
        """Destroy all bots."""
        for bot in self.bots.values():
            destroy(bot)
        self.bots.clear()
        self.respawn_queue.clear()
