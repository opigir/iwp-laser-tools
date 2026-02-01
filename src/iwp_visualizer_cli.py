#!/usr/bin/env python3
"""
IWP Laser Visualizer - Real-time ILDA Wave Protocol visualization
A professional tool for visualizing IWP laser patterns in real-time
"""

import sys
import argparse
from network_discovery import NetworkDiscovery
from udp_server import UDPServer

# Import pygame-dependent modules only when needed
try:
    from laser_visualizer import LaserVisualizer
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

def main():
    parser = argparse.ArgumentParser(
        description="IWP Laser Visualizer - Real-time ILDA Wave Protocol visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python iwp_visualizer_cli.py discover           # Find computer's IP for IWP device setup
  python iwp_visualizer_cli.py server             # Run UDP server only
  python iwp_visualizer_cli.py visualize          # Run visualizer with integrated server
  python iwp_visualizer_cli.py visualize --port 7200  # Use custom port

Commands:
  discover     Auto-discover network configuration
  server       Run UDP packet receiver only
  visualize    Run real-time laser pattern visualizer
        """
    )

    parser.add_argument('command', choices=['discover', 'server', 'visualize'],
                       help='Command to execute')
    parser.add_argument('--port', type=int, default=7200,
                       help='UDP port to listen on (default: 7200)')
    parser.add_argument('--width', type=int, default=800,
                       help='Visualizer window width (default: 800)')
    parser.add_argument('--height', type=int, default=600,
                       help='Visualizer window height (default: 600)')

    args = parser.parse_args()

    if args.command == 'discover':
        print("🔍 Discovering network configuration...")
        discovery = NetworkDiscovery()
        discovery.print_discovery_results()

    elif args.command == 'server':
        print(f"🖥️  Starting UDP server on port {args.port}...")

        def on_packet(packet, address):
            print(f"📡 Packet from {address}: {packet.point_count} points, "
                  f"timestamp {packet.timestamp}")

        def on_error(error):
            print(f"❌ Server error: {error}")

        server = UDPServer(port=args.port)
        server.set_packet_callback(on_packet)
        server.set_error_callback(on_error)

        if server.start():
            try:
                print("Press Ctrl+C to stop server")
                while True:
                    import time
                    time.sleep(1)
                    # Optional: print periodic status
                    if server.get_statistics()['packets_received'] % 100 == 0 and server.get_statistics()['packets_received'] > 0:
                        server.print_status()
            except KeyboardInterrupt:
                print("\n🛑 Stopping server...")
            finally:
                server.stop()
        else:
            print("❌ Failed to start server")
            sys.exit(1)

    elif args.command == 'visualize':
        if not PYGAME_AVAILABLE:
            print("❌ Pygame not available. Install with: pip install pygame")
            print("💡 You can still use the 'server' command to receive packets")
            sys.exit(1)

        print(f"🎨 Starting laser pattern visualizer on port {args.port}...")
        print(f"   Window size: {args.width}x{args.height}")

        visualizer = LaserVisualizer(
            width=args.width,
            height=args.height,
            title=f"IWP Laser Patterns Visualizer(Port {args.port})"
        )

        visualizer.run_with_server(port=args.port)

    print("\n✅ Application finished")


if __name__ == "__main__":
    main()