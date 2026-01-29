"""Audio system for sound effects and music."""
import os
import math
import struct
import wave
from pathlib import Path

# Audio directory
AUDIO_DIR = Path(__file__).parent / "sounds"
AUDIO_DIR.mkdir(exist_ok=True)


def generate_sine_wave(frequency, duration, sample_rate=44100, volume=0.5):
    """Generate a sine wave."""
    samples = int(sample_rate * duration)
    data = []
    for i in range(samples):
        t = i / sample_rate
        value = volume * math.sin(2 * math.pi * frequency * t)
        data.append(value)
    return data


def generate_noise(duration, sample_rate=44100, volume=0.3):
    """Generate white noise."""
    import random
    samples = int(sample_rate * duration)
    return [volume * (random.random() * 2 - 1) for _ in range(samples)]


def apply_envelope(data, attack=0.01, decay=0.1, sustain=0.7, release=0.2):
    """Apply ADSR envelope to audio data."""
    total = len(data)
    attack_samples = int(total * attack)
    decay_samples = int(total * decay)
    release_samples = int(total * release)
    sustain_samples = total - attack_samples - decay_samples - release_samples

    result = []
    for i, sample in enumerate(data):
        if i < attack_samples:
            # Attack phase
            env = i / attack_samples if attack_samples > 0 else 1
        elif i < attack_samples + decay_samples:
            # Decay phase
            progress = (i - attack_samples) / decay_samples if decay_samples > 0 else 0
            env = 1 - (1 - sustain) * progress
        elif i < attack_samples + decay_samples + sustain_samples:
            # Sustain phase
            env = sustain
        else:
            # Release phase
            progress = (i - attack_samples - decay_samples - sustain_samples) / release_samples
            env = sustain * (1 - progress) if release_samples > 0 else 0
        result.append(sample * env)
    return result


def apply_pitch_sweep(data, start_freq, end_freq, sample_rate=44100):
    """Apply a pitch sweep effect."""
    total = len(data)
    result = []
    for i in range(total):
        t = i / sample_rate
        progress = i / total
        freq = start_freq + (end_freq - start_freq) * progress
        phase = 2 * math.pi * freq * t
        result.append(data[i] * math.sin(phase) if i < len(data) else 0)
    return result


def mix_audio(*tracks):
    """Mix multiple audio tracks together."""
    max_len = max(len(t) for t in tracks)
    result = [0] * max_len
    for track in tracks:
        for i, sample in enumerate(track):
            result[i] += sample
    # Normalize
    max_val = max(abs(s) for s in result) if result else 1
    if max_val > 1:
        result = [s / max_val for s in result]
    return result


def save_wav(data, filename, sample_rate=44100):
    """Save audio data as WAV file."""
    filepath = AUDIO_DIR / filename
    with wave.open(str(filepath), 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # Convert to 16-bit integers
        for sample in data:
            # Clamp to [-1, 1]
            sample = max(-1, min(1, sample))
            # Convert to 16-bit integer
            int_sample = int(sample * 32767)
            wav_file.writeframes(struct.pack('<h', int_sample))

    print(f"[AUDIO] Generated: {filename}")
    return str(filepath)


def generate_laser_sound():
    """Generate a sci-fi laser sound effect."""
    duration = 0.15
    sample_rate = 44100
    samples = int(sample_rate * duration)

    data = []
    for i in range(samples):
        t = i / sample_rate
        progress = i / samples

        # Descending pitch from 2000Hz to 800Hz
        freq = 2000 - 1200 * progress

        # Mix of sine and square wave for harsh sound
        sine = math.sin(2 * math.pi * freq * t)
        square = 1 if sine > 0 else -1

        # Mix 70% sine, 30% square
        sample = 0.7 * sine + 0.3 * square

        # Envelope: quick attack, quick decay
        env = 1 - progress
        data.append(sample * env * 0.4)

    return save_wav(data, "laser.wav")


def generate_missile_sound():
    """Generate a missile launch sound effect."""
    duration = 0.4
    sample_rate = 44100
    samples = int(sample_rate * duration)

    data = []
    import random
    random.seed(42)  # Consistent sound

    for i in range(samples):
        t = i / sample_rate
        progress = i / samples

        # Low rumble with rising pitch
        freq = 80 + 120 * progress

        # Base rumble
        rumble = math.sin(2 * math.pi * freq * t)

        # Add noise
        noise = random.random() * 2 - 1

        # Whoosh effect (rising)
        whoosh_freq = 200 + 800 * progress
        whoosh = math.sin(2 * math.pi * whoosh_freq * t) * 0.3

        sample = rumble * 0.5 + noise * 0.3 + whoosh

        # Envelope
        env = min(1, progress * 4) * (1 - progress * 0.5)
        data.append(sample * env * 0.5)

    return save_wav(data, "missile.wav")


def generate_explosion_sound():
    """Generate an explosion sound effect."""
    duration = 0.6
    sample_rate = 44100
    samples = int(sample_rate * duration)

    data = []
    import random
    random.seed(123)

    for i in range(samples):
        t = i / sample_rate
        progress = i / samples

        # Low boom
        boom_freq = 60 * (1 - progress * 0.5)
        boom = math.sin(2 * math.pi * boom_freq * t)

        # Noise burst
        noise = random.random() * 2 - 1

        # Crackle
        crackle = math.sin(2 * math.pi * 800 * t * (1 + random.random()))

        sample = boom * 0.6 + noise * 0.3 + crackle * 0.1

        # Quick attack, long decay envelope
        if progress < 0.05:
            env = progress / 0.05
        else:
            env = (1 - progress) ** 1.5

        data.append(sample * env * 0.6)

    return save_wav(data, "explosion.wav")


def generate_hit_sound():
    """Generate a hit/damage sound effect."""
    duration = 0.1
    sample_rate = 44100
    samples = int(sample_rate * duration)

    data = []
    for i in range(samples):
        t = i / sample_rate
        progress = i / samples

        # Sharp metallic impact
        freq1 = 400 * (1 - progress * 0.3)
        freq2 = 600 * (1 - progress * 0.5)

        sample = (math.sin(2 * math.pi * freq1 * t) +
                  math.sin(2 * math.pi * freq2 * t) * 0.5)

        # Very quick decay
        env = (1 - progress) ** 2
        data.append(sample * env * 0.4)

    return save_wav(data, "hit.wav")


def generate_engine_sound():
    """Generate a looping engine/thruster sound."""
    duration = 1.0  # 1 second loop
    sample_rate = 44100
    samples = int(sample_rate * duration)

    data = []
    import random
    random.seed(456)

    for i in range(samples):
        t = i / sample_rate

        # Low hum
        hum = math.sin(2 * math.pi * 50 * t) * 0.3

        # Oscillating mid frequency
        mid = math.sin(2 * math.pi * 120 * t) * math.sin(2 * math.pi * 2 * t) * 0.2

        # Subtle noise
        noise = (random.random() * 2 - 1) * 0.1

        sample = hum + mid + noise
        data.append(sample * 0.3)

    return save_wav(data, "engine.wav")


def generate_ambient_music():
    """Generate ambient background music."""
    duration = 30.0  # 30 second loop
    sample_rate = 44100
    samples = int(sample_rate * duration)

    data = []
    import random
    random.seed(789)

    # Chord frequencies (Am chord with extensions)
    base_freq = 110  # A2
    chord = [1, 1.2, 1.5, 2, 2.4, 3]  # Minor chord with octave

    for i in range(samples):
        t = i / sample_rate
        progress = i / samples

        sample = 0

        # Slow evolving pad sound
        for j, ratio in enumerate(chord):
            freq = base_freq * ratio
            # Slow modulation
            mod = math.sin(2 * math.pi * 0.1 * t + j)
            wave = math.sin(2 * math.pi * freq * t + mod)
            sample += wave * 0.1

        # Add subtle bass pulse
        bass_freq = base_freq / 2
        bass = math.sin(2 * math.pi * bass_freq * t)
        bass_env = (math.sin(2 * math.pi * 0.25 * t) + 1) / 2  # Pulse every 4 seconds
        sample += bass * bass_env * 0.15

        # Very subtle noise texture
        noise = (random.random() * 2 - 1) * 0.02

        sample += noise

        # Global volume envelope for seamless loop
        if i < sample_rate:  # Fade in first second
            sample *= i / sample_rate
        elif i > samples - sample_rate:  # Fade out last second
            sample *= (samples - i) / sample_rate

        data.append(sample * 0.4)

    return save_wav(data, "ambient_music.wav")


def generate_menu_music():
    """Generate menu background music."""
    duration = 20.0
    sample_rate = 44100
    samples = int(sample_rate * duration)

    data = []

    # Simple arpeggio pattern
    notes = [220, 277.18, 329.63, 440, 329.63, 277.18]  # Am arpeggio
    note_duration = 0.5
    note_samples = int(sample_rate * note_duration)

    for i in range(samples):
        t = i / sample_rate
        note_index = int(t / note_duration) % len(notes)
        freq = notes[note_index]

        # Position within note
        note_pos = (i % note_samples) / note_samples

        # Soft sine wave
        wave = math.sin(2 * math.pi * freq * t)

        # Note envelope
        if note_pos < 0.1:
            env = note_pos / 0.1
        else:
            env = 1 - (note_pos - 0.1) * 0.8

        # Add octave
        wave += math.sin(2 * math.pi * freq * 2 * t) * 0.3

        sample = wave * env * 0.2

        # Fade in/out for looping
        if i < sample_rate:
            sample *= i / sample_rate
        elif i > samples - sample_rate:
            sample *= (samples - i) / sample_rate

        data.append(sample)

    return save_wav(data, "menu_music.wav")


def generate_all_sounds():
    """Generate all sound effects and music."""
    print("[AUDIO] Generating sound effects...")

    sounds = {
        'laser': generate_laser_sound(),
        'missile': generate_missile_sound(),
        'explosion': generate_explosion_sound(),
        'hit': generate_hit_sound(),
        'engine': generate_engine_sound(),
        'ambient_music': generate_ambient_music(),
        'menu_music': generate_menu_music(),
    }

    print(f"[AUDIO] Generated {len(sounds)} audio files in {AUDIO_DIR}")
    return sounds


class AudioManager:
    """Manages game audio playback."""

    def __init__(self):
        self.sounds = {}
        self.music_volume = 0.5
        self.sfx_volume = 0.7
        self.current_music = None

        # Generate sounds if they don't exist
        self._ensure_sounds_exist()

    def _ensure_sounds_exist(self):
        """Make sure all sound files exist."""
        required = ['laser.wav', 'missile.wav', 'explosion.wav', 'hit.wav',
                    'engine.wav', 'ambient_music.wav', 'menu_music.wav']

        for filename in required:
            if not (AUDIO_DIR / filename).exists():
                print(f"[AUDIO] Missing {filename}, generating all sounds...")
                generate_all_sounds()
                break

    def get_sound_path(self, name):
        """Get the path to a sound file."""
        return str(AUDIO_DIR / f"{name}.wav")

    def play_sfx(self, name):
        """Play a sound effect (to be called from Ursina)."""
        # This returns the path; actual playback happens in game code
        return self.get_sound_path(name)

    def get_music_path(self, name):
        """Get path to music file."""
        return self.get_sound_path(name)


# Generate sounds when module is imported
if __name__ == "__main__":
    generate_all_sounds()
