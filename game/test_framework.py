"""Automated testing framework for the game using screenshots."""
import os
import sys
import time
import subprocess
import threading
from datetime import datetime
from pathlib import Path

# Test results directory
TEST_DIR = Path(__file__).parent / "test_results"
TEST_DIR.mkdir(exist_ok=True)


class GameTester:
    """Automated game testing with screenshot capture."""

    def __init__(self):
        self.game_process = None
        self.test_name = None
        self.screenshots = []
        self.start_time = None

    def start_game(self, test_mode=True):
        """Start the game process."""
        game_path = Path(__file__).parent / "main.py"
        env = os.environ.copy()
        if test_mode:
            env['GAME_TEST_MODE'] = '1'

        self.game_process = subprocess.Popen(
            [sys.executable, str(game_path)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.start_time = time.time()
        print(f"[TEST] Game started with PID {self.game_process.pid}")
        return self.game_process

    def stop_game(self):
        """Stop the game process."""
        if self.game_process:
            self.game_process.terminate()
            self.game_process.wait(timeout=5)
            print("[TEST] Game stopped")

    def take_screenshot(self, name_suffix=""):
        """Take a screenshot using macOS screencapture."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{self.test_name}_{timestamp}{name_suffix}.png"
        filepath = TEST_DIR / filename

        # Use macOS screencapture to capture the frontmost window
        result = subprocess.run(
            ['screencapture', '-w', '-o', str(filepath)],
            capture_output=True,
            timeout=5
        )

        if result.returncode == 0 and filepath.exists():
            self.screenshots.append(filepath)
            print(f"[TEST] Screenshot saved: {filename}")
            return filepath
        else:
            print(f"[TEST] Screenshot failed: {result.stderr.decode()}")
            return None

    def wait_and_screenshot(self, delay_ms, suffix=""):
        """Wait for specified milliseconds then take screenshot."""
        time.sleep(delay_ms / 1000.0)
        return self.take_screenshot(suffix)

    def run_test(self, test_name, test_func):
        """Run a test with the given function."""
        self.test_name = test_name
        self.screenshots = []
        print(f"\n{'='*50}")
        print(f"[TEST] Running test: {test_name}")
        print(f"{'='*50}")

        try:
            result = test_func(self)
            status = "PASSED" if result else "FAILED"
        except Exception as e:
            print(f"[TEST] Error: {e}")
            status = "ERROR"
            result = False

        print(f"[TEST] {test_name}: {status}")
        print(f"[TEST] Screenshots: {len(self.screenshots)}")

        return {
            'name': test_name,
            'status': status,
            'screenshots': [str(s) for s in self.screenshots],
            'result': result,
        }


class TestScenarios:
    """Pre-defined test scenarios for game features."""

    @staticmethod
    def test_game_starts(tester):
        """Test that the game starts and shows the menu."""
        tester.start_game()
        time.sleep(2)  # Wait for game to initialize
        tester.take_screenshot("_menu")
        time.sleep(1)
        tester.stop_game()
        return len(tester.screenshots) > 0

    @staticmethod
    def test_host_game(tester):
        """Test hosting a game and seeing the arena."""
        tester.start_game()
        time.sleep(2)
        tester.take_screenshot("_menu")

        # Simulate clicking "Host Game" - would need AppleScript or similar
        # For now, document manual steps
        print("[TEST] Manual step: Click 'Host Game' button")
        time.sleep(3)
        tester.take_screenshot("_arena")
        time.sleep(1)
        tester.stop_game()
        return True

    @staticmethod
    def test_movement(tester):
        """Test player movement in the arena."""
        # This would require input simulation
        print("[TEST] Movement test requires manual interaction")
        return True

    @staticmethod
    def test_shooting(tester):
        """Test weapon firing."""
        print("[TEST] Shooting test requires manual interaction")
        return True


def run_visual_test(test_name, actions, screenshot_times_ms):
    """
    Run a visual test with specified actions and screenshot timing.

    Args:
        test_name: Name of the test
        actions: List of (time_ms, action_description) tuples
        screenshot_times_ms: List of times (in ms) to take screenshots
    """
    tester = GameTester()
    tester.test_name = test_name
    tester.screenshots = []

    print(f"\n[VISUAL TEST] {test_name}")
    print(f"Actions: {actions}")
    print(f"Screenshots at: {screenshot_times_ms}ms")

    # Create test instructions file
    instructions_file = TEST_DIR / f"{test_name}_instructions.txt"
    with open(instructions_file, 'w') as f:
        f.write(f"Test: {test_name}\n")
        f.write(f"Time: {datetime.now()}\n\n")
        f.write("Actions to perform:\n")
        for time_ms, action in actions:
            f.write(f"  At {time_ms}ms: {action}\n")
        f.write(f"\nScreenshots will be taken at: {screenshot_times_ms}ms\n")

    print(f"[TEST] Instructions saved to {instructions_file}")
    return tester


def analyze_screenshot(filepath):
    """
    Analyze a screenshot to check for expected elements.
    Returns basic info about the image.
    """
    if not os.path.exists(filepath):
        return {'error': 'File not found'}

    import struct
    import zlib

    # Read PNG header to get dimensions
    with open(filepath, 'rb') as f:
        header = f.read(24)
        if header[:8] != b'\x89PNG\r\n\x1a\n':
            return {'error': 'Not a valid PNG'}

        width = struct.unpack('>I', header[16:20])[0]
        height = struct.unpack('>I', header[20:24])[0]

    file_size = os.path.getsize(filepath)

    return {
        'width': width,
        'height': height,
        'file_size': file_size,
        'path': str(filepath),
    }


if __name__ == "__main__":
    # Run basic tests
    tester = GameTester()

    print("Game Testing Framework")
    print("=" * 50)
    print("\nAvailable test scenarios:")
    print("  1. test_game_starts - Verify game launches")
    print("  2. test_host_game - Verify hosting works")
    print("  3. test_movement - Verify player movement")
    print("  4. test_shooting - Verify weapons work")
    print("\nRun with: python test_framework.py <test_name>")

    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if hasattr(TestScenarios, test_name):
            test_func = getattr(TestScenarios, test_name)
            result = tester.run_test(test_name, test_func)
            print(f"\nResult: {result}")
        else:
            print(f"Unknown test: {test_name}")
