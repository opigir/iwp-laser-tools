#!/usr/bin/env python3
"""
Simple test of the enhanced visualizer
"""

import pygame
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_visualizer_import():
    """Test importing the enhanced visualizer"""
    try:
        print("Initializing pygame...")
        pygame.init()

        print("Importing enhanced visualizer...")
        from src.enhanced_visualizer import EnhancedLaserVisualizer

        print("✅ Enhanced visualizer imported successfully!")
        return True

    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_startup():
    """Test basic startup without running the full app"""
    try:
        pygame.init()
        from src.enhanced_visualizer import EnhancedLaserVisualizer

        print("Creating enhanced visualizer instance...")
        # Note: This will create a pygame window
        visualizer = EnhancedLaserVisualizer(width=800, height=600)
        print("✅ Visualizer created successfully!")

        # Test basic methods
        print("Testing basic methods...")
        visualizer._toggle_app_mode()
        print(f"✅ Mode toggle works, current mode: {visualizer.app_mode}")

        # Test status
        status = visualizer.ilda_system.get_status()
        print(f"✅ ILDA status: {status['loaded']}")

        # Cleanup
        pygame.quit()
        return True

    except Exception as e:
        print(f"❌ Basic startup failed: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        return False

if __name__ == "__main__":
    print("🧪 Enhanced Visualizer Test")
    print("=" * 30)

    success = True
    success &= test_visualizer_import()
    success &= test_basic_startup()

    print("\n" + "=" * 30)
    if success:
        print("🎉 Basic tests passed!")
        print("Ready to run the enhanced visualizer!")

        answer = input("\nRun the enhanced visualizer now? (y/N): ")
        if answer.lower() in ['y', 'yes']:
            print("\nStarting enhanced visualizer...")
            from src.enhanced_visualizer import main
            main()
    else:
        print("❌ Tests failed - check the errors above")