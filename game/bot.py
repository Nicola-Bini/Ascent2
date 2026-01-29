"""Bot AI for single player practice."""
from ursina import *
import random
import math

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

    def __init__(self, bot_id, position, arena_bounds, difficulty='medium', **kwargs):
        super().__init__(**kwargs)

        self.bot_id = bot_id
        self.player_id = bot_id  # Alias for collision system compatibility
        self.arena_bounds = arena_bounds
        self.difficulty = difficulty
        self.position = Vec3(position) if not isinstance(position, Vec3) else position

        # Set difficulty parameters
        self._set_difficulty(difficulty)

        # Combat stats
        self.max_health = 100
        self.health = self.max_health
        self.is_alive = True
        self.last_shot_time = 0

        # Movement
        self.velocity = Vec3(0, 0, 0)
        self.target_position = None
        self.target_entity = None

        # AI state
        self.state = BotState.PATROL
        self.state_timer = 0
        self.patrol_point = self._get_random_patrol_point()

        # Create visual model
        self._create_model()

    def _set_difficulty(self, difficulty):
        """Set AI parameters based on difficulty."""
        if difficulty == 'easy':
            self.speed = 20
            self.turn_speed = 60
            self.accuracy = 0.4  # 40% accuracy
            self.reaction_time = 1.0
            self.aggression = 0.3
            self.fire_rate = 0.4  # Shoots faster
            self.detection_range = 60
        elif difficulty == 'hard':
            self.speed = 40
            self.turn_speed = 150
            self.accuracy = 0.85
            self.reaction_time = 0.2
            self.aggression = 0.8
            self.fire_rate = 0.08  # Very fast shooting
            self.detection_range = 120
        else:  # medium
            self.speed = 30
            self.turn_speed = 100
            self.accuracy = 0.6
            self.reaction_time = 0.5
            self.aggression = 0.5
            self.fire_rate = 0.15  # Shoots much faster
            self.detection_range = 80

    def _create_model(self):
        """Create the bot's visual model."""
        # Container for scaling (20x bigger)
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
        margin = 20
        return Vec3(
            random.uniform(-hx + margin, hx - margin),
            random.uniform(-hy + margin, hy - margin),
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
        if self.patrol_point is None or (self.position - self.patrol_point).length() < 5:
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

        # Maintain optimal distance
        optimal_dist = 30
        if dist < optimal_dist * 0.7:
            # Too close, back up
            away_dir = (self.position - target_pos).normalized()
            self._move_towards(self.position + away_dir * 20, dt)
        elif dist > optimal_dist * 1.3:
            # Too far, get closer
            self._move_towards(target_pos, dt)
        else:
            # Good distance, strafe
            strafe_dir = self.right * (1 if random.random() > 0.5 else -1)
            self._move_towards(self.position + strafe_dir * 10, dt)

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
        evade_point = self.position + away_dir * 50
        self._move_towards(evade_point, dt)

        # Return to attack after some time
        if self.state_timer > 3.0 or self.health > self.max_health * 0.5:
            self.state = BotState.CHASE
            self.state_timer = 0

    def _move_towards(self, target, dt):
        """Move towards a target position."""
        direction = (target - self.position).normalized()

        # Accelerate towards target
        target_velocity = direction * self.speed
        self.velocity = lerp(self.velocity, target_velocity, dt * 3)

        # Rotate to face movement direction
        if self.velocity.length() > 0.1:
            self._look_at_target(self.position + self.velocity, dt)

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
        """Apply velocity to position."""
        self.position += self.velocity * dt

    def _clamp_to_bounds(self):
        """Keep bot within arena bounds."""
        if not self.arena_bounds:
            return

        hx, hy, hz = self.arena_bounds
        margin = 5

        self.x = clamp(self.x, -hx + margin, hx - margin)
        self.y = clamp(self.y, -hy + margin, hy - margin)
        self.z = clamp(self.z, -hz + margin, hz - margin)

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

        if facing_dot < 0.7:  # Not facing target enough
            return None

        # Apply accuracy (random miss chance)
        if random.random() > self.accuracy:
            # Miss - shoot slightly off target
            miss_offset = Vec3(
                random.uniform(-5, 5),
                random.uniform(-5, 5),
                random.uniform(-5, 5)
            )
            direction = (self.target_entity.position + miss_offset - self.position).normalized()
        else:
            # Hit - aim directly at target (with slight prediction)
            direction = to_target

        self.last_shot_time = time.time()

        return {
            'position': (self.position.x, self.position.y, self.position.z),
            'direction': (direction.x, direction.y, direction.z),
            'owner_id': self.bot_id,
            'weapon': 'primary'
        }

    def set_target(self, entity):
        """Set the bot's target entity."""
        self.target_entity = entity

    def take_damage(self, amount, attacker_id=None):
        """Apply damage to the bot."""
        if not self.is_alive:
            return False

        self.health -= amount

        # Flash red
        for part in self.parts:
            original_color = part.color
            part.color = color.red
            invoke(setattr, part, 'color', original_color, delay=0.1)

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

    def spawn_bot(self, position=None):
        """Spawn a new bot."""
        bot_id = self.next_bot_id
        self.next_bot_id += 1

        if position is None:
            hx, hy, hz = self.arena_bounds
            position = Vec3(
                random.uniform(-hx + 30, hx - 30),
                random.uniform(-hy + 10, hy - 10),
                random.uniform(-hz + 30, hz - 30)
            )

        bot = Bot(bot_id, position, self.arena_bounds, self.difficulty)
        self.bots[bot_id] = bot

        print(f"[BOT] Spawned bot {bot_id} at {position}")
        return bot

    def spawn_bots(self, count):
        """Spawn multiple bots."""
        for _ in range(count):
            self.spawn_bot()

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
