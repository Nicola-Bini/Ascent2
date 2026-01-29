#!/usr/bin/env python3
"""
Capture screenshots of running game windows using Quartz.
"""
import subprocess
import time
import os
import sys

try:
    import Quartz
    from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionAll, kCGNullWindowID
    from Quartz import CGWindowListCreateImage, CGRectNull, kCGWindowListOptionIncludingWindow
    from Quartz import kCGWindowImageDefault, CGImageDestinationCreateWithURL, CGImageDestinationAddImage, CGImageDestinationFinalize
    from CoreFoundation import CFURLCreateWithFileSystemPath, kCFStringEncodingUTF8, kCFURLPOSIXPathStyle
    QUARTZ_AVAILABLE = True
except ImportError:
    QUARTZ_AVAILABLE = False
    print("Quartz not available, using screencapture")

LOG_DIR = "/Users/zeratul/Developer/2026-01-28 - test michele/game/test_logs"
os.makedirs(LOG_DIR, exist_ok=True)

def list_windows():
    """List all windows."""
    if not QUARTZ_AVAILABLE:
        return []

    windows = CGWindowListCopyWindowInfo(kCGWindowListOptionAll, kCGNullWindowID)
    result = []
    for w in windows:
        name = w.get('kCGWindowOwnerName', '')
        title = w.get('kCGWindowName', '')
        wid = w.get('kCGWindowNumber', 0)
        bounds = w.get('kCGWindowBounds', {})
        if name and ('python' in name.lower() or 'game' in name.lower() or 'ursina' in name.lower() or 'descent' in name.lower()):
            result.append({
                'owner': name,
                'title': title,
                'id': wid,
                'bounds': bounds
            })
    return result

def capture_window(window_id, filename):
    """Capture a specific window by ID."""
    if not QUARTZ_AVAILABLE:
        os.system(f'screencapture -x {filename}')
        return

    image = CGWindowListCreateImage(
        CGRectNull,
        kCGWindowListOptionIncludingWindow,
        window_id,
        kCGWindowImageDefault
    )

    if image:
        url = CFURLCreateWithFileSystemPath(None, filename, kCFURLPOSIXPathStyle, False)
        dest = CGImageDestinationCreateWithURL(url, 'public.png', 1, None)
        CGImageDestinationAddImage(dest, image, None)
        CGImageDestinationFinalize(dest)
        print(f"Captured window {window_id} to {filename}")
    else:
        print(f"Failed to capture window {window_id}")

def run_test():
    """Run the full test."""
    print("=" * 60)
    print("MULTIPLAYER GAME TEST")
    print("=" * 60)

    # Kill any existing game processes
    os.system("pkill -f 'auto_test.py' 2>/dev/null")
    time.sleep(1)

    # Start host
    print("\n[1] Starting HOST...")
    host_log = open(f"{LOG_DIR}/host_detailed.log", "w")
    host_proc = subprocess.Popen(
        ["python", "-u", "auto_test.py", "host"],
        cwd="/Users/zeratul/Developer/2026-01-28 - test michele/game",
        stdout=host_log,
        stderr=subprocess.STDOUT,
        env={**os.environ, "PYTHONUNBUFFERED": "1"}
    )
    print(f"    Host PID: {host_proc.pid}")

    # Wait for host to start
    time.sleep(6)

    # List windows
    print("\n[2] Checking windows...")
    windows = list_windows()
    print(f"    Found {len(windows)} game-related windows:")
    for w in windows:
        print(f"      - {w['owner']}: {w['title']} (ID: {w['id']}, Bounds: {w['bounds']})")

    # Take screenshot
    print("\n[3] Taking host screenshot...")
    os.system(f"screencapture -x {LOG_DIR}/capture_host.png")

    # Start client
    print("\n[4] Starting CLIENT...")
    client_log = open(f"{LOG_DIR}/client_detailed.log", "w")
    client_proc = subprocess.Popen(
        ["python", "-u", "auto_test.py", "client", "127.0.0.1"],
        cwd="/Users/zeratul/Developer/2026-01-28 - test michele/game",
        stdout=client_log,
        stderr=subprocess.STDOUT,
        env={**os.environ, "PYTHONUNBUFFERED": "1"}
    )
    print(f"    Client PID: {client_proc.pid}")

    # Wait for client to connect
    time.sleep(6)

    # List windows again
    print("\n[5] Checking windows after client connected...")
    windows = list_windows()
    print(f"    Found {len(windows)} game-related windows:")
    for w in windows:
        print(f"      - {w['owner']}: {w['title']} (ID: {w['id']}, Bounds: {w['bounds']})")

    # Take screenshot
    print("\n[6] Taking both windows screenshot...")
    os.system(f"screencapture -x {LOG_DIR}/capture_both.png")

    # Let them run
    print("\n[7] Running for 10 seconds...")
    time.sleep(10)

    # Final screenshot
    print("\n[8] Taking final screenshot...")
    os.system(f"screencapture -x {LOG_DIR}/capture_final.png")

    # Close logs and terminate
    print("\n[9] Stopping processes...")
    host_log.close()
    client_log.close()

    host_proc.terminate()
    client_proc.terminate()

    time.sleep(2)

    # Read and print logs
    print("\n" + "=" * 60)
    print("HOST LOG:")
    print("=" * 60)
    with open(f"{LOG_DIR}/host_detailed.log", "r") as f:
        content = f.read()
        print(content if content else "(empty)")

    print("\n" + "=" * 60)
    print("CLIENT LOG:")
    print("=" * 60)
    with open(f"{LOG_DIR}/client_detailed.log", "r") as f:
        content = f.read()
        print(content if content else "(empty)")

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Host process ran: {host_proc.pid}")
    print(f"Client process ran: {client_proc.pid}")
    print(f"Screenshots saved to: {LOG_DIR}/")
    print("  - capture_host.png")
    print("  - capture_both.png")
    print("  - capture_final.png")
    print("\nCheck the logs above to verify:")
    print("  - Host: 'Server started' and 'Game started'")
    print("  - Client: 'Connected as Player' and 'Player X joined'")

if __name__ == "__main__":
    run_test()
