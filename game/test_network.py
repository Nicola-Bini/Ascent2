#!/usr/bin/env python3
"""
Test script to verify networking works between two game instances.
Run this to test the network layer without needing to manually start two game windows.
"""
import socket
import threading
import time
import sys

# Add parent directory to path for imports
sys.path.insert(0, '/Users/zeratul/Developer/2026-01-28 - test michele/game')

from networking import NetworkServer, NetworkClient, NetworkMessage, get_local_ip


def test_server_client_connection():
    """Test basic server-client connection."""
    print("=" * 50)
    print("Testing Server-Client Connection")
    print("=" * 50)

    # Start server
    print("\n[1] Starting server on port 5555...")
    server = NetworkServer(port=5555)
    if not server.start():
        print("FAILED: Could not start server")
        return False
    print("Server started successfully")

    time.sleep(0.5)

    # Connect client
    print("\n[2] Connecting client to 127.0.0.1:5555...")
    client = NetworkClient()
    if not client.connect("127.0.0.1", port=5555, timeout=5.0):
        print("FAILED: Could not connect client")
        server.stop()
        return False
    print(f"Client connected! Assigned player_id: {client.player_id}")

    time.sleep(0.5)

    # Test sending player update from client
    print("\n[3] Client sending player state update...")
    test_state = {
        'position': (1.0, 2.0, 3.0),
        'rotation': (0.0, 90.0, 0.0),
        'health': 100,
        'is_alive': True
    }
    client.send_player_update(test_state)

    time.sleep(0.3)

    # Server receives messages
    print("\n[4] Server checking for messages...")
    messages = server.get_messages()
    print(f"Server received {len(messages)} message(s)")
    for msg in messages:
        print(f"   Message type: {msg.get('type')}, player_id: {msg.get('player_id')}")
        if msg.get('state'):
            print(f"   State: {msg.get('state')}")

    # Server broadcasts game state
    print("\n[5] Server broadcasting game state...")
    host_state = {
        'position': (0.0, 0.0, 0.0),
        'rotation': (0.0, 0.0, 0.0),
        'health': 100,
        'is_alive': True
    }
    server.broadcast_game_state({client.player_id: test_state}, host_state=host_state)

    time.sleep(0.3)

    # Client receives messages
    print("\n[6] Client checking for messages...")
    client_messages = client.get_messages()
    print(f"Client received {len(client_messages)} message(s)")
    for msg in client_messages:
        print(f"   Message type: {msg.get('type')}")

    # Test shooting
    print("\n[7] Client sending shoot command...")
    shot_data = {
        'position': (1.0, 2.0, 3.0),
        'direction': (0.0, 0.0, 1.0),
        'owner_id': client.player_id,
        'projectile_id': 12345
    }
    client.send_shoot(shot_data)

    time.sleep(0.3)

    # Server receives shoot
    messages = server.get_messages()
    print(f"Server received {len(messages)} message(s)")
    for msg in messages:
        if msg.get('type') == NetworkMessage.PROJECTILE_SPAWN:
            print(f"   Projectile spawn from player {msg.get('projectile', {}).get('owner_id')}")

    # Cleanup
    print("\n[8] Cleaning up...")
    client.stop()
    server.stop()

    print("\n" + "=" * 50)
    print("TEST PASSED: Server-client networking works!")
    print("=" * 50)
    return True


def test_multiple_clients():
    """Test multiple clients connecting."""
    print("\n" + "=" * 50)
    print("Testing Multiple Clients")
    print("=" * 50)

    # Start server
    print("\n[1] Starting server...")
    server = NetworkServer(port=5556)
    if not server.start():
        print("FAILED: Could not start server")
        return False

    time.sleep(0.5)

    # Connect multiple clients
    clients = []
    for i in range(3):
        print(f"\n[{i+2}] Connecting client {i+1}...")
        client = NetworkClient()
        if client.connect("127.0.0.1", port=5556, timeout=5.0):
            print(f"   Client {i+1} connected with player_id: {client.player_id}")
            clients.append(client)
        else:
            print(f"   FAILED: Client {i+1} could not connect")

    time.sleep(0.5)

    print(f"\n[5] Connected clients: {len(clients)}")

    # Cleanup
    print("\n[6] Cleaning up...")
    for client in clients:
        client.stop()
    server.stop()

    if len(clients) == 3:
        print("\n" + "=" * 50)
        print("TEST PASSED: Multiple clients can connect!")
        print("=" * 50)
        return True
    else:
        print("\n" + "=" * 50)
        print("TEST FAILED: Not all clients connected")
        print("=" * 50)
        return False


def show_local_ip():
    """Show local IP for LAN play."""
    local_ip = get_local_ip()
    print(f"\n📡 Your local IP address: {local_ip}")
    print(f"   Other players on your LAN can join using this IP")


if __name__ == "__main__":
    print("🎮 Descent-like 6DOF Network Test")
    print("=" * 50)

    show_local_ip()

    print("\n")

    # Run tests
    test1 = test_server_client_connection()
    test2 = test_multiple_clients()

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Server-Client Connection: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Multiple Clients:         {'✅ PASS' if test2 else '❌ FAIL'}")

    if test1 and test2:
        print("\n✅ All tests passed! The game networking should work.")
        print("\nTo play:")
        print("  1. Run: python game/main.py")
        print("  2. Click 'HOST GAME' on one computer")
        print("  3. On another computer (or terminal), run the game")
        print("  4. Click 'JOIN GAME' and enter the host's IP")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
