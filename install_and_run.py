#!/usr/bin/env python3
"""
Quick install and run script for Python IWP Receiver
This script checks dependencies and helps get started quickly
"""

import subprocess
import sys
import os

def check_python_version():
    """Check Python version compatibility"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher required")
        print(f"   Current version: {sys.version}")
        return False

    print(f"✅ Python version OK: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def run_network_discovery():
    """Run network discovery to help user configure IWP sender device"""
    print("\n🔍 Running network discovery...")
    try:
        subprocess.run([sys.executable, "src/main.py", "discover"])
        return True
    except Exception as e:
        print(f"❌ Network discovery failed: {e}")
        return False

def main():
    print("🚀 Python IWP Receiver Setup and Quick Start")
    print("=" * 50)

    # Check Python version
    if not check_python_version():
        sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        print("\n💡 Try installing manually:")
        print("   pip install pygame matplotlib numpy pyyaml pandas scipy")
        sys.exit(1)

    # Run network discovery
    if not run_network_discovery():
        sys.exit(1)

    print("\n🎯 Next Steps:")
    print("1. Configure your IWP-enabled sender device with the IP address shown above")
    print("2. To start the visualizer:")
    print("   python src/main.py visualize")
    print("3. To run server only:")
    print("   python src/main.py server")

    # Ask if user wants to start visualizer
    try:
        response = input("\n🎨 Start the laser pattern visualizer now? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            print("\nStarting visualizer...")
            subprocess.run([sys.executable, "src/main.py", "visualize"])
    except KeyboardInterrupt:
        print("\n👋 Setup complete!")

if __name__ == "__main__":
    main()