#!/usr/bin/env python3
"""
Demo script to show the enhanced IWP Visualizer functionality
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("🎯 IWP Laser Tools Demo")
    print("=" * 40)
    print()
    print("This demo shows the IWP Laser Tools with:")
    print("• 📡 Receiver Mode - Listen for IWP packets from network devices")
    print("• 📤 Sender Mode - Load ILDA files and transmit as IWP")
    print("• 🎮 Full GUI controls with pygame interface")
    print("• 📁 Built-in file browser for ILDA files")
    print("• 🌐 Network transmission capabilities")
    print()

    print("Available test modes:")
    print("1. Test original visualizer (receiver mode)")
    print("2. Test original visualizer with ILDA support (if you have ILDA files)")
    print("3. Test network port functionality")
    print("4. Exit")
    print()

    choice = input("Enter your choice (1-4): ").strip()

    if choice == "1":
        print("\n🚀 Starting IWP Laser Tools in receiver mode...")
        print("This will listen for IWP packets on port 7200")
        print("Use your IWP sender device to send data, or use the test tool")
        print("Press ESC to exit the visualizer")
        print()

        # Import and run original visualizer
        from laser_visualizer import LaserVisualizer

        visualizer = LaserVisualizer()
        visualizer.run_with_server(port=7200)

    elif choice == "2":
        ilda_file = input("Enter path to ILDA file: ").strip()
        if ilda_file and os.path.exists(ilda_file):
            print(f"\n🎬 Loading ILDA file: {ilda_file}")
            print("Controls:")
            print("  S - Switch between IWP/ILDA modes")
            print("  O - Open file browser")
            print("  SPACE - Play/pause")
            print("  ESC - Exit")
            print()

            from laser_visualizer import LaserVisualizer

            visualizer = LaserVisualizer()
            visualizer.run_with_server(port=7200, ilda_file=ilda_file)
        else:
            print("❌ ILDA file not found or not specified")

    elif choice == "3":
        print("\n🔧 Testing network port functionality...")
        print("This will test if your system can send/receive UDP packets")
        print()

        from port_test import main as port_test_main
        port_test_main()

    elif choice == "4":
        print("\n👋 Thanks for trying the IWP Laser Tools!")
        return

    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")