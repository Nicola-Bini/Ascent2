"""
Automated game tester using AppleScript for macOS.
This can simulate clicks, key presses, and take screenshots.
"""
import os
import sys
import time
import subprocess
import json
from datetime import datetime
from pathlib import Path

TEST_RESULTS_DIR = Path(__file__).parent / "test_results"
TEST_RESULTS_DIR.mkdir(exist_ok=True)


def run_applescript(script):
    """Run an AppleScript and return the result."""
    result = subprocess.run(
        ['osascript', '-e', script],
        capture_output=True,
        text=True,
        timeout=10
    )
    return result.stdout.strip(), result.returncode


def activate_app(app_name="python"):
    """Bring the game window to front."""
    script = f'''
    tell application "System Events"
        set frontmost of (first process whose name contains "{app_name}") to true
    end tell
    '''
    return run_applescript(script)


def press_key(key):
    """Simulate a key press."""
    # Map common keys to AppleScript key codes
    key_map = {
        'w': 'w', 's': 's', 'a': 'a', 'd': 'd',
        'space': 'space', 'escape': 'escape',
        'return': 'return', 'tab': 'tab',
        'q': 'q', 'e': 'e', 'shift': 'shift',
    }

    key_to_press = key_map.get(key.lower(), key)

    if key_to_press in ['space', 'escape', 'return', 'tab', 'shift']:
        script = f'''
        tell application "System Events"
            key code {get_key_code(key_to_press)}
        end tell
        '''
    else:
        script = f'''
        tell application "System Events"
            keystroke "{key_to_press}"
        end tell
        '''
    return run_applescript(script)


def get_key_code(key_name):
    """Get macOS key code for special keys."""
    codes = {
        'space': 49,
        'escape': 53,
        'return': 36,
        'tab': 48,
        'shift': 56,
        'control': 59,
        'option': 58,
        'command': 55,
    }
    return codes.get(key_name, 0)


def hold_key(key, duration_ms):
    """Hold a key for specified duration."""
    script = f'''
    tell application "System Events"
        key down "{key}"
        delay {duration_ms / 1000.0}
        key up "{key}"
    end tell
    '''
    return run_applescript(script)


def click_at(x, y):
    """Click at screen coordinates."""
    script = f'''
    tell application "System Events"
        click at {{{x}, {y}}}
    end tell
    '''
    return run_applescript(script)


def mouse_click(button="left"):
    """Click mouse button at current position."""
    if button == "left":
        script = '''
        tell application "System Events"
            click
        end tell
        '''
    else:
        script = '''
        tell application "System Events"
            click with control down
        end tell
        '''
    return run_applescript(script)


def take_screenshot(test_name, suffix=""):
    """Take a screenshot of the frontmost window."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filename = f"{test_name}_{timestamp}{suffix}.png"
    filepath = TEST_RESULTS_DIR / filename

    # Capture the frontmost window
    result = subprocess.run(
        ['screencapture', '-l', get_frontmost_window_id(), str(filepath)],
        capture_output=True,
        timeout=5
    )

    # Fallback to interactive window capture
    if result.returncode != 0 or not filepath.exists():
        result = subprocess.run(
            ['screencapture', '-x', str(filepath)],
            capture_output=True,
            timeout=5
        )

    if filepath.exists():
        print(f"[SCREENSHOT] {filename}")
        return str(filepath)
    return None


def get_frontmost_window_id():
    """Get the window ID of the frontmost window."""
    script = '''
    tell application "System Events"
        set frontApp to first application process whose frontmost is true
        set frontWindow to first window of frontApp
        return id of frontWindow
    end tell
    '''
    result, _ = run_applescript(script)
    return result if result else "0"


def start_game():
    """Start the game process."""
    game_path = Path(__file__).parent / "main.py"
    venv_python = Path(__file__).parent.parent / "game_env" / "bin" / "python"

    if venv_python.exists():
        python_exec = str(venv_python)
    else:
        python_exec = sys.executable

    process = subprocess.Popen(
        [python_exec, str(game_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(f"[GAME] Started with PID {process.pid}")
    return process


def stop_game(process):
    """Stop the game process."""
    if process:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        print("[GAME] Stopped")


class VisualTest:
    """A visual test that can be run and verified."""

    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.screenshots = []
        self.results = []
        self.game_process = None

    def start(self):
        """Start the game for testing."""
        print(f"\n{'='*60}")
        print(f"[TEST] {self.name}")
        print(f"[DESC] {self.description}")
        print('='*60)

        self.game_process = start_game()
        time.sleep(3)  # Wait for game to initialize
        activate_app("Descent")  # Game window title contains "Descent"
        time.sleep(0.5)

    def screenshot(self, suffix=""):
        """Take a screenshot."""
        path = take_screenshot(self.name, suffix)
        if path:
            self.screenshots.append(path)
        return path

    def wait(self, ms):
        """Wait for specified milliseconds."""
        time.sleep(ms / 1000.0)

    def key(self, key_name):
        """Press a key."""
        press_key(key_name)
        time.sleep(0.05)

    def hold(self, key_name, duration_ms):
        """Hold a key for duration."""
        hold_key(key_name, duration_ms)

    def click(self, button="left"):
        """Click mouse button."""
        mouse_click(button)
        time.sleep(0.05)

    def finish(self):
        """Finish the test and save results."""
        stop_game(self.game_process)

        result = {
            'name': self.name,
            'description': self.description,
            'timestamp': datetime.now().isoformat(),
            'screenshots': self.screenshots,
            'screenshot_count': len(self.screenshots),
        }

        # Save test result
        result_file = TEST_RESULTS_DIR / f"{self.name}_result.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"\n[RESULT] Test completed: {self.name}")
        print(f"[RESULT] Screenshots: {len(self.screenshots)}")
        print(f"[RESULT] Saved to: {result_file}")

        return result


# Pre-defined tests
def test_menu_display():
    """Test that the main menu displays correctly."""
    test = VisualTest("menu_display", "Verify main menu shows correctly")
    test.start()
    test.wait(2000)
    test.screenshot("_menu")
    test.finish()
    return test


def test_host_game():
    """Test hosting a game and viewing the arena."""
    test = VisualTest("host_game", "Host a game and verify arena displays")
    test.start()
    test.wait(2000)
    test.screenshot("_01_menu")

    # Click Host Game button (approximate position)
    # The button should be in the center of the screen
    test.key("return")  # Try pressing enter to select
    test.wait(500)
    test.key("return")
    test.wait(2000)
    test.screenshot("_02_arena")

    # Look around
    test.wait(500)
    test.screenshot("_03_looking")

    test.finish()
    return test


def test_movement():
    """Test player movement."""
    test = VisualTest("movement", "Test WASD movement in arena")
    test.start()
    test.wait(2000)

    # Host game
    test.key("return")
    test.wait(500)
    test.key("return")
    test.wait(2000)
    test.screenshot("_01_start")

    # Move forward
    test.hold("w", 1000)
    test.wait(100)
    test.screenshot("_02_forward")

    # Strafe right
    test.hold("d", 500)
    test.wait(100)
    test.screenshot("_03_strafe")

    # Move up
    test.hold("space", 500)
    test.wait(100)
    test.screenshot("_04_up")

    test.finish()
    return test


def test_shooting():
    """Test weapon firing."""
    test = VisualTest("shooting", "Test primary and secondary weapons")
    test.start()
    test.wait(2000)

    # Host game
    test.key("return")
    test.wait(500)
    test.key("return")
    test.wait(2000)
    test.screenshot("_01_start")

    # Primary fire
    test.click("left")
    test.wait(100)
    test.screenshot("_02_primary_100ms")
    test.wait(100)
    test.screenshot("_03_primary_200ms")
    test.wait(100)
    test.screenshot("_04_primary_300ms")

    # Secondary fire
    test.click("right")
    test.wait(100)
    test.screenshot("_05_secondary_100ms")
    test.wait(200)
    test.screenshot("_06_secondary_300ms")

    test.finish()
    return test


def run_all_tests():
    """Run all visual tests."""
    print("\n" + "="*60)
    print("AUTOMATED VISUAL TESTING")
    print("="*60)

    tests = [
        test_menu_display,
        test_host_game,
        test_movement,
        test_shooting,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"[ERROR] Test failed: {e}")
            results.append({'name': test_func.__name__, 'error': str(e)})
        time.sleep(2)  # Wait between tests

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for r in results:
        if isinstance(r, VisualTest):
            print(f"  {r.name}: {len(r.screenshots)} screenshots")
        else:
            print(f"  {r.get('name', 'unknown')}: {r.get('error', 'completed')}")

    return results


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        if test_name == "all":
            run_all_tests()
        elif test_name == "menu":
            test_menu_display()
        elif test_name == "host":
            test_host_game()
        elif test_name == "movement":
            test_movement()
        elif test_name == "shooting":
            test_shooting()
        else:
            print(f"Unknown test: {test_name}")
            print("Available: all, menu, host, movement, shooting")
    else:
        print("Usage: python auto_tester.py <test_name>")
        print("Available tests: all, menu, host, movement, shooting")
